import json

from app.utils.chat import call_llm
from app.services.business import memory_service
from app.tools.base import BaseTool
from app.rag.pipeline import AdvancedRAGPipeline, PipelineConfig
from app.core.constants import (
    MEMORY_HISTORY_THRESHOLD,
    MEMORY_HISTORY_SLICE,
    CONTENT_PREVIEW_LENGTH,
    CONTENT_RAG_PREVIEW_LENGTH,
)

_recommend_pipeline = AdvancedRAGPipeline(PipelineConfig(
    enable_query_rewrite=True,
    enable_rerank=True,
    enable_context_compress=False,
    top_k=3,
))

PREFERENCE_EXTRACT_PROMPT = """你是一个用户画像分析助手。请根据以下用户对话历史，提取用户的求职偏好标签。

对话历史：
{history}

请以 JSON 格式输出偏好标签：
{{
  "industry": "目标行业",
  "position": "目标岗位",
  "city": "目标城市",
  "skills": ["核心技能"],
  "experience_level": "经验等级",
  "concerns": ["关注问题"]
}}

只输出 JSON，不要其他内容。信息不足的字段输出空字符串或空数组。"""

PERSONALIZED_RECOMMEND_PROMPT = """你是一个个性化求职推荐助手。请根据用户的偏好标签和检索到的相关资料，生成简短的个性化推荐。

用户偏好：
{preferences}

检索到的相关资料：
{rag_context}

请生成 2-3 条简短的个性化推荐，每条包含推荐内容和推荐理由。
格式：
💡 **个性化推荐**
1. [推荐内容] — [推荐理由]
2. [推荐内容] — [推荐理由]

注意：推荐要具体、贴合用户偏好，避免泛泛而谈。"""


clean_json_response = BaseTool.clean_json
parse_json_response = BaseTool.parse_json


async def extract_preferences(history_text: str) -> dict | None:
    """从对话历史中提取用户偏好标签"""
    prompt = PREFERENCE_EXTRACT_PROMPT.format(history=history_text)
    raw = await call_llm(prompt, max_tokens=500, temperature=0.1)
    preferences = parse_json_response(raw)
    if not preferences:
        return None
    has_value = any(
        preferences.get(k) for k in ("industry", "position", "city", "skills", "concerns")
    )
    return preferences if has_value else None


def build_search_query(preferences: dict, current_query: str = "") -> str:
    """基于偏好标签构建 RAG 检索 query"""
    parts = []
    for key in ("industry", "position", "city"):
        val = preferences.get(key, "")
        if val:
            parts.append(val)
    skills = preferences.get("skills", [])
    if skills:
        parts.extend(skills[:3])
    concerns = preferences.get("concerns", [])
    if concerns:
        parts.extend(concerns[:2])
    if not parts:
        return ""
    return " ".join(parts)


async def build_personalized_recommendation(user_id: str, current_query: str = "") -> str:
    """基于用户历史提取偏好标签，再调用 RAG 检索个性化内容"""
    history = await memory_service.get_raw_history(user_id)
    if len(history) < MEMORY_HISTORY_THRESHOLD:
        return ""

    history_text = "\n".join(
        f"用户：{item['user']}\n助手：{item['assistant'][:CONTENT_PREVIEW_LENGTH]}"
        for item in history[-MEMORY_HISTORY_SLICE:]
    )

    preferences = await extract_preferences(history_text)
    if not preferences:
        return ""

    search_query = build_search_query(preferences, current_query)
    if not search_query:
        return ""

    docs = await _recommend_pipeline.search(search_query)
    if not docs or (len(docs) == 1 and docs[0].get("source") == ""):
        return ""

    rag_context = "\n\n".join(
        f"[资料{i+1}] {d['content'][:CONTENT_RAG_PREVIEW_LENGTH]}" for i, d in enumerate(docs) if d.get("content")
    )

    prompt = PERSONALIZED_RECOMMEND_PROMPT.format(
        preferences=json.dumps(preferences, ensure_ascii=False),
        rag_context=rag_context,
    )
    return await call_llm(prompt, max_tokens=800, temperature=0.7)
