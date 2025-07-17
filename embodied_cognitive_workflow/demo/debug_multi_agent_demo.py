"""
使用认知调试器演示多Agent选择

展示调试器如何显示Agent选择过程。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embodied_cognitive_workflow import CognitiveAgent
from cognitive_debugger import CognitiveDebugger, StepType
from python_core import Agent
from llm_lazy import get_model


def main():
    """使用调试器展示多Agent选择"""
    
    # 设置代理
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"
    
    # 获取语言模型
    llm = get_model('gemini_2_5_flash')
    
    # 创建专业Agent
    agents = []
    
    # 1. 数学专家
    math_expert = Agent(llm=llm)
    math_expert.name = "数学专家"
    math_expert.api_specification = "擅长数学计算、统计分析、数值处理"
    agents.append(math_expert)
    
    # 2. 文件专家
    file_expert = Agent(llm=llm)
    file_expert.name = "文件专家"
    file_expert.api_specification = "擅长文件操作、数据保存、格式转换"
    agents.append(file_expert)
    
    # 3. 通用助手
    general_helper = Agent(llm=llm)
    general_helper.name = "通用助手"
    general_helper.api_specification = "通用任务处理、文本生成、数据整理"
    agents.append(general_helper)
    
    # 创建认知智能体
    cognitive_agent = CognitiveAgent(
        llm=llm,
        agents=agents,
        max_cycles=5,
        verbose=False,  # 关闭verbose以便更清楚地看到调试信息
        enable_meta_cognition=False
    )
    
    # 创建调试器
    debugger = CognitiveDebugger(cognitive_agent)
    
    print("=== 认知调试器：多Agent选择演示 ===\n")
    print("可用的Agent：")
    for agent in agents:
        print(f"  • {agent.name}: {agent.api_specification}")
    print()
    
    # 测试任务：需要文件操作的任务
    task = "请将数字 42 的平方根计算结果保存到 result.txt 文件中"
    
    print(f"任务：{task}")
    print("-" * 60)
    
    # 开始调试
    debugger.start_debug(task)
    
    # 设置断点在决策步骤
    debugger.set_breakpoint(StepType.DECISION_MAKING, description="查看Agent选择")
    debugger.set_breakpoint(StepType.BODY_EXECUTION, description="查看执行者")
    
    print("\n开始单步执行...\n")
    
    # 执行到第一个断点
    results = debugger.run_until_breakpoint()
    
    # 显示决策信息
    if results:
        last_step = results[-1]
        if last_step.step_type == StepType.DECISION_MAKING:
            print("\n🔍 决策断点命中！")
            if last_step.debug_info:
                if "selected_agent" in last_step.debug_info:
                    print(f"   选择的Agent: {last_step.debug_info['selected_agent']}")
                if "instruction" in last_step.debug_info:
                    print(f"   执行指令: {last_step.debug_info['instruction']}")
                if "available_agents" in last_step.debug_info:
                    print(f"   可用Agent: {', '.join(last_step.debug_info['available_agents'])}")
    
    # 继续执行到下一个断点
    print("\n继续执行...\n")
    results = debugger.run_until_breakpoint()
    
    # 显示执行信息
    if results:
        last_step = results[-1]
        if last_step.step_type == StepType.BODY_EXECUTION:
            print("\n🔍 执行断点命中！")
            if last_step.debug_info:
                if "selected_agent" in last_step.debug_info:
                    print(f"   执行者: {last_step.debug_info['selected_agent']}")
                if "instruction" in last_step.debug_info:
                    print(f"   正在执行: {last_step.debug_info['instruction']}")
    
    # 完成执行
    print("\n继续执行到完成...\n")
    final_results = debugger.run_to_completion()
    
    # 显示执行流程
    print("\n" + "="*60)
    print(debugger.visualize_execution_flow())
    
    # 显示性能报告
    report = debugger.get_performance_report()
    print(f"\n性能分析：")
    print(f"  总时间: {report.total_time:.3f}s")
    print(f"  平均步骤时间: {report.avg_step_time:.3f}s")
    print(f"  最慢步骤: {report.slowest_step}")
    
    # 清理测试文件
    if os.path.exists("result.txt"):
        with open("result.txt", "r") as f:
            content = f.read()
        print(f"\n生成的文件内容：{content}")
        os.remove("result.txt")
        print("已清理测试文件")


if __name__ == "__main__":
    main()