"""
测试复杂任务的默认Agent选择

使用复杂任务强制进入认知循环，测试Agent选择。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embodied_cognitive_workflow import CognitiveAgent
from llm_lazy import get_model


def main():
    """测试复杂任务的默认Agent选择"""
    
    # 设置代理
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"
    
    # 获取语言模型
    llm = get_model('gemini_2_5_flash')
    
    # 创建认知智能体（不传入agents，使用默认Agent）
    cognitive_agent = CognitiveAgent(
        llm=llm,
        max_cycles=5,
        verbose=True,
        enable_meta_cognition=False,
        evaluation_mode="internal"
    )
    
    print("=== 测试复杂任务的默认Agent选择 ===\n")
    print(f"默认Agent名称: {cognitive_agent.agents[0].name}")
    print(f"默认Agent能力: {cognitive_agent.agents[0].api_specification}")
    print()
    
    # 复杂任务，确保进入认知循环
    task = """
    创建一个Python计算器类，实现以下功能：
    1. 基本四则运算（加、减、乘、除）
    2. 添加除零错误处理
    3. 编写单元测试验证功能
    4. 确保所有测试通过
    """
    
    print(f"复杂任务：{task}")
    print("-" * 60)
    
    result = cognitive_agent.execute_sync(task)
    
    if result.success:
        print(f"\n✅ 任务执行成功")
    else:
        print(f"\n❌ 任务执行失败: {result.stderr}")
    
    # 检查执行历史
    print("\n检查执行历史中的Agent选择：")
    print("=" * 60)
    
    found_self_agent = False
    found_default_agent = False
    agent_selections = []
    
    for i, history in enumerate(cognitive_agent.execution_history, 1):
        if "执行者：" in history or "选择了" in history:
            agent_selections.append(f"{i}. {history}")
            if "自我智能体" in history:
                found_self_agent = True
            if "默认执行器" in history:
                found_default_agent = True
        elif "决策：" in history and "执行指令" in history:
            agent_selections.append(f"{i}. {history}")
    
    # 显示所有Agent选择相关的日志
    for selection in agent_selections[-10:]:  # 显示最后10条
        print(selection)
    
    print("\n测试结果：")
    if found_self_agent:
        print("❌ 失败：发现了'自我智能体'的引用")
    elif found_default_agent:
        print("✅ 成功：正确使用了'默认执行器'")
    else:
        print("⚠️ 未找到明确的执行者选择日志")
        print("（可能任务被判断为简单任务，直接处理了）")


if __name__ == "__main__":
    main()