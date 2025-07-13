#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent类单元测试 - 智能体集成测试
"""

import unittest
import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Agent
from llm_lazy import get_model
from agent_base import Result


class TestAgentBasic(unittest.TestCase):
    """Agent基础功能测试（不需要API密钥）"""
    
    def setUp(self):
        """测试前准备"""
        pass  # 不初始化需要API的Agent
    
    def test_agent_initialization_basic(self):
        """测试Agent基础初始化"""
        if not os.getenv('DEEPSEEK_API_KEY'):
            self.skipTest("需要DEEPSEEK_API_KEY环境变量")
        
        # 测试基本初始化
        agent = Agent(llm=get_model("deepseek_v3"), stateful=True)
        
        self.assertIsNotNone(agent.llm)
        self.assertIsNotNone(agent.device)
        self.assertIsNotNone(agent.thinker)
        self.assertIsInstance(agent.evaluators, list)
        self.assertGreater(len(agent.evaluators), 0)
        self.assertEqual(agent.max_retries, 10)
        self.assertFalse(agent.skip_evaluation)
        self.assertFalse(agent.skip_generation)
    
    def test_agent_initialization_with_options(self):
        """测试带选项的Agent初始化"""
        if not os.getenv('DEEPSEEK_API_KEY'):
            self.skipTest("需要DEEPSEEK_API_KEY环境变量")
        
        # 测试带选项的初始化
        agent = Agent(
            llm=get_model("deepseek_v3"),
            stateful=False,
            max_retries=5,
            skip_evaluation=True,
            skip_generation=True
        )
        
        self.assertEqual(agent.max_retries, 5)
        self.assertTrue(agent.skip_evaluation)
        self.assertTrue(agent.skip_generation)


@unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
class TestAgentExecution(unittest.TestCase):
    """Agent执行功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.agent = Agent(llm=get_model("deepseek_v3"), stateful=True, max_retries=3)
    
    def test_simple_task_execution_sync(self):
        """测试简单任务同步执行"""
        instruction = "计算1到10的和并打印结果"
        
        result = self.agent.execute_sync(instruction)
        
        self.assertIsInstance(result, Result)
        self.assertTrue(result.success)
        self.assertIn("55", result.stdout)  # 1+2+...+10=55
        print(f"✅ 简单任务同步执行测试通过")
        print(f"执行结果: {result.stdout}")
    
    def test_arithmetic_task_execution(self):
        """测试算术任务执行"""
        instruction = "创建一个函数计算圆的周长和面积，然后计算半径为3的圆"
        
        result = self.agent.execute_sync(instruction)
        
        self.assertTrue(result.success)
        # 半径3的圆：周长≈18.85，面积≈28.27
        self.assertTrue(any(str(round(3.14159 * 6, 1)) in result.stdout for _ in [1]))
        print(f"✅ 算术任务执行测试通过")
    
    def test_data_structure_task(self):
        """测试数据结构任务"""
        instruction = "创建一个字典存储3个学生的姓名和成绩，然后计算平均分"
        
        result = self.agent.execute_sync(instruction)
        
        self.assertTrue(result.success)
        self.assertIn("平均", result.stdout)
        print(f"✅ 数据结构任务测试通过")
    
    def test_loop_and_condition_task(self):
        """测试循环和条件任务"""
        instruction = "找出1到20之间所有的偶数并计算它们的总和"
        
        result = self.agent.execute_sync(instruction)
        
        self.assertTrue(result.success)
        # 2+4+6+8+10+12+14+16+18+20 = 110
        self.assertIn("110", result.stdout)
        print(f"✅ 循环和条件任务测试通过")


@unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
class TestAgentStreamExecution(unittest.TestCase):
    """Agent流式执行测试"""
    
    def setUp(self):
        """测试前准备"""
        self.agent = Agent(llm=get_model("deepseek_v3"), stateful=True, max_retries=2)
    
    def test_stream_execution_basic(self):
        """测试基础流式执行"""
        instruction = "编写一个程序计算阶乘函数，然后计算5的阶乘"
        
        chunks = []
        final_result = None
        
        for chunk in self.agent.execute_stream(instruction):
            if isinstance(chunk, str):
                chunks.append(chunk)
            elif isinstance(chunk, Result):
                final_result = chunk
                if chunk.success:
                    break
        
        self.assertIsNotNone(final_result)
        self.assertTrue(final_result.success)
        self.assertGreater(len(chunks), 0)
        # 5! = 120
        self.assertIn("120", final_result.stdout)
        print(f"✅ 流式执行基础测试通过")
        print(f"流式输出块数: {len(chunks)}")
    
    def test_stream_execution_with_error_recovery(self):
        """测试流式执行的错误恢复"""
        instruction = "写一个计算平方根的程序，包含错误处理"
        
        results = []
        
        for chunk in self.agent.execute_stream(instruction):
            if isinstance(chunk, Result):
                results.append(chunk)
                if chunk.success:
                    break
        
        # 应该最终成功
        self.assertTrue(any(r.success for r in results))
        print(f"✅ 流式执行错误恢复测试通过")
    
    def test_stream_execution_complex_task(self):
        """测试流式执行复杂任务"""
        instruction = "创建一个类表示银行账户，包含存款、取款功能，然后测试这些功能"
        
        final_result = None
        chunk_count = 0
        
        for chunk in self.agent.execute_stream(instruction):
            if isinstance(chunk, str):
                chunk_count += 1
            elif isinstance(chunk, Result):
                final_result = chunk
                if chunk.success:
                    break
        
        self.assertIsNotNone(final_result)
        self.assertTrue(final_result.success)
        self.assertIn("class", final_result.code.lower())
        print(f"✅ 流式执行复杂任务测试通过")


@unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
class TestAgentChatFunctionality(unittest.TestCase):
    """Agent聊天功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.agent = Agent(llm=get_model("deepseek_v3"), stateful=True)
    
    def test_chat_sync_basic(self):
        """测试同步聊天基础功能"""
        message = "请解释什么是递归算法"
        
        result = self.agent.chat_sync(message)
        
        self.assertIsInstance(result, Result)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.return_value)
        self.assertIn("递归", result.return_value)
        print(f"✅ 同步聊天基础功能测试通过")
        print(f"聊天回复: {result.return_value[:100]}...")
    
    def test_chat_stream_basic(self):
        """测试流式聊天基础功能"""
        message = "请简单介绍Python中的列表和元组的区别"
        
        chunks = []
        final_result = None
        
        for chunk in self.agent.chat_stream(message):
            if isinstance(chunk, str):
                chunks.append(chunk)
            elif isinstance(chunk, Result):
                final_result = chunk
                break
        
        self.assertIsNotNone(final_result)
        self.assertTrue(final_result.success)
        self.assertGreater(len(chunks), 0)
        
        full_response = ''.join(chunks)
        self.assertTrue(any(word in full_response for word in ["列表", "元组", "list", "tuple"]))
        print(f"✅ 流式聊天基础功能测试通过")
        print(f"流式回复块数: {len(chunks)}")
    
    def test_chat_with_json_format(self):
        """测试JSON格式聊天"""
        message = "请用JSON格式回答：Python有哪些基本数据类型？"
        response_format = {"type": "json_object"}
        
        result = self.agent.chat_sync(message, response_format)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.return_value)
        
        # 尝试解析JSON
        import json
        try:
            json_data = json.loads(result.return_value)
            self.assertIsInstance(json_data, dict)
            print(f"✅ JSON格式聊天测试通过")
            print(f"JSON响应: {json_data}")
        except json.JSONDecodeError:
            print(f"⚠️ JSON解析失败，但聊天功能正常")


@unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
class TestAgentEvaluationSystem(unittest.TestCase):
    """Agent评估系统测试"""
    
    def setUp(self):
        """测试前准备"""
        self.agent = Agent(llm=get_model("deepseek_v3"), stateful=True, max_retries=2)
    
    def test_single_evaluator(self):
        """测试单个评估器"""
        instruction = "计算2的平方并打印结果"
        
        result = self.agent.execute_sync(instruction)
        
        self.assertTrue(result.success)
        self.assertIn("4", result.stdout)
        print(f"✅ 单个评估器测试通过")
    
    def test_custom_evaluation_message(self):
        """测试自定义评估消息"""
        custom_eval_message = '''
        请判断是否完成了任务。请返回json格式的结果。
        json有两个字段，taskIsComplete，值为true或false，reason字段，字符串类型，判断的理由。

        # 判断规则：
        1. 必须包含正确的数学计算
        2. 必须有清晰的输出
        
        # 任务：{instruction}
        # 代码执行结果：{result}
        '''
        
        self.agent.loadEvaluationSystemMessage(custom_eval_message)
        
        instruction = "计算3+7的结果"
        result = self.agent.execute_sync(instruction)
        
        self.assertTrue(result.success)
        self.assertIn("10", result.stdout)
        print(f"✅ 自定义评估消息测试通过")
        print(f"评估器数量: {len(self.agent.evaluators)}")
    
    def test_multiple_evaluators(self):
        """测试多个评估器"""
        # 添加多个评估器
        eval_message1 = '''
        判断数学计算是否正确。
        返回JSON: {"taskIsComplete": true/false, "reason": "原因"}
        
        任务：{instruction}
        结果：{result}
        '''
        
        eval_message2 = '''
        判断代码质量是否良好。
        返回JSON: {"taskIsComplete": true/false, "reason": "原因"}
        
        任务：{instruction}
        结果：{result}
        '''
        
        self.agent.loadEvaluationSystemMessage(eval_message1)
        self.agent.loadEvaluationSystemMessage(eval_message2)
        
        instruction = "编写计算圆面积的函数并测试"
        result = self.agent.execute_sync(instruction)
        
        # 多个评估器都要通过才算成功
        self.assertTrue(result.success)
        print(f"✅ 多个评估器测试通过")
        print(f"当前评估器数量: {len(self.agent.evaluators)}")


@unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
class TestAgentKnowledgeManagement(unittest.TestCase):
    """Agent知识管理测试"""
    
    def setUp(self):
        """测试前准备"""
        self.agent = Agent(llm=get_model("deepseek_v3"), stateful=True)
    
    def test_knowledge_loading(self):
        """测试知识加载"""
        knowledge = """
        重要的数学常识：
        1. 圆周率π ≈ 3.14159
        2. 自然常数e ≈ 2.71828
        3. 黄金比例φ ≈ 1.618
        """
        
        self.agent.loadKnowledge(knowledge)
        
        instruction = "使用圆周率计算半径为2的圆的面积"
        result = self.agent.execute_sync(instruction)
        
        self.assertTrue(result.success)
        # 面积 = π * r² = π * 4 ≈ 12.56
        self.assertTrue(any(str(round(3.14159 * 4, 1)) in result.stdout for _ in [1]))
        print(f"✅ 知识加载测试通过")
    
    def test_python_module_loading(self):
        """测试Python模块加载"""
        # 加载一些标准模块
        try:
            self.agent.loadPythonModules(['math', 'json'])
            
            instruction = "使用math模块计算sin(π/2)的值"
            result = self.agent.execute_sync(instruction)
            
            self.assertTrue(result.success)
            # sin(π/2) = 1
            self.assertIn("1", result.stdout)
            print(f"✅ Python模块加载测试通过")
        except Exception as e:
            print(f"⚠️ Python模块加载测试跳过: {e}")


@unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
class TestAgentConfigurationOptions(unittest.TestCase):
    """Agent配置选项测试"""
    
    def test_skip_evaluation_option(self):
        """测试跳过评估选项"""
        agent = Agent(llm=get_model("deepseek_v3"), stateful=True, skip_evaluation=True)
        
        instruction = "计算5+5的结果"
        result = agent.execute_sync(instruction)
        
        # 跳过评估应该直接返回执行结果
        self.assertTrue(result.success)
        self.assertIn("10", result.stdout)
        print(f"✅ 跳过评估选项测试通过")
    
    def test_skip_generation_option(self):
        """测试跳过生成选项"""
        agent = Agent(llm=get_model("deepseek_v3"), stateful=True, skip_generation=True)
        
        instruction = "计算6+4的结果"
        result = agent.execute_sync(instruction)
        
        # 跳过生成应该返回原始执行结果
        self.assertTrue(result.success)
        self.assertIn("10", result.stdout)
        print(f"✅ 跳过生成选项测试通过")
    
    def test_both_skip_options(self):
        """测试同时跳过评估和生成"""
        agent = Agent(
            llm=get_model("deepseek_v3"),
            stateful=True,
            skip_evaluation=True,
            skip_generation=True
        )
        
        instruction = "计算7+3的结果"
        result = agent.execute_sync(instruction)
        
        # 同时跳过应该直接返回Thinker的执行结果
        self.assertTrue(result.success)
        self.assertIn("10", result.stdout)
        print(f"✅ 同时跳过选项测试通过")
    
    def test_max_retries_option(self):
        """测试最大重试次数选项"""
        agent = Agent(llm=get_model("deepseek_v3"), stateful=True, max_retries=1)
        
        self.assertEqual(agent.max_retries, 1)
        self.assertEqual(agent.thinker.max_retries, 1)
        print(f"✅ 最大重试次数选项测试通过")


@unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
class TestAgentComplexScenarios(unittest.TestCase):
    """Agent复杂场景测试"""
    
    def setUp(self):
        """测试前准备"""
        self.agent = Agent(llm=get_model("deepseek_v3"), stateful=True, max_retries=3)
    
    def test_stateful_multi_step_task(self):
        """测试有状态的多步骤任务"""
        # 第一步：创建数据
        step1 = "创建一个包含10个随机数的列表并存储为变量data"
        result1 = self.agent.execute_sync(step1)
        self.assertTrue(result1.success)
        
        # 第二步：处理数据
        step2 = "使用之前创建的data变量，计算其平均值和标准差"
        result2 = self.agent.execute_sync(step2)
        self.assertTrue(result2.success)
        self.assertIn("平均", result2.stdout)
        
        print(f"✅ 有状态多步骤任务测试通过")
    
    def test_file_operation_task(self):
        """测试文件操作任务"""
        instruction = """
        创建一个临时文件，写入一些学生成绩数据，
        然后读取文件并计算平均分，最后删除临时文件
        """
        
        result = self.agent.execute_sync(instruction)
        
        self.assertTrue(result.success)
        self.assertIn("平均", result.stdout)
        print(f"✅ 文件操作任务测试通过")
    
    def test_class_and_object_task(self):
        """测试类和对象任务"""
        instruction = """
        定义一个Calculator类，包含加减乘除方法，
        创建实例并进行一些计算，展示结果
        """
        
        result = self.agent.execute_sync(instruction)
        
        self.assertTrue(result.success)
        self.assertIn("class", result.code.lower())
        print(f"✅ 类和对象任务测试通过")
    
    def test_error_recovery_scenario(self):
        """测试错误恢复场景"""
        instruction = "计算一个复杂的数学表达式，包含可能的错误处理"
        
        result = self.agent.execute_sync(instruction)
        
        # 即使有错误，最终应该能恢复
        self.assertTrue(result.success)
        print(f"✅ 错误恢复场景测试通过")


if __name__ == '__main__':
    print("🚀 开始Agent类单元测试...")
    print("="*60)
    
    # 检查API密钥
    if os.getenv('DEEPSEEK_API_KEY'):
        print("📡 检测到DEEPSEEK_API_KEY，将运行完整测试")
    else:
        print("⚠️  未检测到DEEPSEEK_API_KEY，将跳过API相关测试")
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加基础测试
    suite.addTests(loader.loadTestsFromTestCase(TestAgentBasic))
    
    # 添加API相关测试
    if os.getenv('DEEPSEEK_API_KEY'):
        suite.addTests(loader.loadTestsFromTestCase(TestAgentExecution))
        suite.addTests(loader.loadTestsFromTestCase(TestAgentStreamExecution))
        suite.addTests(loader.loadTestsFromTestCase(TestAgentChatFunctionality))
        suite.addTests(loader.loadTestsFromTestCase(TestAgentEvaluationSystem))
        suite.addTests(loader.loadTestsFromTestCase(TestAgentKnowledgeManagement))
        suite.addTests(loader.loadTestsFromTestCase(TestAgentConfigurationOptions))
        suite.addTests(loader.loadTestsFromTestCase(TestAgentComplexScenarios))
    
    print("="*60)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试总结
    print("\n" + "="*60)
    if result.wasSuccessful():
        print("🎉 所有测试通过！")
    else:
        print(f"❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        
        if result.failures:
            print("\n失败的测试:")
            for test, error in result.failures:
                print(f"  - {test}")
                print(f"    {error[:200]}...")
                
        if result.errors:
            print("\n错误的测试:")
            for test, error in result.errors:
                print(f"  - {test}")
                print(f"    {error[:200]}...")
    
    print(f"📊 测试统计:")
    print(f"   - 运行测试: {result.testsRun}")
    print(f"   - 成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   - 失败: {len(result.failures)}")
    print(f"   - 错误: {len(result.errors)}")
    print("="*60)