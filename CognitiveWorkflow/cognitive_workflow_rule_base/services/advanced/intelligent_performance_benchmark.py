# -*- coding: utf-8 -*-
"""
智能性能基准测试系统

实现全面的性能基准测试框架，包括基准数据生成、性能指标评估、
对比分析、回归测试等功能，为系统优化提供科学的性能评估基础。

Phase 3: Self-Learning Optimization 核心组件
"""

from typing import Dict, List, Any, Optional, Tuple, Callable, Union
import logging
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import math
import time
import statistics
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import gc
import random

from ...domain.value_objects import (
    ReplacementStrategyType, StrategyEffectiveness, SituationScore,
    ExecutionMetrics, AdaptiveReplacementConstants, RulePhase
)

logger = logging.getLogger(__name__)


class BenchmarkType(Enum):
    """基准测试类型"""
    PERFORMANCE = "performance"           # 性能测试
    SCALABILITY = "scalability"         # 可扩展性测试
    STRESS = "stress"                    # 压力测试
    ENDURANCE = "endurance"              # 耐久性测试
    REGRESSION = "regression"            # 回归测试
    COMPARATIVE = "comparative"          # 对比测试
    BASELINE = "baseline"                # 基线测试


class BenchmarkMetric(Enum):
    """基准测试指标"""
    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    SUCCESS_RATE = "success_rate"
    ERROR_RATE = "error_rate"
    IMPROVEMENT_SCORE = "improvement_score"
    EFFICIENCY_GAIN = "efficiency_gain"
    RESOURCE_UTILIZATION = "resource_utilization"


@dataclass
class BenchmarkConfiguration:
    """基准测试配置"""
    name: str
    benchmark_type: BenchmarkType
    duration_seconds: int
    iterations: int
    concurrency_level: int
    memory_limit_mb: int
    cpu_limit_percent: float
    metrics_to_collect: List[BenchmarkMetric]
    warm_up_iterations: int = 5
    cool_down_seconds: int = 2
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'benchmark_type': self.benchmark_type.value,
            'duration_seconds': self.duration_seconds,
            'iterations': self.iterations,
            'concurrency_level': self.concurrency_level,
            'memory_limit_mb': self.memory_limit_mb,
            'cpu_limit_percent': self.cpu_limit_percent,
            'metrics_to_collect': [metric.value for metric in self.metrics_to_collect],
            'warm_up_iterations': self.warm_up_iterations,
            'cool_down_seconds': self.cool_down_seconds
        }


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    configuration: BenchmarkConfiguration
    start_time: datetime
    end_time: datetime
    total_duration: float
    iterations_completed: int
    success_count: int
    error_count: int
    metrics: Dict[BenchmarkMetric, List[float]]
    summary_statistics: Dict[str, float]
    system_info: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'configuration': self.configuration.to_dict(),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'total_duration': self.total_duration,
            'iterations_completed': self.iterations_completed,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'metrics': {metric.value: values for metric, values in self.metrics.items()},
            'summary_statistics': self.summary_statistics,
            'system_info': self.system_info
        }


@dataclass
class ComparisonResult:
    """对比结果"""
    baseline_result: BenchmarkResult
    comparison_result: BenchmarkResult
    improvement_metrics: Dict[str, float]
    regression_detected: bool
    significant_changes: List[Dict[str, Any]]
    recommendation: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'baseline_result': self.baseline_result.to_dict(),
            'comparison_result': self.comparison_result.to_dict(),
            'improvement_metrics': self.improvement_metrics,
            'regression_detected': self.regression_detected,
            'significant_changes': self.significant_changes,
            'recommendation': self.recommendation
        }


class SystemResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self, sample_interval: float = 1.0):
        self.sample_interval = sample_interval
        self.monitoring = False
        self.samples: List[Dict[str, float]] = []
        self.monitor_thread: Optional[threading.Thread] = None
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.samples.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
        logger.info("系统资源监控已开始")
    
    def stop_monitoring(self) -> Dict[str, List[float]]:
        """停止监控并返回数据"""
        if not self.monitoring:
            return {}
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        
        # 整理数据
        if not self.samples:
            return {}
        
        result = {
            'cpu_percent': [sample['cpu_percent'] for sample in self.samples],
            'memory_percent': [sample['memory_percent'] for sample in self.samples],
            'memory_mb': [sample['memory_mb'] for sample in self.samples],
            'disk_io_read': [sample['disk_io_read'] for sample in self.samples],
            'disk_io_write': [sample['disk_io_write'] for sample in self.samples],
            'network_sent': [sample['network_sent'] for sample in self.samples],
            'network_recv': [sample['network_recv'] for sample in self.samples]
        }
        
        logger.info(f"系统资源监控已停止，收集了{len(self.samples)}个样本")
        return result
    
    def _monitor_loop(self):
        """监控循环"""
        last_disk_io = psutil.disk_io_counters()
        last_network_io = psutil.net_io_counters()
        
        while self.monitoring:
            try:
                # CPU使用率
                cpu_percent = psutil.cpu_percent()
                
                # 内存使用率
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_mb = memory.used / (1024 * 1024)
                
                # 磁盘IO
                current_disk_io = psutil.disk_io_counters()
                disk_io_read = (current_disk_io.read_bytes - last_disk_io.read_bytes) / self.sample_interval
                disk_io_write = (current_disk_io.write_bytes - last_disk_io.write_bytes) / self.sample_interval
                last_disk_io = current_disk_io
                
                # 网络IO
                current_network_io = psutil.net_io_counters()
                network_sent = (current_network_io.bytes_sent - last_network_io.bytes_sent) / self.sample_interval
                network_recv = (current_network_io.bytes_recv - last_network_io.bytes_recv) / self.sample_interval
                last_network_io = current_network_io
                
                sample = {
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'memory_mb': memory_mb,
                    'disk_io_read': disk_io_read,
                    'disk_io_write': disk_io_write,
                    'network_sent': network_sent,
                    'network_recv': network_recv
                }
                
                self.samples.append(sample)
                
                time.sleep(self.sample_interval)
                
            except Exception as e:
                logger.error(f"系统监控出错: {e}")
                time.sleep(self.sample_interval)


class WorkloadGenerator:
    """工作负载生成器"""
    
    def __init__(self):
        self.strategies = list(ReplacementStrategyType)
        self.rule_phases = list(RulePhase)
    
    def generate_synthetic_context(self, 
                                 complexity_level: str = "medium") -> SituationScore:
        """生成合成上下文"""
        if complexity_level == "low":
            return SituationScore(
                rule_density=random.uniform(0.2, 0.4),
                execution_efficiency=random.uniform(0.7, 0.9),
                goal_progress=random.uniform(0.6, 0.8),
                failure_frequency=random.uniform(0.0, 0.1),
                agent_utilization=random.uniform(0.4, 0.6),
                phase_distribution=random.uniform(0.6, 0.8)
            )
        elif complexity_level == "high":
            return SituationScore(
                rule_density=random.uniform(0.7, 0.9),
                execution_efficiency=random.uniform(0.3, 0.6),
                goal_progress=random.uniform(0.2, 0.5),
                failure_frequency=random.uniform(0.2, 0.4),
                agent_utilization=random.uniform(0.8, 1.0),
                phase_distribution=random.uniform(0.3, 0.5)
            )
        else:  # medium
            return SituationScore(
                rule_density=random.uniform(0.4, 0.7),
                execution_efficiency=random.uniform(0.5, 0.8),
                goal_progress=random.uniform(0.4, 0.7),
                failure_frequency=random.uniform(0.1, 0.2),
                agent_utilization=random.uniform(0.5, 0.8),
                phase_distribution=random.uniform(0.5, 0.7)
            )
    
    def generate_workload_batch(self, 
                              batch_size: int = 10,
                              complexity_distribution: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """生成工作负载批次"""
        if complexity_distribution is None:
            complexity_distribution = {"low": 0.3, "medium": 0.5, "high": 0.2}
        
        workloads = []
        
        for i in range(batch_size):
            # 根据分布选择复杂度
            rand_val = random.random()
            cumulative = 0
            complexity = "medium"
            
            for level, prob in complexity_distribution.items():
                cumulative += prob
                if rand_val <= cumulative:
                    complexity = level
                    break
            
            workload = {
                'workload_id': f"workload_{i:04d}",
                'complexity_level': complexity,
                'context': self.generate_synthetic_context(complexity),
                'strategy': random.choice(self.strategies),
                'parameters': self._generate_random_parameters(),
                'expected_duration': random.uniform(0.1, 2.0)  # 秒
            }
            
            workloads.append(workload)
        
        return workloads
    
    def _generate_random_parameters(self) -> Dict[str, Any]:
        """生成随机参数"""
        return {
            'replacement_ratio': random.uniform(0.1, 0.8),
            'similarity_threshold': random.uniform(0.5, 0.95),
            'performance_threshold': random.uniform(0.3, 0.9),
            'max_rules_per_phase': random.randint(2, 8),
            'max_rules_per_agent': random.randint(3, 10),
            'learning_rate': random.uniform(0.001, 0.1),
            'exploration_factor': random.uniform(0.01, 0.3),
            'conservative_mode': random.choice([True, False])
        }


class BenchmarkExecutor:
    """基准测试执行器"""
    
    def __init__(self):
        self.resource_monitor = SystemResourceMonitor()
        self.workload_generator = WorkloadGenerator()
        self.executor = ThreadPoolExecutor(max_workers=8)
    
    def execute_single_iteration(self, 
                                workload: Dict[str, Any],
                                target_function: Callable) -> Dict[str, Any]:
        """执行单次迭代"""
        start_time = time.time()
        
        try:
            # 执行目标函数
            result = target_function(
                workload['context'],
                workload['strategy'],
                workload['parameters']
            )
            
            execution_time = time.time() - start_time
            success = True
            error_message = None
            
        except Exception as e:
            execution_time = time.time() - start_time
            success = False
            error_message = str(e)
            result = None
            logger.warning(f"基准测试迭代失败: {e}")
        
        return {
            'workload_id': workload['workload_id'],
            'execution_time': execution_time,
            'success': success,
            'error_message': error_message,
            'result': result,
            'memory_usage': self._get_current_memory_usage()
        }
    
    def execute_benchmark(self, 
                         configuration: BenchmarkConfiguration,
                         target_function: Callable) -> BenchmarkResult:
        """执行基准测试"""
        logger.info(f"开始执行基准测试: {configuration.name}")
        
        start_time = datetime.now()
        system_info = self._collect_system_info()
        
        # 初始化结果收集
        metrics = {metric: [] for metric in configuration.metrics_to_collect}
        success_count = 0
        error_count = 0
        iterations_completed = 0
        
        try:
            # 预热
            if configuration.warm_up_iterations > 0:
                logger.info(f"执行预热迭代: {configuration.warm_up_iterations}次")
                self._run_warmup(configuration, target_function)
                time.sleep(configuration.cool_down_seconds)
            
            # 开始资源监控
            self.resource_monitor.start_monitoring()
            
            # 生成工作负载
            total_workloads = []
            batch_size = min(configuration.iterations, 100)  # 分批处理
            
            for batch_start in range(0, configuration.iterations, batch_size):
                batch_end = min(batch_start + batch_size, configuration.iterations)
                batch_workloads = self.workload_generator.generate_workload_batch(
                    batch_end - batch_start
                )
                total_workloads.extend(batch_workloads)
            
            # 执行基准测试
            if configuration.concurrency_level <= 1:
                # 串行执行
                for workload in total_workloads:
                    iteration_result = self.execute_single_iteration(workload, target_function)
                    self._process_iteration_result(iteration_result, metrics, configuration)
                    
                    if iteration_result['success']:
                        success_count += 1
                    else:
                        error_count += 1
                    
                    iterations_completed += 1
                    
                    # 检查时间限制
                    if (datetime.now() - start_time).total_seconds() > configuration.duration_seconds:
                        logger.info("达到时间限制，停止测试")
                        break
            else:
                # 并发执行
                futures = []
                for workload in total_workloads:
                    future = self.executor.submit(self.execute_single_iteration, workload, target_function)
                    futures.append(future)
                    
                    # 控制并发数量
                    if len(futures) >= configuration.concurrency_level:
                        completed_future = next(as_completed(futures))
                        futures.remove(completed_future)
                        
                        iteration_result = completed_future.result()
                        self._process_iteration_result(iteration_result, metrics, configuration)
                        
                        if iteration_result['success']:
                            success_count += 1
                        else:
                            error_count += 1
                        
                        iterations_completed += 1
                        
                        # 检查时间限制
                        if (datetime.now() - start_time).total_seconds() > configuration.duration_seconds:
                            logger.info("达到时间限制，停止测试")
                            break
                
                # 处理剩余的futures
                for future in as_completed(futures):
                    if (datetime.now() - start_time).total_seconds() > configuration.duration_seconds:
                        future.cancel()
                        continue
                    
                    iteration_result = future.result()
                    self._process_iteration_result(iteration_result, metrics, configuration)
                    
                    if iteration_result['success']:
                        success_count += 1
                    else:
                        error_count += 1
                    
                    iterations_completed += 1
            
            # 停止资源监控
            resource_data = self.resource_monitor.stop_monitoring()
            
            # 添加资源使用指标
            if resource_data:
                if BenchmarkMetric.CPU_USAGE in configuration.metrics_to_collect:
                    metrics[BenchmarkMetric.CPU_USAGE] = resource_data['cpu_percent']
                
                if BenchmarkMetric.MEMORY_USAGE in configuration.metrics_to_collect:
                    metrics[BenchmarkMetric.MEMORY_USAGE] = resource_data['memory_mb']
            
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            
            # 计算汇总统计
            summary_statistics = self._calculate_summary_statistics(metrics)
            
            result = BenchmarkResult(
                configuration=configuration,
                start_time=start_time,
                end_time=end_time,
                total_duration=total_duration,
                iterations_completed=iterations_completed,
                success_count=success_count,
                error_count=error_count,
                metrics=metrics,
                summary_statistics=summary_statistics,
                system_info=system_info
            )
            
            logger.info(f"基准测试完成: {configuration.name}, 成功率: {success_count/max(1, iterations_completed):.2%}")
            return result
            
        except Exception as e:
            logger.error(f"基准测试执行失败: {e}")
            self.resource_monitor.stop_monitoring()
            raise
    
    def _run_warmup(self, 
                   configuration: BenchmarkConfiguration,
                   target_function: Callable):
        """运行预热"""
        warmup_workloads = self.workload_generator.generate_workload_batch(
            configuration.warm_up_iterations
        )
        
        for workload in warmup_workloads:
            try:
                self.execute_single_iteration(workload, target_function)
            except:
                pass  # 预热阶段忽略错误
    
    def _process_iteration_result(self, 
                                iteration_result: Dict[str, Any],
                                metrics: Dict[BenchmarkMetric, List[float]],
                                configuration: BenchmarkConfiguration):
        """处理迭代结果"""
        if BenchmarkMetric.EXECUTION_TIME in configuration.metrics_to_collect:
            metrics[BenchmarkMetric.EXECUTION_TIME].append(iteration_result['execution_time'])
        
        if BenchmarkMetric.MEMORY_USAGE in configuration.metrics_to_collect:
            metrics[BenchmarkMetric.MEMORY_USAGE].append(iteration_result['memory_usage'])
        
        if BenchmarkMetric.SUCCESS_RATE in configuration.metrics_to_collect:
            metrics[BenchmarkMetric.SUCCESS_RATE].append(1.0 if iteration_result['success'] else 0.0)
        
        if BenchmarkMetric.ERROR_RATE in configuration.metrics_to_collect:
            metrics[BenchmarkMetric.ERROR_RATE].append(0.0 if iteration_result['success'] else 1.0)
        
        # 如果有结果对象，提取更多指标
        if iteration_result['success'] and iteration_result['result']:
            result_obj = iteration_result['result']
            
            if hasattr(result_obj, 'improvement_score') and BenchmarkMetric.IMPROVEMENT_SCORE in configuration.metrics_to_collect:
                metrics[BenchmarkMetric.IMPROVEMENT_SCORE].append(result_obj.improvement_score)
            
            if hasattr(result_obj, 'get_efficiency_gain') and BenchmarkMetric.EFFICIENCY_GAIN in configuration.metrics_to_collect:
                efficiency_gain = result_obj.get_efficiency_gain()
                if efficiency_gain is not None:
                    metrics[BenchmarkMetric.EFFICIENCY_GAIN].append(efficiency_gain)
    
    def _get_current_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except:
            return 0.0
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """收集系统信息"""
        try:
            return {
                'cpu_count': psutil.cpu_count(),
                'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'disk_usage': {
                    part.device: psutil.disk_usage(part.mountpoint)._asdict() 
                    for part in psutil.disk_partitions()
                },
                'python_version': __import__('sys').version,
                'platform': __import__('platform').platform(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"收集系统信息失败: {e}")
            return {}
    
    def _calculate_summary_statistics(self, 
                                    metrics: Dict[BenchmarkMetric, List[float]]) -> Dict[str, float]:
        """计算汇总统计"""
        summary = {}
        
        for metric, values in metrics.items():
            if not values:
                continue
            
            metric_name = metric.value
            summary.update({
                f"{metric_name}_mean": statistics.mean(values),
                f"{metric_name}_median": statistics.median(values),
                f"{metric_name}_std": statistics.stdev(values) if len(values) > 1 else 0.0,
                f"{metric_name}_min": min(values),
                f"{metric_name}_max": max(values),
                f"{metric_name}_p95": np.percentile(values, 95),
                f"{metric_name}_p99": np.percentile(values, 99)
            })
        
        return summary


class BenchmarkAnalyzer:
    """基准测试分析器"""
    
    def __init__(self):
        self.significance_threshold = 0.05  # 统计显著性阈值
        self.practical_significance_threshold = 0.1  # 实际显著性阈值（10%改变）
    
    def compare_results(self, 
                       baseline: BenchmarkResult,
                       comparison: BenchmarkResult) -> ComparisonResult:
        """对比基准测试结果"""
        logger.info(f"对比基准测试结果: {baseline.configuration.name} vs {comparison.configuration.name}")
        
        # 计算改进指标
        improvement_metrics = self._calculate_improvements(baseline, comparison)
        
        # 检测回归
        regression_detected = self._detect_regression(improvement_metrics)
        
        # 识别显著变化
        significant_changes = self._identify_significant_changes(baseline, comparison)
        
        # 生成建议
        recommendation = self._generate_recommendation(improvement_metrics, regression_detected, significant_changes)
        
        return ComparisonResult(
            baseline_result=baseline,
            comparison_result=comparison,
            improvement_metrics=improvement_metrics,
            regression_detected=regression_detected,
            significant_changes=significant_changes,
            recommendation=recommendation
        )
    
    def _calculate_improvements(self, 
                              baseline: BenchmarkResult,
                              comparison: BenchmarkResult) -> Dict[str, float]:
        """计算改进指标"""
        improvements = {}
        
        # 对比相同的指标
        common_metrics = set(baseline.metrics.keys()) & set(comparison.metrics.keys())
        
        for metric in common_metrics:
            baseline_values = baseline.metrics[metric]
            comparison_values = comparison.metrics[metric]
            
            if not baseline_values or not comparison_values:
                continue
            
            baseline_mean = statistics.mean(baseline_values)
            comparison_mean = statistics.mean(comparison_values)
            
            if baseline_mean == 0:
                continue
            
            # 根据指标类型计算改进（某些指标越小越好）
            if metric in [BenchmarkMetric.EXECUTION_TIME, BenchmarkMetric.MEMORY_USAGE, 
                         BenchmarkMetric.ERROR_RATE, BenchmarkMetric.LATENCY]:
                # 越小越好的指标
                improvement = (baseline_mean - comparison_mean) / baseline_mean
            else:
                # 越大越好的指标
                improvement = (comparison_mean - baseline_mean) / baseline_mean
            
            improvements[metric.value] = improvement
        
        # 汇总统计改进
        baseline_stats = baseline.summary_statistics
        comparison_stats = comparison.summary_statistics
        
        for stat_name in baseline_stats:
            if stat_name in comparison_stats:
                baseline_val = baseline_stats[stat_name]
                comparison_val = comparison_stats[stat_name]
                
                if baseline_val != 0:
                    if 'time' in stat_name.lower() or 'memory' in stat_name.lower() or 'error' in stat_name.lower():
                        improvement = (baseline_val - comparison_val) / baseline_val
                    else:
                        improvement = (comparison_val - baseline_val) / baseline_val
                    
                    improvements[f"summary_{stat_name}"] = improvement
        
        return improvements
    
    def _detect_regression(self, improvements: Dict[str, float]) -> bool:
        """检测性能回归"""
        # 关键性能指标的回归检测
        critical_metrics = [
            'execution_time',
            'memory_usage',
            'error_rate',
            'success_rate'
        ]
        
        regression_count = 0
        for metric in critical_metrics:
            if metric in improvements:
                # 如果关键指标有显著负面变化，视为回归
                if improvements[metric] < -self.practical_significance_threshold:
                    regression_count += 1
        
        # 如果超过一半的关键指标都有回归，则认为存在回归
        return regression_count > len([m for m in critical_metrics if m in improvements]) / 2
    
    def _identify_significant_changes(self, 
                                    baseline: BenchmarkResult,
                                    comparison: BenchmarkResult) -> List[Dict[str, Any]]:
        """识别显著变化"""
        significant_changes = []
        
        # 统计测试（简化实现）
        common_metrics = set(baseline.metrics.keys()) & set(comparison.metrics.keys())
        
        for metric in common_metrics:
            baseline_values = baseline.metrics[metric]
            comparison_values = comparison.metrics[metric]
            
            if len(baseline_values) < 3 or len(comparison_values) < 3:
                continue
            
            # 使用t检验检测统计显著性（简化）
            baseline_mean = statistics.mean(baseline_values)
            comparison_mean = statistics.mean(comparison_values)
            baseline_std = statistics.stdev(baseline_values) if len(baseline_values) > 1 else 0
            comparison_std = statistics.stdev(comparison_values) if len(comparison_values) > 1 else 0
            
            # 计算效应大小（Cohen's d）
            pooled_std = math.sqrt((baseline_std**2 + comparison_std**2) / 2)
            if pooled_std > 0:
                effect_size = abs(comparison_mean - baseline_mean) / pooled_std
            else:
                effect_size = 0
            
            # 计算相对变化
            if baseline_mean != 0:
                relative_change = abs(comparison_mean - baseline_mean) / baseline_mean
            else:
                relative_change = 0
            
            # 判断是否显著
            is_statistically_significant = effect_size > 0.5  # 简化的统计显著性
            is_practically_significant = relative_change > self.practical_significance_threshold
            
            if is_statistically_significant or is_practically_significant:
                change_direction = "improvement" if (
                    (metric in [BenchmarkMetric.EXECUTION_TIME, BenchmarkMetric.MEMORY_USAGE, BenchmarkMetric.ERROR_RATE] 
                     and comparison_mean < baseline_mean) or
                    (metric not in [BenchmarkMetric.EXECUTION_TIME, BenchmarkMetric.MEMORY_USAGE, BenchmarkMetric.ERROR_RATE] 
                     and comparison_mean > baseline_mean)
                ) else "regression"
                
                significant_changes.append({
                    'metric': metric.value,
                    'baseline_mean': baseline_mean,
                    'comparison_mean': comparison_mean,
                    'relative_change': relative_change,
                    'effect_size': effect_size,
                    'change_direction': change_direction,
                    'is_statistically_significant': is_statistically_significant,
                    'is_practically_significant': is_practically_significant
                })
        
        return significant_changes
    
    def _generate_recommendation(self, 
                               improvements: Dict[str, float],
                               regression_detected: bool,
                               significant_changes: List[Dict[str, Any]]) -> str:
        """生成建议"""
        if regression_detected:
            recommendation = "检测到性能回归，建议回滚更改并分析性能下降原因。"
        else:
            positive_changes = [change for change in significant_changes 
                              if change['change_direction'] == 'improvement']
            negative_changes = [change for change in significant_changes 
                              if change['change_direction'] == 'regression']
            
            if len(positive_changes) > len(negative_changes):
                recommendation = f"整体性能有所改善，发现{len(positive_changes)}项改进。"
                if negative_changes:
                    recommendation += f"但需要关注{len(negative_changes)}项性能下降。"
            elif len(negative_changes) > len(positive_changes):
                recommendation = f"存在{len(negative_changes)}项性能问题需要优化。"
            else:
                recommendation = "性能变化不明显，建议进行更多测试或调整优化策略。"
        
        return recommendation
    
    def generate_performance_report(self, 
                                  results: List[BenchmarkResult]) -> Dict[str, Any]:
        """生成性能报告"""
        if not results:
            return {'error': '没有基准测试结果'}
        
        report = {
            'summary': {
                'total_benchmarks': len(results),
                'total_iterations': sum(r.iterations_completed for r in results),
                'total_duration': sum(r.total_duration for r in results),
                'overall_success_rate': sum(r.success_count for r in results) / max(1, sum(r.iterations_completed for r in results))
            },
            'benchmark_results': [result.to_dict() for result in results],
            'performance_trends': self._analyze_performance_trends(results),
            'resource_utilization': self._analyze_resource_utilization(results),
            'recommendations': self._generate_optimization_recommendations(results)
        }
        
        return report
    
    def _analyze_performance_trends(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """分析性能趋势"""
        if len(results) < 2:
            return {'message': '需要至少2个结果来分析趋势'}
        
        # 按时间排序
        sorted_results = sorted(results, key=lambda x: x.start_time)
        
        trends = {}
        
        # 分析执行时间趋势
        execution_times = []
        for result in sorted_results:
            if BenchmarkMetric.EXECUTION_TIME in result.metrics:
                avg_time = statistics.mean(result.metrics[BenchmarkMetric.EXECUTION_TIME])
                execution_times.append(avg_time)
        
        if len(execution_times) >= 2:
            trends['execution_time_trend'] = self._calculate_trend(execution_times)
        
        # 分析内存使用趋势
        memory_usages = []
        for result in sorted_results:
            if BenchmarkMetric.MEMORY_USAGE in result.metrics:
                avg_memory = statistics.mean(result.metrics[BenchmarkMetric.MEMORY_USAGE])
                memory_usages.append(avg_memory)
        
        if len(memory_usages) >= 2:
            trends['memory_usage_trend'] = self._calculate_trend(memory_usages)
        
        return trends
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """计算趋势"""
        if len(values) < 2:
            return {'trend': 'insufficient_data'}
        
        # 简单的线性趋势分析
        x = list(range(len(values)))
        correlation = np.corrcoef(x, values)[0, 1] if len(values) > 1 else 0
        
        # 计算变化率
        first_value = values[0]
        last_value = values[-1]
        change_rate = (last_value - first_value) / first_value if first_value != 0 else 0
        
        if correlation > 0.3:
            trend = "increasing"
        elif correlation < -0.3:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            'trend': trend,
            'correlation': correlation,
            'change_rate': change_rate,
            'first_value': first_value,
            'last_value': last_value
        }
    
    def _analyze_resource_utilization(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """分析资源利用率"""
        cpu_utilizations = []
        memory_utilizations = []
        
        for result in results:
            if BenchmarkMetric.CPU_USAGE in result.metrics:
                cpu_values = result.metrics[BenchmarkMetric.CPU_USAGE]
                if cpu_values:
                    cpu_utilizations.extend(cpu_values)
            
            if BenchmarkMetric.MEMORY_USAGE in result.metrics:
                memory_values = result.metrics[BenchmarkMetric.MEMORY_USAGE]
                if memory_values:
                    memory_utilizations.extend(memory_values)
        
        utilization_analysis = {}
        
        if cpu_utilizations:
            utilization_analysis['cpu'] = {
                'average': statistics.mean(cpu_utilizations),
                'peak': max(cpu_utilizations),
                'stability': 1.0 - (statistics.stdev(cpu_utilizations) / statistics.mean(cpu_utilizations)) if len(cpu_utilizations) > 1 else 1.0
            }
        
        if memory_utilizations:
            utilization_analysis['memory'] = {
                'average_mb': statistics.mean(memory_utilizations),
                'peak_mb': max(memory_utilizations),
                'growth_trend': self._calculate_trend(memory_utilizations)
            }
        
        return utilization_analysis
    
    def _generate_optimization_recommendations(self, results: List[BenchmarkResult]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 分析成功率
        overall_success_rate = sum(r.success_count for r in results) / max(1, sum(r.iterations_completed for r in results))
        if overall_success_rate < 0.95:
            recommendations.append(f"系统成功率较低({overall_success_rate:.1%})，建议增强错误处理和稳定性")
        
        # 分析执行时间
        all_execution_times = []
        for result in results:
            if BenchmarkMetric.EXECUTION_TIME in result.metrics:
                all_execution_times.extend(result.metrics[BenchmarkMetric.EXECUTION_TIME])
        
        if all_execution_times:
            avg_time = statistics.mean(all_execution_times)
            if avg_time > 1.0:  # 超过1秒
                recommendations.append("平均执行时间较长，建议优化算法性能或增加缓存")
            
            time_variance = statistics.stdev(all_execution_times) if len(all_execution_times) > 1 else 0
            if time_variance > avg_time * 0.5:  # 变异系数大于50%
                recommendations.append("执行时间不稳定，建议优化性能一致性")
        
        # 分析内存使用
        all_memory_usage = []
        for result in results:
            if BenchmarkMetric.MEMORY_USAGE in result.metrics:
                all_memory_usage.extend(result.metrics[BenchmarkMetric.MEMORY_USAGE])
        
        if all_memory_usage:
            peak_memory = max(all_memory_usage)
            if peak_memory > 1000:  # 超过1GB
                recommendations.append("内存使用量较高，建议优化内存管理")
        
        if not recommendations:
            recommendations.append("系统性能表现良好，可考虑进一步优化以提升效率")
        
        return recommendations


class IntelligentPerformanceBenchmark:
    """智能性能基准测试系统 - Phase 3核心组件"""
    
    def __init__(self):
        """初始化智能性能基准测试系统"""
        self.executor = BenchmarkExecutor()
        self.analyzer = BenchmarkAnalyzer()
        
        # 预定义的基准测试配置
        self.predefined_configurations = self._create_predefined_configurations()
        
        # 基准测试历史
        self.benchmark_history: List[BenchmarkResult] = []
        self.baseline_results: Dict[str, BenchmarkResult] = {}
        
        logger.info("智能性能基准测试系统已初始化")
    
    def _create_predefined_configurations(self) -> Dict[str, BenchmarkConfiguration]:
        """创建预定义的基准测试配置"""
        configurations = {}
        
        # 快速性能测试
        configurations['quick_performance'] = BenchmarkConfiguration(
            name="快速性能测试",
            benchmark_type=BenchmarkType.PERFORMANCE,
            duration_seconds=60,
            iterations=50,
            concurrency_level=1,
            memory_limit_mb=512,
            cpu_limit_percent=80.0,
            metrics_to_collect=[
                BenchmarkMetric.EXECUTION_TIME,
                BenchmarkMetric.MEMORY_USAGE,
                BenchmarkMetric.SUCCESS_RATE,
                BenchmarkMetric.IMPROVEMENT_SCORE
            ]
        )
        
        # 可扩展性测试
        configurations['scalability'] = BenchmarkConfiguration(
            name="可扩展性测试",
            benchmark_type=BenchmarkType.SCALABILITY,
            duration_seconds=300,
            iterations=200,
            concurrency_level=4,
            memory_limit_mb=1024,
            cpu_limit_percent=90.0,
            metrics_to_collect=[
                BenchmarkMetric.EXECUTION_TIME,
                BenchmarkMetric.THROUGHPUT,
                BenchmarkMetric.CPU_USAGE,
                BenchmarkMetric.MEMORY_USAGE,
                BenchmarkMetric.SUCCESS_RATE
            ]
        )
        
        # 压力测试
        configurations['stress'] = BenchmarkConfiguration(
            name="压力测试",
            benchmark_type=BenchmarkType.STRESS,
            duration_seconds=600,
            iterations=1000,
            concurrency_level=8,
            memory_limit_mb=2048,
            cpu_limit_percent=95.0,
            metrics_to_collect=[
                BenchmarkMetric.EXECUTION_TIME,
                BenchmarkMetric.MEMORY_USAGE,
                BenchmarkMetric.CPU_USAGE,
                BenchmarkMetric.ERROR_RATE,
                BenchmarkMetric.RESOURCE_UTILIZATION
            ]
        )
        
        # 耐久性测试
        configurations['endurance'] = BenchmarkConfiguration(
            name="耐久性测试",
            benchmark_type=BenchmarkType.ENDURANCE,
            duration_seconds=3600,  # 1小时
            iterations=5000,
            concurrency_level=2,
            memory_limit_mb=1024,
            cpu_limit_percent=70.0,
            metrics_to_collect=[
                BenchmarkMetric.EXECUTION_TIME,
                BenchmarkMetric.MEMORY_USAGE,
                BenchmarkMetric.SUCCESS_RATE,
                BenchmarkMetric.ERROR_RATE
            ]
        )
        
        return configurations
    
    def run_benchmark(self, 
                     configuration_name: str,
                     target_function: Callable,
                     custom_config: Optional[BenchmarkConfiguration] = None) -> BenchmarkResult:
        """运行基准测试"""
        try:
            # 选择配置
            if custom_config:
                config = custom_config
            elif configuration_name in self.predefined_configurations:
                config = self.predefined_configurations[configuration_name]
            else:
                raise ValueError(f"未知的基准测试配置: {configuration_name}")
            
            logger.info(f"开始运行基准测试: {config.name}")
            
            # 执行基准测试
            result = self.executor.execute_benchmark(config, target_function)
            
            # 保存到历史
            self.benchmark_history.append(result)
            
            # 如果是基线测试，保存为基线
            if config.benchmark_type == BenchmarkType.BASELINE:
                self.baseline_results[configuration_name] = result
            
            logger.info(f"基准测试完成: {config.name}")
            return result
            
        except Exception as e:
            logger.error(f"运行基准测试失败: {e}")
            raise
    
    def run_comparative_benchmark(self, 
                                 baseline_config_name: str,
                                 comparison_config_name: str,
                                 target_function: Callable) -> ComparisonResult:
        """运行对比基准测试"""
        try:
            logger.info(f"开始对比基准测试: {baseline_config_name} vs {comparison_config_name}")
            
            # 运行基线测试
            baseline_result = self.run_benchmark(baseline_config_name, target_function)
            
            # 运行对比测试
            comparison_result = self.run_benchmark(comparison_config_name, target_function)
            
            # 分析对比结果
            comparison = self.analyzer.compare_results(baseline_result, comparison_result)
            
            logger.info(f"对比基准测试完成，回归检测: {comparison.regression_detected}")
            return comparison
            
        except Exception as e:
            logger.error(f"对比基准测试失败: {e}")
            raise
    
    def run_regression_test(self, 
                           baseline_name: str,
                           target_function: Callable) -> ComparisonResult:
        """运行回归测试"""
        try:
            if baseline_name not in self.baseline_results:
                raise ValueError(f"未找到基线结果: {baseline_name}")
            
            baseline_result = self.baseline_results[baseline_name]
            
            # 使用相同配置运行新测试
            current_result = self.executor.execute_benchmark(
                baseline_result.configuration, 
                target_function
            )
            
            # 对比结果
            comparison = self.analyzer.compare_results(baseline_result, current_result)
            
            logger.info(f"回归测试完成: {baseline_name}, 回归检测: {comparison.regression_detected}")
            return comparison
            
        except Exception as e:
            logger.error(f"回归测试失败: {e}")
            raise
    
    def create_custom_benchmark(self, 
                              name: str,
                              benchmark_type: BenchmarkType,
                              duration_seconds: int = 120,
                              iterations: int = 100,
                              concurrency_level: int = 1,
                              metrics: Optional[List[BenchmarkMetric]] = None) -> BenchmarkConfiguration:
        """创建自定义基准测试配置"""
        if metrics is None:
            metrics = [
                BenchmarkMetric.EXECUTION_TIME,
                BenchmarkMetric.MEMORY_USAGE,
                BenchmarkMetric.SUCCESS_RATE
            ]
        
        config = BenchmarkConfiguration(
            name=name,
            benchmark_type=benchmark_type,
            duration_seconds=duration_seconds,
            iterations=iterations,
            concurrency_level=concurrency_level,
            memory_limit_mb=1024,
            cpu_limit_percent=80.0,
            metrics_to_collect=metrics
        )
        
        # 添加到预定义配置
        self.predefined_configurations[name] = config
        
        logger.info(f"创建自定义基准测试配置: {name}")
        return config
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合报告"""
        try:
            if not self.benchmark_history:
                return {'error': '没有基准测试历史数据'}
            
            # 生成性能报告
            performance_report = self.analyzer.generate_performance_report(self.benchmark_history)
            
            # 添加基准测试系统特定信息
            report = performance_report.copy()
            report.update({
                'benchmark_system_info': {
                    'available_configurations': list(self.predefined_configurations.keys()),
                    'baseline_results_count': len(self.baseline_results),
                    'total_history_count': len(self.benchmark_history),
                    'system_capabilities': self._assess_system_capabilities()
                },
                'configuration_analysis': self._analyze_configuration_effectiveness(),
                'recommendations': self._generate_system_recommendations()
            })
            
            return report
            
        except Exception as e:
            logger.error(f"生成综合报告失败: {e}")
            return {'error': str(e)}
    
    def _assess_system_capabilities(self) -> Dict[str, Any]:
        """评估系统能力"""
        try:
            return {
                'cpu_cores': psutil.cpu_count(),
                'memory_gb': psutil.virtual_memory().total / (1024**3),
                'recommended_concurrency': min(psutil.cpu_count(), 8),
                'recommended_max_iterations': 1000 if psutil.virtual_memory().total > 8 * (1024**3) else 500
            }
        except Exception as e:
            logger.warning(f"评估系统能力失败: {e}")
            return {}
    
    def _analyze_configuration_effectiveness(self) -> Dict[str, Any]:
        """分析配置有效性"""
        config_performance = {}
        
        for result in self.benchmark_history:
            config_name = result.configuration.name
            if config_name not in config_performance:
                config_performance[config_name] = []
            
            # 计算综合性能分数
            success_rate = result.success_count / max(1, result.iterations_completed)
            avg_execution_time = statistics.mean(
                result.metrics.get(BenchmarkMetric.EXECUTION_TIME, [1.0])
            )
            
            # 综合分数（成功率权重更高）
            performance_score = success_rate * 0.7 + (1.0 / max(0.1, avg_execution_time)) * 0.3
            config_performance[config_name].append(performance_score)
        
        # 计算每个配置的平均性能
        config_analysis = {}
        for config_name, scores in config_performance.items():
            config_analysis[config_name] = {
                'average_performance': statistics.mean(scores),
                'performance_stability': 1.0 - (statistics.stdev(scores) / statistics.mean(scores)) if len(scores) > 1 else 1.0,
                'run_count': len(scores)
            }
        
        return config_analysis
    
    def _generate_system_recommendations(self) -> List[str]:
        """生成系统建议"""
        recommendations = []
        
        if len(self.benchmark_history) < 5:
            recommendations.append("建议运行更多基准测试以获得更准确的性能分析")
        
        if not self.baseline_results:
            recommendations.append("建议设置基线测试结果以便进行回归测试")
        
        # 分析测试覆盖度
        tested_types = set(result.configuration.benchmark_type for result in self.benchmark_history)
        all_types = set(BenchmarkType)
        missing_types = all_types - tested_types
        
        if missing_types:
            recommendations.append(f"建议补充以下类型的基准测试: {', '.join(t.value for t in missing_types)}")
        
        return recommendations
    
    def get_benchmark_status(self) -> Dict[str, Any]:
        """获取基准测试状态"""
        return {
            'available_configurations': list(self.predefined_configurations.keys()),
            'history_count': len(self.benchmark_history),
            'baseline_count': len(self.baseline_results),
            'recent_results': [
                {
                    'name': result.configuration.name,
                    'timestamp': result.start_time.isoformat(),
                    'success_rate': result.success_count / max(1, result.iterations_completed)
                }
                for result in self.benchmark_history[-5:]
            ]
        }
    
    def export_benchmark_data(self, format_type: str = 'summary') -> Dict[str, Any]:
        """导出基准测试数据"""
        try:
            if format_type == 'detailed':
                return {
                    'configurations': {name: config.to_dict() for name, config in self.predefined_configurations.items()},
                    'benchmark_history': [result.to_dict() for result in self.benchmark_history],
                    'baseline_results': {name: result.to_dict() for name, result in self.baseline_results.items()},
                    'system_info': self.executor._collect_system_info()
                }
            else:
                return self.get_benchmark_status()
                
        except Exception as e:
            logger.error(f"导出基准测试数据失败: {e}")
            return {'error': str(e)}
    
    def reset_benchmark_data(self):
        """重置基准测试数据"""
        try:
            self.benchmark_history.clear()
            self.baseline_results.clear()
            logger.info("基准测试数据已重置")
        except Exception as e:
            logger.error(f"重置基准测试数据失败: {e}")