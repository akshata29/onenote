#!/usr/bin/env python3
import asyncio
import sys
import os

# Fix for Windows async issue with selector event loop
if os.name == 'nt':  # Windows
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(__file__))

from app.embeddings_client import EmbeddingsClient
from app.search_client import AISearchClient

async def test_fixed_vector_upload():
    try:
        print("=== Testing Vector Upload with Fixed Schema ===")
        
        # Initialize clients
        embedder = EmbeddingsClient()
        search = AISearchClient()
        
        # Delete and recreate index with corrected vector field
        print("🔄 Recreating search index with corrected vector field...")
        try:
            await search.index_client.delete_index(search.settings.search_index)
            print("✅ Deleted existing index")
        except Exception:
            print("   No existing index to delete")
        
        await search.ensure_index_exists()
        print("✅ Created new index with corrected vector field")
        
        # Generate test embedding
        vectors = await embedder.embed(["Test content with corrected vector field"])
        vector = vectors[0]
        
        print(f"✅ Generated embedding: {len(vector)} dimensions")
        
        # Create test document with vector
        doc = {
            "id": "fixed-vector-test-001",
            "content": "Test document with corrected vector field definition",
            "content_vector": vector,
            "title": "Fixed Vector Test",
            "page_id": "test-page-001",
            "page_title": "Test Page",
            "section_id": "test-section-001", 
            "section_name": "Test Section",
            "notebook_id": "test-notebook-001",
            "notebook_name": "Test Notebook",
            "content_type": "page_text",
            "attachment_filetype": ""
        }
        
        print("🔄 Uploading document with vector...")
        try:
            result = await search.client.upload_documents([doc])
            print(f"✅ SUCCESS! Vector upload worked: {result}")
            
            # Wait for indexing
            await asyncio.sleep(3)
            
            # Test vector search
            print("\n🔄 Testing vector search...")
            query_vector = await embedder.embed(["corrected vector field"])
            search_results = await search.search(
                query="vector test",
                vector=query_vector[0], 
                search_mode="hybrid",
                top=1
            )
            
            if search_results:
                doc = search_results[0]
                print(f"✅ Vector search successful!")
                print(f"   Found document: {doc.get('title')}")
                print(f"   Content: {doc.get('content', '')[:50]}...")
                print(f"   Vector: {'Present' if doc.get('content_vector') else 'Missing'}")
                if doc.get('content_vector'):
                    print(f"   Vector length: {len(doc.get('content_vector'))}")
            else:
                print("⚠️  No search results found")
                
        except Exception as e:
            print(f"❌ Upload still failed: {e}")
            if "StartArray" in str(e):
                print("   🔍 Still getting StartArray error - need further investigation")
        
        await search.close()
        print("\n=== Test Complete ===")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fixed_vector_upload())