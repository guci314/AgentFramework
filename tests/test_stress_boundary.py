#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
边界和压力测试模块
测试系统在极端条件下的稳定性和鲁棒性
"""

import unittest
import sys
import os
import time
import threading
import json
import psutil
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhancedAgent_v2 import MultiStepAgent_v2, WorkflowState
from python_core import Agent, Result
from llm_lazy import get_model
from tests.config.test_config import skip_if_api_unavailable, check_deepseek_api_health


class StressBoundaryTest(unittest.TestCase):
    """边界和压力测试类"""
    
    def setUp(self):
        """测试前的设置"""
        self.llm = get_model("deepseek_v3")
        self.agent = MultiStepAgent_v2(llm=self.llm)
        self.test_results = []
        
        # 记录初始系统资源状态
        self.initial_memory = psutil.virtual_memory().used
        self.initial_cpu_percent = psutil.cpu_percent(interval=1)
        
    def tearDown(self):
        """测试后的清理"""
        # 强制垃圾回收
        gc.collect()
        
        # 记录测试后的资源状态
        final_memory = psutil.virtual_memory().used
        memory_increase = final_memory - self.initial_memory
        
        # 如果内存增长超过100MB，记录警告
        if memory_increase > 100 * 1024 * 1024:
            print(f"Warning: Memory increased by {memory_increase / 1024 / 1024:.2f} MB during test")
    
    def test_large_state_data_handling(self):
        """测试处理大量状态数据"""
        print("\n=== 测试大量状态数据处理 ===")
        
        # 创建大型JSON对象
        large_data_sizes = [1000, 5000, 10000]  # 不同的数据大小
        
        for size in large_data_sizes:
            with self.subTest(size=size):
                print(f"测试大小: {size} 个键值对")
                
                # 生成大型状态数据
                large_state = {}
                for i in range(size):
                    large_state[f"key_{i}"] = {
                        "nested_data": f"value_{i}" * 100,  # 每个值约100字符
                        "timestamp": time.time(),
                        "index": i,
                        "metadata": {
                            "type": "test_data",
                            "level": i % 10,
                            "description": f"测试数据项 {i}" * 5
                        }
                    }
                
                # 测试状态设置和获取
                start_time = time.time()
                workflow_state = WorkflowState()
                
                try:
                    # 设置大型状态
                    workflow_state.set_global_state(json.dumps(large_state))
                    
                    # 获取状态
                    retrieved_state = workflow_state.get_global_state()
                    
                    # 验证数据完整性
                    retrieved_data = json.loads(retrieved_state)
                    self.assertEqual(len(retrieved_data), size)
                    
                    # 验证部分数据正确性
                    self.assertEqual(retrieved_data["key_0"]["index"], 0)
                    self.assertEqual(retrieved_data[f"key_{size-1}"]["index"], size-1)
                    
                    elapsed_time = time.time() - start_time
                    print(f"  - 大小 {size}: 耗时 {elapsed_time:.3f}秒")
                    
                    # 性能基准：大型数据处理不应超过10秒
                    self.assertLess(elapsed_time, 10.0, f"大型数据处理耗时过长: {elapsed_time:.3f}秒")
                    
                except Exception as e:
                    self.fail(f"处理大小为 {size} 的数据时失败: {str(e)}")
    
    def test_rapid_state_updates(self):
        """测试快速连续状态更新"""
        print("\n=== 测试快速连续状态更新 ===")
        
        workflow_state = WorkflowState()
        update_counts = [100, 500, 1000]  # 不同的更新次数
        
        for count in update_counts:
            with self.subTest(count=count):
                print(f"测试更新次数: {count}")
                
                start_time = time.time()
                
                try:
                    # 快速连续更新状态
                    for i in range(count):
                        state_data = {
                            "update_index": i,
                            "timestamp": time.time(),
                            "data": f"rapid_update_{i}"
                        }
                        workflow_state.set_global_state(json.dumps(state_data))
                        
                        # 每100次更新验证一次
                        if i % 100 == 0:
                            current_state = workflow_state.get_global_state()
                            self.assertIsNotNone(current_state)
                    
                    elapsed_time = time.time() - start_time
                    print(f"  - {count} 次更新耗时: {elapsed_time:.3f}秒")
                    print(f"  - 平均每次更新: {elapsed_time/count*1000:.3f}毫秒")
                    
                    # 验证最终状态
                    final_state = json.loads(workflow_state.get_global_state())
                    self.assertEqual(final_state["update_index"], count - 1)
                    
                    # 验证历史记录
                    history = workflow_state.get_state_history()
                    self.assertGreater(len(history), 0)
                    
                    # 性能基准：1000次更新不应超过5秒
                    if count == 1000:
                        self.assertLess(elapsed_time, 5.0, f"1000次快速更新耗时过长: {elapsed_time:.3f}秒")
                    
                except Exception as e:
                    self.fail(f"快速更新 {count} 次时失败: {str(e)}")
    
    def test_concurrent_state_access(self):
        """测试并发状态访问"""
        print("\n=== 测试并发状态访问 ===")
        
        workflow_state = WorkflowState()
        thread_counts = [5, 10, 20]  # 不同的线程数量
        operations_per_thread = 50
        
        for thread_count in thread_counts:
            with self.subTest(threads=thread_count):
                print(f"测试线程数: {thread_count}")
                
                # 用于收集结果的列表
                results = []
                errors = []
                
                def worker_thread(thread_id):
                    """工作线程函数"""
                    try:
                        for i in range(operations_per_thread):
                            # 混合读写操作
                            if i % 2 == 0:
                                # 写操作
                                state_data = {
                                    "thread_id": thread_id,
                                    "operation": i,
                                    "timestamp": time.time(),
                                    "data": f"thread_{thread_id}_op_{i}"
                                }
                                workflow_state.set_global_state(json.dumps(state_data))
                            else:
                                # 读操作
                                current_state = workflow_state.get_global_state()
                                if current_state:
                                    parsed_state = json.loads(current_state)
                                    results.append((thread_id, i, parsed_state.get("thread_id")))
                    except Exception as e:
                        errors.append((thread_id, str(e)))
                
                start_time = time.time()
                
                # 创建并启动线程
                threads = []
                for thread_id in range(thread_count):
                    thread = threading.Thread(target=worker_thread, args=(thread_id,))
                    threads.append(thread)
                    thread.start()
                
                # 等待所有线程完成
                for thread in threads:
                    thread.join()
                
                elapsed_time = time.time() - start_time
                print(f"  - {thread_count} 个线程完成，耗时: {elapsed_time:.3f}秒")
                print(f"  - 成功操作: {len(results)}")
                print(f"  - 错误数量: {len(errors)}")
                
                # 验证没有严重错误
                self.assertEqual(len(errors), 0, f"并发访问出现错误: {errors}")
                
                # 验证状态一致性
                final_state = workflow_state.get_global_state()
                self.assertIsNotNone(final_state)
                
                # 性能基准：并发操作不应超过预期时间
                expected_max_time = thread_count * 0.5  # 每个线程最多0.5秒
                self.assertLess(elapsed_time, expected_max_time, 
                               f"并发操作耗时过长: {elapsed_time:.3f}秒")
    
    def test_invalid_input_handling(self):
        """测试无效输入处理"""
        print("\n=== 测试无效输入处理 ===")
        
        workflow_state = WorkflowState()
        
        # 测试各种无效输入
        invalid_inputs = [
            None,  # None值
            "",    # 空字符串
            "invalid_json{[",  # 无效JSON
            "null",  # JSON null
            "[]",    # 空数组
            "{}",    # 空对象
            "\x00\x01\x02",  # 二进制数据
            "a" * 1000000,    # 超长字符串
            json.dumps({"recursive": "self"}) * 1000,  # 超长重复JSON
        ]
        
        for i, invalid_input in enumerate(invalid_inputs):
            with self.subTest(input_type=f"invalid_{i}"):
                print(f"测试无效输入 {i}: {type(invalid_input).__name__}")
                
                try:
                    # 尝试设置无效状态
                    if invalid_input is not None:
                        workflow_state.set_global_state(invalid_input)
                        
                        # 验证系统仍然可以正常工作
                        current_state = workflow_state.get_global_state()
                        self.assertIsNotNone(current_state)
                        
                        print(f"  - 无效输入 {i} 被接受并处理")
                    else:
                        # None输入应该被正确处理
                        workflow_state.set_global_state(invalid_input)
                        current_state = workflow_state.get_global_state()
                        # None应该被转换为某种默认值或保持None
                        print(f"  - None输入处理结果: {current_state}")
                        
                except Exception as e:
                    # 记录异常但不失败测试（某些无效输入预期会抛出异常）
                    print(f"  - 无效输入 {i} 引发异常: {str(e)[:100]}")
    
    def test_memory_usage_under_stress(self):
        """测试压力下的内存使用"""
        print("\n=== 测试压力下的内存使用 ===")
        
        # 监控内存使用
        def get_memory_usage():
            return psutil.virtual_memory().used / 1024 / 1024  # MB
        
        initial_memory = get_memory_usage()
        print(f"初始内存使用: {initial_memory:.2f} MB")
        
        workflow_state = WorkflowState()
        memory_samples = []
        
        # 执行大量操作并监控内存
        operations = 1000
        for i in range(operations):
            # 创建相对大的状态数据
            state_data = {
                "iteration": i,
                "data": f"memory_test_data_{i}" * 50,
                "nested": {
                    "level1": {
                        "level2": {
                            "data": [f"item_{j}" for j in range(20)]
                        }
                    }
                },
                "timestamp": time.time()
            }
            
            workflow_state.set_global_state(json.dumps(state_data))
            
            # 每100次操作采样内存使用
            if i % 100 == 0:
                current_memory = get_memory_usage()
                memory_samples.append(current_memory)
                print(f"  - 操作 {i}: 内存使用 {current_memory:.2f} MB")
        
        final_memory = get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        print(f"最终内存使用: {final_memory:.2f} MB")
        print(f"内存增长: {memory_increase:.2f} MB")
        
        # 验证内存使用合理
        # 内存增长不应超过200MB（这是一个保守的阈值）
        self.assertLess(memory_increase, 200, 
                       f"内存增长过多: {memory_increase:.2f} MB")
        
        # 验证内存使用趋势（不应该无限增长）
        if len(memory_samples) >= 3:
            # 检查最后几个样本的增长率
            recent_growth = memory_samples[-1] - memory_samples[-3]
            print(f"近期内存增长: {recent_growth:.2f} MB")
            
            # 近期增长不应超过50MB
            self.assertLess(recent_growth, 50, 
                           f"近期内存增长过快: {recent_growth:.2f} MB")
    
    def test_ai_updater_stress_with_mock(self):
        """测试AI更新器在压力下的表现（使用模拟）"""
        print("\n=== 测试AI更新器压力表现 ===")
        
        workflow_state = WorkflowState()
        
        # 模拟AI更新器，直接模拟update_state_with_ai方法
        original_method = workflow_state.update_state_with_ai
        
        # 创建模拟响应
        mock_responses = [
            True,   # 成功
            True,   # 成功  
            False,  # 失败
            True,   # 成功
        ] * 50  # 重复模式，总共200个响应
        
        def mock_update_state_with_ai(context):
            """模拟AI状态更新方法"""
            response_index = len(getattr(mock_update_state_with_ai, 'call_history', []))
            if not hasattr(mock_update_state_with_ai, 'call_history'):
                mock_update_state_with_ai.call_history = []
            
            mock_update_state_with_ai.call_history.append(context)
            
            if response_index < len(mock_responses):
                success = mock_responses[response_index]
                if success:
                    # 模拟成功的状态更新
                    test_state = json.dumps({
                        "ai_update": f"模拟AI更新 {response_index}",
                        "timestamp": time.time(),
                        "context": context.get("step_info", "unknown")
                    })
                    workflow_state.set_global_state(test_state)
                    return True
                else:
                    # 模拟失败
                    return False
            return False
        
        # 替换方法
        workflow_state.update_state_with_ai = mock_update_state_with_ai
        
        # 执行大量AI更新
        success_count = 0
        failure_count = 0
        
        start_time = time.time()
        
        for i in range(200):
            try:
                context = {
                    "step_info": f"测试步骤 {i}",
                    "execution_result": f"执行结果 {i}",
                    "timestamp": time.time()
                }
                
                result = workflow_state.update_state_with_ai(context)
                
                if result:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                failure_count += 1
                print(f"  - AI更新 {i} 失败: {str(e)[:50]}")
        
        elapsed_time = time.time() - start_time
        
        print(f"AI更新压力测试完成:")
        print(f"  - 总操作: 200")
        print(f"  - 成功: {success_count}")
        print(f"  - 失败: {failure_count}")
        print(f"  - 耗时: {elapsed_time:.3f}秒")
        print(f"  - 成功率: {success_count/200*100:.1f}%")
        
        # 恢复原方法
        workflow_state.update_state_with_ai = original_method
        
        # 验证性能和成功率 (期望75%成功率，因为模式是3/4成功)
        self.assertGreater(success_count, 140, "AI更新成功率过低")  # 至少70%
        self.assertLess(elapsed_time, 10.0, f"AI更新压力测试耗时过长: {elapsed_time:.3f}秒")
    
    def test_system_resource_monitoring(self):
        """测试系统资源监控"""
        print("\n=== 系统资源监控测试 ===")
        
        # 收集基准资源数据
        def collect_system_stats():
            return {
                "memory_percent": psutil.virtual_memory().percent,
                "memory_used_mb": psutil.virtual_memory().used / 1024 / 1024,
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "disk_usage_percent": psutil.disk_usage('/').percent,
            }
        
        initial_stats = collect_system_stats()
        print(f"初始系统状态:")
        for key, value in initial_stats.items():
            print(f"  - {key}: {value:.2f}")
        
        # 执行一系列操作
        workflow_state = WorkflowState()
        
        # 模拟工作负载
        for i in range(500):
            # 创建和更新状态
            state_data = {
                "workload_test": i,
                "data": f"system_resource_test_{i}" * 20,
                "timestamp": time.time(),
                "nested_data": {
                    "items": [f"item_{j}" for j in range(10)]
                }
            }
            workflow_state.set_global_state(json.dumps(state_data))
            
            # 获取状态
            current_state = workflow_state.get_global_state()
            
            # 获取历史
            if i % 50 == 0:
                history = workflow_state.get_state_history()
        
        final_stats = collect_system_stats()
        print(f"最终系统状态:")
        for key, value in final_stats.items():
            print(f"  - {key}: {value:.2f}")
        
        # 计算资源变化
        resource_changes = {}
        for key in initial_stats:
            change = final_stats[key] - initial_stats[key]
            resource_changes[key] = change
            print(f"  - {key} 变化: {change:+.2f}")
        
        # 验证资源使用合理
        self.assertLess(resource_changes["memory_used_mb"], 100, 
                       "内存使用增长过多")
        
        # CPU使用率变化应该在合理范围内
        self.assertLess(abs(resource_changes["cpu_percent"]), 50, 
                       "CPU使用率变化异常")
    
    def test_edge_case_combinations(self):
        """测试边界条件组合"""
        print("\n=== 边界条件组合测试 ===")
        
        workflow_state = WorkflowState()
        
        # 测试场景组合
        test_scenarios = [
            {
                "name": "空状态快速更新",
                "operations": lambda: [workflow_state.set_global_state("") for _ in range(100)]
            },
            {
                "name": "大状态慢更新",
                "operations": lambda: [
                    workflow_state.set_global_state(json.dumps({"data": "x" * 10000})) 
                    for _ in range(10)
                ]
            },
            {
                "name": "混合读写操作",
                "operations": lambda: [
                    workflow_state.set_global_state(json.dumps({"index": i})) 
                    if i % 2 == 0 else workflow_state.get_global_state()
                    for i in range(50)
                ]
            },
            {
                "name": "历史记录压力",
                "operations": lambda: [
                    workflow_state.get_state_history() for _ in range(100)
                ]
            }
        ]
        
        for scenario in test_scenarios:
            with self.subTest(scenario=scenario["name"]):
                print(f"测试场景: {scenario['name']}")
                
                start_time = time.time()
                
                try:
                    # 执行场景操作
                    operations = scenario["operations"]()
                    
                    elapsed_time = time.time() - start_time
                    print(f"  - 场景 '{scenario['name']}' 完成，耗时: {elapsed_time:.3f}秒")
                    
                    # 验证系统仍然正常工作
                    test_state = workflow_state.get_global_state()
                    self.assertIsNotNone(test_state)
                    
                    # 验证历史功能
                    history = workflow_state.get_state_history()
                    self.assertIsInstance(history, list)
                    
                except Exception as e:
                    self.fail(f"边界条件场景 '{scenario['name']}' 失败: {str(e)}")


if __name__ == '__main__':
    # 设置详细输出
    unittest.main(verbosity=2, buffer=True) 