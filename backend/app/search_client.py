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
            # If index doesn't exist yet, return empty facets rather than failing
            if "was not found" in str(e):
                logger.warning("Search index not found - returning empty facets")
            return {}
    
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
