import re

_RESUME_KEYWORDS = (
    "个人简介", "基本信息", "基本资料", "求职意向",
    "工作经历", "工作经验", "项目经历", "项目经验", "实习经历",
    "教育背景", "教育经历", "教育信息",
    "专业技能", "技能特长", "技能清单",
    "自我评价", "个人总结", "荣誉奖项", "证书资质", "兴趣爱好",
)

_RESUME_PATTERN = re.compile(
    r"^[ \t]*(" + "|".join(re.escape(k) for k in _RESUME_KEYWORDS) + r")[ \t:：]?[ \t]*$",
    re.MULTILINE,
)

_HEADING_PATTERN = re.compile(r"^#{1,6}\s+.+", re.MULTILINE)
_HTML_H_TAG = re.compile(r"<h[1-6][^>]*>", re.IGNORECASE)
_HTML_SIGNATURE = re.compile(r"<!DOCTYPE|<html", re.IGNORECASE)


def detect_doc_type(text: str) -> str:
    """检测文档类型，返回: html | markdown | resume | plain"""
    if not text or not text.strip():
        return "plain"

    # Priority 1: HTML
    if _HTML_SIGNATURE.search(text) or len(_HTML_H_TAG.findall(text)) >= 2:
        return "html"

    # Priority 2: Markdown (at least 2 heading lines)
    if len(_HEADING_PATTERN.findall(text)) >= 2:
        return "markdown"

    # Priority 3: Resume (at least 2 section keywords)
    if len(_RESUME_PATTERN.findall(text)) >= 2:
        return "resume"

    return "plain"
