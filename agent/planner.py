import time

from langchain_core.language_models import BaseLanguageModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from models.planner_output import PlannerOutput
from prompts.planner_prompt import PLANNER_TEMPLATE
from services.llm import get_provider_info
from services.performance import tracker
from services.retry import invoke_with_retry


def create_plan(user_request: str, llm: BaseLanguageModel) -> PlannerOutput:
    parser = PydanticOutputParser(pydantic_object=PlannerOutput)

    prompt = PromptTemplate(
        template=PLANNER_TEMPLATE,
        input_variables=["request"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | llm | parser

    provider, model = get_provider_info(llm.model)
    formatted = prompt.format(request=user_request)
    prompt_chars = len(formatted)

    start = time.time()
    retries_before = tracker.retry_count

    result = invoke_with_retry(
        lambda: chain.invoke({"request": user_request}),
        label="Planner",
    )
    duration = time.time() - start
    retries = tracker.retry_count - retries_before

    tracker.llm_call(
        provider=provider,
        model=model,
        label="Planner",
        duration=duration,
        success=True,
        retries=retries,
        prompt_chars=prompt_chars,
    )

    return result
