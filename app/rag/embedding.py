import logging
from openai import OpenAI, AsyncOpenAI
import httpx
from app.settings import settings

_logger = logging.getLogger(__name__)

# 同步客户端缓存
_sync_client: OpenAI | None = None
_sync_api_key: str = ""
_sync_base_url: str = ""

# 异步客户端缓存
_async_client: AsyncOpenAI | None = None
_async_api_key: str = ""
_async_base_url: str = ""


def _get_sync_client(api_key: str, base_url: str) -> OpenAI:
    global _sync_client, _sync_api_key, _sync_base_url
    if _sync_client is None or api_key != _sync_api_key or base_url != _sync_base_url:
        _sync_client = OpenAI(api_key=api_key, base_url=base_url)
        _sync_api_key = api_key
        _sync_base_url = base_url
    return _sync_client


def _get_async_client(api_key: str, base_url: str) -> AsyncOpenAI:
    global _async_client, _async_api_key, _async_base_url
    if _async_client is None or api_key != _async_api_key or base_url != _async_base_url:
        _async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=httpx.Timeout(60.0, connect=10.0),
        )
        _async_api_key = api_key
        _async_base_url = base_url
    return _async_client


async def _get_embedding_config() -> dict:
    """从 DB 缓存读取 embedding 配置"""
    try:
        from app.services.config import get_cached_ai_config
        cfg = await get_cached_ai_config()
        return {
            "model": cfg.get("embedding_model") or settings.EMBEDDING_MODEL,
            "dimension": int(cfg.get("embedding_dimension") or settings.EMBEDDING_DIMENSION),
            "batch_size": settings.EMBEDDING_BATCH_SIZE,
            "api_key": cfg.get("embedding_api_key") or settings.EMBEDDING_API_KEY,
            "base_url": cfg.get("embedding_base_url") or settings.EMBEDDING_BASE_URL,
        }
    except Exception:
        return {
            "model": settings.EMBEDDING_MODEL,
            "dimension": settings.EMBEDDING_DIMENSION,
            "batch_size": settings.EMBEDDING_BATCH_SIZE,
            "api_key": settings.EMBEDDING_API_KEY,
            "base_url": settings.EMBEDDING_BASE_URL,
        }


class DashScopeEmbeddingFunction:
    """DashScope 向量模型封装，兼容 ChromaDB EmbeddingFunction 协议"""

    def __init__(
        self,
        model: str | None = None,
        dimension: int | None = None,
        batch_size: int | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self.model = model or settings.EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self.batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        self.api_key = api_key or settings.EMBEDDING_API_KEY
        self.base_url = base_url or settings.EMBEDDING_BASE_URL

    def name(self) -> str:
        return f"dashscope_{self.model}"

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def __call__(self, input: list[str]) -> list[list[float]]:
        """ChromaDB 同步调用入口，自动分批处理"""
        if not input:
            return []
        all_embeddings: list[list[float]] = []
        for i in range(0, len(input), self.batch_size):
            batch = input[i : i + self.batch_size]
            embeddings = self._embed_batch(batch)
            all_embeddings.extend(embeddings)
        return all_embeddings

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        client = _get_sync_client(self.api_key, self.base_url)
        try:
            response = client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.dimension,
            )
            return [item.embedding for item in response.data]
        except Exception:
            _logger.exception("DashScope embedding 调用失败, model=%s", self.model)
            raise


async def async_get_embeddings(
    texts: list[str],
    model: str | None = None,
    dimension: int | None = None,
) -> list[list[float]]:
    """异步获取向量，复用全局 AsyncOpenAI 客户端"""
    cfg = await _get_embedding_config()
    _model = model or cfg["model"]
    _dimension = dimension or cfg["dimension"]
    batch_size = cfg["batch_size"]
    api_key = cfg["api_key"]
    base_url = cfg["base_url"]

    client = _get_async_client(api_key, base_url)

    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            response = await client.embeddings.create(
                model=_model,
                input=batch,
                dimensions=_dimension,
            )
            all_embeddings.extend([item.embedding for item in response.data])
        except Exception:
            _logger.exception("异步 embedding 调用失败, model=%s", _model)
            raise

    return all_embeddings
