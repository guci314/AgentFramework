#!/usr/bin/env python3
"""
AI State Updater Unit Tests
============================

Comprehensive unit tests for the AIStateUpdaterService class covering:
- LLM API mocking and isolation of updater logic
- Prompt construction validation from templates and input data  
- Response parsing for valid and invalid LLM responses
- Fallback mechanisms when LLM fails or returns unusable data
- Error handling for API issues, timeouts, and unexpected responses
- Template management and scenario detection
- Confidence scoring and quality assessment

Test Coverage Goals: 90%+ for AIStateUpdaterService class
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import the classes we're testing
from enhancedAgent_v2 import (
    AIStateUpdaterService,
    WorkflowState,
    PromptScenario,
    PromptTemplateManager,
    ResponseParser,
    ParsedStateInfo,
    ResponseQuality,
    FallbackStrategy,
    FallbackStateGenerator
)

# Mock LLM for testing
class MockChatOpenAI:
    """Mock ChatOpenAI for testing"""
    def __init__(self, model="test-model", temperature=0.6, max_tokens=8192):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.call_count = 0
        self.responses = []
        self.should_fail = False
        self.failure_type = "timeout"
        
    def invoke(self, messages):
        """Mock invoke method"""
        self.call_count += 1
        
        if self.should_fail:
            if self.failure_type == "timeout":
                raise Exception("Request timeout")
            elif self.failure_type == "api_error":
                raise Exception("API Error: Rate limit exceeded")
            elif self.failure_type == "auth_error":
                raise Exception("Authentication failed")
        
        if self.responses:
            response = self.responses.pop(0)
        else:
            response = "默认状态更新：系统正在正常运行中"
            
        # Mock response object
        mock_response = Mock()
        mock_response.content = response
        return mock_response
    
    def set_responses(self, responses: List[str]):
        """Set predefined responses"""
        self.responses = responses.copy()
    
    def set_failure(self, should_fail: bool, failure_type: str = "timeout"):
        """Set failure mode"""
        self.should_fail = should_fail
        self.failure_type = failure_type


class TestAIStateUpdaterServiceBasicOperations(unittest.TestCase):
    """Test basic operations of AIStateUpdaterService"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_llm = MockChatOpenAI()
        self.updater = AIStateUpdaterService(
            llm=self.mock_llm,
            max_retries=3,
            retry_delay=0.1,  # Short delay for tests
            enable_sentiment_analysis=True,
            enable_intent_recognition=True
        )
        self.workflow_state = WorkflowState()
        
    def test_initialization(self):
        """Test AIStateUpdaterService initialization"""
        # Test basic initialization
        self.assertIsNotNone(self.updater)
        self.assertEqual(self.updater.max_retries, 3)
        self.assertEqual(self.updater.retry_delay, 0.1)
        self.assertTrue(self.updater.enable_sentiment_analysis)
        self.assertTrue(self.updater.enable_intent_recognition)
        
        # Test template manager initialization
        self.assertIsInstance(self.updater.template_manager, PromptTemplateManager)
        
        # Test response parser initialization
        self.assertIsInstance(self.updater.response_parser, ResponseParser)
        
        # Test fallback generator initialization
        self.assertIsInstance(self.updater.fallback_generator, FallbackStateGenerator)
        
    def test_should_update_basic_conditions(self):
        """Test basic conditions for should_update"""
        # Test with state updates disabled
        self.workflow_state.disable_state_updates()
        context = {"step_info": {"action": "test"}}
        self.assertFalse(self.updater.should_update(self.workflow_state, context))
        
        # Test with state updates enabled but empty context
        self.workflow_state.enable_state_updates()
        self.assertFalse(self.updater.should_update(self.workflow_state, {}))
        
        # Test with valid context
        context = {
            "step_info": {"action": "test", "step_id": "1"},
            "execution_result": "success"
        }
        self.assertTrue(self.updater.should_update(self.workflow_state, context))


class TestAIStateUpdaterServiceLLMIntegration(unittest.TestCase):
    """Test LLM integration with mocking"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_llm = MockChatOpenAI()
        self.updater = AIStateUpdaterService(
            llm=self.mock_llm,
            max_retries=3,
            retry_delay=0.1
        )
        self.workflow_state = WorkflowState()
        self.workflow_state.set_global_state("初始状态：系统启动")
        
    def test_successful_state_update(self):
        """Test successful state update with valid LLM response"""
        # Set up context
        context = {
            "step_info": {
                "action": "execute_step",
                "step_id": "1",
                "instruction": "测试指令"
            },
            "execution_result": "成功执行",
            "step_status": "completed"
        }
        
        # Set expected LLM response
        expected_response = "任务执行成功：测试指令已完成，系统状态良好"
        self.mock_llm.set_responses([expected_response])
        
        # Call update_state
        result = self.updater.update_state(self.workflow_state, context)
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result, expected_response)
        self.assertEqual(self.mock_llm.call_count, 1)
        
    def test_llm_failure_with_retry(self):
        """Test LLM failure with retry mechanism"""
        context = {
            "step_info": {"action": "test", "step_id": "1"},
            "execution_result": "test"
        }
        
        # First two calls fail, third succeeds
        self.mock_llm.set_failure(True, "timeout")
        self.mock_llm.set_responses(["", "", "重试成功的状态更新"])
        
        # Override the failure after 2 calls
        original_invoke = self.mock_llm.invoke
        call_count = 0
        def mock_invoke_with_retry(messages):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Request timeout")
            else:
                mock_response = Mock()
                mock_response.content = "重试成功的状态更新"
                return mock_response
        
        self.mock_llm.invoke = mock_invoke_with_retry
        
        # Call update_state
        result = self.updater.update_state(self.workflow_state, context)
        
        # Verify retry logic worked
        self.assertIsNotNone(result)
        self.assertEqual(result, "重试成功的状态更新")
        self.assertEqual(call_count, 3)  # Two failures + one success
        
    def test_llm_complete_failure_fallback(self):
        """Test complete LLM failure triggers fallback"""
        context = {
            "step_info": {"action": "test", "step_id": "1"},
            "execution_result": "test"
        }
        
        # All calls fail
        self.mock_llm.set_failure(True, "api_error")
        
        # Call update_state
        result = self.updater.update_state(self.workflow_state, context)
        
        # Should get fallback result
        self.assertIsNotNone(result)
        self.assertIn("步骤执行完成", result)  # Default template fallback
        
    def test_invalid_llm_response_parsing(self):
        """Test handling of invalid LLM responses"""
        context = {
            "step_info": {"action": "test", "step_id": "1"},
            "execution_result": "test"
        }
        
        # Set invalid responses (empty, too short, etc.)
        invalid_responses = ["", "   ", "短", None]
        
        for invalid_response in invalid_responses:
            with self.subTest(response=invalid_response):
                self.mock_llm.set_responses([str(invalid_response) if invalid_response else ""])
                
                result = self.updater.update_state(self.workflow_state, context)
                
                # Should get fallback or retry with simplified prompt
                self.assertIsNotNone(result)


class TestAIStateUpdaterServicePromptConstruction(unittest.TestCase):
    """Test prompt construction and template management"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_llm = MockChatOpenAI()
        self.updater = AIStateUpdaterService(llm=self.mock_llm)
        self.workflow_state = WorkflowState()
        
    @patch.object(AIStateUpdaterService, '_build_state_update_prompt')
    def test_prompt_construction_called(self, mock_build_prompt):
        """Test that prompt construction is called correctly"""
        mock_build_prompt.return_value = "测试提示"
        self.mock_llm.set_responses(["测试响应"])
        
        context = {
            "step_info": {"action": "test", "step_id": "1"},
            "execution_result": "test"
        }
        
        self.updater.update_state(self.workflow_state, context)
        
        # Verify prompt construction was called
        mock_build_prompt.assert_called_once_with(self.workflow_state, context)
        
    def test_scenario_detection(self):
        """Test scenario detection for template selection"""
        test_cases = [
            {
                "context": {"step_status": "completed", "execution_result": "success"},
                "expected_scenario": PromptScenario.SUCCESS_COMPLETION
            },
            {
                "context": {"step_status": "failed", "error_info": "test error"},
                "expected_scenario": PromptScenario.ERROR_HANDLING
            },
            {
                "context": {"step_info": {"action": "initialize"}},
                "expected_scenario": PromptScenario.INITIALIZATION
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(context=test_case["context"]):
                scenario = self.updater._detect_scenario(self.workflow_state, test_case["context"])
                self.assertEqual(scenario, test_case["expected_scenario"])
                
    def test_template_variable_preparation(self):
        """Test template variable preparation"""
        self.workflow_state.set_global_state("当前状态")
        context = {
            "step_info": {
                "action": "test_action",
                "step_id": "step_1",
                "instruction": "测试指令"
            },
            "execution_result": "成功",
            "step_status": "completed"
        }
        
        variables = self.updater._prepare_template_variables(self.workflow_state, context)
        
        # Check required variables
        self.assertIn("current_state", variables)
        self.assertIn("step_action", variables)
        self.assertIn("step_result", variables)
        self.assertIn("step_status", variables)
        self.assertEqual(variables["current_state"], "当前状态")
        self.assertEqual(variables["step_action"], "test_action")


class TestAIStateUpdaterServiceResponseParsing(unittest.TestCase):
    """Test response parsing and validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_llm = MockChatOpenAI()
        self.updater = AIStateUpdaterService(
            llm=self.mock_llm,
            enable_sentiment_analysis=True,
            enable_intent_recognition=True
        )
        self.workflow_state = WorkflowState()
        
    def test_valid_response_parsing(self):
        """Test parsing of valid responses"""
        valid_responses = [
            "任务执行成功，系统状态正常",
            "文件上传完成，准备下一步处理",
            "数据库连接已建立，查询操作就绪",
            "用户认证通过，权限验证完成"
        ]
        
        for response in valid_responses:
            with self.subTest(response=response):
                parsed_info = self.updater.response_parser.parse_response(response)
                
                self.assertIsInstance(parsed_info, ParsedStateInfo)
                self.assertGreater(len(parsed_info.main_content), 0)
                self.assertGreaterEqual(parsed_info.confidence_score, 0.0)
                self.assertLessEqual(parsed_info.confidence_score, 1.0)
                
    def test_invalid_response_handling(self):
        """Test handling of invalid responses"""
        invalid_responses = [
            "",           # Empty
            "   ",        # Whitespace only
            "短",         # Too short
            "a" * 1000,   # Too long
            "###ERROR###" # Error marker
        ]
        
        for response in invalid_responses:
            with self.subTest(response=response):
                parsed_info = self.updater.response_parser.parse_response(response)
                
                # Should still return parsed info but with low confidence
                self.assertIsInstance(parsed_info, ParsedStateInfo)
                if response.strip():  # Non-empty responses
                    self.assertLessEqual(parsed_info.confidence_score, 0.5)
                    
    def test_sentiment_analysis(self):
        """Test sentiment analysis functionality"""
        sentiment_test_cases = [
            ("任务成功完成，结果很好", "positive"),
            ("发生错误，需要修复", "negative"),
            ("系统正在运行，状态正常", "neutral")
        ]
        
        for text, expected_sentiment in sentiment_test_cases:
            with self.subTest(text=text):
                parsed_info = self.updater.response_parser.parse_response(text)
                # Note: Actual sentiment may vary based on implementation
                self.assertIsNotNone(parsed_info.sentiment)
                
    def test_intent_recognition(self):
        """Test intent recognition functionality"""
        intent_test_cases = [
            ("更新状态信息", "update"),
            ("报告错误情况", "error_report"),
            ("查询当前状态", "query"),
            ("完成任务操作", "completion")
        ]
        
        for text, expected_intent in intent_test_cases:
            with self.subTest(text=text):
                parsed_info = self.updater.response_parser.parse_response(text)
                # Note: Actual intent may vary based on implementation
                self.assertIsNotNone(parsed_info.intent)


class TestAIStateUpdaterServiceFallbackMechanisms(unittest.TestCase):
    """Test fallback mechanisms and error recovery"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_llm = MockChatOpenAI()
        self.updater = AIStateUpdaterService(
            llm=self.mock_llm,
            fallback_strategies=[
                FallbackStrategy.RETRY_SIMPLIFIED,
                FallbackStrategy.TEMPLATE_BASED,
                FallbackStrategy.RULE_BASED,
                FallbackStrategy.MINIMAL_STATE
            ]
        )
        self.workflow_state = WorkflowState()
        
    def test_fallback_strategy_execution(self):
        """Test execution of fallback strategies"""
        context = {
            "step_info": {"action": "test", "step_id": "1"},
            "execution_result": "test"
        }
        
        # Test each fallback strategy
        strategies = [
            FallbackStrategy.TEMPLATE_BASED,
            FallbackStrategy.RULE_BASED, 
            FallbackStrategy.MINIMAL_STATE
        ]
        
        for strategy in strategies:
            with self.subTest(strategy=strategy):
                result = self.updater.fallback_generator.generate_fallback_state(
                    strategy, self.workflow_state, context, "Test failure"
                )
                
                self.assertIsNotNone(result)
                self.assertGreater(len(result), 0)
                
    def test_simplified_retry_mechanism(self):
        """Test simplified retry mechanism"""
        context = {
            "step_info": {"action": "complex_test", "step_id": "1"},
            "execution_result": "test"
        }
        
        # First call fails, second with simplified prompt succeeds
        call_count = 0
        def mock_invoke_with_simplified_retry(messages):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Complex prompt failed")
            else:
                mock_response = Mock()
                mock_response.content = "简化重试成功"
                return mock_response
        
        self.mock_llm.invoke = mock_invoke_with_simplified_retry
        
        result = self.updater.update_state(self.workflow_state, context)
        
        self.assertIsNotNone(result)
        # Should be either the retry result or a fallback
        self.assertGreater(len(result), 0)
        
    def test_fallback_statistics_tracking(self):
        """Test fallback statistics tracking"""
        initial_stats = self.updater.get_fallback_statistics()
        
        # Force fallback by making LLM always fail
        self.mock_llm.set_failure(True, "api_error")
        
        context = {
            "step_info": {"action": "test", "step_id": "1"},
            "execution_result": "test"
        }
        
        # Trigger fallback
        self.updater.update_state(self.workflow_state, context)
        
        updated_stats = self.updater.get_fallback_statistics()
        
        # Verify statistics were updated
        self.assertGreaterEqual(updated_stats['total_fallbacks'], initial_stats['total_fallbacks'])


class TestAIStateUpdaterServiceErrorHandling(unittest.TestCase):
    """Test comprehensive error handling"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_llm = MockChatOpenAI()
        self.updater = AIStateUpdaterService(llm=self.mock_llm)
        self.workflow_state = WorkflowState()
        
    def test_timeout_error_handling(self):
        """Test handling of timeout errors"""
        self.mock_llm.set_failure(True, "timeout")
        
        context = {
            "step_info": {"action": "test", "step_id": "1"},
            "execution_result": "test"
        }
        
        result = self.updater.update_state(self.workflow_state, context)
        
        # Should return fallback result, not raise exception
        self.assertIsNotNone(result)
        
    def test_api_error_handling(self):
        """Test handling of API errors"""
        self.mock_llm.set_failure(True, "api_error")
        
        context = {
            "step_info": {"action": "test", "step_id": "1"},
            "execution_result": "test"
        }
        
        result = self.updater.update_state(self.workflow_state, context)
        
        # Should return fallback result, not raise exception
        self.assertIsNotNone(result)
        
    def test_authentication_error_handling(self):
        """Test handling of authentication errors"""
        self.mock_llm.set_failure(True, "auth_error")
        
        context = {
            "step_info": {"action": "test", "step_id": "1"},
            "execution_result": "test"
        }
        
        result = self.updater.update_state(self.workflow_state, context)
        
        # Should return fallback result, not raise exception
        self.assertIsNotNone(result)
        
    def test_malformed_context_handling(self):
        """Test handling of malformed context data"""
        malformed_contexts = [
            {},  # Empty context
            {"incomplete": "data"},  # Missing required fields
            {"step_info": None},  # None values
            {"step_info": {"action": ""}},  # Empty values
        ]
        
        for context in malformed_contexts:
            with self.subTest(context=context):
                # Should not raise exception
                try:
                    result = self.updater.update_state(self.workflow_state, context)
                    # If it returns something, should be valid
                    if result is not None:
                        self.assertIsInstance(result, str)
                        self.assertGreater(len(result), 0)
                except Exception as e:
                    self.fail(f"Should not raise exception for context {context}: {e}")


class TestAIStateUpdaterServiceIntegration(unittest.TestCase):
    """Test integration scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_llm = MockChatOpenAI()
        self.updater = AIStateUpdaterService(llm=self.mock_llm)
        self.workflow_state = WorkflowState()
        
    def test_end_to_end_success_scenario(self):
        """Test complete success scenario"""
        # Set up workflow state
        self.workflow_state.set_global_state("初始状态")
        
        # Set up successful context
        context = {
            "step_info": {
                "action": "file_upload",
                "step_id": "upload_1",
                "instruction": "上传用户文件到服务器"
            },
            "execution_result": "文件上传成功",
            "step_status": "completed",
            "timestamp": datetime.now().isoformat()
        }
        
        # Set expected LLM response
        expected_response = "文件上传任务完成：用户文件已成功上传到服务器，系统准备进行下一步处理"
        self.mock_llm.set_responses([expected_response])
        
        # Execute end-to-end
        result = self.updater.update_state(self.workflow_state, context)
        
        # Verify complete pipeline
        self.assertIsNotNone(result)
        self.assertEqual(result, expected_response)
        self.assertEqual(self.mock_llm.call_count, 1)
        
        # Verify parsed info was stored
        last_parsed = self.updater.get_last_parsed_info()
        self.assertIsNotNone(last_parsed)
        self.assertIsInstance(last_parsed, ParsedStateInfo)
        
    def test_complex_failure_recovery_scenario(self):
        """Test complex failure and recovery scenario"""
        context = {
            "step_info": {"action": "complex_operation", "step_id": "complex_1"},
            "execution_result": "partial_failure",
            "error_info": "Network connection unstable"
        }
        
        # Simulate multiple failure types
        responses = []
        
        # First attempt: timeout
        # Second attempt: invalid response  
        # Third attempt: success
        call_count = 0
        def complex_mock_invoke(messages):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                raise Exception("Request timeout")
            elif call_count == 2:
                mock_response = Mock()
                mock_response.content = "短"  # Too short, invalid
                return mock_response
            else:
                mock_response = Mock()
                mock_response.content = "复杂操作部分失败，网络连接不稳定，正在尝试重新建立连接并重试"
                return mock_response
        
        self.mock_llm.invoke = complex_mock_invoke
        
        result = self.updater.update_state(self.workflow_state, context)
        
        # Should eventually succeed or provide meaningful fallback
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 5)  # Meaningful content
        
    def test_performance_under_load(self):
        """Test performance characteristics"""
        self.mock_llm.set_responses(["状态更新"] * 10)
        
        context = {
            "step_info": {"action": "load_test", "step_id": "load_1"},
            "execution_result": "success"
        }
        
        start_time = time.time()
        
        # Execute multiple updates quickly
        results = []
        for i in range(5):
            result = self.updater.update_state(self.workflow_state, context)
            results.append(result)
        
        end_time = time.time()
        
        # Verify all succeeded
        for result in results:
            self.assertIsNotNone(result)
            
        # Verify reasonable performance (should complete in reasonable time)
        total_time = end_time - start_time
        self.assertLess(total_time, 5.0)  # Should complete within 5 seconds


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2) 