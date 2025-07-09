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

# 添加项目根目录和CognitiveWorkflow目录到路径，以便导入模块
project_root = str(Path(__file__).parent.parent.parent.parent)
cognitive_workflow_dir = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)
sys.path.append(cognitive_workflow_dir)

from pythonTask import Agent, llm_deepseek
from cognitive_workflow_rule_base.application.cognitive_workflow_agent_wrapper import IntelligentAgentWrapper

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

    # 2. 创建叶节点IntelligentAgentWrapper (执行者)
    print("\n2. 创建叶节点Agent (执行者)...")
    coder = IntelligentAgentWrapper(
        base_agent=base_coder_agent,
        agent_name="coder"
        # enable_adaptive_replacement=True  # 默认启用自适应规则替换
    )
    tester = IntelligentAgentWrapper(
        base_agent=base_tester_agent,
        agent_name="tester"
    )
    print(f"   - {coder}")
    print(f"   - {tester}")

    # 3. 创建管理者IntelligentAgentWrapper
    print("\n3. 创建管理者Agent...")
    project_manager = IntelligentAgentWrapper(
        base_agent=manager_base_agent,
        agent_name="project_manager",
        team_members={
            "coder": coder,
            "tester": tester
        }
    )
    print(f"   - {project_manager}")
    print(f"   - 管理团队: {list(project_manager.team.keys())}")
    print(f"   - 统一Agent池: {list(project_manager.available_agents.keys())}")

    # 4. 定义一个综合的团队目标
    # 将开发和测试任务合并为一个完整的目标，让系统自主决定如何分工协作
    print("\n4. 定义团队目标...")
    goal = """Please develop a complete calculator program with the following requirements:
1. Create a calculator program in `calculator.py` that can perform addition, subtraction, multiplication, and division
2. Create comprehensive unit tests for the calculator in `test_calculator.py` 
3. Run the tests to ensure everything works correctly
4. The coder should handle the implementation and the tester should handle the testing

This is a complete software development task that requires both coding and testing expertise."""

#     goal="""
#     # 销售数据分析任务

# /home/guci/aiProjects/AgentFrameWork-worktrees/claude-code/sales_data.csv是销售数据文件，请使用此文件进行数据分析。

# # 规则
# 1. 不要生成图表
# 2. 报告中必须包含每个地区，每个产品，每个销售人员的销售额
# 3. 分析报告保存到sales_analysis_report.md
#     """

    print(f"   - 综合目标: {goal}")

    # 5. 通过顶层管理者执行目标
    print("\n5. 开始执行工作流...")
    print("   简化架构: 统一通过工作流规划处理所有任务")
    print("   - execute_instruction_syn(): 统一执行入口，自动分类指令")
    print("   - 工作流引擎: 自动适配单Agent或多Agent场景")
    
    try:
        print(f"\n--- 执行综合目标 (统一工作流模式) ---")
        # 使用execute_instruction_syn()方法进行统一处理
        # 工作流引擎会自动分析任务并智能分配给合适的Agent
        result = project_manager.execute_instruction_syn(goal)
        
        print(f"\n--- 综合目标执行结果 ---")
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
        print("\n🔧 简化架构优势:")
        print("• 统一执行入口: execute_instruction_syn()方法处理所有任务类型")
        print("• 智能分类系统: 自动识别信息性、单步骤、多步骤任务")
        print("• 自适应工作流: 根据available_agents自动调整执行策略")
        print("• 概念简化: 消除委托vs规划的概念重复")
        print("• 代码维护: 单一执行路径，更易维护和扩展")
        
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
    except Exception as e:
        print(f"\n\n演示执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()