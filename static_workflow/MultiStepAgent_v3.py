"""
MultiStepAgent_v3 - 静态工作流智能体
===================================

基于静态工作流架构的多步骤智能体，采用预定义的声明式控制流。
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime as dt

# 添加父目录到路径以导入现有模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_base import Result, reduce_memory_decorator_compress
from pythonTask import Agent
from langchain_core.language_models import BaseChatModel
from result_evaluator import TestResultEvaluator, MockTestResultEvaluator

from .workflow_definitions import WorkflowDefinition, WorkflowStep, WorkflowLoader
from .static_workflow_engine import StaticWorkflowEngine, WorkflowExecutionResult
from .control_flow_evaluator import ControlFlowEvaluator

logger = logging.getLogger(__name__)


class RegisteredAgent:
    """存储已注册的智能体信息"""
    def __init__(self, name: str, instance: Agent, description: str):
        self.name = name
        self.instance = instance
        self.description = description


class MultiStepAgent_v3(Agent):
    """
    静态工作流多步骤智能体
    
    采用声明式控制流架构，通过预定义的工作流配置文件
    实现确定性的高性能执行。
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        registered_agents: Optional[List[RegisteredAgent]] = None,
        max_retries: int = 3,
        thinker_system_message: Optional[str] = None,
        thinker_chat_system_message: Optional[str] = None,
        max_parallel_workers: int = 4,
        workflow_base_path: str = None,
        planning_prompt_template: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        use_mock_evaluator: bool = False
    ):
        """
        初始化静态工作流智能体
        
        Args:
            llm: 语言模型实例
            registered_agents: 已注册的智能体列表
            max_retries: 最大重试次数
            thinker_system_message: 思考者系统消息
            thinker_chat_system_message: 思考者聊天系统消息
            max_parallel_workers: 最大并行工作进程数
            workflow_base_path: 工作流配置文件基础路径
            planning_prompt_template: 自定义规划提示模板
            deepseek_api_key: DeepSeek API密钥，用于智能测试结果判断
            use_mock_evaluator: 是否使用模拟评估器（开发/测试用）
        """
        
        # 使用默认的系统消息
        if thinker_system_message is None:
            thinker_system_message = """
你是一个静态工作流执行智能体，负责按照预定义的工作流配置执行复杂的多步骤任务。

核心职责：
1. 严格按照工作流定义执行步骤
2. 调用相应的智能体执行具体任务
3. 处理步骤间的数据传递和状态管理
4. 执行预定义的控制流逻辑（条件分支、循环、并行）

执行原则：
- 高效：无运行时LLM决策，按预定义路径执行
- 确定：所有控制流路径在设计时确定
- 可靠：完整的错误处理和重试机制
- 可追踪：详细的执行日志和状态记录
"""
        
        super().__init__(
            llm=llm,
            stateful=True,
            thinker_system_message=thinker_system_message,
            thinker_chat_system_message=thinker_chat_system_message,
            max_retries=max_retries
        )
        
        # 初始化智能结果评估器
        if use_mock_evaluator or not deepseek_api_key:
            self.result_evaluator = MockTestResultEvaluator()
            logger.info("使用模拟测试结果评估器")
        else:
            self.result_evaluator = TestResultEvaluator(api_key=deepseek_api_key)
            logger.info("使用DeepSeek智能测试结果评估器")
        
        # 初始化核心组件（传递AI评估器给工作流引擎）
        self.registered_agents = registered_agents if registered_agents is not None else []
        self.max_retries = max_retries
        self.workflow_engine = StaticWorkflowEngine(max_parallel_workers, ai_evaluator=self.result_evaluator)
        self.workflow_loader = WorkflowLoader()
        
        # 设置工作流配置基础路径
        if workflow_base_path is None:
            self.workflow_base_path = Path(__file__).parent / "workflow_examples"
        else:
            self.workflow_base_path = Path(workflow_base_path)
        
        # 注册智能体到StatefulExecutor变量空间
        for spec in self.registered_agents:
            self.device.set_variable(spec.name, spec.instance)
        
        # 设置工作流引擎的步骤执行器
        self.workflow_engine.set_step_executor(self._execute_single_step)
        
        # 设置引擎回调
        self.workflow_engine.on_step_start = self._on_step_start
        self.workflow_engine.on_step_complete = self._on_step_complete
        self.workflow_engine.on_step_failed = self._on_step_failed
        self.workflow_engine.on_workflow_complete = self._on_workflow_complete
        
        # 设置规划提示模板
        self.planning_prompt_template = planning_prompt_template or self._get_default_planning_template()
        
        logger.debug(f"MultiStepAgent_v3 初始化完成，注册了 {len(self.registered_agents)} 个智能体")
    
    def register_agent(self, name: str, instance: Agent, description: str = None) -> None:
        """
        注册智能体
        
        Args:
            name: 智能体名称
            instance: 智能体实例
            description: 智能体描述
        """
        if description is None:
            description = getattr(instance, 'api_specification', f"{name}智能体，通用任务执行者")
        
        spec = RegisteredAgent(name=name, instance=instance, description=description)
        self.registered_agents.append(spec)
        self.device.set_variable(name, instance)
        
        logger.debug(f"已注册智能体: {name}")
    
    def execute_workflow_from_file(self, 
                                 workflow_file: Union[str, Path],
                                 initial_variables: Dict[str, Any] = None) -> WorkflowExecutionResult:
        """
        从文件加载并执行工作流
        
        Args:
            workflow_file: 工作流配置文件路径
            initial_variables: 初始变量
            
        Returns:
            工作流执行结果
        """
        
        # 处理相对路径
        if not Path(workflow_file).is_absolute():
            workflow_file = self.workflow_base_path / workflow_file
        
        try:
            # 加载工作流定义
            workflow_definition = self.workflow_loader.load_from_file(str(workflow_file))
            
            # 执行工作流
            return self.execute_workflow(workflow_definition, initial_variables)
            
        except Exception as e:
            logger.error(f"执行工作流文件失败 {workflow_file}: {e}")
            raise
    
    def execute_workflow(self, 
                        workflow_definition: WorkflowDefinition,
                        initial_variables: Dict[str, Any] = None) -> WorkflowExecutionResult:
        """
        执行工作流定义
        
        Args:
            workflow_definition: 工作流定义
            initial_variables: 初始变量
            
        Returns:
            工作流执行结果
        """
        
        try:
            logger.info(f"开始执行静态工作流: {workflow_definition.workflow_metadata.name}")
            
            # 验证智能体可用性
            self._validate_agents_availability(workflow_definition)
            
            # 设置当前工作流定义供执行历史使用
            self.workflow_definition = workflow_definition
            
            # 执行工作流
            result = self.workflow_engine.execute_workflow(workflow_definition, initial_variables)
            
            # 记录执行结果
            if result.success:
                logger.info(f"工作流执行成功: {workflow_definition.workflow_metadata.name}")
                logger.info(f"完成步骤: {result.completed_steps}/{result.total_steps}")
                logger.info(f"执行时间: {result.execution_time:.2f}秒")
            else:
                logger.error(f"工作流执行失败: {workflow_definition.workflow_metadata.name}")
                logger.error(f"错误信息: {result.error_message}")
            
            return result
            
        except Exception as e:
            logger.error(f"工作流执行异常: {e}")
            raise
    
    def create_workflow_from_dict(self, workflow_dict: Dict[str, Any]) -> WorkflowDefinition:
        """
        从字典创建工作流定义
        
        Args:
            workflow_dict: 工作流配置字典
            
        Returns:
            工作流定义对象
        """
        return self.workflow_loader.load_from_dict(workflow_dict)
    
    def save_workflow_to_file(self, 
                             workflow_definition: WorkflowDefinition,
                             file_path: Union[str, Path]) -> None:
        """
        保存工作流定义到文件
        
        Args:
            workflow_definition: 工作流定义
            file_path: 保存路径
        """
        
        # 处理相对路径
        if not Path(file_path).is_absolute():
            file_path = self.workflow_base_path / file_path
        
        self.workflow_loader.save_to_file(workflow_definition, str(file_path))
    
    def list_available_workflows(self) -> List[str]:
        """
        列出可用的工作流配置文件
        
        Returns:
            工作流文件列表
        """
        
        if not self.workflow_base_path.exists():
            return []
        
        workflow_files = []
        for file_path in self.workflow_base_path.glob("*.json"):
            workflow_files.append(file_path.name)
        for file_path in self.workflow_base_path.glob("*.yml"):
            workflow_files.append(file_path.name)
        for file_path in self.workflow_base_path.glob("*.yaml"):
            workflow_files.append(file_path.name)
        
        return sorted(workflow_files)
    
    def get_workflow_info(self, workflow_file: Union[str, Path]) -> Dict[str, Any]:
        """
        获取工作流基本信息
        
        Args:
            workflow_file: 工作流文件路径
            
        Returns:
            工作流信息字典
        """
        
        # 处理相对路径
        if not Path(workflow_file).is_absolute():
            workflow_file = self.workflow_base_path / workflow_file
        
        try:
            workflow_definition = self.workflow_loader.load_from_file(str(workflow_file))
            
            return {
                'name': workflow_definition.workflow_metadata.name,
                'version': workflow_definition.workflow_metadata.version,
                'description': workflow_definition.workflow_metadata.description,
                'author': workflow_definition.workflow_metadata.author,
                'total_steps': len(workflow_definition.steps),
                'step_names': [step.name for step in workflow_definition.steps],
                'required_agents': list(set(step.agent_name for step in workflow_definition.steps)),
                'global_variables': list(workflow_definition.global_variables.keys()),
                'control_rules_count': len(workflow_definition.control_rules)
            }
            
        except Exception as e:
            logger.error(f"获取工作流信息失败 {workflow_file}: {e}")
            raise
    
    def _validate_agents_availability(self, workflow_definition: WorkflowDefinition) -> None:
        """验证所需智能体是否已注册"""
        
        registered_agent_names = {spec.name for spec in self.registered_agents}
        required_agent_names = {step.agent_name for step in workflow_definition.steps}
        
        missing_agents = required_agent_names - registered_agent_names
        if missing_agents:
            raise ValueError(f"缺少所需的智能体: {', '.join(missing_agents)}")
    
    def _execute_single_step(self, step: WorkflowStep) -> Result:
        """
        执行单个工作流步骤
        
        Args:
            step: 工作流步骤定义
            
        Returns:
            执行结果
        """
        
        agent_name = step.agent_name
        instruction = step.instruction
        instruction_type = step.instruction_type
        
        try:
            # 查找指定的智能体
            target_agent = None
            for spec in self.registered_agents:
                if spec.name == agent_name:
                    target_agent = spec.instance
                    break
            
            if target_agent is None:
                raise ValueError(f"找不到名为 '{agent_name}' 的智能体")
            
            # 构建包含执行历史的指令
            enhanced_instruction = self._build_enhanced_instruction(step)
            
            # 根据指令类型执行
            if instruction_type == "information":
                # 信息性任务，使用chat_sync
                result = target_agent.chat_sync(enhanced_instruction)
            else:
                # 执行性任务，使用execute_sync
                result = target_agent.execute_sync(enhanced_instruction)
            
            return result
            
        except Exception as e:
            error_msg = f"步骤执行失败 {step.id}: {e}"
            logger.error(error_msg)
            return Result(False, instruction, "", error_msg)
    
    def evaluate_condition_with_ai(self, condition: str, last_result: Result) -> bool:
        """
        使用AI智能评估条件表达式
        
        Args:
            condition: 条件表达式
            last_result: 上一步的执行结果
            
        Returns:
            bool: 条件是否满足
        """
        
        try:
            # 检查是否是AI智能评估条件
            if "ai_evaluate_test_result" in condition:
                logger.info(f"使用AI评估测试结果: {condition}")
                
                # 使用智能评估器判断测试结果
                evaluation = self.result_evaluator.evaluate_test_result(
                    result_code=getattr(last_result, 'code', None),
                    result_stdout=getattr(last_result, 'stdout', None),
                    result_stderr=getattr(last_result, 'stderr', None),
                    result_return_value=getattr(last_result, 'return_value', None)
                )
                
                result = evaluation["passed"]
                logger.info(f"AI评估结果: {'通过' if result else '失败'} (置信度: {evaluation['confidence']:.2f})")
                logger.debug(f"评估理由: {evaluation['reason']}")
                
                return result
            
            # 检查是否是传统的success条件
            elif "last_result.success" in condition:
                # 传统条件评估
                if condition == "last_result.success == True":
                    return getattr(last_result, 'success', False)
                elif condition == "last_result.success == False":
                    return not getattr(last_result, 'success', False)
            
            # 其他自定义条件可以在这里扩展
            else:
                logger.warning(f"未识别的条件类型: {condition}")
                # 默认返回success状态
                return getattr(last_result, 'success', False)
                
        except Exception as e:
            logger.error(f"条件评估失败: {e}")
            # 出错时返回保守结果
            return False
    
    def _on_step_start(self, step: WorkflowStep) -> None:
        """步骤开始回调"""
        print(f"\n🚀 开始执行步骤: {step.name} ({step.id})")
        if step.expected_output:
            print(f"   预期输出: {step.expected_output}")
    
    def _on_step_complete(self, step: WorkflowStep, result: Any) -> None:
        """步骤完成回调"""
        success_indicator = "✅" if (result and getattr(result, 'success', False)) else "❌"
        print(f"{success_indicator} 步骤完成: {step.name}")
        
        # 显示简要结果信息
        if result and hasattr(result, 'stdout') and result.stdout:
            output_preview = result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout
            print(f"   输出: {output_preview}")
    
    def _on_step_failed(self, step: WorkflowStep, error: Exception) -> None:
        """步骤失败回调"""
        print(f"❌ 步骤失败: {step.name}")
        print(f"   错误: {error}")
        
        # 如果有重试，显示重试信息
        if step.retry_count < step.max_retries:
            print(f"   将进行第 {step.retry_count + 1} 次重试...")
    
    def _on_workflow_complete(self, result: WorkflowExecutionResult) -> None:
        """工作流完成回调"""
        if result.success:
            print(f"\n🎉 工作流执行成功!")
        else:
            print(f"\n💥 工作流执行失败!")
        
        print(f"总步骤: {result.total_steps}")
        print(f"完成步骤: {result.completed_steps}")
        print(f"失败步骤: {result.failed_steps}")
        print(f"跳过步骤: {result.skipped_steps}")
        print(f"执行时间: {result.execution_time:.2f}秒")
    
    #TODO: 返回值应该是Result类型
    @reduce_memory_decorator_compress
    def execute_multi_step(self, main_instruction: str, interactive: bool = False) -> str:
        """
        多步骤任务执行主入口方法（标准接口兼容）
        
        基于主指令调用LLM生成静态工作流配置，然后执行。
        
        Args:
            main_instruction: 主任务指令
            interactive: 是否交互模式（静态工作流中暂不支持）
            
        Returns:
            执行摘要字符串
        """
        
        try:
            logger.info(f"开始执行多步骤任务: {main_instruction}")
            
            # 步骤1: 调用LLM生成工作流规划
            logger.info("生成工作流规划...")
            workflow_definition = self._generate_workflow_plan(main_instruction)
            
            # 步骤2: 从指令中提取初始变量
            initial_variables = self._extract_variables_from_instruction(main_instruction)
            
            # 步骤3: 执行动态生成的工作流
            logger.info(f"执行生成的工作流，包含 {len(workflow_definition.steps)} 个步骤")
            result = self.execute_workflow(workflow_definition, initial_variables)
            
            # 步骤4: 生成执行摘要
            return self._generate_dynamic_execution_summary(main_instruction, workflow_definition, result)
            
        except Exception as e:
            error_summary = f"""
## 多步骤任务执行失败

**主指令**: {main_instruction}
**错误**: {str(e)}

### 可能的解决方案
1. 检查指令是否清晰明确
2. 确认所需智能体是否已注册
3. 检查LLM生成的工作流是否有效

### 已注册智能体
{', '.join([spec.name for spec in self.registered_agents])}

### 可用工作流模板
{', '.join(self.list_available_workflows())}
"""
            logger.error(f"多步骤任务执行失败: {e}")
            return error_summary
    
    
    def _match_workflow_for_instruction(self, instruction: str) -> str:
        """
        根据指令智能匹配最合适的工作流文件
        
        Args:
            instruction: 用户指令
            
        Returns:
            工作流文件名
        """
        
        instruction_lower = instruction.lower()
        
        # 简单的关键词匹配策略
        if any(keyword in instruction_lower for keyword in ['计算器', 'calculator', '加法', '减法', '乘法', '除法']):
            return 'calculator_workflow.json'
        elif any(keyword in instruction_lower for keyword in ['数据处理', 'data processing', '数据分析', 'data analysis']):
            return 'data_processing.json'
        elif any(keyword in instruction_lower for keyword in ['代码', 'code', '测试', 'test', '编程', 'programming']):
            return 'code_test_workflow.json'
        else:
            # 默认使用计算器工作流（作为示例）
            available_workflows = self.list_available_workflows()
            if available_workflows:
                return available_workflows[0]
            else:
                raise ValueError("没有可用的工作流配置文件")
    
    def _extract_variables_from_instruction(self, instruction: str) -> Dict[str, Any]:
        """
        从指令中提取可能的初始变量
        
        Args:
            instruction: 用户指令
            
        Returns:
            提取的变量字典
        """
        
        variables = {
            'user_instruction': instruction,
            'execution_time': dt.now().isoformat()
        }
        
        # 可以添加更复杂的变量提取逻辑
        # 例如解析指令中的参数、文件名等
        
        return variables
    
    def _get_default_planning_template(self) -> str:
        """获取默认的规划提示模板"""
        return """
# 任务背景
你是一个静态工作流生成器，负责将用户的自然语言指令转换为结构化的静态工作流配置。
你需要分析任务需求，将其分解为可以静态执行的步骤序列，并为每个步骤设计合适的控制流。

# 可用智能体列表
{available_agents_str}

# 主任务指令
{main_instruction}

# 工作流设计原则
1. **静态性**: 所有控制流决策在设计时确定，不依赖运行时LLM判断
2. **确定性**: 相同输入产生相同的执行路径
3. **高效性**: 避免不必要的LLM调用，专注于任务执行
4. **完整性**: 包含错误处理、重试和验证机制

# 步骤分解要求
请将主任务分解为有序的步骤，每个步骤包含:
1. id: 步骤唯一标识符 (如 "step1", "step2", "validate_result" 等)
2. name: 简短的步骤名称
3. instruction: 详细的执行指令，需要清晰明确
4. agent_name: 执行该步骤的智能体名称，必须从以下列表中选择: {available_agent_names}
5. instruction_type: 指令类型 ("execution" 执行代码任务 / "information" 信息查询任务)
6. expected_output: 预期输出描述
7. timeout: 超时时间（秒），可选
8. max_retries: 最大重试次数，默认为2
9. control_flow: 控制流配置（可选，见下方说明）

# 控制流类型说明
- sequential: 顺序执行（默认）
- conditional: 条件分支，基于上一步结果决定下一步
- loop: 循环执行，用于重复执行某些步骤直到满足条件
- parallel: 并行执行多个步骤
- terminal: 终止节点

# 重要：循环控制与步骤重试的区别
- **步骤重试**：单个步骤失败时的自动重试机制，由 `max_retries` 控制
- **工作流循环**：多个步骤之间的循环流程，由 `loop_condition` 控制
- 不要将这两个概念混合使用！

# 控制流配置示例

## conditional类型 - 条件分支
支持两种配置方式：

### 方式1：AI布尔字段（推荐）
```json
"control_flow": {{
  "type": "conditional",
  "ai_evaluate_test_result": true,
  "ai_confidence_threshold": 0.8,
  "ai_fallback_condition": "last_result.success == True",
  "success_next": "next_step_id",
  "failure_next": "error_handling_step"
}}
```

### 方式2：传统条件表达式
```json
"control_flow": {{
  "type": "conditional", 
  "condition": "ai_evaluate_test_result == True",
  "success_next": "next_step_id",
  "failure_next": "error_handling_step"
}}
```

# AI评估配置说明
- `ai_evaluate_test_result`: true/false，是否启用AI智能评估测试结果
- `ai_confidence_threshold`: 0.0-1.0，AI评估置信度阈值，低于此值将使用fallback条件
- `ai_fallback_condition`: 当AI评估失败或置信度不够时的回退条件
- 字符串条件 `"ai_evaluate_test_result == True"`: 兼容旧版本的字符串方式
- 传统条件 `"last_result.success == True"`: 仅判断步骤是否成功执行

# 条件配置建议
1. 对于测试、验证、构建等步骤，优先使用AI布尔字段方式
2. 简单场景用布尔字段，复杂场景可组合条件表达式
3. 始终设置fallback条件确保可靠性

## loop类型 - 循环控制
```json
"control_flow": {{
  "type": "loop",
  "loop_condition": null,
  "loop_target": "step3", 
  "max_iterations": 3,
  "exit_on_max": "error_handling"
}}
```

# 循环控制最佳实践
- **推荐方式**：使用 `max_iterations` 设置循环次数上限，`loop_condition` 设为 null
- **设置出口**：必须设置 `exit_on_max` 指定达到最大迭代次数后的跳转步骤
- **避免复杂条件**：不要使用复杂的工作流状态变量（如 `workflow_state.fix_attempts`）
- **保持简单**：优先使用引擎内置的循环控制机制
- 区分步骤重试（`max_retries`）和工作流循环（`max_iterations`）

# 输出格式
必须严格按照以下JSON格式输出完整的工作流配置:
```json
{{
  "workflow_metadata": {{
    "name": "dynamic_workflow_task",
    "version": "1.0", 
    "description": "基于用户指令动态生成的工作流",
    "author": "MultiStepAgent_v3"
  }},
  "global_variables": {{
    "max_retries": 3,
    "timeout": 300
  }},
  "steps": [
    {{
      "id": "step1",
      "name": "步骤名称",
      "agent_name": "{first_agent_name}",
      "instruction": "详细的执行指令...",
      "instruction_type": "execution",
      "expected_output": "预期输出",
      "timeout": 120,
      "max_retries": 2,
      "control_flow": {{
        "type": "sequential",
        "success_next": "step2",
        "failure_next": "error_handling"
      }}
    }}
  ],
  "control_rules": [
    {{
      "trigger": "execution_time > 600",
      "action": "terminate",
      "target": "error_handling",
      "priority": 1
    }}
  ],
  "error_handling": {{
    "default_strategy": "retry_with_analysis"
  }}
}}
```

# 重要提示
- 每个步骤都要指定合适的智能体
- 确保步骤之间的数据流动清晰
- 为可能失败的步骤设计重试和错误处理
- 条件表达式使用 `last_result.success` 判断上一步是否成功
- 步骤指令要详细具体，便于智能体理解和执行
"""

    def _generate_workflow_plan(self, main_instruction: str) -> WorkflowDefinition:
        """
        调用LLM生成工作流规划
        
        Args:
            main_instruction: 主任务指令
            
        Returns:
            工作流定义对象
        """
        
        # 准备智能体信息
        available_agents_str = "\\n".join([
            f"- {spec.name}: {spec.description}" 
            for spec in self.registered_agents
        ])
        
        available_agent_names = [spec.name for spec in self.registered_agents]
        first_agent_name = available_agent_names[0] if available_agent_names else "智能体名称"
        
        # 格式化规划提示
        planning_prompt = self.planning_prompt_template.format(
            available_agents_str=available_agents_str,
            main_instruction=main_instruction,
            available_agent_names=', '.join(available_agent_names),
            first_agent_name=first_agent_name
        )
        
        logger.debug(f"生成规划提示，长度: {len(planning_prompt)} 字符")
        
        try:
            # 使用JSON格式约束
            response_format = {"type": "json_object"}
            
            # 调用LLM生成规划
            result = self.chat_sync(planning_prompt, response_format=response_format)
            
            if result.success:
                plan_result = result.return_value if result.return_value else result.stdout
            else:
                logger.warning(f"chat_sync返回失败: {result.stderr}")
                # 回退到无格式约束方式
                result = self.chat_sync(planning_prompt)
                plan_result = result.return_value if result.return_value else result.stdout
            
            # 解析JSON响应
            workflow_data = self._parse_llm_workflow_response(plan_result)
            
            # 校验工作流合法性
            validation_result = self._validate_workflow_legality(workflow_data)
            
            if not validation_result["is_valid"]:
                logger.warning(f"工作流校验失败: {validation_result['errors']}")
                # 尝试修复或重新生成
                workflow_data = self._fix_workflow_issues(workflow_data, validation_result["errors"])
            
            # 验证和转换为WorkflowDefinition
            workflow_definition = self._validate_and_convert_workflow(workflow_data, main_instruction)
            
            logger.info(f"成功生成包含 {len(workflow_definition.steps)} 个步骤的工作流")
            return workflow_definition
            
        except Exception as e:
            logger.error(f"工作流规划生成失败: {e}")
            # 回退到预设模板
            return self._create_fallback_workflow(main_instruction)
    
    def _parse_llm_workflow_response(self, response: str) -> Dict[str, Any]:
        """
        解析LLM返回的工作流JSON响应
        
        Args:
            response: LLM响应文本
            
        Returns:
            解析后的工作流数据字典
        """
        
        try:
            # 尝试从autogen提取代码块
            try:
                from autogen.code_utils import extract_code
                extracted_codes = extract_code(response)
                if extracted_codes:
                    workflow_data = json.loads(extracted_codes[0][1])
                    return workflow_data
            except ImportError:
                logger.debug("autogen不可用，使用手动解析")
            
            # 手动提取JSON代码块
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    json_str = response[start:end].strip()
                    return json.loads(json_str)
            
            # 直接解析整个响应
            return json.loads(response)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 响应内容: {response[:500]}...")
            raise ValueError(f"无法解析LLM返回的工作流JSON: {e}")
    
    def _validate_and_convert_workflow(self, workflow_data: Dict[str, Any], main_instruction: str) -> WorkflowDefinition:
        """
        验证并转换工作流数据为WorkflowDefinition对象
        
        Args:
            workflow_data: 工作流数据字典
            main_instruction: 原始主指令
            
        Returns:
            验证后的工作流定义对象
        """
        
        # 确保包含必要字段
        if "steps" not in workflow_data:
            raise ValueError("工作流数据缺少steps字段")
        
        # 设置默认元数据
        if "workflow_metadata" not in workflow_data:
            workflow_data["workflow_metadata"] = {
                "name": "dynamic_generated_workflow",
                "version": "1.0",
                "description": f"基于指令动态生成: {main_instruction[:100]}...",
                "author": "MultiStepAgent_v3"
            }
        
        # 设置默认全局变量
        if "global_variables" not in workflow_data:
            workflow_data["global_variables"] = {
                "max_retries": 3,
                "timeout": 300
            }
        
        # 验证智能体名称
        available_agent_names = {spec.name for spec in self.registered_agents}
        for step in workflow_data["steps"]:
            if step.get("agent_name") not in available_agent_names:
                logger.warning(f"步骤 {step.get('id')} 使用了未注册的智能体: {step.get('agent_name')}")
                # 使用第一个可用智能体作为替代
                if available_agent_names:
                    step["agent_name"] = next(iter(available_agent_names))
        
        # 自动修复步骤引用问题
        self._fix_workflow_references(workflow_data)
        
        # 使用WorkflowLoader创建WorkflowDefinition
        return self.workflow_loader.load_from_dict(workflow_data)
    
    def _create_fallback_workflow(self, main_instruction: str) -> WorkflowDefinition:
        """
        创建回退工作流（当LLM生成失败时使用）
        
        Args:
            main_instruction: 主任务指令
            
        Returns:
            简单的回退工作流定义
        """
        
        first_agent_name = self.registered_agents[0].name if self.registered_agents else "default_agent"
        
        fallback_workflow_data = {
            "workflow_metadata": {
                "name": "fallback_workflow",
                "version": "1.0", 
                "description": f"回退工作流: {main_instruction}",
                "author": "MultiStepAgent_v3"
            },
            "global_variables": {
                "max_retries": 3,
                "timeout": 300
            },
            "steps": [
                {
                    "id": "execute_task",
                    "name": "执行主任务",
                    "agent_name": first_agent_name,
                    "instruction": main_instruction,
                    "instruction_type": "execution",
                    "expected_output": "任务执行结果",
                    "timeout": 300,
                    "max_retries": 2,
                    "control_flow": {
                        "type": "terminal"
                    }
                }
            ],
            "control_rules": [],
            "error_handling": {
                "default_strategy": "retry_with_analysis"
            }
        }
        
        logger.info("使用回退工作流，将整个任务分配给单个智能体执行")
        return self.workflow_loader.load_from_dict(fallback_workflow_data)
    
    def _generate_dynamic_execution_summary(self, 
                                          main_instruction: str,
                                          workflow_definition: WorkflowDefinition, 
                                          result: WorkflowExecutionResult) -> str:
        """
        生成动态工作流执行摘要
        
        Args:
            main_instruction: 原始主指令
            workflow_definition: 工作流定义
            result: 执行结果
            
        Returns:
            执行摘要字符串
        """
        
        summary = f"""
## 多步骤任务执行摘要

**原始指令**: {main_instruction}
**生成工作流**: {result.workflow_name}
**执行状态**: {'成功' if result.success else '失败'}
**总步骤数**: {result.total_steps}
**完成步骤**: {result.completed_steps}
**失败步骤**: {result.failed_steps}
**跳过步骤**: {result.skipped_steps}
**执行时间**: {result.execution_time:.2f}秒

### 生成的工作流步骤
"""
        
        for i, step in enumerate(workflow_definition.steps, 1):
            summary += f"{i}. **{step.name}** ({step.id}) - 执行者: {step.agent_name}\\n"
            summary += f"   指令类型: {step.instruction_type}\\n"
            if step.expected_output:
                summary += f"   预期输出: {step.expected_output}\\n"
            summary += f"\\n"
        
        summary += "### 执行详情\\n"
        
        for step_id, step_info in result.step_results.items():
            status_icon = {
                'completed': '✅',
                'failed': '❌', 
                'skipped': '⏭️',
                'pending': '⏸️',
                'running': '🔄'
            }.get(step_info['status'], '❓')
            
            summary += f"- {status_icon} **{step_info['name']}** ({step_id}): {step_info['status']}\\n"
            
            if step_info['error_message']:
                summary += f"  - 错误: {step_info['error_message']}\\n"
            
            if step_info['retry_count'] > 0:
                summary += f"  - 重试次数: {step_info['retry_count']}\\n"
        
        if not result.success and result.error_message:
            summary += f"\\n**错误信息**: {result.error_message}\\n"
        
        return summary
    
    def _fix_workflow_references(self, workflow_data: Dict[str, Any]) -> None:
        """
        自动修复工作流中的步骤引用问题
        
        Args:
            workflow_data: 工作流数据字典（会被就地修改）
        """
        
        # 收集所有有效的步骤ID
        steps = workflow_data.get("steps", [])
        valid_step_ids = {step.get("id") for step in steps if step.get("id") is not None}
        
        # 确保valid_step_ids不为空，避免后续NoneType错误
        if not valid_step_ids:
            logger.warning("没有找到有效的步骤ID，跳过引用修复")
            return
        
        # 修复步骤中的控制流引用
        for i, step in enumerate(steps):
            step_id = step.get("id")
            control_flow = step.get("control_flow", {})
            
            # 如果没有控制流，且不是最后一步，则设置为sequential指向下一步
            if not control_flow and i < len(steps) - 1:
                next_step_id = steps[i + 1].get("id")
                step["control_flow"] = {
                    "type": "sequential",
                    "success_next": next_step_id,
                    "failure_next": None
                }
                logger.debug(f"为步骤 {step_id} 添加默认sequential控制流，指向 {next_step_id}")
                continue
            elif not control_flow and i == len(steps) - 1:
                # 最后一步设置为terminal
                step["control_flow"] = {"type": "terminal"}
                logger.debug(f"为最后步骤 {step_id} 设置terminal控制流")
                continue
            
            # 修复success_next引用
            if "success_next" in control_flow:
                if control_flow["success_next"] and control_flow["success_next"] not in valid_step_ids:
                    logger.warning(f"修复步骤 {step_id} 的无效success_next引用: {control_flow['success_next']}")
                    # 尝试指向下一个顺序步骤
                    if i < len(steps) - 1:
                        control_flow["success_next"] = steps[i + 1].get("id")
                    else:
                        control_flow["success_next"] = None
            
            # 修复failure_next引用
            if "failure_next" in control_flow:
                if control_flow["failure_next"] and control_flow["failure_next"] not in valid_step_ids:
                    logger.warning(f"修复步骤 {step_id} 的无效failure_next引用: {control_flow['failure_next']}")
                    # 对于失败情况，设置为None（将依赖默认行为）
                    control_flow["failure_next"] = None
            
            # 修复loop_target引用
            if "loop_target" in control_flow:
                if control_flow["loop_target"] and control_flow["loop_target"] not in valid_step_ids:
                    logger.warning(f"修复步骤 {step_id} 的无效loop_target引用: {control_flow['loop_target']}")
                    control_flow["loop_target"] = step_id  # 指向自己
            
            # 修复exit_on_max引用
            if "exit_on_max" in control_flow:
                if control_flow["exit_on_max"] and control_flow["exit_on_max"] not in valid_step_ids:
                    logger.warning(f"修复步骤 {step_id} 的无效exit_on_max引用: {control_flow['exit_on_max']}")
                    # 对于exit_on_max，应该指向终止步骤而不是设为None
                    terminal_step_id = self._find_or_create_terminal_step(steps, valid_step_ids)
                    control_flow["exit_on_max"] = terminal_step_id
                    logger.info(f"将步骤 {step_id} 的 exit_on_max 设置为终止步骤: {terminal_step_id}")
            
            # 修复parallel_steps引用
            if "parallel_steps" in control_flow:
                parallel_steps = control_flow.get("parallel_steps", [])
                if isinstance(parallel_steps, list) and parallel_steps:
                    valid_parallel_steps = []
                    for parallel_step_id in parallel_steps:
                        # 确保parallel_step_id不为None且在valid_step_ids中
                        if parallel_step_id is not None and parallel_step_id in valid_step_ids:
                            valid_parallel_steps.append(parallel_step_id)
                        else:
                            logger.warning(f"移除步骤 {step_id} 中的无效parallel_steps引用: {parallel_step_id}")
                    
                    # 如果没有有效的并行步骤，将类型改为sequential
                    if not valid_parallel_steps:
                        logger.warning(f"步骤 {step_id} 没有有效的并行步骤，改为sequential类型")
                        control_flow["type"] = "sequential"
                        if i < len(steps) - 1:
                            control_flow["success_next"] = steps[i + 1].get("id")
                        control_flow.pop("parallel_steps", None)
                    else:
                        control_flow["parallel_steps"] = valid_parallel_steps
            
            # 确保控制流类型正确
            if "type" not in control_flow:
                if i < len(steps) - 1:
                    control_flow["type"] = "sequential"
                else:
                    control_flow["type"] = "terminal"
                logger.debug(f"为步骤 {step_id} 设置默认控制流类型: {control_flow['type']}")
        
        # 修复控制规则中的目标引用
        control_rules = workflow_data.get("control_rules", [])
        valid_rules = []
        for rule in control_rules:
            if "target" in rule:
                if rule["target"] not in valid_step_ids:
                    logger.warning(f"移除控制规则中的无效target引用: {rule['target']}")
                else:
                    valid_rules.append(rule)
            else:
                valid_rules.append(rule)
        
        workflow_data["control_rules"] = valid_rules
        logger.debug("工作流引用修复完成")
    
    def _build_enhanced_instruction(self, current_step: WorkflowStep) -> str:
        """
        构建包含执行历史的增强指令
        
        Args:
            current_step: 当前要执行的步骤
            
        Returns:
            包含历史上下文的增强指令
        """
        
        # 获取已完成步骤的历史
        execution_history = self._get_execution_history(current_step)
        
        # 构建基本指令信息
        enhanced_instruction = f"""# 工作流步骤执行

## 当前步骤信息
- 步骤ID: {current_step.id}
- 步骤名称: {current_step.name}
- 执行者: {current_step.agent_name}
- 指令类型: {current_step.instruction_type}
- 预期输出: {current_step.expected_output}
"""
        
        # 添加执行历史
        if execution_history:
            enhanced_instruction += f"""
## 执行历史上下文
以下是之前已完成的步骤及其结果，请基于这些信息执行当前任务：

{execution_history}
"""
        
        # 添加当前执行指令
        enhanced_instruction += f"""
## 当前任务指令
{current_step.instruction}

## 重要提示
- 请基于上述执行历史的结果来执行当前任务
- 避免重复之前已完成的工作
- 确保与前面步骤的输出保持一致性
- 如果是代码相关任务，请确保代码的正确性和完整性
- 如果需要引用前面步骤的结果，请明确说明来源
"""
        
        return enhanced_instruction
    
    def _get_execution_history(self, current_step: WorkflowStep) -> str:
        """
        获取当前步骤之前的执行历史
        
        Args:
            current_step: 当前步骤
            
        Returns:
            格式化的执行历史字符串
        """
        
        if not self.workflow_definition:
            return ""
        
        history_parts = []
        current_step_index = None
        
        # 找到当前步骤的索引
        for i, step in enumerate(self.workflow_definition.steps):
            if step.id == current_step.id:
                current_step_index = i
                break
        
        if current_step_index is None:
            return ""
        
        # 收集已完成的步骤历史
        for i in range(current_step_index):
            step = self.workflow_definition.steps[i]
            
            # 只包含已完成的步骤
            if hasattr(step, 'status') and step.status and step.status.value == 'completed':
                history_part = f"""
### 步骤 {i+1}: {step.name} ({step.id})
- **执行者**: {step.agent_name}
- **指令类型**: {step.instruction_type}
- **原始指令**: {step.instruction[:200]}{'...' if len(step.instruction) > 200 else ''}
"""
                
                # 添加执行结果
                if hasattr(step, 'result') and step.result:
                    result = step.result
                    if hasattr(result, 'success') and result.success:
                        history_part += f"- **执行状态**: ✅ 成功\n"
                        
                        # 添加代码结果
                        if hasattr(result, 'code') and result.code:
                            code_preview = result.code[:500] + "..." if len(result.code) > 500 else result.code
                            history_part += f"- **生成代码**:\n```python\n{code_preview}\n```\n"
                        
                        # 添加输出结果
                        if hasattr(result, 'stdout') and result.stdout:
                            output_preview = result.stdout[:300] + "..." if len(result.stdout) > 300 else result.stdout
                            history_part += f"- **输出结果**: {output_preview}\n"
                        
                        if hasattr(result, 'return_value') and result.return_value:
                            return_preview = str(result.return_value)[:200] + "..." if len(str(result.return_value)) > 200 else str(result.return_value)
                            history_part += f"- **返回值**: {return_preview}\n"
                    else:
                        history_part += f"- **执行状态**: ❌ 失败\n"
                        if hasattr(result, 'stderr') and result.stderr:
                            error_preview = result.stderr[:200] + "..." if len(result.stderr) > 200 else result.stderr
                            history_part += f"- **错误信息**: {error_preview}\n"
                else:
                    history_part += f"- **执行状态**: ⏸️ 待处理\n"
                
                history_parts.append(history_part)
        
        if not history_parts:
            return "暂无执行历史（这是第一个步骤）"
        
        return "\n".join(history_parts)
    
    def _validate_workflow_legality(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        校验工作流的合法性
        
        Args:
            workflow_data: 工作流数据字典
            
        Returns:
            校验结果字典 {"is_valid": bool, "errors": List[str]}
        """
        
        errors = []
        
        # 检查必要字段
        if "steps" not in workflow_data:
            errors.append("缺少必要字段: steps")
            return {"is_valid": False, "errors": errors}
        
        steps = workflow_data["steps"]
        if not steps:
            errors.append("工作流至少需要包含一个步骤")
            return {"is_valid": False, "errors": errors}
        
        # 收集所有步骤ID
        step_ids = set()
        for step in steps:
            if "id" not in step:
                errors.append(f"步骤缺少id字段: {step}")
                continue
            step_ids.add(step["id"])
        
        # 确保step_ids不为空，避免后续NoneType错误
        if not step_ids:
            errors.append("没有找到有效的步骤ID")
            return {"is_valid": False, "errors": errors}
        
        # 检查智能体名称
        available_agent_names = {spec.name for spec in self.registered_agents}
        for step in steps:
            agent_name = step.get("agent_name")
            if agent_name and agent_name not in available_agent_names:
                errors.append(f"步骤 {step.get('id')} 使用了未注册的智能体: {agent_name}")
        
        # 检查控制流引用
        for step in steps:
            step_id = step.get("id")
            control_flow = step.get("control_flow", {})
            
            # 检查success_next引用
            success_next = control_flow.get("success_next")
            if success_next and success_next not in step_ids:
                errors.append(f"步骤 {step_id} 的 success_next 引用了不存在的步骤: {success_next}")
            
            # 检查failure_next引用
            failure_next = control_flow.get("failure_next")
            if failure_next and failure_next not in step_ids:
                errors.append(f"步骤 {step_id} 的 failure_next 引用了不存在的步骤: {failure_next}")
            
            # 检查loop_target引用
            loop_target = control_flow.get("loop_target")
            if loop_target and loop_target not in step_ids:
                errors.append(f"步骤 {step_id} 的 loop_target 引用了不存在的步骤: {loop_target}")
            
            # 检查exit_on_max引用
            exit_on_max = control_flow.get("exit_on_max")
            if exit_on_max and exit_on_max not in step_ids:
                errors.append(f"步骤 {step_id} 的 exit_on_max 引用了不存在的步骤: {exit_on_max}")
            
            # 检查parallel_steps引用
            parallel_steps = control_flow.get("parallel_steps", [])
            for parallel_step_id in parallel_steps:
                if parallel_step_id not in step_ids:
                    errors.append(f"步骤 {step_id} 的 parallel_steps 引用了不存在的步骤: {parallel_step_id}")
        
        # 检查控制规则引用
        control_rules = workflow_data.get("control_rules", [])
        for rule in control_rules:
            target = rule.get("target")
            if target and target not in step_ids:
                errors.append(f"控制规则的 target 引用了不存在的步骤: {target}")
        
        # 检查循环逻辑冲突
        self._check_loop_logic_conflicts(steps, errors)
        
        # 检查循环引用（简单检查）
        self._check_circular_references(steps, errors)
        
        is_valid = len(errors) == 0
        return {"is_valid": is_valid, "errors": errors}
    
    def _check_loop_logic_conflicts(self, steps: List[Dict], errors: List[str]) -> None:
        """检查循环逻辑冲突"""
        
        for step in steps:
            step_id = step.get("id")
            control_flow = step.get("control_flow", {})
            
            # 只检查类型为loop的步骤
            if control_flow.get("type") != "loop":
                continue
            
            loop_condition = control_flow.get("loop_condition", "")
            max_retries = step.get("max_retries", 0)
            max_iterations = control_flow.get("max_iterations", 0)
            
            # 确保loop_condition不为None，避免NoneType错误
            if loop_condition is None:
                loop_condition = ""
            
            # 检查是否混用了步骤重试和工作流循环概念
            if loop_condition and "retry_count" in loop_condition and "max_retries" in loop_condition:
                errors.append(f"步骤 {step_id} 的循环条件错误使用了步骤重试机制 'retry_count < max_retries'，应使用工作流状态变量")
            
            # 检查是否同时设置了max_retries和max_iterations且值不一致
            if max_retries > 0 and max_iterations > 0 and max_retries != max_iterations:
                errors.append(f"步骤 {step_id} 同时设置了 max_retries({max_retries}) 和 max_iterations({max_iterations})，这可能导致逻辑冲突")
            
            # 检查循环条件是否为空
            if not loop_condition:
                errors.append(f"步骤 {step_id} 的循环类型缺少 loop_condition")
            
            # 检查是否缺少循环目标
            if not control_flow.get("loop_target"):
                errors.append(f"步骤 {step_id} 的循环类型缺少 loop_target")
            
            # 检查循环条件格式
            if loop_condition and not any(keyword in loop_condition for keyword in ['workflow_state', 'iteration_count', '<', '>', '==']):
                errors.append(f"步骤 {step_id} 的循环条件格式可能有误: {loop_condition}")

    def _check_circular_references(self, steps: List[Dict], errors: List[str]) -> None:
        """检查循环引用（简单版本）"""
        
        # 构建步骤依赖图
        dependencies = {}
        for step in steps:
            step_id = step.get("id")
            if not step_id:
                continue
                
            deps = set()
            control_flow = step.get("control_flow", {})
            
            # 添加success_next依赖
            if control_flow.get("success_next"):
                deps.add(control_flow["success_next"])
            
            # 添加failure_next依赖
            if control_flow.get("failure_next"):
                deps.add(control_flow["failure_next"])
            
            # loop_target不算循环引用（这是预期的循环）
            
            dependencies[step_id] = deps
        
        # 简单的循环检测（可以改进为更复杂的算法）
        for step_id, deps in dependencies.items():
            if step_id in deps:
                errors.append(f"步骤 {step_id} 存在自引用")
    
    def _fix_workflow_issues(self, workflow_data: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
        """
        修复工作流问题
        
        Args:
            workflow_data: 有问题的工作流数据
            errors: 校验错误列表
            
        Returns:
            修复后的工作流数据
        """
        
        logger.info(f"开始修复工作流问题，共 {len(errors)} 个错误")
        
        # 使用现有的修复机制
        self._fix_workflow_references(workflow_data)
        
        # 针对特定错误类型进行修复
        for error in errors:
            if "未注册的智能体" in error:
                self._fix_agent_references(workflow_data)
            elif "缺少必要字段" in error:
                self._add_missing_fields(workflow_data)
            elif "循环条件错误使用了步骤重试机制" in error or "循环逻辑冲突" in error:
                self._fix_loop_configuration(workflow_data)
        
        logger.info(f"工作流问题修复完成")
        return workflow_data
    
    def _fix_agent_references(self, workflow_data: Dict[str, Any]) -> None:
        """修复智能体引用问题"""
        
        if not self.registered_agents:
            return
        
        default_agent = self.registered_agents[0].name
        
        for step in workflow_data.get("steps", []):
            agent_name = step.get("agent_name")
            if not agent_name or agent_name not in {spec.name for spec in self.registered_agents}:
                step["agent_name"] = default_agent
                logger.debug(f"修复步骤 {step.get('id')} 的智能体引用为: {default_agent}")
    
    def _add_missing_fields(self, workflow_data: Dict[str, Any]) -> None:
        """添加缺失的必要字段"""
        
        if "workflow_metadata" not in workflow_data:
            workflow_data["workflow_metadata"] = {
                "name": "auto_generated_workflow",
                "version": "1.0",
                "description": "自动生成的工作流",
                "author": "MultiStepAgent_v3"
            }
        
        if "global_variables" not in workflow_data:
            workflow_data["global_variables"] = {
                "max_retries": 3,
                "timeout": 300
            }
        
        if "steps" not in workflow_data:
            workflow_data["steps"] = []
        
        # 确保每个步骤都有必要字段
        for i, step in enumerate(workflow_data["steps"]):
            if "id" not in step:
                step["id"] = f"step_{i+1}"
            if "name" not in step:
                step["name"] = f"步骤 {i+1}"
            if "agent_name" not in step and self.registered_agents:
                step["agent_name"] = self.registered_agents[0].name
            if "instruction_type" not in step:
                step["instruction_type"] = "execution"
    
    def _fix_loop_configuration(self, workflow_data: Dict[str, Any]) -> None:
        """修复循环配置问题"""
        
        steps = workflow_data.get("steps", [])
        
        for step in steps:
            step_id = step.get("id")
            control_flow = step.get("control_flow", {})
            
            # 只修复循环类型的步骤
            if control_flow.get("type") != "loop":
                continue
            
            loop_condition = control_flow.get("loop_condition", "")
            
            # 修复错误的循环条件（步骤重试机制）
            if "retry_count" in loop_condition and "max_retries" in loop_condition:
                logger.warning(f"修复步骤 {step_id} 的错误循环条件: {loop_condition}")
                # 替换为正确的工作流状态变量
                control_flow["loop_condition"] = "workflow_state.fix_attempts < 3"
                control_flow["max_iterations"] = 3
                # 清除可能冲突的步骤级重试设置
                if step.get("max_retries", 0) > 0:
                    step["max_retries"] = 0
                    logger.debug(f"清除步骤 {step_id} 的 max_retries 以避免与循环逻辑冲突")
            
            # 确保循环步骤有必要的字段
            if not control_flow.get("loop_condition"):
                control_flow["loop_condition"] = "workflow_state.iteration_count < 3"
                logger.debug(f"为步骤 {step_id} 添加默认循环条件")
            
            if not control_flow.get("loop_target"):
                # 尝试找到前一个步骤作为循环目标
                step_ids = [s.get("id") for s in steps]
                try:
                    current_index = step_ids.index(step_id)
                    if current_index > 0:
                        control_flow["loop_target"] = step_ids[current_index - 1]
                    else:
                        control_flow["loop_target"] = step_id  # 指向自己
                    logger.debug(f"为步骤 {step_id} 设置循环目标: {control_flow['loop_target']}")
                except ValueError:
                    control_flow["loop_target"] = step_id
            
            if not control_flow.get("max_iterations"):
                control_flow["max_iterations"] = 3
                logger.debug(f"为步骤 {step_id} 设置默认最大迭代次数: 3")
            
            # 如果同时设置了max_retries和max_iterations且不一致，统一为max_iterations
            max_retries = step.get("max_retries", 0)
            max_iterations = control_flow.get("max_iterations", 0)
            if max_retries > 0 and max_iterations > 0 and max_retries != max_iterations:
                logger.warning(f"步骤 {step_id} 的 max_retries({max_retries}) 与 max_iterations({max_iterations}) 不一致，统一为 max_iterations")
                step["max_retries"] = 0  # 清除步骤级重试，使用循环迭代
            
            logger.info(f"修复步骤 {step_id} 的循环配置完成")
    
    def _find_or_create_terminal_step(self, steps: List[Dict], valid_step_ids: set) -> str:
        """
        查找或创建终止步骤
        
        Args:
            steps: 步骤列表
            valid_step_ids: 有效的步骤ID集合
            
        Returns:
            终止步骤的ID
        """
        
        # 首先查找现有的终止步骤
        for step in steps:
            control_flow = step.get("control_flow", {})
            if control_flow.get("type") == "terminal":
                step_id = step.get("id")
                if step_id in valid_step_ids:
                    logger.debug(f"找到现有的终止步骤: {step_id}")
                    return step_id
        
        # 如果没有找到终止步骤，查找最后一个步骤并将其设为终止步骤
        if steps:
            last_step = steps[-1]
            last_step_id = last_step.get("id")
            
            if last_step_id and last_step_id in valid_step_ids:
                # 将最后一个步骤的控制流设置为terminal
                if "control_flow" not in last_step:
                    last_step["control_flow"] = {}
                last_step["control_flow"]["type"] = "terminal"
                
                logger.info(f"将最后一个步骤设置为终止步骤: {last_step_id}")
                return last_step_id
        
        # 如果还是没有合适的步骤，创建一个新的终止步骤
        terminal_step_id = "workflow_end"
        
        # 确保新步骤ID不与现有ID冲突
        counter = 1
        while terminal_step_id in valid_step_ids:
            terminal_step_id = f"workflow_end_{counter}"
            counter += 1
        
        # 创建终止步骤
        terminal_step = {
            "id": terminal_step_id,
            "name": "工作流结束",
            "agent_name": self.registered_agents[0].name if self.registered_agents else "default_agent",
            "instruction": "工作流执行结束，整理和汇总执行结果",
            "instruction_type": "information",
            "expected_output": "工作流执行摘要",
            "timeout": 60,
            "max_retries": 1,
            "control_flow": {
                "type": "terminal"
            }
        }
        
        # 将新步骤添加到步骤列表
        steps.append(terminal_step)
        valid_step_ids.add(terminal_step_id)
        
        logger.info(f"创建新的终止步骤: {terminal_step_id}")
        return terminal_step_id