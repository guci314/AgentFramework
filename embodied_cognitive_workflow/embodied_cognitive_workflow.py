"""
具身认知工作流协调器

基于具身认知工作流理论的主协调器实现。
协调自我、本我和身体三层架构的交互和认知循环。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pythonTask import Agent
from ego_agent import EgoAgent
from id_agent import IdAgent
from agent_base import Result
from langchain_core.language_models import BaseChatModel
from typing import List, Optional, Dict, Any
import logging
from enum import Enum
from dataclasses import dataclass


class WorkflowStatus(Enum):
    """工作流状态枚举"""
    NOT_STARTED = "未开始"
    RUNNING = "运行中"
    SUCCESS = "成功"
    FAILED = "失败"
    TIMEOUT = "超时"
    EXCEPTION = "异常"


class DecisionType(Enum):
    """决策类型枚举"""
    REQUEST_EVALUATION = "请求评估"
    JUDGMENT_FAILED = "判断失败"
    CONTINUE_CYCLE = "继续循环"


@dataclass
class CycleOutcome:
    """单轮认知循环的执行结果"""
    continue_workflow: bool  # 是否继续工作流
    cycle_data: Optional[str] = None  # 本轮循环产生的数据
    final_result: Optional[Result] = None  # 如果工作流结束，包含最终结果
    decision_type: Optional[DecisionType] = None  # 本轮的决策类型


class WorkflowContext:
    """工作流上下文管理器"""
    
    def __init__(self, instruction: str):
        self.instruction = instruction
        self.history = []
        self.current_cycle = 0
        self.current_state = ""  # 当前状态分析结果
        self.id_evaluation = ""  # 本我对当前状态的评估结果
        self.goal_achieved = False  # 目标是否已达成
    
    def add_cycle_result(self, cycle_num: int, result: str):
        """添加循环结果"""
        self.history.append(f"第{cycle_num}轮结果：{result}")
    
    def update_current_state(self, state_analysis: str):
        """更新当前状态"""
        self.current_state = state_analysis
    
    def update_id_evaluation(self, evaluation_result: str):
        """更新本我的评估结果"""
        self.id_evaluation = evaluation_result
    
    def update_goal_status(self, achieved: bool):
        """更新目标达成状态"""
        self.goal_achieved = achieved
    
    def get_current_context(self) -> str:
        """获取当前上下文"""
        base_context = f"用户指令：{self.instruction}"
        if self.current_state:
            base_context += f"\n当前状态：{self.current_state}"
        if self.id_evaluation:
            base_context += f"\n本我评估：{self.id_evaluation}"
        if self.goal_achieved:
            base_context += f"\n目标状态：已达成"
        else:
            base_context += f"\n目标状态：未达成"
        if self.history:
            base_context += "\n\n" + "\n\n".join(self.history)
        return base_context


class EmbodiedCognitiveWorkflow:
    """
    具身认知工作流协调器
    
    负责协调心灵层（自我+本我）和身体层的交互，
    实现"走一步看一步"的动态认知循环。
    """
    
    def __init__(self, 
                 llm: BaseChatModel,
                 body_config: Optional[dict] = None,
                 ego_config: Optional[dict] = None,
                 id_config: Optional[dict] = None,
                 max_cycles: int = 50,
                 verbose: bool = True):
        """
        初始化具身认知工作流系统
        
        Args:
            llm: 语言模型
            body_config: 身体(Agent)的配置参数
            ego_config: 自我智能体的配置参数
            id_config: 本我智能体的配置参数
            max_cycles: 防止无限循环的最大次数限制
            verbose: 是否输出详细的过程日志
        """
        self.llm = llm
        self.max_cycles = max_cycles
        self.verbose = verbose
        
        # 初始化身体层（使用现有的Agent类）
        body_config = body_config or {}
        self.body = Agent(llm=llm, **body_config)
        self.body.name = "身体"
        self.body.loadKnowledge('unittest的测试输出在标准错误流而不是标准输出流')
        self.body.loadKnowledge('在Jupyter notebook中模块重载方法：使用importlib.reload()重新加载已修改的模块。具体用法：import importlib; importlib.reload(your_module)。这样可以在不重启notebook的情况下获取模块的最新修改。')
        
        # 初始化心灵层
        ego_config = ego_config or {}
        id_config = id_config or {}
        
        self.ego = EgoAgent(llm=llm, **ego_config)
        self.id_agent = IdAgent(llm=llm, **id_config)
        
        # 工作流状态
        self._status = WorkflowStatus.NOT_STARTED
        self.current_cycle_count = 0
        self.workflow_status = "未开始"
        self.execution_history = []
        
        if self.verbose:
            logging.basicConfig(level=logging.INFO)
    
    def execute_cognitive_cycle(self, instruction: str) -> Result:
        """
        执行完整的具身认知工作流
        
        Args:
            instruction: 用户指令
            
        Returns:
            Result: 最终执行结果
        """
        try:
            self._log(f"开始执行认知循环，用户指令：{instruction}")
            
            # 初始化工作流
            context = self._initialize_workflow(instruction)
            
            # 执行主循环
            result = self._execute_main_loop(context)
            
            return result
            
        except Exception as e:
            return self._handle_workflow_exception(e)
    
    def _initialize_workflow(self, instruction: str) -> WorkflowContext:
        """
        初始化工作流
        
        Args:
            instruction: 用户指令
            
        Returns:
            WorkflowContext: 初始化后的工作流上下文
        """
        self._log("初始化工作流")
        
        # 本我初始化任务规格（包含目标、标准、验证方法）
        self._log("本我初始化任务规格")
        self.id_agent.initialize_value_system(instruction)
        self._log(f"任务规格初始化完成：{self.id_agent.get_task_specification()}")
        
        # 设置工作流状态
        self._set_status(WorkflowStatus.RUNNING)
        
        # 创建上下文
        context = WorkflowContext(instruction)
        
        return context
    
    def _execute_main_loop(self, context: WorkflowContext) -> Result:
        """
        执行主循环
        
        Args:
            context: 工作流上下文
            
        Returns:
            Result: 执行结果
        """
        while context.current_cycle < self.max_cycles:
            context.current_cycle += 1
            self.current_cycle_count = context.current_cycle
            self._log(f"\n=== 认知循环第 {context.current_cycle} 轮 ===")
            
            # 执行单轮认知循环
            outcome = self._execute_single_cycle(context)
            
            # 根据循环结果决定下一步
            if not outcome.continue_workflow:
                # 工作流结束，返回最终结果
                return outcome.final_result
            
            # 如果有循环数据，记录到历史中
            if outcome.cycle_data:
                context.add_cycle_result(context.current_cycle, outcome.cycle_data)
        
        # 超过最大循环次数
        return self._handle_timeout()
    
    def _execute_single_cycle(self, context: WorkflowContext) -> CycleOutcome:
        """
        执行单轮认知循环
        
        Args:
            context: 工作流上下文
            
        Returns:
            CycleOutcome: 循环执行结果
        """
        # 自我分析当前状态并更新到上下文
        self._analyze_current_state(context)
        
        # 自我决策下一步行动
        decision = self._make_decision(context.current_state)
        
        # 根据决策类型执行相应操作
        if decision == DecisionType.REQUEST_EVALUATION:
            return self._handle_evaluation_request(context)
        
        elif decision == DecisionType.JUDGMENT_FAILED:
            return self._handle_judgment_failed(context)
        
        elif decision == DecisionType.CONTINUE_CYCLE:
            return self._handle_continue_cycle(context)
        
        else:
            # 默认请求评估
            self._log(f"未知的决策结果：{decision}，默认请求评估")
            return self._handle_evaluation_request(context)
    
    def _analyze_current_state(self, context: WorkflowContext) -> None:
        """
        分析当前状态并更新到上下文
        
        Args:
            context: 工作流上下文
        """
        current_context = context.get_current_context()
        state_analysis = self.ego.analyze_current_state(current_context)
        self._log(f"自我状态分析：{state_analysis}")
        
        # 更新到上下文中
        context.update_current_state(state_analysis)
    
    def _make_decision(self, state_analysis: str) -> DecisionType:
        """
        做出决策
        
        Args:
            state_analysis: 状态分析结果
            
        Returns:
            DecisionType: 决策类型
        """
        next_action = self.ego.decide_next_action(state_analysis)
        self._log(f"自我决策：{next_action}")
        
        # 将字符串决策转换为枚举
        decision_mapping = {
            "请求评估": DecisionType.REQUEST_EVALUATION,
            "判断失败": DecisionType.JUDGMENT_FAILED,
            "继续循环": DecisionType.CONTINUE_CYCLE
        }
        
        return decision_mapping.get(next_action, DecisionType.REQUEST_EVALUATION)
    
    def _handle_judgment_failed(self, context: WorkflowContext) -> CycleOutcome:
        """
        处理判断失败
        
        Args:
            context: 工作流上下文
            
        Returns:
            CycleOutcome: 包含失败结果的循环结果
        """
        self._log("自我判断工作流失败，目标无法达成")
        self._set_status(WorkflowStatus.FAILED)
        
        final_result = Result(False, "", "", None, 
                           f"工作流失败：自我判断目标无法达成。状态分析：{context.current_state}")
        
        return CycleOutcome(
            continue_workflow=False,
            final_result=final_result,
            decision_type=DecisionType.JUDGMENT_FAILED
        )
    
    def _handle_continue_cycle(self, context: WorkflowContext) -> CycleOutcome:
        """
        处理继续循环
        
        Args:
            context: 工作流上下文
            
        Returns:
            CycleOutcome: 包含循环数据的循环结果
        """
        cycle_data = self._execute_cognitive_step(context)
        
        return CycleOutcome(
            continue_workflow=True,
            cycle_data=cycle_data,
            decision_type=DecisionType.CONTINUE_CYCLE
        )
    
    def _handle_timeout(self) -> Result:
        """
        处理超时
        
        Returns:
            Result: 超时结果
        """
        self._log(f"达到最大循环次数 {self.max_cycles}，工作流终止")
        self._set_status(WorkflowStatus.TIMEOUT)
        return Result(False, "", "", None, 
                     f"工作流超时：达到最大循环次数 {self.max_cycles}")
    
    def _handle_workflow_exception(self, e: Exception) -> Result:
        """
        处理工作流异常
        
        Args:
            e: 异常对象
            
        Returns:
            Result: 异常结果
        """
        self._log(f"工作流执行出现异常：{str(e)}")
        self._set_status(WorkflowStatus.EXCEPTION)
        return Result(False, "", "", None, f"工作流执行异常：{str(e)}")
    
    def _set_status(self, status: WorkflowStatus):
        """设置工作流状态"""
        self._status = status
        self.workflow_status = status.value  # 保持向后兼容
    
    @property
    def current_cycle_count(self) -> int:
        """当前循环次数（向后兼容）"""
        return getattr(self, '_current_cycle_count', 0)
    
    @current_cycle_count.setter
    def current_cycle_count(self, value: int):
        """设置当前循环次数"""
        self._current_cycle_count = value
    
    def _handle_evaluation_request(self, context: WorkflowContext) -> CycleOutcome:
        """
        处理自我的评估请求
        
        Args:
            context: 工作流上下文
            
        Returns:
            CycleOutcome: 包含评估结果的循环结果
        """
        # 自我请求本我评估
        evaluation_request = self.ego.request_id_evaluation(context.current_state)
        self._log(f"自我评估请求：{evaluation_request}")
        
        # 本我生成评估指令
        evaluation_instruction = self.id_agent.generate_evaluation_instruction(evaluation_request)
        self._log(f"本我评估指令：{evaluation_instruction}")
        
        # 身体执行评估指令（观察）
        observation_result = self.body.execute_sync(evaluation_instruction)
        self._log(f"身体观察结果：{observation_result.return_value}")
        
        # 本我评估目标达成情况
        evaluation_json = self.id_agent.evaluate_goal_achievement(observation_result.return_value)
        self._log(f"本我评估结果：{evaluation_json}")
        
        # 解析JSON评估结果
        try:
            import json
            evaluation_data = json.loads(evaluation_json)
            goal_achieved = evaluation_data.get("目标是否达成", False)
            reason = evaluation_data.get("原因", "未提供原因")
            
            # 更新上下文
            context.update_id_evaluation(reason)
            context.update_goal_status(goal_achieved)
            
            if goal_achieved:
                # 目标达成，工作流成功结束
                self._log("本我确认目标达成，工作流成功结束")
                self._set_status(WorkflowStatus.SUCCESS)
                
                # 获取最终状态作为结果
                final_status_query = "请查看当前的工作成果和状态，提供一个完整的总结"
                final_result = self.body.chat_sync(final_status_query)
                
                final_result = Result(True, "", "", None, 
                                    f"工作流成功完成。目标达成确认：{reason}\n最终状态：{final_result.return_value}")
                
                return CycleOutcome(
                    continue_workflow=False,
                    final_result=final_result,
                    decision_type=DecisionType.REQUEST_EVALUATION
                )
            else:
                # 目标未达成，继续循环
                self._log(f"目标未达成，继续循环。原因：{reason}")
                return CycleOutcome(
                    continue_workflow=True,
                    cycle_data=f"评估结果：{reason}",
                    decision_type=DecisionType.REQUEST_EVALUATION
                )
                
        except (json.JSONDecodeError, KeyError) as e:
            # JSON解析失败，使用备用逻辑
            self._log(f"JSON解析失败，使用备用逻辑：{e}")
            context.update_id_evaluation(evaluation_json)
            context.update_goal_status(False)
            
            if "工作流结束" in evaluation_json:
                self._set_status(WorkflowStatus.SUCCESS)
                final_result = Result(True, "", "", None, f"工作流成功完成：{evaluation_json}")
                return CycleOutcome(
                    continue_workflow=False,
                    final_result=final_result,
                    decision_type=DecisionType.REQUEST_EVALUATION
                )
            else:
                return CycleOutcome(
                    continue_workflow=True,
                    cycle_data=evaluation_json,
                    decision_type=DecisionType.REQUEST_EVALUATION
                )
    
    def _execute_cognitive_step(self, context: WorkflowContext) -> Optional[str]:
        """
        执行一个认知步骤（观察或执行）
        
        Args:
            context: 工作流上下文，包含当前状态、本我评估等完整信息
            
        Returns:
            Optional[str]: 执行结果，失败时返回None
        """
        try:
            # 自我决定是生成观察指令还是执行指令
            # 这里可以让自我根据状态分析来决定
            # 获取完整的上下文信息
            current_context = context.get_current_context()
            
            decision_message = f"""基于完整的上下文信息，决定下一步需要观察还是执行：

完整上下文：
{current_context}

请综合考虑以下信息后选择行动类型：
- 当前状态分析结果
- 本我的评估反馈（如果有）
- 目标达成情况
- 历史执行记录

返回JSON格式：
{{
    "行动类型": "观察或执行",
    "理由": "简要说明理由"
}}

可选择：
- "观察" - 如果需要了解更多信息（避免重复本我已评估的内容）
- "执行" - 如果需要执行具体操作或已有足够信息"""
            
            decision_result = self.ego.chat_sync(decision_message, response_format={"type": "json_object"})
            
            try:
                import json
                response_data = json.loads(decision_result.return_value.strip())
                action_type = response_data.get("行动类型", "执行").strip()
            except (json.JSONDecodeError, KeyError):
                # JSON解析失败，默认执行
                action_type = "执行"
            
            if "观察" in action_type:
                # 生成观察指令（传入完整上下文）
                observation_instruction = self.ego.generate_observation_instruction(current_context)
                self._log(f"生成观察指令：{observation_instruction}")
                
                # 身体执行观察（使用execute_sync）
                observation_result = self.body.execute_sync(observation_instruction)
                if observation_result.success:
                    self._log(f"观察成功：{observation_result.return_value}")
                    return f"观察结果：{observation_result.return_value}"
                else:
                    self._log(f"观察失败：{observation_result.stderr}")
                    return None
            
            else:  # 默认执行
                # 生成执行指令（传入完整上下文）
                execution_instruction = self.ego.generate_execution_instruction(current_context)
                self._log(f"生成执行指令：{execution_instruction}")
                
                # 身体执行指令
                execution_result = self.body.execute_sync(execution_instruction)
                if execution_result.success:
                    self._log(f"执行成功：{execution_result.return_value}")
                    return f"执行结果：{execution_result.return_value}"
                else:
                    # 执行失败，让自我处理错误
                    error_handling = self.ego.handle_execution_error(
                        execution_result.stderr or "执行失败", execution_instruction)
                    self._log(f"执行失败，错误处理：{error_handling}")
                    return f"执行失败，错误处理方案：{error_handling}"
                    
        except Exception as e:
            self._log(f"认知步骤执行异常：{str(e)}")
            return None
    
    def _log(self, message: str):
        """记录日志"""
        if self.verbose:
            print(f"[具身认知工作流] {message}")
            logging.info(message)
    
    def get_workflow_status(self) -> dict:
        """
        获取当前工作流状态
        
        Returns:
            dict: 包含状态信息的字典
        """
        return {
            "状态": self.workflow_status,
            "当前循环次数": self.current_cycle_count,
            "最大循环次数": self.max_cycles,
            "目标描述": self.id_agent.get_current_goal(),
            "价值标准": self.id_agent.get_value_standard()
        }
    
    def reset_workflow(self):
        """重置工作流状态"""
        self.current_cycle_count = 0
        self._set_status(WorkflowStatus.NOT_STARTED)
        self.execution_history.clear()
        
        # 清理各组件的记忆（如果需要）
        # 注意：这可能会清除有用的知识，谨慎使用
        # self.ego.memory.clear()
        # self.id_agent.memory.clear()
        # self.body.thinker.memory.clear()
    
    def load_knowledge(self, knowledge: str):
        """
        向所有组件加载知识
        
        Args:
            knowledge: 要加载的知识内容
        """
        self.ego.loadKnowledge(knowledge)
        self.id_agent.loadKnowledge(knowledge)
        self.body.loadKnowledge(knowledge)
        self._log(f"已向所有组件加载知识：{knowledge[:100]}...")
    
    def load_python_modules(self, module_list: List[str]):
        """
        向身体加载Python模块
        
        Args:
            module_list: Python模块名称列表
        """
        self.body.loadPythonModules(module_list)
        self._log(f"已向身体加载Python模块：{module_list}")


# 便利函数：快速创建和使用具身认知工作流
def create_embodied_cognitive_workflow(llm: BaseChatModel, **kwargs) -> EmbodiedCognitiveWorkflow:
    """
    便利函数：创建具身认知工作流实例
    
    Args:
        llm: 语言模型
        **kwargs: 其他配置参数
        
    Returns:
        EmbodiedCognitiveWorkflow: 工作流实例
    """
    return EmbodiedCognitiveWorkflow(llm=llm, **kwargs)


def execute_embodied_cognitive_task(llm: BaseChatModel, task_description: str, **kwargs) -> Result:
    """
    便利函数：一次性执行具身认知任务
    
    Args:
        llm: 语言模型
        task_description: 任务描述
        **kwargs: 其他配置参数
        
    Returns:
        Result: 执行结果
    """
    workflow = create_embodied_cognitive_workflow(llm, **kwargs)
    return workflow.execute_cognitive_cycle(task_description)