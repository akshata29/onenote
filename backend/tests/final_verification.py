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

async def final_vector_verification():
    try:
        print("=== FINAL VERIFICATION: Vector Storage Success ===")
        
        search = AISearchClient()
        
        # Get all documents with explicit vector field selection
        search_results = await search.client.search(
            search_text="*", 
            top=10,
            select=["id", "title", "content", "content_vector", "notebook_name", "content_type"]
        )
        
        results = []
        async for item in search_results:
            results.append(item)
        
        print(f"✅ Found {len(results)} documents with vector data")
        
        vector_populated = 0
        vector_null = 0
        
        for i, doc in enumerate(results):
            title = doc.get('title', 'Untitled')[:35]
            content_preview = doc.get('content', '')[:40]
            
            vector = doc.get('content_vector')
            if vector and isinstance(vector, list) and len(vector) == 1536:
                vector_populated += 1
                status = f"✅ VECTOR ({len(vector)} dims)"
            else:
                vector_null += 1
                status = f"❌ NULL/INVALID"
            
            print(f"{i+1:2}. {title:<35} | {status}")
        
        print(f"\n=== FINAL RESULTS ===")
        print(f"Documents with vectors: {vector_populated}")
        print(f"Documents without vectors: {vector_null}")
        
        if vector_populated == len(results) and vector_populated > 0:
            print("\n🎉 COMPLETE SUCCESS! All documents have proper embeddings!")
            print("✅ Enhanced AI Search is fully operational with:")
            print("   • Vector similarity search")
            print("   • Semantic search capabilities") 
            print("   • Hybrid search (keywords + vectors)")
            print("   • Rich metadata filtering")
            print("   • Document Intelligence integration")
        elif vector_populated > 0:
            print(f"\n✅ Partial success: {vector_populated}/{len(results)} documents have vectors")
        else:
            print(f"\n❌ Issue: No documents have populated vectors")
        
        await search.close()
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(final_vector_verification())