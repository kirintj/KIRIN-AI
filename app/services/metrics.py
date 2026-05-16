"""应用指标收集：计数器、直方图、Prometheus格式暴露。"""

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Counter:
    name: str
    help: str = ""
    value: float = 0
    labels: dict[str, str] = field(default_factory=dict)

    def inc(self, value: float = 1) -> None:
        self.value += value


@dataclass
class Histogram:
    name: str
    help: str = ""
    buckets: list[float] = field(default_factory=lambda: [0.01, 0.05, 0.1, 0.5, 1, 5, 10])
    sum: float = 0
    count: int = 0
    bucket_counts: dict[float, int] = field(default_factory=dict)

    def __post_init__(self):
        if not self.bucket_counts:
            self.bucket_counts = {b: 0 for b in self.buckets}

    def observe(self, value: float) -> None:
        self.sum += value
        self.count += 1
        for bucket in self.buckets:
            if value <= bucket:
                self.bucket_counts[bucket] += 1


class MetricsCollector:
    """指标收集器（线程安全）"""

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: dict[str, Counter] = {}
        self._histograms: dict[str, Histogram] = {}

    def counter(self, name: str, help: str = "") -> Counter:
        """获取或创建计数器"""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name=name, help=help)
            return self._counters[name]

    def histogram(self, name: str, help: str = "", buckets: list[float] | None = None) -> Histogram:
        """获取或创建直方图"""
        with self._lock:
            if name not in self._histograms:
                kwargs = {"name": name, "help": help}
                if buckets:
                    kwargs["buckets"] = buckets
                self._histograms[name] = Histogram(**kwargs)
            return self._histograms[name]

    def to_prometheus(self) -> str:
        """导出Prometheus格式指标"""
        lines = []

        with self._lock:
            for counter in self._counters.values():
                if counter.help:
                    lines.append(f"# HELP {counter.name} {counter.help}")
                lines.append(f"# TYPE {counter.name} counter")
                lines.append(f"{counter.name} {counter.value}")

            for histogram in self._histograms.values():
                if histogram.help:
                    lines.append(f"# HELP {histogram.name} {histogram.help}")
                lines.append(f"# TYPE {histogram.name} histogram")
                for bucket, count in sorted(histogram.bucket_counts.items()):
                    lines.append(f'{histogram.name}_bucket{{le="{bucket}"}} {count}')
                lines.append(f"{histogram.name}_bucket{{le=\"+Inf\"}} {histogram.count}")
                lines.append(f"{histogram.name}_sum {histogram.sum}")
                lines.append(f"{histogram.name}_count {histogram.count}")

        return "\n".join(lines) + "\n"


# 全局单例
_collector: MetricsCollector | None = None


def get_metrics() -> MetricsCollector:
    """获取全局指标收集器"""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector
