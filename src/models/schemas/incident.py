from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    model_validator,
)

from src.models.enums import (
    IncidentCategory,
    Severity,
    Impact,
    Team,
)


class Classification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: IncidentCategory = Field(description="Основной тип ИБ-инцидента")
    severity: Severity = Field(description="Серьёзность по шкале low/medium/high/critical")
    impact: Impact = Field(description="Затронутая составляющая CIA")
    confidence: float = Field(ge=0.0, le=1.0, description="Уверенность модели в классификации")
    suspected_actor: Optional[str] = Field(default=None, description="Предполагаемый актор, если известен")
    requires_escalation: bool = Field(default=False, description="Требуется ли немедленная эскалация")

    @model_validator(mode="after")
    def critical_must_escalate(self):
        if self.severity == "critical" and not self.requires_escalation:
            raise ValueError("severity=critical требует requires_escalation=True")
        return self


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
