#!/usr/bin/env python3
"""
测试评估器使用情况
===============

检查 calculator_static_workflow.py 使用的是哪个评估器
"""

import os
from static_workflow.MultiStepAgent_v3 import MultiStepAgent_v3, RegisteredAgent
from static_workflow.result_evaluator import TestResultEvaluator, MockTestResultEvaluator
from pythonTask import Agent
from langchain_openai import ChatOpenAI

def test_evaluator_selection():
    """测试评估器选择逻辑"""
    
    print("🧪 测试评估器选择逻辑")
    print("=" * 50)
    
    # 创建简单的LLM（不用于评估器测试）
    simple_llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo", api_key="dummy")
    
    # 测试场景1：默认行为（尝试使用AI评估器，无API key时降级）
    print("\n📋 场景1: 默认行为（无环境变量）")
    # 临时清除环境变量
    original_key = os.environ.get('DEEPSEEK_API_KEY')
    if 'DEEPSEEK_API_KEY' in os.environ:
        del os.environ['DEEPSEEK_API_KEY']
    
    agent1 = MultiStepAgent_v3(
        llm=simple_llm,
        registered_agents=[]
    )
    print(f"   评估器类型: {type(agent1.result_evaluator).__name__}")
    print(f"   是否为Mock: {isinstance(agent1.result_evaluator, MockTestResultEvaluator)}")
    
    # 恢复环境变量
    if original_key:
        os.environ['DEEPSEEK_API_KEY'] = original_key
    
    # 测试场景2：有环境变量时的行为
    print("\n📋 场景2: 有环境变量时的行为")
    # 设置临时API key
    os.environ['DEEPSEEK_API_KEY'] = "test-api-key"
    agent2 = MultiStepAgent_v3(
        llm=simple_llm,
        registered_agents=[]
    )
    print(f"   评估器类型: {type(agent2.result_evaluator).__name__}")
    print(f"   是否为Mock: {isinstance(agent2.result_evaluator, MockTestResultEvaluator)}")
    
    # 测试场景3：强制使用 mock 评估器
    print("\n📋 场景3: 强制使用 mock 评估器")
    agent3 = MultiStepAgent_v3(
        llm=simple_llm,
        registered_agents=[],
        use_mock_evaluator=True
    )
    print(f"   评估器类型: {type(agent3.result_evaluator).__name__}")
    print(f"   是否为Mock: {isinstance(agent3.result_evaluator, MockTestResultEvaluator)}")
    
    # 恢复原始环境变量
    if original_key:
        os.environ['DEEPSEEK_API_KEY'] = original_key
    elif 'DEEPSEEK_API_KEY' in os.environ:
        del os.environ['DEEPSEEK_API_KEY']
    
    # 测试场景4：检查环境变量
    print("\n📋 场景4: 检查当前环境变量")
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    print(f"   DEEPSEEK_API_KEY 环境变量: {'已设置' if deepseek_key else '未设置'}")
    print(f"   环境变量值: {deepseek_key[:20] + '...' if deepseek_key and len(deepseek_key) > 20 else deepseek_key}")
    
    # 测试场景5：模拟 calculator_static_workflow.py 的调用方式
    print("\n📋 场景5: 模拟 calculator_static_workflow.py 的调用")
    try:
        # 这与 calculator_static_workflow.py 中的调用完全一致
        agent_v3 = MultiStepAgent_v3(
            llm=simple_llm,  # 使用简单LLM代替DeepSeek
            registered_agents=[],  # 简化为空列表
            max_retries=3,
            max_parallel_workers=2
            # 注意：没有显式传递 use_mock_evaluator 参数，将根据环境变量自动选择
        )
        print(f"   评估器类型: {type(agent_v3.result_evaluator).__name__}")
        print(f"   是否为Mock: {isinstance(agent_v3.result_evaluator, MockTestResultEvaluator)}")
        
        # 测试评估功能
        if isinstance(agent_v3.result_evaluator, MockTestResultEvaluator):
            print("   ✅ 使用Mock评估器，基于启发式规则评估")
            print("   📝 评估能力: 本地规则判断，不需要API key")
        else:
            print("   ✅ 使用DeepSeek评估器，基于AI模型评估")
            print("   📝 评估能力: 智能AI分析，需要API key")
            
    except Exception as e:
        print(f"   ❌ 创建失败: {e}")

def test_mock_evaluator_capability():
    """测试Mock评估器的能力"""
    
    print("\n" + "=" * 50)
    print("🔬 测试Mock评估器的评估能力")
    print("=" * 50)
    
    mock_evaluator = MockTestResultEvaluator()
    
    test_cases = [
        {
            "name": "unittest成功",
            "stderr": "Ran 5 tests in 0.002s\n\nOK",
            "expected": True
        },
        {
            "name": "unittest失败", 
            "stderr": "FAILED (failures=1)",
            "expected": False
        },
        {
            "name": "pytest成功",
            "stdout": "5 passed in 0.1s",
            "expected": True
        },
        {
            "name": "pytest失败",
            "stdout": "3 passed, 2 failed",
            "expected": False
        },
        {
            "name": "构建成功",
            "stdout": "Build completed successfully",
            "expected": True
        }
    ]
    
    for case in test_cases:
        result = mock_evaluator.evaluate_test_result(
            result_stdout=case.get("stdout", ""),
            result_stderr=case.get("stderr", ""),
            result_return_value=""
        )
        
        status = "✅" if result["passed"] == case["expected"] else "❌"
        print(f"   {status} {case['name']}: {result['passed']} (置信度: {result['confidence']:.2f})")
        print(f"      理由: {result['reason']}")

if __name__ == "__main__":
    test_evaluator_selection()
    test_mock_evaluator_capability()
    
    print("\n" + "=" * 50)
    print("📋 结论总结")
    print("=" * 50)
    print("1. 如果 use_mock_evaluator=True，强制使用 MockTestResultEvaluator")
    print("2. 如果 use_mock_evaluator=False（默认）且有DEEPSEEK_API_KEY环境变量，使用 TestResultEvaluator") 
    print("3. 如果 use_mock_evaluator=False（默认）且无DEEPSEEK_API_KEY环境变量，自动降级为 MockTestResultEvaluator")
    print("4. calculator_static_workflow.py 使用默认参数，将根据环境变量自动选择评估器")
    print("5. Mock 评估器基于启发式规则，能够处理常见的测试输出格式")
    print("\n🎯 对于大多数基本测试场景，Mock 评估器已经足够准确！")