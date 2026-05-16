from app.rag.doc_type_detector import detect_doc_type


def test_detect_html():
    text = "<html><body><h1>Title</h1><p>Content</p></body></html>"
    assert detect_doc_type(text) == "html"


def test_detect_html_h_tags():
    text = "Some text\n<h1>Title</h1>\n<h2>Subtitle</h2>\nMore text"
    assert detect_doc_type(text) == "html"


def test_detect_markdown():
    text = "# Title\n\nSome content\n\n## Subtitle\n\nMore content"
    assert detect_doc_type(text) == "markdown"


def test_detect_markdown_single_heading():
    text = "# Only one heading\n\nRest is plain text without structure"
    result = detect_doc_type(text)
    assert result != "markdown"


def test_detect_resume():
    text = "张三\n工作经历\n阿里巴巴\n教育背景\n北京大学"
    assert detect_doc_type(text) == "resume"


def test_detect_resume_with_colon():
    text = "个人简介：我是一个开发者\n工作经历：\n阿里巴巴\n教育背景：\n北京大学"
    assert detect_doc_type(text) == "resume"


def test_detect_plain():
    text = "这是一段普通文本，没有任何结构标记。就是普通的描述性内容。"
    assert detect_doc_type(text) == "plain"


def test_detect_empty():
    assert detect_doc_type("") == "plain"


def test_detect_resume_single_keyword():
    text = "这是一份简历\n只有工作经历这个关键词\n其他都是普通文本内容"
    result = detect_doc_type(text)
    assert result != "resume"
