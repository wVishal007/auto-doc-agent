from langchain_core.prompts import PromptTemplate

from models.planner_output import PlannerOutput, ReflectionResult
from prompts.reflection_prompt import REFLECTION_TEMPLATE
from services.llm import extract_text, get_llm


def _build_content_summary(content: dict) -> str:
    lines = []
    for section_name, section_content in content.items():
        preview = section_content[:200].replace("\n", " ")
        lines.append(f"--- {section_name} ---\n{preview}...")
    return "\n\n".join(lines)


def review_content(
    plan: PlannerOutput, content: dict
) -> ReflectionResult:
    llm = get_llm(task="reflector", temperature=0.2)
    requested_sections = ", ".join(plan.sections)
    content_summary = _build_content_summary(content)

    prompt = PromptTemplate(
        template=REFLECTION_TEMPLATE,
        input_variables=[
            "document_title",
            "requested_sections",
            "generated_content",
        ],
    )

    chain = prompt | llm
    response = chain.invoke(
        {
            "document_title": plan.document_title,
            "requested_sections": requested_sections,
            "generated_content": content_summary,
        }
    )

    result_text = extract_text(response).strip()

    if result_text.upper().startswith("PASS"):
        return ReflectionResult(
            status="PASS",
            feedback="All sections meet quality standards.",
            additional_content={},
        )

    if result_text.upper().startswith("IMPROVED"):
        additional = _generate_missing_sections(
            plan, content, result_text, llm
        )
        return ReflectionResult(
            status="IMPROVED",
            feedback=result_text,
            additional_content=additional,
        )

    return ReflectionResult(
        status="PASS",
        feedback="Review completed.",
        additional_content={},
    )


def _generate_missing_sections(
    plan: PlannerOutput,
    existing_content: dict,
    feedback: str,
    llm,
) -> dict:
    content_llm = get_llm(task="content", temperature=0.4)
    prompt_text = (
        f"The following sections were identified as missing or needing improvement:\n\n"
        f"{feedback}\n\n"
        f"Original request: {plan.document_title}\n"
        f"Available sections: {', '.join(plan.sections)}\n\n"
        f"Generate content for any section that needs it. "
        f"Respond with the section name followed by the content."
    )

    response = content_llm.invoke(prompt_text)
    new_content = extract_text(response).strip()

    sections = {}
    current_section = None
    current_lines = []

    for line in new_content.split("\n"):
        line = line.strip()
        if not line:
            continue
        for section_name in plan.sections:
            if section_name.lower() in line.lower() and len(line) < 80:
                if current_section and current_lines:
                    sections[current_section] = "\n".join(current_lines)
                current_section = section_name
                current_lines = []
                break
        else:
            if current_section:
                current_lines.append(line)

    if current_section and current_lines:
        sections[current_section] = "\n".join(current_lines)

    return sections
