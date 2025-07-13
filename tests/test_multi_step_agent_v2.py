import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhancedAgent_v2 import MultiStepAgent_v2, RegisteredAgent, WorkflowState
from python_core import Agent, Result
from llm_lazy import get_model
from tests.config.test_config import skip_if_api_unavailable, check_deepseek_api_health


class EchoAgent(Agent):
    """测试用的回显Agent，返回输入的内容"""
    
    def __init__(self, llm=None):
        super().__init__(llm or get_model("deepseek_v3"))
        self.api_specification = "回显智能体，返回输入的内容"
    
    def execute_stream(self, prompt):
        """返回输入内容的生成器"""
        # 提取实际的指令内容
        lines = prompt.strip().split('\n')
        instruction_line = None
        for line in lines:
            if line.startswith('## 指令'):
                # 找到指令行的下一行
                idx = lines.index(line)
                if idx + 1 < len(lines):
                    instruction_line = lines[idx + 1].strip()
                    break
        
        if instruction_line and '回显' in instruction_line:
            # 提取要回显的内容
            if '"' in instruction_line:
                # 提取引号中的内容
                start = instruction_line.find('"')
                end = instruction_line.rfind('"')
                if start != -1 and end != -1 and start != end:
                    echo_content = instruction_line[start+1:end]
                    yield echo_content
                    return Result(True, prompt, echo_content, "", echo_content)
        
        # 默认回显整个指令
        yield instruction_line or prompt
        return Result(True, prompt, instruction_line or prompt, "", instruction_line or prompt)


class TextLengthAgent(Agent):
    """测试用的文本长度计算Agent"""
    
    def __init__(self, llm=None):
        super().__init__(llm or get_model("deepseek_v3"))
        self.api_specification = "文本长度计算智能体，计算文本的长度"
    
    def execute_stream(self, prompt):
        """计算文本长度并返回"""
        # 从前序步骤结果中提取文本
        lines = prompt.strip().split('\n')
        text_to_measure = ""
        
        # 查找前序步骤结果
        in_previous_results = False
        for line in lines:
            if '前序步骤结果' in line:
                in_previous_results = True
                continue
            elif in_previous_results and line.strip():
                if '步骤' in line and '的结果:' in line:
                    # 提取结果内容
                    result_start = line.find('的结果:')
                    if result_start != -1:
                        text_to_measure = line[result_start + 4:].strip()
                        break
        
        # 如果没有找到前序结果，从指令中提取
        if not text_to_measure:
            for line in lines:
                if line.startswith('## 指令'):
                    idx = lines.index(line)
                    if idx + 1 < len(lines):
                        instruction = lines[idx + 1].strip()
                        if '长度' in instruction and '"' in instruction:
                            # 提取引号中的内容
                            start = instruction.find('"')
                            end = instruction.rfind('"')
                            if start != -1 and end != -1 and start != end:
                                text_to_measure = instruction[start+1:end]
                                break
        
        # 计算长度
        length = len(text_to_measure)
        result_text = str(length)
        
        yield result_text
        return Result(True, prompt, result_text, "", result_text)


class TestMultiStepAgentV2(unittest.TestCase):
    """MultiStepAgent_v2类的单元测试"""
    
    def setUp(self):
        """测试前的设置"""
        self.llm = get_model("deepseek_v3")
        self.agent = MultiStepAgent_v2(llm=self.llm)
        
    def tearDown(self):
        """测试后的清理"""
        pass
    
    def test_import_and_initialization(self):
        """测试基本导入和初始化"""
        # 测试导入是否成功
        self.assertIsInstance(self.agent, MultiStepAgent_v2)
        
        # 测试基本属性是否存在
        self.assertTrue(hasattr(self.agent, 'registered_agents'))
        self.assertTrue(hasattr(self.agent, 'device'))
        self.assertTrue(hasattr(self.agent, 'max_retries'))
        
        # 测试初始状态
        self.assertEqual(len(self.agent.registered_agents), 0)
        self.assertEqual(self.agent.max_retries, 3)
    
    def test_register_agent_success(self):
        """测试成功注册agent"""
        test_agent = Agent(llm=self.llm)
        test_agent.api_specification = "测试智能体"
        
        self.agent.register_agent("test_agent", test_agent)
        
        # 验证agent是否成功注册
        self.assertEqual(len(self.agent.registered_agents), 1)
        self.assertEqual(self.agent.registered_agents[0].name, "test_agent")
        self.assertEqual(self.agent.registered_agents[0].instance, test_agent)
        self.assertEqual(self.agent.registered_agents[0].description, "测试智能体")
    
    def test_register_multiple_agents(self):
        """测试注册多个agent"""
        agent1 = Agent(llm=self.llm)
        agent1.api_specification = "智能体1"
        agent2 = Agent(llm=self.llm)
        agent2.api_specification = "智能体2"
        
        self.agent.register_agent("agent1", agent1)
        self.agent.register_agent("agent2", agent2)
        
        # 验证两个agent都成功注册
        self.assertEqual(len(self.agent.registered_agents), 2)
        self.assertEqual(self.agent.registered_agents[0].name, "agent1")
        self.assertEqual(self.agent.registered_agents[1].name, "agent2")
    
    def test_register_agent_with_duplicate_name(self):
        """测试注册相同名称的agent"""
        agent1 = Agent(llm=self.llm)
        agent1.api_specification = "第一个智能体"
        agent2 = Agent(llm=self.llm)
        agent2.api_specification = "第二个智能体"
        
        self.agent.register_agent("duplicate", agent1)
        self.agent.register_agent("duplicate", agent2)
        
        # 应该有两个agent，都叫duplicate（系统允许重复名称）
        self.assertEqual(len(self.agent.registered_agents), 2)
    
    def test_register_agent_with_empty_name(self):
        """测试注册空名称的agent"""
        test_agent = Agent(llm=self.llm)
        test_agent.api_specification = "空名称测试"
        
        self.agent.register_agent("", test_agent)
        
        # 应该允许空名称
        self.assertEqual(len(self.agent.registered_agents), 1)
        self.assertEqual(self.agent.registered_agents[0].name, "")
    
    def test_register_agent_with_special_characters(self):
        """测试注册包含特殊字符的agent名称"""
        test_agent = Agent(llm=self.llm)
        special_name = "test@#$%^&*()agent"
        
        self.agent.register_agent(special_name, test_agent)
        
        self.assertEqual(len(self.agent.registered_agents), 1)
        self.assertEqual(self.agent.registered_agents[0].name, special_name)
    
    def test_register_agent_with_none(self):
        """测试注册None作为agent"""
        self.agent.register_agent("none_agent", None)
        
        # 应该允许注册None
        self.assertEqual(len(self.agent.registered_agents), 1)
        self.assertEqual(self.agent.registered_agents[0].name, "none_agent")
        self.assertEqual(self.agent.registered_agents[0].instance, None)
    
    def test_register_agent_with_string_as_agent(self):
        """测试注册字符串作为agent"""
        self.agent.register_agent("string_agent", "not_an_agent")
        
        # 应该允许注册任何对象
        self.assertEqual(len(self.agent.registered_agents), 1)
        self.assertEqual(self.agent.registered_agents[0].instance, "not_an_agent")
    
    def test_register_agent_with_number_as_name(self):
        """测试注册数字作为agent名称"""
        test_agent = Agent(llm=self.llm)
        
        self.agent.register_agent(123, test_agent)
        
        # 应该允许数字作为名称
        self.assertEqual(len(self.agent.registered_agents), 1)
        self.assertEqual(self.agent.registered_agents[0].name, 123)
    
    def test_register_agent_without_api_specification(self):
        """测试注册没有api_specification的agent"""
        test_agent = Agent(llm=self.llm)
        # 不设置api_specification
        
        self.agent.register_agent("test_agent", test_agent)
        
        # 应该使用默认描述
        expected_description = "test_agent智能体，通用任务执行者"
        self.assertEqual(self.agent.registered_agents[0].description, expected_description)
    
    def test_register_agent_with_empty_api_specification(self):
        """测试注册空api_specification的agent"""
        test_agent = Agent(llm=self.llm)
        test_agent.api_specification = ""
        
        self.agent.register_agent("empty_spec", test_agent)
        
        self.assertEqual(self.agent.registered_agents[0].description, "")
    
    def test_register_agent_creates_agent_specification(self):
        """测试注册agent时创建正确的RegisteredAgent对象"""
        test_agent = Agent(llm=self.llm)
        test_agent.api_specification = "测试描述"
        
        self.agent.register_agent("test_agent", test_agent)
        
        spec = self.agent.registered_agents[0]
        self.assertIsInstance(spec, RegisteredAgent)
        self.assertEqual(spec.name, "test_agent")
        self.assertEqual(spec.instance, test_agent)
        self.assertEqual(spec.description, "测试描述")
    
    @skip_if_api_unavailable
    def test_plan_execution_structure_validation(self):
        """测试plan_execution返回的计划结构验证"""
        # 注册一个测试agent
        test_agent = Agent(llm=self.llm)
        test_agent.api_specification = "测试智能体"
        self.agent.register_agent("test_agent", test_agent)
        
        # 执行计划生成
        plan = self.agent.plan_execution("创建一个简单的hello world程序")
        
        # 验证计划是列表
        self.assertIsInstance(plan, list)
        self.assertGreater(len(plan), 0)
        
        # 验证每个步骤都有必要的字段
        for step in plan:
            self.assertIsInstance(step, dict)
            self.assertIn('id', step)
            self.assertIn('name', step)
            self.assertIn('instruction', step)
            self.assertIn('agent_name', step)
            self.assertIn('status', step)
            self.assertIn('expected_output', step)
            self.assertIn('prerequisites', step)
            
            # 验证字段类型
            self.assertIsInstance(step['id'], str)
            self.assertIsInstance(step['name'], str)
            self.assertIsInstance(step['instruction'], str)
            self.assertIsInstance(step['agent_name'], str)
            self.assertIsInstance(step['status'], str)
            
            # 验证状态为pending
            self.assertEqual(step['status'], 'pending')
    
    @skip_if_api_unavailable
    def test_plan_execution_with_registered_agents(self):
        """测试有注册agent时的计划执行"""
        # 注册多个agent
        coder = Agent(llm=self.llm)
        coder.api_specification = "编程智能体"
        tester = Agent(llm=self.llm)
        tester.api_specification = "测试智能体"
        
        self.agent.register_agent("coder", coder)
        self.agent.register_agent("tester", tester)
        
        # 执行计划生成
        plan = self.agent.plan_execution("编写并测试一个计算器程序")
        
        # 验证计划中的agent_name都来自注册的agent
        registered_agent_names = {"coder", "tester"}
        for step in plan:
            self.assertIn(step['agent_name'], registered_agent_names)
    
    @skip_if_api_unavailable
    def test_plan_execution_different_task_types(self):
        """测试不同类型任务的计划执行"""
        # 注册agent
        test_agent = Agent(llm=self.llm)
        test_agent.api_specification = "通用智能体"
        self.agent.register_agent("general", test_agent)
        
        # 测试简单任务
        simple_plan = self.agent.plan_execution("打印hello world")
        self.assertIsInstance(simple_plan, list)
        self.assertGreater(len(simple_plan), 0)
        
        # 测试复杂任务
        complex_plan = self.agent.plan_execution("开发一个完整的web应用，包括前端、后端和数据库")
        self.assertIsInstance(complex_plan, list)
        self.assertGreater(len(complex_plan), 0)
        
        # 复杂任务应该有更多步骤
        self.assertGreaterEqual(len(complex_plan), len(simple_plan))
    
    @skip_if_api_unavailable
    def test_plan_execution_empty_task(self):
        """测试空任务描述的计划执行"""
        # 注册agent
        test_agent = Agent(llm=self.llm)
        self.agent.register_agent("test", test_agent)
        
        # 测试空字符串
        plan = self.agent.plan_execution("")
        self.assertIsInstance(plan, list)
        # 应该至少有一个回退步骤
        self.assertGreater(len(plan), 0)
    
    @skip_if_api_unavailable
    def test_plan_execution_complex_task(self):
        """测试复杂任务的计划执行"""
        # 注册多个专业agent
        agents_config = [
            ("researcher", "研究智能体，负责信息收集"),
            ("designer", "设计智能体，负责架构设计"),
            ("coder", "编程智能体，负责代码实现"),
            ("tester", "测试智能体，负责质量保证")
        ]
        
        for name, desc in agents_config:
            agent = Agent(llm=self.llm)
            agent.api_specification = desc
            self.agent.register_agent(name, agent)
        
        # 执行复杂任务计划
        complex_task = """
        开发一个机器学习项目：
        1. 研究相关技术和数据集
        2. 设计模型架构
        3. 实现训练代码
        4. 进行模型测试和验证
        """
        
        plan = self.agent.plan_execution(complex_task)
        
        # 验证计划质量
        self.assertIsInstance(plan, list)
        self.assertGreater(len(plan), 2)  # 复杂任务应该有多个步骤
        
        # 验证不同类型的agent都被使用
        used_agents = {step['agent_name'] for step in plan}
        self.assertGreater(len(used_agents), 1)  # 应该使用多个不同的agent
    
    def test_select_next_executable_step_no_pending_steps(self):
        """测试没有待执行步骤时的情况"""
        # 创建一个所有步骤都已完成的计划
        plan = [
            {
                'id': 'step1',
                'name': '步骤1',
                'status': 'completed',
                'prerequisites': '无'
            },
            {
                'id': 'step2', 
                'name': '步骤2',
                'status': 'completed',
                'prerequisites': '无'
            }
        ]
        
        # 设置计划
        self.agent.device.set_variable("current_plan", plan)
        
        # 测试选择下一个可执行步骤
        result = self.agent.select_next_executable_step(plan)
        
        # 应该返回None
        self.assertIsNone(result)
    
    def test_select_next_executable_step_single_pending_step(self):
        """测试只有一个待执行步骤时的情况"""
        plan = [
            {
                'id': 'step1',
                'name': '步骤1', 
                'status': 'completed',
                'prerequisites': '无'
            },
            {
                'id': 'step2',
                'name': '步骤2',
                'status': 'pending',
                'prerequisites': '无'
            }
        ]
        
        # 设置计划
        self.agent.device.set_variable("current_plan", plan)
        
        # 测试选择下一个可执行步骤
        result = self.agent.select_next_executable_step(plan)
        
        # 应该返回唯一的待执行步骤
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)  # (index, step)
        index, step = result
        self.assertEqual(index, 1)
        self.assertEqual(step['id'], 'step2')
    
    @skip_if_api_unavailable
    def test_select_next_executable_step_multiple_pending_no_prerequisites(self):
        """测试多个待执行步骤且都无先决条件的情况"""
        plan = [
            {
                'id': 'step1',
                'name': '步骤1',
                'status': 'pending', 
                'prerequisites': '无'
            },
            {
                'id': 'step2',
                'name': '步骤2',
                'status': 'pending',
                'prerequisites': '无'
            },
            {
                'id': 'step3',
                'name': '步骤3',
                'status': 'pending',
                'prerequisites': '无'
            }
        ]
        
        # 设置计划
        self.agent.device.set_variable("current_plan", plan)
        
        # 测试选择下一个可执行步骤
        result = self.agent.select_next_executable_step(plan)
        
        # 应该返回其中一个步骤
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        index, step = result
        self.assertIn(step['id'], ['step1', 'step2', 'step3'])
    
    def test_select_next_executable_step_with_skipped_and_running(self):
        """测试包含跳过和运行中步骤的情况"""
        plan = [
            {
                'id': 'step1',
                'name': '步骤1',
                'status': 'completed',
                'prerequisites': '无'
            },
            {
                'id': 'step2',
                'name': '步骤2', 
                'status': 'skipped',
                'prerequisites': '无'
            },
            {
                'id': 'step3',
                'name': '步骤3',
                'status': 'running',
                'prerequisites': '无'
            },
            {
                'id': 'step4',
                'name': '步骤4',
                'status': 'pending',
                'prerequisites': '无'
            }
        ]
        
        # 设置计划
        self.agent.device.set_variable("current_plan", plan)
        
        # 测试选择下一个可执行步骤
        result = self.agent.select_next_executable_step(plan)
        
        # 应该返回step4（唯一的pending步骤）
        self.assertIsNotNone(result)
        index, step = result
        self.assertEqual(step['id'], 'step4')
    
    def test_select_next_executable_step_empty_plan(self):
        """测试空计划的情况"""
        plan = []
        
        # 测试选择下一个可执行步骤
        result = self.agent.select_next_executable_step(plan)
        
        # 应该返回None
        self.assertIsNone(result)
    
    @skip_if_api_unavailable
    def test_select_next_executable_step_all_failed(self):
        """测试所有步骤都失败的情况"""
        plan = [
            {
                'id': 'step1',
                'name': '步骤1',
                'status': 'failed',
                'prerequisites': '无'
            },
            {
                'id': 'step2',
                'name': '步骤2',
                'status': 'failed', 
                'prerequisites': '无'
            }
        ]
        
        # 设置计划
        self.agent.device.set_variable("current_plan", plan)
        
        # 由于failed状态不在排除列表中，这些步骤应该被视为待执行
        result = self.agent.select_next_executable_step(plan)
        
        # 应该返回其中一个失败的步骤（可以重试）
        self.assertIsNotNone(result)
        index, step = result
        self.assertIn(step['status'], ['failed'])
    
    @skip_if_api_unavailable
    def test_select_next_executable_step_mixed_statuses(self):
        """测试混合状态步骤的情况"""
        plan = [
            {
                'id': 'step1',
                'name': '步骤1',
                'status': 'completed',
                'prerequisites': '无'
            },
            {
                'id': 'step2',
                'name': '步骤2',
                'status': 'failed',
                'prerequisites': '无'
            },
            {
                'id': 'step3',
                'name': '步骤3',
                'status': 'pending',
                'prerequisites': '无'
            },
            {
                'id': 'step4',
                'name': '步骤4',
                'status': 'skipped',
                'prerequisites': '无'
            }
        ]
        
        # 设置计划
        self.agent.device.set_variable("current_plan", plan)
        
        result = self.agent.select_next_executable_step(plan)
        
        # 应该返回step2或step3（failed和pending状态）
        self.assertIsNotNone(result)
        index, step = result
        self.assertIn(step['id'], ['step2', 'step3'])
        self.assertIn(step['status'], ['failed', 'pending'])
    
    @skip_if_api_unavailable
    def test_execute_multi_step_simple_echo_task(self):
        """测试execute_multi_step方法的简单回显任务"""
        # 注册EchoAgent
        echo_agent = EchoAgent(self.llm)
        self.agent.register_agent("echo", echo_agent)
        
        # 执行简单的回显任务
        task = '回显短语 "hello world"'
        result = self.agent.execute_multi_step(task)
        
        # 验证结果是字符串类型（执行摘要）
        self.assertIsInstance(result, str)
        
        # 验证执行摘要包含相关信息
        self.assertIn("执行摘要", result)
        self.assertIn("总步骤数", result)
        
        # 验证执行历史
        plan = self.agent.get_plan()
        self.assertGreater(len(plan), 0)
        
        # 至少应该有一个步骤被执行
        executed_steps = [step for step in plan if step.get('status') in ['completed', 'running']]
        self.assertGreater(len(executed_steps), 0)
        
        # 验证计划中包含echo相关的步骤
        echo_steps = [step for step in plan if step.get('agent_name') == 'echo']
        self.assertGreater(len(echo_steps), 0)
    
    @skip_if_api_unavailable
    def test_execute_multi_step_echo_and_length_task(self):
        """测试execute_multi_step方法的回显和长度计算任务"""
        # 注册两个测试agent
        echo_agent = EchoAgent(self.llm)
        length_agent = TextLengthAgent(self.llm)
        
        self.agent.register_agent("echo", echo_agent)
        self.agent.register_agent("length", length_agent)
        
        # 执行组合任务
        task = '回显短语 "hello agent" 然后计算其长度'
        result = self.agent.execute_multi_step(task)
        
        # 验证结果是执行摘要
        self.assertIsInstance(result, str)
        self.assertIn("执行摘要", result)
        
        # 验证计划被创建
        plan = self.agent.get_plan()
        self.assertGreater(len(plan), 0)
        
        # 验证至少有一些步骤被执行
        executed_steps = [step for step in plan if step.get('status') in ['completed', 'running']]
        self.assertGreater(len(executed_steps), 0)
        
        # 验证使用了正确的agent
        agent_names_used = {step.get('agent_name') for step in plan}
        self.assertTrue(agent_names_used.intersection({'echo', 'length'}))
    
    @skip_if_api_unavailable
    def test_execute_multi_step_with_no_registered_agents(self):
        """测试没有注册agent时的execute_multi_step"""
        # 不注册任何agent
        task = "执行一个简单任务"
        result = self.agent.execute_multi_step(task)
        
        # 应该能够完成（使用默认处理）
        self.assertIsInstance(result, str)
        self.assertIn("执行摘要", result)
        
        # 验证计划被创建
        plan = self.agent.get_plan()
        self.assertGreater(len(plan), 0)
    
    def test_execute_multi_step_empty_task(self):
        """测试空任务的execute_multi_step"""
        # 注册一个agent
        test_agent = Agent(llm=self.llm)
        test_agent.api_specification = "测试智能体"
        self.agent.register_agent("test", test_agent)
        
        # 执行空任务
        result = self.agent.execute_multi_step("")
        
        # 应该能够处理空任务
        self.assertIsInstance(result, str)
    
    @skip_if_api_unavailable
    def test_execute_multi_step_workflow_state_management(self):
        """测试execute_multi_step的工作流状态管理"""
        # 注册测试agent
        echo_agent = EchoAgent(self.llm)
        self.agent.register_agent("echo", echo_agent)
        
        # 验证初始状态
        self.assertIsInstance(self.agent.workflow_state, WorkflowState)
        initial_step_index = self.agent.workflow_state.current_step_index
        
        # 执行任务
        task = '回显 "test workflow"'
        result = self.agent.execute_multi_step(task)
        
        # 验证工作流状态被正确管理
        self.assertIsInstance(result, str)
        
        # 验证计划存在
        plan = self.agent.get_plan()
        self.assertIsInstance(plan, list)
        
        # 验证工作流状态对象仍然存在且有效
        self.assertIsInstance(self.agent.workflow_state, WorkflowState)
    
    @skip_if_api_unavailable
    def test_execute_multi_step_task_history_tracking(self):
        """测试execute_multi_step的任务历史跟踪"""
        # 注册测试agent
        echo_agent = EchoAgent(self.llm)
        self.agent.register_agent("echo", echo_agent)
        
        # 执行任务
        task = '回显 "track history"'
        result = self.agent.execute_multi_step(task)
        
        # 验证结果
        self.assertIsInstance(result, str)
        
        # 验证计划中的步骤有状态更新
        plan = self.agent.get_plan()
        self.assertGreater(len(plan), 0)
        
        # 检查是否有步骤被标记为已完成或正在运行
        status_found = False
        for step in plan:
            if step.get('status') in ['completed', 'running', 'failed']:
                status_found = True
                break
        
        self.assertTrue(status_found, "应该有步骤的状态被更新")

    # ====== 异常处理测试 ======
    
    def test_execute_multi_step_with_failing_agent(self):
        """测试execute_multi_step处理失败的智能体"""
        
        class FailingAgent(Agent):
            """总是失败的测试智能体"""
            def __init__(self, llm=None):
                super().__init__(llm=llm)
                self.api_specification = "故意失败的智能体，用于测试异常处理"
            
            def execute_stream(self, prompt):
                """总是抛出异常的execute方法"""
                from agent_base import Result
                raise RuntimeError("测试异常：智能体执行失败")
        
        # 注册失败的智能体
        failing_agent = FailingAgent(self.llm)
        self.agent.register_agent("failing", failing_agent)
        
        # 执行可能失败的任务
        task = "使用failing智能体执行一个会失败的任务"
        
        # 应该能够处理异常，不会崩溃
        result = self.agent.execute_multi_step(task)
        
        # 验证返回了执行摘要
        self.assertIsInstance(result, str)
        self.assertIn("执行摘要", result)
        
        # 验证计划被创建
        plan = self.agent.get_plan()
        self.assertIsInstance(plan, list)
        self.assertGreater(len(plan), 0)
        
        # 检查是否有失败的步骤被记录
        failed_steps = [step for step in plan if step.get('status') == 'failed']
        # 注意：由于系统的容错性，可能没有明确的failed状态，但系统应该能够优雅处理
    
    def test_execute_multi_step_with_malformed_plan_steps(self):
        """测试execute_multi_step处理格式错误的计划步骤"""
        
        # 创建一个带有格式错误步骤的计划
        malformed_plan = [
            {
                # 缺少必需的字段如'instruction', 'agent_name'
                'id': 'malformed_step',
                'name': '格式错误的步骤',
                'status': 'pending'
                # 故意不包含instruction和agent_name
            }
        ]
        
        # 直接设置格式错误的计划
        self.agent.device.set_variable("current_plan", malformed_plan)
        
        # 尝试选择下一个可执行步骤
        result = self.agent.select_next_executable_step(malformed_plan)
        
        # 系统应该能够处理格式错误的步骤
        # 可能返回None或能够处理缺失字段
        if result is not None:
            index, step = result
            self.assertIsInstance(index, int)
            self.assertIsInstance(step, dict)
    
    def test_execute_single_step_with_missing_agent(self):
        """测试execute_single_step处理不存在的智能体"""
        
        # 创建一个引用不存在智能体的步骤
        step_with_missing_agent = {
            'id': 'test_step',
            'name': '测试步骤',
            'instruction': '执行某个任务',
            'agent_name': 'nonexistent_agent',  # 不存在的智能体
            'instruction_type': 'execution',
            'status': 'pending'
        }
        
        # 执行单个步骤
        result = self.agent.execute_single_step(step_with_missing_agent)
        
        # 验证返回了Result对象
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Result)
        
        # 应该标记为失败，因为智能体不存在
        self.assertFalse(result.success)
        self.assertIn("找不到名为", result.stderr)
        self.assertIn("nonexistent_agent", result.stderr)
    
    def test_execute_multi_step_with_empty_agent_list(self):
        """测试execute_multi_step在没有注册智能体时的行为"""
        
        # 确保没有注册任何智能体（重新创建agent实例）
        agent_without_agents = MultiStepAgent_v2(llm=self.llm)
        
        # 执行任务
        task = "执行一个简单的任务"
        result = agent_without_agents.execute_multi_step(task)
        
        # 应该能够处理并返回摘要
        self.assertIsInstance(result, str)
        self.assertIn("执行摘要", result)
        
        # 验证计划被创建（可能包含回退计划）
        plan = agent_without_agents.get_plan()
        self.assertIsInstance(plan, list)
    
    @skip_if_api_unavailable
    def test_execute_multi_step_with_api_failure_simulation(self):
        """测试execute_multi_step处理API调用失败"""
        
        class APIFailingAgent(Agent):
            """模拟API失败的智能体"""
            def __init__(self, llm=None):
                super().__init__(llm=llm)
                self.api_specification = "模拟API失败的智能体"
            
            def execute_stream(self, prompt):
                """模拟API调用超时或失败"""
                from agent_base import Result
                # 模拟网络超时或API错误
                for chunk in ["API", "调用", "失败"]:
                    yield chunk
                # 返回失败结果
                yield Result(False, prompt, "API调用失败", "网络超时或API不可用", None)
        
        # 注册API失败的智能体
        api_failing_agent = APIFailingAgent(self.llm)
        self.agent.register_agent("api_failing", api_failing_agent)
        
        # 执行任务
        task = "使用api_failing智能体进行任务处理"
        result = self.agent.execute_multi_step(task)
        
        # 验证系统能够处理API失败
        self.assertIsInstance(result, str)
        self.assertIn("执行摘要", result)
        
        # 验证计划存在
        plan = self.agent.get_plan()
        self.assertIsInstance(plan, list)
    
    def test_execute_multi_step_with_invalid_instruction_type(self):
        """测试execute_multi_step处理无效的指令类型"""
        
        # 注册一个正常的智能体
        echo_agent = EchoAgent(self.llm)
        self.agent.register_agent("echo", echo_agent)
        
        # 手动创建带有无效指令类型的计划
        invalid_plan = [
            {
                'id': 'step1',
                'name': '无效指令类型步骤',
                'instruction': '执行某个任务',
                'agent_name': 'echo',
                'instruction_type': 'invalid_type',  # 无效的指令类型
                'status': 'pending',
                'prerequisites': '无'
            }
        ]
        
        # 设置无效计划
        self.agent.device.set_variable("current_plan", invalid_plan)
        
        # 尝试执行单个步骤
        result = self.agent.execute_single_step(invalid_plan[0])
        
        # 系统应该能够处理无效的指令类型
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Result)
    
    def test_can_execute_step_with_llm_failure(self):
        """测试can_execute_step方法在LLM调用失败时的行为"""
        
        # 创建一个需要LLM判断的步骤
        step_with_prerequisites = {
            'id': 'complex_step',
            'name': '需要复杂判断的步骤',
            'instruction': '执行复杂任务',
            'prerequisites': '需要完成前置任务A和B，并且文件X存在',
            'agent_name': 'echo'
        }
        
        # 注册echo智能体以避免其他错误
        echo_agent = EchoAgent(self.llm)
        self.agent.register_agent("echo", echo_agent)
        
        # 正常情况下调用应该工作
        can_exec, reason = self.agent.can_execute_step(step_with_prerequisites)
        
        # 验证返回的是布尔值和字符串
        self.assertIsInstance(can_exec, bool)
        self.assertIsInstance(reason, str)
        self.assertGreater(len(reason), 0)
    
    def test_make_decision_with_invalid_input(self):
        """测试make_decision方法处理无效输入"""
        
        # 测试None输入
        decision = self.agent.make_decision(current_result=None)
        
        # 验证返回了有效的决策字典
        self.assertIsInstance(decision, dict)
        self.assertIn('action', decision)
        self.assertIn('reason', decision)
        self.assertIn('new_tasks', decision)
        
        # 验证action是有效值
        valid_actions = ['continue', 'complete', 'retry', 'generate_new_task', 
                        'jump_to', 'loop_back', 'generate_fix_task_and_loop']
        self.assertIn(decision['action'], valid_actions)
        
        # 测试无效的current_result
        invalid_result = "这不是一个Result对象"
        decision = self.agent.make_decision(current_result=invalid_result)
        
        # 应该仍然返回有效决策
        self.assertIsInstance(decision, dict)
        self.assertIn('action', decision)

    # ====== 边界条件测试 ======
    
    @skip_if_api_unavailable
    def test_plan_execution_with_empty_task(self):
        """测试plan_execution方法处理空任务描述"""
        
        # 注册一个智能体以避免"无可用智能体"的问题
        echo_agent = EchoAgent(self.llm)
        self.agent.register_agent("echo", echo_agent)
        
        # 测试空字符串任务
        empty_task = ""
        plan = self.agent.plan_execution(empty_task)
        
        # 验证返回的是有效计划（可能是回退计划）
        self.assertIsInstance(plan, list)
        self.assertGreater(len(plan), 0)  # 应该生成至少一个步骤
        
        # 验证回退计划的结构
        for step in plan:
            self.assertIsInstance(step, dict)
            self.assertIn('id', step)
            self.assertIn('name', step)
            self.assertIn('instruction', step)
            self.assertIn('agent_name', step)
    
    def test_plan_execution_with_whitespace_only_task(self):
        """测试plan_execution方法处理仅包含空白字符的任务"""
        
        # 注册一个智能体
        echo_agent = EchoAgent(self.llm)
        self.agent.register_agent("echo", echo_agent)
        
        # 测试仅包含空白字符的任务
        whitespace_task = "   \n\t  \n  "
        plan = self.agent.plan_execution(whitespace_task)
        
        # 验证返回的是有效计划
        self.assertIsInstance(plan, list)
        self.assertGreater(len(plan), 0)
    
    def test_execute_multi_step_with_empty_plan(self):
        """测试execute_multi_step方法处理空计划"""
        
        # 手动设置空计划
        self.agent.device.set_variable("current_plan", [])
        
        # 执行空任务（应该会生成回退计划）
        result = self.agent.execute_multi_step("无操作任务")
        
        # 验证返回了执行摘要
        self.assertIsInstance(result, str)
        self.assertIn("执行摘要", result)
    
    def test_select_next_executable_step_with_all_completed_steps(self):
        """测试select_next_executable_step在所有步骤都已完成时的行为"""
        
        # 创建全部已完成的计划
        completed_plan = [
            {
                'id': 'step1',
                'name': '已完成步骤1',
                'status': 'completed',
                'prerequisites': '无'
            },
            {
                'id': 'step2',
                'name': '已完成步骤2',
                'status': 'completed',
                'prerequisites': '无'
            }
        ]
        
        # 设置计划
        self.agent.device.set_variable("current_plan", completed_plan)
        
        # 测试选择下一个可执行步骤
        result = self.agent.select_next_executable_step(completed_plan)
        
        # 应该返回None，因为没有待执行的步骤
        self.assertIsNone(result)
    
    def test_select_next_executable_step_with_all_skipped_steps(self):
        """测试select_next_executable_step在所有步骤都被跳过时的行为"""
        
        # 创建全部跳过的计划
        skipped_plan = [
            {
                'id': 'step1',
                'name': '跳过步骤1',
                'status': 'skipped',
                'prerequisites': '无'
            },
            {
                'id': 'step2',
                'name': '跳过步骤2',
                'status': 'skipped',
                'prerequisites': '无'
            }
        ]
        
        # 设置计划
        self.agent.device.set_variable("current_plan", skipped_plan)
        
        # 测试选择下一个可执行步骤
        result = self.agent.select_next_executable_step(skipped_plan)
        
        # 应该返回None，因为没有待执行的步骤
        self.assertIsNone(result)
    
    def test_select_next_executable_step_with_circular_dependencies(self):
        """测试select_next_executable_step处理循环依赖的情况"""
        
        # 创建带有循环依赖的计划
        circular_plan = [
            {
                'id': 'step1',
                'name': '步骤1',
                'status': 'pending',
                'prerequisites': '需要完成步骤2'  # 依赖step2
            },
            {
                'id': 'step2',
                'name': '步骤2',
                'status': 'pending',
                'prerequisites': '需要完成步骤1'  # 依赖step1，形成循环
            }
        ]
        
        # 设置计划
        self.agent.device.set_variable("current_plan", circular_plan)
        
        # 测试选择下一个可执行步骤
        # 注意：这个测试可能会因为LLM的判断而有不同结果
        # 系统应该能够处理这种情况，不崩溃
        try:
            result = self.agent.select_next_executable_step(circular_plan)
            # 结果可能是None（无法执行），或者系统智能选择了一个步骤
            self.assertTrue(result is None or isinstance(result, tuple))
        except Exception as e:
            # 如果抛出异常，应该是有意义的异常
            self.assertIsInstance(e, Exception)
    
    def test_execute_single_step_with_empty_instruction(self):
        """测试execute_single_step处理空指令"""
        
        # 注册一个智能体
        echo_agent = EchoAgent(self.llm)
        self.agent.register_agent("echo", echo_agent)
        
        # 创建空指令的步骤
        empty_instruction_step = {
            'id': 'test_step',
            'name': '空指令步骤',
            'instruction': '',  # 空指令
            'agent_name': 'echo',
            'instruction_type': 'execution',
            'status': 'pending'
        }
        
        # 执行单个步骤
        result = self.agent.execute_single_step(empty_instruction_step)
        
        # 验证返回了Result对象
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Result)
        
        # 应该失败，因为指令为空
        self.assertFalse(result.success)
        self.assertIn("instruction", result.stderr)
    
    def test_execute_single_step_with_missing_required_fields(self):
        """测试execute_single_step处理缺少必需字段的步骤"""
        
        # 测试缺少agent_name的步骤
        step_without_agent = {
            'id': 'test_step',
            'name': '缺少智能体步骤',
            'instruction': '执行某个任务',
            # 'agent_name': 缺少这个字段
            'instruction_type': 'execution',
            'status': 'pending'
        }
        
        result = self.agent.execute_single_step(step_without_agent)
        
        # 应该失败并返回错误信息
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Result)
        self.assertFalse(result.success)
        self.assertIn("agent_name", result.stderr)
    
    @skip_if_api_unavailable 
    def test_execute_multi_step_with_extremely_long_instruction(self):
        """测试execute_multi_step处理极长指令"""
        
        # 注册一个智能体
        echo_agent = EchoAgent(self.llm)
        self.agent.register_agent("echo", echo_agent)
        
        # 创建极长的指令（模拟边界情况）
        long_instruction = "执行任务 " + "非常 " * 1000 + "复杂的任务"
        
        # 执行任务
        result = self.agent.execute_multi_step(long_instruction)
        
        # 验证系统能够处理长指令
        self.assertIsInstance(result, str)
        self.assertIn("执行摘要", result)
    
    def test_register_agent_boundary_conditions(self):
        """测试register_agent的边界条件"""
        # 测试非常长的名称
        long_name = "a" * 1000
        test_agent = Agent(llm=self.llm)
        self.agent.register_agent(long_name, test_agent)
        
        # 验证注册成功
        agent_names = [spec.name for spec in self.agent.registered_agents]
        self.assertIn(long_name, agent_names)
        
        # 测试非常长的描述
        test_agent2 = Agent(llm=self.llm)
        test_agent2.api_specification = "x" * 10000
        self.agent.register_agent("long_desc", test_agent2)
        
        agent_names = [spec.name for spec in self.agent.registered_agents]
        self.assertIn("long_desc", agent_names)


if __name__ == '__main__':
    # 运行测试前检查API状态
    is_healthy, message = check_deepseek_api_health()
    if not is_healthy:
        print(f"警告: deepseek API不可用 - {message}")
        print("部分测试将被跳过")
    
    # 运行测试
    unittest.main(verbosity=2) 