#!/usr/bin/env python3
"""
验证Agent是否正确使用Aider原则
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

if __name__ == "__main__":
    print("验证Agent是否遵循'优先使用Aider'原则...")
    
    # 询问Agent关于创建文件的方法
    result = agent.chat_sync("如果用户要求你创建一个Python文件，你应该怎么做？")
    
    print("\nAgent的回答：")
    print(result.return_value)
    
    # 检查回答中是否提到aider
    if "aider" in result.return_value.lower():
        print("\n✅ 验证通过：Agent知道应该使用aider来创建Python文件")
    else:
        print("\n❌ 验证失败：Agent没有提到使用aider")