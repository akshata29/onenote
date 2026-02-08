# Document Intelligence Integration Examples

"""
Example code for processing various attachment types with Azure Document Intelligence.
This demonstrates the attachment processing capabilities of the OneNote RAG system.
"""

import asyncio
from typing import Dict, List, Any
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

class AttachmentProcessor:
    """Example implementation of attachment processing pipeline."""
    
    def __init__(self, endpoint: str, api_key: str):
        self.client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        
    async def process_pdf_attachment(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Process PDF attachment and extract structured content.
        
        Returns:
            Dict containing extracted text, tables, and metadata
        """
        try:
            # Use prebuilt-layout model for comprehensive extraction
            poller = await self.client.begin_analyze_document(
                "prebuilt-layout",
                body=pdf_bytes,
                features=["languages", "keyValuePairs"],
                output_content_format="markdown"
            )
            
            result = await poller.result()
            
            # Extract structured content
            return {
                "text_content": result.content,
                "tables": self._extract_tables(result.tables),
                "key_value_pairs": self._extract_kv_pairs(result.key_value_pairs),
                "languages": [lang.locale for lang in result.languages],
                "page_count": len(result.pages)
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def process_image_attachment(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Process image attachment with OCR capabilities.
        
        Returns:
            Dict containing extracted text and visual metadata
        """
        try:
            poller = await self.client.begin_analyze_document(
                "prebuilt-read",
                body=image_bytes
            )
            
            result = await poller.result()
            
            return {
                "extracted_text": result.content,
                "confidence_scores": [
                    line.confidence for page in result.pages 
                    for line in page.lines
                ],
                "has_handwriting": any(
                    style.is_handwritten for style in result.styles
                ) if result.styles else False
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _extract_tables(self, tables) -> List[Dict]:
        """Convert Document Intelligence tables to structured format."""
        if not tables:
            return []
        
        structured_tables = []
        for table in tables:
            # Create table matrix
            rows = {}
            for cell in table.cells:
                if cell.row_index not in rows:
                    rows[cell.row_index] = {}
                rows[cell.row_index][cell.column_index] = cell.content or ""
            
            # Convert to list of lists
            max_cols = max(max(row.keys()) for row in rows.values()) + 1
            table_data = []
            for row_idx in sorted(rows.keys()):
                row_data = []
                for col_idx in range(max_cols):
                    row_data.append(rows[row_idx].get(col_idx, ""))
                table_data.append(row_data)
            
            structured_tables.append({
                "rows": table.row_count,
                "columns": table.column_count, 
                "data": table_data
            })
        
        return structured_tables
    
    def _extract_kv_pairs(self, kv_pairs) -> List[Dict]:
        """Extract key-value pairs from document."""
        if not kv_pairs:
            return []
        
        pairs = []
        for kv in kv_pairs:
            if kv.key and kv.value:
                pairs.append({
                    "key": kv.key.content,
                    "value": kv.value.content,
                    "key_confidence": getattr(kv.key, 'confidence', 0.0),
                    "value_confidence": getattr(kv.value, 'confidence', 0.0)
                })
        
        return pairs

# Usage examples for different file types
async def main():
    processor = AttachmentProcessor(
        endpoint="https://your-doc-intelligence.cognitiveservices.azure.com/",
        api_key="your-api-key"
    )
    
    # Example: Process a PDF research paper
    with open("research_paper.pdf", "rb") as f:
        pdf_result = await processor.process_pdf_attachment(f.read())
        print("PDF Processing Result:", pdf_result)
    
    # Example: Process an architecture diagram image
    with open("architecture_diagram.png", "rb") as f:  
        image_result = await processor.process_image_attachment(f.read())
        print("Image Processing Result:", image_result)

if __name__ == "__main__":
    asyncio.run(main())