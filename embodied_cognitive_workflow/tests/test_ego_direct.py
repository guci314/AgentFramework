"""
直接测试Ego的决策，确认修复效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ego_agent import EgoAgent
from llm_lazy import get_model


def main():
    """直接测试Ego决策"""
    
    # 设置代理
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"
    
    # 获取语言模型
    llm = get_model('gemini_2_5_flash')
    
    # 创建Ego Agent
    ego = EgoAgent(llm)
    
    print("=== 直接测试Ego决策 ===\n")
    
    # 测试场景1：单Agent
    print("场景1：单Agent情况")
    state_analysis = "需要创建一个文件"
    available_agents = [
        {"name": "默认执行器", "capabilities": "通用任务执行，包括文件操作"}
    ]
    
    print(f"状态分析: {state_analysis}")
    print(f"可用Agent: {available_agents[0]['name']}")
    
    decision, instruction, agent_name = ego.decide_next_action(state_analysis, available_agents)
    
    print(f"\n决策结果:")
    print(f"- 决策: {decision}")
    print(f"- 选择的执行者: {agent_name}")
    
    if agent_name == "默认执行器":
        print("✅ 正确：选择了默认执行器")
    elif "自我智能体" in str(agent_name):
        print("❌ 错误：选择了自我智能体")
    else:
        print(f"⚠️ 选择了: {agent_name}")
    
    print("\n" + "-"*60 + "\n")
    
    # 测试场景2：多Agent
    print("场景2：多Agent情况")
    state_analysis = "需要进行数学计算"
    available_agents = [
        {"name": "数学专家", "capabilities": "数学计算和分析"},
        {"name": "文件管理器", "capabilities": "文件操作"}
    ]
    
    print(f"状态分析: {state_analysis}")
    print("可用Agents:")
    for agent in available_agents:
        print(f"- {agent['name']}: {agent['capabilities']}")
    
    decision, instruction, agent_name = ego.decide_next_action(state_analysis, available_agents)
    
    print(f"\n决策结果:")
    print(f"- 决策: {decision}")
    print(f"- 选择的执行者: {agent_name}")
    
    valid_names = [agent['name'] for agent in available_agents]
    if agent_name in valid_names:
        print(f"✅ 正确：选择了有效的Agent")
    elif "自我智能体" in str(agent_name):
        print("❌ 错误：选择了自我智能体")
    else:
        print(f"⚠️ 选择了未知的Agent: {agent_name}")


if __name__ == "__main__":
    main()