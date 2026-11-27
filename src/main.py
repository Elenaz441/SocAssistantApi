from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.config import settings
from src.llm.client import GigaChatClient
from src.llm.workflows import IncidentWorkflows
from src.routers.incidents import router as incidents_router
from src.routers.tasks import router as tasks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    llm_client = GigaChatClient()
    app.state.incident_workflows = IncidentWorkflows(llm_client)
    yield


app = FastAPI(
    title="Incident Analysis API",
    description="API для анализа инцидентов информационной безопасности с помощью LLM.",
    version="1.0.0",
    lifespan=lifespan
)
app.include_router(incidents_router)
app.include_router(tasks_router)


@app.get("/health", tags=["Сервис"])
async def health():
    return {
        "status": "ok",
        "model": settings.GIGACHAT_MODEL
    }
