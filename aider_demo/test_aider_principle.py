#!/usr/bin/env python3
"""
测试Agent是否遵循"优先使用Aider"原则
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
    print("=== 测试1: 请求创建Python文件 ===")
    instruction1 = "请创建一个名为user_manager.py的Python文件，包含UserManager类，具有添加用户和删除用户的功能"
    
    result1 = agent.execute_sync(instruction1)
    print(f"测试1结果: {'✅ 成功' if result1.success else '❌ 失败'}")
    if result1.success:
        print("返回内容摘要:", result1.return_value[:200] + "..." if len(result1.return_value) > 200 else result1.return_value)
    
    print("\n" + "="*50 + "\n")
    
    print("=== 测试2: 请求解释代码概念 ===")
    instruction2 = "请解释一下Python中的装饰器是什么？"
    
    result2 = agent.chat_sync(instruction2)
    print(f"测试2结果: {'✅ 成功' if result2.success else '❌ 失败'}")
    print("回答摘要:", result2.return_value[:200] + "..." if len(result2.return_value) > 200 else result2.return_value)