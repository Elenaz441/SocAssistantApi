from typing import Optional

from pydantic import (
    BaseModel,
    Field,
)

from src.models.enums import WorkflowName
from src.models.schemas.incident import Incident


class AnalyzeRequest(BaseModel):
    incident_text: str = Field(min_length=5, max_length=20000)
    workflow: WorkflowName = "sequential"


class StepMetric(BaseModel):
    stage: str
    latency_s: float
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    success: bool
    error: Optional[str] = None


class AnalyzeResponse(BaseModel):
    success: bool
    workflow: WorkflowName
    incident: Optional[Incident] = None
    wall_time_s: float
    api_calls: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    steps: list[StepMetric] = Field(default_factory=list)
    error: Optional[str] = None


class ExperimentTableResponse(BaseModel):
    success: bool = True
    rows: list[dict]
    summary: list[dict]
    note: Optional[str] = None
