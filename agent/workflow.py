from models.planner_output import PlannerOutput
from models.response import AgentResponse, ExecutionLogEntry
from agent.planner import create_plan
from agent.executor import generate_document
from agent.reflector import review_document
from services.document_generator import build_docx
from services.llm import create_llm, get_provider_info
from services.performance import tracker
from config import settings


def _summarize_request(user_request: str) -> str:
    if len(user_request) <= 80:
        return user_request
    return user_request[:77] + "..."


def run_agent(user_request: str) -> AgentResponse:
    tracker.request_started()
    log = []

    planner_llm = create_llm(settings.planner_model, settings.temperature)
    generator_llm = create_llm(settings.generator_model, settings.temperature)
    reflect_llm = create_llm(settings.reflector_model, settings.temperature)
    fallback_llm = create_llm(settings.fallback_model, settings.temperature)

    _, planner_model_name = get_provider_info(settings.planner_model)
    _, generator_model_name = get_provider_info(settings.generator_model)
    _, reflect_model_name = get_provider_info(settings.reflector_model)
    _, fallback_model_name = get_provider_info(settings.fallback_model)

    # ── Planning ────────────────────────────────────────────────
    tracker.stage_start("Planning")
    log.append(
        ExecutionLogEntry(
            step="Planning",
            status="in_progress",
            details="Analyzing request and creating task plan...",
        )
    )

    try:
        plan: PlannerOutput = create_plan(user_request, planner_llm)
        tracker.stage_end("Planning")
        log.append(
            ExecutionLogEntry(
                step="Planning",
                status="success",
                details=f"Identified {len(plan.tasks)} tasks, "
                f"{len(plan.assumptions)} assumptions, "
                f"{len(plan.sections)} sections.",
            )
        )
    except Exception as e:
        tracker.stage_end("Planning")
        log.append(
            ExecutionLogEntry(
                step="Planning", status="failed", details=str(e)
            )
        )
        raise

    # ── Document Generation ─────────────────────────────────────
    tracker.stage_start("Document Generation")
    log.append(
        ExecutionLogEntry(
            step="Document Generation",
            status="in_progress",
            details="Generating complete document in single pass...",
        )
    )

    current_generator = generator_llm
    used_fallback = False

    try:
        full_document = generate_document(plan, user_request, current_generator)
        tracker.stage_end("Document Generation")
        section_count = full_document.count("\n# ") + 1 if "\n# " in full_document else len(plan.sections)
        log.append(
            ExecutionLogEntry(
                step="Document Generation",
                status="success",
                details=f"Generated document with {section_count} sections in a single pass.",
            )
        )
    except Exception as e:
        log.append(
            ExecutionLogEntry(
                step="Document Generation",
                status="failed",
                details=f"Primary generator failed: {str(e)}. Trying fallback...",
            )
        )
        generator_provider, _ = get_provider_info(settings.generator_model)
        fallback_provider, _ = get_provider_info(settings.fallback_model)
        tracker.fallback(generator_provider, fallback_provider)
        try:
            current_generator = fallback_llm
            full_document = generate_document(plan, user_request, current_generator)
            used_fallback = True
            tracker.stage_end("Document Generation")
            log.append(
                ExecutionLogEntry(
                    step="Document Generation",
                    status="success",
                    details=f"Fallback succeeded. Generated document in single pass.",
                )
            )
        except Exception as e2:
            tracker.stage_end("Document Generation")
            log.append(
                ExecutionLogEntry(
                    step="Document Generation",
                    status="failed",
                    details=f"Fallback also failed: {str(e2)}",
                )
            )
            raise

    # ── Reflection ─────────────────────────────────────────────
    tracker.stage_start("Reflection")
    log.append(
        ExecutionLogEntry(
            step="Reflection",
            status="in_progress",
            details="Reviewing document quality and completeness...",
        )
    )

    regenerated = False

    try:
        reflection = review_document(plan, full_document, reflect_llm, user_request)
        tracker.stage_end("Reflection")

        if reflection.status == "PASS":
            log.append(
                ExecutionLogEntry(
                    step="Reflection",
                    status="success",
                    details=f"Quality score: {reflection.quality_score}/10. All sections meet standards.",
                )
            )
        else:
            log.append(
                ExecutionLogEntry(
                    step="Reflection",
                    status="success",
                    details=f"Quality score: {reflection.quality_score}/10. "
                    f"Regenerating document with feedback.",
                )
            )

            tracker.stage_start("Regeneration")
            log.append(
                ExecutionLogEntry(
                    step="Document Regeneration",
                    status="in_progress",
                    details="Regenerating full document based on reflection feedback...",
                )
            )

            try:
                full_document = generate_document(
                    plan, user_request, current_generator, feedback=reflection.feedback
                )
                regenerated = True
                tracker.stage_end("Regeneration")
                log.append(
                    ExecutionLogEntry(
                        step="Document Regeneration",
                        status="success",
                        details=f"Regenerated document with feedback incorporated.",
                    )
                )
            except Exception as e:
                tracker.stage_end("Regeneration")
                log.append(
                    ExecutionLogEntry(
                        step="Document Regeneration",
                        status="failed",
                        details=f"Regeneration failed: {str(e)}. Using original document.",
                    )
                )
    except Exception as e:
        tracker.stage_end("Reflection")
        log.append(
            ExecutionLogEntry(
                step="Reflection",
                status="success",
                details="Skipped reflection (non-critical).",
            )
        )

    # ── DOCX Generation ────────────────────────────────────────
    tracker.stage_start("DOCX Generation")
    log.append(
        ExecutionLogEntry(
            step="Document Generation",
            status="in_progress",
            details="Building .docx file...",
        )
    )

    try:
        document_path = build_docx(
            title=plan.document_title,
            full_document=full_document,
            output_dir=settings.output_dir,
        )
        tracker.stage_end("DOCX Generation")
        log.append(
            ExecutionLogEntry(
                step="Document Generation",
                status="success",
                details=f"Saved to {document_path}",
            )
        )
    except Exception as e:
        tracker.stage_end("DOCX Generation")
        log.append(
            ExecutionLogEntry(
                step="Document Generation",
                status="failed",
                details=str(e),
            )
        )
        raise

    fallback_note = " (used fallback model)" if used_fallback else ""
    regen_note = " (regenerated after reflection)" if regenerated else ""
    summary = (
        f"Generated {plan.document_title} with "
        f"{len(plan.sections)} sections based on {len(plan.tasks)} planned tasks"
        f"{fallback_note}{regen_note}. "
        f"Request: {_summarize_request(user_request)}"
    )

    tracker.print_summary()

    return AgentResponse(
        tasks=[t.model_dump() for t in plan.tasks],
        assumptions=plan.assumptions,
        summary=summary,
        document_path=document_path,
        execution_log=log,
    )
