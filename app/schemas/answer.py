from pydantic import BaseModel, Field, conint


class AnswerRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: conint(ge=1, le=5) = 3  # guardrail: cap at 5


class Citation(BaseModel):
    doc: str
    location: str
    snippet: str


class AnswerResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    refusal: bool = False
    needs_clarification: list[str] = Field(default_factory=list)
