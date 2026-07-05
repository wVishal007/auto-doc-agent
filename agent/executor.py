from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_core.prompts import PromptTemplate

from models.planner_output import PlannerOutput
from prompts.executor_prompt import EXECUTOR_TEMPLATE
from services.llm import extract_text, get_llm


def _generate_section(
    plan: PlannerOutput,
    section: str,
    user_request: str,
    prompt_template: PromptTemplate,
    temperature: float,
    use_fallback: bool = False,
) -> tuple:
    task = "fallback" if use_fallback else "content"
    llm = get_llm(task=task, temperature=temperature)
    chain = prompt_template | llm
    all_sections = ", ".join(plan.sections)
    response = chain.invoke(
        {
            "document_title": plan.document_title,
            "section_name": section,
            "user_request": user_request,
            "all_sections": all_sections,
        }
    )
    return section, extract_text(response).strip()


def generate_content(plan: PlannerOutput, user_request: str, use_fallback: bool = False) -> dict:
    prompt = PromptTemplate(
        template=EXECUTOR_TEMPLATE,
        input_variables=[
            "document_title",
            "section_name",
            "user_request",
            "all_sections",
        ],
    )

    raw = {}
    with ThreadPoolExecutor(max_workers=len(plan.sections)) as executor:
        futures = {
            executor.submit(
                _generate_section, plan, s, user_request, prompt, 0.4, use_fallback
            ): s
            for s in plan.sections
        }
        for future in as_completed(futures):
            section, text = future.result()
            raw[section] = text

    content = {s: raw[s] for s in plan.sections if s in raw}
    return content
