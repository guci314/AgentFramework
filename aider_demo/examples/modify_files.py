#!/usr/bin/env python3
"""
示例：使用Agent修改现有文件
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
    
    # 首先创建一个示例文件
    with open('existing_script.py', 'w') as f:
        f.write('''
def main():
    print("This is a simple script")
    return 0

if __name__ == "__main__":
    main()
''')
    
    # 指令：为现有文件添加功能
    instruction = """
    请使用aider修改existing_script.py文件，添加以下功能：
    1. 日志记录功能
    2. 配置文件读取
    3. 命令行参数解析
    使用deepseek模型，不要使用git
    """
    
    print("🔧 开始修改文件...")
    result = agent.execute_sync(instruction)
    print(f"修改结果: {result.return_value}")

if __name__ == '__main__':
    main()