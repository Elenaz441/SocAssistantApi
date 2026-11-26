import asyncio
import json
import time

from typing import Type

from gigachat import GigaChat

from gigachat.models import (
    ChatCompletionRequest,
    ChatMessage,
    ChatModelOptions,
    ChatResponseFormat,
)

from pydantic import BaseModel

from src.config import settings
from src.llm.prompts import COMMON_RULES
from src.models.schemas import StepMetric


class GigaChatClient:
    """
    Клиент для взаимодействия с GigaChat.

    Отвечает за:
    - отправку запросов;
    - получение JSON-ответов;
    - подсчёт токенов;
    - измерение времени;
    - обработку ошибок.
    """

    def __init__(self):
        self._semaphore = asyncio.Semaphore(
            settings.MAX_CONCURRENT_REQUESTS
        )

    async def ask_json(
        self,
        schema: Type[BaseModel],
        instruction: str,
        data: dict,
        stage: str,
        trace: list[StepMetric],
    ) -> BaseModel:
        # Создаём объект статистики этапа
        metric = StepMetric(
            stage=stage,
            latency_s=0,
            success=False
        )
        trace.append(metric)

        started_at = time.perf_counter()

        try:
            request = ChatCompletionRequest(
                model=settings.GIGACHAT_MODEL,
                messages=[
                    ChatMessage(
                        role="system",
                        content=(
                            f"{COMMON_RULES}\n"
                            f"Задача: {instruction}"
                        )
                    ),
                    ChatMessage(
                        role="user",
                        content=json.dumps(
                            data,
                            ensure_ascii=False
                        )
                    )
                ],
                model_options=ChatModelOptions(
                    response_format=ChatResponseFormat(
                        type="json_schema",
                        schema=schema,
                        strict=True
                    )
                )
            )

            # Ограничиваем количество одновременных запросов
            async with self._semaphore:
                async with GigaChat(
                    credentials=settings.GIGACHAT_API_KEY,
                    model=settings.GIGACHAT_MODEL,
                    base_url=settings.GIGACHAT_BASE_URL,
                    verify_ssl_certs=False,
                ) as giga:
                    completion, parsed = await giga.achat.parse(
                        request,
                        response_format=schema
                    )

            # Получаем статистику токенов
            metric.prompt_tokens = completion.usage.input_tokens
            metric.completion_tokens = completion.usage.output_tokens
            metric.total_tokens = metric.prompt_tokens + metric.completion_tokens
            metric.success = True

            return parsed

        except Exception as exc:
            metric.error = f"{type(exc).__name__}: {str(exc)[:300]}"
            raise

        finally:
            metric.latency_s = round(time.perf_counter() - started_at, 4)
