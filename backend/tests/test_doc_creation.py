#!/usr/bin/env python3
import asyncio
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(__file__))

from app.embeddings_client import EmbeddingsClient
from app.chunking import paragraph_chunks
from app.config import get_settings

async def test_embedding_in_doc_creation():
    try:
        print("Testing embedding generation and document creation...")
        
        settings = get_settings()
        embedder = EmbeddingsClient()
        
        # Test content like what we'd see in real ingestion
        test_content = "Technical Architecture Review\n\n# Architecture Review: Acme Integration\n\n## System Overview"
        
        # Create chunks like real ingestion
        chunks = paragraph_chunks(test_content, settings.chunk_size, settings.chunk_overlap)
        print(f"Created {len(chunks)} chunks")
        
        # Generate embeddings like real ingestion
        contents = [c["content"] for c in chunks]
        vectors = await embedder.embed(contents)
        print(f"Generated {len(vectors)} vectors")
        
        # Create documents like real ingestion
        docs = []
        for idx, chunk in enumerate(chunks):
            vector = vectors[idx]
            
            # Validate vector like real ingestion does
            if not isinstance(vector, list):
                print(f"❌ Invalid vector at index {idx}: expected list, got {type(vector)}")
                vector = [0.0] * 1536  # Fallback to zero vector
            elif len(vector) != 1536:
                print(f"❌ Invalid vector length at index {idx}: expected 1536, got {len(vector)}")
                vector = [0.0] * 1536  # Fallback to zero vector
            else:
                print(f"✅ Valid vector at index {idx}: {len(vector)} dimensions")
            
            doc = {
                "id": f"test-{idx}",
                "content": chunk["content"],
                "content_vector": vector,
                "title": "Test Document",
                "page_id": "test-page",
                "page_title": "Test Page", 
                "section_id": "test-section",
                "section_name": "Test Section",
                "notebook_id": "test-notebook",
                "notebook_name": "Test Notebook",
                "content_type": "page_text",
                "attachment_filetype": ""
            }
            
            docs.append(doc)
            print(f"Document {idx}: content_vector is {'None' if doc['content_vector'] is None else 'populated'}")
            if doc['content_vector']:
                print(f"  Vector preview: {doc['content_vector'][:3]}...")
        
        print(f"\n✅ Successfully created {len(docs)} documents with embeddings")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_embedding_in_doc_creation())