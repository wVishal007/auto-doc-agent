import re
import time

from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate

from models.planner_output import PlannerOutput, ReflectionResult
from prompts.reflection_prompt import REFLECTION_TEMPLATE
from services.llm import extract_text_or_raise, get_provider_info
from services.performance import tracker
from services.retry import invoke_with_retry


def _parse_reflection(text: str) -> dict:
    score = 7
    weak = []
    status = "PASS"
    feedback = ""

    m = re.search(r"SCORE:\s*(\d+)", text, re.IGNORECASE)
    if m:
        score = max(1, min(10, int(m.group(1))))

    m = re.search(r"WEAK SECTIONS:\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
    if m:
        raw = m.group(1).strip()
        if raw.lower() != "none":
            weak = [s.strip() for s in raw.split(",") if s.strip()]

    m = re.search(r"STATUS:\s*(PASS|IMPROVED)", text, re.IGNORECASE)
    if m:
        status = m.group(1).upper()

    m = re.search(r"FEEDBACK:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
    if m:
        feedback = m.group(1).strip()

    return {"score": score, "weak_sections": weak, "status": status, "feedback": feedback}


def review_document(
    plan: PlannerOutput,
    full_document: str,
    llm: BaseLanguageModel,
    user_request: str = "",
) -> ReflectionResult:
    requested_sections = ", ".join(plan.sections)

    prompt = PromptTemplate(
        template=REFLECTION_TEMPLATE,
        input_variables=[
            "document_title",
            "requested_sections",
            "full_document",
            "user_request",
        ],
    )

    chain = prompt | llm
    provider, model = get_provider_info(llm.model)

    formatted = prompt.format(
        document_title=plan.document_title,
        requested_sections=requested_sections,
        full_document=full_document,
        user_request=user_request,
    )
    prompt_chars = len(formatted)

    start = time.time()
    retries_before = tracker.retry_count

    # DIAGNOSTIC - remove after debugging
    def _diag_reflector_call():
        _t0 = time.time()
        print(f"  [DIAGNOSTIC] Reflector chain.invoke() starting at t={_t0:.3f}")
        try:
            _res = chain.invoke(
                {
                    "document_title": plan.document_title,
                    "requested_sections": requested_sections,
                    "full_document": full_document,
                    "user_request": user_request,
                }
            )
            _t1 = time.time()
            print(f"  [DIAGNOSTIC] Reflector chain.invoke() succeeded at t={_t1:.3f} (+{_t1-_t0:.3f}s)")
            return _res
        except Exception as e:
            _t1 = time.time()
            print(f"  [DIAGNOSTIC] Reflector chain.invoke() FAILED at t={_t1:.3f} (+{_t1-_t0:.3f}s): {type(e).__name__} {repr(e)}")
            raise

    response = invoke_with_retry(
        _diag_reflector_call,
        label="Reflection",
    )
    duration = time.time() - start
    retries = tracker.retry_count - retries_before

    result_text = extract_text_or_raise(response)
    parsed = _parse_reflection(result_text)

    tracker.llm_call(
        provider=provider,
        model=model,
        label="Reflection",
        duration=duration,
        success=True,
        retries=retries,
        prompt_chars=prompt_chars,
        response_chars=len(result_text),
    )

    tracker.reflection(parsed["score"], parsed["weak_sections"], duration)

    return ReflectionResult(
        status=parsed["status"],
        quality_score=parsed["score"],
        weak_sections=parsed["weak_sections"],
        feedback=parsed["feedback"],
        additional_content={},
    )
