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
        trace: list[StepMetric],
        use_retry: bool = True
    ) -> Incident:
        core = await self._ask(
            schema=IncidentCore,
            instruction=ONE_SHOT_TASK,
            data=self._payload(text),
            stage="one_shot",
            trace=trace,
            use_retry=use_retry
        )

        return Incident(
            **core.model_dump(),
            team=TEAM_BY_CATEGORY[core.category]
        )

    # Последовательный режим
    async def sequential(
        self,
        text: str,
        trace: list[StepMetric],
        use_retry: bool = True
    ) -> Incident:
        # Этап 1. Классификация
        classification = await self._ask(
            schema=Classification,
            instruction=CLASSIFY_TASK,
            data=self._payload(text),
            stage="classify",
            trace=trace,
            use_retry=use_retry
        )

        # Этап 2. Извлечение IOC
        entities = await self._ask(
            schema=Entities,
            instruction=ENTITIES_TASK,
            data=self._payload(
                text,
                classification=classification.model_dump()
            ),
            stage="extract_entities",
            trace=trace,
            use_retry=use_retry
        )

        # Этап 3. Анализ
        analysis = await self._ask(
            schema=Analysis,
            instruction=ANALYSIS_TASK,
            data=self._payload(
                text,
                classification=classification.model_dump(),
                entities=entities.model_dump()
            ),
            stage="analyze",
            trace=trace,
            use_retry=use_retry
        )

        # Этап 4. Реагирование
        response = await self._ask(
            schema=Response,
            instruction=RESPONSE_TASK,
            data=self._payload(
                text,
                classification=classification.model_dump(),
                entities=entities.model_dump(),
                analysis=analysis.model_dump()
            ),
            stage="respond",
            trace=trace,
            use_retry=use_retry
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

    async def _ask(
        self,
        schema,
        instruction,
        data,
        stage,
        trace,
        use_retry=True,
    ):
        if use_retry:
            return await self.llm.ask_json_with_retry(
                schema=schema,
                instruction=instruction,
                data=data,
                stage=stage,
                trace=trace,
                max_retries=2,
            )
        return await self.llm.ask_json(
            schema=schema,
            instruction=instruction,
            data=data,
            stage=stage,
            trace=trace,
        )
