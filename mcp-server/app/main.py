from typing import Any, Dict, List
from fastapi import Depends, FastAPI, HTTPException

from .auth import auth_dependency
from .graph_client import GraphClient
from .config import get_settings
from .chunking import paragraph_chunks

app = FastAPI(title="OneNote MCP Server", version="1.0.0")


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/notebooks")
async def list_notebooks(user=Depends(auth_dependency)):
    async with GraphClient(user_assertion=user["__raw"]) as graph:
        items = await graph.list_notebooks()
        return {"value": items}


@app.get("/notebooks/{notebook_id}/sections")
async def list_sections(notebook_id: str, user=Depends(auth_dependency)):
    async with GraphClient(user_assertion=user["__raw"]) as graph:
        items = await graph.list_sections(notebook_id)
        return {"value": items}


@app.get("/sections/{section_id}/pages")
async def list_pages(section_id: str, user=Depends(auth_dependency)):
    async with GraphClient(user_assertion=user["__raw"]) as graph:
        items = await graph.list_pages(section_id)
        return {"value": items}


@app.get("/pages/{page_id}")
async def get_page(page_id: str, user=Depends(auth_dependency)):
    async with GraphClient(user_assertion=user["__raw"]) as graph:
        content = await graph.get_page_content(page_id)
        return content


@app.get("/pages/{page_id}/resources")
async def list_page_resources(page_id: str, user=Depends(auth_dependency)):
    async with GraphClient(user_assertion=user["__raw"]) as graph:
        items = await graph.list_resources(page_id)
        return {"value": items}


@app.get("/resources/content")
async def get_resource_content(resource_url: str, user=Depends(auth_dependency)):
    async with GraphClient(user_assertion=user["__raw"]) as graph:
        data = await graph.download_resource(resource_url)
        return {"length": len(data), "content_base64": data.decode("latin1")}


@app.post("/search")
async def search(body: Dict[str, Any], user=Depends(auth_dependency)):
    query = body.get("query", "")
    scope = body.get("scope") or {}
    settings = get_settings()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    results: List[Dict[str, Any]] = []
    async with GraphClient(user_assertion=user["__raw"]) as graph:
        notebooks = [scope["notebook_id"]] if scope.get("notebook_id") else []
        if not notebooks:
            nb_items = await graph.list_notebooks()
            notebooks = [n["id"] for n in nb_items]
        for nb_id in notebooks:
            sections = [scope["section_id"]] if scope.get("section_id") else []
            if not sections:
                sec_items = await graph.list_sections(nb_id)
                sections = [s["id"] for s in sec_items]
            for sec_id in sections:
                pages = await graph.list_pages(sec_id)
                for page in pages[: settings.max_pages_sample]:
                    page_id = page.get("id")
                    title = page.get("title")
                    content = await graph.get_page_content(page_id)
                    text = content.get("text", "")
                    chunks = paragraph_chunks(text, settings.chunk_size, settings.chunk_overlap)
                    for ch in chunks:
                        snippet = ch["content"]
                        if query.lower() in snippet.lower():
                            results.append(
                                {
                                    "page_id": page_id,
                                    "page_title": title,
                                    "snippet": snippet[:600],
                                    "section_id": sec_id,
                                    "notebook_id": nb_id,
                                }
                            )
                    if settings.include_attachments:
                        try:
                            resources = await graph.list_resources(page_id)
                            for res in resources:
                                res_url = res.get("@odata.id") or res.get("contentUrl") or res.get("self")
                                if not res_url:
                                    continue
                                try:
                                    data = await graph.download_resource(res_url)
                                    # naive text attempt; keep as latin1 fallback
                                    text_blob = data.decode(errors="ignore")
                                    if query.lower() in text_blob.lower():
                                        results.append(
                                            {
                                                "page_id": page_id,
                                                "page_title": title,
                                                "snippet": text_blob[:400],
                                                "resource_url": res_url,
                                                "section_id": sec_id,
                                                "notebook_id": nb_id,
                                                "source_type": "attachment",
                                            }
                                        )
                                except Exception:
                                    continue
                        except Exception:
                            # Skip resource processing if page doesn't have resources or access is denied
                            continue
        return {"results": results}


@app.post("/extract")
async def extract_content(body: Dict[str, Any], user=Depends(auth_dependency)):
    """Extract all content from specified scope for LLM context"""
    scope = body.get("scope") or {}
    settings = get_settings()
    
    content_items: List[Dict[str, Any]] = []
    async with GraphClient(user_assertion=user["__raw"]) as graph:
        notebooks = [scope["notebook_id"]] if scope.get("notebook_id") else []
        if not notebooks:
            nb_items = await graph.list_notebooks()
            notebooks = [n["id"] for n in nb_items]
        
        for nb_id in notebooks:
            sections = [scope["section_id"]] if scope.get("section_id") else []
            if not sections:
                sec_items = await graph.list_sections(nb_id)
                sections = [s["id"] for s in sec_items]
            
            for sec_id in sections:
                pages = await graph.list_pages(sec_id)
                for page in pages[: settings.max_pages_sample]:
                    page_id = page.get("id")
                    title = page.get("title")
                    content = await graph.get_page_content(page_id)
                    text = content.get("text", "")
                    
                    content_items.append({
                        "page_id": page_id,
                        "page_title": title,
                        "content": text,
                        "section_id": sec_id,
                        "notebook_id": nb_id,
                    })
    
    return {"content": content_items}
