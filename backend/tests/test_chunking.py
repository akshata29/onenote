from app.chunking import paragraph_chunks


def test_paragraph_chunks_basic():
    text = "para1\n\npara2"
    chunks = paragraph_chunks(text, chunk_size=50, overlap=10)
    assert len(chunks) == 1
    assert "para1" in chunks[0]["content"]
