#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试跳转功能修复的脚本
"""

from enhancedAgent_v2 import MultiStepAgent_v2
from llm_lazy import get_modelnt_base import Agent

def test_jump_functionality():
    """测试跳转功能"""
    
    # 创建多步骤Agent
    multi_agent = MultiStepAgent_v2(llm=get_model("deepseek_chat"))
    
    # 注册一个简单的Agent
    test_agent = Agent(llm=get_model("deepseek_chat"))
    multi_agent.register_agent(
        name="test_agent",
        instance=test_agent
    )
    
    # 创建一个简单的测试指令
    main_instruction = """
    执行一个简单的测试任务：
    1. 输出 "第一步完成"
    2. 输出 "第二步完成" 
    3. 输出 "第三步完成"
    4. 验证所有步骤是否完成
    
    如果第二步完成后，应该直接跳转到验证步骤。
    """
    
    print("开始测试跳转功能...")
    print("=" * 50)
    
    try:
        # 执行多步骤任务
        result = multi_agent.execute_multi_step(main_instruction)
        print("\n测试结果:")
        print("=" * 50)
        print(result)
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_jump_functionality() 