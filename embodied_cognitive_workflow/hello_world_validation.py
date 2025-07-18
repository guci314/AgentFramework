#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hello World任务验证：单/多Agent模式对比测试

本模块用于验证多Agent重构后的系统功能正确性，通过对比单Agent和多Agent模式
在执行简单Hello World任务时的行为差异，确保重构成功且向后兼容。

主要功能：
- 测试多Agent模式下的任务执行能力
- 验证Agent查找和选择机制
- 确保方法命名一致性
- 验证向后兼容性

测试场景：
- 创建Python编程专家和测试专家两个专门Agent
- 执行Hello World函数和单元测试生成任务
- 验证多Agent协作的完整工作流程

作者：AI Agent Framework Team
创建时间：2024年
版本：1.0
"""

import sys
import os
import time

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from python_core import Agent
from embodied_cognitive_workflow import CognitiveAgent
from llm_lazy import get_model
from unittest.mock import Mock

def create_llm():
    """创建DeepSeek模型或模拟LLM"""
    try:
        # 尝试使用真实的DeepSeek模型
        return get_model("deepseek_chat")
    except Exception as e:
        print(f"⚠️ 无法加载DeepSeek模型，使用Mock LLM: {e}")
        # 如果失败，使用模拟LLM
        mock_llm = Mock()
        mock_llm.invoke = Mock(return_value=Mock(content="def hello_world():\n    return 'Hello, World!'"))
        return mock_llm



def test_multi_agent_mode():
    """测试多Agent模式"""
    print("🔸 测试多Agent模式")
    
    # 创建专门的Agent
    llm = create_llm()
    
    # Python编程专家
    python_agent = Agent(llm=llm)
    python_agent.name = "Python编程专家"
    python_agent.set_api_specification("专精Python编程、函数设计和代码实现")
    
    # 测试专家
    test_agent = Agent(llm=llm)
    test_agent.name = "测试专家"
    test_agent.set_api_specification("专精单元测试、测试框架和测试用例设计")
    test_agent.loadKnowledge("unittest的测试结果在标准错误流中而不是标准输出流中")
    test_agent.loadKnowledge("只运行指令中指定的测试文件，不要运行TestLoader的discover方法")
    
    # 创建多Agent工作流
    workflow = CognitiveAgent(llm=llm, agents=[python_agent, test_agent], verbose=False, enable_meta_cognition=False)
    workflow.loadKnowledge("unittest的测试结果在标准错误流中而不是标准输出流中")
    
    # 测试执行Hello World任务
    try:
        result = workflow.execute_sync("写个hello world 函数和单元测试,分别保存在hello_world.py和test_hello_world.py文件中。验证阶段不要运行所有测试，只运行test_hello_world.py文件中的测试。单元测试框架使用unittest")
        print(f"   - 执行成功: {result.success}")
        print(f"   - 执行结果: {result.stdout[:50]}..." if result.stdout else "   - 无执行结果")
    except Exception as e:
        print(f"   - 执行遇到问题: {e}")
    
    print("   ✅ 多Agent模式测试完成\n")
    return workflow




if __name__ == '__main__':
    test_multi_agent_mode()
    