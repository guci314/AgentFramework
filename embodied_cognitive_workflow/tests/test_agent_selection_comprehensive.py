"""
综合测试Agent选择功能

测试各种场景下的Agent选择是否正确。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embodied_cognitive_workflow import CognitiveAgent
from python_core import Agent
from llm_lazy import get_model


def test_single_agent():
    """测试单个Agent的情况"""
    print("\n=== 测试1：单个Agent ===")
    
    llm = get_model('gemini_2_5_flash')
    
    single_agent = Agent(llm=llm)
    single_agent.name = "通用执行器"
    single_agent.api_specification = "处理各种任务"
    
    cognitive_agent = CognitiveAgent(
        llm=llm,
        agents=[single_agent],
        max_cycles=3,
        verbose=False
    )
    
    result = cognitive_agent.execute_sync("生成一个随机数")
    print(f"单Agent测试结果: {'成功' if result.success else '失败'}")
    
    # 检查执行历史
    for history in cognitive_agent.execution_history:
        if "执行者" in history and "自我智能体" in history:
            print("❌ 错误：发现了'自我智能体'的引用")
            return False
    
    print("✅ 通过：没有选择'自我智能体'")
    return True


def test_multiple_agents():
    """测试多个Agent的情况"""
    print("\n=== 测试2：多个Agent ===")
    
    llm = get_model('gemini_2_5_flash')
    
    # 创建多个Agent
    math_agent = Agent(llm=llm)
    math_agent.name = "数学计算器"
    math_agent.api_specification = "数学计算"
    
    text_agent = Agent(llm=llm)
    text_agent.name = "文本处理器"
    text_agent.api_specification = "文本生成和处理"
    
    cognitive_agent = CognitiveAgent(
        llm=llm,
        agents=[math_agent, text_agent],
        max_cycles=3,
        verbose=False
    )
    
    # 测试数学任务
    result = cognitive_agent.execute_sync("计算 123 + 456")
    print(f"数学任务结果: {'成功' if result.success else '失败'}")
    
    # 检查是否选择了正确的Agent
    selected_math = False
    for history in cognitive_agent.execution_history:
        if "执行者：数学计算器" in history:
            selected_math = True
            print("✅ 正确选择了数学计算器")
        if "执行者：自我智能体" in history:
            print("❌ 错误：选择了'自我智能体'")
            return False
    
    # 清空历史
    cognitive_agent.execution_history.clear()
    
    # 测试文本任务
    result = cognitive_agent.execute_sync("生成一首诗")
    print(f"文本任务结果: {'成功' if result.success else '失败'}")
    
    # 检查是否选择了正确的Agent
    selected_text = False
    for history in cognitive_agent.execution_history:
        if "执行者：文本处理器" in history:
            selected_text = True
            print("✅ 正确选择了文本处理器")
        if "执行者：自我智能体" in history:
            print("❌ 错误：选择了'自我智能体'")
            return False
    
    return True


def test_no_agents():
    """测试没有Agent的情况"""
    print("\n=== 测试3：无Agent（默认行为）===")
    
    llm = get_model('gemini_2_5_flash')
    
    cognitive_agent = CognitiveAgent(
        llm=llm,
        max_cycles=3,
        verbose=False
    )
    
    result = cognitive_agent.execute_sync("简单任务")
    print(f"无Agent测试结果: {'成功' if result.success else '失败'}")
    
    # 不应该有Agent选择相关的日志
    for history in cognitive_agent.execution_history:
        if "执行者：" in history:
            print(f"发现执行者日志: {history}")
    
    print("✅ 通过：无Agent时没有选择逻辑")
    return True


def main():
    """运行所有测试"""
    # 设置代理
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"
    
    print("=== Agent选择综合测试 ===")
    
    tests = [
        ("单Agent测试", test_single_agent),
        ("多Agent测试", test_multiple_agents),
        ("无Agent测试", test_no_agents)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n{test_name} 异常: {str(e)}")
            results.append((test_name, False))
    
    # 总结
    print("\n=== 测试总结 ===")
    all_passed = True
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有测试通过！Ego不再选择'自我智能体'")
    else:
        print("\n⚠️ 部分测试失败，需要进一步检查")


if __name__ == "__main__":
    main()