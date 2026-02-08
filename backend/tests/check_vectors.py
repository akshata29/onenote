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

async def check_vectors_after_ingestion():
    try:
        print("=== Checking Vector Storage After Successful Ingestion ===")
        
        search = AISearchClient()
        
        # Search for the documents that were just ingested
        print("🔍 Searching for recently ingested documents...")
        search_results = await search.client.search(search_text="*", top=10)
        
        results = []
        async for item in search_results:
            results.append(item)
        
        print(f"✅ Found {len(results)} documents in search index")
        
        vector_count = 0
        null_vector_count = 0
        
        for i, doc in enumerate(results):
            print(f"\n--- Document {i+1} ---")
            print(f"ID: {doc.get('id')}")
            print(f"Title: {doc.get('title')}")
            print(f"Content: {doc.get('content', '')[:80]}...")
            
            # Check vector field - this is the critical test!
            vector = doc.get('content_vector')
            if vector is None:
                print("❌ content_vector: NULL")
                null_vector_count += 1
            elif isinstance(vector, list) and len(vector) > 0:
                print(f"✅ content_vector: {len(vector)} dimensions")
                print(f"   First 3 values: {vector[:3]}")
                vector_count += 1
            else:
                print(f"⚠️  content_vector: unexpected type {type(vector)}")
        
        print(f"\n=== SUMMARY ===")
        print(f"Documents with vectors: {vector_count}")
        print(f"Documents with NULL vectors: {null_vector_count}")
        
        if vector_count > 0 and null_vector_count == 0:
            print("🎉 SUCCESS! All documents have populated embeddings!")
        elif vector_count > 0:
            print("✅ PARTIAL SUCCESS: Some documents have embeddings")
        else:
            print("❌ FAILURE: No documents have embeddings")
        
        await search.close()
        
    except Exception as e:
        print(f"❌ Check failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_vectors_after_ingestion())