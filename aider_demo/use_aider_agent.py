#!/usr/bin/env python3
"""
使用标准Agent加载aider知识
"""
import sys
import os

# 添加父目录到Python路径以导入Agent框架
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Agent
from llm_lazy import get_model
from aider_knowledge import aider_knowledge

# 创建标准Agent
llm = get_model('deepseek_chat')
agent = Agent(llm=llm, stateful=True)

# 通过loadKnowledge注入aider知识
agent.loadKnowledge(aider_knowledge)

# # 设置Agent的API规范（可选）
# agent.set_api_specification("""
# 我是一个具备aider编程知识的智能体。我了解：
# 1. aider的各种命令和参数
# 2. 如何使用aider生成和修改代码
# 3. aider支持的AI模型
# 4. 最佳实践和注意事项
# """)

# Agent现在已经具备了aider编程知识，可以回答相关问题和生成aider命令

if __name__ == "__main__":
    # # 示例：询问aider相关问题
    # result = agent.chat_sync("aider支持哪些AI模型？")
    # print("Agent回答:", result.return_value)
    
    # 示例：生成aider命令
    result=None
    for i in agent.execute_stream("创建Python计算器class，类名为Calculator，文件名为calculator1.py。创建单元测试文件calculator1_test.py。"):
        print(i,end="",flush=True)
        result=i
    print("\nAgent生成的命令:")
    print(result)