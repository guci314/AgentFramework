#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluator类单元测试 - 任务评估器测试
"""

import unittest
import os
import sys
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Evaluator, Thinker, StatefulExecutor
from llm_lazy import get_model
from agent_base import Result
from mda.prompts import default_evaluate_message


class TestEvaluatorBasic(unittest.TestCase):
    """Evaluator基础功能测试（不需要API密钥）"""
    
    def setUp(self):
        """测试前准备"""
        # 创建基础组件但不初始化需要API的部分
        self.device = StatefulExecutor()
    
    def test_evaluator_initialization(self):
        """测试Evaluator初始化"""
        if not os.getenv('DEEPSEEK_API_KEY'):
            self.skipTest("需要DEEPSEEK_API_KEY环境变量")
        
        evaluator = Evaluator(llm=get_model("deepseek_v3"), systemMessage=default_evaluate_message)
        
        # 验证初始化属性
        self.assertIsNotNone(evaluator.llm)
        self.assertIsNotNone(evaluator.system_message)
        self.assertIsInstance(evaluator.knowledges, list)
        self.assertEqual(len(evaluator.knowledges), 0)
    
    def test_knowledge_loading(self):
        """测试知识加载功能"""
        if not os.getenv('DEEPSEEK_API_KEY'):
            self.skipTest("需要DEEPSEEK_API_KEY环境变量")
        
        evaluator = Evaluator(llm=get_model("deepseek_v3"), systemMessage=default_evaluate_message)
        
        # 加载知识
        knowledge1 = "Python是一种高级编程语言"
        knowledge2 = "列表是Python中的可变数据类型"
        
        evaluator.loadKnowledge(knowledge1)
        evaluator.loadKnowledge(knowledge2)
        
        self.assertEqual(len(evaluator.knowledges), 2)
        self.assertIn(knowledge1, evaluator.knowledges)
        self.assertIn(knowledge2, evaluator.knowledges)
    
    def test_simple_error_detection(self):
        """测试简单错误检测（兜底逻辑）"""
        if not os.getenv('DEEPSEEK_API_KEY'):
            self.skipTest("需要DEEPSEEK_API_KEY环境变量")
        
        evaluator = Evaluator(llm=get_model("deepseek_v3"), systemMessage=default_evaluate_message)
        
        # 测试明显的错误结果
        error_result = Result(
            success=False,
            code="undefined_variable",
            stdout="",
            stderr="NameError: name 'undefined_variable' is not defined",
            return_value=None
        )
        
        is_complete, reason = evaluator.evaluate("测试任务", error_result)
        
        self.assertFalse(is_complete)
        self.assertIn("出错", reason)


@unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
class TestEvaluatorWithDeepSeek(unittest.TestCase):
    """Evaluator与DeepSeek集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.device = StatefulExecutor()
        self.thinker = Thinker(llm=get_model("deepseek_v3"), device=self.device)
        self.evaluator = Evaluator(llm=get_model("deepseek_v3"), systemMessage=default_evaluate_message, thinker=self.thinker)
    
    def test_successful_task_evaluation(self):
        """测试成功任务的评估"""
        # 创建一个成功的执行结果
        success_result = Result(
            success=True,
            code="""
x = 10
y = 20
result = x + y
print(f"计算结果: {result}")
assert result == 30, "计算错误"
print("任务完成")
""",
            stdout="计算结果: 30\n任务完成\n",
            stderr=None,
            return_value=None
        )
        
        instruction = "计算10+20的结果"
        is_complete, reason = self.evaluator.evaluate(instruction, success_result)
        
        print(f"评估结果: {is_complete}")
        print(f"评估原因: {reason}")
        
        # 由于使用真实LLM，结果可能因模型而异，我们主要验证函数正常运行
        self.assertIsInstance(is_complete, bool)
        self.assertIsInstance(reason, str)
        self.assertGreater(len(reason), 10)
        print(f"✅ 成功任务评估测试通过")
    
    def test_failed_task_evaluation(self):
        """测试失败任务的评估"""
        # 创建一个失败的执行结果
        failed_result = Result(
            success=False,
            code="result = x + y",
            stdout="",
            stderr="NameError: name 'x' is not defined",
            return_value=None
        )
        
        instruction = "计算x+y的结果"
        is_complete, reason = self.evaluator.evaluate(instruction, failed_result)
        
        print(f"失败任务评估结果: {is_complete}")
        print(f"失败任务评估原因: {reason}")
        
        # 失败的任务通常应该被评估为未完成
        self.assertIsInstance(is_complete, bool)
        self.assertIsInstance(reason, str)
        print(f"✅ 失败任务评估测试通过")
    
    def test_hello_world_evaluation(self):
        """测试Hello World任务评估"""
        # 创建Hello World执行结果
        hello_result = Result(
            success=True,
            code='print("Hello, World!")',
            stdout="Hello, World!\n",
            stderr=None,
            return_value=None
        )
        
        instruction = "编写一个Hello World程序"
        is_complete, reason = self.evaluator.evaluate(instruction, hello_result)
        
        print(f"Hello World评估结果: {is_complete}")
        print(f"Hello World评估原因: {reason}")
        
        self.assertIsInstance(is_complete, bool)
        self.assertIsInstance(reason, str)
        print(f"✅ Hello World评估测试通过")
    
    def test_calculation_task_evaluation(self):
        """测试计算任务评估"""
        # 创建计算任务结果
        calc_result = Result(
            success=True,
            code="""
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
average = total / len(numbers)
print(f"总和: {total}")
print(f"平均值: {average}")
""",
            stdout="总和: 15\n平均值: 3.0\n",
            stderr=None,
            return_value=None
        )
        
        instruction = "计算列表[1,2,3,4,5]的总和和平均值"
        is_complete, reason = self.evaluator.evaluate(instruction, calc_result)
        
        print(f"计算任务评估结果: {is_complete}")
        print(f"计算任务评估原因: {reason}")
        
        self.assertIsInstance(is_complete, bool)
        self.assertIsInstance(reason, str)
        print(f"✅ 计算任务评估测试通过")


@unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
class TestEvaluatorCustomCriteria(unittest.TestCase):
    """Evaluator自定义评估标准测试"""
    
    def setUp(self):
        """测试前准备"""
        self.device = StatefulExecutor()
        self.thinker = Thinker(llm=get_model("deepseek_v3"), device=self.device)
    
    def test_custom_evaluation_message(self):
        """测试自定义评估消息"""
        custom_message = '''
        请判断是否完成了任务。请返回json格式的结果。
        json有两个字段，taskIsComplete，值为true或false，reason字段，字符串类型，判断的理由。

        # 判断规则：
        1. 必须包含中文输出
        2. 必须计算正确的数学结果
        3. 输出格式要清晰
        
        # 知识：
        {knowledges}

        # 任务：
        {instruction}

        # 代码执行结果：
        {result}
        '''
        
        evaluator = Evaluator(llm=get_model("deepseek_v3"), systemMessage=custom_message, thinker=self.thinker)
        
        # 测试符合条件的结果
        good_result = Result(
            success=True,
            code='print("计算结果：", 2 + 3)',
            stdout="计算结果： 5\n",
            stderr=None,
            return_value=None
        )
        
        instruction = "计算2+3并用中文输出结果"
        is_complete, reason = evaluator.evaluate(instruction, good_result)
        
        print(f"自定义评估结果: {is_complete}")
        print(f"自定义评估原因: {reason}")
        
        self.assertIsInstance(is_complete, bool)
        self.assertIsInstance(reason, str)
        print(f"✅ 自定义评估消息测试通过")
    
    def test_strict_evaluation_criteria(self):
        """测试严格评估标准"""
        strict_message = '''
        请判断是否完成了任务。请返回json格式的结果。
        json有两个字段，taskIsComplete，值为true或false，reason字段，字符串类型，判断的理由。

        # 严格判断规则：
        1. 代码必须无语法错误
        2. 输出必须包含"任务完成"字样
        3. 必须有断言验证结果正确性
        
        # 任务：{instruction}
        # 代码执行结果：{result}
        '''
        
        evaluator = Evaluator(llm=get_model("deepseek_v3"), systemMessage=strict_message, thinker=self.thinker)
        
        # 测试不完全符合严格标准的结果
        partial_result = Result(
            success=True,
            code='print("Hello")',
            stdout="Hello\n",
            stderr=None,
            return_value=None
        )
        
        instruction = "打印Hello并验证结果"
        is_complete, reason = evaluator.evaluate(instruction, partial_result)
        
        print(f"严格评估结果: {is_complete}")
        print(f"严格评估原因: {reason}")
        
        self.assertIsInstance(is_complete, bool)
        self.assertIsInstance(reason, str)
        print(f"✅ 严格评估标准测试通过")


@unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
class TestEvaluatorWithKnowledge(unittest.TestCase):
    """Evaluator知识加载测试"""
    
    def setUp(self):
        """测试前准备"""
        self.device = StatefulExecutor()
        self.thinker = Thinker(llm=get_model("deepseek_v3"), device=self.device)
        self.evaluator = Evaluator(llm=get_model("deepseek_v3"), systemMessage=default_evaluate_message, thinker=self.thinker)
    
    def test_evaluation_with_domain_knowledge(self):
        """测试带领域知识的评估"""
        # 加载数学相关知识
        math_knowledge = """
        数学计算规则：
        1. 平方根计算：√16 = 4
        2. 阶乘计算：5! = 5×4×3×2×1 = 120
        3. 斐波那契数列：1,1,2,3,5,8,13,21...
        """
        
        self.evaluator.loadKnowledge(math_knowledge)
        
        # 测试斐波那契数列计算
        fib_result = Result(
            success=True,
            code="""
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = [fibonacci(i) for i in range(8)]
print(f"斐波那契数列前8项: {result}")
""",
            stdout="斐波那契数列前8项: [0, 1, 1, 2, 3, 5, 8, 13]\n",
            stderr=None,
            return_value=None
        )
        
        instruction = "计算斐波那契数列的前8项"
        is_complete, reason = self.evaluator.evaluate(instruction, fib_result)
        
        print(f"领域知识评估结果: {is_complete}")
        print(f"领域知识评估原因: {reason}")
        
        self.assertIsInstance(is_complete, bool)
        self.assertIsInstance(reason, str)
        print(f"✅ 领域知识评估测试通过")
    
    def test_evaluation_with_programming_knowledge(self):
        """测试带编程知识的评估"""
        # 加载编程最佳实践知识
        programming_knowledge = """
        Python编程最佳实践：
        1. 函数应该有清晰的文档字符串
        2. 变量名应该具有描述性
        3. 应该包含适当的错误处理
        4. 代码应该有注释说明
        """
        
        self.evaluator.loadKnowledge(programming_knowledge)
        
        # 测试遵循最佳实践的代码
        good_code_result = Result(
            success=True,
            code='''
def calculate_average(numbers):
    """
    计算数字列表的平均值
    
    Args:
        numbers: 数字列表
    
    Returns:
        float: 平均值
    """
    if not numbers:
        raise ValueError("列表不能为空")
    
    total_sum = sum(numbers)  # 计算总和
    count = len(numbers)      # 获取数量
    average = total_sum / count  # 计算平均值
    
    return average

# 测试函数
test_numbers = [10, 20, 30, 40, 50]
result = calculate_average(test_numbers)
print(f"平均值: {result}")
''',
            stdout="平均值: 30.0\n",
            stderr=None,
            return_value=None
        )
        
        instruction = "编写一个计算平均值的函数，要求有文档字符串和注释"
        is_complete, reason = self.evaluator.evaluate(instruction, good_code_result)
        
        print(f"编程知识评估结果: {is_complete}")
        print(f"编程知识评估原因: {reason}")
        
        self.assertIsInstance(is_complete, bool)
        self.assertIsInstance(reason, str)
        print(f"✅ 编程知识评估测试通过")


@unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
class TestEvaluatorErrorHandling(unittest.TestCase):
    """Evaluator错误处理测试"""
    
    def setUp(self):
        """测试前准备"""
        self.device = StatefulExecutor()
        self.thinker = Thinker(llm=get_model("deepseek_v3"), device=self.device)
    
    def test_evaluation_with_malformed_json(self):
        """测试处理格式错误的JSON响应"""
        # 使用可能产生格式错误JSON的评估消息
        problematic_message = '''
        评估任务是否完成。返回JSON，但可能格式不正确。
        
        任务：{instruction}
        结果：{result}
        '''
        
        evaluator = Evaluator(llm=get_model("deepseek_v3"), systemMessage=problematic_message, thinker=self.thinker)
        
        test_result = Result(
            success=True,
            code='print("test")',
            stdout="test\n",
            stderr=None,
            return_value=None
        )
        
        instruction = "打印test"
        
        # 即使JSON格式有问题，函数也应该能处理并返回合理结果
        is_complete, reason = evaluator.evaluate(instruction, test_result)
        
        print(f"JSON错误处理评估结果: {is_complete}")
        print(f"JSON错误处理评估原因: {reason}")
        
        self.assertIsInstance(is_complete, bool)
        self.assertIsInstance(reason, str)
        self.assertGreater(len(reason), 5)
        print(f"✅ JSON错误处理测试通过")
    
    def test_evaluation_with_empty_result(self):
        """测试评估空结果"""
        evaluator = Evaluator(llm=get_model("deepseek_v3"), systemMessage=default_evaluate_message, thinker=self.thinker)
        
        empty_result = Result(
            success=True,
            code="",
            stdout="",
            stderr=None,
            return_value=None
        )
        
        instruction = "执行空任务"
        is_complete, reason = evaluator.evaluate(instruction, empty_result)
        
        print(f"空结果评估结果: {is_complete}")
        print(f"空结果评估原因: {reason}")
        
        self.assertIsInstance(is_complete, bool)
        self.assertIsInstance(reason, str)
        print(f"✅ 空结果评估测试通过")
    
    def test_evaluation_retry_mechanism(self):
        """测试评估重试机制"""
        evaluator = Evaluator(llm=get_model("deepseek_v3"), systemMessage=default_evaluate_message, thinker=self.thinker)
        
        # 创建一个可能导致解析问题的复杂结果
        complex_result = Result(
            success=True,
            code='''
import json
data = {"key": "value with special chars: \\n\\t\\""}
print(json.dumps(data))
''',
            stdout='{"key": "value with special chars: \\n\\t\\""}\n',
            stderr=None,
            return_value=None
        )
        
        instruction = "处理包含特殊字符的JSON数据"
        is_complete, reason = evaluator.evaluate(instruction, complex_result)
        
        print(f"重试机制评估结果: {is_complete}")
        print(f"重试机制评估原因: {reason}")
        
        # 验证即使是复杂情况也能得到合理结果
        self.assertIsInstance(is_complete, bool)
        self.assertIsInstance(reason, str)
        print(f"✅ 重试机制测试通过")


if __name__ == '__main__':
    print("🚀 开始Evaluator类单元测试...")
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
    suite.addTests(loader.loadTestsFromTestCase(TestEvaluatorBasic))
    
    # 添加API相关测试
    if os.getenv('DEEPSEEK_API_KEY'):
        suite.addTests(loader.loadTestsFromTestCase(TestEvaluatorWithDeepSeek))
        suite.addTests(loader.loadTestsFromTestCase(TestEvaluatorCustomCriteria))
        suite.addTests(loader.loadTestsFromTestCase(TestEvaluatorWithKnowledge))
        suite.addTests(loader.loadTestsFromTestCase(TestEvaluatorErrorHandling))
    
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