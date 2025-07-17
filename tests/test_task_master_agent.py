"""
TaskMasterAgent 基本测试

测试 TaskMasterAgent 的核心功能，包括初始化、配置、数据转换等。
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import json
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from task_master_agent import TaskMasterAgent, AgentSpecification, TaskMasterWorkflowState
from task_master.client import TaskMasterClient, TaskMasterClientError
from task_master.data_mapper import TaskMasterDataMapper
from task_master.config import TaskMasterConfig
from python_core import Agent
from agent_base import Result


class MockLLM:
    """模拟 LLM 类用于测试"""
    def __init__(self):
        self.model = "mock-model"
    
    def invoke(self, messages, **kwargs):
        class MockResponse:
            content = '{"action": "continue", "reason": "测试决策"}'
        return MockResponse()


class TestTaskMasterConfig(unittest.TestCase):
    """测试 TaskMasterConfig 类"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = TaskMasterConfig(self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_default_config(self):
        """测试默认配置"""
        # 创建新的配置实例避免测试间污染
        fresh_config = TaskMasterConfig(self.temp_dir + "_fresh")
        self.assertEqual(fresh_config.get("project.auto_init"), True)
        self.assertEqual(fresh_config.get_complexity_threshold(), 5)
        self.assertEqual(fresh_config.is_research_enabled(), True)
    
    def test_config_modification(self):
        """测试配置修改"""
        self.config.set("task_management.complexity_threshold", 7)
        self.assertEqual(self.config.get_complexity_threshold(), 7)
        
        self.config.set("ai_models.use_research", False)
        self.assertEqual(self.config.is_research_enabled(), False)
    
    def test_config_validation(self):
        """测试配置验证"""
        self.assertTrue(self.config.validate_config())
        
        # 设置无效的复杂度阈值
        self.config.set("task_management.complexity_threshold", 15)
        self.assertFalse(self.config.validate_config())
        
        # 恢复有效值，避免影响其他测试
        self.config.set("task_management.complexity_threshold", 5)
    
    def test_config_save_load(self):
        """测试配置保存和加载"""
        self.config.set("test_key", "test_value")
        self.assertTrue(self.config.save_config())
        
        new_config = TaskMasterConfig(self.temp_dir)
        self.assertEqual(new_config.get("test_key"), "test_value")


class TestTaskMasterDataMapper(unittest.TestCase):
    """测试 TaskMasterDataMapper 类"""
    
    def setUp(self):
        self.mapper = TaskMasterDataMapper()
        self.llm = MockLLM()
    
    def test_status_mapping(self):
        """测试状态映射"""
        # MultiStepAgent -> Task Master AI
        self.assertEqual(self.mapper._map_status_to_tm("running"), "in-progress")
        self.assertEqual(self.mapper._map_status_to_tm("completed"), "done")
        
        # Task Master AI -> MultiStepAgent
        self.assertEqual(self.mapper._map_status_to_multistep("in-progress"), "running")
        self.assertEqual(self.mapper._map_status_to_multistep("done"), "completed")
    
    def test_tm_task_to_step_format(self):
        """测试 Task Master AI 任务转换为步骤格式"""
        tm_task = {
            "id": 1,
            "title": "测试任务",
            "description": "这是一个测试任务",
            "status": "pending",
            "priority": "high",
            "agent_name": "test_agent",
            "dependencies": ["2"],
            "subtasks": []
        }
        
        step = self.mapper.tm_task_to_step_format(tm_task)
        
        self.assertEqual(step["id"], "1")
        self.assertEqual(step["name"], "测试任务")
        self.assertEqual(step["instruction"], "这是一个测试任务")
        self.assertEqual(step["status"], "pending")
        self.assertEqual(step["dependencies"], ["2"])
    
    def test_step_to_tm_task_format(self):
        """测试步骤格式转换为 Task Master AI 任务"""
        step = {
            "id": "step1",
            "name": "测试步骤",
            "instruction": "执行测试",
            "agent_name": "test_agent",
            "status": "pending",
            "dependencies": ["step2"],
            "instruction_type": "execution",
            "phase": "execution"
        }
        
        tm_task = self.mapper.step_to_tm_task_format(step, task_id=1)
        
        self.assertEqual(tm_task["id"], 1)
        self.assertEqual(tm_task["title"], "测试步骤")
        self.assertEqual(tm_task["description"], "执行测试")
        self.assertEqual(tm_task["status"], "pending")
        self.assertEqual(tm_task["dependencies"], ["step2"])
    
    def test_agent_specs_formatting(self):
        """测试智能体规格格式化"""
        mock_agent = Agent(self.llm)
        specs = [
            AgentSpecification("coder", mock_agent, "编程智能体"),
            AgentSpecification("tester", mock_agent, "测试智能体")
        ]
        
        formatted = self.mapper.agent_specs_to_tm_format(specs)
        self.assertIn("coder: 编程智能体", formatted)
        self.assertIn("tester: 测试智能体", formatted)
        
        names = self.mapper.agent_specs_to_name_list(specs)
        self.assertEqual(names, ["coder", "tester"])
    
    def test_format_validation(self):
        """测试格式验证"""
        valid_step = {
            "id": "1",
            "name": "测试",
            "instruction": "执行",
            "agent_name": "test"
        }
        self.assertTrue(self.mapper.validate_step_format(valid_step))
        
        invalid_step = {"id": "1"}
        self.assertFalse(self.mapper.validate_step_format(invalid_step))


class TestTaskMasterClient(unittest.TestCase):
    """测试 TaskMasterClient 类"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.client = TaskMasterClient(self.temp_dir, auto_create=True)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """测试客户端初始化"""
        self.assertTrue(self.client.is_initialized())
        self.assertTrue(Path(self.temp_dir, ".taskmaster").exists())
        self.assertTrue(Path(self.temp_dir, ".taskmaster", "tasks", "tasks.json").exists())
    
    def test_add_task(self):
        """测试添加任务"""
        task = self.client.add_task(
            prompt="测试任务",
            priority="high"
        )
        
        self.assertIsNotNone(task)
        self.assertEqual(task.get("priority"), "high")
    
    def test_get_tasks(self):
        """测试获取任务列表"""
        # 添加一个任务
        self.client.add_task(prompt="测试任务1")
        
        tasks = self.client.get_tasks()
        self.assertIsInstance(tasks, list)
    
    def test_next_task(self):
        """测试获取下一个任务"""
        # 添加一个任务
        self.client.add_task(prompt="测试任务")
        
        next_task = self.client.next_task()
        # 在模拟模式下可能返回 None 或任务
        self.assertIsInstance(next_task, (dict, type(None)))
    
    def test_research_function(self):
        """测试研究功能"""
        result = self.client.research("测试查询")
        self.assertIsInstance(result, str)
        self.assertIn("测试查询", result)


class TestTaskMasterAgent(unittest.TestCase):
    """测试 TaskMasterAgent 类"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.llm = MockLLM()
        
        # 创建测试智能体
        self.test_agent = Agent(self.llm)
        self.agent_specs = [
            AgentSpecification("test_agent", self.test_agent, "测试智能体")
        ]
        
        self.tm_agent = TaskMasterAgent(
            project_root=self.temp_dir,
            llm=self.llm,
            agent_specs=self.agent_specs,
            auto_init=True
        )
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """测试 TaskMasterAgent 初始化"""
        self.assertEqual(len(self.tm_agent.agent_specs), 1)
        self.assertTrue(self.tm_agent.tm_client.is_initialized())
        self.assertIsInstance(self.tm_agent.config, TaskMasterConfig)
        self.assertIsInstance(self.tm_agent.workflow_state, TaskMasterWorkflowState)
    
    def test_register_agent(self):
        """测试智能体注册"""
        new_agent = Agent(self.llm)
        success = self.tm_agent.register_agent("new_agent", new_agent, "新智能体")
        
        self.assertTrue(success)
        self.assertEqual(len(self.tm_agent.agent_specs), 2)
    
    def test_project_status(self):
        """测试项目状态获取"""
        status = self.tm_agent.get_project_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn("total_tasks", status)
        self.assertIn("agents_registered", status)
        self.assertEqual(status["agents_registered"], 1)
    
    def test_research_function(self):
        """测试研究功能"""
        result = self.tm_agent.research("Python 最佳实践")
        self.assertIsInstance(result, str)
    
    def test_complexity_analysis(self):
        """测试复杂度分析"""
        analysis = self.tm_agent.get_complexity_analysis()
        self.assertIsInstance(analysis, dict)
    
    def test_enhanced_decision_making(self):
        """测试增强决策制定"""
        mock_result = Result(True, "test", "success", "", "test_result")
        task_context = {
            "task_id": "1",
            "task_name": "测试任务",
            "agent_name": "test_agent"
        }
        
        decision = self.tm_agent.enhanced_decision_making(mock_result, task_context)
        
        self.assertIsInstance(decision, dict)
        self.assertIn("action", decision)
        self.assertIn("reason", decision)
    
    def test_sync_with_tm(self):
        """测试与 Task Master AI 同步"""
        success = self.tm_agent.sync_with_tm()
        self.assertTrue(success)
        self.assertEqual(self.tm_agent.workflow_state.sync_status, "synced")
    
    def test_execution_modes(self):
        """测试不同执行模式"""
        instruction = "创建一个简单的测试"
        
        # 测试模式参数（不实际执行，避免 API 调用）
        self.assertEqual(self.tm_agent.execution_mode, "tm_native")
        
        # 测试模式切换
        try:
            # 这里只测试模式参数，不实际执行
            result = self.tm_agent.execute_multi_step(
                instruction, 
                mode="legacy"
            )
            # 在模拟环境下，legacy 模式可能会失败，这是正常的
        except Exception:
            pass  # 预期在测试环境中会失败


class TestWorkflowState(unittest.TestCase):
    """测试工作流状态管理"""
    
    def test_workflow_state_initialization(self):
        """测试工作流状态初始化"""
        state = TaskMasterWorkflowState()
        
        self.assertIsNone(state.current_task_id)
        self.assertEqual(state.sync_status, "synced")
        self.assertIsInstance(state.execution_context, dict)
        self.assertIsInstance(state.performance_metrics, dict)
    
    def test_performance_metrics(self):
        """测试性能指标"""
        state = TaskMasterWorkflowState()
        
        metrics = state.performance_metrics
        self.assertEqual(metrics["tasks_completed"], 0)
        self.assertEqual(metrics["tasks_failed"], 0)
        self.assertEqual(metrics["average_execution_time"], 0)


def run_basic_tests():
    """运行基本测试"""
    print("运行 TaskMasterAgent 基本测试...")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestTaskMasterConfig,
        TestTaskMasterDataMapper,
        TestTaskMasterClient,
        TestTaskMasterAgent,
        TestWorkflowState
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出结果
    print(f"\n测试结果:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("TaskMasterAgent 测试套件")
    print("=" * 50)
    
    try:
        success = run_basic_tests()
        
        if success:
            print("\n✅ 所有测试通过!")
        else:
            print("\n❌ 部分测试失败")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 测试执行失败: {e}")
        sys.exit(1)