from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class Notebook(BaseModel):
    id: str
    displayName: str


class Section(BaseModel):
    id: str
    displayName: str
    notebook_id: Optional[str] = None


class Page(BaseModel):
    id: str
    title: str
    content_url: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    mode: str  # "mcp" or "search"
    notebook_id: Optional[str] = None
    section_id: Optional[str] = None
    page_id: Optional[str] = None
    # Enhanced search parameters
    search_mode: Optional[str] = "hybrid"  # "hybrid", "semantic", "simple", "full"
    filters: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    answer: str
    citations: List[dict]
    mode: str
    search_mode: Optional[str] = None
    filter_applied: Optional[bool] = None
    total_results: Optional[int] = None


class SearchFilters(BaseModel):
    """Enhanced search filters for RAG queries."""
    notebook_ids: Optional[List[str]] = None
    section_ids: Optional[List[str]] = None
    page_ids: Optional[List[str]] = None
    content_types: Optional[List[str]] = None  # ["page_text", "attachment"]
    date_range: Optional[Dict[str, str]] = None  # {"start": "2024-01-01", "end": "2024-12-31"}
    attachment_types: Optional[List[str]] = None  # ["pdf", "docx", "xlsx"]
    has_attachments: Optional[bool] = None


class AdvancedSearchRequest(BaseModel):
    """Request model for advanced search with filters."""
    query: str
    filters: Optional[SearchFilters] = None
    search_mode: Optional[str] = "hybrid"
    top: Optional[int] = 8


class IngestionJobRequest(BaseModel):
    notebook_id: Optional[str] = None
    notebook_name: Optional[str] = None
    enable_attachment_processing: Optional[bool] = True


class IngestionJobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    progress: Optional[int] = None  # 0-100
    notebook_name: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class SearchFacetsResponse(BaseModel):
    """Search facets for building filter UI."""
    facets: Dict[str, List[Dict[str, Any]]]


class SearchSuggestionsResponse(BaseModel):
    """Search suggestions for autocomplete."""
    suggestions: List[str]


class IngestionSummaryResponse(BaseModel):
    """Summary of ingestion results."""
    pages_processed: int
    attachments_processed: int
    chunks_created: int
    errors: int
    start_time: str
    end_time: str
    duration_seconds: float
    batch_id: str
    success: bool


class AdminStatsResponse(BaseModel):
    """Admin dashboard statistics."""
    indexed_notebooks: int
    indexed_sections: int 
    content_chunks: int
    processed_attachments: int
    active_ingestion_jobs: int
