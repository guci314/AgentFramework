"""
简单测试Ego Agent选择逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ego_agent import EgoAgent
from llm_lazy import get_model
import json


def main():
    """简单测试Ego Agent选择"""
    
    # 设置代理
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"
    
    # 获取语言模型
    llm = get_model('gemini_2_5_flash')
    
    # 创建Ego Agent
    ego = EgoAgent(llm)
    
    print("=== Ego Agent选择测试 ===\n")
    
    # 简单的状态分析
    state_analysis = "当前需要计算数学问题"
    
    # 可用Agent列表
    available_agents = [
        {"name": "计算器", "capabilities": "数学计算"},
        {"name": "文件助手", "capabilities": "文件操作"}
    ]
    
    print("可用Agent:")
    for agent in available_agents:
        print(f"- {agent['name']}: {agent['capabilities']}")
    
    # 测试决策
    try:
        decision, instruction, agent_name = ego.decide_next_action(state_analysis, available_agents)
        
        print(f"\n决策结果: {decision}")
        if agent_name:
            print(f"选择的执行者: {agent_name}")
            
            # 验证选择
            valid_names = [agent['name'] for agent in available_agents]
            if agent_name in valid_names:
                print("✅ 选择了有效的Agent")
            elif agent_name == "自我智能体":
                print("❌ 错误：选择了'自我智能体'")
            else:
                print(f"❌ 错误：选择了无效的Agent '{agent_name}'")
        
    except Exception as e:
        print(f"出现错误: {str(e)}")
        print("这可能是因为响应太长。让我们测试一个更直接的场景...")
        
        # 直接测试JSON解析逻辑
        print("\n直接测试Agent验证逻辑:")
        
        # 模拟错误的响应
        test_responses = [
            {"决策": "执行指令", "执行者": "自我智能体"},
            {"决策": "执行指令", "执行者": "计算器"},
            {"决策": "执行指令", "执行者": "不存在的Agent"}
        ]
        
        for resp in test_responses:
            print(f"\n测试响应: {resp}")
            
            # 模拟验证逻辑
            decision = resp.get("决策", "").strip()
            agent_name = resp.get("执行者", "")
            
            if decision == "执行指令" and available_agents:
                valid_agent_names = [agent['name'] for agent in available_agents]
                if agent_name not in valid_agent_names:
                    print(f"  警告：选择了无效的执行者 '{agent_name}'")
                    agent_name = valid_agent_names[0] if valid_agent_names else None
                    print(f"  使用默认Agent: {agent_name}")
                else:
                    print(f"  ✅ 选择了有效的Agent: {agent_name}")


if __name__ == "__main__":
    main()