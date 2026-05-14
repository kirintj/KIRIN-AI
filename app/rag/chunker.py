import re

_DEFAULT_MAX_SIZE = 500
_DEFAULT_OVERLAP = 80


def semantic_chunk(
    text: str,
    max_size: int = _DEFAULT_MAX_SIZE,
    overlap: int = _DEFAULT_OVERLAP,
) -> list[str]:
    """按语义边界（段落/句号）分块，超长段落再按句子切分，分块间有重叠"""
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

    # 为非尾块添加 overlap
    if overlap > 0 and len(chunks) > 1:
        chunks = _add_overlap(chunks, overlap)

    return chunks if chunks else [text] if text.strip() else []


def _add_overlap(chunks: list[str], overlap: int) -> list[str]:
    """为每个分块（最后一个除外）的末尾追加下一块的开头作为重叠"""
    result: list[str] = []
    for i, chunk in enumerate(chunks):
        if i < len(chunks) - 1:
            next_prefix = chunks[i + 1][:overlap]
            result.append(chunk + "\n" + next_prefix)
        else:
            result.append(chunk)
    return result


def _split_long_paragraph(
    para: str,
    max_size: int,
    overlap: int = 0,
) -> list[str]:
    """超长段落按中文标点切分，优先句号级别，其次逗号级别"""
    merged = _merge_by_separator(para, max_size, r"([。！？；\n])")
    if len(merged) > 1:
        return merged

    merged = _merge_by_separator(para, max_size, r"([，：、,:\n])")
    if len(merged) > 1:
        return merged

    return _split_fixed(para, max_size, overlap)


def _merge_by_separator(text: str, max_size: int, pattern: str) -> list[str]:
    """按指定分隔符切分后合并为不超过 max_size 的块"""
    parts = re.split(pattern, text)
    merged: list[str] = []
    buf = ""
    for i in range(0, len(parts), 2):
        s = parts[i] + (parts[i + 1] if i + 1 < len(parts) else "")
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
    return merged


def _split_fixed(text: str, chunk_size: int, overlap: int = 0) -> list[str]:
    """固定长度兜底切分，支持 overlap"""
    chunks: list[str] = []
    start = 0
    step = max(1, chunk_size - overlap) if overlap > 0 else chunk_size
    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        start += step
    return chunks
