"""
CognitiveDebugger - 具身认知工作流调试器

提供单步执行、状态检查、断点设置等调试功能，
帮助开发者深入理解和优化认知循环的执行过程。
"""

import sys
import os
import time
import uuid
import copy
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Iterator, Union, Callable

# 添加父目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from embodied_cognitive_workflow.embodied_cognitive_workflow import CognitiveAgent, WorkflowContext
    from embodied_cognitive_workflow.decision_types import Decision, DecisionType
except ImportError:
    try:
        from .embodied_cognitive_workflow import CognitiveAgent, WorkflowContext
        from .decision_types import Decision, DecisionType
    except ImportError:
        from embodied_cognitive_workflow import CognitiveAgent, WorkflowContext
        from decision_types import Decision, DecisionType

from agent_base import Result
from langchain_core.messages import BaseMessage
import json
import pickle


class StepType(Enum):
    """认知调试步骤类型枚举"""
    # 初始化阶段
    INIT = "初始化"
    COMPLEXITY_EVAL = "复杂性评估"
    META_COGNITION_PRE = "元认知预监督"
    
    # 认知循环阶段
    CYCLE_START = "循环开始"
    STATE_ANALYSIS = "更新状态"
    DECISION_MAKING = "决策判断"
    ID_EVALUATION = "本我评估"
    BODY_EXECUTION = "身体执行"
    CYCLE_END = "循环决策"
    
    # 结束阶段
    META_COGNITION_POST = "元认知后监督"
    FINALIZE = "最终化"
    COMPLETED = "执行完成"


@dataclass
class PerformanceMetrics:
    """性能指标"""
    execution_time: float = 0.0
    memory_usage: int = 0
    token_count: int = 0
    llm_calls: int = 0
    step_count: int = 0


@dataclass
class StateChange:
    """状态变化记录"""
    timestamp: datetime
    step_type: StepType
    field_name: str
    old_value: Any
    new_value: Any
    description: str = ""


@dataclass
class StepResult:
    """步骤执行结果"""
    # 基本信息
    step_type: StepType
    step_id: str
    timestamp: datetime
    
    # 执行数据
    input_data: Any
    output_data: Any
    execution_time: float
    
    # 状态信息
    agent_layer: str  # 执行层 (MetaCognitive/Ego/Id/Body)
    next_step: Optional[StepType]
    
    # 调试信息
    debug_info: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None
    
    # 认知相关
    decision_type: Optional[DecisionType] = None
    state_analysis: Optional[str] = None
    goal_achieved: Optional[bool] = None
    
    def __post_init__(self):
        if not self.step_id:
            self.step_id = str(uuid.uuid4())[:8]


@dataclass
class ExecutionTrace:
    """执行轨迹"""
    trace_id: str
    cycle_number: int
    step_sequence: List[StepType]
    decision_path: List[DecisionType]
    state_changes: List[StateChange]
    performance_metrics: PerformanceMetrics
    
    def __post_init__(self):
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())[:8]


@dataclass
class Breakpoint:
    """断点定义"""
    id: str
    step_type: StepType
    condition: Optional[str] = None  # Python表达式
    hit_count: int = 0
    enabled: bool = True
    description: str = ""
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


@dataclass
class StateSnapshot:
    """状态快照"""
    timestamp: datetime
    cycle_count: int
    current_step: StepType
    
    # 上下文状态
    instruction: str
    goal_achieved: bool
    current_state_analysis: str
    id_evaluation: str
    
    # 智能体状态
    memory_length: int
    memory_tokens: int
    agent_layers_status: Dict[str, Any]
    
    # 执行统计
    total_steps: int
    execution_time: float
    performance_metrics: Dict[str, Any]


@dataclass 
class DebugState:
    """调试状态管理"""
    # 执行状态
    current_step: StepType = StepType.INIT
    cycle_count: int = 0
    is_finished: bool = False
    execution_start_time: Optional[datetime] = None
    
    # 上下文状态
    workflow_context: Optional[WorkflowContext] = None
    agent_memory_snapshot: List[BaseMessage] = field(default_factory=list)
    
    # 执行历史
    step_history: List[StepResult] = field(default_factory=list)
    execution_trace: List[ExecutionTrace] = field(default_factory=list)
    
    # 状态快照历史（用于回退）
    state_snapshots: List[Dict[str, Any]] = field(default_factory=list)
    
    # 调试控制
    breakpoints: List[Breakpoint] = field(default_factory=list)
    step_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 性能统计
    performance_metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    
    # 多Agent支持
    execution_instruction: Optional[str] = None  # 当前执行指令
    selected_agent: Optional[str] = None  # 选择的Agent名称
    
    # 断点状态
    _at_breakpoint: bool = False  # 标记当前是否在断点处


class BreakpointManager:
    """断点管理器"""
    
    def __init__(self):
        self.breakpoints: List[Breakpoint] = []
    
    def add_breakpoint(self, breakpoint: Breakpoint) -> str:
        """添加断点"""
        self.breakpoints.append(breakpoint)
        return breakpoint.id
    
    def remove_breakpoint(self, breakpoint_id: str) -> bool:
        """移除断点"""
        for i, bp in enumerate(self.breakpoints):
            if bp.id == breakpoint_id:
                del self.breakpoints[i]
                return True
        return False
    
    def check_breakpoint(self, step_type: StepType, context: Dict[str, Any]) -> Optional[Breakpoint]:
        """检查是否命中断点"""
        for bp in self.breakpoints:
            if not bp.enabled:
                continue
                
            if bp.step_type != step_type:
                continue
            
            # 检查条件
            if bp.condition:
                try:
                    # 创建安全的执行环境
                    eval_context = {
                        'step_type': step_type,
                        'context': context,
                        **context  # 展开context到全局命名空间
                    }
                    if eval(bp.condition, {"__builtins__": {}}, eval_context):
                        bp.hit_count += 1
                        return bp
                except Exception as e:
                    print(f"断点条件评估失败: {e}")
                    continue
            else:
                # 无条件断点
                bp.hit_count += 1
                return bp
        
        return None
    
    def list_breakpoints(self) -> List[Breakpoint]:
        """列出所有断点"""
        return self.breakpoints.copy()
    
    def enable_breakpoint(self, breakpoint_id: str) -> bool:
        """启用断点"""
        for bp in self.breakpoints:
            if bp.id == breakpoint_id:
                bp.enabled = True
                return True
        return False
    
    def disable_breakpoint(self, breakpoint_id: str) -> bool:
        """禁用断点"""
        for bp in self.breakpoints:
            if bp.id == breakpoint_id:
                bp.enabled = False
                return True
        return False


class StepExecutor:
    """步骤执行器"""
    
    def __init__(self, cognitive_agent: CognitiveAgent):
        self.agent = cognitive_agent
        self.step_mapping = self._build_step_mapping()
    
    def _build_step_mapping(self) -> Dict[StepType, Callable]:
        """构建步骤到执行函数的映射"""
        return {
            StepType.INIT: self._execute_init,
            StepType.COMPLEXITY_EVAL: self._execute_complexity_eval,
            StepType.META_COGNITION_PRE: self._execute_meta_cognition_pre,
            StepType.CYCLE_START: self._execute_cycle_start,
            StepType.STATE_ANALYSIS: self._execute_state_analysis,
            StepType.DECISION_MAKING: self._execute_decision_making,
            StepType.ID_EVALUATION: self._execute_id_evaluation,
            StepType.BODY_EXECUTION: self._execute_body_execution,
            StepType.CYCLE_END: self._execute_cycle_end,
            StepType.META_COGNITION_POST: self._execute_meta_cognition_post,
            StepType.FINALIZE: self._execute_finalize,
            StepType.COMPLETED: self._execute_completed,
        }
    
    def execute_step(self, step_type: StepType, input_data: Any, debug_state: DebugState) -> StepResult:
        """执行单个步骤"""
        start_time = time.time()
        step_id = str(uuid.uuid4())[:8]
        
        try:
            # 获取执行函数
            execute_func = self.step_mapping.get(step_type)
            if not execute_func:
                raise ValueError(f"未知的步骤类型: {step_type}")
            
            # 执行步骤
            output_data, next_step, agent_layer, debug_info = execute_func(input_data, debug_state)
            
            execution_time = time.time() - start_time
            
            return StepResult(
                step_type=step_type,
                step_id=step_id,
                timestamp=datetime.now(),
                input_data=input_data,
                output_data=output_data,
                execution_time=execution_time,
                agent_layer=agent_layer,
                next_step=next_step,
                debug_info=debug_info
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return StepResult(
                step_type=step_type,
                step_id=step_id,
                timestamp=datetime.now(),
                input_data=input_data,
                output_data=None,
                execution_time=execution_time,
                agent_layer="Unknown",
                next_step=None,
                error=e,
                debug_info={"error": str(e)}
            )
    
    def get_next_step(self, current_step: StepType, step_result: StepResult, debug_state: DebugState) -> Optional[StepType]:
        """根据当前步骤和结果确定下一步"""
        if step_result.error:
            return StepType.FINALIZE
        
        if step_result.next_step:
            return step_result.next_step
        
        # 默认的步骤转换逻辑
        step_transitions = {
            StepType.INIT: StepType.COMPLEXITY_EVAL,
            StepType.COMPLEXITY_EVAL: self._decide_after_complexity_eval(step_result, debug_state),
            StepType.META_COGNITION_PRE: StepType.CYCLE_START,
            StepType.CYCLE_START: StepType.STATE_ANALYSIS,
            StepType.STATE_ANALYSIS: StepType.DECISION_MAKING,
            StepType.DECISION_MAKING: self._decide_after_decision_making(step_result, debug_state),
            StepType.ID_EVALUATION: self._decide_after_id_evaluation(step_result, debug_state),
            StepType.BODY_EXECUTION: StepType.CYCLE_END,
            StepType.CYCLE_END: self._decide_after_cycle_end(step_result, debug_state),
            StepType.META_COGNITION_POST: StepType.FINALIZE,
            StepType.FINALIZE: StepType.COMPLETED,
            StepType.COMPLETED: None
        }
        
        return step_transitions.get(current_step)
    
    def can_execute_step(self, step_type: StepType) -> bool:
        """检查是否可以执行指定步骤"""
        return step_type in self.step_mapping
    
    # 具体步骤执行方法
    def _execute_init(self, input_data: Any, debug_state: DebugState) -> tuple:
        """初始化步骤"""
        instruction = input_data if isinstance(input_data, str) else ""
        
        # 创建工作流上下文
        workflow_context = WorkflowContext(instruction)
        debug_state.workflow_context = workflow_context
        debug_state.execution_start_time = datetime.now()
        
        debug_info = {
            "instruction": instruction,
            "context_created": True,
            "agent_initialized": True
        }
        
        return workflow_context, StepType.COMPLEXITY_EVAL, "System", debug_info
    
    def _execute_complexity_eval(self, input_data: Any, debug_state: DebugState) -> tuple:
        """复杂性评估步骤"""
        instruction = debug_state.workflow_context.instruction
        
        # 调用智能体的真实复杂性评估方法
        can_handle_directly = self.agent._can_handle_directly(instruction)
        
        debug_info = {
            "instruction": instruction,
            "can_handle_directly": can_handle_directly,
            "evaluation_method": "AI-based",
            "agent_method": "_can_handle_directly"
        }
        
        next_step = StepType.BODY_EXECUTION if can_handle_directly else StepType.META_COGNITION_PRE
        
        return can_handle_directly, next_step, "Ego", debug_info
    
    def _execute_meta_cognition_pre(self, input_data: Any, debug_state: DebugState) -> tuple:
        """元认知预监督步骤"""
        if not self.agent.enable_meta_cognition or not self.agent.meta_cognition:
            return "跳过元认知预监督", StepType.CYCLE_START, "MetaCognitive", {"skipped": True}
        
        instruction = debug_state.workflow_context.instruction
        
        # 调用元认知预监督（这里需要从原始方法中提取逻辑）
        # 暂时返回占位符结果
        supervision_result = "元认知预监督完成"
        
        debug_info = {
            "supervision_type": "pre",
            "meta_cognition_enabled": True,
            "result": supervision_result
        }
        
        return supervision_result, StepType.CYCLE_START, "MetaCognitive", debug_info
    
    def _execute_cycle_start(self, input_data: Any, debug_state: DebugState) -> tuple:
        """循环开始步骤"""
        debug_state.cycle_count += 1
        
        debug_info = {
            "cycle_number": debug_state.cycle_count,
            "max_cycles": self.agent.max_cycles,
            "context": debug_state.workflow_context.get_current_context()
        }
        
        return debug_state.cycle_count, StepType.STATE_ANALYSIS, "System", debug_info
    
    def _execute_state_analysis(self, input_data: Any, debug_state: DebugState) -> tuple:
        """状态分析步骤"""
        context = debug_state.workflow_context.get_current_context()
        
        # 调用自我的真实状态分析方法
        state_analysis = self.agent.ego.analyze_current_state(context)
        
        debug_state.workflow_context.update_current_state(state_analysis)
        
        debug_info = {
            "context": context,
            "analysis_result": state_analysis,
            "cycle": debug_state.cycle_count,
            "agent_method": "ego.analyze_current_state"
        }
        
        return state_analysis, StepType.DECISION_MAKING, "Ego", debug_info
    
    def _execute_decision_making(self, input_data: Any, debug_state: DebugState) -> tuple:
        """决策判断步骤"""
        state_analysis = input_data
        
        # 获取可用Agent实例
        available_agents = None
        if hasattr(self.agent, 'agents') and self.agent.agents:
            available_agents = self.agent.agents
        
        # 调用自我的真实决策判断方法，返回Decision对象
        decision = self.agent.ego.decide_next_action(state_analysis, available_agents)
        
        # 从Decision对象中提取信息
        decision_type = decision.decision_type
        instruction = decision.instruction
        agent_name = decision.agent.name if decision.agent else None
        
        # 构建调试信息
        debug_info = {
            "state_analysis": state_analysis,
            "decision_type": decision_type.value,
            "agent_method": "ego.decide_next_action"
        }
        
        # 如果有指令，添加到调试信息
        if instruction:
            debug_info["instruction"] = instruction
            # 存储指令到调试状态，供后续步骤使用
            debug_state.execution_instruction = instruction
        
        # 如果有Agent选择信息，添加到调试信息
        if agent_name:
            debug_info["selected_agent"] = agent_name
            # 存储Agent选择到调试状态
            debug_state.selected_agent = agent_name
            # 存储实际的Agent实例
            if hasattr(debug_state, 'selected_agent_instance'):
                debug_state.selected_agent_instance = decision.agent
            else:
                setattr(debug_state, 'selected_agent_instance', decision.agent)
        
        # 如果有可用Agent列表，也添加到调试信息
        if available_agents:
            debug_info["available_agents"] = [getattr(a, 'name', '未命名Agent') for a in available_agents]
        
        return decision_type, self._get_next_step_for_decision(decision_type), "Ego", debug_info
    
    def _execute_id_evaluation(self, input_data: Any, debug_state: DebugState) -> tuple:
        """本我评估步骤"""
        decision_type = input_data
        
        # 先获取自我的评估请求
        evaluation_request = self.agent.ego.request_id_evaluation(debug_state.workflow_context.current_state)
        
        # 调用本我的评估
        evaluation_json = self.agent.id_agent.evaluate_with_context(
            evaluation_request, 
            debug_state.workflow_context.current_state
        )
        
        # 解析JSON评估结果
        try:
            import json
            evaluation_data = json.loads(evaluation_json)
            goal_achieved = evaluation_data.get("目标是否达成", False)
            reason = evaluation_data.get("原因", "未提供原因")
            evaluation_result = reason
        except json.JSONDecodeError:
            # JSON解析失败，使用原始字符串作为评估结果
            evaluation_result = evaluation_json
            goal_achieved = False
        
        # 更新工作流上下文中的goal_achieved变量
        debug_state.workflow_context.update_id_evaluation(evaluation_result)
        debug_state.workflow_context.update_goal_status(goal_achieved)
        
        debug_info = {
            "evaluation_request": evaluation_request,
            "evaluation_json": evaluation_json,
            "evaluation_result": evaluation_result,
            "goal_achieved": goal_achieved,
            "agent_method": f"id.evaluate_with_context"
        }
        
        next_step = StepType.CYCLE_END if goal_achieved else StepType.BODY_EXECUTION
        
        return evaluation_result, next_step, "Id", debug_info
    
    def _execute_body_execution(self, input_data: Any, debug_state: DebugState) -> tuple:
        """身体执行步骤"""
        # 检查是否是直接执行模式
        if isinstance(input_data, bool) and input_data:  # can_handle_directly = True
            # 直接执行模式
            instruction = debug_state.workflow_context.instruction
            quick_prompt = f"""直接完成以下任务：
{instruction}

请提供清晰、准确的结果。"""
            execution_result = self.agent._execute_body_operation(quick_prompt)
        else:
            # 认知循环模式
            # 使用存储的执行指令和Agent选择
            instruction = getattr(debug_state, 'execution_instruction', None)
            agent_name = getattr(debug_state, 'selected_agent', None)
            
            if instruction:
                # 使用Ego提供的具体指令和Agent选择
                # 获取实际的Agent实例
                agent_instance = getattr(debug_state, 'selected_agent_instance', None)
                execution_result = self.agent._execute_body_operation(instruction, agent_instance)
            else:
                # 回退到旧的行为
                current_context = debug_state.workflow_context.get_current_context()
                # 使用默认的第一个Agent执行
                default_agent = self.agent.agents[0] if self.agent.agents else None
                if default_agent:
                    execution_result = default_agent.execute_sync(current_context)
                else:
                    execution_result = Result(
                        success=False,
                    code="",
                    stderr="没有可用的Agent",
                    return_value=""
                )
        
        # 记录执行结果到历史中
        if execution_result.success and execution_result.return_value:
            cycle_data = f"身体执行结果：{execution_result.return_value}"
            debug_state.workflow_context.add_cycle_result(debug_state.cycle_count, cycle_data)
            
            # 在直接执行模式下，如果执行成功，设置目标为已达成
            if isinstance(input_data, bool) and input_data:  # 直接执行模式
                debug_state.workflow_context.goal_achieved = True
        
        debug_info = {
            "execution_mode": "direct" if (isinstance(input_data, bool) and input_data) else "cognitive_cycle",
            "execution_result": execution_result.to_dict() if hasattr(execution_result, 'to_dict') else str(execution_result),
            "success": execution_result.success,
            "agent_method": "_execute_body_operation" if (isinstance(input_data, bool) and input_data) else "agent.execute_sync"
        }
        
        # 添加Agent选择信息（如果有）
        if hasattr(debug_state, 'selected_agent') and debug_state.selected_agent:
            debug_info["selected_agent"] = debug_state.selected_agent
        
        # 添加执行指令（如果有）
        if hasattr(debug_state, 'execution_instruction') and debug_state.execution_instruction:
            debug_info["instruction"] = debug_state.execution_instruction
        
        # 直接执行模式应该结束，而不是继续循环
        next_step = StepType.FINALIZE if (isinstance(input_data, bool) and input_data) else StepType.CYCLE_END
        return execution_result, next_step, "Body", debug_info
    
    def _execute_cycle_end(self, input_data: Any, debug_state: DebugState) -> tuple:
        """循环决策步骤 - 判断是否继续下一轮循环"""
        execution_result = input_data
        
        # 检查是否应该继续循环
        should_continue = (
            debug_state.cycle_count < self.agent.max_cycles and
            not debug_state.workflow_context.goal_achieved
        )
        
        debug_info = {
            "cycle_number": debug_state.cycle_count,
            "should_continue": should_continue,
            "goal_achieved": debug_state.workflow_context.goal_achieved,
            "max_cycles_reached": debug_state.cycle_count >= self.agent.max_cycles
        }
        
        next_step = StepType.STATE_ANALYSIS if should_continue else StepType.META_COGNITION_POST
        
        return should_continue, next_step, "System", debug_info
    
    def _execute_meta_cognition_post(self, input_data: Any, debug_state: DebugState) -> tuple:
        """元认知后监督步骤"""
        if not self.agent.enable_meta_cognition or not self.agent.meta_cognition:
            return "跳过元认知后监督", StepType.FINALIZE, "MetaCognitive", {"skipped": True}
        
        # 调用元认知后监督（需要从原始方法中提取）
        # 暂时返回占位符结果
        supervision_result = "元认知后监督完成"
        
        debug_info = {
            "supervision_type": "post",
            "meta_cognition_enabled": True,
            "result": supervision_result
        }
        
        return supervision_result, StepType.FINALIZE, "MetaCognitive", debug_info
    
    def _execute_finalize(self, input_data: Any, debug_state: DebugState) -> tuple:
        """最终化步骤"""
        final_result = Result(
            success=debug_state.workflow_context.goal_achieved,
            code="",
            stdout="",
            stderr="",
            return_value="认知循环执行完成"
        )
        
        debug_state.is_finished = True
        
        debug_info = {
            "final_result": final_result.to_dict(),
            "total_cycles": debug_state.cycle_count,
            "goal_achieved": debug_state.workflow_context.goal_achieved,
            "execution_time": (datetime.now() - debug_state.execution_start_time).total_seconds()
        }
        
        return final_result, StepType.COMPLETED, "System", debug_info
    
    def _execute_completed(self, input_data: Any, debug_state: DebugState) -> tuple:
        """执行完成步骤"""
        debug_info = {
            "status": "completed",
            "final_result": input_data
        }
        
        return input_data, None, "System", debug_info
    
    # 辅助方法
    def _decide_after_complexity_eval(self, step_result: StepResult, debug_state: DebugState) -> StepType:
        """复杂性评估后的决策"""
        can_handle_directly = step_result.output_data
        return StepType.BODY_EXECUTION if can_handle_directly else StepType.META_COGNITION_PRE
    
    def _decide_after_decision_making(self, step_result: StepResult, debug_state: DebugState) -> StepType:
        """决策判断后的步骤选择"""
        decision_type = step_result.output_data
        return self._get_next_step_for_decision(decision_type)
    
    def _decide_after_id_evaluation(self, step_result: StepResult, debug_state: DebugState) -> StepType:
        """本我评估后的步骤选择"""
        goal_achieved = debug_state.workflow_context.goal_achieved
        return StepType.CYCLE_END if goal_achieved else StepType.BODY_EXECUTION
    
    def _decide_after_cycle_end(self, step_result: StepResult, debug_state: DebugState) -> StepType:
        """循环结束后的步骤选择"""
        should_continue = step_result.output_data
        return StepType.STATE_ANALYSIS if should_continue else StepType.META_COGNITION_POST
    
    def _get_next_step_for_decision(self, decision_type: DecisionType) -> StepType:
        """根据决策类型确定下一步"""
        decision_mapping = {
            DecisionType.REQUEST_EVALUATION: StepType.ID_EVALUATION,
            DecisionType.JUDGMENT_FAILED: StepType.BODY_EXECUTION,
            DecisionType.EXECUTE_INSTRUCTION: StepType.BODY_EXECUTION
        }
        return decision_mapping.get(decision_type, StepType.CYCLE_END)


@dataclass
class PerformanceReport:
    """性能分析报告"""
    total_time: float
    avg_step_time: float
    slowest_step: str
    fastest_step: str
    step_time_breakdown: Dict[str, float]
    cycle_performance: List[Dict[str, Any]]
    memory_usage_trend: List[int]
    token_usage_trend: List[int]


class DebugUtils:
    """调试辅助工具类"""
    
    @staticmethod
    def analyze_performance(step_results: List[StepResult]) -> PerformanceReport:
        """分析性能数据
        
        Args:
            step_results: 步骤执行结果列表
            
        Returns:
            PerformanceReport: 性能分析报告
        """
        if not step_results:
            return PerformanceReport(0, 0, "", "", {}, [], [], [])
        
        # 计算总时间和平均时间
        total_time = sum(step.execution_time for step in step_results)
        avg_step_time = total_time / len(step_results)
        
        # 找出最慢和最快的步骤
        slowest_step_result = max(step_results, key=lambda x: x.execution_time)
        fastest_step_result = min(step_results, key=lambda x: x.execution_time)
        
        slowest_step = f"{slowest_step_result.step_type.value} ({slowest_step_result.execution_time:.3f}s)"
        fastest_step = f"{fastest_step_result.step_type.value} ({fastest_step_result.execution_time:.3f}s)"
        
        # 按步骤类型统计时间
        step_time_breakdown = {}
        for step in step_results:
            step_type = step.step_type.value
            if step_type not in step_time_breakdown:
                step_time_breakdown[step_type] = 0
            step_time_breakdown[step_type] += step.execution_time
        
        # 按循环分析性能
        cycle_performance = []
        current_cycle = 1
        cycle_steps = []
        
        for step in step_results:
            if step.step_type == StepType.CYCLE_START:
                if cycle_steps:
                    # 完成上一个循环的统计
                    cycle_time = sum(s.execution_time for s in cycle_steps)
                    cycle_performance.append({
                        "cycle": current_cycle - 1,
                        "total_time": cycle_time,
                        "step_count": len(cycle_steps),
                        "avg_time": cycle_time / len(cycle_steps) if cycle_steps else 0
                    })
                    cycle_steps = []
                current_cycle += 1
            cycle_steps.append(step)
        
        # 处理最后一个循环
        if cycle_steps:
            cycle_time = sum(s.execution_time for s in cycle_steps)
            cycle_performance.append({
                "cycle": current_cycle - 1,
                "total_time": cycle_time,
                "step_count": len(cycle_steps),
                "avg_time": cycle_time / len(cycle_steps) if cycle_steps else 0
            })
        
        return PerformanceReport(
            total_time=total_time,
            avg_step_time=avg_step_time,
            slowest_step=slowest_step,
            fastest_step=fastest_step,
            step_time_breakdown=step_time_breakdown,
            cycle_performance=cycle_performance,
            memory_usage_trend=[],  # 需要从调试状态中获取
            token_usage_trend=[]    # 需要从调试状态中获取
        )
    
    @staticmethod
    def visualize_execution_flow(step_results: List[StepResult]) -> str:
        """可视化执行流程
        
        Args:
            step_results: 步骤执行结果列表
            
        Returns:
            str: 可视化的执行流程图
        """
        if not step_results:
            return "无执行步骤"
        
        flow_chart = ["🔄 认知循环执行流程", "=" * 50]
        
        for i, step in enumerate(step_results):
            # 步骤信息
            step_line = f"{i+1:2d}. {step.step_type.value}"
            
            # 添加层级信息
            layer_icon = {
                "MetaCognitive": "👥",
                "Ego": "🧠", 
                "Id": "💫",
                "Body": "🏃",
                "System": "⚙️"
            }.get(step.agent_layer, "❓")
            
            step_line += f" ({layer_icon} {step.agent_layer})"
            
            # 添加执行时间
            step_line += f" - {step.execution_time:.3f}s"
            
            # 添加状态信息
            if step.error:
                step_line += " ❌"
            else:
                step_line += " ✅"
            
            flow_chart.append(step_line)
            
            # 添加决策信息
            if step.debug_info.get("decision_type"):
                decision = step.debug_info["decision_type"]
                flow_chart.append(f"    └─ 决策: {decision}")
            
            # 添加Agent选择信息
            if step.debug_info.get("selected_agent"):
                agent = step.debug_info["selected_agent"]
                flow_chart.append(f"    └─ 执行者: {agent}")
            
            # 添加执行指令信息（简短显示）
            if step.debug_info.get("instruction"):
                instruction = step.debug_info["instruction"]
                # 截断长指令
                if len(instruction) > 50:
                    instruction = instruction[:47] + "..."
                flow_chart.append(f"    └─ 指令: {instruction}")
        
        flow_chart.append("=" * 50)
        flow_chart.append(f"总步骤: {len(step_results)}")
        flow_chart.append(f"总时间: {sum(s.execution_time for s in step_results):.3f}s")
        
        return "\n".join(flow_chart)
    
    @staticmethod
    def export_debug_session(debug_state: DebugState, file_path: str) -> bool:
        """导出调试会话
        
        Args:
            debug_state: 调试状态
            file_path: 导出文件路径
            
        Returns:
            bool: 是否导出成功
        """
        try:
            # 准备导出数据
            export_data = {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "debug_state": {
                    "current_step": debug_state.current_step.value,
                    "cycle_count": debug_state.cycle_count,
                    "is_finished": debug_state.is_finished,
                    "execution_start_time": debug_state.execution_start_time.isoformat() if debug_state.execution_start_time else None,
                },
                "step_history": [
                    {
                        "step_type": step.step_type.value,
                        "step_id": step.step_id,
                        "timestamp": step.timestamp.isoformat(),
                        "execution_time": step.execution_time,
                        "agent_layer": step.agent_layer,
                        "debug_info": step.debug_info,
                        "error": str(step.error) if step.error else None
                    }
                    for step in debug_state.step_history
                ],
                "performance_metrics": debug_state.performance_metrics.__dict__,
                "breakpoints": [
                    {
                        "id": bp.id,
                        "step_type": bp.step_type.value,
                        "condition": bp.condition,
                        "hit_count": bp.hit_count,
                        "enabled": bp.enabled,
                        "description": bp.description
                    }
                    for bp in debug_state.breakpoints
                ]
            }
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"导出调试会话失败: {e}")
            return False
    
    @staticmethod
    def import_debug_session(file_path: str) -> Optional[Dict]:
        """导入调试会话
        
        Args:
            file_path: 导入文件路径
            
        Returns:
            Optional[Dict]: 导入的调试会话数据，失败时返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ 成功导入调试会话")
            print(f"   版本: {data.get('version', '未知')}")
            print(f"   时间: {data.get('timestamp', '未知')}")
            print(f"   步骤数: {len(data.get('step_history', []))}")
            
            return data
        except Exception as e:
            print(f"导入调试会话失败: {e}")
            return None


class CognitiveDebugger:
    """认知调试器主类"""
    
    def __init__(self, cognitive_agent: CognitiveAgent):
        """初始化调试器
        
        Args:
            cognitive_agent: 要调试的认知智能体
        """
        self.wrapped_agent = cognitive_agent
        self.debug_state = DebugState()
        self.step_executor = StepExecutor(cognitive_agent)
        self.breakpoint_manager = BreakpointManager()
        self._instruction = None
    
    def start_debug(self, instruction: str) -> None:
        """开始调试会话
        
        Args:
            instruction: 执行指令
        """
        self._instruction = instruction
        self.debug_state = DebugState()  # 重置调试状态
        self.debug_state.execution_start_time = datetime.now()
        
        print(f"🚀 开始调试认知循环")
        print(f"📝 指令: {instruction}")
        print(f"⚙️  智能体配置:")
        
        # 安全地获取智能体属性
        if hasattr(self.wrapped_agent, 'max_cycles'):
            print(f"   - 最大循环数: {self.wrapped_agent.max_cycles}")
        else:
            print(f"   - 最大循环数: 未设置")
            
        if hasattr(self.wrapped_agent, 'enable_meta_cognition'):
            print(f"   - 元认知启用: {self.wrapped_agent.enable_meta_cognition}")
        else:
            print(f"   - 元认知启用: 未设置")
            
        if hasattr(self.wrapped_agent, 'evaluation_mode'):
            print(f"   - 评估模式: {self.wrapped_agent.evaluation_mode}")
        else:
            print(f"   - 评估模式: 未设置")
            
        print(f"🔧 调试器就绪，使用 run_one_step() 开始单步执行\n")
    
    def run_one_step(self) -> StepResult:
        """执行单步
        
        Returns:
            StepResult: 步骤执行结果
            
        Raises:
            RuntimeError: 当调试已完成时尝试执行下一步
        """
        if self.debug_state.is_finished:
            raise RuntimeError("调试已完成，无法继续执行步骤。工作流已结束。")
        
        current_step = self.debug_state.current_step
        
        # 检查断点
        context = {
            "cycle_count": self.debug_state.cycle_count,
            "current_step": current_step,
            "instruction": self._instruction
        }
        
        # 安全地添加goal_achieved
        if self.debug_state.workflow_context:
            context["goal_achieved"] = self.debug_state.workflow_context.goal_achieved
        else:
            context["goal_achieved"] = False
        
        hit_breakpoint = self.breakpoint_manager.check_breakpoint(current_step, context)
        if hit_breakpoint:
            print(f"🛑 断点触发: {hit_breakpoint.description or hit_breakpoint.step_type}")
            print(f"   断点ID: {hit_breakpoint.id}")
            print(f"   命中次数: {hit_breakpoint.hit_count}")
            self.debug_state._at_breakpoint = True  # 标记当前在断点处
            return None
        
        # 准备输入数据
        input_data = self._prepare_input_data(current_step)
        
        # 执行步骤
        step_result = self.step_executor.execute_step(current_step, input_data, self.debug_state)
        
        # 更新调试状态
        self._update_debug_state(step_result)
        
        # 确定下一步
        next_step = self.step_executor.get_next_step(current_step, step_result, self.debug_state)
        if next_step:
            self.debug_state.current_step = next_step
        
        # 打印步骤信息
        self._print_step_info(step_result)
        
        return step_result
    
    def run_steps(self, count: int) -> List[StepResult]:
        """执行指定步数
        
        Args:
            count: 要执行的步数
            
        Returns:
            List[StepResult]: 步骤执行结果列表
        """
        results = []
        for i in range(count):
            if self.debug_state.is_finished:
                print(f"⏹️  执行在第 {i+1} 步完成")
                break
            
            step_result = self.run_one_step()
            if step_result:
                results.append(step_result)
            else:
                print(f"⏸️  执行在第 {i+1} 步暂停（断点或错误）")
                break
        
        return results
    
    def run_until_breakpoint(self) -> List[StepResult]:
        """运行到下一个断点
        
        如果当前已经在断点处，会先执行一步离开当前断点，然后继续执行直到遇到下一个断点。
        
        Returns:
            List[StepResult]: 执行过程中的所有步骤结果
        """
        results = []
        
        # 如果当前在断点处，先强制执行当前步骤以离开断点
        if hasattr(self.debug_state, '_at_breakpoint') and self.debug_state._at_breakpoint:
            # 临时禁用断点检查，执行当前步骤
            current_step = self.debug_state.current_step
            if current_step and current_step != StepType.COMPLETED:
                # 准备输入数据
                input_data = self._prepare_input_data(current_step)
                
                # 执行当前步骤
                step_result = self.step_executor.execute_step(
                    current_step, 
                    input_data,
                    self.debug_state
                )
                
                if step_result:
                    # 更新调试状态
                    self.debug_state.step_history.append(step_result)
                    self.debug_state.current_step = step_result.next_step
                    
                    # 更新性能指标
                    self.debug_state.performance_metrics.step_count += 1
                    self.debug_state.performance_metrics.execution_time += step_result.execution_time
                    
                    # 如果步骤是循环结束，增加循环计数
                    if step_result.step_type == StepType.CYCLE_END:
                        self.debug_state.cycle_count += 1
                    
                    results.append(step_result)
                    self.debug_state._at_breakpoint = False
                    
                    # 检查是否完成
                    if step_result.next_step == StepType.COMPLETED:
                        self.debug_state.is_finished = True
                        return results
        
        # 继续执行直到下一个断点
        while not self.debug_state.is_finished:
            step_result = self.run_one_step()
            if step_result:
                results.append(step_result)
            else:
                # 遇到断点，停止执行
                break
        
        return results
    
    def continue_execution(self) -> List[StepResult]:
        """继续执行到下一个断点
        
        这是 run_until_breakpoint() 的别名，提供更直观的调试器命令。
        
        Returns:
            List[StepResult]: 执行过程中的所有步骤结果
            
        Example:
            >>> # 在断点处暂停后
            >>> results = debugger.continue_execution()
            >>> # 执行会继续直到下一个断点或完成
        """
        return self.run_until_breakpoint()
    
    def run_to_completion(self) -> List[StepResult]:
        """运行到结束
        
        Returns:
            List[StepResult]: 完整的执行结果
        """
        results = []
        
        print("🏃 运行到完成...")
        
        while not self.debug_state.is_finished:
            step_result = self.run_one_step()
            if step_result:
                results.append(step_result)
            else:
                break
        
        print(f"✅ 执行完成，共执行 {len(results)} 步")
        
        return results
    
    def capture_debug_snapshot(self) -> StateSnapshot:
        """捕获调试快照
        
        捕获当前调试会话的综合快照，包括工作流状态、执行进度、
        性能指标、内存使用情况和智能体层状态等全面信息。
        
        Returns:
            StateSnapshot: 包含调试会话完整信息的快照对象
        """
        if not self.debug_state.workflow_context:
            print("⚠️  调试会话尚未开始")
            return None
        
        # 计算内存使用情况
        memory_length = len(self.wrapped_agent.memory) if hasattr(self.wrapped_agent, 'memory') else 0
        memory_tokens = 0
        if hasattr(self.wrapped_agent, 'calculate_memory_tokens'):
            try:
                memory_tokens = self.wrapped_agent.calculate_memory_tokens()
            except:
                memory_tokens = 0
        
        # 收集智能体层状态
        agent_layers_status = {
            "ego": {"available": bool(self.wrapped_agent.ego)},
            "id": {"available": bool(self.wrapped_agent.id_agent)},
            "agents": {"available": bool(self.wrapped_agent.agents), "count": len(self.wrapped_agent.agents) if self.wrapped_agent.agents else 0},
            "meta_cognition": {
                "available": bool(self.wrapped_agent.meta_cognition),
                "enabled": self.wrapped_agent.enable_meta_cognition
            }
        }
        
        # 计算执行时间
        execution_time = 0
        if self.debug_state.execution_start_time:
            execution_time = (datetime.now() - self.debug_state.execution_start_time).total_seconds()
        
        snapshot = StateSnapshot(
            timestamp=datetime.now(),
            cycle_count=self.debug_state.cycle_count,
            current_step=self.debug_state.current_step,
            instruction=self.debug_state.workflow_context.instruction,
            goal_achieved=self.debug_state.workflow_context.goal_achieved,
            current_state_analysis=self.debug_state.workflow_context.current_state,
            id_evaluation=self.debug_state.workflow_context.id_evaluation,
            memory_length=memory_length,
            memory_tokens=memory_tokens,
            agent_layers_status=agent_layers_status,
            total_steps=len(self.debug_state.step_history),
            execution_time=execution_time,
            performance_metrics=self.debug_state.performance_metrics.__dict__
        )
        
        self._print_state_snapshot(snapshot)
        
        return snapshot
    
    def inspect_workflow_state(self) -> Optional[WorkflowContext]:
        """检查工作流状态
        
        直接返回WorkflowContext对象，方便访问所有工作流状态信息。
        
        Returns:
            Optional[WorkflowContext]: 工作流上下文对象，如果调试未开始则返回None
            
        Example:
            >>> workflow_context = debugger.inspect_workflow_state()
            >>> if workflow_context:
            ...     print(workflow_context.current_state)
            ...     print(workflow_context.goal_achieved)
        """
        if not self.debug_state.workflow_context:
            print("⚠️  调试会话尚未开始，无法获取工作流状态")
            return None
            
        return self.debug_state.workflow_context
    
    def set_breakpoint(self, step_type: StepType, condition: str = None, description: str = "") -> str:
        """设置断点
        
        Args:
            step_type: 断点的步骤类型
            condition: 可选的断点条件（Python表达式）
            description: 断点描述
            
        Returns:
            str: 断点ID
        """
        breakpoint = Breakpoint(
            id="",  # 将在__post_init__中生成
            step_type=step_type,
            condition=condition,
            description=description
        )
        
        breakpoint_id = self.breakpoint_manager.add_breakpoint(breakpoint)
        
        print(f"✅ 断点已设置")
        print(f"   ID: {breakpoint_id}")
        print(f"   步骤: {step_type.value}")
        if condition:
            print(f"   条件: {condition}")
        if description:
            print(f"   描述: {description}")
        
        return breakpoint_id
    
    def remove_breakpoint(self, breakpoint_id: str) -> bool:
        """移除断点
        
        Args:
            breakpoint_id: 断点ID
            
        Returns:
            bool: 是否成功移除
        """
        success = self.breakpoint_manager.remove_breakpoint(breakpoint_id)
        
        if success:
            print(f"✅ 断点 {breakpoint_id} 已移除")
        else:
            print(f"❌ 断点 {breakpoint_id} 不存在")
        
        return success
    
    def list_breakpoints(self) -> List[Breakpoint]:
        """列出所有断点
        
        Returns:
            List[Breakpoint]: 断点列表
        """
        breakpoints = self.breakpoint_manager.list_breakpoints()
        
        if not breakpoints:
            print("📋 当前没有设置断点")
        else:
            print(f"📋 当前断点列表 ({len(breakpoints)} 个):")
            for bp in breakpoints:
                status = "🟢" if bp.enabled else "🔴"
                print(f"   {status} {bp.id}: {bp.step_type.value}")
                if bp.condition:
                    print(f"      条件: {bp.condition}")
                if bp.description:
                    print(f"      描述: {bp.description}")
                print(f"      命中次数: {bp.hit_count}")
        
        return breakpoints
    
    def clear_breakpoints(self) -> None:
        """清除所有断点"""
        self.breakpoint_manager.breakpoints.clear()
        print("✅ 所有断点已清除")
    
    def get_execution_trace(self) -> List[StepResult]:
        """获取执行轨迹
        
        Returns:
            List[StepResult]: 执行轨迹
        """
        return self.debug_state.step_history.copy()
    
    def step_back(self, steps: int = 1) -> bool:
        """回退步骤
        
        Args:
            steps: 要回退的步数
            
        Returns:
            bool: 是否成功回退
        """
        if steps <= 0:
            print("❌ 回退步数必须大于0")
            return False
        
        if len(self.debug_state.step_history) < steps:
            print(f"❌ 无法回退 {steps} 步，当前只有 {len(self.debug_state.step_history)} 步历史")
            return False
        
        # 保存当前状态到快照
        self._save_state_snapshot()
        
        # 回退步骤历史
        for _ in range(steps):
            if self.debug_state.step_history:
                removed_step = self.debug_state.step_history.pop()
                print(f"🔙 回退步骤: {removed_step.step_type.value}")
        
        # 恢复当前步骤
        if self.debug_state.step_history:
            last_step = self.debug_state.step_history[-1]
            self.debug_state.current_step = last_step.next_step or StepType.COMPLETED
        else:
            self.debug_state.current_step = StepType.INIT
        
        # 更新其他状态
        self.debug_state.is_finished = False
        
        print(f"✅ 成功回退 {steps} 步，当前步骤: {self.debug_state.current_step.value}")
        return True
    
    def get_performance_report(self) -> PerformanceReport:
        """获取性能分析报告
        
        Returns:
            PerformanceReport: 性能分析报告
        """
        return DebugUtils.analyze_performance(self.debug_state.step_history)
    
    def visualize_execution_flow(self) -> str:
        """可视化当前执行流程
        
        Returns:
            str: 可视化的执行流程图
        """
        return DebugUtils.visualize_execution_flow(self.debug_state.step_history)
    
    def export_session(self, file_path: str) -> bool:
        """导出调试会话
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            bool: 是否导出成功
        """
        return DebugUtils.export_debug_session(self.debug_state, file_path)
    
    def import_session(self, file_path: str) -> bool:
        """导入调试会话（只导入数据，不恢复执行状态）
        
        Args:
            file_path: 导入文件路径
            
        Returns:
            bool: 是否导入成功
        """
        data = DebugUtils.import_debug_session(file_path)
        if data:
            print("⚠️  注意：导入的会话数据仅供查看，不会恢复执行状态")
            return True
        return False
    
    def reset_debug(self) -> None:
        """重置调试会话"""
        self.debug_state = DebugState()
        self._instruction = None
        print("🔄 调试会话已重置")
    
    # 私有辅助方法
    def _prepare_input_data(self, step_type: StepType) -> Any:
        """为步骤准备输入数据"""
        if step_type == StepType.INIT:
            return self._instruction
        elif len(self.debug_state.step_history) > 0:
            return self.debug_state.step_history[-1].output_data
        else:
            return None
    
    def _update_debug_state(self, step_result: StepResult):
        """更新调试状态"""
        self.debug_state.step_history.append(step_result)
        
        # 更新性能指标
        self.debug_state.performance_metrics.step_count += 1
        self.debug_state.performance_metrics.execution_time += step_result.execution_time
        
        # 保存状态快照（每5步保存一次）
        if len(self.debug_state.step_history) % 5 == 0:
            self._save_state_snapshot()
        
        # 如果有错误，标记为完成
        if step_result.error:
            self.debug_state.is_finished = True
    
    def _save_state_snapshot(self):
        """保存当前状态快照"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "current_step": self.debug_state.current_step.value,
            "cycle_count": self.debug_state.cycle_count,
            "step_count": len(self.debug_state.step_history),
            "is_finished": self.debug_state.is_finished
        }
        
        # 限制快照数量，保持最近的20个
        self.debug_state.state_snapshots.append(snapshot)
        if len(self.debug_state.state_snapshots) > 20:
            self.debug_state.state_snapshots.pop(0)
    
    def _print_step_info(self, step_result: StepResult):
        """打印步骤信息"""
        print(f"📍 步骤: {step_result.step_type.value}")
        print(f"   层级: {step_result.agent_layer}")
        print(f"   耗时: {step_result.execution_time:.3f}s")
        
        # 如果是决策判断步骤，显示Agent选择信息
        if step_result.step_type == StepType.DECISION_MAKING and step_result.debug_info:
            if step_result.debug_info.get("selected_agent"):
                print(f"   🎯 选择执行者: {step_result.debug_info['selected_agent']}")
            if step_result.debug_info.get("available_agents"):
                print(f"   👥 可用执行者: {', '.join(step_result.debug_info['available_agents'])}")
        
        # 如果是身体执行步骤，显示执行者信息
        if step_result.step_type == StepType.BODY_EXECUTION and step_result.debug_info:
            if step_result.debug_info.get("selected_agent"):
                print(f"   🏃 执行者: {step_result.debug_info['selected_agent']}")
        
        if step_result.error:
            print(f"   ❌ 错误: {step_result.error}")
        else:
            print(f"   ✅ 输出: {self._format_output(step_result.output_data)}")
        
        if step_result.debug_info:
            # 特殊处理execution_result中的code和return_value字段
            if 'execution_result' in step_result.debug_info and isinstance(step_result.debug_info['execution_result'], dict):
                debug_info_copy = step_result.debug_info.copy()
                exec_result = debug_info_copy['execution_result']
                
                # 格式化code字段
                if 'code' in exec_result and exec_result['code']:
                    print(f"   🔍 调试信息:")
                    # 打印其他调试信息
                    for key, value in debug_info_copy.items():
                        if key != 'execution_result':
                            print(f"      {key}: {value}")
                    
                    # 打印execution_result的其他字段
                    print(f"      execution_result:")
                    for key, value in exec_result.items():
                        if key == 'code':
                            print(f"         code:")
                            # 按行打印代码
                            code_lines = exec_result['code'].split('\n')
                            for line in code_lines:
                                print(f"            {line}")
                        elif key == 'return_value' and value:
                            print(f"         return_value:")
                            # 按行打印返回值
                            return_lines = str(value).split('\n')
                            for line in return_lines:
                                print(f"            {line}")
                        else:
                            print(f"         {key}: {value}")
                else:
                    print(f"   🔍 调试信息: {step_result.debug_info}")
            else:
                print(f"   🔍 调试信息: {step_result.debug_info}")
        
        if step_result.next_step:
            print(f"   ➡️  下一步: {step_result.next_step.value}")
        
        print()
    
    def _print_state_snapshot(self, snapshot: StateSnapshot):
        """打印状态快照"""
        print(f"📊 状态快照 ({snapshot.timestamp.strftime('%H:%M:%S')})")
        print(f"   当前步骤: {snapshot.current_step.value}")
        print(f"   循环轮数: {snapshot.cycle_count}")
        print(f"   总步骤数: {snapshot.total_steps}")
        print(f"   执行时间: {snapshot.execution_time:.2f}s")
        print(f"   目标达成: {'✅' if snapshot.goal_achieved else '❌'}")
        print(f"   内存使用: {snapshot.memory_length} 条消息 ({snapshot.memory_tokens} tokens)")
        print(f"   智能体层级:")
        for layer, status in snapshot.agent_layers_status.items():
            available = "✅" if status.get("available") else "❌"
            enabled = ""
            if layer == "meta_cognition":
                enabled = f" ({'启用' if status.get('enabled') else '禁用'})"
            elif layer == "agents":
                count = status.get("count", 0)
                enabled = f" ({count} 个Agent)"
            print(f"     {layer}: {available}{enabled}")
        
        # 显示当前Agent选择信息（如果有）
        if hasattr(self.debug_state, 'selected_agent') and self.debug_state.selected_agent:
            print(f"   当前执行者: {self.debug_state.selected_agent}")
        
        print()
    
    def _format_output(self, output_data: Any) -> str:
        """格式化输出数据"""
        if output_data is None:
            return "None"
        elif isinstance(output_data, str):
            return output_data[:100] + "..." if len(output_data) > 100 else output_data
        elif isinstance(output_data, Result):
            return f"Result(success={output_data.success})"
        else:
            return str(output_data)[:100] + "..." if len(str(output_data)) > 100 else str(output_data)