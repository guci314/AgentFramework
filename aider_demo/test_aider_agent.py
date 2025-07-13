#!/usr/bin/env python3
"""
AiderAgent单元测试
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Agent
from llm_lazy import get_model
import tempfile
from aider_knowledge import aider_knowledge

class TestAiderAgent(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.llm = get_model('deepseek_v3')
        
        # 创建标准Agent并注入aider知识
        cls.agent = Agent(llm=cls.llm, stateful=True)
        cls.agent.loadKnowledge(aider_knowledge)
        
        # 创建临时测试目录
        cls.test_dir = tempfile.mkdtemp()
        os.chdir(cls.test_dir)
    
    def test_knowledge_loaded(self):
        """测试1: 验证知识是否成功加载"""
        # 通过让Agent回答问题来验证知识是否加载
        result = self.agent.chat_sync("请简单描述一下aider是什么？")
        
        self.assertTrue(result.success)
        response = result.return_value.lower()
        
        # 验证回答中包含aider相关内容
        self.assertIn("aider", response)
        self.assertTrue(
            "编程" in response or 
            "ai" in response or 
            "助手" in response
        )
        print("✅ 测试1通过: aider知识成功加载到Agent记忆中")
    
    def test_api_specification_set(self):
        """测试2: 验证API规范是否设置"""
        # 设置API规范
        self.agent.set_api_specification("""
        我是一个具备aider编程知识的智能体。
        """)
        self.assertIsNotNone(self.agent.api_specification)
        self.assertIn("aider", self.agent.api_specification)
        print("✅ 测试2通过: API规范正确设置")
    
    def test_understand_aider_command(self):
        """测试3: 验证Agent理解aider命令"""
        # 询问Agent关于aider的问题
        result = self.agent.chat_sync("aider支持哪些模型？")
        
        self.assertTrue(result.success)
        response = result.return_value.lower()
        
        # 验证回答中包含已注入的模型信息
        self.assertIn("deepseek", response)
        self.assertTrue(
            "gpt" in response or 
            "claude" in response or 
            "gemini" in response
        )
        
        print("✅ 测试3通过: Agent正确理解aider相关知识")
    
    def test_generate_aider_command(self):
        """测试4: 验证Agent生成aider命令的能力"""
        # 让Agent生成创建文件的aider命令
        instruction = "请生成一个使用aider创建hello.py文件的命令，使用deepseek模型"
        result = self.agent.execute_sync(instruction)
        
        self.assertTrue(result.success)
        command = result.return_value
        
        # 验证生成的命令包含关键元素
        self.assertIn("aider", command.lower())
        self.assertIn("--model", command)
        self.assertIn("deepseek", command.lower())
        self.assertIn("hello.py", command.lower())
        
        print("✅ 测试4通过: Agent能够生成正确的aider命令")
        print(f"   生成的命令: {command}")
    
    def test_aider_best_practices(self):
        """测试5: 验证Agent了解aider最佳实践"""
        # 询问最佳实践
        result = self.agent.chat_sync("使用aider时有哪些最佳实践？")
        
        self.assertTrue(result.success)
        response = result.return_value.lower()
        
        # 验证回答包含最佳实践内容
        self.assertTrue(
            "具体" in response or 
            "明确" in response or 
            "指令" in response
        )
        
        print("✅ 测试5通过: Agent了解aider最佳实践")

if __name__ == '__main__':
    unittest.main(verbosity=2)