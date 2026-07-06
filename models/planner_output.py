from pydantic import BaseModel, Field
from typing import List


class Task(BaseModel):
    id: int = Field(description="Task ID")
    description: str = Field(description="What needs to be done")


class PlannerOutput(BaseModel):
    tasks: List[Task] = Field(description="List of tasks to execute")
    assumptions: List[str] = Field(description="Assumptions made due to missing information")
    sections: List[str] = Field(description="Document sections to generate")
    document_title: str = Field(description="Professional title for the generated document")


class ReflectionResult(BaseModel):
    status: str = Field(description="PASS or IMPROVED")
    quality_score: int = Field(default=7, ge=1, le=10, description="Overall quality score 1-10")
    weak_sections: list = Field(default_factory=list, description="Sections needing improvement")
    feedback: str = Field(description="Review feedback")
    additional_content: dict = Field(default_factory=dict, description="Additional sections if IMPROVED")
