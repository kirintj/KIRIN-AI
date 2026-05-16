"""规则加载器：从JSON文件加载规则，支持热更新。"""

import json
import logging
from pathlib import Path

from .engine import Rule, Condition, MatchType, LogicOp, RuleEngine

_logger = logging.getLogger(__name__)

# 默认规则文件路径
_DEFAULT_RULES_PATH = Path(__file__).parent / "default_rules.json"

# 全局规则引擎实例
_engine: RuleEngine | None = None
_rules_path: Path = _DEFAULT_RULES_PATH


def _parse_rule(data: dict) -> Rule:
    """将JSON字典解析为Rule对象"""
    conditions = []
    for cond_data in data.get("conditions", []):
        conditions.append(Condition(
            type=MatchType(cond_data["type"]),
            values=cond_data["values"],
            logic=LogicOp(cond_data.get("logic", "or")),
        ))

    return Rule(
        name=data["name"],
        intent=data["intent"],
        conditions=conditions,
        priority=data.get("priority", 0),
        enabled=data.get("enabled", True),
        description=data.get("description", ""),
    )


def load_rules(path: Path | str | None = None) -> RuleEngine:
    """从JSON文件加载规则"""
    global _engine, _rules_path

    if path is not None:
        _rules_path = Path(path)

    engine = RuleEngine()

    if not _rules_path.exists():
        _logger.warning("rules file not found: %s, using empty engine", _rules_path)
        _engine = engine
        return engine

    try:
        with open(_rules_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        rules_data = data if isinstance(data, list) else data.get("rules", [])
        rules = [_parse_rule(r) for r in rules_data]
        engine.load(rules)
        _logger.info("loaded %d rules from %s", engine.rule_count, _rules_path)

    except Exception:
        _logger.exception("failed to load rules from %s", _rules_path)

    _engine = engine
    return engine


def reload_rules() -> RuleEngine:
    """重新加载规则（热更新）"""
    return load_rules(_rules_path)


def get_engine() -> RuleEngine:
    """获取全局规则引擎实例"""
    global _engine
    if _engine is None:
        load_rules()
    return _engine
