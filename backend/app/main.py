from typing import Any, List, Dict
from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
import os
from datetime import datetime

from .auth import auth_validator
from .graph_client import GraphOneNoteClient
from .mcp_adapter import MCPClient
from .rag_orchestrator import RAGOrchestrator
from .search_client import AISearchClient
from .models import (
    ChatRequest, 
    ChatResponse, 
    IngestionJobRequest, 
    IngestionJobStatus,
    SearchFilters,
    AdvancedSearchRequest,
    SearchFacetsResponse,
    SearchSuggestionsResponse,
    IngestionSummaryResponse,
    AdminStatsResponse
)
from .ingestion_worker import run_notebook_ingestion
from .telemetry import setup_tracing

logger = logging.getLogger(__name__)

# In-memory tracking for ingestion jobs (use Redis/DB in production)
ingestion_jobs: Dict[str, IngestionJobStatus] = {}
indexed_notebooks: set = set()  # Track completed notebooks

app = FastAPI(title="OneNote RAG", version="1.0.0")
setup_tracing(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize search index on application startup."""
    
    # Fix for Windows async/aiohttp issue
    if os.name == 'nt':  # Windows
        try:
            # Try to set SelectorEventLoop for Windows compatibility with aiohttp
            import asyncio
            if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                logger.info("Set Windows SelectorEventLoop policy for aiohttp compatibility")
        except Exception as e:
            logger.warning(f"Could not set Windows event loop policy: {e}")
    
    try:
        logger.info("Initializing search index...")
        search_client = AISearchClient()
        
        await search_client.ensure_index_exists()
        await search_client.close()
        logger.info("Search index initialization complete")
    except Exception as e:
        logger.error(f"Failed to initialize search index: {str(e)}")
        # Don't fail startup - let the app continue without search functionality


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
    async with RAGOrchestrator(user_assertion=user["access_token"]) as orchestrator:
        if body.mode.lower() == "mcp":
            result = await orchestrator.answer_with_mcp(body.message, scope={
                "notebook_id": body.notebook_id,
                "section_id": body.section_id,
                "page_id": body.page_id,
            })
        else:
            # Use structured filters if provided, otherwise build from legacy fields
            filters = body.filters
            if not filters and (body.notebook_id or body.section_id or body.page_id):
                filters = {}
                if body.notebook_id:
                    filters["notebook_ids"] = [body.notebook_id]
                if body.section_id:
                    filters["section_ids"] = [body.section_id]
                if body.page_id:
                    filters["page_ids"] = [body.page_id]
            
            result = await orchestrator.answer_with_search(
                message=body.message, 
                filters=filters,
                search_mode=body.search_mode or "hybrid"
            )
        
        return ChatResponse(**result)


@app.post("/ingestion", response_model=IngestionJobStatus)
@app.post("/ingest", response_model=IngestionJobStatus)  # Alias for frontend compatibility
async def start_ingestion(body: IngestionJobRequest, background_tasks: BackgroundTasks, user: dict[str, Any] = Depends(auth_validator)):
    if not body.notebook_id:
        return IngestionJobStatus(job_id="n/a", status="failed", message="notebook_id required")
    
    job_id = body.notebook_id
    
    # Initialize job status
    ingestion_jobs[job_id] = IngestionJobStatus(
        job_id=job_id,
        status="running",
        notebook_name=body.notebook_name,
        message=f"Starting ingestion for {body.notebook_name or job_id}",
        progress=0,
        started_at=datetime.now().isoformat()
    )
    
    # Enhanced ingestion with status tracking
    async def enhanced_ingestion_task():
        try:
            # Update progress
            if job_id in ingestion_jobs:
                ingestion_jobs[job_id].message = "Processing notebook content..."
                ingestion_jobs[job_id].progress = 25
            
            result = await run_notebook_ingestion(
                user["access_token"], 
                body.notebook_id,
                body.notebook_name
            )
            
            # Mark as completed
            if job_id in ingestion_jobs:
                ingestion_jobs[job_id].status = "completed"
                ingestion_jobs[job_id].progress = 100
                ingestion_jobs[job_id].message = f"Successfully processed {result.get('summary', {}).get('chunks_created', 0)} chunks"
                ingestion_jobs[job_id].summary = result.get('summary')
                ingestion_jobs[job_id].completed_at = datetime.now().isoformat()
            
            # Add to indexed notebooks set
            indexed_notebooks.add(job_id)
            
            logger.info(f"Ingestion completed: {result}")
            
        except Exception as e:
            # Mark as failed
            if job_id in ingestion_jobs:
                ingestion_jobs[job_id].status = "failed"
                ingestion_jobs[job_id].message = f"Ingestion failed: {str(e)}"
                ingestion_jobs[job_id].completed_at = datetime.now().isoformat()
            logger.error(f"Ingestion failed: {str(e)}")
    
    background_tasks.add_task(enhanced_ingestion_task)
    return ingestion_jobs[job_id]


# New Admin/Management Endpoints

@app.get("/search/facets", response_model=SearchFacetsResponse)
async def get_search_facets(
    query: str = "*",
    user: dict[str, Any] = Depends(auth_validator)
):
    """Get facet information for building search filter UI."""
    async with RAGOrchestrator(user_assertion=user["access_token"]) as orchestrator:
        facets = await orchestrator.get_search_facets(query)
        return SearchFacetsResponse(facets=facets)


@app.get("/search/suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    query: str,
    top: int = 5,
    user: dict[str, Any] = Depends(auth_validator)
):
    """Get search suggestions for autocomplete."""
    async with RAGOrchestrator(user_assertion=user["access_token"]) as orchestrator:
        suggestions = await orchestrator.get_search_suggestions(query, top)
        return SearchSuggestionsResponse(suggestions=suggestions)


@app.post("/search/advanced", response_model=ChatResponse)
async def advanced_search(
    request: AdvancedSearchRequest,
    user: dict[str, Any] = Depends(auth_validator)
):
    """Advanced search with structured filters."""
    async with RAGOrchestrator(user_assertion=user["access_token"]) as orchestrator:
        # Convert Pydantic model to dict if filters are provided
        filters_dict = None
        if request.filters:
            filters_dict = request.filters.dict(exclude_none=True)
        
        result = await orchestrator.answer_with_search(
            message=request.query,
            filters=filters_dict,
            search_mode=request.search_mode or "hybrid"
        )
        
        return ChatResponse(**result)


@app.get("/admin/notebooks")
async def list_all_notebooks(user: dict[str, Any] = Depends(auth_validator)):
    """List all notebooks with enhanced metadata for admin interface."""
    mcp = MCPClient(user_token=user["access_token"])
    notebooks = await mcp.list_notebooks()
    
    # Filter out indexed notebooks
    available_notebooks = [
        nb for nb in notebooks 
        if nb.get('id') not in indexed_notebooks
    ]
    
    return {"value": available_notebooks, "indexed_count": len(indexed_notebooks)}


@app.get("/admin/available-notebooks")
async def get_available_notebooks(user: dict[str, Any] = Depends(auth_validator)):
    """Get notebooks that haven't been indexed yet."""
    try:
        mcp = MCPClient(user_token=user["access_token"])
        notebooks = await mcp.list_notebooks()
        
        logger.info(f"MCP returned {len(notebooks)} notebooks")
        logger.info(f"Currently indexed notebooks: {indexed_notebooks}")
        
        # Filter out indexed notebooks
        available_notebooks = [
            nb for nb in notebooks 
            if nb.get('id') not in indexed_notebooks
        ]
        
        logger.info(f"Available (unindexed) notebooks: {len(available_notebooks)}")
        for nb in available_notebooks[:3]:  # Log first 3 for debugging
            logger.info(f"  - {nb.get('displayName', 'Unknown')} (ID: {nb.get('id', 'Unknown')})")
        
        return available_notebooks
    except Exception as e:
        logger.error(f"Error getting available notebooks: {e}")
        return []


@app.get("/admin/status", response_model=AdminStatsResponse)
@app.get("/admin/stats", response_model=AdminStatsResponse)  # Alias for frontend compatibility
async def get_admin_status(user: dict[str, Any] = Depends(auth_validator)):
    """Get admin dashboard statistics."""
    try:
        # Count active ingestion jobs
        active_jobs = sum(1 for job in ingestion_jobs.values() if job.status == 'running')
        
        # Use tracked data for basic stats (avoid expensive search operations)
        notebook_count = len(indexed_notebooks)
        
        return AdminStatsResponse(
            indexed_notebooks=notebook_count,
            indexed_sections=notebook_count * 5,  # Estimate based on notebooks
            content_chunks=notebook_count * 50,   # Estimate based on notebooks
            processed_attachments=notebook_count * 10,  # Estimate based on notebooks
            active_ingestion_jobs=active_jobs
        )
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        # Return safe defaults if there's an error
        active_jobs = sum(1 for job in ingestion_jobs.values() if job.status == 'running')
        return AdminStatsResponse(
            indexed_notebooks=len(indexed_notebooks),
            indexed_sections=0,
            content_chunks=0,
            processed_attachments=0,
            active_ingestion_jobs=active_jobs
        )


@app.get("/admin/ingestion-status/{job_id}", response_model=IngestionJobStatus)
async def get_ingestion_status(job_id: str, user: dict[str, Any] = Depends(auth_validator)):
    """Get status of specific ingestion job."""
    if job_id not in ingestion_jobs:
        return IngestionJobStatus(
            job_id=job_id,
            status="not_found",
            message="Job not found"
        )
    return ingestion_jobs[job_id]


@app.get("/admin/ingestion-jobs", response_model=List[IngestionJobStatus])
async def list_ingestion_jobs(user: dict[str, Any] = Depends(auth_validator)):
    """List all ingestion jobs with their current status."""
    return list(ingestion_jobs.values())


@app.get("/admin/ingestion/status/{notebook_id}")
async def get_ingestion_status(
    notebook_id: str,
    user: dict[str, Any] = Depends(auth_validator)
):
    """Get ingestion status for a specific notebook (placeholder for real implementation)."""
    # In production, this would query a database or cache for ingestion status
    return {
        "notebook_id": notebook_id,
        "status": "completed",  # This would be dynamic
        "message": "Placeholder status - implement with real tracking"
    }


@app.post("/admin/ingestion/batch")
async def start_batch_ingestion(
    notebook_ids: List[str],
    background_tasks: BackgroundTasks,
    user: dict[str, Any] = Depends(auth_validator)
):
    """Start ingestion for multiple notebooks."""
    batch_id = f"batch_{len(notebook_ids)}_{hash(tuple(notebook_ids)) % 10000}"
    
    async def batch_ingestion_task():
        results = []
        for notebook_id in notebook_ids:
            try:
                result = await run_notebook_ingestion(user["access_token"], notebook_id)
                results.append({"notebook_id": notebook_id, "status": "success", "result": result})
            except Exception as e:
                results.append({"notebook_id": notebook_id, "status": "failed", "error": str(e)})
        
        print(f"Batch ingestion {batch_id} completed: {results}")
    
    background_tasks.add_task(batch_ingestion_task)
    
    return {
        "batch_id": batch_id,
        "status": "running",
        "notebook_count": len(notebook_ids),
        "message": f"Started batch ingestion for {len(notebook_ids)} notebooks"
    }
