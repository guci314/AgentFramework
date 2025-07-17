#!/usr/bin/env python3
"""
AI状态更新器缓存和条件逻辑测试
===================================

测试新增的缓存和条件逻辑功能：
1. LRU缓存系统测试
2. 上下文哈希生成测试
3. AI调用条件检查测试
4. 综合缓存和条件逻辑集成测试
5. 性能影响评估

这些测试验证优化功能的正确性和性能提升效果。
"""

import time
import logging
from datetime import datetime
from enhancedAgent_v2 import (
    WorkflowState, 
    AIStateUpdaterService, 
    LRUCache, 
    ContextHasher, 
    AICallConditionChecker,
    AICallCacheEntry
)
from unittest.mock import Mock, MagicMock

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockLLM:
    """Mock LLM用于测试"""
    def __init__(self):
        self.call_count = 0
        self.responses = ["测试状态更新：当前任务已完成，系统运行正常"]
        
    def invoke(self, messages):
        self.call_count += 1
        response = Mock()
        response.content = self.responses[0] if self.responses else "默认响应"
        logger.info(f"Mock LLM调用 #{self.call_count}")
        return response

def test_lru_cache():
    """测试LRU缓存功能"""
    print("🧪 测试LRU缓存功能...")
    
    cache = LRUCache(max_size=3)
    
    # 测试基本操作
    entry1 = AICallCacheEntry("响应1", datetime.now(), "hash1", 0.9, 1)
    entry2 = AICallCacheEntry("响应2", datetime.now(), "hash2", 0.8, 1)
    entry3 = AICallCacheEntry("响应3", datetime.now(), "hash3", 0.7, 1)
    entry4 = AICallCacheEntry("响应4", datetime.now(), "hash4", 0.6, 1)
    
    # 添加缓存项
    cache.put("key1", entry1)
    cache.put("key2", entry2)
    cache.put("key3", entry3)
    
    # 测试缓存命中
    cached = cache.get("key1")
    assert cached is not None, "缓存项应该存在"
    assert cached.response == "响应1", "缓存响应不匹配"
    assert cached.usage_count == 2, "使用次数应该增加"
    
    # 测试LRU淘汰
    cache.put("key4", entry4)  # 应该淘汰key2
    assert cache.get("key2") is None, "key2应该被淘汰"
    assert cache.get("key1") is not None, "key1应该还在（最近使用过）"
    
    # 测试统计信息
    stats = cache.get_stats()
    assert stats['cache_size'] == 3, "缓存大小不正确"
    assert stats['hits'] > 0, "应该有缓存命中"
    
    print("✅ LRU缓存测试通过")
    return True

def test_context_hasher():
    """测试上下文哈希生成"""
    print("🧪 测试上下文哈希生成...")
    
    # 创建测试状态
    state = WorkflowState()
    state.set_global_state("测试状态", source="test")
    
    # 测试上下文
    context1 = {
        'step_info': {'action': 'test_action', 'step_id': 'step1'},
        'execution_result': '执行成功',
        'step_status': 'completed'
    }
    
    context2 = {
        'step_info': {'action': 'test_action', 'step_id': 'step1'},
        'execution_result': '执行成功',
        'step_status': 'completed'
    }
    
    context3 = {
        'step_info': {'action': 'different_action', 'step_id': 'step1'},
        'execution_result': '执行成功',
        'step_status': 'completed'
    }
    
    # 测试相同上下文生成相同哈希
    hash1 = ContextHasher.hash_context(state, context1)
    hash2 = ContextHasher.hash_context(state, context2)
    assert hash1 == hash2, "相同上下文应该生成相同哈希"
    
    # 测试不同上下文生成不同哈希
    hash3 = ContextHasher.hash_context(state, context3)
    assert hash1 != hash3, "不同上下文应该生成不同哈希"
    
    # 测试包含时间戳的哈希
    hash4 = ContextHasher.hash_context(state, context1, include_timestamp=True)
    time.sleep(0.1)
    hash5 = ContextHasher.hash_context(state, context1, include_timestamp=True)
    assert hash4 != hash5, "包含时间戳的哈希应该不同"
    
    print("✅ 上下文哈希测试通过")
    return True

def test_condition_checker():
    """测试AI调用条件检查器"""
    print("🧪 测试AI调用条件检查器...")
    
    checker = AICallConditionChecker()
    state = WorkflowState()
    
    # 测试初始化场景
    context_init = {}
    should_call, reason = checker.should_make_ai_call(state, context_init)
    print(f"初始化测试 - should_call: {should_call}, reason: '{reason}'")
    assert should_call, "初始化时应该调用AI"
    assert "初始化" in reason or "工作流初始化" in reason, f"原因应该包含初始化，实际原因: '{reason}'"
    
    # 设置一些状态，确保有历史记录
    state.set_global_state("初始状态", source="test")
    state.set_global_state("测试状态", source="test")
    
    # 测试错误条件
    context_error = {
        'error_info': '测试错误',
        'step_status': 'failed'
    }
    should_call, reason = checker.should_make_ai_call(state, context_error)
    print(f"错误测试 - should_call: {should_call}, reason: '{reason}'")
    assert should_call, "有错误时应该调用AI"
    assert "错误" in reason or "AI分析" in reason, f"原因应该包含错误相关信息，实际原因: '{reason}'"
    
    # 测试状态转换
    context_transition = {
        'step_status': 'completed',
        'execution_result': '任务完成'
    }
    should_call, reason = checker.should_make_ai_call(state, context_transition)
    assert should_call, "状态转换时应该调用AI"
    
    # 测试不重要变化
    context_minor = {
        'step_status': 'running',
        'execution_result': 'ok'
    }
    should_call, reason = checker.should_make_ai_call(state, context_minor)
    # 可能调用也可能不调用，取决于具体逻辑
    
    # 测试配置更新
    original_config = checker.get_configuration()
    checker.set_significance_threshold(0.5)
    checker.set_time_threshold(600)
    
    new_config = checker.get_configuration()
    assert new_config['significance_threshold'] == 0.5, "阈值更新失败"
    assert new_config['time_threshold_seconds'] == 600, "时间阈值更新失败"
    
    print("✅ 条件检查器测试通过")
    return True

def test_ai_updater_integration():
    """测试AI状态更新器与缓存、条件逻辑的集成"""
    print("🧪 测试AI状态更新器集成...")
    
    # 创建Mock LLM
    mock_llm = MockLLM()
    
    # 创建启用缓存和条件逻辑的AI更新器
    updater = AIStateUpdaterService(
        llm=mock_llm,
        enable_caching=True,
        cache_size=5,
        enable_conditional_logic=True
    )
    
    # 创建测试状态
    state = WorkflowState()
    
    # 第一次调用 - 应该调用LLM（初始化）
    context1 = {
        'step_info': {'action': 'init', 'step_id': 'step1'},
        'execution_result': '初始化完成',
        'step_status': 'completed'
    }
    
    result1 = updater.update_state(state, context1)
    assert result1 is not None, "第一次更新应该成功"
    first_call_count = mock_llm.call_count
    
    # 相同上下文的第二次调用 - 应该使用缓存
    result2 = updater.update_state(state, context1)
    assert result2 == result1, "缓存结果应该相同"
    assert mock_llm.call_count == first_call_count, "应该使用缓存，不增加LLM调用"
    
    # 检查缓存统计
    cache_stats = updater.get_cache_statistics()
    assert cache_stats['enabled'], "缓存应该启用"
    assert cache_stats['hits'] >= 1, "应该有缓存命中"
    
    # 不同上下文的调用 - 应该调用LLM
    context2 = {
        'step_info': {'action': 'process', 'step_id': 'step2'},
        'execution_result': '处理完成',
        'step_status': 'completed'
    }
    
    result3 = updater.update_state(state, context2)
    assert result3 is not None, "新上下文更新应该成功"
    assert mock_llm.call_count > first_call_count, "新上下文应该调用LLM"
    
    # 测试条件逻辑配置
    condition_config = updater.get_condition_checker_config()
    assert condition_config['enabled'], "条件逻辑应该启用"
    
    # 测试性能统计
    perf_stats = updater.get_performance_statistics()
    assert 'caching' in perf_stats, "应该包含缓存统计"
    assert 'conditional_logic' in perf_stats, "应该包含条件逻辑统计"
    
    print("✅ AI状态更新器集成测试通过")
    return True

def test_performance_impact():
    """测试性能影响"""
    print("🧪 测试性能影响...")
    
    # 创建两个更新器：一个启用优化，一个不启用
    mock_llm1 = MockLLM()
    mock_llm2 = MockLLM()
    
    updater_optimized = AIStateUpdaterService(
        llm=mock_llm1,
        enable_caching=True,
        enable_conditional_logic=True
    )
    
    updater_basic = AIStateUpdaterService(
        llm=mock_llm2,
        enable_caching=False,
        enable_conditional_logic=False
    )
    
    # 准备测试数据
    state1 = WorkflowState()
    state2 = WorkflowState()
    
    contexts = [
        {'step_info': {'action': f'action_{i}', 'step_id': f'step_{i}'}, 
         'execution_result': f'结果_{i}', 'step_status': 'completed'}
        for i in range(10)
    ]
    
    # 添加一些重复的上下文来测试缓存效果
    contexts.extend(contexts[:5])
    
    # 测试优化版本
    start_time = time.time()
    for context in contexts:
        updater_optimized.update_state(state1, context)
    optimized_time = time.time() - start_time
    optimized_calls = mock_llm1.call_count
    
    # 测试基础版本
    start_time = time.time()
    for context in contexts:
        updater_basic.update_state(state2, context)
    basic_time = time.time() - start_time
    basic_calls = mock_llm2.call_count
    
    print(f"📊 性能对比:")
    print(f"   优化版本: {optimized_time:.3f}s, LLM调用: {optimized_calls}次")
    print(f"   基础版本: {basic_time:.3f}s, LLM调用: {basic_calls}次")
    print(f"   缓存节省的LLM调用: {basic_calls - optimized_calls}次")
    
    # 验证缓存确实减少了LLM调用
    assert optimized_calls < basic_calls, "优化版本应该减少LLM调用次数"
    
    # 获取缓存统计
    cache_stats = updater_optimized.get_cache_statistics()
    print(f"   缓存命中率: {cache_stats.get('hit_rate_percent', 0):.1f}%")
    
    print("✅ 性能影响测试通过")
    return True

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始缓存和条件逻辑功能测试...\n")
    
    tests = [
        test_lru_cache,
        test_context_hasher,
        test_condition_checker,
        test_ai_updater_integration,
        test_performance_impact
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()  # 空行分隔
        except Exception as e:
            print(f"❌ 测试失败: {test_func.__name__} - {e}")
            print()
    
    print(f"📋 测试总结: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有缓存和条件逻辑测试均通过！")
        print("\n✨ 优化功能验证成功：")
        print("   - LRU缓存系统正常工作")
        print("   - 上下文哈希生成正确")
        print("   - 条件逻辑检查有效")
        print("   - AI更新器集成完善")
        print("   - 性能优化效果明显")
    else:
        print("⚠️  部分测试失败，需要检查实现")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1) 