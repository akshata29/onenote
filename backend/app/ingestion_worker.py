import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import hashlib
import json

from .graph_client import GraphOneNoteClient
from .chunking import paragraph_chunks
from .embeddings_client import EmbeddingsClient
from .search_client import AISearchClient
from .document_intelligence_client import DocumentIntelligenceClient
from .config import get_settings

logger = logging.getLogger(__name__)


class IngestionWorker:
    def __init__(self, user_assertion: str):
        self.graph = GraphOneNoteClient(user_assertion)
        self.embedder = EmbeddingsClient()
        self.search = AISearchClient()
        self.doc_intelligence = DocumentIntelligenceClient()
        self.settings = get_settings()
        self.user_assertion = user_assertion
        
        # Track ingestion statistics
        self.stats = {
            "pages_processed": 0,
            "attachments_processed": 0,
            "chunks_created": 0,
            "errors": 0,
            "start_time": datetime.now(timezone.utc)
        }

    async def close(self):
        """Clean up resources.""" 
        await self.search.close()

    async def ingest_notebook(self, notebook_id: str, notebook_name: str = None) -> Dict[str, Any]:
        """
        Ingest a complete notebook with enhanced metadata and attachment processing.
        """
        try:
            logger.info(f"Starting ingestion for notebook {notebook_id}")
            
            sections = await self.graph.list_sections(notebook_id)
            
            for section in sections:
                await self.ingest_section(
                    section_id=section["id"], 
                    notebook_id=notebook_id,
                    notebook_name=notebook_name or "Unknown Notebook",
                    section_name=section.get("displayName", "Unknown Section")
                )
            
            return self._get_ingestion_summary()
            
        except Exception as e:
            logger.error(f"Failed to ingest notebook {notebook_id}: {str(e)}")
            self.stats["errors"] += 1
            raise

    async def ingest_section(
        self, 
        section_id: str, 
        notebook_id: str, 
        notebook_name: str,
        section_name: str | None = None
    ) -> None:
        """
        Ingest a section with all its pages and attachments.
        """
        try:
            logger.info(f"Ingesting section {section_id}")
            
            pages = await self.graph.list_pages(section_id)
            
            for page in pages:
                await self.ingest_page(
                    page_id=page["id"],
                    notebook_id=notebook_id,
                    notebook_name=notebook_name,
                    section_id=section_id,
                    section_name=section_name,
                    page_title=page.get("title", "Untitled Page"),
                    page_created_time=page.get("createdDateTime"),
                    page_modified_time=page.get("lastModifiedDateTime")
                )
                
        except Exception as e:
            logger.error(f"Failed to ingest section {section_id}: {str(e)}")
            self.stats["errors"] += 1
            raise

    async def ingest_page(
        self, 
        page_id: str, 
        notebook_id: str,
        notebook_name: str,
        section_id: str, 
        section_name: str | None,
        page_title: str | None, 
        page_created_time: str | None = None,
        page_modified_time: str | None = None
    ) -> None:
        """
        Ingest a page with enhanced metadata and process any attachments.
        """
        try:
            logger.info(f"Ingesting page {page_id}: {page_title}")
            
            # Get page content
            page_content = await self.graph.get_page_content(page_id)
            text = page_content.get("text", "")
            html = page_content.get("html", "")
            
            # Parse created/modified times
            created_time = self._parse_iso_datetime(page_created_time) if page_created_time else None
            modified_time = self._parse_iso_datetime(page_modified_time) if page_modified_time else None
            
            # Process page text content
            if text.strip():
                await self._process_text_content(
                    content=text,
                    page_id=page_id,
                    notebook_id=notebook_id,
                    notebook_name=notebook_name,
                    section_id=section_id,
                    section_name=section_name,
                    page_title=page_title,
                    created_time=created_time,
                    modified_time=modified_time,
                    content_type="page_text"
                )
            
            # Process attachments if enabled
            if self.settings.enable_attachment_processing:
                logger.info(f"Attachment processing is ENABLED for page {page_id}")
                await self._process_page_attachments(
                    page_id=page_id,
                    notebook_id=notebook_id,
                    notebook_name=notebook_name,
                    section_id=section_id,
                    section_name=section_name,
                    page_title=page_title,
                    created_time=created_time,
                    modified_time=modified_time
                )
            else:
                logger.warning(f"Attachment processing is DISABLED for page {page_id}")
            
            self.stats["pages_processed"] += 1
            
        except Exception as e:
            logger.error(f"Failed to ingest page {page_id}: {str(e)}")
            self.stats["errors"] += 1
            raise

    async def _process_text_content(
        self,
        content: str,
        page_id: str,
        notebook_id: str,
        notebook_name: str,
        section_id: str,
        section_name: str,
        page_title: str,
        created_time: datetime = None,
        modified_time: datetime = None,
        content_type: str = "page_text",
        attachment_metadata: Dict = None
    ) -> None:
        """
        Process and chunk text content for indexing.
        """
        if not content.strip():
            return
        
        # Create chunks
        chunks = paragraph_chunks(content, self.settings.chunk_size, self.settings.chunk_overlap)
        if not chunks:
            return
        
        # Generate embeddings
        contents = [c["content"] for c in chunks]
        vectors = await self.embedder.embed(contents)
        
        # Create search documents with enhanced metadata
        docs: List[Dict] = []
        current_time = datetime.now(timezone.utc)
        
        for idx, chunk in enumerate(chunks):
            doc_id = self._generate_document_id(page_id, content_type, idx)
            
            # Validate vector before using it
            vector = vectors[idx]
            if not isinstance(vector, list):
                logger.error(f"Invalid vector at index {idx}: expected list, got {type(vector)}")
                vector = [0.0] * 1536  # Fallback to zero vector
            elif len(vector) != 1536:
                logger.error(f"Invalid vector length at index {idx}: expected 1536, got {len(vector)}")
                vector = [0.0] * 1536  # Fallback to zero vector
            
            # Handle attachment-specific fields
            attachment_filename = ""
            attachment_filetype = ""
            document_title = page_title or "Untitled"
            enhanced_content = chunk["content"]
            
            if attachment_metadata:
                attachment_filename = attachment_metadata.get("attachment_filename", "")
                attachment_filetype = attachment_metadata.get("attachment_filetype", "")
                
                # For attachments, enhance title and content for better searchability
                if attachment_filename:
                    document_title = f"{attachment_filename} - {page_title or 'Untitled'}"
                    # Add filename as searchable text at the beginning of content
                    enhanced_content = f"ATTACHMENT: {attachment_filename}\n\n{chunk['content']}"
            
            base_doc = {
                "id": doc_id,
                "content": enhanced_content,  # Include filename in content for attachments
                "content_vector": vector,
                "title": document_title,  # Include filename in title for attachments
                "page_id": page_id,
                "page_title": page_title or "",
                "section_id": section_id,
                "section_name": section_name or "",
                "notebook_id": notebook_id,
                "notebook_name": notebook_name or "",
                "content_type": content_type,
                "attachment_filetype": attachment_filetype,
            }
            
            docs.append(base_doc)
        
        # Upload to search index
        await self.search.client.upload_documents(docs)
        self.stats["chunks_created"] += len(docs)
        
        logger.info(f"Processed {len(docs)} chunks for {content_type} content of page {page_id}")
    
    async def _process_page_attachments(
        self,
        page_id: str,
        notebook_id: str,
        notebook_name: str,
        section_id: str,
        section_name: str,
        page_title: str,
        created_time: datetime = None,
        modified_time: datetime = None
    ) -> None:
        """
        Process all attachments for a given page.
        """
        try:
            logger.info(f"\n🔍 INGESTION DEBUG: Starting attachment processing for page {page_id} ({page_title})")
            
            # Get attachments from the page
            attachments = await self.graph.list_page_attachments(page_id)
            
            logger.info(f"📊 INGESTION DEBUG: Found {len(attachments)} attachments for page {page_id} ({page_title})")
            
            if attachments:
                logger.info(f"📋 INGESTION DEBUG: Attachment details:")
                for i, att in enumerate(attachments):
                    logger.info(f"   {i+1}. Name: {att.get('name', 'unknown')}, Type: {att.get('contentType', 'unknown')}, Size: {att.get('size', 0)} bytes")
            else:
                logger.warning(f"❌ INGESTION DEBUG: NO ATTACHMENTS FOUND for page {page_id}! This might indicate:")
                logger.warning(f"   - HTML parsing patterns are incorrect for OneNote structure")
                logger.warning(f"   - Attachments are embedded differently than expected")
                logger.warning(f"   - Page actually has no attachments (unlikely based on user report)")
                return
            
            logger.info(f"Processing {len(attachments)} attachments for page {page_id}")
            
            for i, attachment in enumerate(attachments):
                logger.info(f"Processing attachment {i+1}/{len(attachments)}: {attachment.get('name', 'unknown')}")
                try:
                    await self._process_single_attachment(
                        attachment=attachment,
                        page_id=page_id,
                        notebook_id=notebook_id,
                        notebook_name=notebook_name,
                        section_id=section_id,
                        section_name=section_name,
                        page_title=page_title,
                        created_time=created_time,
                        modified_time=modified_time
                    )
                except Exception as e:
                    logger.error(f"Failed to process attachment {attachment.get('name', 'unknown')}: {str(e)}", exc_info=True)
                    self.stats["errors"] += 1
                    
        except Exception as e:
            logger.error(f"Failed to get attachments for page {page_id}: {str(e)}", exc_info=True)
    
    async def _process_single_attachment(
        self,
        attachment: Dict,
        page_id: str,
        notebook_id: str,
        notebook_name: str,
        section_id: str,
        section_name: str,
        page_title: str,
        created_time: datetime = None,
        modified_time: datetime = None
    ) -> None:
        """
        Process a single attachment using Document Intelligence.
        """
        try:
            attachment_name = attachment.get("name", "unknown")
            attachment_id = attachment.get("id")
            
            # Check file size limit
            file_size = attachment.get("size", 0)
            max_size_bytes = self.settings.max_attachment_size_mb * 1024 * 1024
            
            if file_size > max_size_bytes:
                logger.warning(f"Attachment {attachment_name} too large ({file_size} bytes), skipping")
                return
            
            # Download attachment content
            attachment_content = await self.graph.get_attachment_content(page_id, attachment_id)
            if not attachment_content:
                logger.warning(f"Could not download attachment {attachment_name}")
                return
            
            # Process with Document Intelligence
            logger.info(f"📄 Processing {attachment_name} with Document Intelligence...")
            logger.info(f"   File size: {file_size} bytes")
            logger.info(f"   Content type: {attachment.get('contentType', 'unknown')}")
            
            analysis_result = await self.doc_intelligence.analyze_document(
                file_content=attachment_content,
                filename=attachment_name,
                content_type=attachment.get("contentType")
            )
            
            logger.info(f"📊 Document Intelligence result for {attachment_name}:")
            logger.info(f"   Success: {analysis_result.get('success', False)}")
            logger.info(f"   Content length: {len(analysis_result.get('content', ''))}")
            logger.info(f"   Error: {analysis_result.get('error', 'None')}")
            
            if not analysis_result.get("success"):
                logger.error(f"❌ Document Intelligence failed for {attachment_name}: {analysis_result.get('error')}")
                # Don't return - try to continue processing other attachments
                self.stats["errors"] += 1
                return
            
            # Extract content and metadata
            extracted_content = analysis_result.get("content", "")
            metadata = analysis_result.get("metadata", {})
            
            if extracted_content.strip():
                # Process extracted content
                await self._process_text_content(
                    content=extracted_content,
                    page_id=page_id,
                    notebook_id=notebook_id,
                    notebook_name=notebook_name,
                    section_id=section_id,
                    section_name=section_name,
                    page_title=page_title,
                    created_time=created_time,
                    modified_time=modified_time,
                    content_type="attachment",
                    attachment_metadata=metadata
                )
                
                self.stats["attachments_processed"] += 1
                logger.info(f"Successfully processed attachment {attachment_name}")
            
        except Exception as e:
            logger.error(f"Failed to process attachment {attachment.get('name', 'unknown')}: {str(e)}")
            raise
    
    def _generate_document_id(self, page_id: str, content_type: str, chunk_index: int) -> str:
        """Generate a unique document ID."""
        base_id = f"{page_id}-{content_type}-{chunk_index}"
        # Create a hash to ensure uniqueness and consistent length
        return hashlib.md5(base_id.encode()).hexdigest()[:16] + f"-{chunk_index}"
    
    def _get_batch_id(self) -> str:
        """Generate a unique batch ID for this ingestion session."""
        if not hasattr(self, "_batch_id"):
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            self._batch_id = f"batch_{timestamp}_{id(self)}"
        return self._batch_id
    
    def _parse_iso_datetime(self, iso_string: str) -> Optional[datetime]:
        """Parse ISO datetime string."""
        try:
            return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    def _get_ingestion_summary(self) -> Dict[str, Any]:
        """Get summary of ingestion statistics."""
        end_time = datetime.now(timezone.utc)
        duration = end_time - self.stats["start_time"]
        
        return {
            "summary": {
                "pages_processed": self.stats["pages_processed"],
                "attachments_processed": self.stats["attachments_processed"],
                "chunks_created": self.stats["chunks_created"],
                "errors": self.stats["errors"],
                "start_time": self.stats["start_time"].isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration.total_seconds(),
                "batch_id": self._get_batch_id()
            },
            "success": self.stats["errors"] == 0
        }

    async def close(self) -> None:
        await self.graph.close()
        await self.search.client.close()
        if self.doc_intelligence:
            await self.doc_intelligence.close()


async def run_notebook_ingestion(user_assertion: str, notebook_id: str, notebook_name: str = None) -> Dict[str, Any]:
    """
    Run enhanced notebook ingestion with comprehensive statistics and error handling.
    """
    worker = IngestionWorker(user_assertion)
    try:
        result = await worker.ingest_notebook(notebook_id, notebook_name)
        return result
    finally:
        await worker.close()
