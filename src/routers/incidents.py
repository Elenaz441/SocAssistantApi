import time
from fastapi import APIRouter, HTTPException, Request
from src.config import settings
from src.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    StepMetric
)


router = APIRouter(
    prefix="/incidents",
    tags=["ИБ-инциденты"]
)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_incident(
    payload: AnalyzeRequest,
    request: Request
):
    if not settings.GIGACHAT_API_KEY:
        raise HTTPException(status_code=503, detail="Не задан GIGACHAT_API_KEY.")
    workflow = request.app.state.incident_workflows
    started_at = time.perf_counter()
    trace: list[StepMetric] = []
    incident = None
    error = None
    try:
        if payload.workflow == "one_shot":
            incident = await workflow.one_shot(payload.incident_text, trace)
        else:
            incident = await workflow.sequential(payload.incident_text, trace)
    except Exception as exc:
        error = f"{type(exc).__name__}: {str(exc)[:350]}"

    # Суммируем токены всех этапов
    prompt_tokens = sum(
        step.prompt_tokens or 0
        for step in trace
    )

    completion_tokens = sum(
        step.completion_tokens or 0
        for step in trace
    )

    total_tokens = prompt_tokens + completion_tokens
    wall_time = round(time.perf_counter() - started_at, 4)

    return AnalyzeResponse(
        success=incident is not None and error is None,
        workflow=payload.workflow,
        incident=incident,
        wall_time_s=wall_time,
        api_calls=len(trace),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        steps=trace,
        error=error
    )
