import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.tools.base import ensure_user_dir
from app.utils.chat import call_llm

INTERVIEW_SIM_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "interview_sim"

INTERVIEW_TYPES = {
    "tech": "技术面试",
    "hr": "HR面试",
    "behavior": "行为面试",
    "case": "案例分析",
}

SYSTEM_PROMPT_MAP = {
    "tech": (
        "你是一位严格的技术面试官。你正在对候选人进行技术面试。\n"
        "规则：\n"
        "- 每次只问一个问题，等待候选人回答\n"
        "- 根据候选人回答追问或进入下一题\n"
        "- 如果回答不完整，引导候选人补充\n"
        "- 面试约8-10个问题后给出总结评价\n"
        "- 用专业但友好的语气\n"
        "- 不要一次给出所有问题"
    ),
    "hr": (
        "你是一位专业的HR面试官。你正在对候选人进行HR面试。\n"
        "规则：\n"
        "- 关注候选人的软技能、团队协作、职业规划\n"
        "- 每次只问一个问题\n"
        "- 根据回答深入追问\n"
        "- 面试约6-8个问题后给出总结评价\n"
        "- 语气温和专业"
    ),
    "behavior": (
        "你是一位行为面试官，使用STAR法则进行面试。\n"
        "规则：\n"
        "- 要求候选人用具体事例回答\n"
        "- 引导候选人按Situation-Task-Action-Result结构回答\n"
        "- 每次只问一个行为问题\n"
        "- 面试约6-8个问题后给出总结评价"
    ),
    "case": (
        "你是一位案例分析面试官。你正在对候选人进行案例分析面试。\n"
        "规则：\n"
        "- 给出一个商业场景或问题\n"
        "- 引导候选人分析问题、提出框架\n"
        "- 逐步深入追问\n"
        "- 评估候选人的逻辑思维和问题解决能力"
    ),
}

EVALUATION_PROMPT = """你是一位面试评估专家。请根据以下面试对话记录，给出综合评估。

面试类型：{interview_type}
目标岗位：{position}
目标公司：{company}

面试对话记录：
{conversation}

请按以下格式输出评估结果：

## 综合评分（1-10分）

## 优势
- （列出3-5个优势）

## 待提升
- （列出2-4个待提升点）

## 各维度评分
- 专业知识：X/10
- 表达能力：X/10
- 逻辑思维：X/10
- 应变能力：X/10
- 综合印象：X/10

## 改进建议
（给出具体的改进建议）"""


def _get_session_path(user_id: str, session_id: str) -> Path:
    return ensure_user_dir(INTERVIEW_SIM_DIR, user_id) / f"{session_id}.json"


def _get_sessions_meta_path(user_id: str) -> Path:
    return ensure_user_dir(INTERVIEW_SIM_DIR, user_id) / "sessions.json"


def _load_sessions_meta_sync(user_id: str) -> list[dict]:
    path = _get_sessions_meta_path(user_id)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save_sessions_meta_sync(user_id: str, meta: list[dict]):
    path = _get_sessions_meta_path(user_id)
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _create_session_sync(user_id: str, data: dict) -> dict:
    import uuid
    session_id = uuid.uuid4().hex[:12]
    now = datetime.now().isoformat()
    session = {
        "id": session_id,
        "company": data.get("company", ""),
        "position": data.get("position", ""),
        "interview_type": data.get("interview_type", "tech"),
        "status": "active",
        "messages": [],
        "score": None,
        "evaluation": None,
        "created_at": now,
        "updated_at": now,
    }
    path = _get_session_path(user_id, session_id)
    path.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")

    meta = _load_sessions_meta_sync(user_id)
    meta.insert(0, {
        "id": session_id,
        "company": session["company"],
        "position": session["position"],
        "interview_type": session["interview_type"],
        "status": "active",
        "score": None,
        "created_at": now,
        "updated_at": now,
    })
    _save_sessions_meta_sync(user_id, meta)
    return session


def _get_session_sync(user_id: str, session_id: str) -> Optional[dict]:
    path = _get_session_path(user_id, session_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _add_message_sync(user_id: str, session_id: str, role: str, content: str) -> bool:
    session = _get_session_sync(user_id, session_id)
    if not session:
        return False
    session["messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    })
    session["updated_at"] = datetime.now().isoformat()
    path = _get_session_path(user_id, session_id)
    path.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def _finish_session_sync(user_id: str, session_id: str, evaluation: dict) -> bool:
    session = _get_session_sync(user_id, session_id)
    if not session:
        return False
    session["status"] = "completed"
    session["score"] = evaluation.get("score")
    session["evaluation"] = evaluation
    session["updated_at"] = datetime.now().isoformat()
    path = _get_session_path(user_id, session_id)
    path.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")

    meta = _load_sessions_meta_sync(user_id)
    for item in meta:
        if item["id"] == session_id:
            item["status"] = "completed"
            item["score"] = evaluation.get("score")
            item["updated_at"] = datetime.now().isoformat()
            break
    _save_sessions_meta_sync(user_id, meta)
    return True


def _delete_session_sync(user_id: str, session_id: str) -> bool:
    path = _get_session_path(user_id, session_id)
    if path.exists():
        path.unlink()
    meta = _load_sessions_meta_sync(user_id)
    new_meta = [m for m in meta if m["id"] != session_id]
    if len(new_meta) == len(meta) and not path.exists():
        return False
    _save_sessions_meta_sync(user_id, new_meta)
    return True


async def create_session(user_id: str, data: dict) -> dict:
    return await asyncio.to_thread(_create_session_sync, user_id, data)


async def get_session(user_id: str, session_id: str) -> Optional[dict]:
    return await asyncio.to_thread(_get_session_sync, user_id, session_id)


async def list_sessions(user_id: str) -> list[dict]:
    return await asyncio.to_thread(_load_sessions_meta_sync, user_id)


async def add_message_to_session(user_id: str, session_id: str, role: str, content: str) -> bool:
    return await asyncio.to_thread(_add_message_sync, user_id, session_id, role, content)


async def finish_session(user_id: str, session_id: str, evaluation: dict) -> bool:
    return await asyncio.to_thread(_finish_session_sync, user_id, session_id, evaluation)


async def delete_session(user_id: str, session_id: str) -> bool:
    return await asyncio.to_thread(_delete_session_sync, user_id, session_id)


async def generate_interview_reply(
    session: dict,
    user_message: str,
) -> str:
    interview_type = session.get("interview_type", "tech")
    system_prompt = SYSTEM_PROMPT_MAP.get(interview_type, SYSTEM_PROMPT_MAP["tech"])

    company = session.get("company", "")
    position = session.get("position", "")
    if company or position:
        system_prompt += f"\n\n面试背景：公司={company}，岗位={position}"

    conversation = []
    for msg in session.get("messages", []):
        conversation.append({"role": msg["role"], "content": msg["content"]})
    conversation.append({"role": "user", "content": user_message})

    prompt = f"{system_prompt}\n\n对话历史：\n"
    for msg in conversation:
        role_label = "面试官" if msg["role"] == "assistant" else "候选人"
        prompt += f"{role_label}：{msg['content']}\n"
    prompt += "\n请以面试官身份回复："

    return await call_llm(prompt, max_tokens=600, temperature=0.7)


async def evaluate_session(session: dict) -> dict:
    interview_type = INTERVIEW_TYPES.get(session.get("interview_type", "tech"), "技术面试")
    conversation_lines = []
    for msg in session.get("messages", []):
        role_label = "面试官" if msg["role"] == "assistant" else "候选人"
        conversation_lines.append(f"{role_label}：{msg['content']}")
    conversation = "\n".join(conversation_lines)

    prompt = EVALUATION_PROMPT.format(
        interview_type=interview_type,
        position=session.get("position", "未知"),
        company=session.get("company", "未知"),
        conversation=conversation,
    )
    result = await call_llm(prompt, max_tokens=2000, temperature=0.5)

    score = None
    for line in result.split("\n"):
        if "综合评分" in line:
            import re
            match = re.search(r'(\d+)', line)
            if match:
                score = int(match.group(1))

    return {"score": score, "evaluation_text": result}
