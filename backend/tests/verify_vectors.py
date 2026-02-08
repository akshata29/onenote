#!/usr/bin/env python3
import asyncio
import sys
import os

# Fix for Windows async issue
if os.name == 'nt':  # Windows
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app.search_client import AISearchClient

async def verify_vector_storage():
    try:
        print("=== Verifying Vector Storage in Search Index ===")
        
        search = AISearchClient()
        
        # Search for our test documents
        print("🔍 Searching for documents...")
        search_results = await search.client.search(search_text="*", top=5)
        
        results = []
        async for item in search_results:
            results.append(item)
        
        print(f"✅ Found {len(results)} documents in search index")
        
        for i, doc in enumerate(results):
            print(f"\n--- Document {i+1} ---")
            print(f"ID: {doc.get('id')}")
            print(f"Title: {doc.get('title')}")
            print(f"Content: {doc.get('content', '')[:50]}...")
            
            # Check vector field
            vector = doc.get('content_vector')
            if vector is None:
                print("❌ content_vector: NULL")
            elif isinstance(vector, list):
                print(f"✅ content_vector: {len(vector)} dimensions")
                print(f"   First 3 values: {vector[:3]}")
            else:
                print(f"⚠️  content_vector: unexpected type {type(vector)}")
        
        await search.close()
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_vector_storage())