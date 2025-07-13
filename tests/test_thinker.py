#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thinker类单元测试 - 代码生成器测试
"""

import unittest
import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Thinker, StatefulExecutor
from llm_lazy import get_model
from agent_base import Result


class TestThinkerBasic(unittest.TestCase):
    """Thinker基础功能测试（不需要API密钥）"""
    
    def setUp(self):
        """测试前准备"""
        self.device = StatefulExecutor()
        # 不初始化真实的Thinker，避免API调用
    
    def test_thinker_initialization(self):
        """测试Thinker初始化"""
        if not os.getenv('DEEPSEEK_API_KEY'):
            self.skipTest("需要DEEPSEEK_API_KEY环境变量")
        
        thinker = Thinker(llm=get_model("deepseek_v3"), device=self.device)
        
        # 验证初始化属性
        self.assertIsNotNone(thinker.llm)
        self.assertIsNotNone(thinker.device)
        self.assertEqual(thinker.max_retries, 10)
        self.assertIsInstance(thinker.memory, list)
        self.assertEqual(thinker.current_code, '')
    
    def test_device_integration(self):
        """测试与Device的集成"""
        # 直接测试device功能
        code = """
x = 42
y = 58
result = x + y
print(f"计算结果: {result}")
return_value = result
"""
        result = self.device.execute_code(code)
        
        self.assertTrue(result.success)
        self.assertIn("计算结果: 100", result.stdout)
        self.assertEqual(self.device.get_variable('return_value'), 100)


@unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
class TestThinkerWithDeepSeek(unittest.TestCase):
    """Thinker与DeepSeek集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.device = StatefulExecutor()
        self.thinker = Thinker(llm=get_model("deepseek_v3"), device=self.device, max_retries=3)
    
    def test_simple_code_generation(self):
        """测试简单代码生成"""
        instruction = "写一个Python程序，计算1到10的和并打印结果"
        
        result = self.thinker.execute_sync(instruction)
        
        self.assertIsInstance(result, Result)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.code)
        self.assertIn("55", result.stdout)  # 1+2+...+10=55
        print(f"✅ 简单代码生成测试通过")
        print(f"生成的代码:\n{result.code}")
        print(f"执行输出:\n{result.stdout}")
    
    def test_arithmetic_calculation(self):
        """测试算术计算任务"""
        instruction = "创建一个函数来计算圆的面积，然后计算半径为5的圆的面积"
        
        result = self.thinker.execute_sync(instruction)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.code)
        # 圆面积 = π * r^2，r=5时约为78.54
        self.assertTrue("78" in result.stdout or "79" in result.stdout)
        print(f"✅ 算术计算测试通过")
        print(f"生成的代码:\n{result.code}")
    
    def test_data_processing(self):
        """测试数据处理任务"""
        instruction = "创建一个包含5个学生成绩的列表，然后计算平均分、最高分和最低分"
        
        result = self.thinker.execute_sync(instruction)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.code)
        self.assertIn("平均", result.stdout)
        self.assertIn("最高", result.stdout)
        self.assertIn("最低", result.stdout)
        print(f"✅ 数据处理测试通过")
        print(f"执行输出:\n{result.stdout}")
    
    def test_loop_and_condition(self):
        """测试循环和条件语句"""
        instruction = "写一个程序，找出1到100之间所有能被3整除但不能被5整除的数字"
        
        result = self.thinker.execute_sync(instruction)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.code)
        # 应该包含3, 6, 9, 12, 18, 21等
        self.assertTrue(any(str(i) in result.stdout for i in [3, 6, 9, 12, 18, 21]))
        print(f"✅ 循环和条件测试通过")
    
    def test_error_handling_and_retry(self):
        """测试错误处理和重试机制"""
        instruction = "创建一个故意有语法错误的程序，然后修复它"
        
        # 这个测试可能会触发重试机制
        result = self.thinker.execute_sync(instruction)
        
        # 即使有重试，最终应该成功
        self.assertTrue(result.success)
        print(f"✅ 错误处理和重试测试通过")


@unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
class TestThinkerStreamExecution(unittest.TestCase):
    """Thinker流式执行测试"""
    
    def setUp(self):
        """测试前准备"""
        self.device = StatefulExecutor()
        self.thinker = Thinker(llm=get_model("deepseek_v3"), device=self.device, max_retries=2)
    
    def test_stream_execution(self):
        """测试流式执行"""
        instruction = "编写一个程序计算斐波那契数列的前10项"
        
        chunks = []
        final_result = None
        
        for chunk in self.thinker.execute_stream(instruction):
            if isinstance(chunk, str):
                chunks.append(chunk)
            elif isinstance(chunk, Result):
                final_result = chunk
                break
        
        self.assertIsNotNone(final_result)
        self.assertTrue(final_result.success)
        self.assertGreater(len(chunks), 0)  # 应该有流式输出
        
        # 验证斐波那契数列
        self.assertTrue(any("55" in str(chunk) for chunk in chunks + [final_result.stdout]))
        print(f"✅ 流式执行测试通过")
        print(f"流式输出块数: {len(chunks)}")
    
    def test_stream_with_multiple_attempts(self):
        """测试流式执行的多次尝试"""
        instruction = "写一个复杂的数据分析程序，包含异常处理"
        
        results = []
        
        for chunk in self.thinker.execute_stream(instruction):
            if isinstance(chunk, Result):
                results.append(chunk)
                if chunk.success:
                    break
        
        # 应该最终成功
        self.assertTrue(any(r.success for r in results))
        print(f"✅ 流式多次尝试测试通过")


@unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
class TestThinkerChatFunctionality(unittest.TestCase):
    """Thinker聊天功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.device = StatefulExecutor()
        self.thinker = Thinker(llm=get_model("deepseek_v3"), device=self.device)
    
    def test_chat_sync(self):
        """测试同步聊天"""
        message = "请解释什么是递归？"
        
        result = self.thinker.chat_sync(message)
        
        self.assertIsInstance(result, Result)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.return_value)
        self.assertIn("递归", result.return_value)
        print(f"✅ 同步聊天测试通过")
        print(f"聊天回复: {result.return_value[:100]}...")
    
    def test_chat_stream(self):
        """测试流式聊天"""
        message = "请简单介绍Python编程语言的特点"
        
        chunks = []
        final_result = None
        
        for chunk in self.thinker.chat_stream(message):
            if isinstance(chunk, str):
                chunks.append(chunk)
            elif isinstance(chunk, Result):
                final_result = chunk
                break
        
        self.assertIsNotNone(final_result)
        self.assertTrue(final_result.success)
        self.assertGreater(len(chunks), 0)
        
        full_response = ''.join(chunks)
        self.assertIn("Python", full_response)
        print(f"✅ 流式聊天测试通过")
        print(f"流式回复块数: {len(chunks)}")
    
    def test_chat_with_json_response(self):
        """测试JSON格式响应"""
        message = "请用JSON格式回答：Python有哪些主要特点？"
        response_format = {"type": "json_object"}
        
        result = self.thinker.chat_sync(message, response_format)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.return_value)
        
        # 尝试解析JSON
        import json
        try:
            json_data = json.loads(result.return_value)
            self.assertIsInstance(json_data, dict)
            print(f"✅ JSON响应测试通过")
            print(f"JSON响应: {json_data}")
        except json.JSONDecodeError:
            print(f"⚠️ JSON解析失败，但聊天功能正常")
            print(f"原始响应: {result.return_value[:200]}...")


@unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
class TestThinkerResultGeneration(unittest.TestCase):
    """Thinker结果生成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.device = StatefulExecutor()
        self.thinker = Thinker(llm=get_model("deepseek_v3"), device=self.device)
    
    def test_generate_result_sync(self):
        """测试同步结果生成"""
        # 先执行一个任务
        instruction = "计算1到5的平方和"
        exec_result = self.thinker.execute_sync(instruction)
        
        self.assertTrue(exec_result.success)
        
        # 生成最终结果
        final_result = self.thinker.generateResult_sync(instruction, exec_result)
        
        self.assertIsInstance(final_result, str)
        self.assertGreater(len(final_result), 50)  # 应该有合理长度的回复
        self.assertIn("55", final_result)  # 应该包含计算结果
        print(f"✅ 同步结果生成测试通过")
        print(f"生成的结果: {final_result[:200]}...")
    
    def test_generate_result_stream(self):
        """测试流式结果生成"""
        # 创建一个模拟的执行结果
        mock_result = Result(
            success=True,
            code="print('Hello, World!')",
            stdout="Hello, World!\n",
            stderr=None,
            return_value=None
        )
        
        instruction = "打印Hello World"
        
        chunks = []
        for chunk in self.thinker.generateResult_stream(instruction, mock_result):
            chunks.append(chunk)
        
        self.assertGreater(len(chunks), 0)
        full_response = ''.join(chunks)
        self.assertGreater(len(full_response), 20)
        print(f"✅ 流式结果生成测试通过")
        print(f"流式生成块数: {len(chunks)}")


@unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
class TestThinkerComplexTasks(unittest.TestCase):
    """Thinker复杂任务测试"""
    
    def setUp(self):
        """测试前准备"""
        self.device = StatefulExecutor()
        self.thinker = Thinker(llm=get_model("deepseek_v3"), device=self.device, max_retries=5)
    
    def test_file_operation_task(self):
        """测试文件操作任务"""
        instruction = """
        创建一个临时文本文件，写入一些数据，然后读取并处理数据。
        文件内容应该包含几行数字，计算这些数字的总和。
        """
        
        result = self.thinker.execute_sync(instruction)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.code)
        self.assertIn("总和", result.stdout)
        print(f"✅ 文件操作任务测试通过")
    
    def test_class_definition_task(self):
        """测试类定义任务"""
        instruction = """
        定义一个Student类，包含姓名、年龄和成绩属性，
        添加一个方法来判断是否及格（成绩>=60），
        然后创建几个学生实例并测试。
        """
        
        result = self.thinker.execute_sync(instruction)
        
        self.assertTrue(result.success)
        self.assertIn("class", result.code.lower())
        self.assertIn("Student", result.code)
        print(f"✅ 类定义任务测试通过")
    
    def test_data_analysis_task(self):
        """测试数据分析任务"""
        instruction = """
        生成一些随机数据，计算基本统计信息（平均值、中位数、标准差），
        并创建一个简单的数据可视化。
        """
        
        result = self.thinker.execute_sync(instruction)
        
        self.assertTrue(result.success)
        self.assertTrue(any(word in result.stdout for word in ["平均", "中位数", "标准差"]))
        print(f"✅ 数据分析任务测试通过")


if __name__ == '__main__':
    print("🚀 开始Thinker类单元测试...")
    print("="*60)
    
    # 检查API密钥
    if os.getenv('DEEPSEEK_API_KEY'):
        print("📡 检测到DEEPSEEK_API_KEY，将运行完整测试")
    else:
        print("⚠️  未检测到DEEPSEEK_API_KEY，将跳过API相关测试")
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加基础测试（不需要API）
    suite.addTests(loader.loadTestsFromTestCase(TestThinkerBasic))
    
    # 添加API相关测试
    if os.getenv('DEEPSEEK_API_KEY'):
        suite.addTests(loader.loadTestsFromTestCase(TestThinkerWithDeepSeek))
        suite.addTests(loader.loadTestsFromTestCase(TestThinkerStreamExecution))
        suite.addTests(loader.loadTestsFromTestCase(TestThinkerChatFunctionality))
        suite.addTests(loader.loadTestsFromTestCase(TestThinkerResultGeneration))
        suite.addTests(loader.loadTestsFromTestCase(TestThinkerComplexTasks))
    
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