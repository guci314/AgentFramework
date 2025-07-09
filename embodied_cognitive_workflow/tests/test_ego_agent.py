#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自我智能体(Ego Agent)单元测试

测试自我智能体的核心功能：
1. 状态分析能力
2. 决策制定逻辑
3. 指令生成功能
4. 错误处理机制
5. JSON响应处理
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from embodied_cognitive_workflow.ego_agent import EgoAgent
from agent_base import Result


class TestEgoAgentInitialization(unittest.TestCase):
    """测试自我智能体初始化"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
    
    def test_default_initialization(self):
        """测试默认初始化"""
        ego = EgoAgent(llm=self.mock_llm)
        
        self.assertEqual(ego.name, "自我智能体")
        self.assertIsNotNone(ego.llm)
        self.assertIn("自我智能体", ego.system_message)
        self.assertIn("理性思考", ego.system_message)
        self.assertIn("增量式规划", ego.system_message)
    
    def test_custom_system_message(self):
        """测试自定义系统消息"""
        custom_message = "自定义的自我智能体系统消息"
        ego = EgoAgent(llm=self.mock_llm, system_message=custom_message)
        
        self.assertEqual(ego.system_message, custom_message)
        self.assertEqual(ego.name, "自我智能体")


class TestStateAnalysis(unittest.TestCase):
    """测试状态分析功能"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.ego = EgoAgent(llm=self.mock_llm)
        
        # 模拟chat_sync方法
        self.ego.chat_sync = Mock()
    
    def test_analyze_current_state_basic(self):
        """测试基础状态分析"""
        context = "用户指令：创建计算器\n当前已完成基础框架搭建"
        expected_analysis = "已完成基础框架，需要实现具体功能"
        
        self.ego.chat_sync.return_value = Result(True, "", expected_analysis, None, "")
        
        result = self.ego.analyze_current_state(context)
        
        self.assertEqual(result, expected_analysis)
        
        # 验证调用参数
        call_args = self.ego.chat_sync.call_args[0][0]
        self.assertIn("请分析当前状态", call_args)
        self.assertIn(context, call_args)
        self.assertIn("当前处于什么状态", call_args)
        self.assertIn("已经完成了什么", call_args)
        self.assertIn("还需要做什么", call_args)
    
    def test_analyze_current_state_complex(self):
        """测试复杂状态分析"""
        context = """用户指令：创建完整的银行系统
第1轮结果：创建了账户类
第2轮结果：实现了存款功能
本我评估：还需要实现取款和转账功能"""
        
        detailed_analysis = """当前状态分析：
1. 已创建基础账户类结构
2. 完成了存款功能的实现
3. 尚需实现取款和转账功能
4. 可能需要添加余额查询和交易历史功能"""
        
        self.ego.chat_sync.return_value = Result(True, "", detailed_analysis, None, "")
        
        result = self.ego.analyze_current_state(context)
        
        self.assertEqual(result, detailed_analysis)
        self.assertIn("银行系统", self.ego.chat_sync.call_args[0][0])


class TestDecisionMaking(unittest.TestCase):
    """测试决策制定功能"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.ego = EgoAgent(llm=self.mock_llm)
        self.ego.chat_sync = Mock()
    
    def test_decide_continue_cycle(self):
        """测试决定继续循环"""
        state_analysis = "功能尚未完成，需要继续实现"
        
        json_response = '{"决策": "继续循环", "理由": "还有明确的下一步任务"}'
        self.ego.chat_sync.return_value = Result(True, "", json_response, None, "")
        
        decision = self.ego.decide_next_action(state_analysis)
        
        self.assertEqual(decision, "继续循环")
        
        # 验证response_format参数
        call_kwargs = self.ego.chat_sync.call_args[1]
        self.assertEqual(call_kwargs.get('response_format'), {"type": "json_object"})
    
    def test_decide_request_evaluation(self):
        """测试决定请求评估"""
        state_analysis = "所有功能似乎已经完成"
        
        json_response = '{"决策": "请求评估", "理由": "功能可能已完成，需要确认"}'
        self.ego.chat_sync.return_value = Result(True, "", json_response, None, "")
        
        decision = self.ego.decide_next_action(state_analysis)
        
        self.assertEqual(decision, "请求评估")
    
    def test_decide_judgment_failed(self):
        """测试决定判断失败"""
        state_analysis = "遇到无法解决的技术障碍"
        
        json_response = '{"决策": "判断失败", "理由": "技术限制无法克服"}'
        self.ego.chat_sync.return_value = Result(True, "", json_response, None, "")
        
        decision = self.ego.decide_next_action(state_analysis)
        
        self.assertEqual(decision, "判断失败")
    
    def test_decide_with_invalid_json(self):
        """测试无效JSON响应处理"""
        state_analysis = "状态不明确"
        
        # 返回无效的JSON
        self.ego.chat_sync.return_value = Result(True, "", "这不是JSON格式", None, "")
        
        decision = self.ego.decide_next_action(state_analysis)
        
        # 应该返回默认值
        self.assertEqual(decision, "请求评估")
    
    def test_decide_with_invalid_option(self):
        """测试无效选项处理"""
        state_analysis = "状态分析"
        
        # 返回无效的决策选项
        json_response = '{"决策": "无效选项", "理由": "测试"}'
        self.ego.chat_sync.return_value = Result(True, "", json_response, None, "")
        
        decision = self.ego.decide_next_action(state_analysis)
        
        # 应该返回默认值
        self.assertEqual(decision, "请求评估")


class TestEvaluationRequest(unittest.TestCase):
    """测试评估请求功能"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.ego = EgoAgent(llm=self.mock_llm)
        self.ego.chat_sync = Mock()
    
    def test_request_id_evaluation_basic(self):
        """测试基础评估请求"""
        current_state = "计算器基本功能已实现"
        expected_request = "请本我评估：计算器的基本功能是否满足要求"
        
        self.ego.chat_sync.return_value = Result(True, "", expected_request, None, "")
        
        result = self.ego.request_id_evaluation(current_state)
        
        self.assertEqual(result, expected_request)
        
        # 验证消息内容
        call_args = self.ego.chat_sync.call_args[0][0]
        self.assertIn("需要本我评估", call_args)
        self.assertIn(current_state, call_args)
        self.assertIn("观察当前状态", call_args)
        self.assertIn("判断目标是否达成", call_args)
    
    def test_request_id_evaluation_detailed(self):
        """测试详细评估请求"""
        current_state = """已完成：
- 用户注册功能
- 登录验证
- 基本权限管理
待确认是否满足安全要求"""
        
        detailed_request = """请本我进行全面评估：
1. 用户系统的完整性检查
2. 安全性是否达到标准
3. 是否还需要其他功能补充"""
        
        self.ego.chat_sync.return_value = Result(True, "", detailed_request, None, "")
        
        result = self.ego.request_id_evaluation(current_state)
        
        self.assertEqual(result, detailed_request)


class TestInstructionGeneration(unittest.TestCase):
    """测试指令生成功能"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.ego = EgoAgent(llm=self.mock_llm)
        self.ego.chat_sync = Mock()
    
    def test_generate_observation_instruction(self):
        """测试生成观察指令"""
        thinking_result = "需要了解当前代码的测试覆盖率"
        expected_instruction = "请运行测试并显示代码覆盖率报告"
        
        self.ego.chat_sync.return_value = Result(True, "", expected_instruction, None, "")
        
        result = self.ego.generate_observation_instruction(thinking_result)
        
        self.assertEqual(result, expected_instruction)
        
        # 验证提示内容
        call_args = self.ego.chat_sync.call_args[0][0]
        self.assertIn("生成一个观察指令", call_args)
        self.assertIn(thinking_result, call_args)
        self.assertIn("明确说明要观察什么", call_args)
        self.assertIn("为什么需要这个信息", call_args)
    
    def test_generate_execution_instruction(self):
        """测试生成执行指令"""
        perception_result = "发现缺少错误处理机制"
        expected_instruction = "在所有关键函数中添加try-except错误处理"
        
        self.ego.chat_sync.return_value = Result(True, "", expected_instruction, None, "")
        
        result = self.ego.generate_execution_instruction(perception_result)
        
        self.assertEqual(result, expected_instruction)
        
        # 验证提示内容
        call_args = self.ego.chat_sync.call_args[0][0]
        self.assertIn("生成一个执行指令", call_args)
        self.assertIn(perception_result, call_args)
        self.assertIn("明确说明要执行的操作", call_args)
        self.assertIn("为什么需要这个操作", call_args)
    
    def test_instruction_generation_with_context(self):
        """测试带上下文的指令生成"""
        # 测试观察指令
        complex_thinking = """经过分析，我们需要：
1. 检查数据库连接状态
2. 验证API响应时间
3. 确认缓存机制是否正常"""
        
        self.ego.chat_sync.return_value = Result(
            True, "", "执行性能测试并生成详细报告", None, ""
        )
        
        result = self.ego.generate_observation_instruction(complex_thinking)
        self.assertIsNotNone(result)
        
        # 测试执行指令
        complex_perception = """观察结果显示：
- 数据库查询速度慢
- 没有使用索引
- 需要优化查询语句"""
        
        self.ego.chat_sync.return_value = Result(
            True, "", "为主要查询添加数据库索引并优化SQL语句", None, ""
        )
        
        result = self.ego.generate_execution_instruction(complex_perception)
        self.assertIsNotNone(result)


class TestErrorHandling(unittest.TestCase):
    """测试错误处理功能"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.ego = EgoAgent(llm=self.mock_llm)
        self.ego.chat_sync = Mock()
    
    def test_handle_execution_error_basic(self):
        """测试基础错误处理"""
        error_info = "ImportError: No module named 'numpy'"
        original_instruction = "使用numpy进行数据分析"
        
        expected_solution = """错误分析：缺少numpy模块
处理方案：
1. 先安装numpy：pip install numpy
2. 然后重新执行数据分析任务"""
        
        self.ego.chat_sync.return_value = Result(True, "", expected_solution, None, "")
        
        result = self.ego.handle_execution_error(error_info, original_instruction)
        
        self.assertEqual(result, expected_solution)
        
        # 验证错误处理提示
        call_args = self.ego.chat_sync.call_args[0][0]
        self.assertIn("身体执行指令时出现错误", call_args)
        self.assertIn(error_info, call_args)
        self.assertIn(original_instruction, call_args)
        self.assertIn("错误是什么原因造成的", call_args)
    
    def test_handle_execution_error_complex(self):
        """测试复杂错误处理"""
        error_info = """Traceback (most recent call last):
  File "test.py", line 10, in <module>
    result = divide(10, 0)
  File "test.py", line 5, in divide
    return a / b
ZeroDivisionError: division by zero"""
        
        original_instruction = "实现除法功能并测试"
        
        detailed_solution = """错误分析：除零错误
原因：代码没有处理除数为0的情况

处理方案：
1. 修改divide函数，添加除零检查
2. 当除数为0时，返回错误信息或抛出自定义异常
3. 在调用处添加异常处理

建议的代码修改：
def divide(a, b):
    if b == 0:
        raise ValueError("除数不能为0")
    return a / b"""
        
        self.ego.chat_sync.return_value = Result(True, "", detailed_solution, None, "")
        
        result = self.ego.handle_execution_error(error_info, original_instruction)
        
        self.assertEqual(result, detailed_solution)
        self.assertIn("ZeroDivisionError", self.ego.chat_sync.call_args[0][0])
    
    def test_handle_execution_error_recovery_strategy(self):
        """测试错误恢复策略"""
        error_info = "ConnectionError: Unable to connect to database"
        original_instruction = "从数据库读取用户数据"
        
        recovery_strategy = """错误分析：数据库连接失败

可能原因：
1. 数据库服务未启动
2. 连接配置错误
3. 网络问题

处理方案：
1. 首先检查数据库服务状态
2. 验证连接配置（主机、端口、凭据）
3. 实现连接重试机制
4. 添加备用数据源（如本地缓存）

立即行动：
- 使用模拟数据继续开发
- 实现数据库连接的健康检查
- 添加详细的错误日志"""
        
        self.ego.chat_sync.return_value = Result(True, "", recovery_strategy, None, "")
        
        result = self.ego.handle_execution_error(error_info, original_instruction)
        
        self.assertEqual(result, recovery_strategy)


class TestEgoAgentIntegration(unittest.TestCase):
    """测试自我智能体集成场景"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.ego = EgoAgent(llm=self.mock_llm)
    
    def test_complete_decision_cycle(self):
        """测试完整的决策循环"""
        # 设置模拟响应
        self.ego.chat_sync = Mock()
        
        # 1. 分析状态
        context = "用户要求创建Web服务器"
        state_analysis = "需要创建基础的HTTP服务器"
        self.ego.chat_sync.return_value = Result(True, "", state_analysis, None, "")
        
        analysis_result = self.ego.analyze_current_state(context)
        self.assertEqual(analysis_result, state_analysis)
        
        # 2. 做出决策
        decision_json = '{"决策": "继续循环", "理由": "需要实现服务器功能"}'
        self.ego.chat_sync.return_value = Result(True, "", decision_json, None, "")
        
        decision = self.ego.decide_next_action(analysis_result)
        self.assertEqual(decision, "继续循环")
        
        # 3. 生成执行指令
        execution_instruction = "创建Flask服务器并实现基础路由"
        self.ego.chat_sync.return_value = Result(True, "", execution_instruction, None, "")
        
        instruction = self.ego.generate_execution_instruction("需要Web框架")
        self.assertEqual(instruction, execution_instruction)
    
    def test_error_recovery_cycle(self):
        """测试错误恢复循环"""
        self.ego.chat_sync = Mock()
        
        # 1. 初始执行失败
        error = "ModuleNotFoundError: No module named 'flask'"
        instruction = "使用Flask创建服务器"
        
        # 2. 处理错误
        error_solution = "先安装Flask：pip install flask"
        self.ego.chat_sync.return_value = Result(True, "", error_solution, None, "")
        
        solution = self.ego.handle_execution_error(error, instruction)
        self.assertIn("pip install flask", solution)
        
        # 3. 生成新的执行指令
        new_instruction = "安装Flask后重新创建服务器"
        self.ego.chat_sync.return_value = Result(True, "", new_instruction, None, "")
        
        new_inst = self.ego.generate_execution_instruction("Flask已安装")
        self.assertEqual(new_inst, new_instruction)
    
    def test_evaluation_request_cycle(self):
        """测试评估请求循环"""
        self.ego.chat_sync = Mock()
        
        # 1. 分析完成状态
        final_state = "所有功能已实现并测试通过"
        self.ego.chat_sync.return_value = Result(True, "", final_state, None, "")
        
        state = self.ego.analyze_current_state("功能开发完成")
        
        # 2. 决定请求评估
        eval_decision = '{"决策": "请求评估", "理由": "功能似乎已完成"}'
        self.ego.chat_sync.return_value = Result(True, "", eval_decision, None, "")
        
        decision = self.ego.decide_next_action(state)
        self.assertEqual(decision, "请求评估")
        
        # 3. 生成评估请求
        eval_request = "请本我评估所有功能是否满足要求"
        self.ego.chat_sync.return_value = Result(True, "", eval_request, None, "")
        
        request = self.ego.request_id_evaluation(state)
        self.assertEqual(request, eval_request)


class TestEgoAgentEdgeCases(unittest.TestCase):
    """测试自我智能体边缘情况"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.ego = EgoAgent(llm=self.mock_llm)
        self.ego.chat_sync = Mock()
    
    def test_empty_context_handling(self):
        """测试空上下文处理"""
        # 空字符串上下文
        self.ego.chat_sync.return_value = Result(True, "", "无有效上下文", None, "")
        result = self.ego.analyze_current_state("")
        self.assertIsNotNone(result)
        
        # None上下文处理
        self.ego.chat_sync.return_value = Result(True, "", "缺少上下文信息", None, "")
        result = self.ego.analyze_current_state(None)
        self.assertIsNotNone(result)
    
    def test_malformed_json_responses(self):
        """测试格式错误的JSON响应"""
        test_cases = [
            '{"决策": "继续循环"',  # 缺少闭合
            '{"决策": 继续循环}',    # 值没有引号
            '决策: 继续循环',        # 不是JSON格式
            '{"wrong_key": "继续循环"}',  # 错误的键
            ''                      # 空响应
        ]
        
        for malformed_json in test_cases:
            self.ego.chat_sync.return_value = Result(True, "", malformed_json, None, "")
            decision = self.ego.decide_next_action("测试")
            # 应该返回默认值而不是崩溃
            self.assertEqual(decision, "请求评估")
    
    def test_long_context_handling(self):
        """测试长上下文处理"""
        # 创建一个非常长的上下文
        long_context = "历史记录：\n" + "\n".join([f"第{i}轮：执行了操作{i}" for i in range(100)])
        
        self.ego.chat_sync.return_value = Result(True, "", "处理长上下文", None, "")
        
        result = self.ego.analyze_current_state(long_context)
        self.assertIsNotNone(result)
        
        # 确保长上下文被传递
        call_args = self.ego.chat_sync.call_args[0][0]
        self.assertIn("第99轮", call_args)
    
    def test_special_characters_handling(self):
        """测试特殊字符处理"""
        special_contexts = [
            "包含'单引号'的内容",
            '包含"双引号"的内容',
            "包含\n换行符\n的内容",
            "包含\t制表符\t的内容",
            "包含\\反斜杠\\的内容",
            "包含{JSON}字符的内容"
        ]
        
        for context in special_contexts:
            self.ego.chat_sync.return_value = Result(
                True, "", f"分析了：{context}", None, ""
            )
            result = self.ego.analyze_current_state(context)
            self.assertIn(context.replace('\n', '').replace('\t', ''), result.replace('\n', '').replace('\t', ''))
    
    def test_concurrent_state_analysis(self):
        """测试并发状态分析"""
        # 模拟多个状态需要同时分析
        states = [
            "前端开发进度",
            "后端API状态",
            "数据库迁移情况"
        ]
        
        for state in states:
            self.ego.chat_sync.return_value = Result(
                True, "", f"{state}：正在进行", None, ""
            )
            result = self.ego.analyze_current_state(state)
            self.assertIn("正在进行", result)


if __name__ == '__main__':
    print("🚀 开始自我智能体(Ego Agent)单元测试...")
    print("="*60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestEgoAgentInitialization,
        TestStateAnalysis,
        TestDecisionMaking,
        TestEvaluationRequest,
        TestInstructionGeneration,
        TestErrorHandling,
        TestEgoAgentIntegration,
        TestEgoAgentEdgeCases
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试总结
    print("\n" + "="*60)
    if result.wasSuccessful():
        print("🎉 所有测试通过！")
    else:
        print(f"❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
    
    print(f"📊 测试统计:")
    print(f"   - 运行测试: {result.testsRun}")
    print(f"   - 成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   - 失败: {len(result.failures)}")
    print(f"   - 错误: {len(result.errors)}")
    print("="*60)