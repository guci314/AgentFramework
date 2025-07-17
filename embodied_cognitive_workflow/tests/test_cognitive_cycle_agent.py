"""
测试认知循环中的Agent选择
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embodied_cognitive_workflow import CognitiveAgent
from llm_lazy import get_model


def main():
    """测试认知循环中的Agent选择"""
    
    # 设置代理
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"
    
    # 获取语言模型
    llm = get_model('gemini_2_5_flash')
    
    print("=== 测试1：默认Agent（单Agent模式）===")
    
    # 创建认知智能体（不传入agents，使用默认Agent）
    cognitive_agent = CognitiveAgent(
        llm=llm,
        max_cycles=2,  # 限制循环次数
        verbose=True,
        enable_meta_cognition=False
    )
    
    print(f"Agent名称: {cognitive_agent.agents[0].name}")
    print(f"Agent能力: {cognitive_agent.agents[0].api_specification}")
    
    # 使用一个会进入认知循环的任务
    task = "创建一个文件test.txt，写入内容'Hello World'，然后读取并验证内容"
    
    print(f"\n任务：{task}")
    print("-" * 60)
    
    result = cognitive_agent.execute_sync(task)
    
    # 分析执行历史
    print("\n分析执行历史:")
    for history in cognitive_agent.execution_history:
        if "自我决策" in history:
            print(f"- {history}")
            if "自我智能体" in history:
                print("  ❌ 发现'自我智能体'")
            elif "默认执行器" in history:
                print("  ✅ 正确使用'默认执行器'")
    
    # 清理测试文件
    if os.path.exists("test.txt"):
        os.remove("test.txt")
        print("\n已清理测试文件")
    
    print("\n" + "="*60)
    print("=== 测试2：多Agent模式 ===")
    
    from python_core import Agent
    
    # 创建两个专门的Agent
    file_agent = Agent(llm=llm)
    file_agent.name = "文件管理器"
    file_agent.api_specification = "文件操作专家"
    
    verify_agent = Agent(llm=llm)
    verify_agent.name = "验证专家"
    verify_agent.api_specification = "数据验证和检查"
    
    cognitive_agent2 = CognitiveAgent(
        llm=llm,
        agents=[file_agent, verify_agent],
        max_cycles=2,
        verbose=True,
        enable_meta_cognition=False
    )
    
    print(f"\n可用Agents:")
    for agent in cognitive_agent2.agents:
        print(f"- {agent.name}: {agent.api_specification}")
    
    result2 = cognitive_agent2.execute_sync(task)
    
    # 分析执行历史
    print("\n分析执行历史:")
    for history in cognitive_agent2.execution_history:
        if "自我决策" in history:
            print(f"- {history}")
            if "自我智能体" in history:
                print("  ❌ 发现'自我智能体'")
            elif "文件管理器" in history or "验证专家" in history:
                print("  ✅ 正确选择了专业Agent")
    
    # 清理测试文件
    if os.path.exists("test.txt"):
        os.remove("test.txt")
        print("\n已清理测试文件")


if __name__ == "__main__":
    main()