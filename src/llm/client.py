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

    def _build_request(
        self,
        schema: Type[BaseModel],
        instruction: str,
        data: dict,
        feedback: str = "",
    ):
        user_data = dict(data)
        if feedback:
            user_data["validation_feedback"] = (
                "Предыдущая попытка завершилась ошибкой. Исправь результат с учётом замечания: "
                + feedback
            )

        return ChatCompletionRequest(
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
                        user_data,
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

    async def ask_json_with_retry(
        self,
        schema: Type[BaseModel],
        instruction: str,
        data: dict,
        stage: str,
        trace: list[StepMetric],
        max_retries: int = 2,
    ) -> BaseModel:

        metric = StepMetric(
            stage=stage,
            latency_s=0,
            success=False,
        )
        trace.append(metric)
        started_at = time.perf_counter()
        last_exception = None

        prompt_tokens = 0
        completion_tokens = 0
        usage_received = False

        try:
            for attempt in range(max_retries + 1):
                metric.attempts = attempt + 1
                metric.retries = attempt
                try:
                    request = self._build_request(
                        schema=schema,
                        instruction=instruction,
                        data=data,
                        feedback=(
                            str(last_exception)
                            if last_exception else ""
                        ),
                    )
                    async with self._semaphore:
                        async with GigaChat(
                            credentials=settings.GIGACHAT_API_KEY,
                            model=settings.GIGACHAT_MODEL,
                            base_url=settings.GIGACHAT_BASE_URL,
                            verify_ssl_certs=False,
                        ) as giga:
                            completion, parsed = await giga.achat.parse(
                                request,
                                response_format=schema,
                            )
                    prompt_tokens += completion.usage.input_tokens
                    completion_tokens += completion.usage.output_tokens
                    validated = schema.model_validate(parsed.model_dump())
                    metric.success = True
                    return validated
                except Exception as exc:
                    last_exception = exc
                    if attempt == max_retries:
                        raise
        except Exception as exc:
            metric.error = f"{type(exc).__name__}: {str(exc)[:300]}"
            raise
        finally:
            metric.latency_s = round(time.perf_counter() - started_at, 4)
            if usage_received:
                metric.prompt_tokens = prompt_tokens
                metric.completion_tokens = completion_tokens
                metric.total_tokens = prompt_tokens + completion_tokens
