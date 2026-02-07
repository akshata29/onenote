from typing import Any
from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from .auth import auth_validator
from .graph_client import GraphOneNoteClient
from .mcp_adapter import MCPClient
from .rag_orchestrator import RAGOrchestrator
from .models import ChatRequest, ChatResponse, IngestionJobRequest, IngestionJobStatus
from .ingestion_worker import run_notebook_ingestion
from .telemetry import setup_tracing

app = FastAPI(title="OneNote RAG", version="1.0.0")
setup_tracing(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/notebooks")
async def list_notebooks(user: dict[str, Any] = Depends(auth_validator)):
    mcp = MCPClient(user_token=user["access_token"])
    notebooks = await mcp.list_notebooks()
    return {"value": notebooks}


@app.get("/notebooks/{notebook_id}/sections")
async def list_sections(notebook_id: str, user: dict[str, Any] = Depends(auth_validator)):
    mcp = MCPClient(user_token=user["access_token"])
    sections = await mcp.list_sections(notebook_id)
    return {"value": sections}


@app.get("/sections/{section_id}/pages")
async def list_pages(section_id: str, user: dict[str, Any] = Depends(auth_validator)):
    mcp = MCPClient(user_token=user["access_token"])
    pages = await mcp.list_pages(section_id)
    return {"value": pages}


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, user: dict[str, Any] = Depends(auth_validator)):
    orchestrator = RAGOrchestrator(user_assertion=user["access_token"])
    if body.mode.lower() == "mcp":
        result = await orchestrator.answer_with_mcp(body.message, scope={
            "notebook_id": body.notebook_id,
            "section_id": body.section_id,
            "page_id": body.page_id,
        })
    else:
        filters = []
        if body.notebook_id:
            filters.append(f"notebook_id eq '{body.notebook_id}'")
        if body.section_id:
            filters.append(f"section_id eq '{body.section_id}'")
        if body.page_id:
            filters.append(f"page_id eq '{body.page_id}'")
        filter_expr = " and ".join(filters) if filters else None
        result = await orchestrator.answer_with_search(body.message, filters=filter_expr)
    return ChatResponse(**result)


@app.post("/ingestion", response_model=IngestionJobStatus)
async def start_ingestion(body: IngestionJobRequest, background_tasks: BackgroundTasks, user: dict[str, Any] = Depends(auth_validator)):
    if not body.notebook_id:
        return IngestionJobStatus(job_id="n/a", status="failed", message="notebook_id required")
    background_tasks.add_task(run_notebook_ingestion, user["access_token"], body.notebook_id)
    return IngestionJobStatus(job_id=body.notebook_id, status="running", message="Started")
