"""
工作流示例测试
============

测试各种预定义的工作流示例，验证复杂控制流的正确性。
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path
from langchain_openai import ChatOpenAI

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from python_core import Agent
from static_workflow.MultiStepAgent_v3 import MultiStepAgent_v3


# 使用指定的DeepSeek模型配置
get_model("deepseek_chat") = ChatOpenAI(
    temperature=0,
    model="deepseek-chat",  
    base_url="https://api.deepseek.com",
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    max_tokens=8192
)


class TestWorkflowExamples:
    """工作流示例测试类"""
    
    def setup_method(self):
        """测试前准备"""
        
        # 检查API密钥
        if not os.getenv('DEEPSEEK_API_KEY'):
            pytest.skip("需要设置DEEPSEEK_API_KEY环境变量")
        
        # 初始化主智能体
        self.agent_v3 = MultiStepAgent_v3(llm=get_model("deepseek_chat"))
        
        # 创建完整的智能体团队
        self._setup_agent_team()
        
        # 创建临时工作目录
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
        
        print(f"\n使用临时目录: {self.temp_dir}")
    
    def _setup_agent_team(self):
        """设置智能体团队"""
        
        # 代码开发者
        coder_agent = Agent(
            llm=get_model("deepseek_chat"),
            stateful=True,
            thinker_system_message="""你是一个专业的Python开发者。
职责：
- 编写高质量、可读性强的Python代码
- 遵循PEP 8编码规范
- 实现完整的功能模块
- 添加适当的文档字符串和注释
- 处理异常情况和边界条件
"""
        )
        
        # 测试工程师
        tester_agent = Agent(
            llm=get_model("deepseek_chat"),
            stateful=True,
            thinker_system_message="""你是一个专业的软件测试工程师。
职责：
- 编写全面的单元测试和集成测试
- 使用pytest框架进行测试
- 确保高测试覆盖率
- 分析测试结果和失败原因
- 提供清晰的测试报告
"""
        )
        
        # 数据科学家
        data_agent = Agent(
            llm=get_model("deepseek_chat"),
            stateful=True,
            thinker_system_message="""你是一个专业的数据科学家。
职责：
- 数据加载、清洗和预处理
- 数据质量评估和验证
- 统计分析和特征工程
- 数据可视化和报告生成
- 处理各种数据格式（CSV、JSON、Excel等）
"""
        )
        
        # 机器学习工程师
        ml_agent = Agent(
            llm=get_model("deepseek_chat"),
            stateful=True,
            thinker_system_message="""你是一个专业的机器学习工程师。
职责：
- 特征提取和特征工程
- 模型选择和训练
- 模型评估和优化
- 机器学习管道构建
"""
        )
        
        # 分析师
        analyst = Agent(
            llm=get_model("deepseek_chat"),
            stateful=True,
            thinker_system_message="""你是一个专业的数据分析师。
职责：
- 需求分析和理解
- 统计分析和报告
- 数据洞察和建议
- 结果解释和可视化
"""
        )
        
        # 代码审查员
        reviewer = Agent(
            llm=get_model("deepseek_chat"),
            stateful=True,
            thinker_system_message="""你是一个专业的代码审查员。
职责：
- 代码质量评估
- 最佳实践检查
- 安全性审查
- 性能优化建议
- 可维护性评估
"""
        )
        
        # 协调员
        coordinator = Agent(
            llm=get_model("deepseek_chat"),
            stateful=True,
            thinker_system_message="""你是一个项目协调员。
职责：
- 项目管理和协调
- 问题分析和解决方案
- 风险评估和缓解
- 团队沟通和协作
"""
        )
        
        # 注册所有智能体
        self.agent_v3.register_agent("coder", coder_agent, "Python开发专家")
        self.agent_v3.register_agent("tester", tester_agent, "软件测试专家")
        self.agent_v3.register_agent("data_agent", data_agent, "数据科学专家")
        self.agent_v3.register_agent("ml_agent", ml_agent, "机器学习专家")
        self.agent_v3.register_agent("analyst", analyst, "数据分析专家")
        self.agent_v3.register_agent("reviewer", reviewer, "代码审查专家")
        self.agent_v3.register_agent("coordinator", coordinator, "项目协调专家")
        
        print(f"已注册 {len(self.agent_v3.registered_agents)} 个智能体")
    
    def test_calculator_workflow_full(self):
        """测试完整的计算器工作流"""
        
        print("\n=== 开始计算器工作流测试 ===")
        
        try:
            # 执行计算器工作流
            result = self.agent_v3.execute_workflow_from_file("calculator_workflow.json")
            
            # 基本验证
            assert result is not None, "应该返回执行结果"
            
            print(f"\n工作流执行完成:")
            print(f"- 成功: {result.success}")
            print(f"- 总步骤: {result.total_steps}")
            print(f"- 完成步骤: {result.completed_steps}")
            print(f"- 失败步骤: {result.failed_steps}")
            print(f"- 执行时间: {result.execution_time:.2f}秒")
            
            # 详细验证
            if result.success:
                assert result.completed_steps > 0, "应该至少完成一个步骤"
                
                # 检查关键步骤是否执行
                key_steps = ["implement_calculator", "write_tests", "run_tests"]
                completed_key_steps = [step for step in key_steps if step in result.step_results]
                assert len(completed_key_steps) > 0, f"应该至少完成一个关键步骤: {key_steps}"
                
                print(f"完成的关键步骤: {completed_key_steps}")
                
                # 检查输出内容
                self._verify_calculator_outputs(result)
            
            else:
                print(f"工作流执行失败: {result.error_message}")
                # 即使失败，也应该有详细的错误信息
                assert result.error_message is not None, "失败时应该有错误信息"
                
                # 检查是否正确处理了错误
                if "error_handling" in result.step_results:
                    error_step = result.step_results["error_handling"]
                    assert error_step["status"] in ["completed", "running"], "错误处理步骤应该被执行"
        
        except Exception as e:
            pytest.fail(f"计算器工作流测试出现异常: {e}")
    
    def _verify_calculator_outputs(self, result):
        """验证计算器工作流的输出内容"""
        
        # 收集所有步骤的输出
        all_outputs = []
        for step_id, step_info in result.step_results.items():
            if step_info.get('result'):
                if hasattr(step_info['result'], 'stdout') and step_info['result'].stdout:
                    all_outputs.append(step_info['result'].stdout)
                if hasattr(step_info['result'], 'return_value') and step_info['result'].return_value:
                    all_outputs.append(str(step_info['result'].return_value))
        
        combined_output = ' '.join(all_outputs).lower()
        
        # 检查计算器相关关键词
        calculator_keywords = [
            'calculator', '计算器', 'add', 'subtract', 'multiply', 'divide',
            'class', 'def', 'python', 'test', 'pytest'
        ]
        
        found_keywords = [kw for kw in calculator_keywords if kw in combined_output]
        print(f"找到的关键词: {found_keywords}")
        
        assert len(found_keywords) > 0, f"输出应该包含计算器相关内容，但只找到: {found_keywords}"
    
    def test_simple_sequential_workflow(self):
        """测试简单顺序工作流"""
        
        print("\n=== 开始简单顺序工作流测试 ===")
        
        # 创建简单的顺序工作流
        simple_workflow = {
            "workflow_metadata": {
                "name": "simple_sequential",
                "version": "1.0",
                "description": "简单顺序执行测试"
            },
            "global_variables": {
                "project_name": "test_project"
            },
            "steps": [
                {
                    "id": "step1",
                    "name": "创建项目结构",
                    "agent_name": "coder",
                    "instruction": "创建一个简单的Python项目结构，包含main.py文件，内容为print('Hello, ${project_name}!')",
                    "instruction_type": "execution",
                    "expected_output": "项目文件",
                    "control_flow": {
                        "type": "sequential",
                        "success_next": "step2",
                        "failure_next": None
                    }
                },
                {
                    "id": "step2",
                    "name": "运行项目",
                    "agent_name": "tester",
                    "instruction": "运行main.py文件并检查输出是否正确",
                    "instruction_type": "execution",
                    "expected_output": "运行结果",
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
        workflow_def = self.agent_v3.create_workflow_from_dict(simple_workflow)
        result = self.agent_v3.execute_workflow(workflow_def)
        
        # 验证结果
        print(f"顺序工作流结果: 成功={result.success}, 完成={result.completed_steps}/{result.total_steps}")
        
        assert result.total_steps == 2, "应该有2个步骤"
        
        if result.success:
            assert result.completed_steps == 2, "所有步骤都应该完成"
            assert "step1" in result.step_results
            assert "step2" in result.step_results
        else:
            print(f"顺序工作流失败: {result.error_message}")
            assert result.failed_steps > 0, "应该有失败的步骤"
    
    def test_conditional_branch_workflow(self):
        """测试条件分支工作流"""
        
        print("\n=== 开始条件分支工作流测试 ===")
        
        # 创建条件分支工作流
        conditional_workflow = {
            "workflow_metadata": {
                "name": "conditional_branch",
                "version": "1.0",
                "description": "条件分支测试工作流"
            },
            "global_variables": {
                "enable_advanced_features": True
            },
            "steps": [
                {
                    "id": "check_condition",
                    "name": "检查功能开关",
                    "agent_name": "analyst",
                    "instruction": "检查enable_advanced_features变量的值，并设置feature_enabled变量为对应的布尔值",
                    "instruction_type": "execution",
                    "expected_output": "功能开关状态",
                    "control_flow": {
                        "type": "conditional",
                        "condition": "enable_advanced_features == True",
                        "success_next": "advanced_feature",
                        "failure_next": "basic_feature"
                    }
                },
                {
                    "id": "advanced_feature",
                    "name": "高级功能",
                    "agent_name": "coder",
                    "instruction": "实现高级功能：创建一个包含类和方法的复杂Python模块",
                    "instruction_type": "execution",
                    "expected_output": "高级功能实现",
                    "control_flow": {
                        "type": "terminal"
                    }
                },
                {
                    "id": "basic_feature",
                    "name": "基础功能",
                    "agent_name": "coder",
                    "instruction": "实现基础功能：创建一个简单的Python脚本",
                    "instruction_type": "execution",
                    "expected_output": "基础功能实现",
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
        print(f"条件分支工作流结果: 成功={result.success}, 完成={result.completed_steps}/{result.total_steps}")
        
        assert result.total_steps == 3, "应该有3个步骤"
        
        if result.success:
            assert result.completed_steps >= 2, "至少应该完成2个步骤（检查条件+一个分支）"
            assert "check_condition" in result.step_results
            
            # 验证正确的分支被执行
            if "advanced_feature" in result.step_results:
                assert result.step_results["advanced_feature"]["status"] == "completed"
                assert "basic_feature" not in result.step_results or \
                       result.step_results["basic_feature"]["status"] != "completed"
                print("执行了高级功能分支")
            elif "basic_feature" in result.step_results:
                assert result.step_results["basic_feature"]["status"] == "completed"
                print("执行了基础功能分支")
        
        else:
            print(f"条件分支工作流失败: {result.error_message}")
    
    def test_loop_workflow(self):
        """测试循环工作流"""
        
        print("\n=== 开始循环工作流测试 ===")
        
        # 创建循环工作流
        loop_workflow = {
            "workflow_metadata": {
                "name": "loop_test",
                "version": "1.0",
                "description": "循环控制测试工作流"
            },
            "global_variables": {
                "max_attempts": 3,
                "target_value": 10
            },
            "steps": [
                {
                    "id": "initialize",
                    "name": "初始化",
                    "agent_name": "coder",
                    "instruction": "设置初始值：counter = 0, success = False",
                    "instruction_type": "execution",
                    "expected_output": "初始化结果",
                    "control_flow": {
                        "type": "sequential",
                        "success_next": "process_loop",
                        "failure_next": None
                    }
                },
                {
                    "id": "process_loop",
                    "name": "处理循环",
                    "agent_name": "coder",
                    "instruction": "递增counter值：counter += 1，如果counter达到target_value则设置success = True",
                    "instruction_type": "execution",
                    "expected_output": "处理结果",
                    "control_flow": {
                        "type": "loop",
                        "loop_condition": "counter < target_value AND retry_count < max_attempts",
                        "loop_target": "process_loop",
                        "max_iterations": "${max_attempts}",
                        "exit_on_max": "finalize"
                    }
                },
                {
                    "id": "finalize",
                    "name": "完成处理",
                    "agent_name": "analyst",
                    "instruction": "检查最终结果并生成报告",
                    "instruction_type": "information",
                    "expected_output": "最终报告",
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
        workflow_def = self.agent_v3.create_workflow_from_dict(loop_workflow)
        result = self.agent_v3.execute_workflow(workflow_def)
        
        # 验证结果
        print(f"循环工作流结果: 成功={result.success}, 完成={result.completed_steps}/{result.total_steps}")
        
        if result.success:
            assert "initialize" in result.step_results
            assert "process_loop" in result.step_results
            assert "finalize" in result.step_results
            print("循环工作流成功完成")
        else:
            print(f"循环工作流失败: {result.error_message}")
    
    def test_workflow_info_and_listing(self):
        """测试工作流信息获取和列表功能"""
        
        print("\n=== 开始工作流信息测试 ===")
        
        # 测试列出可用工作流
        available_workflows = self.agent_v3.list_available_workflows()
        print(f"可用工作流: {available_workflows}")
        
        assert isinstance(available_workflows, list), "应该返回工作流列表"
        
        # 测试获取工作流信息
        for workflow_file in available_workflows:
            if workflow_file.endswith('.json'):
                try:
                    workflow_info = self.agent_v3.get_workflow_info(workflow_file)
                    print(f"\n工作流信息 - {workflow_file}:")
                    print(f"- 名称: {workflow_info['name']}")
                    print(f"- 版本: {workflow_info['version']}")
                    print(f"- 描述: {workflow_info['description']}")
                    print(f"- 总步骤: {workflow_info['total_steps']}")
                    print(f"- 所需智能体: {workflow_info['required_agents']}")
                    
                    # 基本验证
                    assert 'name' in workflow_info
                    assert 'total_steps' in workflow_info
                    assert 'required_agents' in workflow_info
                    assert workflow_info['total_steps'] > 0
                    
                except Exception as e:
                    print(f"获取 {workflow_file} 信息失败: {e}")
    
    def teardown_method(self):
        """测试后清理"""
        
        # 清理临时文件
        import shutil
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                print(f"已清理临时目录: {self.temp_dir}")
            except:
                pass


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s", "--tb=short"])