from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from models.planner_output import PlannerOutput
from prompts.planner_prompt import PLANNER_TEMPLATE
from services.llm import get_llm


def create_plan(user_request: str) -> PlannerOutput:
    parser = PydanticOutputParser(pydantic_object=PlannerOutput)

    prompt = PromptTemplate(
        template=PLANNER_TEMPLATE,
        input_variables=["request"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | get_llm(task="planner") | parser
    result = chain.invoke({"request": user_request})

    return result
