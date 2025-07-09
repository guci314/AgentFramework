#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本我智能体(Id Agent)单元测试

测试本我智能体的核心功能：
1. 价值系统初始化
2. 评估指令生成
3. 目标达成评估
4. 价值标准管理
5. 任务规格维护
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from embodied_cognitive_workflow.id_agent import IdAgent
from agent_base import Result


class TestIdAgentInitialization(unittest.TestCase):
    """测试本我智能体初始化"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
    
    def test_default_initialization(self):
        """测试默认初始化"""
        id_agent = IdAgent(llm=self.mock_llm)
        
        self.assertEqual(id_agent.name, "本我智能体")
        self.assertIsNotNone(id_agent.llm)
        self.assertIn("本我智能体", id_agent.system_message)
        self.assertIn("价值驱动", id_agent.system_message)
        self.assertIn("实用导向", id_agent.system_message)
        self.assertEqual(id_agent.value_standard, "")
        self.assertEqual(id_agent.goal_description, "")
        self.assertEqual(id_agent.task_specification, "")
    
    def test_custom_system_message(self):
        """测试自定义系统消息"""
        custom_message = "自定义的本我智能体系统消息"
        id_agent = IdAgent(llm=self.mock_llm, system_message=custom_message)
        
        self.assertEqual(id_agent.system_message, custom_message)
        self.assertEqual(id_agent.name, "本我智能体")


class TestValueSystemInitialization(unittest.TestCase):
    """测试价值系统初始化"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.id_agent = IdAgent(llm=self.mock_llm)
        self.id_agent.chat_sync = Mock()
    
    def test_initialize_value_system_basic(self):
        """测试基础价值系统初始化"""
        instruction = "创建一个简单的计算器"
        
        expected_response = """目标描述：创建具有基本四则运算功能的计算器
价值标准：
1. 能正确执行加减乘除运算
2. 有友好的用户界面
3. 包含错误处理机制
验证方法：通过测试用例验证计算结果的准确性"""
        
        self.id_agent.chat_sync.return_value = Result(True, "", expected_response, None, "")
        
        result = self.id_agent.initialize_value_system(instruction)
        
        self.assertEqual(result, expected_response)
        self.assertEqual(self.id_agent.task_specification, expected_response)
        self.assertEqual(self.id_agent.goal_description, "创建具有基本四则运算功能的计算器")
        self.assertIn("能正确执行加减乘除运算", self.id_agent.value_standard)
        
        # 验证调用参数
        call_args = self.id_agent.chat_sync.call_args[0][0]
        self.assertIn(instruction, call_args)
        self.assertIn("核心需求", call_args)
        self.assertIn("成功标准", call_args)
    
    def test_initialize_value_system_complex(self):
        """测试复杂价值系统初始化"""
        instruction = "开发一个完整的电子商务平台，包括用户管理、商品展示、购物车和支付功能"
        
        complex_response = """目标描述：开发功能完整的电子商务平台
价值标准：
1. 用户系统：注册、登录、个人信息管理功能正常
2. 商品系统：商品展示、搜索、分类浏览功能完整
3. 购物功能：购物车添加、删除、修改数量功能可用
4. 支付流程：能完成基本的支付流程（可以是模拟）
5. 系统稳定：基本功能运行无明显错误
验证方法：
1. 用户流程测试：从注册到下单的完整流程
2. 功能单元测试：各模块独立功能验证
3. 集成测试：模块间交互正常"""
        
        self.id_agent.chat_sync.return_value = Result(True, "", complex_response, None, "")
        
        result = self.id_agent.initialize_value_system(instruction)
        
        self.assertEqual(self.id_agent.task_specification, complex_response)
        self.assertIn("电子商务平台", self.id_agent.goal_description)
        self.assertIn("用户系统", self.id_agent.value_standard)
    
    def test_initialize_value_system_parsing(self):
        """测试价值系统解析"""
        instruction = "实现数据分析工具"
        
        # 测试不同格式的响应
        responses = [
            # 标准格式
            """目标描述：数据分析工具
价值标准：支持CSV导入和统计分析
验证方法：测试数据处理准确性""",
            
            # 缺少某些部分
            """目标描述：数据分析工具
价值标准：基本统计功能""",
            
            # 格式变化
            """目标描述:数据分析工具
价值标准:
- 数据导入功能
- 统计分析功能
验证方法:功能测试"""
        ]
        
        for response in responses:
            self.id_agent.chat_sync.return_value = Result(True, "", response, None, "")
            result = self.id_agent.initialize_value_system(instruction)
            
            # 应该能够解析出目标描述
            self.assertIsNotNone(self.id_agent.goal_description)
            self.assertIn("数据分析工具", self.id_agent.goal_description)


class TestEvaluationInstructionGeneration(unittest.TestCase):
    """测试评估指令生成"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.id_agent = IdAgent(llm=self.mock_llm)
        self.id_agent.chat_sync = Mock()
        
        # 设置预定义的目标和标准
        self.id_agent.goal_description = "创建Web API服务"
        self.id_agent.value_standard = "支持GET和POST请求，返回JSON格式数据"
    
    def test_generate_evaluation_instruction_simple(self):
        """测试生成简单评估指令"""
        evaluation_request = "请检查API是否能正常工作"
        expected_instruction = "运行API服务并测试GET /api/test端点是否返回有效JSON"
        
        self.id_agent.chat_sync.return_value = Result(True, "", expected_instruction, None, "")
        
        result = self.id_agent.generate_evaluation_instruction(evaluation_request)
        
        self.assertEqual(result, expected_instruction)
        
        # 验证调用参数
        call_args = self.id_agent.chat_sync.call_args[0][0]
        self.assertIn(evaluation_request, call_args)
        self.assertIn(self.id_agent.goal_description, call_args)
        self.assertIn(self.id_agent.value_standard, call_args)
        self.assertIn("1-2个简单的观察指令", call_args)
    
    def test_generate_evaluation_instruction_focused(self):
        """测试生成聚焦的评估指令"""
        evaluation_request = "需要验证所有功能是否完整实现"
        
        # 本我应该生成简洁的指令
        focused_instruction = """1. 测试API的基本连通性：curl http://localhost:5000/health
2. 验证核心功能：发送测试请求到主要端点"""
        
        self.id_agent.chat_sync.return_value = Result(True, "", focused_instruction, None, "")
        
        result = self.id_agent.generate_evaluation_instruction(evaluation_request)
        
        self.assertEqual(result, focused_instruction)
        # 验证生成的是简洁指令
        self.assertLess(len(result.split('\n')), 5)  # 不超过5行
    
    def test_generate_evaluation_instruction_practical(self):
        """测试生成实用的评估指令"""
        self.id_agent.goal_description = "实现用户登录功能"
        self.id_agent.value_standard = "用户能够成功登录并获取认证令牌"
        
        evaluation_request = "检查登录功能是否可用"
        
        practical_instruction = "使用测试账号(test@example.com/password123)尝试登录，检查是否返回token"
        
        self.id_agent.chat_sync.return_value = Result(True, "", practical_instruction, None, "")
        
        result = self.id_agent.generate_evaluation_instruction(evaluation_request)
        
        # 验证指令的实用性
        self.assertIn("测试账号", result)
        self.assertIn("token", result)
        
        # 确认避免了复杂的测试要求
        call_args = self.id_agent.chat_sync.call_args[0][0]
        self.assertIn("避免复杂的测试要求", call_args)
        self.assertIn("实用导向", call_args)


class TestGoalAchievementEvaluation(unittest.TestCase):
    """测试目标达成评估"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.id_agent = IdAgent(llm=self.mock_llm)
        self.id_agent.chat_sync = Mock()
        
        # 设置目标和标准
        self.id_agent.goal_description = "创建待办事项应用"
        self.id_agent.value_standard = "能够添加、删除、标记完成任务"
    
    def test_evaluate_goal_achieved(self):
        """测试评估目标达成"""
        observation_result = """测试结果：
1. 成功添加了新任务"买菜"
2. 成功删除了任务"开会"  
3. 成功将任务"写报告"标记为完成
所有核心功能正常工作"""
        
        expected_json = '{"目标是否达成": true, "原因": "核心功能都已实现且正常工作"}'
        
        self.id_agent.chat_sync.return_value = Result(True, "", expected_json, None, "")
        
        result = self.id_agent.evaluate_goal_achievement(observation_result)
        
        # 验证返回的是有效JSON
        parsed_result = json.loads(result)
        self.assertTrue(parsed_result["目标是否达成"])
        self.assertEqual(parsed_result["原因"], "核心功能都已实现且正常工作")
        
        # 验证使用了response_format
        call_kwargs = self.id_agent.chat_sync.call_args[1]
        self.assertEqual(call_kwargs.get('response_format'), {"type": "json_object"})
    
    def test_evaluate_goal_not_achieved(self):
        """测试评估目标未达成"""
        observation_result = """测试结果：
1. 添加任务功能正常
2. 删除功能报错：TypeError: Cannot read property 'id' of undefined
3. 标记完成功能未实现"""
        
        expected_json = '{"目标是否达成": false, "原因": "删除功能有错误，标记完成功能未实现"}'
        
        self.id_agent.chat_sync.return_value = Result(True, "", expected_json, None, "")
        
        result = self.id_agent.evaluate_goal_achievement(observation_result)
        
        parsed_result = json.loads(result)
        self.assertFalse(parsed_result["目标是否达成"])
        self.assertIn("删除功能有错误", parsed_result["原因"])
    
    def test_evaluate_with_lenient_criteria(self):
        """测试宽松的评估标准"""
        self.id_agent.value_standard = "基本的任务管理功能"
        
        observation_result = """测试结果：
1. 可以添加任务
2. 可以查看任务列表
3. 删除功能有小bug但基本可用
4. 没有实现优先级功能"""
        
        # 本我应该宽松评估，核心功能可用即可
        lenient_json = '{"目标是否达成": true, "原因": "基本任务管理功能已满足，虽有小问题但不影响核心使用"}'
        
        self.id_agent.chat_sync.return_value = Result(True, "", lenient_json, None, "")
        
        result = self.id_agent.evaluate_goal_achievement(observation_result)
        
        parsed_result = json.loads(result)
        self.assertTrue(parsed_result["目标是否达成"])
        self.assertIn("基本", parsed_result["原因"])
    
    def test_evaluate_json_error_handling(self):
        """测试JSON错误处理"""
        observation_result = "功能测试完成"
        
        # 模拟LLM返回无效JSON
        self.id_agent.chat_sync.return_value = Result(True, "", "这不是JSON格式", None, "")
        
        result = self.id_agent.evaluate_goal_achievement(observation_result)
        
        # 应该返回默认的错误JSON
        parsed_result = json.loads(result)
        self.assertFalse(parsed_result["目标是否达成"])
        self.assertIn("JSON格式错误", parsed_result["原因"])


class TestValueStandardManagement(unittest.TestCase):
    """测试价值标准管理"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.id_agent = IdAgent(llm=self.mock_llm)
        self.id_agent.chat_sync = Mock()
        
        # 初始化价值系统
        self.id_agent.goal_description = "创建聊天机器人"
        self.id_agent.value_standard = "能够理解用户输入并给出合理回复"
        self.id_agent.task_specification = "完整的任务规格"
    
    def test_get_current_goal(self):
        """测试获取当前目标"""
        goal = self.id_agent.get_current_goal()
        self.assertEqual(goal, "创建聊天机器人")
    
    def test_get_value_standard(self):
        """测试获取价值标准"""
        standard = self.id_agent.get_value_standard()
        self.assertEqual(standard, "能够理解用户输入并给出合理回复")
    
    def test_get_task_specification(self):
        """测试获取任务规格"""
        spec = self.id_agent.get_task_specification()
        self.assertEqual(spec, "完整的任务规格")
    
    def test_reset_goal(self):
        """测试重置目标"""
        new_instruction = "改为创建数据可视化工具"
        
        new_response = """目标描述：创建数据可视化工具
价值标准：支持柱状图、折线图、饼图的绘制
验证方法：使用示例数据测试图表生成"""
        
        self.id_agent.chat_sync.return_value = Result(True, "", new_response, None, "")
        
        result = self.id_agent.reset_goal(new_instruction)
        
        self.assertEqual(result, new_response)
        self.assertEqual(self.id_agent.goal_description, "创建数据可视化工具")
        self.assertIn("柱状图", self.id_agent.value_standard)
    
    def test_adjust_value_standard(self):
        """测试调整价值标准"""
        adjustment = "发现用户更需要支持语音输入功能"
        
        adjusted_standard = """调整后的价值标准：
1. 能够理解文本用户输入并给出合理回复
2. 支持基本的语音输入转文本功能
3. 保持原有的对话质量"""
        
        self.id_agent.chat_sync.return_value = Result(True, "", adjusted_standard, None, "")
        
        result = self.id_agent.adjust_value_standard(adjustment)
        
        self.assertEqual(result, adjusted_standard)
        self.assertEqual(self.id_agent.value_standard, adjusted_standard)
        
        # 验证调整逻辑
        call_args = self.id_agent.chat_sync.call_args[0][0]
        self.assertIn(adjustment, call_args)
        self.assertIn("仍然符合原始目标", call_args)
        self.assertIn("更加现实可行", call_args)


class TestIdAgentIntegration(unittest.TestCase):
    """测试本我智能体集成场景"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.id_agent = IdAgent(llm=self.mock_llm)
        self.id_agent.chat_sync = Mock()
    
    def test_complete_evaluation_cycle(self):
        """测试完整的评估循环"""
        # 1. 初始化价值系统
        instruction = "创建文件管理器"
        init_response = """目标描述：创建基础文件管理器
价值标准：支持文件的创建、读取、删除操作
验证方法：测试文件操作功能"""
        
        self.id_agent.chat_sync.return_value = Result(True, "", init_response, None, "")
        self.id_agent.initialize_value_system(instruction)
        
        # 2. 生成评估指令
        eval_request = "检查文件操作功能"
        eval_instruction = "创建test.txt，写入内容，读取并删除"
        
        self.id_agent.chat_sync.return_value = Result(True, "", eval_instruction, None, "")
        instruction = self.id_agent.generate_evaluation_instruction(eval_request)
        
        # 3. 评估执行结果
        observation = "所有文件操作成功完成"
        eval_json = '{"目标是否达成": true, "原因": "文件操作功能正常"}'
        
        self.id_agent.chat_sync.return_value = Result(True, "", eval_json, None, "")
        result = self.id_agent.evaluate_goal_achievement(observation)
        
        parsed = json.loads(result)
        self.assertTrue(parsed["目标是否达成"])
    
    def test_iterative_standard_adjustment(self):
        """测试迭代的标准调整"""
        # 初始目标
        self.id_agent.goal_description = "创建图片编辑器"
        self.id_agent.value_standard = "支持图片裁剪、旋转、滤镜功能"
        
        # 第一次调整 - 发现技术限制
        adjustment1 = "发现滤镜功能实现复杂度过高"
        adjusted1 = "支持图片裁剪、旋转功能，暂时不实现滤镜"
        
        self.id_agent.chat_sync.return_value = Result(True, "", adjusted1, None, "")
        self.id_agent.adjust_value_standard(adjustment1)
        
        # 第二次调整 - 用户反馈
        adjustment2 = "用户更需要图片格式转换功能"
        adjusted2 = "支持图片裁剪、旋转、格式转换（JPG/PNG）功能"
        
        self.id_agent.chat_sync.return_value = Result(True, "", adjusted2, None, "")
        result = self.id_agent.adjust_value_standard(adjustment2)
        
        self.assertIn("格式转换", result)
        self.assertNotIn("滤镜", result)
    
    def test_practical_evaluation_approach(self):
        """测试实用的评估方法"""
        # 设置复杂项目
        self.id_agent.goal_description = "开发项目管理系统"
        self.id_agent.value_standard = "基本的项目创建和任务分配功能"
        
        # 生成实用的评估指令
        eval_request = "验证系统功能"
        
        # 本我应该避免复杂的测试
        practical_instruction = "创建一个测试项目，添加2-3个任务，分配给用户"
        
        self.id_agent.chat_sync.return_value = Result(True, "", practical_instruction, None, "")
        instruction = self.id_agent.generate_evaluation_instruction(eval_request)
        
        # 验证指令的简洁性
        self.assertLess(len(instruction), 100)  # 指令应该简短
        self.assertNotIn("覆盖率", instruction)  # 不应包含复杂测试要求
        self.assertNotIn("性能测试", instruction)
        
        # 评估时也应该宽松
        observation = "项目创建成功，任务分配基本可用，界面还比较简陋"
        lenient_eval = '{"目标是否达成": true, "原因": "核心功能已实现，界面可以后续优化"}'
        
        self.id_agent.chat_sync.return_value = Result(True, "", lenient_eval, None, "")
        result = self.id_agent.evaluate_goal_achievement(observation)
        
        parsed = json.loads(result)
        self.assertTrue(parsed["目标是否达成"])


class TestIdAgentEdgeCases(unittest.TestCase):
    """测试本我智能体边缘情况"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_llm = Mock()
        self.id_agent = IdAgent(llm=self.mock_llm)
        self.id_agent.chat_sync = Mock()
    
    def test_empty_instruction_handling(self):
        """测试空指令处理"""
        # 空字符串
        self.id_agent.chat_sync.return_value = Result(
            True, "", "目标描述：未明确\n价值标准：需要进一步明确", None, ""
        )
        result = self.id_agent.initialize_value_system("")
        self.assertIsNotNone(result)
        
        # None值
        result = self.id_agent.initialize_value_system(None)
        self.assertIsNotNone(result)
    
    def test_malformed_response_parsing(self):
        """测试格式错误的响应解析"""
        instruction = "创建应用"
        
        # 缺少标准格式标记的响应
        malformed_response = "创建一个应用程序，要求功能完整"
        
        self.id_agent.chat_sync.return_value = Result(True, "", malformed_response, None, "")
        result = self.id_agent.initialize_value_system(instruction)
        
        # 应该能够处理，即使无法完美解析
        self.assertEqual(self.id_agent.task_specification, malformed_response)
        # goal_description和value_standard可能为空或保持原值
    
    def test_extremely_long_instruction(self):
        """测试极长指令处理"""
        long_instruction = "创建一个系统，" + "包含各种功能，" * 100
        
        self.id_agent.chat_sync.return_value = Result(
            True, "", "目标描述：综合系统\n价值标准：核心功能可用", None, ""
        )
        
        result = self.id_agent.initialize_value_system(long_instruction)
        self.assertIsNotNone(result)
        self.assertEqual(self.id_agent.goal_description, "综合系统")
    
    def test_json_response_variations(self):
        """测试JSON响应的各种变化"""
        observation = "测试完成"
        
        # 测试各种JSON格式
        json_variations = [
            '{"目标是否达成": true, "原因": "完成"}',
            '{"目标是否达成":true,"原因":"完成"}',  # 无空格
            '{\n  "目标是否达成": true,\n  "原因": "完成"\n}',  # 多行
            '{"原因": "完成", "目标是否达成": true}',  # 键顺序不同
        ]
        
        for json_str in json_variations:
            self.id_agent.chat_sync.return_value = Result(True, "", json_str, None, "")
            result = self.id_agent.evaluate_goal_achievement(observation)
            
            # 所有变化都应该能正确解析
            parsed = json.loads(result)
            self.assertTrue(parsed["目标是否达成"])
            self.assertEqual(parsed["原因"], "完成")
    
    def test_concurrent_goal_management(self):
        """测试并发目标管理"""
        # 快速切换多个目标
        goals = [
            ("创建计算器", "基本运算功能"),
            ("创建记事本", "文本编辑功能"),
            ("创建画图工具", "基本绘图功能")
        ]
        
        for instruction, expected_standard in goals:
            response = f"目标描述：{instruction}\n价值标准：{expected_standard}"
            self.id_agent.chat_sync.return_value = Result(True, "", response, None, "")
            
            self.id_agent.initialize_value_system(instruction)
            self.assertIn(expected_standard, self.id_agent.value_standard)
    
    def test_special_characters_in_values(self):
        """测试值中的特殊字符"""
        special_instructions = [
            "创建包含'引号'的系统",
            '创建包含"双引号"的系统',
            "创建包含\n换行的系统",
            "创建包含{花括号}的系统",
            "创建包含\\反斜杠的系统"
        ]
        
        for inst in special_instructions:
            response = f"目标描述：{inst}\n价值标准：功能正常"
            self.id_agent.chat_sync.return_value = Result(True, "", response, None, "")
            
            result = self.id_agent.initialize_value_system(inst)
            self.assertIsNotNone(result)
            # 确保特殊字符被正确处理
            self.assertIn(inst.replace('\n', ''), self.id_agent.goal_description.replace('\n', ''))


if __name__ == '__main__':
    print("🚀 开始本我智能体(Id Agent)单元测试...")
    print("="*60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestIdAgentInitialization,
        TestValueSystemInitialization,
        TestEvaluationInstructionGeneration,
        TestGoalAchievementEvaluation,
        TestValueStandardManagement,
        TestIdAgentIntegration,
        TestIdAgentEdgeCases
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