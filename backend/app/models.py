from typing import List, Optional
from pydantic import BaseModel


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


class ChatResponse(BaseModel):
    answer: str
    citations: List[dict]
    mode: str


class IngestionJobRequest(BaseModel):
    notebook_id: Optional[str] = None


class IngestionJobStatus(BaseModel):
    job_id: str
    status: str
    message: Optional[str] = None
