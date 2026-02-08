#!/usr/bin/env python3
import asyncio
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(__file__))

from app.embeddings_client import EmbeddingsClient
from app.config import get_settings

async def test_embeddings():
    try:
        print("Testing embeddings generation...")
        
        # Check configuration
        settings = get_settings()
        print(f"OpenAI endpoint: {settings.openai_endpoint}")
        print(f"Deployment name: {settings.openai_embedding_deployment_name}")
        print(f"API version: {settings.openai_api_version}")
        
        # Test embeddings
        client = EmbeddingsClient()
        test_texts = ["This is a test text for embedding generation"]
        
        print(f"Generating embeddings for {len(test_texts)} text(s)...")
        result = await client.embed(test_texts)
        
        if result and len(result) > 0:
            print(f"✅ Success! Generated {len(result)} embedding(s)")
            print(f"First embedding length: {len(result[0])}")
            print(f"First few values: {result[0][:5]}...")
        else:
            print("❌ No embeddings returned")
            
    except Exception as e:
        print(f"❌ Error generating embeddings: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_embeddings())