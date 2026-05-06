from app.log import logger
from app.repositories.config import sysconfig_repository

AI_CONFIG_DEFAULTS = {
    "model_name": "qwen-turbo",
    "max_tokens": "2000",
    "temperature": "0.7",
    "embedding_model": "text-embedding-v3",
    "embedding_dimension": "1024",
    "rag_enable_query_rewrite": "true",
    "rag_enable_rerank": "true",
    "rag_enable_hybrid_search": "true",
    "rag_enable_context_compress": "false",
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
