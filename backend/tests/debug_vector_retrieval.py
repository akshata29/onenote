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

async def debug_vector_retrieval():
    try:
        print("=== Debugging Vector Field Retrieval ===")
        
        search = AISearchClient()
        
        # Try different search approaches to get vectors
        print("\n--- Test 1: Default search (might exclude vectors) ---")
        results1 = await search.client.search(search_text="*", top=1)
        docs1 = []
        async for item in results1:
            docs1.append(item)
            
        if docs1:
            doc = docs1[0]
            print(f"Document keys: {list(doc.keys())}")
            print(f"content_vector in keys: {'content_vector' in doc.keys()}")
        
        print("\n--- Test 2: Search with explicit select fields ---")
        results2 = await search.client.search(
            search_text="*", 
            top=1,
            select=["id", "title", "content", "content_vector"]
        )
        docs2 = []
        async for item in results2:
            docs2.append(item)
            
        if docs2:
            doc = docs2[0]
            print(f"Document keys: {list(doc.keys())}")
            print(f"content_vector: {'Present' if doc.get('content_vector') else 'Missing/NULL'}")
            if doc.get('content_vector'):
                print(f"Vector length: {len(doc['content_vector'])}")
        
        print("\n--- Test 3: Search with all fields (including vectors) ---")
        results3 = await search.client.search(
            search_text="*", 
            top=1,
            select="*"
        )
        docs3 = []
        async for item in results3:
            docs3.append(item)
            
        if docs3:
            doc = docs3[0]
            print(f"Total fields returned: {len(doc.keys())}")
            print(f"All fields: {list(doc.keys())}")
            if 'content_vector' in doc:
                vector = doc['content_vector']
                if vector is None:
                    print("❌ content_vector field exists but is NULL")
                else:
                    print(f"✅ content_vector has data: {len(vector)} dimensions")
            else:
                print("❌ content_vector field not returned")
        
        await search.close()
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_vector_retrieval())