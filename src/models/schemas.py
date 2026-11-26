from typing import Optional

from pydantic import BaseModel, Field
from .enums import IncidentCategory, Severity, Impact, Team, WorkflowName


class Classification(BaseModel):
    category: IncidentCategory = Field(description="Основной тип ИБ-инцидента")
    severity: Severity = Field(description="Серьёзность по шкале low/medium/high/critical")
    impact: Impact = Field(description="Затронутая составляющая CIA")


class Entities(BaseModel):
    iocs: list[str] = Field(default_factory=list, description="IP, домены, хэши, файлы, хосты")
    affected_assets: list[str] = Field(default_factory=list, description="Затронутые системы/аккаунты")
    mitre_tactics: list[str] = Field(default_factory=list, description="Техники MITRE ATT&CK")


class Analysis(BaseModel):
    summary: str = Field(description="Суть инцидента одним предложением")
    indicators: list[str] = Field(description="Наблюдаемые признаки/индикаторы")
    missing_info: list[str] = Field(description="Чего не хватает для точной оценки")


class Response(BaseModel):
    recommended_actions: list[str] = Field(description="Первые шаги реагирования")
    escalation_needed: bool = Field(description="Требуется ли эскалация на L2/IR")


class IncidentCore(Classification, Entities, Analysis, Response):
    pass


class Incident(IncidentCore):
    team: Team


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
