import re

_DEFAULT_MAX_SIZE = 500
_DEFAULT_OVERLAP = 50


def semantic_chunk(
    text: str,
    max_size: int = _DEFAULT_MAX_SIZE,
    overlap: int = _DEFAULT_OVERLAP,
) -> list[str]:
    """按语义边界（段落/句号）分块，超长段落再按句子切分"""
    paragraphs = re.split(r"\n{2,}", text)
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current) + len(para) + 1 <= max_size:
            current = (current + "\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            if len(para) > max_size:
                sub_chunks = _split_long_paragraph(para, max_size, overlap)
                chunks.extend(sub_chunks[:-1])
                current = sub_chunks[-1]
            else:
                current = para

    if current:
        chunks.append(current)

    return chunks if chunks else [text] if text.strip() else []


def _split_long_paragraph(
    para: str,
    max_size: int,
    overlap: int,
) -> list[str]:
    """超长段落按中文句号/分号等切分"""
    sentences = re.split(r"([。！？；\n])", para)
    merged: list[str] = []
    buf = ""
    for i in range(0, len(sentences), 2):
        s = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
        if not s.strip():
            continue
        if len(buf) + len(s) <= max_size:
            buf += s
        else:
            if buf:
                merged.append(buf)
            buf = s
    if buf:
        merged.append(buf)

    if len(merged) <= 1:
        return _split_fixed(para, max_size, overlap)
    return merged


def _split_fixed(text: str, chunk_size: int, overlap: int) -> list[str]:
    """固定长度兜底切分"""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        start += chunk_size - overlap
    return chunks
