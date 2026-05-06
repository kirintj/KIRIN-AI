from pydantic import BaseModel, Field


class ConfigItem(BaseModel):
    key: str = Field(..., description="配置键")
    value: str = Field("", description="配置值")
    desc: str | None = Field(None, description="配置描述")


class ConfigUpdate(BaseModel):
    configs: list[ConfigItem] = Field(..., description="配置列表")
