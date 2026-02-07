from typing import List, Dict


def paragraph_chunks(text: str, chunk_size: int, overlap: int) -> List[Dict[str, str]]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[Dict[str, str]] = []
    buffer: List[str] = []
    buffer_len = 0
    for para in paragraphs:
        if buffer_len + len(para) + 1 > chunk_size and buffer:
            chunks.append({"content": "\n\n".join(buffer)})
            overlap_text = "\n\n".join(buffer)[-overlap:]
            buffer = [overlap_text, para]
            buffer_len = len(overlap_text) + len(para)
        else:
            buffer.append(para)
            buffer_len += len(para) + 1
    if buffer:
        chunks.append({"content": "\n\n".join(buffer)})
    return chunks
