"""
具身认知工作流协调器 - 优化版本

展示如何优化 execute_cognitive_cycle 方法的重构方案
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


class EmbodiedCognitiveWorkflowOptimized:
    """
    具身认知工作流协调器 - 优化版本
    
    优化内容：
    1. 拆分大方法为小方法
    2. 使用枚举代替魔法字符串
    3. 统一状态管理
    4. 改善错误处理
    5. 提高可测试性
    """
    
    def __init__(self, 
                 llm: BaseChatModel,
                 body_config: Optional[dict] = None,
                 ego_config: Optional[dict] = None,
                 id_config: Optional[dict] = None,
                 max_cycles: int = 50,
                 verbose: bool = True):
        """初始化具身认知工作流系统"""
        self.llm = llm
        self.max_cycles = max_cycles
        self.verbose = verbose
        
        # 初始化身体层
        body_config = body_config or {}
        self.body = Agent(llm=llm, **body_config)
        self.body.name = "身体"
        
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
    
    # ============== 主方法 ==============
    
    def execute_cognitive_cycle(self, instruction: str) -> Result:
        """
        执行完整的具身认知工作流 - 优化版本
        
        优化点：
        1. 方法职责单一，只负责协调
        2. 错误处理集中化
        3. 状态管理统一
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
    
    # ============== 初始化相关 ==============
    
    def _initialize_workflow(self, instruction: str) -> WorkflowContext:
        """
        初始化工作流
        
        职责：
        1. 设置任务规格
        2. 初始化状态
        3. 创建上下文
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
    
    # ============== 主循环相关 ==============
    
    def _execute_main_loop(self, context: WorkflowContext) -> Result:
        """
        执行主循环
        
        职责：
        1. 控制循环次数
        2. 协调单轮执行
        3. 处理循环结束
        """
        while context.current_cycle < self.max_cycles:
            context.current_cycle += 1
            self.current_cycle_count = context.current_cycle
            self._log(f"\n=== 认知循环第 {context.current_cycle} 轮 ===")
            
            # 执行单轮认知循环
            result = self._execute_single_cycle(context)
            
            if result:  # 如果有结果返回，说明工作流结束
                return result
        
        # 超过最大循环次数
        return self._handle_timeout()
    
    def _execute_single_cycle(self, context: WorkflowContext) -> Optional[Result]:
        """
        执行单轮认知循环
        
        职责：
        1. 状态分析
        2. 决策制定
        3. 决策执行
        """
        # 自我分析当前状态并更新到上下文
        self._analyze_current_state(context)
        
        # 自我决策下一步行动
        decision = self._make_decision(context.current_state)
        
        # 执行决策
        return self._execute_decision(decision, context.current_state, context)
    
    # ============== 状态分析和决策 ==============
    
    def _analyze_current_state(self, context: WorkflowContext) -> None:
        """
        分析当前状态并更新到上下文
        
        职责：获取并分析当前状态，更新到上下文中
        """
        current_context = context.get_current_context()
        state_analysis = self.ego.analyze_current_state(current_context)
        self._log(f"自我状态分析：{state_analysis}")
        
        # 更新到上下文中
        context.update_current_state(state_analysis)
    
    def _make_decision(self, state_analysis: str) -> DecisionType:
        """
        做出决策
        
        职责：
        1. 调用自我决策
        2. 转换为枚举类型
        3. 处理未知决策
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
    
    def _execute_decision(self, decision: DecisionType, state_analysis: str, context: WorkflowContext) -> Optional[Result]:
        """
        执行决策
        
        职责：根据决策类型调用相应的处理方法
        """
        if decision == DecisionType.REQUEST_EVALUATION:
            return self._handle_evaluation_request(state_analysis, context)
        elif decision == DecisionType.JUDGMENT_FAILED:
            return self._handle_judgment_failed(state_analysis)
        elif decision == DecisionType.CONTINUE_CYCLE:
            return self._handle_continue_cycle(state_analysis, context)
        else:
            # 默认请求评估
            self._log(f"未知的决策结果：{decision}，默认请求评估")
            return self._handle_evaluation_request(state_analysis, context)
    
    # ============== 决策处理方法 ==============
    
    def _handle_evaluation_request(self, state_analysis: str, context: WorkflowContext) -> Optional[Result]:
        """
        处理自我的评估请求
        
        职责：
        1. 协调评估流程
        2. 判断是否结束工作流
        3. 更新上下文中的评估结果
        """
        # 自我请求本我评估
        evaluation_request = self.ego.request_id_evaluation(state_analysis)
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
                
                return Result(True, "", "", None, 
                            f"工作流成功完成。目标达成确认：{reason}\n最终状态：{final_result.return_value}")
            else:
                # 目标未达成，继续循环
                self._log(f"目标未达成，继续循环。原因：{reason}")
                return None
                
        except (json.JSONDecodeError, KeyError) as e:
            # JSON解析失败，使用备用逻辑
            self._log(f"JSON解析失败，使用备用逻辑：{e}")
            context.update_id_evaluation(evaluation_json)
            context.update_goal_status(False)
            
            if "工作流结束" in evaluation_json:
                self._set_status(WorkflowStatus.SUCCESS)
                return Result(True, "", "", None, f"工作流成功完成：{evaluation_json}")
            else:
                return None
    
    def _handle_judgment_failed(self, state_analysis: str) -> Result:
        """
        处理判断失败
        
        职责：设置失败状态并返回结果
        """
        self._log("自我判断工作流失败，目标无法达成")
        self._set_status(WorkflowStatus.FAILED)
        return Result(False, "", "", None, 
                     f"工作流失败：自我判断目标无法达成。状态分析：{state_analysis}")
    
    def _handle_continue_cycle(self, state_analysis: str, context: WorkflowContext) -> Optional[Result]:
        """
        处理继续循环
        
        职责：
        1. 执行认知步骤
        2. 更新上下文
        """
        cycle_result = self._execute_cognitive_step(state_analysis)
        if cycle_result:
            context.add_cycle_result(context.current_cycle, cycle_result)
        
        return None  # 继续循环
    
    # ============== 错误处理 ==============
    
    def _handle_timeout(self) -> Result:
        """
        处理超时
        
        职责：设置超时状态并返回结果
        """
        self._log(f"达到最大循环次数 {self.max_cycles}，工作流终止")
        self._set_status(WorkflowStatus.TIMEOUT)
        return Result(False, "", "", None, 
                     f"工作流超时：达到最大循环次数 {self.max_cycles}")
    
    def _handle_workflow_exception(self, e: Exception) -> Result:
        """
        处理工作流异常
        
        职责：
        1. 记录异常
        2. 设置异常状态
        3. 返回异常结果
        """
        self._log(f"工作流执行出现异常：{str(e)}")
        self._set_status(WorkflowStatus.EXCEPTION)
        return Result(False, "", "", None, f"工作流执行异常：{str(e)}")
    
    # ============== 工具方法 ==============
    
    def _set_status(self, status: WorkflowStatus):
        """
        设置工作流状态
        
        职责：统一状态管理
        """
        self._status = status
        self.workflow_status = status.value  # 保持向后兼容
    
    def _log(self, message: str):
        """记录日志"""
        if self.verbose:
            print(f"[具身认知工作流-优化版] {message}")
            logging.info(message)
    
    # ============== 其他方法保持不变 ==============
    
    def _execute_cognitive_step(self, state_analysis: str) -> Optional[str]:
        """执行一个认知步骤（观察或执行）"""
        # 这里可以保持原有实现，或者进一步优化
        pass
    
    def get_workflow_status(self) -> dict:
        """获取当前工作流状态"""
        return {
            "状态": self._status.value,
            "当前循环次数": self.current_cycle_count,
            "最大循环次数": self.max_cycles,
            "目标描述": self.id_agent.get_current_goal() if hasattr(self.id_agent, 'get_current_goal') else "未设置",
            "价值标准": self.id_agent.get_value_standard() if hasattr(self.id_agent, 'get_value_standard') else "未设置"
        } 