# -*- coding: utf-8 -*-
"""
任务翻译层测试用例

验证上下文隔离和任务提取效果，确保层次化认知架构中的上下文污染问题得到解决。

Author: Claude Code Assistant
Date: 2025-07-01
Version: 1.0.0
"""

import unittest
import logging
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from CognitiveWorkflow.cognitive_workflow_rule_base.services.task_translator import (
    TaskTranslator, TaskExtractor, ContextFilter, GranularityAdapter, 
    TranslationResult
)

# 设置日志级别
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestTaskTranslator(unittest.TestCase):
    """任务翻译器测试类"""
    
    def setUp(self):
        """测试初始化"""
        # 创建模拟的LLM
        self.mock_llm = Mock()
        
        # 创建翻译器实例
        self.translator = TaskTranslator(llm=self.mock_llm)
        
        logger.info("✅ 测试环境初始化完成")
    
    def test_complex_nested_goal_translation(self):
        """测试复杂嵌套目标的翻译效果"""
        logger.info("🧪 测试：复杂嵌套目标翻译")
        
        # 模拟复杂的嵌套目标（类似之前讨论的上下文污染案例）
        complex_goal = """
        基于当前层次化认知架构的执行状态，考虑到上层Agent已经完成了需求分析和技术选型，
        同时考虑到系统架构约束和性能要求，以及团队的技术栈偏好和项目时间限制，
        需要你在当前的开发环境中实现一个简单的计算器功能，支持基础的四则运算。
        注意要考虑错误处理、输入验证，以及与现有系统的集成兼容性。
        上层系统状态包括：数据库连接池已就绪、缓存层已配置、日志系统已启用、
        监控指标收集器已部署，认证授权模块已集成...
        """
        
        # 模拟LLM响应
        mock_response = Mock()
        mock_response.content = """{
            "extracted_task": "实现一个简单的计算器功能，支持基础的四则运算",
            "filtered_context": "开发环境中的计算器实现，需要错误处理和输入验证",
            "confidence": 0.88,
            "reasoning": "从复杂的层次化背景中提取出核心的计算器实现任务，移除了上层系统状态和架构决策的干扰信息",
            "boundary_constraints": ["支持四则运算", "包含错误处理", "输入验证", "系统集成兼容"]
        }"""
        
        with patch.object(self.translator, '_call_llm_with_json_format', return_value=mock_response.content):
            result = self.translator.translate_task(complex_goal)
            
            # 验证翻译结果
            self.assertIsInstance(result, TranslationResult)
            self.assertEqual(result.extracted_task, "实现一个简单的计算器功能，支持基础的四则运算")
            self.assertGreater(result.confidence, 0.8)
            self.assertEqual(len(result.boundary_constraints), 4)
            
            # 验证上下文被有效过滤
            self.assertNotIn("层次化认知架构", result.extracted_task)
            self.assertNotIn("数据库连接池", result.extracted_task)
            self.assertNotIn("上层Agent", result.extracted_task)
            
            logger.info(f"✅ 翻译成功 - 原始长度: {len(complex_goal)}, 翻译后长度: {len(result.extracted_task)}")
    
    def test_simple_goal_preservation(self):
        """测试简单目标的保持效果"""
        logger.info("🧪 测试：简单目标保持")
        
        simple_goal = "创建一个TODO列表应用"
        
        # 模拟LLM响应
        mock_response = """{
            "extracted_task": "创建一个TODO列表应用",
            "filtered_context": "基础的任务管理应用开发",
            "confidence": 0.95,
            "reasoning": "目标已经足够简洁明确，无需大幅修改",
            "boundary_constraints": []
        }"""
        
        with patch.object(self.translator, '_call_llm_with_json_format', return_value=mock_response):
            result = self.translator.translate_task(simple_goal)
            
            # 验证简单目标基本保持不变
            self.assertEqual(result.extracted_task, simple_goal)
            self.assertGreater(result.confidence, 0.9)
    
    def test_boundary_constraints_extraction(self):
        """测试边界约束提取"""
        logger.info("🧪 测试：边界约束提取")
        
        constrained_goal = """
        在React项目中实现用户认证功能，必须使用JWT token，
        需要支持记住密码功能，密码长度至少8位，
        必须与现有的API端点兼容。
        """
        
        mock_response = """{
            "extracted_task": "实现用户认证功能",
            "filtered_context": "React项目中的用户认证实现",
            "granularity_level": "mid_level",
            "confidence": 0.90,
            "reasoning": "提取核心认证任务，保留技术约束",
            "boundary_constraints": ["使用JWT token", "支持记住密码", "密码长度至少8位", "兼容现有API端点"]
        }"""
        
        with patch.object(self.translator, '_call_llm_with_json_format', return_value=mock_response):
            result = self.translator.translate_task(constrained_goal)
            
            # 验证约束条件被正确提取
            self.assertEqual(len(result.boundary_constraints), 4)
            self.assertIn("使用JWT token", result.boundary_constraints)
            self.assertIn("密码长度至少8位", result.boundary_constraints)
    
    
    def test_error_handling(self):
        """测试错误处理"""
        logger.info("🧪 测试：错误处理")
        
        goal = "测试目标"
        
        # 模拟LLM调用失败
        with patch.object(self.translator, '_call_llm_with_json_format', side_effect=Exception("LLM调用失败")):
            result = self.translator.translate_task(goal)
            
            # 验证错误处理
            self.assertEqual(result.extracted_task, goal)  # 使用原始目标
            self.assertEqual(result.confidence, 0.0)
            self.assertEqual(result.granularity_level, "unknown")
            self.assertIn("翻译失败", result.reasoning)


class TestTaskExtractor(unittest.TestCase):
    """任务提取器测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.mock_llm = Mock()
        self.translator = TaskTranslator(self.mock_llm)
        self.extractor = TaskExtractor(self.translator)
    
    def test_core_task_extraction(self):
        """测试核心任务提取"""
        logger.info("🧪 测试：核心任务提取")
        
        complex_goal = "在考虑系统架构和性能优化的前提下，实现用户管理模块"
        expected_task = "实现用户管理模块"
        
        mock_result = TranslationResult(
            extracted_task=expected_task,
            filtered_context="",
            granularity_level="mid_level",
            confidence=0.85,
            reasoning="提取核心任务",
            boundary_constraints=[]
        )
        
        with patch.object(self.translator, 'translate_task', return_value=mock_result):
            result = self.extractor.extract_core_task(complex_goal)
            self.assertEqual(result, expected_task)


class TestContextFilter(unittest.TestCase):
    """上下文过滤器测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.mock_llm = Mock()
        self.translator = TaskTranslator(self.mock_llm)
        self.filter = ContextFilter(self.translator)
    
    def test_context_filtering(self):
        """测试上下文过滤"""
        logger.info("🧪 测试：上下文过滤")
        
        complex_goal = "基于当前架构约束，实现数据持久化功能，需要考虑ACID特性"
        
        mock_result = TranslationResult(
            extracted_task="实现数据持久化功能",
            filtered_context="数据库操作实现",
            granularity_level="mid_level",
            confidence=0.80,
            reasoning="过滤复杂上下文",
            boundary_constraints=["ACID特性支持"]
        )
        
        with patch.object(self.translator, 'translate_task', return_value=mock_result):
            context, constraints = self.filter.filter_context(complex_goal)
            
            self.assertEqual(context, "数据库操作实现")
            self.assertEqual(len(constraints), 1)
            self.assertIn("ACID特性支持", constraints)


class TestGranularityAdapter(unittest.TestCase):
    """粒度适配器测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.mock_llm = Mock()
        self.translator = TaskTranslator(self.mock_llm)
        self.adapter = GranularityAdapter(self.translator)
    
    def test_granularity_determination(self):
        """测试粒度级别确定"""
        logger.info("🧪 测试：粒度级别确定")
        
        goal = "优化数据库查询性能"
        
        mock_result = TranslationResult(
            extracted_task=goal,
            filtered_context="",
            granularity_level="low_level",
            confidence=0.85,
            reasoning="具体的优化任务",
            boundary_constraints=[]
        )
        
        with patch.object(self.translator, 'translate_task', return_value=mock_result):
            granularity = self.adapter.determine_granularity(goal)
            self.assertEqual(granularity, "low_level")


class TestIntegrationScenarios(unittest.TestCase):
    """集成场景测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.mock_llm = Mock()
        self.translator = TaskTranslator(self.mock_llm)
    
    def test_context_pollution_prevention(self):
        """测试上下文污染防护"""
        logger.info("🧪 测试：上下文污染防护")
        
        # 模拟严重的上下文污染场景
        polluted_goal = """
        当前系统运行在Kubernetes集群中，使用微服务架构，
        前端采用React+TypeScript，后端使用Spring Boot，
        数据库是PostgreSQL集群，缓存层是Redis，
        消息队列是RabbitMQ，监控使用Prometheus+Grafana，
        日志收集用ELK Stack，CI/CD基于Jenkins，
        容器镜像存储在Harbor，代码托管在GitLab。
        
        在这个复杂的技术栈背景下，上层决策Agent已经分析了业务需求，
        确定了技术方案，制定了项目计划，分配了人力资源，
        估算了开发成本，评估了技术风险，设计了系统架构。
        
        现在需要你实现一个简单的用户注册功能。
        """
        
        # 模拟LLM的翻译响应
        mock_response = """{
            "extracted_task": "实现用户注册功能",
            "filtered_context": "Web应用的用户注册实现",
            "granularity_level": "mid_level",
            "confidence": 0.92,
            "reasoning": "成功提取核心的用户注册任务，过滤掉了复杂的技术栈描述和上层决策过程，这些信息对当前任务执行不是必需的",
            "boundary_constraints": ["Web应用集成", "数据持久化", "输入验证"]
        }"""
        
        with patch.object(self.translator, '_call_llm_with_json_format', return_value=mock_response):
            result = self.translator.translate_task(polluted_goal)
            
            # 验证污染信息被有效清除
            clean_task = result.extracted_task
            
            # 不应包含技术栈详情
            self.assertNotIn("Kubernetes", clean_task)
            self.assertNotIn("PostgreSQL", clean_task)  
            self.assertNotIn("RabbitMQ", clean_task)
            self.assertNotIn("Jenkins", clean_task)
            
            # 不应包含上层决策过程
            self.assertNotIn("上层决策Agent", clean_task)
            self.assertNotIn("业务需求分析", clean_task)
            self.assertNotIn("技术方案", clean_task)
            self.assertNotIn("项目计划", clean_task)
            
            # 应该保持核心任务清晰
            self.assertIn("用户注册", clean_task)
            self.assertTrue(len(clean_task) < len(polluted_goal) * 0.1)  # 大幅简化
            
            logger.info(f"✅ 上下文污染防护成功")
            logger.info(f"  - 原始长度: {len(polluted_goal)} 字符")
            logger.info(f"  - 清理后长度: {len(clean_task)} 字符") 
            logger.info(f"  - 压缩比: {len(clean_task)/len(polluted_goal)*100:.1f}%")


def run_all_tests():
    """运行所有测试"""
    logger.info("🚀 开始运行任务翻译层测试套件")
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestTaskTranslator,
        TestTaskExtractor, 
        TestContextFilter,
        TestGranularityAdapter,
        TestIntegrationScenarios
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 测试结果统计
    logger.info(f"📊 测试结果统计:")
    logger.info(f"  - 总测试数: {result.testsRun}")
    logger.info(f"  - 成功: {result.testsRun - len(result.failures) - len(result.errors)}")  
    logger.info(f"  - 失败: {len(result.failures)}")
    logger.info(f"  - 错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        logger.info("✅ 所有测试通过！")
    else:
        logger.error("❌ 部分测试失败")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_all_tests()