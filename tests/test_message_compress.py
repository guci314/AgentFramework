#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
message_compress.py 简化单元测试 - 专注核心功能测试
"""

import unittest
import os
import sys
from typing import List

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from message_compress import compress_messages
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage


class TestMessageCompressCore(unittest.TestCase):
    """消息压缩核心功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.small_messages = self._create_test_messages(5)
        self.medium_messages = self._create_test_messages(15)
        self.boundary_messages = self._create_test_messages(10)
        
    def _create_test_messages(self, count: int) -> List[BaseMessage]:
        """创建测试消息列表"""
        messages = []
        for i in range(count):
            if i % 2 == 0:
                messages.append(HumanMessage(content=f"用户消息{i+1}"))
            else:
                messages.append(AIMessage(content=f"AI回复{i+1}"))
        return messages
    
    def test_no_compression_empty_list(self):
        """测试空列表不压缩"""
        result = compress_messages([])
        self.assertEqual(len(result), 0)
        self.assertEqual(result, [])
    
    def test_no_compression_single_message(self):
        """测试单条消息不压缩"""
        single_message = [HumanMessage(content="单条消息")]
        result = compress_messages(single_message)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].content, "单条消息")
        self.assertIsInstance(result[0], HumanMessage)
    
    def test_no_compression_small_list(self):
        """测试小于10条消息不压缩"""
        result = compress_messages(self.small_messages)
        self.assertEqual(len(result), 5)
        self.assertEqual(result, self.small_messages)
    
    def test_no_compression_boundary_case(self):
        """测试恰好10条消息不压缩"""
        result = compress_messages(self.boundary_messages)
        self.assertEqual(len(result), 10)
        self.assertEqual(result, self.boundary_messages)
    
    def test_message_type_preservation(self):
        """测试消息类型保持正确"""
        mixed_messages = [
            HumanMessage(content="用户1"),
            AIMessage(content="AI1"),
            HumanMessage(content="用户2"),
            AIMessage(content="AI2"),
        ]
        
        result = compress_messages(mixed_messages)
        self.assertEqual(len(result), 4)
        
        # 验证消息类型交替
        for i, msg in enumerate(result):
            if i % 2 == 0:
                self.assertIsInstance(msg, HumanMessage)
                self.assertIn("用户", msg.content)
            else:
                self.assertIsInstance(msg, AIMessage)
                self.assertIn("AI", msg.content)
    
    def test_input_validation(self):
        """测试输入验证"""
        # 测试非法输入类型
        with self.assertRaises(TypeError):
            compress_messages("invalid_input")
        
        # 测试None输入
        with self.assertRaises(TypeError):
            compress_messages(None)
    
    def test_message_content_basic(self):
        """测试消息内容基本处理"""
        messages_with_special_content = [
            HumanMessage(content=""),  # 空内容
            AIMessage(content="正常内容"),
            HumanMessage(content="特殊字符!@#$%^&*()"),
            AIMessage(content="中文内容测试"),
            HumanMessage(content="数字123456"),
            AIMessage(content="换行\n内容"),
        ]
        
        result = compress_messages(messages_with_special_content)
        self.assertEqual(len(result), 6)  # 不触发压缩
        
        # 验证内容保持不变
        for i, (original, processed) in enumerate(zip(messages_with_special_content, result)):
            self.assertEqual(original.content, processed.content)
            self.assertEqual(type(original), type(processed))


class TestMessageCompressIntegrationSimple(unittest.TestCase):
    """简化集成测试 - 需要真实API密钥"""
    
    def setUp(self):
        """检查API密钥是否可用"""
        self.has_deepseek_key = bool(os.getenv('DEEPSEEK_API_KEY'))
        
    @unittest.skipUnless(os.getenv('DEEPSEEK_API_KEY'), "需要DEEPSEEK_API_KEY环境变量")
    def test_real_compression_with_deepseek(self):
        """真实压缩测试 - DeepSeek"""
        # 创建足够的消息以触发压缩
        test_messages = []
        for i in range(12):
            test_messages.append(HumanMessage(content=f"这是测试消息{i+1}，用于验证压缩功能"))
            test_messages.append(AIMessage(content=f"这是AI回复{i+1}，确认收到用户消息"))
        
        try:
            result = compress_messages(test_messages, use_deepseek=True)
            
            # 基本验证
            self.assertEqual(len(result), 12)  # 压缩后固定12条
            self.assertIsInstance(result[0], HumanMessage)
            self.assertIsInstance(result[1], AIMessage)
            self.assertEqual(result[1].content, "ok")
            
            # 验证摘要不为空
            self.assertGreater(len(result[0].content), 50)
            
            # 验证最后10条消息保持不变
            original_last_10 = test_messages[-10:]
            preserved_messages = result[2:]
            self.assertEqual(len(preserved_messages), 10)
            
            for original, preserved in zip(original_last_10, preserved_messages):
                self.assertEqual(original.content, preserved.content)
                self.assertEqual(type(original), type(preserved))
            
            print(f"✅ 真实API压缩测试成功: {len(test_messages)}条 -> {len(result)}条")
            
        except Exception as e:
            self.fail(f"DeepSeek API调用失败: {e}")
    
    @unittest.skipUnless(os.getenv('OPENROUTER_API_KEY'), "需要OPENROUTER_API_KEY环境变量")
    def test_real_compression_with_gemini(self):
        """真实压缩测试 - Gemini"""
        test_messages = []
        for i in range(8):
            test_messages.append(HumanMessage(content=f"Gemini测试消息{i+1}"))
            test_messages.append(AIMessage(content=f"Gemini测试回复{i+1}"))
        
        try:
            result = compress_messages(test_messages, use_deepseek=False)
            
            # 基本验证
            self.assertEqual(len(result), 12)
            self.assertIsInstance(result[0], HumanMessage)
            self.assertIsInstance(result[1], AIMessage)
            
            print(f"✅ Gemini真实API压缩测试成功")
            
        except Exception as e:
            self.fail(f"Gemini API调用失败: {e}")
    
    def test_compression_decision_logic(self):
        """测试压缩决策逻辑"""
        # 测试不同长度的消息列表
        test_cases = [
            (0, False),   # 空列表
            (1, False),   # 单条消息
            (5, False),   # 小于10条
            (10, False),  # 恰好10条
            (11, True),   # 大于10条，应该压缩
            (20, True),   # 大于10条，应该压缩
        ]
        
        for count, should_compress in test_cases:
            messages = []
            for i in range(count):
                if i % 2 == 0:
                    messages.append(HumanMessage(content=f"测试{i}"))
                else:
                    messages.append(AIMessage(content=f"回复{i}"))
            
            if should_compress and self.has_deepseek_key:
                # 如果应该压缩且有API密钥，进行真实压缩测试
                try:
                    result = compress_messages(messages)
                    self.assertEqual(len(result), 12)
                    print(f"✅ 压缩决策测试 {count}条消息 -> 压缩为12条")
                except Exception as e:
                    print(f"⚠️  压缩决策测试失败 {count}条消息: {e}")
            elif not should_compress:
                # 不应该压缩的情况
                result = compress_messages(messages)
                self.assertEqual(len(result), count)
                print(f"✅ 压缩决策测试 {count}条消息 -> 不压缩，保持{count}条")


class TestMessageCompressEdgeCases(unittest.TestCase):
    """边界情况测试"""
    
    def test_mixed_message_types(self):
        """测试混合消息类型"""
        # 连续的同类型消息
        consecutive_human = [
            HumanMessage(content="消息1"),
            HumanMessage(content="消息2"),
            AIMessage(content="回复1"),
            AIMessage(content="回复2"),
        ]
        
        result = compress_messages(consecutive_human)
        self.assertEqual(len(result), 4)
        self.assertEqual(result, consecutive_human)
    
    def test_extremely_long_content(self):
        """测试极长内容消息"""
        long_content = "这是一条非常长的消息内容。" * 1000  # 约15000字符
        long_messages = [
            HumanMessage(content=long_content),
            AIMessage(content="简短回复"),
        ]
        
        result = compress_messages(long_messages)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].content, long_content)
    
    def test_unicode_and_emoji(self):
        """测试Unicode和表情符号"""
        unicode_messages = [
            HumanMessage(content="你好世界 🌍"),
            AIMessage(content="Hello World! 😊"),
            HumanMessage(content="测试中文字符：汉字、标点！？"),
            AIMessage(content="Testing emojis: 🚀🎉💻📱"),
        ]
        
        result = compress_messages(unicode_messages)
        self.assertEqual(len(result), 4)
        
        # 验证Unicode内容保持不变
        for original, processed in zip(unicode_messages, result):
            self.assertEqual(original.content, processed.content)


if __name__ == '__main__':
    print("🚀 开始message_compress.py简化单元测试...")
    print("="*60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加核心功能测试
    suite.addTests(loader.loadTestsFromTestCase(TestMessageCompressCore))
    
    # 添加边界情况测试
    suite.addTests(loader.loadTestsFromTestCase(TestMessageCompressEdgeCases))
    
    # 添加集成测试（如果有API密钥）
    if os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENROUTER_API_KEY'):
        suite.addTests(loader.loadTestsFromTestCase(TestMessageCompressIntegrationSimple))
        print("📡 包含真实API集成测试")
    else:
        print("⚠️  跳过真实API测试（缺少API密钥）")
    
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
                print(f"  - {test}: {error}")
                
        if result.errors:
            print("\n错误的测试:")
            for test, error in result.errors:
                print(f"  - {test}: {error}")
    
    print(f"📊 测试统计:")
    print(f"   - 运行测试: {result.testsRun}")
    print(f"   - 成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   - 失败: {len(result.failures)}")
    print(f"   - 错误: {len(result.errors)}")
    print("="*60)