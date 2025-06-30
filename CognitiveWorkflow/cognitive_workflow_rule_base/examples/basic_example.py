# -*- coding: utf-8 -*-
"""
基础使用示例 - V2 (递归架构)

展示如何使用统一的、可递归的CognitiveAgent来构建层次化团队并执行任务。
"""

import sys
import os
from pathlib import Path
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加父目录到路径，以便导入模块
sys.path.append(str(Path(__file__).parent.parent.parent))

from pythonTask import Agent, llm_deepseek,llm_gemini_2_5_flash_google,llm_gemini_2_5_pro_google
from cognitive_workflow_rule_base.cognitive_workflow_agent_wrapper import CognitiveAgent

# 尝试导入WorkflowExecutionResult，如果失败则定义一个虚拟类
try:
    from cognitive_workflow_rule_base.domain.value_objects import WorkflowExecutionResult
except ImportError:
    logger.warning("无法导入 WorkflowExecutionResult，将使用虚拟类。")
    class WorkflowExecutionResult:
        pass

# 使用的LLM
selected_llm = llm_deepseek

def demonstrate_recursive_team_execution():
    """演示基于递归团队的执行过程"""
    
    print("\n🧠 递归认知团队执行演示")
    print("="*50)
    
    # 1. 创建基础Agent (作
    print("1. 创建基础Agent...")
    base_coder_agent = Agent(llm=selected_llm)
    base_coder_agent.loadKnowledge('unittest的测试结果在标准错误流而不是标准输出流')
    
    base_tester_agent = Agent(llm=selected_llm)
    base_tester_agent.loadKnowledge('unittest的测试结果在标准错误流而不是标准输出流')

    manager_base_agent = Agent(llm=selected_llm) # 管理者也需要一个基础Agent来使用LLM

    # 2. 创建叶节点CognitiveAgent (执行者)
    print("\n2. 创建叶节点Agent (执行者)...")
    coder = CognitiveAgent(
        base_agent=base_coder_agent,
        agent_name="coder"
    )
    tester = CognitiveAgent(
        base_agent=base_tester_agent,
        agent_name="tester"
    )
    print(f"   - {coder}")
    print(f"   - {tester}")

    # 3. 创建管理者CognitiveAgent
    print("\n3. 创建管理者Agent...")
    project_manager = CognitiveAgent(
        base_agent=manager_base_agent,
        agent_name="project_manager",
        team_members={
            "coder": coder,
            "tester": tester
        }
    )
    print(f"   - {project_manager}")
    print(f"   - 管理团队: {list(project_manager.team.keys())}")

    # 4. 定义一个需要委托的复杂目标
    # 注意：为了让简化的_decide_delegation生效，指令中需要包含团队成员的名字
    # 我们将任务分解为两个子目标，模拟管理者逐一发出指令
    print("\n4. 定义团队目标...")
    goals = [
        "coder, please create a calculator program in `calculator.py` that can perform addition, subtraction, multiplication, and division.",
        "tester, please create unit tests for `calculator.py` in `test_calculator.py` and run them to ensure everything works correctly."
    ]

    print(f"   - 目标 1: {goals[0]}")
    print(f"   - 目标 2: {goals[1]}")

    # 5. 通过顶层管理者执行目标
    print("\n5. 开始执行工作流...")
    try:
        for i, g in enumerate(goals):
            print(f"\n--- 执行第 {i+1} 个子目标 ---")
            # 调用顶层Agent的execute方法
            result = project_manager.execute(g)
            
            print(f"\n--- 子目标 {i+1} 执行结果 ---")
            if isinstance(result, WorkflowExecutionResult):
                print(f"   成功: {'是' if result.is_successful else '否'}")
                print(f"   最终消息: {result.final_message}")
            else:
                # 可能是来自 single_step 或 informational 查询的直接结果
                print(f"   结果: {result}")

    except Exception as e:
        print(f"   执行失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    
    print("🚀 统一递归认知工作流系统演示")
    print("="*60)
    
    try:
        demonstrate_recursive_team_execution()
        
        print("\n🎉 演示完成!")
        print("\n核心特性展示:")
        print("✓ 统一的、可递归的CognitiveAgent")
        print("✓ 通过组合构建层次化团队")
        print("✓ 任务的递归委托与执行")
        
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
    except Exception as e:
        print(f"\n\n演示执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()