from src.llm.prompts import (
    CLASSIFY_TASK,
    ENTITIES_TASK,
    ANALYSIS_TASK,
    RESPONSE_TASK,
    ONE_SHOT_TASK
)
from src.models import (
    Classification,
    Entities,
    Analysis,
    Response,
    IncidentCore,
    Incident,
    StepMetric,
    TEAM_BY_CATEGORY
)


class IncidentWorkflows:
    """
    Сценарии анализа ИБ-инцидентов.
    Не содержит деталей SDK.
    """

    def __init__(self, llm_client):
        self.llm = llm_client

    @staticmethod
    def _payload(text, **extra):
        return {
            "incident_text": text,
            **extra
        }

    # Режим одного запроса
    async def one_shot(
        self,
        text: str,
        trace: list[StepMetric]
    ) -> Incident:
        core = await self.llm.ask_json(
            schema=IncidentCore,
            instruction=ONE_SHOT_TASK,
            data=self._payload(text),
            stage="one_shot",
            trace=trace
        )

        return Incident(
            **core.model_dump(),
            team=TEAM_BY_CATEGORY[core.category]
        )

    # Последовательный режим
    async def sequential(
        self,
        text: str,
        trace: list[StepMetric]
    ) -> Incident:
        # Этап 1. Классификация
        classification = await self.llm.ask_json(
            schema=Classification,
            instruction=CLASSIFY_TASK,
            data=self._payload(text),
            stage="classify",
            trace=trace
        )

        # Этап 2. Извлечение IOC
        entities = await self.llm.ask_json(
            schema=Entities,
            instruction=ENTITIES_TASK,
            data=self._payload(
                text,
                classification=classification.model_dump()
            ),
            stage="extract_entities",
            trace=trace
        )

        # Этап 3. Анализ
        analysis = await self.llm.ask_json(
            schema=Analysis,
            instruction=ANALYSIS_TASK,
            data=self._payload(
                text,
                classification=classification.model_dump(),
                entities=entities.model_dump()
            ),
            stage="analyze",
            trace=trace
        )

        # Этап 4. Реагирование
        response = await self.llm.ask_json(
            schema=Response,
            instruction=RESPONSE_TASK,
            data=self._payload(
                text,
                classification=classification.model_dump(),
                entities=entities.model_dump(),
                analysis=analysis.model_dump()
            ),
            stage="respond",
            trace=trace
        )

        # Объединяем результаты всех этапов
        return Incident(
            **classification.model_dump(),
            **entities.model_dump(),
            **analysis.model_dump(),
            **response.model_dump(),
            team=TEAM_BY_CATEGORY[
                classification.category
            ]
        )
