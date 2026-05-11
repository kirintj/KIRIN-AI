"""全局常量定义，消除魔法数字和硬编码。"""

# ── HTTP ────────────────────────────────────────────────────────────────────
MAX_REQUEST_BODY_SIZE = 1024 * 1024  # 1MB，审计日志截断阈值

# ── LLM ─────────────────────────────────────────────────────────────────────
LLM_TIMEOUT_SECONDS = 120.0
LLM_CONNECT_TIMEOUT_SECONDS = 10.0
JOB_ASSISTANT_TIMEOUT_SECONDS = 180

# ── Memory ──────────────────────────────────────────────────────────────────
MEMORY_HISTORY_THRESHOLD = 3   # 触发个性化推荐的最少历史条数
MEMORY_HISTORY_SLICE = 10      # 发送给 LLM 的最大历史条数
MEMORY_MAX_HISTORY = 20        # 每用户最大记忆条数

# ── Content truncation ──────────────────────────────────────────────────────
CONTENT_TRUNCATION_LENGTH = 30     # 会话标题自动截断长度
CONTENT_PREVIEW_LENGTH = 200       # 历史文本预览长度
CONTENT_RAG_PREVIEW_LENGTH = 300   # RAG 上下文预览长度

# ── Business statuses ───────────────────────────────────────────────────────
STATUS_LIST = ["wishlist", "applied", "screening", "interview", "offer", "rejected"]
STATUS_LABELS = {
    "wishlist": "意向",
    "applied": "已投递",
    "screening": "筛选中",
    "interview": "面试中",
    "offer": "已录用",
    "rejected": "已拒绝",
}
STATUS_COLORS = {
    "wishlist": "#86909C",
    "applied": "#0A59F7",
    "screening": "#722ED1",
    "interview": "#ED6F21",
    "offer": "#64BB5C",
    "rejected": "#E84026",
}
