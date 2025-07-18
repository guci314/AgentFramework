#!/usr/bin/env python3
"""
Visual Debugger 使用示例
展示如何以编程方式使用认知调试器
"""

import os
import sys

# 设置代理环境变量
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 添加路径 - 需要添加项目根目录
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from embodied_cognitive_workflow.visual_debugger import CycleDebuggerGUI
from embodied_cognitive_workflow.embodied_cognitive_workflow import CognitiveAgent
from python_core import Agent
from llm_lazy import get_model


def example_single_agent():
    """单Agent示例"""
    print("=== 单Agent调试示例 ===")
    
    # 创建LLM
    llm = get_model("gemini_2_5_flash")
    
    # 创建通用Agent
    general_agent = Agent(llm=llm)
    general_agent.name = "通用助手"
    general_agent.set_api_specification("通用任务执行、文件操作、代码编写")
    
    # 创建认知智能体
    cognitive_agent = CognitiveAgent(
        llm=llm,
        agents=[general_agent],
        max_cycles=5,
        verbose=False
    )
    
    # 创建调试器GUI
    debugger = CycleDebuggerGUI(cognitive_agent)
    
    # 设置任务
    debugger.task_text.delete("1.0", "end")
    debugger.task_text.insert("1.0", "创建一个简单的Python函数，返回'Hello, World!'")
    
    # 运行
    debugger.run()


def example_multi_agent():
    """多Agent协作示例"""
    print("=== 多Agent协作调试示例 ===")
    
    # 创建LLM
    llm = get_model("deepseek_chat")
    
    # 创建多个专业Agent
    agents = []
    
    # 1. Python专家
    python_agent = Agent(llm=llm)
    python_agent.name = "Python专家"
    python_agent.set_api_specification("Python代码编写、调试、优化")
    agents.append(python_agent)
    
    # 2. 测试专家
    test_agent = Agent(llm=llm)
    test_agent.name = "测试专家"
    test_agent.set_api_specification("单元测试编写、测试用例设计、pytest/unittest框架")
    agents.append(test_agent)
    
    # 3. 文档专家
    doc_agent = Agent(llm=llm)
    doc_agent.name = "文档专家"
    doc_agent.set_api_specification("代码文档编写、README创建、API文档")
    agents.append(doc_agent)
    
    # 创建认知智能体
    cognitive_agent = CognitiveAgent(
        llm=llm,
        agents=agents,
        max_cycles=15,
        verbose=False,
        enable_meta_cognition=False
    )
    
    # 创建调试器GUI
    debugger = CycleDebuggerGUI(cognitive_agent)
    
    # 设置复杂任务
    debugger.task_text.delete("1.0", "end")
    debugger.task_text.insert("1.0", 
        "创建一个计算器类，包含加减乘除功能，编写完整的单元测试，并添加使用文档"
    )
    
    # 运行
    debugger.run()


def example_force_cycle():
    """强制认知循环示例"""
    print("=== 强制认知循环调试示例 ===")
    
    # 创建LLM
    llm = get_model("qwen_qwq_32b")
    
    # 创建Agent
    agent = Agent(llm=llm)
    agent.name = "分析专家"
    agent.set_api_specification("深度分析、推理、问题解决")
    
    # 创建强制认知循环的CognitiveAgent
    class ForceCycleCognitiveAgent(CognitiveAgent):
        def _can_handle_directly(self, instruction: str) -> bool:
            return False  # 总是使用认知循环
    
    cognitive_agent = ForceCycleCognitiveAgent(
        llm=llm,
        agents=[agent],
        max_cycles=8,
        verbose=False
    )
    
    # 创建调试器GUI
    debugger = CycleDebuggerGUI(cognitive_agent)
    
    # 设置分析任务
    debugger.task_text.delete("1.0", "end")
    debugger.task_text.insert("1.0", "分析斐波那契数列的性质并给出前10项")
    
    # 运行
    debugger.run()


def example_with_meta_cognition():
    """带元认知的示例"""
    print("=== 元认知调试示例 ===")
    
    # 创建LLM
    llm = get_model("gemini_2_5_pro")
    
    # 创建Agent
    agent = Agent(llm=llm)
    agent.name = "高级智能体"
    agent.set_api_specification("复杂任务处理、策略制定、自我监督")
    
    # 创建带元认知的认知智能体
    cognitive_agent = CognitiveAgent(
        llm=llm,
        agents=[agent],
        max_cycles=10,
        verbose=False,
        enable_meta_cognition=True  # 启用元认知
    )
    
    # 创建调试器GUI
    debugger = CycleDebuggerGUI(cognitive_agent)
    
    # 设置需要元认知监督的任务
    debugger.task_text.delete("1.0", "end")
    debugger.task_text.insert("1.0", 
        "设计一个简单的任务管理系统，包含添加、删除、标记完成功能"
    )
    
    # 运行
    debugger.run()


def example_auto_mode():
    """自动判断模式示例 - 展示直接执行vs认知循环"""
    print("=== 自动判断模式示例 ===")
    print("系统会根据任务复杂度自动选择执行模式")
    print("简单任务：直接执行")
    print("复杂任务：认知循环")
    print("-" * 40)
    
    # 创建LLM
    llm = get_model("gemini_2_5_flash")
    
    # 创建通用Agent
    agent = Agent(llm=llm)
    agent.name = "智能助手"
    agent.set_api_specification("通用任务处理、代码编写、分析能力")
    
    # 创建正常模式的认知智能体（会自动判断）
    cognitive_agent = CognitiveAgent(
        llm=llm,
        agents=[agent],
        max_cycles=5,
        verbose=False
    )
    
    # 创建调试器GUI
    debugger = CycleDebuggerGUI(cognitive_agent)
    
    # 设置一个会触发不同模式的任务
    print("\n提示：")
    print("- 简单任务如'计算2+2'会直接执行")
    print("- 复杂任务如'创建一个类并编写测试'会触发认知循环")
    
    debugger.task_text.delete("1.0", "end")
    debugger.task_text.insert("1.0", "计算100的阶乘")  # 这是个中等复杂度的任务
    
    # 运行
    debugger.run()


if __name__ == "__main__":
    print("Visual Debugger 使用示例")
    print("=" * 60)
    print("1. 单Agent调试")
    print("2. 多Agent协作调试")
    print("3. 强制认知循环调试")
    print("4. 元认知调试")
    print("5. 自动判断模式（展示直接执行vs认知循环）")
    print("=" * 60)
    
    choice = input("请选择示例 (1-5): ").strip()
    
    if choice == "1":
        example_single_agent()
    elif choice == "2":
        example_multi_agent()
    elif choice == "3":
        example_force_cycle()
    elif choice == "4":
        example_with_meta_cognition()
    elif choice == "5":
        example_auto_mode()
    else:
        print("无效选择，运行默认示例")
        example_single_agent()