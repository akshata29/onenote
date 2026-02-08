# Advanced Chunking Strategies for Multi-Modal Documents

"""
Different approaches to document chunking based on content type and structure.
Optimized for OneNote RAG system attachment processing.
"""

from typing import List, Dict, Any, Tuple
import re
from dataclasses import dataclass

@dataclass
class DocumentChunk:
    """Represents a processed document chunk."""
    content: str
    chunk_type: str  # 'text', 'table', 'image_caption', 'code'
    metadata: Dict[str, Any]
    start_index: int
    end_index: int
    confidence_score: float = 1.0

class SemanticChunker:
    """
    Advanced chunking strategy that preserves document structure and meaning.
    """
    
    def __init__(self, 
                 target_chunk_size: int = 1000,
                 overlap_size: int = 200,
                 preserve_structure: bool = True):
        self.target_chunk_size = target_chunk_size
        self.overlap_size = overlap_size
        self.preserve_structure = preserve_structure
    
    def chunk_extracted_content(self, 
                              content: str,
                              content_type: str,
                              metadata: Dict = None) -> List[DocumentChunk]:
        """
        Main chunking method that routes to specialized chunkers based on content type.
        """
        if not metadata:
            metadata = {}
            
        if content_type == "application/pdf":
            return self._chunk_pdf_content(content, metadata)
        elif content_type in ["image/jpeg", "image/png", "image/jpg"]:
            return self._chunk_image_content(content, metadata)
        elif content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            return self._chunk_docx_content(content, metadata)
        else:
            return self._chunk_generic_text(content, metadata)
    
    def _chunk_pdf_content(self, content: str, metadata: Dict) -> List[DocumentChunk]:
        """
        PDF-specific chunking that handles tables, headers, and structured content.
        """
        chunks = []
        
        # Split content by major sections (identified by ## headers)
        sections = re.split(r'\n##\s+', content)
        
        for section_idx, section in enumerate(sections):
            if not section.strip():
                continue
                
            # Add header back if it's not the first section
            if section_idx > 0:
                section = "## " + section
            
            # Handle tables separately
            if "| " in section and "|" in section:
                table_chunks = self._extract_table_chunks(section, metadata)
                chunks.extend(table_chunks)
            else:
                # Regular text chunking with overlap
                text_chunks = self._chunk_text_with_overlap(
                    section, 
                    chunk_type="pdf_section",
                    metadata=metadata
                )
                chunks.extend(text_chunks)
        
        return chunks
    
    def _chunk_image_content(self, content: str, metadata: Dict) -> List[DocumentChunk]:
        """
        Image-specific chunking for extracted text from images/diagrams.
        """
        # For extracted text from images, treat as single chunk if small
        if len(content) <= self.target_chunk_size:
            return [DocumentChunk(
                content=content,
                chunk_type="image_text",
                metadata={**metadata, "is_ocr_content": True},
                start_index=0,
                end_index=len(content),
                confidence_score=metadata.get("avg_confidence", 0.8)
            )]
        
        # For longer extracted text, use sentence-based chunking
        return self._chunk_by_sentences(content, "image_text", metadata)
    
    def _chunk_docx_content(self, content: str, metadata: Dict) -> List[DocumentChunk]:
        """
        DOCX-specific chunking that preserves document structure.
        """
        chunks = []
        
        # Split by paragraphs but preserve structure
        paragraphs = content.split('\n\n')
        current_chunk = ""
        
        for para in paragraphs:
            if not para.strip():
                continue
                
            # Check if adding this paragraph exceeds target size
            if len(current_chunk + para) > self.target_chunk_size and current_chunk:
                # Create chunk with current content
                chunks.append(DocumentChunk(
                    content=current_chunk.strip(),
                    chunk_type="docx_section",
                    metadata=metadata,
                    start_index=len("".join([c.content for c in chunks])),
                    end_index=len("".join([c.content for c in chunks])) + len(current_chunk)
                ))
                
                # Start new chunk with overlap
                if self.overlap_size > 0:
                    words = current_chunk.split()
                    overlap_words = words[-self.overlap_size//10:]  # Approximate word overlap
                    current_chunk = " ".join(overlap_words) + " " + para
                else:
                    current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(DocumentChunk(
                content=current_chunk.strip(),
                chunk_type="docx_section", 
                metadata=metadata,
                start_index=len("".join([c.content for c in chunks])),
                end_index=len("".join([c.content for c in chunks])) + len(current_chunk)
            ))
        
        return chunks
    
    def _extract_table_chunks(self, section: str, metadata: Dict) -> List[DocumentChunk]:
        """
        Extract and chunk table content separately to preserve structure.
        """
        chunks = []
        
        # Find table boundaries
        table_pattern = r'(\|[^\n]*\|\n(?:\|[^\n]*\|\n)*)'
        tables = re.finditer(table_pattern, section, re.MULTILINE)
        
        last_end = 0
        
        for table_match in tables:
            # Add text before table
            pre_table_text = section[last_end:table_match.start()].strip()
            if pre_table_text:
                text_chunks = self._chunk_text_with_overlap(
                    pre_table_text, 
                    "text_before_table",
                    metadata
                )
                chunks.extend(text_chunks)
            
            # Add table as separate chunk
            table_content = table_match.group(1)
            chunks.append(DocumentChunk(
                content=table_content,
                chunk_type="table",
                metadata={**metadata, "is_structured_data": True},
                start_index=table_match.start(),
                end_index=table_match.end()
            ))
            
            last_end = table_match.end()
        
        # Add remaining text after last table
        remaining_text = section[last_end:].strip()
        if remaining_text:
            text_chunks = self._chunk_text_with_overlap(
                remaining_text,
                "text_after_table", 
                metadata
            )
            chunks.extend(text_chunks)
        
        return chunks
    
    def _chunk_text_with_overlap(self, 
                               text: str, 
                               chunk_type: str,
                               metadata: Dict) -> List[DocumentChunk]:
        """
        Chunk text with intelligent overlap based on sentence boundaries.
        """
        if len(text) <= self.target_chunk_size:
            return [DocumentChunk(
                content=text,
                chunk_type=chunk_type,
                metadata=metadata,
                start_index=0,
                end_index=len(text)
            )]
        
        chunks = []
        sentences = self._split_into_sentences(text)
        
        current_chunk = ""
        current_start = 0
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            
            # Check if adding this sentence exceeds target size
            if len(current_chunk + sentence) > self.target_chunk_size and current_chunk:
                # Create current chunk
                chunks.append(DocumentChunk(
                    content=current_chunk.strip(),
                    chunk_type=chunk_type,
                    metadata=metadata,
                    start_index=current_start,
                    end_index=current_start + len(current_chunk)
                ))
                
                # Calculate overlap
                if self.overlap_size > 0 and len(chunks) > 0:
                    # Find sentences to include in overlap
                    overlap_chars = 0
                    overlap_sentences = []
                    
                    for j in range(i - 1, -1, -1):
                        if overlap_chars + len(sentences[j]) <= self.overlap_size:
                            overlap_sentences.insert(0, sentences[j])
                            overlap_chars += len(sentences[j])
                        else:
                            break
                    
                    current_chunk = "".join(overlap_sentences) + sentence
                    current_start = current_start + len(chunks[-1].content) - overlap_chars
                else:
                    current_chunk = sentence
                    current_start = current_start + len(current_chunk) if chunks else 0
            else:
                current_chunk += sentence
            
            i += 1
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append(DocumentChunk(
                content=current_chunk.strip(),
                chunk_type=chunk_type,
                metadata=metadata,
                start_index=current_start,
                end_index=current_start + len(current_chunk)
            ))
        
        return chunks
    
    def _chunk_by_sentences(self, text: str, chunk_type: str, metadata: Dict) -> List[DocumentChunk]:
        """Chunk text by sentence boundaries for better semantic coherence."""
        sentences = self._split_into_sentences(text)
        
        if len(sentences) <= 3:  # Short content, keep as single chunk
            return [DocumentChunk(
                content=text,
                chunk_type=chunk_type,
                metadata=metadata,
                start_index=0,
                end_index=len(text)
            )]
        
        # Group sentences into chunks
        chunks = []
        current_sentences = []
        current_length = 0
        
        for sentence in sentences:
            if current_length + len(sentence) > self.target_chunk_size and current_sentences:
                # Create chunk
                chunk_content = "".join(current_sentences)
                chunks.append(DocumentChunk(
                    content=chunk_content,
                    chunk_type=chunk_type,
                    metadata=metadata,
                    start_index=sum(len(c.content) for c in chunks),
                    end_index=sum(len(c.content) for c in chunks) + len(chunk_content)
                ))
                
                # Start new chunk
                current_sentences = [sentence]
                current_length = len(sentence)
            else:
                current_sentences.append(sentence)
                current_length += len(sentence)
        
        # Add final chunk
        if current_sentences:
            chunk_content = "".join(current_sentences)
            chunks.append(DocumentChunk(
                content=chunk_content,
                chunk_type=chunk_type,
                metadata=metadata,
                start_index=sum(len(c.content) for c in chunks),
                end_index=sum(len(c.content) for c in chunks) + len(chunk_content)
            ))
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences while preserving structure.""" 
        # Simple sentence splitting - can be enhanced with NLTK or spaCy
        sentence_endings = r'[.!?]+\s+'
        sentences = re.split(sentence_endings, text)
        
        # Reconstruct with endings
        result = []
        parts = re.split(r'([.!?]+\s+)', text)
        
        for i in range(0, len(parts) - 1, 2):
            if i + 1 < len(parts):
                result.append(parts[i] + parts[i + 1])
            else:
                result.append(parts[i])
        
        return [s for s in result if s.strip()]
    
    def _chunk_generic_text(self, content: str, metadata: Dict) -> List[DocumentChunk]:
        """Fallback chunking for unknown content types."""
        return self._chunk_text_with_overlap(content, "generic_text", metadata)

# Usage example
def demonstrate_chunking_strategies():
    """Example usage of different chunking strategies.""" 
    
    chunker = SemanticChunker(
        target_chunk_size=800,
        overlap_size=150,
        preserve_structure=True
    )
    
    # Example PDF content with tables
    pdf_content = """
## Executive Summary
This document outlines the performance benchmarks for our RAG system.

| Metric | Value | Target |
|--------|-------|--------|
| Response Time | 1.2s | <2s |
| Accuracy | 87% | >85% |
| Throughput | 50 qps | >30 qps |

## Detailed Analysis  
The system demonstrates strong performance across all key metrics...
    """
    
    chunks = chunker.chunk_extracted_content(
        pdf_content, 
        "application/pdf",
        {"filename": "performance_report.pdf", "page_count": 5}
    )
    
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1} ({chunk.chunk_type}): {len(chunk.content)} chars")
        print(f"Content preview: {chunk.content[:100]}...")
        print(f"Metadata: {chunk.metadata}")
        print("-" * 50)

if __name__ == "__main__":
    demonstrate_chunking_strategies()