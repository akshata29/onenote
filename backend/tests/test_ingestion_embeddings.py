#!/usr/bin/env python3
import asyncio
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(__file__))

from app.ingestion_worker import IngestionWorker

async def test_ingestion_embeddings():
    try:
        print("Testing ingestion worker embedding generation...")
        
        # Create worker with dummy assertion
        worker = IngestionWorker('dummy_assertion')
        
        # Test embedding generation like in the real process
        test_content = 'This is sample content for testing embeddings during ingestion'
        chunks = [{'content': test_content, 'start_char': 0, 'end_char': len(test_content)}]
        
        # Generate embeddings like in the real process
        contents = [c['content'] for c in chunks]
        print(f"Generating embeddings for {len(contents)} chunk(s)...")
        vectors = await worker.embedder.embed(contents)
        
        print(f"✅ Generated {len(vectors)} vector(s)")
        print(f"First vector length: {len(vectors[0])} (should be 1536)")
        print(f"Vector preview: {vectors[0][:3]}...")
        
        # Test document creation like in real ingestion
        doc_id = "test-doc-id"
        vector = vectors[0]
        
        # Check vector validation logic from ingestion worker
        if not isinstance(vector, list):
            print(f"❌ Invalid vector type: expected list, got {type(vector)}")
        elif len(vector) != 1536:
            print(f"❌ Invalid vector length: expected 1536, got {len(vector)}")
        else:
            print(f"✅ Vector validation passed")
        
        # Create a test document like the real ingestion does
        test_doc = {
            "id": doc_id,
            "content": test_content,
            "content_vector": vector,
            "title": "Test Document",
            "page_id": "test-page-id",
            "page_title": "Test Page",
            "section_id": "test-section-id", 
            "section_name": "Test Section",
            "notebook_id": "test-notebook-id",
            "notebook_name": "Test Notebook",
            "content_type": "page_text",
            "attachment_filetype": ""
        }
        
        print(f"✅ Created test document with vector field: {test_doc['content_vector'] is not None}")
        print(f"Vector in document: {test_doc['content_vector'][:3] if test_doc['content_vector'] else 'None'}...")
        
        await worker.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ingestion_embeddings())