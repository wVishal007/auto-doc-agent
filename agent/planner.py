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

    # DIAGNOSTIC - remove after debugging
    def _diag_planner_call():
        _t0 = time.time()
        print(f"  [DIAGNOSTIC] Planner chain.invoke() starting at t={_t0:.3f}")
        try:
            _res = chain.invoke({"request": user_request})
            _t1 = time.time()
            print(f"  [DIAGNOSTIC] Planner chain.invoke() succeeded at t={_t1:.3f} (+{_t1-_t0:.3f}s)")
            return _res
        except Exception as e:
            _t1 = time.time()
            print(f"  [DIAGNOSTIC] Planner chain.invoke() FAILED at t={_t1:.3f} (+{_t1-_t0:.3f}s): {type(e).__name__} {repr(e)}")
            raise

    result = invoke_with_retry(_diag_planner_call, label="Planner")
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
