#!/usr/bin/env python3
"""
自动生成的Visual Debugger脚本
基于: embodied_cognitive_workflow/hello_world_validation.py
"""

import os
import sys

# 设置代理环境变量
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from embodied_cognitive_workflow.visual_debugger import CycleDebuggerGUI
from embodied_cognitive_workflow.embodied_cognitive_workflow import CognitiveAgent
from python_core import Agent
from llm_lazy import get_model

def main():
    """运行Hello World验证任务的调试器"""
    print("🚀 启动Visual Debugger - Hello World验证任务")
    print("=" * 60)
    
    # 分析文件内容，识别到这是一个多Agent测试任务
    # 需要Python编程专家和测试专家
    
    # 创建LLM - 使用deepseek_chat（与原文件一致）
    llm = get_model("deepseek_chat")
    
    # 创建专业Agents
    agents = []
    
    # 1. Python编程专家
    python_agent = Agent(llm=llm)
    python_agent.name = "Python编程专家"
    python_agent.set_api_specification("专精Python编程、函数设计和代码实现")
    agents.append(python_agent)
    
    # 2. 测试专家
    test_agent = Agent(llm=llm)
    test_agent.name = "测试专家"
    test_agent.set_api_specification("专精单元测试、测试框架和测试用例设计")
    # 添加知识（从原文件中提取）
    test_agent.loadKnowledge("unittest的测试结果在标准错误流中而不是标准输出流中")
    test_agent.loadKnowledge("只运行指令中指定的测试文件，不要运行TestLoader的discover方法")
    agents.append(test_agent)
    
    # 创建认知智能体
    cognitive_agent = CognitiveAgent(
        llm=llm,
        agents=agents,
        max_cycles=15,  # 增加循环次数以确保任务完成
        verbose=False,
        enable_meta_cognition=False
    )
    
    # 添加知识到认知智能体
    cognitive_agent.loadKnowledge("unittest的测试结果在标准错误流中而不是标准输出流中")
    
    # 创建调试器GUI
    debugger = CycleDebuggerGUI(cognitive_agent)
    
    # 设置任务（从原文件中提取的任务描述）
    task_description = """写个hello world 函数和单元测试,分别保存在hello_world.py和test_hello_world.py文件中。
验证阶段不要运行所有测试，只运行test_hello_world.py文件中的测试。
单元测试框架使用unittest"""
    
    debugger.task_text.delete("1.0", "end")
    debugger.task_text.insert("1.0", task_description)
    
    print("📋 任务设置完成：")
    print(task_description)
    print("-" * 60)
    print("✨ 调试器GUI已启动，请在窗口中操作")
    print("\n💡 GUI窗口已在后台独立运行")
    print("   查看日志: tail -f debugger.log")
    print("   如需终止: 关闭GUI窗口或使用kill命令")
    
    # 运行GUI - 会保持打开状态直到用户手动关闭
    debugger.run()
    
    print("\n" + "=" * 60)
    print("✅ 调试器已关闭")
    print("📁 生成的文件已保留在当前目录中：")
    
    # 显示生成的文件
    generated_files = ["hello_world.py", "test_hello_world.py"]
    for file in generated_files:
        if os.path.exists(file):
            print(f"   - {file}")
    
    print("\n💡 提示：如需删除这些文件，请手动删除")

if __name__ == "__main__":
    main()