"""
测试Agent选择修复

验证Ego不会选择"自我智能体"，而是从提供的Agent列表中选择。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embodied_cognitive_workflow import CognitiveAgent
from python_core import Agent
from llm_lazy import get_model


def main():
    """测试Agent选择修复"""
    
    # 设置代理
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"
    
    # 获取语言模型
    llm = get_model('gemini_2_5_flash')
    
    # 创建几个测试Agent
    test_agent = Agent(llm=llm)
    test_agent.name = "测试执行器"
    test_agent.api_specification = "执行测试任务、验证功能"
    
    calc_agent = Agent(llm=llm)
    calc_agent.name = "计算器"
    calc_agent.api_specification = "数学计算、统计分析"
    
    # 创建认知智能体
    cognitive_agent = CognitiveAgent(
        llm=llm,
        agents=[test_agent, calc_agent],
        max_cycles=3,
        verbose=True,
        enable_meta_cognition=False
    )
    
    print("=== 测试Agent选择修复 ===\n")
    print("可用的Agent：")
    for agent in [test_agent, calc_agent]:
        print(f"- {agent.name}: {agent.api_specification}")
    print()
    
    # 测试任务
    task = "执行Calculator类的单元测试，验证所有功能正常"
    
    print(f"测试任务：{task}")
    print("-" * 60)
    
    result = cognitive_agent.execute_sync(task)
    
    if result.success:
        print(f"\n✅ 任务执行成功")
        print(f"结果：{result.return_value}")
    else:
        print(f"\n❌ 任务执行失败")
        print(f"错误：{result.stderr}")
    
    # 检查执行历史，看是否正确选择了Agent
    print("\n执行历史中的Agent选择：")
    print("-" * 60)
    for i, history in enumerate(cognitive_agent.execution_history, 1):
        if "执行者" in history or "选择" in history or "Agent" in history:
            print(f"{i}. {history}")


if __name__ == "__main__":
    main()