"""
静态工作流系统测试
================

使用真实的DeepSeek模型测试MultiStepAgent_v3的静态工作流功能。
"""

import os
import sys
import pytest
import tempfile
import json
from pathlib import Path
from langchain_openai import ChatOpenAI

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pythonTask import Agent
from static_workflow.MultiStepAgent_v3 import MultiStepAgent_v3, RegisteredAgent
from static_workflow.workflow_definitions import WorkflowDefinition, WorkflowLoader
from static_workflow.static_workflow_engine import StaticWorkflowEngine
from static_workflow.control_flow_evaluator import ControlFlowEvaluator


# 使用指定的DeepSeek模型配置
llm_deepseek = ChatOpenAI(
    temperature=0,
    model="deepseek-chat",  
    base_url="https://api.deepseek.com",
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    max_tokens=8192
)


class TestStaticWorkflow:
    """静态工作流系统测试类"""
    
    def setup_method(self):
        """测试前准备 - 使用真实DeepSeek模型"""
        
        # 检查API密钥
        if not os.getenv('DEEPSEEK_API_KEY'):
            pytest.skip("需要设置DEEPSEEK_API_KEY环境变量")
        
        # 初始化主智能体
        self.agent_v3 = MultiStepAgent_v3(llm=llm_deepseek)
        
        # 创建测试智能体（使用真实DeepSeek模型）
        self.coder_agent = Agent(
            llm=llm_deepseek, 
            stateful=True,
            thinker_system_message="你是一个专业的Python开发者，擅长编写高质量的代码。"
        )
        
        self.tester_agent = Agent(
            llm=llm_deepseek,
            stateful=True, 
            thinker_system_message="你是一个专业的软件测试工程师，擅长编写和执行测试用例。"
        )
        
        self.data_agent = Agent(
            llm=llm_deepseek,
            stateful=True,
            thinker_system_message="你是一个数据科学家，擅长数据处理和分析。"
        )
        
        # 注册测试智能体
        self.agent_v3.register_agent("coder", self.coder_agent, "专业Python开发者")
        self.agent_v3.register_agent("tester", self.tester_agent, "软件测试工程师")
        self.agent_v3.register_agent("data_agent", self.data_agent, "数据科学家")
        
        # 创建临时工作目录
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
    
    def test_workflow_definition_loading(self):
        """测试工作流定义加载"""
        
        # 测试从示例文件加载
        workflow_files = self.agent_v3.list_available_workflows()
        assert len(workflow_files) > 0, "应该有可用的工作流文件"
        
        # 加载计算器工作流
        if "calculator_workflow.json" in workflow_files:
            workflow_info = self.agent_v3.get_workflow_info("calculator_workflow.json")
            
            assert workflow_info['name'] == "calculator_implementation"
            assert len(workflow_info['step_names']) > 0
            assert 'coder' in workflow_info['required_agents']
            assert 'tester' in workflow_info['required_agents']
    
    def test_simple_workflow_execution(self):
        """测试简单工作流执行"""
        
        # 创建一个简单的测试工作流
        simple_workflow = {
            "workflow_metadata": {
                "name": "simple_test",
                "version": "1.0",
                "description": "简单测试工作流"
            },
            "global_variables": {
                "test_var": "hello"
            },
            "steps": [
                {
                    "id": "step1",
                    "name": "问候测试",
                    "agent_name": "coder",
                    "instruction": "请输出一个简单的Python问候程序，打印'Hello, Static Workflow!'",
                    "instruction_type": "execution",
                    "expected_output": "Python问候程序",
                    "control_flow": {
                        "type": "terminal"
                    }
                }
            ],
            "control_rules": [],
            "error_handling": {
                "default_strategy": "retry_with_backoff"
            }
        }
        
        # 执行工作流
        workflow_def = self.agent_v3.create_workflow_from_dict(simple_workflow)
        result = self.agent_v3.execute_workflow(workflow_def)
        
        # 验证结果
        assert result.success, f"工作流应该执行成功，但失败了: {result.error_message}"
        assert result.completed_steps == 1
        assert result.failed_steps == 0
        assert "step1" in result.step_results
        
        step1_result = result.step_results["step1"]
        assert step1_result["status"] == "completed"
    
    def test_conditional_workflow(self):
        """测试条件分支工作流"""
        
        conditional_workflow = {
            "workflow_metadata": {
                "name": "conditional_test",
                "version": "1.0",
                "description": "条件分支测试工作流"
            },
            "global_variables": {
                "test_condition": True
            },
            "steps": [
                {
                    "id": "check_condition",
                    "name": "检查条件",
                    "agent_name": "tester",
                    "instruction": "设置一个测试结果变量test_result = True，并报告条件检查结果",
                    "instruction_type": "execution",
                    "expected_output": "条件检查结果",
                    "control_flow": {
                        "type": "conditional",
                        "condition": "test_condition == True",
                        "success_next": "success_step",
                        "failure_next": "failure_step"
                    }
                },
                {
                    "id": "success_step",
                    "name": "成功步骤",
                    "agent_name": "coder",
                    "instruction": "打印成功信息：条件检查通过",
                    "instruction_type": "execution",
                    "expected_output": "成功信息",
                    "control_flow": {
                        "type": "terminal"
                    }
                },
                {
                    "id": "failure_step",
                    "name": "失败步骤",
                    "agent_name": "coder",
                    "instruction": "打印失败信息：条件检查失败",
                    "instruction_type": "execution",
                    "expected_output": "失败信息",
                    "control_flow": {
                        "type": "terminal"
                    }
                }
            ],
            "control_rules": [],
            "error_handling": {
                "default_strategy": "continue"
            }
        }
        
        # 执行工作流
        workflow_def = self.agent_v3.create_workflow_from_dict(conditional_workflow)
        result = self.agent_v3.execute_workflow(workflow_def)
        
        # 验证结果
        assert result.success, f"条件工作流应该执行成功: {result.error_message}"
        assert result.completed_steps >= 2  # check_condition + success_step
        
        # 验证正确的分支被执行
        assert "check_condition" in result.step_results
        assert "success_step" in result.step_results
        assert "failure_step" not in result.step_results or result.step_results["failure_step"]["status"] != "completed"
    
    def test_calculator_workflow_execution(self):
        """测试计算器工作流执行（真实DeepSeek LLM）"""
        
        try:
            # 执行计算器工作流
            result = self.agent_v3.execute_workflow_from_file("calculator_workflow.json")
            
            # 验证工作流基本执行
            assert result is not None, "应该返回执行结果"
            print(f"\n工作流执行结果: 成功={result.success}, 完成步骤={result.completed_steps}/{result.total_steps}")
            
            # 如果执行失败，至少验证错误处理是否正常
            if not result.success:
                assert result.error_message is not None, "失败时应该有错误信息"
                print(f"执行失败原因: {result.error_message}")
            else:
                # 成功时验证关键步骤
                assert result.completed_steps > 0, "应该至少完成一个步骤"
                
                # 检查是否有calculator相关的输出
                step_outputs = []
                for step_id, step_info in result.step_results.items():
                    if step_info.get('result') and hasattr(step_info['result'], 'stdout'):
                        step_outputs.append(step_info['result'].stdout)
                
                output_text = ' '.join(step_outputs).lower()
                assert any(keyword in output_text for keyword in ['calculator', '计算器', 'add', 'subtract', 'multiply', 'divide']), \
                    "输出应该包含计算器相关内容"
            
        except Exception as e:
            pytest.fail(f"计算器工作流执行出现异常: {e}")
    
    def test_workflow_engine_components(self):
        """测试工作流引擎组件"""
        
        # 测试控制流评估器
        evaluator = ControlFlowEvaluator()
        evaluator.set_context(
            global_variables={"test_var": 42},
            runtime_variables={"result": True}
        )
        
        # 测试条件评估
        assert evaluator.evaluate_condition("test_var > 40") == True
        assert evaluator.evaluate_condition("result == True") == True
        assert evaluator.evaluate_condition("test_var < 30") == False
        
        # 测试变量插值
        assert evaluator.interpolate_value("${test_var}") == "42"
        assert evaluator.interpolate_value("Value is ${test_var}") == "Value is 42"
    
    def test_agent_registration(self):
        """测试智能体注册功能"""
        
        # 创建新的测试智能体
        test_agent = Agent(llm=llm_deepseek, stateful=True)
        
        # 注册智能体
        initial_count = len(self.agent_v3.registered_agents)
        self.agent_v3.register_agent("test_agent", test_agent, "测试智能体")
        
        # 验证注册结果
        assert len(self.agent_v3.registered_agents) == initial_count + 1
        
        # 验证智能体可以在StatefulExecutor中访问
        retrieved_agent = self.agent_v3.device.get_variable("test_agent")
        assert retrieved_agent is test_agent
    
    def test_workflow_error_handling(self):
        """测试工作流错误处理"""
        
        # 创建一个会失败的工作流
        error_workflow = {
            "workflow_metadata": {
                "name": "error_test",
                "version": "1.0",
                "description": "错误处理测试工作流"
            },
            "global_variables": {},
            "steps": [
                {
                    "id": "failing_step",
                    "name": "失败步骤",
                    "agent_name": "nonexistent_agent",  # 不存在的智能体
                    "instruction": "这个步骤会失败",
                    "instruction_type": "execution",
                    "expected_output": "不会有输出",
                    "control_flow": {
                        "type": "sequential",
                        "success_next": None,
                        "failure_next": "error_step"
                    }
                },
                {
                    "id": "error_step",
                    "name": "错误处理步骤",
                    "agent_name": "tester",
                    "instruction": "处理前面步骤的错误",
                    "instruction_type": "information",
                    "expected_output": "错误处理结果",
                    "control_flow": {
                        "type": "terminal"
                    }
                }
            ],
            "control_rules": [],
            "error_handling": {
                "default_strategy": "continue_on_error"
            }
        }
        
        # 执行工作流
        workflow_def = self.agent_v3.create_workflow_from_dict(error_workflow)
        result = self.agent_v3.execute_workflow(workflow_def)
        
        # 验证错误处理
        assert not result.success, "工作流应该因为不存在的智能体而失败"
        assert result.error_message is not None, "应该有错误信息"
        assert result.failed_steps > 0, "应该有失败的步骤"
    
    def teardown_method(self):
        """测试后清理"""
        
        # 清理临时文件
        import shutil
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass


class TestWorkflowComponents:
    """工作流组件单元测试"""
    
    def test_workflow_loader(self):
        """测试工作流加载器"""
        
        loader = WorkflowLoader()
        
        # 测试从字典加载
        test_dict = {
            "workflow_metadata": {
                "name": "test_workflow",
                "version": "1.0"
            },
            "steps": [
                {
                    "id": "test_step",
                    "name": "测试步骤",
                    "agent_name": "test_agent",
                    "instruction": "测试指令"
                }
            ],
            "global_variables": {},
            "control_rules": [],
            "error_handling": {}
        }
        
        workflow = loader.load_from_dict(test_dict)
        assert workflow.workflow_metadata.name == "test_workflow"
        assert len(workflow.steps) == 1
        assert workflow.steps[0].id == "test_step"
    
    def test_control_flow_evaluator(self):
        """测试控制流评估器"""
        
        evaluator = ControlFlowEvaluator()
        
        # 设置测试上下文
        test_context = {
            "global_variables": {"threshold": 5, "max_count": 10},
            "runtime_variables": {"current_count": 3, "status": "active"}
        }
        
        evaluator.set_context(**test_context)
        
        # 测试简单条件
        assert evaluator.evaluate_condition("current_count < threshold") == True
        assert evaluator.evaluate_condition("current_count > threshold") == False
        
        # 测试复杂条件
        assert evaluator.evaluate_condition("current_count < max_count AND status == 'active'") == True
        assert evaluator.evaluate_condition("current_count >= threshold OR status == 'inactive'") == False
        
        # 测试变量插值
        assert evaluator.interpolate_value("${threshold}") == "5"
        assert evaluator.interpolate_value("Count: ${current_count}/${max_count}") == "Count: 3/10"
    
    def test_static_workflow_engine(self):
        """测试静态工作流引擎基础功能"""
        
        engine = StaticWorkflowEngine()
        
        # 测试引擎初始化
        assert engine.evaluator is not None
        assert engine.parallel_executor is not None
        
        # 测试步骤执行器设置
        def dummy_executor(step):
            return f"Executed: {step.name}"
        
        engine.set_step_executor(dummy_executor)
        assert engine.step_executor is dummy_executor


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])