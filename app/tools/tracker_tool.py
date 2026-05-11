from app.tools.base import BaseTool
from app.utils.chat import call_llm
from app.services.business import tracker_service, STATUS_LIST, STATUS_LABELS


async def _extract_application_fields(query: str) -> dict:
    prompt = (
        "你是一个求职信息解析助手。从用户输入中提取求职申请信息，以 JSON 格式输出。\n\n"
        f"用户输入：{query}\n\n"
        '输出格式：\n'
        '{\n'
        '  "company": "公司名称",\n'
        '  "position": "职位名称",\n'
        '  "status": "wishlist/applied/screening/interview/offer/rejected",\n'
        '  "salary": "薪资范围，无则为空字符串",\n'
        '  "location": "工作地点，无则为空字符串",\n'
        '  "source": "投递渠道，如Boss直聘、拉勾等，无则为空字符串",\n'
        '  "notes": "备注信息",\n'
        '  "contact": "联系人信息，无则为空字符串"\n'
        '}\n\n'
        "状态映射规则：\n"
        "- 想投/意向/考虑中 → wishlist\n"
        "- 已投递/已申请/投了 → applied\n"
        "- 筛选中/评估中/简历审核 → screening\n"
        "- 面试中/约面试/二面/三面 → interview\n"
        "- 录用/offer/入职 → offer\n"
        "- 拒绝/没过/挂了 → rejected\n\n"
        "- 只输出 JSON，不要其他内容"
    )
    raw = await call_llm(prompt, max_tokens=400, temperature=0.1)
    return BaseTool.parse_json(raw) or {"company": "", "position": "", "status": "applied"}


async def _generate_tracker_response(query: str, app_data: dict) -> str:
    status_label = STATUS_LABELS.get(app_data.get("status", "applied"), "已投递")
    prompt = (
        "你是一个智能求职助手。用户刚刚添加了一条求职记录，请用自然、友好的语气确认。\n\n"
        f"用户原始输入：{query}\n"
        f"公司：{app_data.get('company', '未知')}\n"
        f"职位：{app_data.get('position', '未知')}\n"
        f"状态：{status_label}\n"
        f"薪资：{app_data.get('salary', '未填写')}\n"
        f"地点：{app_data.get('location', '未填写')}\n\n"
        "要求：\n"
        "- 用 1-2 句话自然地确认已添加记录\n"
        "- 可以适当给出求职建议或提醒\n"
        "- 语气友好、专业\n"
        "- 不要使用 markdown 格式"
    )
    return await call_llm(prompt, max_tokens=200, temperature=0.7)


class TrackerTool(BaseTool):
    name = "tracker_tool"

    async def run(self, query: str = "", **kwargs) -> str:
        user_id = kwargs.get("user_id", "")
        if not user_id:
            raise ValueError("user_id is required")
        fields = await _extract_application_fields(query)
        app_data = await tracker_service.create_application(user_id, **fields)
        return await _generate_tracker_response(query, app_data)
