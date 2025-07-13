"""
具身认知工作流协调器

基于具身认知工作流理论的主协调器实现。
协调自我、本我和身体三层架构的交互和认知循环。
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 使用轻量级核心模块，避免导入49个语言模型
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from python_core import Agent

# 处理相对导入问题
try:
    from .ego_agent import EgoAgent
    from .id_agent import IdAgent
    from .meta_cognitive_agent import MetaCognitiveAgent as MetaCognitionAgent
except ImportError:
    # 当作为独立模块运行时，使用绝对导入
    from ego_agent import EgoAgent
    from id_agent import IdAgent
    from meta_cognitive_agent import MetaCognitiveAgent as MetaCognitionAgent
from agent_base import AgentBase, Result
from langchain_core.language_models import BaseChatModel
from typing import List, Optional, Dict, Any, Iterator
import logging
import json
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
    """
    工作流上下文管理器
    
    负责管理具身认知工作流的执行上下文，包括状态跟踪、历史记录和目标监控。
    是认知循环中各个智能体层级之间共享状态和信息的核心组件。
    
    核心特性：
    - 自然语言状态表示：所有状态信息都以自然语言形式存储和传递
    - 动态状态更新：支持实时更新当前状态分析和评估结果
    - 历史记录管理：维护完整的认知循环执行历史
    - 目标达成跟踪：通过goal_achieved变量精确控制工作流终止
    
    属性说明：
        instruction (str): 用户的原始指令
        history (List[str]): 认知循环的历史执行记录
        current_cycle (int): 当前循环轮数
        current_state (str): **自然语言描述的当前状态分析结果**
                            由自我智能体(Ego)生成，包含对当前情况的理性分析
        id_evaluation (str): **自然语言描述的本我评估结果**
                           由本我智能体(Id)生成，表示对目标达成情况的评估
        goal_achieved (bool): **关键的工作流控制变量**
                            决定认知循环是否继续执行，True时工作流终止
    
    设计理念：
    - 所有认知状态都采用自然语言表示，便于智能体理解和处理
    - 避免硬编码的状态枚举，支持灵活的动态状态描述
    - 通过自然语言实现认知透明性和可解释性
    """
    
    def __init__(self, instruction: str):
        """
        初始化工作流上下文
        
        Args:
            instruction (str): 用户的原始指令
        """
        self.instruction = instruction
        self.history = []
        self.current_cycle = 0
        self.current_state = ""  # 自然语言描述的当前状态分析结果
        self.id_evaluation = ""  # 自然语言描述的本我评估结果  
        self.goal_achieved = False  # 目标是否已达成 - 工作流控制变量
    
    def add_cycle_result(self, cycle_num: int, result: str):
        """
        添加认知循环的执行结果到历史记录
        
        Args:
            cycle_num (int): 循环轮数
            result (str): 自然语言描述的循环执行结果
        """
        self.history.append(f"第{cycle_num}轮结果：{result}")
    
    def update_current_state(self, state_analysis: str):
        """
        更新当前状态分析结果
        
        由自我智能体(Ego)调用，用自然语言描述当前的认知状态和情况分析。
        这是认知循环中的关键信息，用于后续的决策和评估。
        
        Args:
            state_analysis (str): 自然语言描述的当前状态分析结果
                                包含对当前情况的理性分析和判断
        """
        self.current_state = state_analysis
    
    def update_id_evaluation(self, evaluation_result: str):
        """
        更新本我智能体的评估结果
        
        由本我智能体(Id)调用，用自然语言描述对当前任务完成情况的评估。
        这个评估结果用于判断是否达成目标。
        
        Args:
            evaluation_result (str): 自然语言描述的本我评估结果
                                   包含对目标达成情况的价值判断
        """
        self.id_evaluation = evaluation_result
    
    def update_goal_status(self, achieved: bool):
        """
        更新目标达成状态 - 工作流控制的关键方法
        
        这是控制认知循环是否继续的核心变量设置方法。
        当goal_achieved为True时，工作流将终止认知循环。
        
        Args:
            achieved (bool): 目标是否已达成
                           True: 目标达成，工作流应该结束
                           False: 目标未达成，继续认知循环
        """
        self.goal_achieved = achieved
    
    def get_current_context(self) -> str:
        """
        获取当前完整的认知上下文
        
        将所有状态信息整合为一个自然语言描述的完整上下文，
        用于各个智能体层级之间的信息传递和状态同步。
        
        Returns:
            str: 自然语言格式的完整认知上下文，包含：
                - 用户原始指令
                - 当前状态分析 (如果有)
                - 本我评估结果 (如果有) 
                - 目标达成状态
                - 历史执行记录 (如果有)
        """
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
    
    def __str__(self) -> str:
        """返回人类友好的字符串表示"""
        status = "已达成" if self.goal_achieved else "未达成"
        cycle_info = f"第{self.current_cycle}轮" if self.current_cycle > 0 else "初始化"
        history_count = len(self.history)
        
        return (f"WorkflowContext(指令='{self.instruction[:30]}...', "
                f"循环={cycle_info}, 目标={status}, 历史记录={history_count}条)")
    
    def __repr__(self) -> str:
        """返回调试友好的字符串表示"""
        return self.__str__()


# MetaCognitionAgent 已经在 meta_cognitive_agent.py 中实现
# 这里的占位类已不再需要，请直接使用导入的版本


class CognitiveAgent(AgentBase):
    """
    认知智能体 - 具身认知工作流系统
    
    基于具身认知理论的智能体实现，现已升级为四层认知架构：
    元认知层(SuperEgo) - 元认知监督和道德约束
    自我层(Ego) - 理性思考和决策
    本我层(Id) - 欲望驱动和目标导向  
    身体层(Body) - 执行和感知
    
    核心特性：
    - 四层架构：元认知智能体、自我智能体、本我智能体、身体智能体
    - 元认知监督：元认知层提供认知质量控制和策略优化
    - 自适应执行：根据任务复杂性选择直接处理或认知循环
    - 动态决策：实时状态分析和路径调整
    - 目标导向：以用户需求为中心的价值驱动系统
    - UltraThink能力：先进的元认知分析和学习能力
    """
    
    def __init__(self, 
                 llm: BaseChatModel,
                 agents: Optional[List[Agent]] = None,
                 body_config: Optional[dict] = None,
                 ego_config: Optional[dict] = None,
                 id_config: Optional[dict] = None,
                 meta_cognition_config: Optional[dict] = None,
                 enable_meta_cognition: bool = True,
                 max_cycles: int = 50,
                 verbose: bool = True,
                 system_message: Optional[str] = None,
                 evaluation_mode: str = "external"):
        """
        初始化认知智能体
        
        Args:
            llm: 语言模型
            agents: Agent列表，如果为None则自动创建默认body Agent
            body_config: 身体(Agent)的配置参数（仅在agents为None时使用）
            ego_config: 自我智能体的配置参数
            id_config: 本我智能体的配置参数
            meta_cognition_config: 元认知智能体的配置参数
            enable_meta_cognition: 是否启用元认知智能体
            max_cycles: 防止无限循环的最大次数限制
            verbose: 是否输出详细的过程日志
            system_message: 系统消息，如果未提供将使用默认消息
            evaluation_mode: 本我评估模式 ("internal", "external", "auto")
        """
        # 设置默认系统消息
        default_system_message = """你是认知智能体，基于具身认知理论的四层架构智能体系统，负责协调元认知、自我、本我和身体层的交互。

你的核心能力：
1. 四层架构协调：统筹元认知、自我、本我和身体智能体的协作
2. 元认知监督：通过元认知层进行认知质量控制和策略优化  
3. 动态认知循环：根据任务复杂性选择直接处理或多轮认知循环
4. 智能决策：判断任务是否可以一次性完成或需要分步思考
5. UltraThink能力：先进的元认知分析、反思学习和策略优化
6. 自适应执行：增量式规划，动态调整执行策略

工作原则：
- 简单任务直接处理，复杂任务启动认知循环
- 元认知层提供全程监督和质量控制
- 保持认知的连续性和一致性
- 以用户目标为导向，确保任务完成
- 提供详细的执行过程反馈和元认知洞察"""
        
        # 调用父类构造函数
        super().__init__(llm, system_message or default_system_message)
        self.max_cycles = max_cycles
        self.verbose = verbose
        self.evaluation_mode = evaluation_mode
        self.enable_meta_cognition = enable_meta_cognition
        
        # 初始化身体层（多Agent支持）
        if agents:
            # 使用提供的Agent列表
            self.agents = agents[:]  # 复制列表避免外部修改
        else:
            # 向后兼容：创建默认body Agent
            body_config = body_config or {}
            default_body = Agent(llm=llm, **body_config)
            default_body.name = "身体"
            default_body.loadKnowledge('unittest的测试输出在标准错误流而不是标准输出流')
            default_body.loadKnowledge('在Jupyter notebook中模块重载方法：使用importlib.reload()重新加载已修改的模块。具体用法：import importlib; importlib.reload(your_module)。这样可以在不重启notebook的情况下获取模块的最新修改。')
            self.agents = [default_body]
        
        
        # 初始化心灵层
        ego_config = ego_config or {}
        id_config = id_config or {}
        meta_cognition_config = meta_cognition_config or {}
        
        # 初始化日志系统（必须在使用logger之前）
        if self.verbose:
            logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.ego = EgoAgent(llm=llm, **ego_config)
        
        # 合并evaluation_mode到id_config
        id_config_with_mode = id_config.copy() if id_config else {}
        id_config_with_mode['evaluation_mode'] = evaluation_mode
        self.id_agent = IdAgent(llm=llm, **id_config_with_mode)
        
        # 初始化元认知层（元认知监督层）
        self.meta_cognition = None
        if enable_meta_cognition:
            try:
                self.meta_cognition = MetaCognitionAgent(llm=llm, **meta_cognition_config)
                self.meta_cognition.start_cognitive_monitoring()
                self.logger.info("元认知智能体已启用，开始元认知监督")
            except Exception as e:
                self.logger.warning(f"元认知智能体初始化失败，将在无监督模式下运行: {e}")
                self.enable_meta_cognition = False
        
        # 工作流状态
        self._status = WorkflowStatus.NOT_STARTED
        self.current_cycle_count = 0
        self.workflow_status = "未开始"
        self.execution_history = []
    
    def execute_sync(self, instruction: str = None) -> Result:
        """
        同步执行方法 - 执行认知循环，根据任务特性选择处理方式：
        - 直接处理：能一次性完成的简单任务
        - 认知循环：需要思考、规划的复杂任务
        
        Args:
            instruction: 执行指令，如果为None则返回错误
            
        Returns:
            Result: 执行结果
        """
        if instruction is None:
            return Result(success=False, code="", stderr="指令不能为空", return_value="错误：未提供执行指令")
        self.logger.info(f"开始执行认知循环，用户指令：{instruction}")
        print(f"[具身认知工作流] 开始执行认知循环，用户指令：{instruction}")
        
        try:
            # 元认知预监督
            if self.enable_meta_cognition and self.meta_cognition:
                self._meta_cognition_pre_supervision(instruction)
            
            # 判断是否可以直接处理
            can_handle_directly = self._can_handle_directly(instruction)
            
            if can_handle_directly:
                self.logger.info("使用直接处理模式")
                print("[具身认知工作流] 使用直接处理模式")
                result = self._execute_direct_task(instruction)
            else:
                self.logger.info("使用认知循环模式")
                print("[具身认知工作流] 使用认知循环模式")
                result = self._execute_cognitive_cycle_full(instruction)
            
            # 元认知后监督
            if self.enable_meta_cognition and self.meta_cognition:
                self._meta_cognition_post_supervision(instruction, result)
            
            return result
                
        except Exception as e:
            self.logger.error(f"认知循环执行失败: {e}")
            print(f"[具身认知工作流] 认知循环执行失败: {e}")
            return Result(success=False, code="", stderr=str(e), return_value=f"认知循环执行失败: {str(e)}")
    
    def execute_stream(self, instruction: str = None) -> Iterator[object]:
        """
        流式执行方法 - 执行认知循环并返回流式结果
        
        Args:
            instruction: 执行指令，如果为None则返回错误
            
        Returns:
            Iterator[object]: 流式结果，包含过程信息和最终结果
        """        
        if instruction is None:
            yield Result(success=False, code="", stderr="指令不能为空", return_value="错误：未提供执行指令")
            return
            
        # 开始执行流式输出
        yield f"[具身认知工作流] 开始执行认知循环，用户指令：{instruction}"
        
        try:
            # 元认知预监督（流式）
            if self.enable_meta_cognition and self.meta_cognition:
                yield "[具身认知工作流] 开始元认知预监督..."
                for chunk in self._meta_cognition_pre_supervision_stream(instruction):
                    if isinstance(chunk, str):
                        yield f"[元认知预监督] {chunk}"
                    # 最后一个chunk是Result对象，不需要yield
            
            # 判断是否可以直接处理
            yield "[具身认知工作流] 分析任务复杂性..."
            can_handle_directly = self._can_handle_directly(instruction)
            
            if can_handle_directly:
                yield "[具身认知工作流] 使用直接处理模式"
                # 直接处理模式也需要流式输出
                for chunk in self._execute_direct_task_stream(instruction):
                    if isinstance(chunk, Result):
                        result = chunk
                        break
                    else:
                        yield chunk
            else:
                yield "[具身认知工作流] 使用认知循环模式"
                # 使用流式认知循环
                for chunk in self._execute_cognitive_cycle_stream(instruction):
                    if isinstance(chunk, Result):
                        result = chunk
                        break
                    else:
                        yield chunk
            
            # 元认知后监督（流式）
            if self.enable_meta_cognition and self.meta_cognition:
                yield "[具身认知工作流] 开始元认知后监督..."
                for chunk in self._meta_cognition_post_supervision_stream(instruction, result):
                    if isinstance(chunk, str):
                        yield f"[元认知后监督] {chunk}"
                    # 最后一个chunk是Result对象，不需要yield
            
            # 返回最终结果
            yield result
                
        except Exception as e:
            error_msg = f"认知循环执行失败: {str(e)}"
            yield f"[具身认知工作流] {error_msg}"
            yield Result(success=False, code="", stderr=str(e), return_value=error_msg)
    
    # Backward compatibility method
    def execute_cognitive_cycle(self, instruction: str) -> Result:
        """
        向后兼容方法 - 重定向到execute_sync
        
        Args:
            instruction: 执行指令
            
        Returns:
            Result: 执行结果
        """
        return self.execute_sync(instruction)
    
    def chat_sync(self, message: str, response_format: Optional[Dict] = None) -> Result:
        """
        同步聊天方法 - 转发给自我智能体处理
        
        Args:
            message: 聊天消息
            response_format: 可选的响应格式
            
        Returns:
            Result: 聊天结果
        """
        if message is None:
            return Result(success=False, code="", stderr="消息不能为空", return_value="错误：未提供聊天消息")
        
        # 转发给自我智能体处理聊天
        return self.ego.chat_sync(message, response_format)
    
    def chat_stream(self, message: str, response_format: Optional[Dict] = None) -> Iterator[object]:
        """
        流式聊天方法 - 转发给自我智能体处理
        
        Args:
            message: 聊天消息
            response_format: 可选的响应格式
            
        Returns:
            Iterator[object]: 流式聊天结果
        """
        if message is None:
            yield Result(success=False, code="", stderr="消息不能为空", return_value="错误：未提供聊天消息")
            return
        
        # 转发给自我智能体处理流式聊天
        yield from self.ego.chat_stream(message, response_format)
    
    def _can_handle_directly(self, instruction: str) -> bool:
        """
        使用AI评估任务是否可以直接处理
        
        通过AI分析任务的复杂性和特征来判断：
        - 简单任务：可以一次性完成，不需要多轮思考和规划
        - 复杂任务：需要多步骤、规划、或迭代式处理
        
        Args:
            instruction: 用户指令
            
        Returns:
            bool: 是否可以直接处理
        """
        try:
            # 使用AI评估任务复杂性
            evaluation_prompt = f"""请评估以下任务是否可以直接处理：

任务描述：{instruction}

判断标准：
- 可以直接处理：简单的计算、查询、基本问答、单一操作等，可以一次性完成
- 需要认知循环：复杂的创建、开发、分析、多步骤流程、需要规划的任务等

请返回JSON格式：
{{
    "可以直接处理": true/false,
    "理由": "简要说明判断理由",
    "任务类型": "简单任务/复杂任务"
}}

示例：
- "计算 15 + 23" → 可以直接处理（简单计算）
- "创建一个Web应用" → 需要认知循环（复杂开发任务）
- "什么是Python" → 可以直接处理（简单问答）
- "设计一个数据处理流程" → 需要认知循环（需要规划和设计）"""

            # 使用ego agent进行评估
            evaluation_result = self.ego.chat_sync(evaluation_prompt, response_format={"type": "json_object"})
            
            if evaluation_result.success:
                try:
                    import json
                    response_data = json.loads(evaluation_result.return_value.strip())
                    can_handle_directly = response_data.get("可以直接处理", False)
                    reason = response_data.get("理由", "未提供理由")
                    task_type = response_data.get("任务类型", "未知")
                    
                    self._log(f"AI评估结果：{task_type}，可直接处理：{can_handle_directly}，理由：{reason}")
                    return can_handle_directly
                    
                except (json.JSONDecodeError, KeyError) as e:
                    self._log(f"AI评估结果解析失败：{e}，使用保守策略（认知循环）")
                    return False
            else:
                self._log(f"AI评估失败：{evaluation_result.stderr}，使用保守策略（认知循环）")
                return False
                
        except Exception as e:
            self._log(f"AI评估异常：{str(e)}，使用保守策略（认知循环）")
            return False
    
    def _execute_direct_task(self, instruction: str) -> Result:
        """
        直接处理任务的快速路径
        
        Args:
            instruction: 用户指令
            
        Returns:
            Result: 执行结果
        """
        self._log("使用直接处理模式")
        
        try:
            # 直接让身体执行，无需复杂的认知循环
            quick_prompt = f"""直接完成以下任务：

{instruction}

请提供清晰、准确的结果。"""
            
            result = self._execute_body_operation(quick_prompt)
            
            if result.success:
                self._log("直接处理任务成功")
                self._set_status(WorkflowStatus.SUCCESS)
                return Result(True, "", "", None, 
                            f"任务已完成：{result.return_value}")
            else:
                # 直接处理失败，降级到认知循环
                self._log("直接处理失败，降级到认知循环")
                return self._execute_cognitive_cycle_full(instruction)
                
        except Exception as e:
            # 异常时降级到认知循环
            self._log(f"直接处理异常，降级到认知循环：{e}")
            return self._execute_cognitive_cycle_full(instruction)
    
    def _execute_direct_task_stream(self, instruction: str) -> Iterator[object]:
        """
        流式直接处理任务的快速路径
        
        Args:
            instruction: 用户指令
            
        Returns:
            Iterator[object]: 流式结果，包含过程信息和最终结果
        """
        yield "[直接处理] 开始直接处理任务..."
        
        try:
            # 直接让身体执行，无需复杂的认知循环
            quick_prompt = f"""直接完成以下任务：

{instruction}

请提供清晰、准确的结果。"""
            
            yield "[直接处理] 调用身体执行..."
            # 使用身体的流式执行
            for chunk in self._execute_body_operation_stream(quick_prompt):
                if isinstance(chunk, Result):
                    result = chunk
                    break
                else:
                    yield chunk  # 直接输出，不添加前缀
            
            if result.success:
                yield "[直接处理] 任务成功完成"
                self._set_status(WorkflowStatus.SUCCESS)
                yield Result(True, "", "", None, 
                           f"任务已完成：{result.return_value}")
            else:
                # 直接处理失败，降级到认知循环
                yield "[直接处理] 失败，降级到认知循环模式"
                for chunk in self._execute_cognitive_cycle_stream(instruction):
                    yield chunk
                
        except Exception as e:
            # 异常时降级到认知循环
            yield f"[直接处理] 异常，降级到认知循环模式：{e}"
            for chunk in self._execute_cognitive_cycle_stream(instruction):
                yield chunk
    
    def _execute_cognitive_cycle_stream(self, instruction: str) -> Iterator[object]:
        """
        流式执行完整的认知循环
        
        Args:
            instruction: 用户指令
            
        Returns:
            Iterator[object]: 流式结果，包含过程信息和最终结果
        """
        try:
            yield "[认知循环] 初始化工作流..."
            context = self._initialize_workflow(instruction)
            
            yield "[认知循环] 开始主循环..."
            for chunk in self._execute_main_loop_stream(context):
                yield chunk
                
        except Exception as e:
            yield f"[认知循环] 异常：{e}"
            yield self._handle_workflow_exception(e)
    
    def _execute_main_loop_stream(self, context: WorkflowContext) -> Iterator[object]:
        """
        流式执行主循环
        
        Args:
            context: 工作流上下文
            
        Returns:
            Iterator[object]: 流式结果，包含过程信息和最终结果
        """
        while context.current_cycle < self.max_cycles:
            context.current_cycle += 1
            self.current_cycle_count = context.current_cycle
            yield f"[认知循环] 第 {context.current_cycle} 轮开始..."
            
            # 流式执行单轮认知循环
            for chunk in self._execute_single_cycle_stream(context):
                if isinstance(chunk, CycleOutcome):
                    outcome = chunk
                    break
                else:
                    yield chunk
            
            # 根据循环结果决定下一步
            if not outcome.continue_workflow:
                # 工作流结束，返回最终结果
                yield f"[认知循环] 工作流结束，返回最终结果"
                yield outcome.final_result
                return
            
            # 如果有循环数据，记录到历史中
            if outcome.cycle_data:
                context.add_cycle_result(context.current_cycle, outcome.cycle_data)
                yield f"[认知循环] 第 {context.current_cycle} 轮完成：{outcome.cycle_data[:100]}..."
        
        # 超过最大循环次数
        yield f"[认知循环] 达到最大循环次数 {self.max_cycles}"
        yield self._handle_timeout()
    
    def _execute_single_cycle_stream(self, context: WorkflowContext) -> Iterator[object]:
        """
        流式执行单轮认知循环
        
        Args:
            context: 工作流上下文
            
        Returns:
            Iterator[object]: 流式结果，包含过程信息和最终的CycleOutcome
        """
        # 自我分析当前状态并更新到上下文
        yield "[自我分析] 开始分析当前状态..."
        for chunk in self._analyze_current_state_stream(context):
            yield chunk
        
        # 自我决策下一步行动
        yield "[自我决策] 开始决策下一步行动..."
        for chunk in self._make_decision_stream(context.current_state):
            if isinstance(chunk, str):
                yield chunk
            else:
                decision = chunk
                break
        
        # 根据决策类型执行相应操作
        if decision == DecisionType.REQUEST_EVALUATION:
            yield "[认知循环] 请求本我评估..."
            for chunk in self._handle_evaluation_request_stream(context):
                yield chunk
        
        elif decision == DecisionType.JUDGMENT_FAILED:
            yield "[认知循环] 自我判断失败..."
            yield self._handle_judgment_failed(context)
        
        elif decision == DecisionType.CONTINUE_CYCLE:
            yield "[认知循环] 继续循环执行..."
            for chunk in self._handle_continue_cycle_stream(context):
                yield chunk
        
        else:
            # 默认请求评估
            yield f"[认知循环] 未知决策 {decision}，默认请求评估..."
            for chunk in self._handle_evaluation_request_stream(context):
                yield chunk
    
    def _execute_cognitive_cycle_full(self, instruction: str) -> Result:
        """
        执行完整的认知循环
        
        Args:
            instruction: 用户指令
            
        Returns:
            Result: 执行结果
        """
        try:
            context = self._initialize_workflow(instruction)
            return self._execute_main_loop(context)
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
        
        # 本我根据评估模式进行评估
        if self.id_agent.evaluation_mode == "internal":
            self._log("使用内观评估模式")
            evaluation_json = self.id_agent.evaluate_with_context(
                evaluation_request, 
                context.current_state
            )
        else:
            self._log("使用外观评估模式")
            evaluation_json = self.id_agent.evaluate_with_context(
                evaluation_request, 
                context.current_state, 
                agents=self.agents
            )
        
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
                final_result = self._execute_body_chat(final_status_query)
                
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
        执行认知步骤，支持Ego智能Agent选择
        
        Args:
            context: 工作流上下文，包含当前状态、本我评估等完整信息
            
        Returns:
            Optional[str]: 执行结果，失败时返回None
        """
        try:
            # 构建包含Agent信息的决策消息
            decision_message = self._build_decision_message_with_agents(context)
            
            # Ego做决策
            decision_response = self.ego.chat_sync(decision_message, response_format={"type": "json_object"})
            
            try:
                decision_data = json.loads(decision_response.return_value)
                selected_agent_name = decision_data.get("指定Agent", "")
                instruction = decision_data.get("具体指令", "")
                reason = decision_data.get("理由", "")
                
                self._log(f"Ego决策：选择Agent：{selected_agent_name}，理由：{reason}")
                
                # 根据Ego的选择执行
                if selected_agent_name:
                    selected_agent = self._find_agent_by_name(selected_agent_name)
                    if selected_agent:
                        result = selected_agent.execute_sync(instruction)
                        if result.success:
                            self._log(f"执行成功：{result.return_value}")
                            return f"执行结果：{result.return_value}"
                        else:
                            self._log(f"执行失败：{result.stderr}")
                            # 执行失败，让自我处理错误
                            error_handling = self.ego.handle_execution_error(
                                result.stderr or "执行失败", instruction)
                            self._log(f"错误处理：{error_handling}")
                            return f"执行失败，错误处理方案：{error_handling}"
                
                # 回退到默认Agent
                return self._execute_with_default_agent(instruction)
                
            except (json.JSONDecodeError, KeyError) as e:
                self._log(f"JSON解析失败: {e}")
                # JSON解析失败，使用默认Agent执行
                return self._fallback_execution(context)
                    
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
    
    def reset(self):
        """重置工作流状态"""
        self.current_cycle_count = 0
        self._set_status(WorkflowStatus.NOT_STARTED)
        self.execution_history.clear()
        
        # 清理各组件的记忆（如果需要）
        self.ego.reset()
        self.id_agent.reset()
        if self.agents:
            self.agents[0].reset()
    
    def loadKnowledge(self, knowledge: str):
        """
        向所有组件加载知识（方法名与AgentBase一致）
        
        Args:
            knowledge: 要加载的知识内容
        """
        self.ego.loadKnowledge(knowledge)
        self.id_agent.loadKnowledge(knowledge)
        # 向所有Agent加载知识
        for agent in self.agents:
            agent.loadKnowledge(knowledge)
        self._log(f"已向所有组件加载知识：{knowledge[:100]}...")
    
    def loadPythonModules(self, module_list: List[str]):
        """
        向所有Agent加载Python模块（方法名与python_core.py一致）
        
        Args:
            module_list: Python模块名称列表
        """
        for agent in self.agents:
            if hasattr(agent, 'loadPythonModules'):
                agent.loadPythonModules(module_list)
        self._log(f"已向所有Agent加载模块：{module_list}")
    
    def _execute_body_operation(self, instruction: str) -> Result:
        """执行身体层操作，使用默认Agent"""
        default_agent = self.agents[0] if self.agents else None
        if default_agent:
            return default_agent.execute_sync(instruction)
        else:
            return Result(success=False, code="", stderr="没有可用的Agent", return_value="")

    def _execute_body_operation_stream(self, instruction: str) -> Iterator:
        """流式执行身体层操作"""
        default_agent = self.agents[0] if self.agents else None
        if default_agent:
            yield from default_agent.execute_stream(instruction)
        else:
            yield Result(success=False, code="", stderr="没有可用的Agent", return_value="")

    def _execute_body_chat(self, message: str) -> Result:
        """执行身体层聊天操作，使用默认Agent"""
        default_agent = self.agents[0] if self.agents else None
        if default_agent:
            return default_agent.chat_sync(message)
        else:
            return Result(success=False, code="", stderr="没有可用的Agent", return_value="")

    def _find_agent_by_name(self, name: str) -> Optional[Agent]:
        """根据名称查找Agent"""
        for agent in self.agents:
            if agent.name == name:
                return agent
        return None

    def _build_decision_message_with_agents(self, context: WorkflowContext) -> str:
        """构建包含Agent信息的决策消息"""
        agent_info = ""
        for agent in self.agents:
            api_spec = getattr(agent, 'api_specification', None) or "通用执行能力"
            agent_info += f"- {agent.name}: {api_spec}\n"
        
        current_context = context.get_current_context()
        
        return f"""请模拟人类的思维模式，分析当前情况并决定下一步行动。

完整上下文：
{current_context}

可用Agent：
{agent_info}

思考过程要求：
1. 首先在脑海中构思达成目标的完整路径（可能需要多个步骤）
2. 考虑当前状态和已完成的工作
3. 从整体规划中识别出当前最需要执行的下一步
4. 为这一步设计具体、可执行的指令

请像人类一样思考：虽然脑海中有完整的规划，但专注于设计好当前这一步。

返回JSON格式：
{{
    "理由": "基于整体规划，选择此步骤的原因", 
    "指定Agent": "最适合执行这一步的Agent名称",
    "具体指令": "给选定Agent的具体、详细的执行指令"
}}
"""

    def _execute_with_default_agent(self, instruction: str) -> str:
        """使用默认Agent执行"""
        result = self._execute_body_operation(instruction)
        if result.success:
            return f"执行结果：{result.return_value}"
        else:
            return f"执行失败：{result.stderr}"

    def _fallback_execution(self, context: WorkflowContext) -> str:
        """回退执行机制"""
        result = self._execute_body_operation("继续执行当前任务")
        if result.success:
            return f"默认执行结果：{result.return_value}"
        else:
            return f"默认执行失败：{result.stderr}"
    
    def _meta_cognition_pre_supervision(self, instruction: str):
        """元认知执行前监督"""
        try:
            if not self.meta_cognition:
                return
            
            self.logger.info("[元认知监督] 开始执行前认知监督")
            
            # 分析指令复杂性和潜在风险
            cognitive_data = {
                'instruction': instruction,
                'timestamp': time.time(),
                'mode': 'pre_execution'
            }
            
            # 执行综合认知监督
            supervision_result = self.meta_cognition.comprehensive_cognitive_supervision(
                cognitive_data=cognitive_data,
                context={'phase': 'pre_execution', 'instruction': instruction},
                goals=[f"安全执行指令: {instruction}"]
            )
            
            # 处理监督建议
            if supervision_result.get('overall_assessment'):
                assessment = supervision_result['overall_assessment']
                if assessment.get('cognitive_health_level') == 'critical':
                    self.logger.warning("[元认知监督] 检测到认知健康严重问题，建议谨慎执行")
                    print("[元认知监督] ⚠️ 检测到认知健康严重问题")
                elif assessment.get('critical_issues'):
                    self.logger.info(f"[元认知监督] 检测到问题: {assessment['critical_issues']}")
            
            if self.verbose:
                print(f"[元认知监督] ✅ 执行前监督完成")
            
        except Exception as e:
            self.logger.error(f"元认知执行前监督失败: {e}")
    
    def _meta_cognition_post_supervision(self, instruction: str, result: Result):
        """元认知执行后监督"""
        try:
            if not self.meta_cognition:
                return
            
            self.logger.info("[元认知监督] 开始执行后认知监督")
            
            # 分析执行结果
            cognitive_data = {
                'instruction': instruction,
                'result_success': result.success,
                'result_content': result.return_value,
                'timestamp': time.time(),
                'mode': 'post_execution',
                'efficiency': 0.8 if result.success else 0.3,
                'error_rate': 0.0 if result.success else 1.0
            }
            
            # 执行综合认知监督
            supervision_result = self.meta_cognition.comprehensive_cognitive_supervision(
                cognitive_data=cognitive_data,
                context={'phase': 'post_execution', 'instruction': instruction, 'result': result.to_dict()},
                goals=[f"评估执行质量: {instruction}"]
            )
            
            # 进行反思学习
            experience_data = {
                'instruction': instruction,
                'execution_mode': 'cognitive_cycle' if hasattr(self, 'current_cycle_count') else 'direct',
                'success': result.success
            }
            
            outcome = {
                'result': result.to_dict(),
                'supervision': supervision_result
            }
            
            reflection_result = self.meta_cognition.reflect_and_learn(experience_data, outcome)
            
            # 处理监督结果
            if supervision_result.get('overall_assessment'):
                assessment = supervision_result['overall_assessment']
                if assessment.get('priority_recommendations'):
                    self.logger.info(f"[元认知监督] 优化建议: {assessment['priority_recommendations']}")
            
            if self.verbose:
                print(f"[元认知监督] ✅ 执行后监督和反思完成")
                if reflection_result and not reflection_result.get('error'):
                    insights = reflection_result.get('lessons_learned', [])
                    if insights:
                        print(f"[元认知洞察] 💡 学习要点: {insights[0] if insights else '无'}")
            
        except Exception as e:
            self.logger.error(f"元认知执行后监督失败: {e}")
    
    def get_super_ego_state(self) -> Dict[str, Any]:
        """获取元认知状态信息（向后兼容）"""
        return self.get_meta_cognition_state()
    
    def get_meta_cognition_state(self) -> Dict[str, Any]:
        """获取元认知状态信息"""
        if not self.enable_meta_cognition or not self.meta_cognition:
            return {'enabled': False, 'message': '元认知智能体未启用'}
        
        try:
            state = self.meta_cognition.get_meta_cognitive_state()
            health_assessment = self.meta_cognition.assess_cognitive_health()
            learning_summary = self.meta_cognition.get_learning_summary()
            
            return {
                'enabled': True,
                'meta_cognitive_state': state,
                'cognitive_health': health_assessment.__dict__,
                'learning_summary': learning_summary,
                'supervision_metrics': self.meta_cognition.supervision_metrics
            }
        except Exception as e:
            return {'enabled': True, 'error': str(e)}
    
    def enable_super_ego_monitoring(self):
        """启用元认知监控（向后兼容）"""
        self.enable_meta_cognition_monitoring()
    
    def enable_meta_cognition_monitoring(self):
        """启用元认知监控"""
        if self.meta_cognition:
            self.enable_meta_cognition = True
            self.meta_cognition.start_cognitive_monitoring()
            self.logger.info("元认知监控已启用")
        else:
            self.logger.warning("元认知智能体未初始化，无法启用监控")
    
    def disable_super_ego_monitoring(self):
        """禁用元认知监控（向后兼容）"""
        self.disable_meta_cognition_monitoring()
    
    def disable_meta_cognition_monitoring(self):
        """禁用元认知监控"""
        if self.meta_cognition:
            self.enable_meta_cognition = False
            self.meta_cognition.stop_cognitive_monitoring()
            self.logger.info("元认知监控已禁用")

    # ========== 流式执行的辅助方法 ==========
    
    def _meta_cognition_pre_supervision_stream(self, instruction: str) -> Iterator[object]:
        """元认知执行前监督（流式）"""
        try:
            if not self.meta_cognition:
                yield "元认知未启用，跳过预监督"
                yield Result(True, "", "", None, "跳过预监督")
                return
            
            yield "开始执行前认知监督"
            
            # 分析指令复杂性和潜在风险
            cognitive_data = {
                'instruction': instruction,
                'timestamp': time.time(),
                'mode': 'pre_execution'
            }
            
            # 使用元认知的流式监督
            supervision_prompt = f"""对以下指令进行预监督分析：
指令：{instruction}
请分析潜在风险和复杂性。"""
            
            for chunk in self.meta_cognition.chat_stream(supervision_prompt):
                if isinstance(chunk, Result):
                    yield "执行前监督完成"
                    yield chunk
                    break
                else:
                    yield chunk
                    
        except Exception as e:
            yield f"元认知执行前监督失败: {e}"
            yield Result(False, "", "", str(e), "监督失败")
    
    def _meta_cognition_post_supervision_stream(self, instruction: str, result: Result) -> Iterator[object]:
        """元认知执行后监督（流式）"""
        try:
            if not self.meta_cognition:
                yield "元认知未启用，跳过后监督"
                yield Result(True, "", "", None, "跳过后监督")
                return
            
            yield "开始执行后认知监督"
            
            # 使用元认知的流式监督
            supervision_prompt = f"""对以下执行结果进行后监督分析：
指令：{instruction}
执行成功：{result.success}
结果：{result.return_value}
请分析执行质量和改进建议。"""
            
            for chunk in self.meta_cognition.chat_stream(supervision_prompt):
                if isinstance(chunk, Result):
                    yield "执行后监督完成"
                    yield chunk
                    break
                else:
                    yield chunk
                    
        except Exception as e:
            yield f"元认知执行后监督失败: {e}"
            yield Result(False, "", "", str(e), "监督失败")
    
    def _analyze_current_state_stream(self, context: WorkflowContext) -> Iterator[object]:
        """流式分析当前状态并更新到上下文"""
        try:
            current_context = context.get_current_context()
            
            # 使用自我的流式分析
            for chunk in self.ego.chat_stream(f"分析当前状态：{current_context}"):
                if isinstance(chunk, Result):
                    state_analysis = chunk.return_value
                    context.update_current_state(state_analysis)
                    yield f"状态分析完成：{state_analysis[:100]}..."
                    break
                else:
                    yield chunk
                    
        except Exception as e:
            yield f"状态分析失败: {e}"
            context.update_current_state(f"状态分析失败: {e}")
    
    def _make_decision_stream(self, state_analysis: str) -> Iterator[object]:
        """流式做出决策"""
        try:
            # 使用自我的流式决策
            for chunk in self.ego.chat_stream(f"基于状态分析做出决策：{state_analysis}"):
                if isinstance(chunk, Result):
                    next_action = chunk.return_value
                    yield f"决策完成：{next_action}"
                    
                    # 将字符串决策转换为枚举
                    decision_mapping = {
                        "请求评估": DecisionType.REQUEST_EVALUATION,
                        "判断失败": DecisionType.JUDGMENT_FAILED,
                        "继续循环": DecisionType.CONTINUE_CYCLE
                    }
                    
                    decision = decision_mapping.get(next_action, DecisionType.REQUEST_EVALUATION)
                    yield decision
                    break
                else:
                    yield chunk
                    
        except Exception as e:
            yield f"决策失败: {e}"
            yield DecisionType.REQUEST_EVALUATION  # 默认决策
    
    def _handle_evaluation_request_stream(self, context: WorkflowContext) -> Iterator[object]:
        """流式处理自我的评估请求"""
        try:
            # 自我请求本我评估
            evaluation_request = self.ego.request_id_evaluation(context.current_state)
            yield f"评估请求：{evaluation_request[:100]}..."
            
            # 本我根据评估模式进行评估
            if self.id_agent.evaluation_mode == "internal":
                yield "使用内观评估模式"
                
                # 使用本我的流式内观评估
                for chunk in self.id_agent.chat_stream(
                    f"内观评估：{evaluation_request}\n当前状态：{context.current_state}", 
                    response_format={"type": "json_object"}
                ):
                    if isinstance(chunk, Result):
                        evaluation_json = chunk.return_value
                        break
                    else:
                        yield chunk
            else:
                yield "使用外观评估模式"
                
                # 生成评估指令
                evaluation_instruction = self.id_agent.generate_evaluation_instruction(evaluation_request)
                yield f"评估指令：{evaluation_instruction[:100]}..."
                
                # 身体执行观察
                for chunk in self._execute_body_operation_stream(evaluation_instruction):
                    if isinstance(chunk, Result):
                        observation_result = chunk
                        break
                    else:
                        yield chunk  # 直接输出，不添加前缀
                
                # 本我评估结果
                for chunk in self.id_agent.chat_stream(
                    f"评估目标达成：{observation_result.return_value}",
                    response_format={"type": "json_object"}
                ):
                    if isinstance(chunk, Result):
                        evaluation_json = chunk.return_value
                        break
                    else:
                        yield chunk
            
            yield f"评估结果：{evaluation_json[:100]}..."
            
            # 解析JSON评估结果
            try:
                import json
                evaluation_data = json.loads(evaluation_json)
                goal_achieved = evaluation_data.get("目标是否达成", False)
                reason = evaluation_data.get("原因", "未提供原因")
                
                if goal_achieved:
                    yield "目标已达成，工作流结束"
                    final_result = Result(True, "", "", None, 
                                        f"工作流成功完成！{reason}")
                    yield CycleOutcome(
                        continue_workflow=False,
                        final_result=final_result,
                        decision_type=DecisionType.REQUEST_EVALUATION
                    )
                else:
                    yield f"目标未达成，继续循环：{reason}"
                    yield CycleOutcome(
                        continue_workflow=True,
                        cycle_data=f"评估结果：{reason}",
                        decision_type=DecisionType.REQUEST_EVALUATION
                    )
                    
            except json.JSONDecodeError as e:
                yield f"评估结果解析失败：{e}"
                # 默认继续循环
                yield CycleOutcome(
                    continue_workflow=True,
                    cycle_data=f"评估结果解析失败：{e}",
                    decision_type=DecisionType.REQUEST_EVALUATION
                )
                
        except Exception as e:
            yield f"评估处理失败: {e}"
            yield CycleOutcome(
                continue_workflow=False,
                final_result=Result(False, "", "", None, f"评估处理失败：{e}"),
                decision_type=DecisionType.REQUEST_EVALUATION
            )
    
    def _handle_continue_cycle_stream(self, context: WorkflowContext) -> Iterator[object]:
        """流式处理继续循环"""
        try:
            yield "开始执行认知步骤"
            
            # 流式执行认知步骤
            for chunk in self._execute_cognitive_step_stream(context):
                if isinstance(chunk, str):
                    cycle_data = chunk
                    break
                else:
                    yield chunk
            
            yield f"认知步骤完成：{cycle_data[:100]}..."
            
            yield CycleOutcome(
                continue_workflow=True,
                cycle_data=cycle_data,
                decision_type=DecisionType.CONTINUE_CYCLE
            )
            
        except Exception as e:
            yield f"继续循环处理失败: {e}"
            yield CycleOutcome(
                continue_workflow=False,
                final_result=Result(False, "", "", None, f"继续循环处理失败：{e}"),
                decision_type=DecisionType.CONTINUE_CYCLE
            )
    
    def _execute_cognitive_step_stream(self, context: WorkflowContext) -> Iterator[object]:
        """流式执行认知步骤"""
        try:
            # 获取当前上下文
            current_context = context.get_current_context()
            
            # 自我分析并生成指令
            thinking_result = self.ego.analyze_current_state(current_context)
            yield f"思考结果：{thinking_result[:100]}..."
            
            # 决定是观察还是执行
            if "观察" in thinking_result or "查看" in thinking_result or "分析" in thinking_result:
                # 生成观察指令
                observation_instruction = self.ego.generate_observation_instruction(thinking_result)
                yield f"观察指令：{observation_instruction[:100]}..."
                
                # 身体执行观察
                default_agent = self.agents[0] if self.agents else None
                if default_agent:
                    for chunk in default_agent.chat_stream(observation_instruction):
                        if isinstance(chunk, Result):
                            observation_result = chunk
                            break
                        else:
                            yield chunk  # 直接输出，不添加前缀
                
                if observation_result.success:
                    yield f"观察成功：{observation_result.return_value[:100]}..."
                    yield f"观察结果：{observation_result.return_value}"
                else:
                    yield f"观察失败：{observation_result.stderr}"
                    yield f"观察失败，错误：{observation_result.stderr}"
                    
            else:
                # 生成执行指令
                execution_instruction = self.ego.generate_execution_instruction(thinking_result)
                yield f"执行指令：{execution_instruction[:100]}..."
                
                # 身体执行操作
                for chunk in self._execute_body_operation_stream(execution_instruction):
                    if isinstance(chunk, Result):
                        execution_result = chunk
                        break
                    else:
                        yield chunk  # 直接输出，不添加前缀
                
                if execution_result.success:
                    yield f"执行成功：{execution_result.return_value[:100]}..."
                    yield f"执行结果：{execution_result.return_value}"
                else:
                    # 执行失败，让自我处理错误
                    error_handling = self.ego.handle_execution_error(
                        execution_result.stderr or "执行失败", execution_instruction)
                    yield f"执行失败，错误处理：{error_handling[:100]}..."
                    yield f"执行失败，错误处理方案：{error_handling}"
                    
        except Exception as e:
            yield f"认知步骤执行异常：{str(e)}"
            yield f"认知步骤执行异常：{str(e)}"


# 便利函数：快速创建和使用认知智能体
def create_cognitive_agent(llm: BaseChatModel, **kwargs) -> CognitiveAgent:
    """
    便利函数：创建认知智能体实例
    
    Args:
        llm: 语言模型
        **kwargs: 其他配置参数
        
    Returns:
        CognitiveAgent: 认知智能体实例
    """
    return CognitiveAgent(llm=llm, **kwargs)


def execute_cognitive_task(llm: BaseChatModel, task_description: str, **kwargs) -> Result:
    """
    便利函数：一次性执行认知任务
    
    Args:
        llm: 语言模型
        task_description: 任务描述
        **kwargs: 其他配置参数
        
    Returns:
        Result: 执行结果
    """
    agent = create_cognitive_agent(llm, **kwargs)
    return agent.execute_sync(task_description)



