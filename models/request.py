from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    request: str = Field(..., min_length=1, description="Natural language request")
