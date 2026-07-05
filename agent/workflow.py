from models.planner_output import PlannerOutput
from models.response import AgentResponse, ExecutionLogEntry
from agent.planner import create_plan
from agent.executor import generate_content
from agent.reflector import review_content
from services.document_generator import build_docx
from config import settings


def _summarize_request(user_request: str) -> str:
    if len(user_request) <= 80:
        return user_request
    return user_request[:77] + "..."


def run_agent(user_request: str) -> AgentResponse:
    log = []

    log.append(
        ExecutionLogEntry(
            step="Planning",
            status="in_progress",
            details="Analyzing request and creating task plan...",
        )
    )

    try:
        plan: PlannerOutput = create_plan(user_request)
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
        log.append(
            ExecutionLogEntry(
                step="Planning", status="failed", details=str(e)
            )
        )
        raise

    log.append(
        ExecutionLogEntry(
            step="Execution",
            status="in_progress",
            details="Generating document content in parallel...",
        )
    )

    try:
        content = generate_content(plan, user_request)
        sections_summary = ", ".join(content.keys())
        log.append(
            ExecutionLogEntry(
                step="Execution",
                status="success",
                details=f"Generated {len(content)} sections: {sections_summary}",
            )
        )
    except Exception as e:
        log.append(
            ExecutionLogEntry(
                step="Execution",
                status="failed",
                details=f"Primary model failed: {str(e)}. Trying fallback...",
            )
        )
        try:
            content = generate_content(plan, user_request, use_fallback=True)
            log.append(
                ExecutionLogEntry(
                    step="Execution",
                    status="success",
                    details=f"Fallback succeeded. Generated {len(content)} sections.",
                )
            )
        except Exception as e2:
            log.append(
                ExecutionLogEntry(
                    step="Execution",
                    status="failed",
                    details=f"Fallback also failed: {str(e2)}",
                )
            )
            raise

    log.append(
        ExecutionLogEntry(
            step="Reflection",
            status="in_progress",
            details="Reviewing document quality and completeness...",
        )
    )

    try:
        reflection = review_content(plan, content)
        if reflection.status == "PASS":
            log.append(
                ExecutionLogEntry(
                    step="Reflection",
                    status="success",
                    details="All sections meet quality standards.",
                )
            )
        else:
            content.update(reflection.additional_content)
            log.append(
                ExecutionLogEntry(
                    step="Reflection",
                    status="success",
                    details=f"Improved content: {reflection.feedback[:100]}...",
                )
            )
    except Exception as e:
        log.append(
            ExecutionLogEntry(
                step="Reflection",
                status="success",
                details="Skipped reflection (non-critical).",
            )
        )

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
            sections=content,
            output_dir=settings.output_dir,
        )
        log.append(
            ExecutionLogEntry(
                step="Document Generation",
                status="success",
                details=f"Saved to {document_path}",
            )
        )
    except Exception as e:
        log.append(
            ExecutionLogEntry(
                step="Document Generation",
                status="failed",
                details=str(e),
            )
        )
        raise

    summary = (
        f"Generated {plan.document_title} with "
        f"{len(content)} sections based on {len(plan.tasks)} planned tasks. "
        f"Request: {_summarize_request(user_request)}"
    )

    return AgentResponse(
        tasks=[t.model_dump() for t in plan.tasks],
        assumptions=plan.assumptions,
        summary=summary,
        document_path=document_path,
        execution_log=log,
    )
