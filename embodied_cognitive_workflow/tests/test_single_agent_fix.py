"""
测试单Agent情况下的执行者选择
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embodied_cognitive_workflow import CognitiveAgent
from cognitive_debugger import CognitiveDebugger, StepType
from llm_lazy import get_model


def main():
    """测试单Agent情况下的执行者选择"""
    
    # 设置代理
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"
    
    # 获取语言模型
    llm = get_model('gemini_2_5_flash')
    
    # 创建认知智能体（使用默认Agent）
    cognitive_agent = CognitiveAgent(
        llm=llm,
        max_cycles=3,
        verbose=False,
        enable_meta_cognition=False
    )
    
    print("=== 测试单Agent执行者选择 ===\n")
    print(f"默认Agent名称: {cognitive_agent.agents[0].name}")
    print(f"默认Agent能力: {cognitive_agent.agents[0].api_specification}")
    
    # 创建调试器
    debugger = CognitiveDebugger(cognitive_agent)
    
    # 使用一个会进入认知循环的任务
    task = "创建一个包含100个随机数的列表，然后计算平均值"
    
    print(f"\n任务：{task}")
    print("-" * 60)
    
    # 启动调试
    debugger.start_debug(task)
    
    # 设置断点在决策步骤
    debugger.set_breakpoint(StepType.DECISION_MAKING, description="查看Agent选择")
    
    print("\n开始执行...\n")
    
    # 执行到第一个断点
    results = debugger.run_until_breakpoint()
    
    # 检查决策信息
    if results:
        last_step = results[-1]
        if last_step.step_type == StepType.DECISION_MAKING and last_step.debug_info:
            print("🔍 决策信息：")
            if "selected_agent" in last_step.debug_info:
                selected = last_step.debug_info['selected_agent']
                print(f"   选择的执行者: {selected}")
                
                if selected == "自我智能体" or "自我智能体" in selected:
                    print("   ❌ 错误：选择了'自我智能体'")
                elif selected == "默认执行器":
                    print("   ✅ 正确：选择了'默认执行器'")
                else:
                    print(f"   ⚠️ 选择了其他执行者: {selected}")
            
            if "available_agents" in last_step.debug_info:
                print(f"   可用Agents: {last_step.debug_info['available_agents']}")
    
    # 完成执行
    debugger.run_to_completion()
    
    print("\n测试完成。")


if __name__ == "__main__":
    main()