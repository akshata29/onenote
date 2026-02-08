#!/usr/bin/env python3
import asyncio
import sys
import os

# Fix for Windows async issue
if os.name == 'nt':  # Windows
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(__file__))

from app.embeddings_client import EmbeddingsClient
from app.search_client import AISearchClient
from app.config import get_settings

async def test_search_upload():
    try:
        print("Testing document upload to search index...")
        
        # Initialize clients
        embedder = EmbeddingsClient()
        search = AISearchClient()
        
        # Ensure index exists
        await search.ensure_index_exists()
        print("✅ Search index ready")
        
        # Generate a test document with embeddings
        test_content = "Test document for verifying vector upload functionality"
        vectors = await embedder.embed([test_content])
        vector = vectors[0]
        
        print(f"✅ Generated embedding: {len(vector)} dimensions")
        
        # Create test document exactly like the ingestion worker does
        test_doc = {
            "id": "test-vector-upload-001",
            "content": test_content,
            "content_vector": vector,
            "title": "Vector Upload Test",
            "page_id": "test-page-001",
            "page_title": "Test Page",
            "section_id": "test-section-001",
            "section_name": "Test Section",
            "notebook_id": "test-notebook-001",
            "notebook_name": "Test Notebook",
            "content_type": "page_text",
            "attachment_filetype": ""
        }
        
        print(f"✅ Created test document")
        print(f"  - ID: {test_doc['id']}")
        print(f"  - Content: {test_doc['content'][:50]}...")
        vector_info = 'None' if test_doc['content_vector'] is None else f'{len(test_doc["content_vector"])} dims'
        print(f"  - Vector: {vector_info}")
        
        # Upload to search index exactly like ingestion worker
        print("Uploading document to search index...")
        result = await search.client.upload_documents([test_doc])
        print(f"✅ Upload complete: {result}")
        
        # Wait a moment for indexing
        await asyncio.sleep(2)
        
        # Search for the document to verify it was indexed
        search_results = await search.client.search(search_text="Vector Upload Test", top=1)
        results = []
        async for item in search_results:
            results.append(item)
        
        if results:
            doc = results[0]
            print(f"✅ Document found in search index:")
            print(f"  - ID: {doc.get('id')}")
            print(f"  - Content: {doc.get('content', '')[:50]}...")
            vector_info = 'None' if doc.get('content_vector') is None else f'{len(doc.get("content_vector", []))} dims'
            print(f"  - Vector: {vector_info}")
            
            if doc.get('content_vector') is None:
                print("❌ ISSUE FOUND: content_vector is None in search result!")
            else:
                print("✅ content_vector is populated correctly")
        else:
            print("❌ Document not found in search results")
        
        # Clean up
        await search.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search_upload())