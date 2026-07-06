import time

from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate

from models.planner_output import PlannerOutput
from prompts.executor_prompt import EXECUTOR_TEMPLATE
from services.llm import extract_text_or_raise, get_provider_info
from services.performance import tracker
from services.retry import invoke_with_retry


def generate_document(
    plan: PlannerOutput,
    user_request: str,
    llm: BaseLanguageModel,
    feedback: str = "",
) -> str:
    prompt = PromptTemplate(
        template=EXECUTOR_TEMPLATE,
        input_variables=[
            "document_title",
            "user_request",
            "sections",
            "assumptions",
            "feedback_section",
        ],
    )

    sections_str = ", ".join(plan.sections)
    assumptions_str = "\n".join(f"- {a}" for a in plan.assumptions) if plan.assumptions else "None"
    feedback_section = (
        f"\nPrevious Review Feedback:\n{feedback}\n\nAddress all issues mentioned above.\n"
        if feedback
        else ""
    )

    formatted = prompt.format(
        document_title=plan.document_title,
        user_request=user_request,
        sections=sections_str,
        assumptions=assumptions_str,
        feedback_section=feedback_section,
    )
    prompt_chars = len(formatted)
    provider, model = get_provider_info(llm.model)

    chain = prompt | llm
    start = time.time()
    retries_before = tracker.retry_count

    response = invoke_with_retry(
        lambda: chain.invoke({
            "document_title": plan.document_title,
            "user_request": user_request,
            "sections": sections_str,
            "assumptions": assumptions_str,
            "feedback_section": feedback_section,
        }),
        label="Document Generation",
        max_retries=1,
    )
    duration = time.time() - start
    retries = tracker.retry_count - retries_before

    full_text = extract_text_or_raise(response)

    tracker.llm_call(
        provider=provider,
        model=model,
        label="Document Generation",
        duration=duration,
        success=True,
        retries=retries,
        prompt_chars=prompt_chars,
        response_chars=len(full_text),
    )

    return full_text
