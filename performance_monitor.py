"""
性能监控和指标收集系统

提供轻量级的性能监控功能，用于跟踪WorkflowState和AI更新器的关键性能指标。
"""

import time
import threading
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, NamedTuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import statistics
import json

# 配置日志
logger = logging.getLogger(__name__)

class MetricType(Enum):
    """指标类型枚举"""
    COUNTER = "counter"           # 计数器 - 单调递增
    GAUGE = "gauge"              # 测量仪 - 可增可减的值
    HISTOGRAM = "histogram"      # 直方图 - 值的分布
    TIMER = "timer"              # 计时器 - 时间测量
    RATE = "rate"                # 速率 - 每秒事件数

class MetricUnit(Enum):
    """指标单位枚举"""
    BYTES = "bytes"
    MILLISECONDS = "ms"
    SECONDS = "s"
    COUNT = "count"
    PERCENTAGE = "percentage"
    TOKENS = "tokens"
    CALLS_PER_SECOND = "calls/s"

@dataclass
class MetricDefinition:
    """指标定义"""
    name: str
    metric_type: MetricType
    unit: MetricUnit
    description: str
    tags: Dict[str, str] = field(default_factory=dict)

class MetricValue(NamedTuple):
    """指标值"""
    value: float
    timestamp: datetime
    tags: Dict[str, str] = {}

@dataclass
class MetricStatistics:
    """指标统计信息"""
    count: int = 0
    sum: float = 0.0
    min: float = float('inf')
    max: float = float('-inf')
    avg: float = 0.0
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    recent_values: deque = field(default_factory=lambda: deque(maxlen=1000))

    def update(self, value: float):
        """更新统计信息"""
        self.count += 1
        self.sum += value
        self.min = min(self.min, value)
        self.max = max(self.max, value)
        self.avg = self.sum / self.count
        
        self.recent_values.append(value)
        
        # 计算百分位数（仅当有足够数据时）
        if len(self.recent_values) >= 10:
            sorted_values = sorted(self.recent_values)
            n = len(sorted_values)
            self.p50 = sorted_values[int(n * 0.5)]
            self.p95 = sorted_values[int(n * 0.95)]
            self.p99 = sorted_values[int(n * 0.99)]

class PerformanceTimer:
    """性能计时器上下文管理器"""
    
    def __init__(self, metric_collector: 'MetricCollector', metric_name: str, tags: Dict[str, str] = None):
        self.metric_collector = metric_collector
        self.metric_name = metric_name
        self.tags = tags or {}
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration_ms = (time.perf_counter() - self.start_time) * 1000
            self.metric_collector.record_timer(self.metric_name, duration_ms, self.tags)

class MetricCollector:
    """指标收集器"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self._metrics: Dict[str, MetricDefinition] = {}
        self._values: Dict[str, List[MetricValue]] = defaultdict(list)
        self._statistics: Dict[str, MetricStatistics] = defaultdict(MetricStatistics)
        self._lock = threading.RLock()
        
        # 注册默认指标
        self._register_default_metrics()
        
    def _register_default_metrics(self):
        """注册默认指标"""
        default_metrics = [
            # WorkflowState 内存指标
            MetricDefinition(
                "workflow_state_memory_bytes",
                MetricType.GAUGE,
                MetricUnit.BYTES,
                "WorkflowState对象内存使用量"
            ),
            MetricDefinition(
                "workflow_state_history_count",
                MetricType.GAUGE,
                MetricUnit.COUNT,
                "WorkflowState历史记录数量"
            ),
            MetricDefinition(
                "workflow_state_serialized_size_bytes",
                MetricType.GAUGE,
                MetricUnit.BYTES,
                "WorkflowState序列化大小"
            ),
            
            # 状态更新性能指标
            MetricDefinition(
                "state_update_duration_ms",
                MetricType.TIMER,
                MetricUnit.MILLISECONDS,
                "状态更新耗时"
            ),
            MetricDefinition(
                "state_update_count",
                MetricType.COUNTER,
                MetricUnit.COUNT,
                "状态更新次数"
            ),
            
            # AI调用性能指标
            MetricDefinition(
                "ai_call_duration_ms",
                MetricType.TIMER,
                MetricUnit.MILLISECONDS,
                "AI调用耗时"
            ),
            MetricDefinition(
                "ai_call_count",
                MetricType.COUNTER,
                MetricUnit.COUNT,
                "AI调用次数"
            ),
            MetricDefinition(
                "ai_call_tokens",
                MetricType.HISTOGRAM,
                MetricUnit.TOKENS,
                "AI调用token消耗"
            ),
            MetricDefinition(
                "ai_call_success_rate",
                MetricType.GAUGE,
                MetricUnit.PERCENTAGE,
                "AI调用成功率"
            ),
            
            # 缓存性能指标
            MetricDefinition(
                "cache_hit_count",
                MetricType.COUNTER,
                MetricUnit.COUNT,
                "缓存命中次数"
            ),
            MetricDefinition(
                "cache_miss_count",
                MetricType.COUNTER,
                MetricUnit.COUNT,
                "缓存失效次数"
            ),
            MetricDefinition(
                "cache_hit_rate",
                MetricType.GAUGE,
                MetricUnit.PERCENTAGE,
                "缓存命中率"
            ),
            
            # 系统资源指标
            MetricDefinition(
                "system_memory_usage_bytes",
                MetricType.GAUGE,
                MetricUnit.BYTES,
                "系统内存使用量"
            ),
            MetricDefinition(
                "system_cpu_usage_percentage",
                MetricType.GAUGE,
                MetricUnit.PERCENTAGE,
                "系统CPU使用率"
            ),
        ]
        
        for metric in default_metrics:
            self.register_metric(metric)
    
    def register_metric(self, metric: MetricDefinition):
        """注册指标"""
        with self._lock:
            self._metrics[metric.name] = metric
            logger.debug(f"注册指标: {metric.name} ({metric.metric_type.value})")
    
    def record_counter(self, name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """记录计数器指标"""
        self._record_metric(name, value, tags)
    
    def record_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """记录测量仪指标"""
        self._record_metric(name, value, tags)
    
    def record_timer(self, name: str, duration_ms: float, tags: Dict[str, str] = None):
        """记录计时器指标"""
        self._record_metric(name, duration_ms, tags)
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """记录直方图指标"""
        self._record_metric(name, value, tags)
    
    def _record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """记录指标值"""
        with self._lock:
            if name not in self._metrics:
                logger.warning(f"未注册的指标: {name}")
                return
            
            tags = tags or {}
            metric_value = MetricValue(value, datetime.now(), tags)
            
            # 限制存储的值数量
            if len(self._values[name]) >= self.max_metrics:
                self._values[name] = self._values[name][-self.max_metrics//2:]
            
            self._values[name].append(metric_value)
            self._statistics[name].update(value)
    
    def get_timer(self, name: str, tags: Dict[str, str] = None) -> PerformanceTimer:
        """获取计时器上下文管理器"""
        return PerformanceTimer(self, name, tags)
    
    def get_metric_statistics(self, name: str) -> Optional[MetricStatistics]:
        """获取指标统计信息"""
        with self._lock:
            return self._statistics.get(name)
    
    def get_all_statistics(self) -> Dict[str, MetricStatistics]:
        """获取所有指标统计信息"""
        with self._lock:
            return dict(self._statistics)
    
    def get_recent_values(self, name: str, limit: int = 100) -> List[MetricValue]:
        """获取最近的指标值"""
        with self._lock:
            values = self._values.get(name, [])
            return values[-limit:] if values else []
    
    def clear_metrics(self, name: Optional[str] = None):
        """清除指标数据"""
        with self._lock:
            if name:
                self._values.pop(name, None)
                self._statistics.pop(name, None)
            else:
                self._values.clear()
                self._statistics.clear()
    
    def export_metrics(self, format: str = "json") -> str:
        """导出指标数据"""
        with self._lock:
            if format.lower() == "json":
                return self._export_json()
            elif format.lower() == "prometheus":
                return self._export_prometheus()
            else:
                raise ValueError(f"不支持的导出格式: {format}")
    
    def _export_json(self) -> str:
        """导出为JSON格式"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {}
        }
        
        for name, stats in self._statistics.items():
            metric_def = self._metrics.get(name)
            if metric_def:
                data["metrics"][name] = {
                    "definition": {
                        "type": metric_def.metric_type.value,
                        "unit": metric_def.unit.value,
                        "description": metric_def.description
                    },
                    "statistics": {
                        "count": stats.count,
                        "sum": stats.sum,
                        "min": stats.min if stats.min != float('inf') else None,
                        "max": stats.max if stats.max != float('-inf') else None,
                        "avg": stats.avg,
                        "p50": stats.p50,
                        "p95": stats.p95,
                        "p99": stats.p99
                    }
                }
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _export_prometheus(self) -> str:
        """导出为Prometheus格式"""
        lines = []
        
        for name, stats in self._statistics.items():
            metric_def = self._metrics.get(name)
            if not metric_def:
                continue
            
            # HELP行
            lines.append(f"# HELP {name} {metric_def.description}")
            
            # TYPE行
            prom_type = {
                MetricType.COUNTER: "counter",
                MetricType.GAUGE: "gauge",
                MetricType.HISTOGRAM: "histogram",
                MetricType.TIMER: "histogram"
            }.get(metric_def.metric_type, "gauge")
            lines.append(f"# TYPE {name} {prom_type}")
            
            # 数据行
            if stats.count > 0:
                lines.append(f"{name}_count {stats.count}")
                lines.append(f"{name}_sum {stats.sum}")
                if stats.min != float('inf'):
                    lines.append(f"{name}_min {stats.min}")
                if stats.max != float('-inf'):
                    lines.append(f"{name}_max {stats.max}")
                lines.append(f"{name}_avg {stats.avg}")
                
                # 百分位数
                if stats.p50 > 0:
                    lines.append(f"{name}{{quantile=\"0.5\"}} {stats.p50}")
                if stats.p95 > 0:
                    lines.append(f"{name}{{quantile=\"0.95\"}} {stats.p95}")
                if stats.p99 > 0:
                    lines.append(f"{name}{{quantile=\"0.99\"}} {stats.p99}")
        
        return "\n".join(lines)

class SystemResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self, metric_collector: MetricCollector):
        self.metric_collector = metric_collector
        self._monitoring = False
        self._monitor_thread = None
        self._monitor_interval = 5.0  # 5秒间隔
    
    def start_monitoring(self, interval: float = 5.0):
        """开始监控系统资源"""
        if self._monitoring:
            return
        
        self._monitor_interval = interval
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info(f"系统资源监控已启动，间隔: {interval}秒")
    
    def stop_monitoring(self):
        """停止监控系统资源"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        logger.info("系统资源监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self._monitoring:
            try:
                # 内存使用情况
                memory_info = psutil.virtual_memory()
                self.metric_collector.record_gauge(
                    "system_memory_usage_bytes",
                    memory_info.used
                )
                
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metric_collector.record_gauge(
                    "system_cpu_usage_percentage",
                    cpu_percent
                )
                
                time.sleep(self._monitor_interval)
                
            except Exception as e:
                logger.error(f"系统资源监控错误: {e}")
                time.sleep(self._monitor_interval)

class PerformanceMonitor:
    """性能监控主类"""
    
    def __init__(self, enable_system_monitoring: bool = True):
        self.metric_collector = MetricCollector()
        self.system_monitor = SystemResourceMonitor(self.metric_collector)
        self._enabled = True
        
        if enable_system_monitoring:
            self.system_monitor.start_monitoring()
    
    def enable(self):
        """启用性能监控"""
        self._enabled = True
        logger.info("性能监控已启用")
    
    def disable(self):
        """禁用性能监控"""
        self._enabled = False
        logger.info("性能监控已禁用")
    
    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self._enabled
    
    def record_workflow_state_memory(self, memory_bytes: int, history_count: int, serialized_size: int):
        """记录WorkflowState内存指标"""
        if not self._enabled:
            return
        
        self.metric_collector.record_gauge("workflow_state_memory_bytes", memory_bytes)
        self.metric_collector.record_gauge("workflow_state_history_count", history_count)
        self.metric_collector.record_gauge("workflow_state_serialized_size_bytes", serialized_size)
    
    def record_state_update(self, duration_ms: float, success: bool = True):
        """记录状态更新指标"""
        if not self._enabled:
            return
        
        self.metric_collector.record_timer("state_update_duration_ms", duration_ms)
        self.metric_collector.record_counter("state_update_count")
    
    def record_ai_call(self, duration_ms: float, tokens: int, success: bool = True):
        """记录AI调用指标"""
        if not self._enabled:
            return
        
        self.metric_collector.record_timer("ai_call_duration_ms", duration_ms)
        self.metric_collector.record_counter("ai_call_count")
        self.metric_collector.record_histogram("ai_call_tokens", tokens)
        
        # 更新成功率
        self._update_success_rate("ai_call_success_rate", success)
    
    def record_cache_hit(self):
        """记录缓存命中"""
        if not self._enabled:
            return
        
        self.metric_collector.record_counter("cache_hit_count")
        self._update_cache_hit_rate()
    
    def record_cache_miss(self):
        """记录缓存失效"""
        if not self._enabled:
            return
        
        self.metric_collector.record_counter("cache_miss_count")
        self._update_cache_hit_rate()
    
    def _update_success_rate(self, metric_name: str, success: bool):
        """更新成功率指标"""
        # 简化的成功率计算 - 基于最近的操作
        stats = self.metric_collector.get_metric_statistics(metric_name.replace("_rate", "_count"))
        if stats and stats.count > 0:
            # 这里可以实现更复杂的成功率计算逻辑
            pass
    
    def _update_cache_hit_rate(self):
        """更新缓存命中率"""
        hit_stats = self.metric_collector.get_metric_statistics("cache_hit_count")
        miss_stats = self.metric_collector.get_metric_statistics("cache_miss_count")
        
        if hit_stats and miss_stats:
            total = hit_stats.sum + miss_stats.sum
            if total > 0:
                hit_rate = (hit_stats.sum / total) * 100
                self.metric_collector.record_gauge("cache_hit_rate", hit_rate)
    
    def get_timer(self, metric_name: str, tags: Dict[str, str] = None) -> PerformanceTimer:
        """获取计时器"""
        return self.metric_collector.get_timer(metric_name, tags)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        stats = self.metric_collector.get_all_statistics()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_enabled": self._enabled,
            "summary": {},
            "details": {}
        }
        
        # 生成摘要
        for name, stat in stats.items():
            if stat.count > 0:
                report["details"][name] = {
                    "count": stat.count,
                    "avg": round(stat.avg, 2),
                    "min": round(stat.min, 2) if stat.min != float('inf') else None,
                    "max": round(stat.max, 2) if stat.max != float('-inf') else None,
                    "p95": round(stat.p95, 2) if stat.p95 > 0 else None
                }
        
        # 关键指标摘要
        if "ai_call_duration_ms" in stats:
            ai_stats = stats["ai_call_duration_ms"]
            report["summary"]["ai_performance"] = {
                "avg_duration_ms": round(ai_stats.avg, 2),
                "total_calls": ai_stats.count,
                "p95_duration_ms": round(ai_stats.p95, 2) if ai_stats.p95 > 0 else None
            }
        
        if "workflow_state_memory_bytes" in stats:
            memory_stats = stats["workflow_state_memory_bytes"]
            report["summary"]["memory_usage"] = {
                "current_bytes": int(memory_stats.recent_values[-1]) if memory_stats.recent_values else 0,
                "peak_bytes": int(memory_stats.max) if memory_stats.max != float('-inf') else 0
            }
        
        if "cache_hit_rate" in stats:
            cache_stats = stats["cache_hit_rate"]
            report["summary"]["cache_performance"] = {
                "hit_rate_percentage": round(cache_stats.recent_values[-1], 2) if cache_stats.recent_values else 0
            }
        
        return report
    
    def export_metrics(self, format: str = "json") -> str:
        """导出指标"""
        return self.metric_collector.export_metrics(format)
    
    def clear_metrics(self):
        """清除所有指标数据"""
        self.metric_collector.clear_metrics()
        logger.info("已清除所有性能指标数据")
    
    def shutdown(self):
        """关闭性能监控"""
        self.system_monitor.stop_monitoring()
        self._enabled = False
        logger.info("性能监控已关闭")

# 全局性能监控实例
_global_monitor: Optional[PerformanceMonitor] = None

def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor

def configure_performance_monitoring(enabled: bool = True, system_monitoring: bool = True):
    """配置性能监控"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor(enable_system_monitoring=system_monitoring)
    
    if enabled:
        _global_monitor.enable()
    else:
        _global_monitor.disable()

# 便捷装饰器
def monitor_performance(metric_name: str, tags: Dict[str, str] = None):
    """性能监控装饰器"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            if monitor.is_enabled():
                with monitor.get_timer(metric_name, tags):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator 