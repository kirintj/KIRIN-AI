"""规则引擎核心：匹配、优先级、条件组合。"""

import re
from dataclasses import dataclass, field
from enum import Enum


class MatchType(str, Enum):
    CONTAINS = "contains"        # 包含关键词
    STARTS_WITH = "starts_with"  # 以...开头
    REGEX = "regex"              # 正则匹配
    EXACT = "exact"              # 精确匹配


class LogicOp(str, Enum):
    AND = "and"
    OR = "or"


@dataclass
class Condition:
    """单个匹配条件"""
    type: MatchType
    values: list[str]          # 关键词列表
    logic: LogicOp = LogicOp.OR  # 多个value之间的逻辑


@dataclass
class Rule:
    """单条规则"""
    name: str                  # 规则名称（唯一标识）
    intent: str                # 目标意图
    conditions: list[Condition]  # 条件列表（多个条件之间是AND）
    priority: int = 0          # 优先级，越大越优先
    enabled: bool = True       # 是否启用
    description: str = ""      # 描述

    def __post_init__(self):
        if isinstance(self.conditions, dict):
            # 从JSON加载时转换
            self.conditions = [Condition(**c) for c in self.conditions]


@dataclass
class MatchResult:
    """匹配结果"""
    intent: str
    rule_name: str
    confidence: float = 1.0


class RuleEngine:
    """规则引擎"""

    def __init__(self):
        self._rules: list[Rule] = []

    def load(self, rules: list[Rule]):
        """加载规则列表"""
        self._rules = sorted(
            [r for r in rules if r.enabled],
            key=lambda r: r.priority,
            reverse=True,
        )

    def match(self, text: str) -> MatchResult | None:
        """匹配文本，返回最高优先级的匹配结果"""
        for rule in self._rules:
            if self._match_rule(text, rule):
                return MatchResult(
                    intent=rule.intent,
                    rule_name=rule.name,
                )
        return None

    def _match_rule(self, text: str, rule: Rule) -> bool:
        """检查文本是否匹配规则的所有条件（AND逻辑）"""
        return all(self._match_condition(text, cond) for cond in rule.conditions)

    def _match_condition(self, text: str, cond: Condition) -> bool:
        """检查文本是否匹配单个条件"""
        if cond.logic == LogicOp.OR:
            return any(self._match_value(text, v, cond.type) for v in cond.values)
        else:  # AND
            return all(self._match_value(text, v, cond.type) for v in cond.values)

    def _match_value(self, text: str, value: str, match_type: MatchType) -> bool:
        """检查文本是否匹配单个值"""
        if match_type == MatchType.CONTAINS:
            return value in text
        elif match_type == MatchType.STARTS_WITH:
            return text.startswith(value)
        elif match_type == MatchType.REGEX:
            return bool(re.search(value, text))
        elif match_type == MatchType.EXACT:
            return text == value
        return False

    @property
    def rule_count(self) -> int:
        return len(self._rules)

    def get_rules(self) -> list[Rule]:
        """获取所有规则（包括禁用的）"""
        return self._rules.copy()
