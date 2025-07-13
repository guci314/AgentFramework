#!/usr/bin/env python3
"""
安全的aider使用示例 - 避免交互式提示
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
    # 使用更安全的指令，避免触发shell命令
    instruction = """
    请使用aider Python API创建一个名为safe_calculator.py的文件。
    文件应包含一个Calculator类，具有add和multiply方法。
    注意：只创建文件，不要执行或测试代码。
    使用完全非交互式的配置。
    """
    
    print("开始执行任务...")
    result = agent.execute_sync(instruction)
    
    if result.success:
        print("✅ 任务成功完成")
        print(f"返回值: {result.return_value}")
    else:
        print("❌ 任务失败")
        print(f"错误: {result.stderr}")