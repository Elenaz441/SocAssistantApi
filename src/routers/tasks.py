from fastapi import APIRouter, HTTPException, Request

from src.config import settings

from src.tasks import (
    run_task1,
    run_task2
)

from src.models.schemas import ExperimentTableResponse


router = APIRouter(
    tags=["Учебные задания"]
)

@router.post("/task1", response_model=ExperimentTableResponse)
async def task1(request: Request):
    if not settings.GIGACHAT_API_KEY:
        raise HTTPException(status_code=503, detail="Не задан GIGACHAT_API_KEY")
    workflows = request.app.state.incident_workflows
    rows, summary = await run_task1(workflows)
    return ExperimentTableResponse(
        rows=rows,
        summary=summary,
        note=(
            "Сравнение архитектур One-shot и Sequential "
            "на 10 тестовых инцидентах. "
            "Возвращаются подробная и сводная таблицы."
        )
    )

@router.post("/task2", response_model=ExperimentTableResponse)
async def task2(request: Request):
    if not settings.GIGACHAT_API_KEY:
        raise HTTPException(status_code=503, detail="Не задан GIGACHAT_API_KEY")
    llm_client = request.app.state.llm_client
    rows, summary = await run_task2(llm_client)
    return ExperimentTableResponse(
        rows=rows,
        summary=summary,
        note=(
            "Эксперимент Structured Output + Retry. "
            "JSON Schema передаётся через GigaChat SDK. "
            "Максимальное количество повторов - 2."
        )
    )
