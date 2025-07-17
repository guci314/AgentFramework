"""
最终测试：验证Ego不再选择"自我智能体"
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embodied_cognitive_workflow import CognitiveAgent
from cognitive_debugger import CognitiveDebugger, StepType
from llm_lazy import get_model


def main():
    """最终测试修复效果"""
    
    # 设置代理
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"
    
    # 获取语言模型
    llm = get_model('gemini_2_5_flash')
    
    print("=== 最终测试：验证Ego选择修复 ===\n")
    
    # 创建认知智能体（使用默认Agent）
    cognitive_agent = CognitiveAgent(
        llm=llm,
        max_cycles=2,
        verbose=False,
        enable_meta_cognition=False
    )
    
    print("默认Agent配置：")
    print(f"- 名称: {cognitive_agent.agents[0].name}")
    print(f"- 能力: {cognitive_agent.agents[0].api_specification}")
    print()
    
    # 创建调试器
    debugger = CognitiveDebugger(cognitive_agent)
    
    # 使用会进入认知循环的任务
    task = "创建一个Python脚本文件hello.py，内容为print('Hello World')"
    
    print(f"测试任务：{task}")
    print("-" * 60)
    
    # 启动调试
    debugger.start_debug(task)
    
    # 设置断点在决策步骤
    debugger.set_breakpoint(StepType.DECISION_MAKING)
    
    # 执行到断点
    results = debugger.run_until_breakpoint()
    
    # 检查结果
    test_passed = True
    found_decision = False
    
    if results:
        for step in results:
            if step.step_type == StepType.DECISION_MAKING and step.debug_info:
                found_decision = True
                print("\n📍 决策步骤信息:")
                
                # 检查可用Agents
                if "available_agents" in step.debug_info:
                    agents = step.debug_info["available_agents"]
                    print(f"   可用Agents: {agents}")
                else:
                    print("   ⚠️ 未找到available_agents信息")
                
                # 检查选择的Agent
                if "selected_agent" in step.debug_info:
                    selected = step.debug_info["selected_agent"]
                    print(f"   选择的执行者: {selected}")
                    
                    # 验证选择
                    if "自我智能体" in selected:
                        print("   ❌ 错误：仍然选择了'自我智能体'")
                        test_passed = False
                    elif selected == "默认执行器":
                        print("   ✅ 正确：选择了'默认执行器'")
                    else:
                        print(f"   ⚠️ 选择了未知执行者: {selected}")
                        test_passed = False
                else:
                    print("   ⚠️ 未找到selected_agent信息")
    
    # 清理测试文件
    if os.path.exists("hello.py"):
        os.remove("hello.py")
    
    # 测试结果
    print("\n" + "="*60)
    print("测试结果：")
    if not found_decision:
        print("⚠️ 未找到决策步骤，任务可能被直接处理了")
    elif test_passed:
        print("✅ 测试通过！Ego正确选择了默认执行器")
        print("🎉 修复成功：不再选择'自我智能体'")
    else:
        print("❌ 测试失败：Ego仍然选择了错误的执行者")


if __name__ == "__main__":
    main()