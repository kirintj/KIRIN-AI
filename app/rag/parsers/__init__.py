from __future__ import annotations

import os

from app.rag.doc_type_detector import detect_doc_type
from app.rag.parsers.base import BaseParser
from app.rag.parsers.markdown_parser import MarkdownParser
from app.rag.parsers.html_parser import HtmlParser
from app.rag.parsers.resume_parser import ResumeParser
from app.rag.parsers.pdf_parser import PdfParser
from app.rag.parsers.plain_parser import PlainParser

_PARSERS: dict[str, BaseParser] = {
    "markdown": MarkdownParser(),
    "html": HtmlParser(),
    "resume": ResumeParser(),
    "plain": PlainParser(),
}

_PDF_EXTENSIONS = {".pdf"}


def get_parser_for_file(content: str, filename: str = "") -> BaseParser:
    """根据文件名扩展名和内容选择合适的 Parser。"""
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        if ext in _PDF_EXTENSIONS:
            return PdfParser()
        if ext == ".md":
            return _PARSERS["markdown"]

    doc_type = detect_doc_type(content)
    return _PARSERS[doc_type]


def get_parser(doc_type: str) -> BaseParser:
    """根据 doc_type 字符串获取 Parser。"""
    return _PARSERS.get(doc_type, _PARSERS["plain"])
