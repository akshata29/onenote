#!/usr/bin/env python3
import asyncio
import sys
import os
import json

# Fix for Windows async issue
if os.name == 'nt':  # Windows
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(__file__))

from app.embeddings_client import EmbeddingsClient
from app.search_client import AISearchClient
from app.config import get_settings

async def debug_document_upload():
    try:
        print("=== Debugging Document Upload Field Types ===")
        
        # Initialize clients
        embedder = EmbeddingsClient()
        search = AISearchClient()
        
        # Generate a test document with embeddings like real ingestion
        test_content = "Test document for debugging field type issues"
        vectors = await embedder.embed([test_content])
        vector = vectors[0]
        
        print(f"✅ Generated embedding: type={type(vector)}, length={len(vector)}")
        print(f"   First 3 values: {vector[:3]}")
        
        # Create test document EXACTLY like ingestion worker
        doc = {
            "id": "debug-test-001",
            "content": test_content,
            "content_vector": vector,
            "title": "Debug Test",
            "page_id": "debug-page-001", 
            "page_title": "Debug Page",
            "section_id": "debug-section-001",
            "section_name": "Debug Section",
            "notebook_id": "debug-notebook-001",
            "notebook_name": "Debug Notebook",
            "content_type": "page_text",
            "attachment_filetype": ""
        }
        
        print("\n=== Document Field Analysis ===")
        for field, value in doc.items():
            print(f"{field:20}: type={type(value).__name__:10} | value={repr(str(value)[:50])}")
            if field == "content_vector":
                print(f"                     length={len(value) if isinstance(value, (list, tuple)) else 'N/A'}")
                if isinstance(value, list) and len(value) > 0:
                    print(f"                     first_elem_type={type(value[0]).__name__}")
        
        print(f"\n=== JSON Serialization Test ===")
        try:
            json_str = json.dumps(doc, ensure_ascii=False)
            print(f"✅ JSON serialization successful, size: {len(json_str)} chars")
        except Exception as e:
            print(f"❌ JSON serialization failed: {e}")
            return
        
        print(f"\n=== Azure Search Upload Test ===")
        try:
            print("Attempting upload to Azure AI Search...")
            result = await search.client.upload_documents([doc])
            print(f"✅ Upload successful: {result}")
            
            # Wait for indexing
            await asyncio.sleep(2)
            
            # Try to retrieve the document
            search_results = await search.client.search(search_text="Debug Test", top=1)
            results = []
            async for item in search_results:
                results.append(item)
            
            if results:
                found_doc = results[0]
                print(f"✅ Document found in search index")
                vector_info = 'None' if found_doc.get('content_vector') is None else f'{len(found_doc.get("content_vector", []))} dims'
                print(f"   content_vector: {vector_info}")
            else:
                print("⚠️  Document not found in search results (might need more time to index)")
                
        except Exception as upload_error:
            print(f"❌ Upload failed: {upload_error}")
            print(f"   Error type: {type(upload_error)}")
            
            # Try to get more detail from the error
            if hasattr(upload_error, 'response'):
                print(f"   Response status: {getattr(upload_error.response, 'status_code', 'unknown')}")
                try:
                    error_text = upload_error.response.text()
                    print(f"   Response body: {error_text}")
                except:
                    pass
        
        await search.close()
        print("\n=== Debug Complete ===")
        
    except Exception as e:
        print(f"❌ Debug script error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_document_upload())