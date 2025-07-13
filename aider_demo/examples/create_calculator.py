#!/usr/bin/env python3
"""
示例：使用Agent创建计算器程序
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from python_core import Agent
from llm_lazy import get_model
from aider_knowledge import aider_knowledge

def main():
    # 初始化标准Agent
    llm = get_model('deepseek_v3')
    agent = Agent(llm=llm, stateful=True)
    
    # 注入aider知识
    agent.loadKnowledge(aider_knowledge)
    
    # 指令：创建一个计算器程序
    instruction = """
    请使用aider创建一个名为calculator.py的简单计算器程序，包含以下功能：
    1. 加法、减法、乘法、除法
    2. 主函数with命令行交互
    3. 错误处理
    使用deepseek模型
    """
    
    print("🚀 开始创建计算器程序...")
    result = agent.execute_sync(instruction)
    print(f"执行结果: {result.return_value}")

if __name__ == '__main__':
    main()