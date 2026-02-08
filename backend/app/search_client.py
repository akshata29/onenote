from typing import Any, Dict, List, Optional
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex, SimpleField, SearchableField, SearchField, VectorSearch, HnswAlgorithmConfiguration, VectorSearchProfile, SemanticConfiguration, SemanticField, SemanticPrioritizedFields, SemanticSearch
from azure.search.documents import SearchItemPaged
from azure.search.documents.models import VectorizedQuery, QueryType
from azure.core.credentials import AzureKeyCredential
import logging

from .config import get_settings

logger = logging.getLogger(__name__)


class AISearchClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        api_key = self.settings.search_api_key
        self.client = SearchClient(
            endpoint=self.settings.search_endpoint,
            index_name=self.settings.search_index,
            credential=AzureKeyCredential(api_key),
        )
        
        # Index management client
        self.index_client = SearchIndexClient(
            endpoint=self.settings.search_endpoint,
            credential=AzureKeyCredential(api_key)
        )

    async def ensure_index_exists(self):
        """
        Check if the search index exists and create it if it doesn't.
        """
        try:
            # Try to get the index
            await self.index_client.get_index(self.settings.search_index)
            logger.info(f"Search index '{self.settings.search_index}' exists")
        except Exception:
            logger.info(f"Creating search index '{self.settings.search_index}'")
            await self._create_index()

    async def _create_index(self):
        """
        Create the search index with the proper schema.
        """
        # Define the search index schema
        fields = [
            SimpleField(name="id", type="Edm.String", key=True),
            SearchableField(name="content", type="Edm.String", analyzer_name="standard.lucene"),
            SearchableField(name="title", type="Edm.String", analyzer_name="standard.lucene"),
            SimpleField(name="notebook_id", type="Edm.String", facetable=True, filterable=True),
            SimpleField(name="notebook_name", type="Edm.String", facetable=True, filterable=True),
            SimpleField(name="section_id", type="Edm.String", facetable=True, filterable=True),
            SimpleField(name="section_name", type="Edm.String", facetable=True, filterable=True),
            SimpleField(name="page_id", type="Edm.String", facetable=True, filterable=True),
            SimpleField(name="page_title", type="Edm.String", facetable=True, filterable=True),
            SimpleField(name="content_type", type="Edm.String", facetable=True, filterable=True),
            SimpleField(name="attachment_filetype", type="Edm.String", facetable=True, filterable=True),
            SearchField(
                name="content_vector", 
                type="Collection(Edm.Single)",
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="default-profile"
            )
        ]

        # Configure vector search
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(name="default-hnsw")
            ],
            profiles=[
                VectorSearchProfile(
                    name="default-profile",
                    algorithm_configuration_name="default-hnsw"
                )
            ]
        )

        # Configure semantic search if enabled
        semantic_search = None
        if self.settings.enable_semantic_ranking:
            semantic_search = SemanticSearch(
                configurations=[
                    SemanticConfiguration(
                        name="default",
                        prioritized_fields=SemanticPrioritizedFields(
                            title_field=SemanticField(field_name="title"),
                            content_fields=[SemanticField(field_name="content")]
                        )
                    )
                ]
            )

        # Create the index
        index = SearchIndex(
            name=self.settings.search_index,
            fields=fields,
            vector_search=vector_search,
            semantic_search=semantic_search
        )

        await self.index_client.create_index(index)
        logger.info(f"Successfully created search index '{self.settings.search_index}'")

    async def close(self):
        """Close the clients."""
        await self.client.close()
        await self.index_client.close()
    
    async def delete_notebook_documents(self, notebook_id: str) -> Dict[str, Any]:
        """
        Delete all documents for a specific notebook from the search index.
        
        Args:
            notebook_id: The notebook ID to delete documents for
            
        Returns:
            Dict with deletion statistics
        """
        try:
            logger.info(f"Searching for documents to delete with notebook_id: '{notebook_id}'")
            
            # First, let's see what documents exist in the index
            all_docs_results = await self.client.search(
                search_text="*",
                select=["id", "notebook_id", "notebook_name", "content_type"],
                top=50
            )
            
            logger.info("Sample documents in index:")
            async for doc in all_docs_results:
                logger.info(f"  ID: {doc['id']}, notebook_id: '{doc.get('notebook_id')}', name: '{doc.get('notebook_name')}', type: {doc.get('content_type')}")
            
            # Search for all documents with the notebook_id
            search_results = await self.client.search(
                search_text="*",
                filter=f"notebook_id eq '{notebook_id}'",
                select=["id", "notebook_id", "notebook_name"],
                top=10000  # Get all documents for this notebook
            )
            
            # Collect document IDs to delete
            doc_ids = []
            async for result in search_results:
                logger.info(f"Found document to delete: {result['id']} (notebook_id: '{result.get('notebook_id')}')")
                doc_ids.append(result["id"])
            
            logger.info(f"Total documents found for notebook {notebook_id}: {len(doc_ids)}")
            
            if not doc_ids:
                logger.info(f"No documents found for notebook {notebook_id}")
                return {
                    "success": True,
                    "deleted_count": 0,
                    "message": "No documents found to delete"
                }
            
            # Delete documents in batches
            batch_size = 1000
            total_deleted = 0
            
            for i in range(0, len(doc_ids), batch_size):
                batch = doc_ids[i:i + batch_size]
                delete_docs = [{"id": doc_id} for doc_id in batch]
                
                await self.client.delete_documents(delete_docs)
                total_deleted += len(batch)
                logger.info(f"Deleted batch of {len(batch)} documents for notebook {notebook_id}")
            
            logger.info(f"Successfully deleted {total_deleted} documents for notebook {notebook_id}")
            return {
                "success": True,
                "deleted_count": total_deleted,
                "message": f"Successfully deleted {total_deleted} documents"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete documents for notebook {notebook_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "deleted_count": 0
            }
    
    async def get_document_count_by_notebook(self, notebook_id: str) -> int:
        """
        Get the count of documents for a specific notebook.
        
        Args:
            notebook_id: The notebook ID to count documents for
            
        Returns:
            Number of documents in the index for this notebook
        """
        try:
            search_results = await self.client.search(
                search_text="*",
                filter=f"notebook_id eq '{notebook_id}'",
                select=["id"],
                include_total_count=True,
                top=0  # We only want the count
            )
            
            # Count the results manually since include_total_count might not work as expected
            count = 0
            async for _ in search_results:
                count += 1
                
            return count
            
        except Exception as e:
            logger.error(f"Failed to count documents for notebook {notebook_id}: {str(e)}")
            return 0

    async def search(
        self, 
        query: str, 
        vector: List[float] | None, 
        filters: str | None = None, 
        top: int = 8,
        search_mode: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        """
        Enhanced search with multiple search modes and better filtering.
        """
        try:
            vector_query = None
            if vector is not None:
                vector_query = VectorizedQuery(
                    vector=vector,
                    k_nearest_neighbors=top,
                    fields="content_vector",
                    kind="vector"
                )

            # Determine query type based on search mode
            query_type = None
            if search_mode == "semantic" and self.settings.enable_semantic_ranking:
                query_type = QueryType.SEMANTIC
            elif search_mode == "simple":
                query_type = QueryType.SIMPLE
            elif search_mode == "full":
                query_type = QueryType.FULL

            search_params = {
                "search_text": query,
                "filter": filters,
                "top": top,
                "query_type": query_type,
            }

            # Add vector query if available
            if vector_query:
                search_params["vector_queries"] = [vector_query]

            # Add semantic configuration if enabled
            if self.settings.enable_semantic_ranking and search_mode in ["hybrid", "semantic"]:
                search_params["semantic_configuration_name"] = self.settings.ai_search_semantic_config

            results: SearchItemPaged[Any] = await self.client.search(**search_params)
            
            hits: List[Dict[str, Any]] = []
            async for item in results:
                doc = item.copy()
                doc["score"] = item.get("@search.score")
                doc["rerankerScore"] = item.get("@search.rerankerScore")
                hits.append(doc)
            
            return hits

        except Exception as e:
            logger.error(f"Search query failed: {str(e)}")
            return []
    
    def build_filter_query(
        self,
        notebook_ids: List[str] = None,
        section_ids: List[str] = None,
        page_ids: List[str] = None,
        content_types: List[str] = None,
        date_range: Dict[str, str] = None,
        attachment_types: List[str] = None,
        has_attachments: bool = None
    ) -> str:
        """
        Build OData filter query from search parameters.
        
        Args:
            notebook_ids: List of notebook IDs to filter by
            section_ids: List of section IDs to filter by  
            page_ids: List of page IDs to filter by
            content_types: List of content types ('page_text', 'attachment')
            date_range: Dict with 'start' and 'end' dates in ISO format
            attachment_types: List of attachment file types ('pdf', 'docx', etc.)
            has_attachments: Filter by whether content has attachments
        
        Returns:
            OData filter string
        """
        filters = []
        
        # Notebook filter
        if notebook_ids:
            notebook_filter = " or ".join([f"notebook_id eq '{nid}'" for nid in notebook_ids])
            filters.append(f"({notebook_filter})")
        
        # Section filter
        if section_ids:
            section_filter = " or ".join([f"section_id eq '{sid}'" for sid in section_ids])
            filters.append(f"({section_filter})")
        
        # Page filter
        if page_ids:
            page_filter = " or ".join([f"page_id eq '{pid}'" for pid in page_ids])
            filters.append(f"({page_filter})")
        
        # Content type filter
        if content_types:
            type_filter = " or ".join([f"content_type eq '{ct}'" for ct in content_types])
            filters.append(f"({type_filter})")
        
        # Date range filter
        if date_range:
            if date_range.get("start"):
                filters.append(f"created_date ge '{date_range['start']}'")
            if date_range.get("end"):
                filters.append(f"created_date le '{date_range['end']}'")
        
        # Attachment type filter
        if attachment_types:
            att_filter = " or ".join([f"attachment_filetype eq '{at}'" for at in attachment_types])
            filters.append(f"({att_filter})")
        
        # Has attachments filter
        if has_attachments is not None:
            filters.append(f"has_attachments eq {str(has_attachments).lower()}")
        
        return " and ".join(filters) if filters else None
    
    async def get_facets(self, query: str = "*", facet_fields: List[str] = None) -> Dict[str, List[Dict]]:
        """
        Get facet counts for filtering options.
        """
        if not facet_fields:
            facet_fields = [
                "notebook_name",
                "section_name", 
                "content_type",
                "attachment_filetype"
            ]
        
        try:
            results = await self.client.search(
                search_text=query,
                facets=facet_fields,
                top=0  # We only want facets, not results
            )
            
            facets = {}
            if hasattr(results, 'get_facets'):
                facet_data = await results.get_facets()
                for field in facet_fields:
                    facet_results = facet_data.get(field, [])
                    facets[field] = [
                        {"value": item["value"], "count": item["count"]}
                        for item in facet_results
                    ]
            
            return facets
            
        except Exception as e:
            logger.error(f"Facet query failed: {str(e)}")
            return {}

    async def get_indexed_notebook_ids(self) -> set[str]:
        """
        Get the list of notebook IDs that are currently indexed in Azure AI Search.
        """
        try:
            # Use a simple approach - get unique notebook_ids by searching and aggregating
            results = await self.client.search(
                search_text="*",
                select=["notebook_id"],
                top=10000  # Get all results to count unique notebook IDs
            )
            
            indexed_ids = set()
            async for result in results:
                notebook_id = result.get("notebook_id")
                if notebook_id:
                    indexed_ids.add(notebook_id)
            
            logger.info(f"Found {len(indexed_ids)} indexed notebooks in AI Search: {list(indexed_ids)}")
            return indexed_ids
            
        except Exception as e:
            logger.error(f"Failed to get indexed notebook IDs: {str(e)}")
            return set()
    
    async def get_search_suggestions(self, query: str, top: int = 5) -> List[str]:
        """
        Get search suggestions based on indexed content using simple search.
        """
        try:
            # Use simple search to find relevant content for suggestions
            search_results = await self.client.search(
                search_text=query,
                top=top * 2,  # Get more results to extract diverse suggestions
                query_type=QueryType.SIMPLE,
                search_fields=["title", "content"],
                select=["title", "content"]
            )
            
            suggestions = []
            seen_terms = set()
            
            async for result in search_results:
                # Extract meaningful phrases from titles and content
                title = result.get("title", "")
                content = result.get("content", "")[:200]  # First 200 chars
                
                # Simple suggestion extraction
                for text in [title, content]:
                    if text and len(text.strip()) > 10:
                        # Clean and limit suggestion length
                        suggestion = text.strip()[:60]
                        if suggestion.lower() not in seen_terms and suggestion not in suggestions:
                            suggestions.append(suggestion)
                            seen_terms.add(suggestion.lower())
                            
                        if len(suggestions) >= top:
                            break
                
                if len(suggestions) >= top:
                    break
            
            return suggestions[:top]
            
        except Exception as e:
            logger.error(f"Suggestions query failed: {str(e)}")
            # Return simple query-based suggestions as fallback
            return [
                f"{query} in documents",
                f"Search for {query}",
                f"{query} related content"
            ][:top]
