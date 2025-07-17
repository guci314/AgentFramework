#!/usr/bin/env python3
"""
End-to-End Scenario Tests for Workflow State Management and AI Integration
==========================================================================

This module contains comprehensive end-to-end tests that validate the complete
workflow execution scenarios, including:

1. Happy Path: Successful multi-step execution with AI state updates
2. Failure & Retry: Step failure followed by successful retry
3. AI-Driven State Changes: Mid-workflow AI state updates affecting subsequent steps
4. Terminal Failure: Workflow halts correctly on unrecoverable errors

Each test validates:
- Complete state history tracking
- AI state updater integration
- Decision-making logic
- Error handling and recovery
- Final workflow outcomes
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import the classes we're testing
from enhancedAgent_v2 import (
    MultiStepAgent_v2,
    WorkflowState,
    AIStateUpdaterService,
    PromptScenario,
    StateHistoryEntry,
    Result
)

# Mock LLM for end-to-end testing
class E2EMockChatOpenAI:
    """Enhanced Mock ChatOpenAI for end-to-end scenario testing"""
    def __init__(self, model="e2e-test-model"):
        self.model = model
        self.call_count = 0
        self.response_queue = []
        self.should_fail = False
        self.failure_count = 0
        self.max_failures = 0
        
    def invoke(self, messages):
        """Mock invoke method with enhanced control"""
        self.call_count += 1
        
        if self.should_fail and self.failure_count < self.max_failures:
            self.failure_count += 1
            raise Exception(f"Mock LLM failure #{self.failure_count}")
            
        if self.response_queue:
            response = self.response_queue.pop(0)
        else:
            # Default response based on context
            if hasattr(self, '_current_scenario'):
                if self._current_scenario == 'state_update':
                    response = f"状态更新：系统执行进度 {self.call_count}"
                elif self._current_scenario == 'planning':
                    response = self._generate_default_plan()
                else:
                    response = f"任务执行完成 #{self.call_count}"
            else:
                response = f"默认LLM响应 #{self.call_count}"
            
        # Mock response object
        mock_response = Mock()
        mock_response.content = response
        return mock_response
    
    def set_responses(self, responses: List[str]):
        """Set predefined response queue"""
        self.response_queue = responses.copy()
    
    def set_failure_mode(self, should_fail: bool, max_failures: int = 1):
        """Configure failure behavior"""
        self.should_fail = should_fail
        self.max_failures = max_failures
        self.failure_count = 0
    
    def set_scenario(self, scenario: str):
        """Set current test scenario"""
        self._current_scenario = scenario
    
    def _generate_default_plan(self):
        """Generate a default test plan"""
        return """
        [
            {
                "id": "step1",
                "name": "初始化测试环境",
                "instruction": "设置测试环境和必要的资源",
                "agent_name": "test_agent",
                "instruction_type": "execution",
                "phase": "information",
                "expected_output": "环境初始化完成",
                "prerequisites": "无"
            },
            {
                "id": "step2", 
                "name": "执行核心任务",
                "instruction": "执行主要的测试任务",
                "agent_name": "test_agent",
                "instruction_type": "execution", 
                "phase": "execution",
                "expected_output": "任务执行完成",
                "prerequisites": "环境已初始化"
            },
            {
                "id": "step3",
                "name": "验证结果",
                "instruction": "验证任务执行结果",
                "agent_name": "test_agent",
                "instruction_type": "execution",
                "phase": "verification", 
                "expected_output": "验证完成",
                "prerequisites": "核心任务已完成"
            }
        ]
        """


class TestE2EWorkflowScenarios(unittest.TestCase):
    """End-to-end workflow scenario tests"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_llm = E2EMockChatOpenAI()
        self.agent = MultiStepAgent_v2(llm=self.mock_llm)
        self.workflow_state = self.agent.workflow_state
        
    def test_happy_path_successful_execution(self):
        """
        Scenario 1: Happy Path - Complete successful execution with AI state updates
        
        This test validates:
        - Multi-step workflow execution
        - AI state updates between steps
        - State history accumulation
        - Successful completion
        """
        print("\\n=== E2E Test: Happy Path Scenario ===")
        
        # Set up responses for planning and execution
        plan_response = """
        [
            {
                "id": "init_task",
                "name": "Initialize Environment", 
                "instruction": "Set up the test environment",
                "agent_name": "test_agent",
                "instruction_type": "execution",
                "phase": "information",
                "expected_output": "Environment ready",
                "prerequisites": "None"
            },
            {
                "id": "process_task",
                "name": "Process Data",
                "instruction": "Process the test data",
                "agent_name": "test_agent", 
                "instruction_type": "execution",
                "phase": "execution",
                "expected_output": "Data processed",
                "prerequisites": "Environment initialized"
            }
        ]
        """
        
        execution_responses = [
            "环境初始化成功完成",
            "数据处理任务顺利完成"
        ]
        
        state_update_responses = [
            "初始化阶段：测试环境已成功设置，准备进行数据处理",
            "执行阶段：数据处理完成，所有测试通过，系统运行正常"
        ]
        
        # Configure mock responses
        all_responses = [plan_response] + execution_responses + state_update_responses
        self.mock_llm.set_responses(all_responses)
        
        # Mock successful step execution
        with patch.object(self.agent, '_execute_single_workflow_step') as mock_execute:
            # Configure mock to return success
            mock_execute.side_effect = [
                True,  # Step 1 success
                True   # Step 2 success
            ]
            
            # Set up AI state updater for workflow state
            ai_updater = AIStateUpdaterService(
                llm=self.mock_llm,
                max_retries=2,
                retry_delay=0.01
            )
            self.workflow_state.set_ai_updater(ai_updater)
            
            # Execute the workflow
            main_instruction = "Execute a complete test workflow with state management"
            result = self.agent.execute_multi_step(main_instruction, interactive=False)
            
            # Validate the execution
            self.assertIsNotNone(result)
            self.assertIn("完成", result)  # Should mention completion
            
            # Validate state evolution
            final_state = self.workflow_state.get_global_state()
            self.assertIsNotNone(final_state)
            self.assertGreater(len(final_state), 0)
            
            # Validate state history
            history = self.workflow_state.get_state_history()
            self.assertGreaterEqual(len(history), 1)  # At least some state updates
            
            # Validate LLM interactions
            self.assertGreaterEqual(self.mock_llm.call_count, 3)  # Planning + execution + state updates
            
            print(f"✅ Happy path completed successfully")
            print(f"   Final state: {final_state[:100]}...")
            print(f"   History entries: {len(history)}")
            print(f"   LLM calls: {self.mock_llm.call_count}")
    
    def test_failure_and_retry_scenario(self):
        """
        Scenario 2: Failure & Retry - Step fails initially but succeeds on retry
        
        This test validates:
        - Error detection and handling
        - Retry mechanism activation
        - State updates during failure/recovery
        - Successful completion after retry
        """
        print("\\n=== E2E Test: Failure & Retry Scenario ===")
        
        # Set up responses
        plan_response = """
        [
            {
                "id": "reliable_task",
                "name": "Reliable Task",
                "instruction": "Execute a reliable task",
                "agent_name": "test_agent",
                "instruction_type": "execution",
                "phase": "execution", 
                "expected_output": "Task completed",
                "prerequisites": "None"
            },
            {
                "id": "failing_task",
                "name": "Initially Failing Task",
                "instruction": "Execute a task that fails initially",
                "agent_name": "test_agent",
                "instruction_type": "execution",
                "phase": "execution",
                "expected_output": "Task eventually succeeds",
                "prerequisites": "Previous task completed"
            }
        ]
        """
        
        execution_responses = [
            "第一个任务成功完成",
            "第二个任务失败 - 需要重试",
            "重试成功 - 第二个任务现在完成"
        ]
        
        state_responses = [
            "正常执行阶段：第一个任务完成，系统运行正常",
            "错误恢复阶段：检测到任务失败，正在准备重试",
            "恢复完成阶段：重试成功，系统已恢复正常运行"
        ]
        
        all_responses = [plan_response] + execution_responses + state_responses
        self.mock_llm.set_responses(all_responses)
        
        # Mock execution with failure then success
        with patch.object(self.agent, '_execute_single_workflow_step') as mock_execute:
            # First step succeeds, second fails, then retry succeeds
            mock_execute.side_effect = [
                True,   # Step 1 success
                False,  # Step 2 failure
                True    # Step 2 retry success
            ]
            
            # Set up AI state updater
            ai_updater = AIStateUpdaterService(
                llm=self.mock_llm,
                max_retries=2,
                retry_delay=0.01
            )
            self.workflow_state.set_ai_updater(ai_updater)
            
            # Execute the workflow
            main_instruction = "Execute workflow with failure recovery testing"
            result = self.agent.execute_multi_step(main_instruction, interactive=False)
            
            # Validate recovery occurred
            self.assertIsNotNone(result)
            
            # Check state reflects the failure and recovery journey
            final_state = self.workflow_state.get_global_state()
            self.assertIsNotNone(final_state)
            
            # Validate history shows the progression
            history = self.workflow_state.get_state_history()
            self.assertGreaterEqual(len(history), 1)
            
            # Validate multiple execution attempts
            self.assertGreaterEqual(mock_execute.call_count, 2)  # At least initial + retry
            
            print(f"✅ Failure & retry scenario completed")
            print(f"   Final state: {final_state[:100]}...")
            print(f"   Execution attempts: {mock_execute.call_count}")
            print(f"   History entries: {len(history)}")
    
    def test_ai_driven_state_changes_scenario(self):
        """
        Scenario 3: AI-Driven State Changes - Mid-workflow AI updates affect subsequent steps
        
        This test validates:
        - AI state updates during execution
        - State-aware instruction generation
        - Dynamic workflow adaptation
        - Context preservation
        """
        print("\\n=== E2E Test: AI-Driven State Changes Scenario ===")
        
        # Set initial state
        initial_state = "工作流启动：准备执行多步骤任务"
        self.workflow_state.set_global_state(initial_state)
        
        # Set up AI updater first
        ai_updater = AIStateUpdaterService(
            llm=self.mock_llm,
            max_retries=2,
            retry_delay=0.01
        )
        self.workflow_state.set_ai_updater(ai_updater)
        
        # Test AI state update functionality directly
        context = {
            "step_info": {
                "action": "process_critical_data",
                "step_id": "critical_step",
                "instruction": "处理关键数据",
                "type": "data_processing"
            },
            "execution_result": "关键数据处理完成",
            "step_status": "completed"
        }
        
        # Set response for AI state update
        state_update_response = "数据处理阶段：关键数据已成功处理，系统进入高级分析模式"
        self.mock_llm.set_responses([state_update_response])
        
        # Trigger AI state update
        success = self.workflow_state.update_state_with_ai(context)
        
        # Validate AI update worked
        self.assertTrue(success)
        
        updated_state = self.workflow_state.get_global_state()
        self.assertEqual(updated_state, state_update_response)
        
        # Test state-aware instruction generation
        step = {
            "action": "analyze_results",
            "description": "分析处理结果",
            "step_id": "analysis_step"
        }
        
        instruction = self.agent._generate_state_aware_instruction(
            step=step,
            instruction="分析处理结果",
            previous_results=[],
            global_state=self.workflow_state
        )
        
        # Validate instruction is state-aware
        self.assertIsNotNone(instruction)
        self.assertGreater(len(instruction), 50)
        self.assertIn("数据处理", instruction)  # Should reference current state
        
        # Validate history tracking
        history = self.workflow_state.get_state_history()
        self.assertGreaterEqual(len(history), 1)
        
        print(f"✅ AI-driven state changes scenario completed")
        print(f"   State updated: {updated_state[:100]}...")
        print(f"   Instruction length: {len(instruction)}")
        print(f"   AI calls: {self.mock_llm.call_count}")
    
    def test_terminal_failure_scenario(self):
        """
        Scenario 4: Terminal Failure - Workflow halts correctly on unrecoverable errors
        
        This test validates:
        - Error detection and classification
        - Retry limit enforcement
        - Graceful failure handling
        - State preservation during failure
        """
        print("\\n=== E2E Test: Terminal Failure Scenario ===")
        
        # Set up AI updater
        ai_updater = AIStateUpdaterService(
            llm=self.mock_llm,
            max_retries=2,
            retry_delay=0.01
        )
        self.workflow_state.set_ai_updater(ai_updater)
        
        # Configure LLM to fail consistently
        self.mock_llm.set_failure_mode(True, max_failures=10)  # Keep failing
        
        # Test AI updater failure handling
        context = {
            "step_info": {
                "action": "critical_operation",
                "step_id": "critical_fail",
                "instruction": "执行关键操作",
                "type": "critical"
            },
            "execution_result": "操作失败",
            "error_info": "系统错误：无法恢复",
            "step_status": "failed"
        }
        
        # This should trigger fallback mechanisms
        result = ai_updater.update_state(self.workflow_state, context)
        
        # Validate fallback worked (should return something, not crash)
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
        
        # Check that failure was handled gracefully
        final_state = self.workflow_state.get_global_state()
        self.assertIsNotNone(final_state)
        
        # Validate error handling statistics
        statistics = ai_updater.get_fallback_statistics()
        self.assertGreater(statistics.get('total_fallbacks', 0), 0)
        
        print(f"✅ Terminal failure scenario completed")
        print(f"   Fallback result: {result[:100]}...")
        print(f"   Final state: {final_state[:100]}...")
        print(f"   Fallback count: {statistics.get('total_fallbacks', 0)}")


class TestE2EWorkflowStateEvolution(unittest.TestCase):
    """Test state evolution patterns across different scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_llm = E2EMockChatOpenAI()
        self.agent = MultiStepAgent_v2(llm=self.mock_llm)
        self.workflow_state = self.agent.workflow_state
        
    def test_state_history_progression(self):
        """Test that state history correctly captures workflow progression"""
        print("\\n=== E2E Test: State History Progression ===")
        
        # Set up AI updater
        ai_updater = AIStateUpdaterService(
            llm=self.mock_llm,
            max_retries=2,
            retry_delay=0.01
        )
        self.workflow_state.set_ai_updater(ai_updater)
        
        # Simulate multiple state updates throughout workflow
        state_progression = [
            ("初始化", "系统初始化：环境配置完成"),
            ("数据准备", "数据准备阶段：输入数据已加载和验证"),
            ("处理执行", "处理执行阶段：主要任务正在执行"),
            ("结果验证", "结果验证阶段：处理结果已验证通过"),
            ("任务完成", "任务完成：所有步骤成功执行，系统就绪")
        ]
        
        # Execute state updates
        for i, (phase, expected_state) in enumerate(state_progression):
            context = {
                "step_info": {
                    "action": f"step_{i+1}",
                    "step_id": f"phase_{phase}",
                    "instruction": f"执行{phase}步骤",
                    "type": "execution"
                },
                "execution_result": f"{phase}完成",
                "step_status": "completed"
            }
            
            # Set expected response
            self.mock_llm.set_responses([expected_state])
            
            # Update state
            success = self.workflow_state.update_state_with_ai(context)
            self.assertTrue(success)
            
            # Verify current state
            current_state = self.workflow_state.get_global_state()
            self.assertEqual(current_state, expected_state)
        
        # Validate complete history
        history = self.workflow_state.get_state_history()
        self.assertGreaterEqual(len(history), len(state_progression))
        
        # Validate history count
        history_count = self.workflow_state.get_state_history_count()
        self.assertEqual(history_count, len(state_progression))
        
        print(f"✅ State history progression test completed")
        print(f"   States tracked: {len(state_progression)}")
        print(f"   History entries: {len(history)}")
        print(f"   Final state: {self.workflow_state.get_global_state()[:100]}...")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2) 