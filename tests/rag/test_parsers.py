from app.rag.parsers import get_parser, get_parser_for_file
from app.rag.parsers.markdown_parser import MarkdownParser
from app.rag.parsers.html_parser import HtmlParser
from app.rag.parsers.resume_parser import ResumeParser
from app.rag.parsers.pdf_parser import PdfParser
from app.rag.parsers.plain_parser import PlainParser


def test_get_parser_by_type():
    assert isinstance(get_parser("markdown"), MarkdownParser)
    assert isinstance(get_parser("html"), HtmlParser)
    assert isinstance(get_parser("resume"), ResumeParser)
    assert isinstance(get_parser("plain"), PlainParser)
    assert isinstance(get_parser("unknown"), PlainParser)


def test_get_parser_for_file_pdf():
    parser = get_parser_for_file("some text", "resume.pdf")
    assert isinstance(parser, PdfParser)


def test_get_parser_for_file_md():
    parser = get_parser_for_file("# Title\n\n## Sub", "readme.md")
    assert isinstance(parser, MarkdownParser)


def test_get_parser_for_file_content_resume():
    text = "张三\n工作经历\n阿里巴巴\n教育背景\n北京大学"
    parser = get_parser_for_file(text, "unknown.txt")
    assert isinstance(parser, ResumeParser)


def test_markdown_parser_basic():
    from app.rag.parsers.markdown_parser import MarkdownParser
    text = """# Title

Intro paragraph.

## Section 1

Section 1 content.

### Sub 1.1

Sub content.

## Section 2

Section 2 content."""
    parser = MarkdownParser()
    root = parser.parse(text)
    assert root.level == -1
    assert len(root.children) == 1  # single H1
    h1 = root.children[0]
    assert h1.title == "Title"
    assert h1.level == 1
    assert "Intro paragraph" in h1.content
    assert len(h1.children) == 2  # two H2s
    assert h1.children[0].title == "Section 1"
    assert h1.children[0].level == 2
    assert len(h1.children[0].children) == 1  # one H3
    assert h1.children[0].children[0].title == "Sub 1.1"
    assert h1.children[0].children[0].level == 3


def test_markdown_parser_no_headings():
    from app.rag.parsers.markdown_parser import MarkdownParser
    text = "Just plain text with no headings at all."
    parser = MarkdownParser()
    root = parser.parse(text)
    assert root.level == -1
    assert len(root.children) == 0
    assert "Just plain text" in root.content


def test_markdown_parser_h2_only():
    from app.rag.parsers.markdown_parser import MarkdownParser
    text = """## A

Content A.

## B

Content B."""
    parser = MarkdownParser()
    root = parser.parse(text)
    assert len(root.children) == 2
    assert root.children[0].title == "A"
    assert root.children[1].title == "B"


def test_html_parser_basic():
    from app.rag.parsers.html_parser import HtmlParser
    text = """<h1>Title</h1>
<p>Intro paragraph.</p>
<h2>Section 1</h2>
<p>Section 1 content.</p>
<h3>Sub 1.1</h3>
<p>Sub content.</p>
<h2>Section 2</h2>
<p>Section 2 content.</p>"""
    parser = HtmlParser()
    root = parser.parse(text)
    assert root.level == -1
    assert len(root.children) == 1
    h1 = root.children[0]
    assert h1.title == "Title"
    assert h1.level == 1
    assert len(h1.children) == 2
    assert h1.children[0].title == "Section 1"
    assert h1.children[0].level == 2


def test_html_parser_no_headings():
    from app.rag.parsers.html_parser import HtmlParser
    text = "<p>Just a paragraph.</p><div>No headings.</div>"
    parser = HtmlParser()
    root = parser.parse(text)
    assert len(root.children) == 0


def test_resume_parser_basic():
    from app.rag.parsers.resume_parser import ResumeParser
    text = """张三
13800138000

工作经历
阿里巴巴 - 高级工程师
2020至今
负责核心系统架构设计

腾讯 - 工程师
2018-2020
参与微信支付开发

教育背景
北京大学 计算机科学 本科 2014-2018

专业技能
Python, Go, Java
分布式系统设计"""
    parser = ResumeParser()
    root = parser.parse(text)
    assert root.level == -1
    titles = [c.title for c in root.children]
    assert "工作经历" in titles
    assert "教育背景" in titles
    assert "专业技能" in titles
    assert "张三" in root.content


def test_resume_parser_with_list_items():
    from app.rag.parsers.resume_parser import ResumeParser
    text = """工作经历
- 阿里巴巴：负责核心系统
- 腾讯：参与支付开发"""
    parser = ResumeParser()
    root = parser.parse(text)
    section = root.children[0]
    assert section.title == "工作经历"
    assert len(section.children) >= 2


def test_pdf_parser_delegates_to_resume():
    from app.rag.parsers.pdf_parser import PdfParser
    text = "张三\n工作经历\n阿里巴巴\n教育背景\n北京大学"
    parser = PdfParser()
    root = parser.parse(text)
    titles = [c.title for c in root.children]
    assert "工作经历" in titles


def test_pdf_parser_delegates_to_plain():
    from app.rag.parsers.pdf_parser import PdfParser
    text = "Just some random text without any structure markers."
    parser = PdfParser()
    root = parser.parse(text)
    assert len(root.children) == 0
    assert "random text" in root.content


def test_pdf_parser_numbered_sections():
    from app.rag.parsers.pdf_parser import PdfParser
    text = """1. 项目概述
本项目旨在构建一个系统。

2. 技术方案
采用微服务架构。

3. 实施计划
分三个阶段实施。"""
    parser = PdfParser()
    root = parser.parse(text)
    titles = [c.title for c in root.children]
    assert len(titles) >= 2


def test_plain_parser():
    from app.rag.parsers.plain_parser import PlainParser
    text = "Hello world.\n\nThis is a paragraph.\n\nAnother paragraph."
    parser = PlainParser()
    root = parser.parse(text)
    assert root.level == -1
    assert len(root.children) == 0
    assert "Hello world" in root.content
