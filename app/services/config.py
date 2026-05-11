from app.log import logger
from app.repositories.config import sysconfig_repository
from app.settings import settings

AI_CONFIG_DEFAULTS = {
    "model_name": settings.MODEL_NAME,
    "max_tokens": str(settings.MAX_TOKENS),
    "temperature": str(settings.TEMPERATURE),
    "embedding_model": settings.EMBEDDING_MODEL,
    "embedding_dimension": str(settings.EMBEDDING_DIMENSION),
    "rag_enable_query_rewrite": str(settings.RAG_ENABLE_QUERY_REWRITE).lower(),
    "rag_enable_rerank": str(settings.RAG_ENABLE_RERANK).lower(),
    "rag_enable_hybrid_search": str(settings.RAG_ENABLE_HYBRID_SEARCH).lower(),
    "rag_enable_context_compress": str(settings.RAG_ENABLE_CONTEXT_COMPRESS).lower(),
}


class SysConfigService:
    def __init__(self):
        self.repo = sysconfig_repository

    async def get_ai_config(self) -> dict:
        db_configs = await self.repo.get_all_as_dict()
        result = {}
        for key, default_value in AI_CONFIG_DEFAULTS.items():
            result[key] = db_configs.get(key, default_value)
        return result

    async def update_ai_config(self, configs: list[dict]) -> dict:
        for item in configs:
            key = item.get("key")
            value = str(item.get("value", ""))
            desc = item.get("desc")
            if key in AI_CONFIG_DEFAULTS:
                await self.repo.upsert(key=key, value=value, desc=desc)
            else:
                logger.warning("忽略未知的配置项: %s", key)
        return await self.get_ai_config()

    async def init_defaults(self):
        for key, default_value in AI_CONFIG_DEFAULTS.items():
            existing = await self.repo.get_by_key(key)
            if not existing:
                await self.repo.upsert(key=key, value=default_value)


sysconfig_service = SysConfigService()
