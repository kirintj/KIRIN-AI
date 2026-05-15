import logging
from openai import OpenAI, AsyncOpenAI
import httpx
from app.settings import settings

_logger = logging.getLogger(__name__)

_sync_client: OpenAI | None = None
_async_client: AsyncOpenAI | None = None


def _get_sync_client() -> OpenAI:
    global _sync_client
    if _sync_client is None:
        _sync_client = OpenAI(
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_BASE_URL,
        )
    return _sync_client


def _get_async_client() -> AsyncOpenAI:
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_BASE_URL,
            timeout=httpx.Timeout(60.0, connect=10.0),
        )
    return _async_client


async def _get_embedding_config() -> tuple[str, int, int]:
    """从 DB 缓存读取 embedding 配置，返回 (model, dimension, batch_size)"""
    try:
        from app.services.config import get_cached_ai_config
        cfg = await get_cached_ai_config()
        model = cfg.get("embedding_model") or settings.EMBEDDING_MODEL
        dimension = int(cfg.get("embedding_dimension") or settings.EMBEDDING_DIMENSION)
        return model, dimension, settings.EMBEDDING_BATCH_SIZE
    except Exception:
        return settings.EMBEDDING_MODEL, settings.EMBEDDING_DIMENSION, settings.EMBEDDING_BATCH_SIZE


class DashScopeEmbeddingFunction:
    """DashScope 向量模型封装，兼容 ChromaDB EmbeddingFunction 协议"""

    def __init__(
        self,
        model: str | None = None,
        dimension: int | None = None,
        batch_size: int | None = None,
    ):
        self.model = model or settings.EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self.batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE

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
        client = _get_sync_client()
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
    if model is None or dimension is None:
        db_model, db_dimension, batch_size = await _get_embedding_config()
        _model = model or db_model
        _dimension = dimension or db_dimension
    else:
        _model = model
        _dimension = dimension
        batch_size = settings.EMBEDDING_BATCH_SIZE

    client = _get_async_client()

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
