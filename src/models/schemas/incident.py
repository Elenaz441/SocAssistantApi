from pydantic import (
    BaseModel,
    Field,
)

from src.models.enums import (
    IncidentCategory,
    Severity,
    Impact,
    Team,
)


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
