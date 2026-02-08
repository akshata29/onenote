#!/usr/bin/env python3
import asyncio
import sys
import os
import json

# Fix for Windows async issue with selector event loop
if os.name == 'nt':  # Windows
    try:
        # Try to use WindowsSelectorEventLoopPolicy if available
        if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            print("✅ Set Windows SelectorEventLoop policy")
        else:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            print("✅ Set Windows ProactorEventLoop policy")
    except Exception as e:
        print(f"⚠️  Could not set event loop policy: {e}")

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(__file__))

from app.embeddings_client import EmbeddingsClient
from app.search_client import AISearchClient
from app.config import get_settings
from azure.core.exceptions import HttpResponseError

async def test_upload_scenarios():
    try:
        print("=== Testing Upload Scenarios to Isolate Vector Issue ===")
        
        # Initialize clients
        embedder = EmbeddingsClient()
        search = AISearchClient()
        
        # Generate test embedding
        vectors = await embedder.embed(["test content"])
        vector = vectors[0]
        
        print(f"✅ Generated embedding: {len(vector)} dimensions")
        
        # Test 1: Document WITHOUT vector field
        print("\n--- Test 1: Upload without vector field ---")
        doc_no_vector = {
            "id": "test-no-vector-001",
            "content": "Test document without vector field",
            "title": "No Vector Test",
            "page_id": "test-page-001",
            "page_title": "Test Page",
            "section_id": "test-section-001",
            "section_name": "Test Section",
            "notebook_id": "test-notebook-001",
            "notebook_name": "Test Notebook",
            "content_type": "page_text",
            "attachment_filetype": ""
        }
        
        try:
            result1 = await search.client.upload_documents([doc_no_vector])
            print(f"✅ Upload without vector: SUCCESS - {result1}")
        except Exception as e:
            print(f"❌ Upload without vector failed: {e}")
            if "StartArray" in str(e):
                print("   🔍 StartArray error still occurs without vector field!")
        
        # Test 2: Document WITH vector field
        print("\n--- Test 2: Upload with vector field ---")
        doc_with_vector = {
            "id": "test-with-vector-002",
            "content": "Test document with vector field",
            "content_vector": vector,
            "title": "With Vector Test",
            "page_id": "test-page-002",
            "page_title": "Test Page 2",
            "section_id": "test-section-002",
            "section_name": "Test Section 2",
            "notebook_id": "test-notebook-002",
            "notebook_name": "Test Notebook 2",
            "content_type": "page_text",
            "attachment_filetype": ""
        }
        
        try:
            result2 = await search.client.upload_documents([doc_with_vector])
            print(f"✅ Upload with vector: SUCCESS - {result2}")
        except Exception as e:
            print(f"❌ Upload with vector failed: {e}")
            if "StartArray" in str(e):
                print("   🔍 StartArray error occurs with vector field!")
                print(f"   Vector type: {type(vector)}, length: {len(vector)}")
                print(f"   First few values: {vector[:3]}")
        
        # Test 3: Minimal document to isolate the problematic field
        print("\n--- Test 3: Minimal document test ---")
        minimal_doc = {
            "id": "test-minimal-003", 
            "content": "Minimal test document",
            "title": "Minimal Test"
        }
        
        try:
            result3 = await search.client.upload_documents([minimal_doc])
            print(f"✅ Minimal document upload: SUCCESS - {result3}")
        except Exception as e:
            print(f"❌ Minimal document upload failed: {e}")
        
        await search.close()
        
    except Exception as e:
        print(f"❌ Test script error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_upload_scenarios())