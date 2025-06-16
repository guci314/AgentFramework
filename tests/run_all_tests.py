#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行所有pythonTask.py相关的单元测试
"""

import unittest
import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入所有测试模块
import test_device
import test_stateful_executor
import test_thinker
import test_evaluator
import test_agent

# 导入测试类
from test_device import *
from test_stateful_executor import *
from test_thinker import *
from test_evaluator import *
from test_agent import *


def print_banner(title):
    """打印测试标题横幅"""
    print("\n" + "="*70)
    print(f"🚀 {title}")
    print("="*70)


def print_summary(title, result):
    """打印测试结果摘要"""
    print(f"\n📊 {title} 测试总结:")
    print(f"   - 运行测试: {result.testsRun}")
    print(f"   - 成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   - 失败: {len(result.failures)}")
    print(f"   - 错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print(f"   - 状态: ✅ 全部通过")
    else:
        print(f"   - 状态: ❌ 有失败或错误")
    
    return result.wasSuccessful()


def run_test_suite(test_name, test_classes):
    """运行指定的测试套件"""
    print_banner(f"{test_name} 测试")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=1, buffer=True, stream=sys.stdout)
    result = runner.run(suite)
    
    return print_summary(test_name, result)


def main():
    """主函数"""
    start_time = time.time()
    
    print_banner("AgentFrameWork pythonTask.py 组件单元测试")
    
    # 检查API密钥
    has_deepseek = bool(os.getenv('DEEPSEEK_API_KEY'))
    
    if has_deepseek:
        print("📡 检测到DEEPSEEK_API_KEY，将运行完整测试（包括真实API调用）")
    else:
        print("⚠️  未检测到DEEPSEEK_API_KEY，将跳过需要API的测试")
    
    # 测试结果统计
    total_results = []
    
    # 1. Device 测试
    device_success = run_test_suite("Device类", [
        TestDeviceBasic,
        TestDeviceEdgeCases,
        TestDeviceResultValidation
    ])
    total_results.append(("Device", device_success))
    
    # 2. StatefulExecutor 测试
    executor_success = run_test_suite("StatefulExecutor类", [
        TestStatefulExecutorBasic,
        TestStatefulExecutorComplexTypes,
        TestStatefulExecutorErrorHandling,
        TestStatefulExecutorReturnValue
    ])
    total_results.append(("StatefulExecutor", executor_success))
    
    # 3. Thinker 测试
    thinker_classes = [TestThinkerBasic]
    if has_deepseek:
        thinker_classes.extend([
            TestThinkerWithDeepSeek,
            TestThinkerStreamExecution,
            TestThinkerChatFunctionality,
            TestThinkerResultGeneration,
            TestThinkerComplexTasks
        ])
    
    thinker_success = run_test_suite("Thinker类", thinker_classes)
    total_results.append(("Thinker", thinker_success))
    
    # 4. Evaluator 测试
    evaluator_classes = [TestEvaluatorBasic]
    if has_deepseek:
        evaluator_classes.extend([
            TestEvaluatorWithDeepSeek,
            TestEvaluatorCustomCriteria,
            TestEvaluatorWithKnowledge,
            TestEvaluatorErrorHandling
        ])
    
    evaluator_success = run_test_suite("Evaluator类", evaluator_classes)
    total_results.append(("Evaluator", evaluator_success))
    
    # 5. Agent 测试
    agent_classes = [TestAgentBasic]
    if has_deepseek:
        agent_classes.extend([
            TestAgentExecution,
            TestAgentStreamExecution,
            TestAgentChatFunctionality,
            TestAgentEvaluationSystem,
            TestAgentKnowledgeManagement,
            TestAgentConfigurationOptions,
            TestAgentComplexScenarios
        ])
    
    agent_success = run_test_suite("Agent类", agent_classes)
    total_results.append(("Agent", agent_success))
    
    # 总体结果汇总
    end_time = time.time()
    duration = end_time - start_time
    
    print_banner("测试总结")
    
    print(f"⏱️  总耗时: {duration:.2f} 秒")
    print(f"🔧 测试环境: {'包含API调用' if has_deepseek else '仅本地测试'}")
    
    print("\n📋 各组件测试结果:")
    all_passed = True
    for component, success in total_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   - {component:15} : {status}")
        if not success:
            all_passed = False
    
    print(f"\n🏆 总体结果: {'🎉 全部测试通过！' if all_passed else '❌ 存在测试失败'}")
    
    if not has_deepseek:
        print("\n💡 提示: 设置 DEEPSEEK_API_KEY 环境变量可运行完整的API集成测试")
    
    # 如果有失败，设置退出码
    if not all_passed:
        sys.exit(1)


if __name__ == '__main__':
    main()