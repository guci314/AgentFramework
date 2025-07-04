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
from typing import List, Optional
import logging


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
        
        # 初始化心灵层
        ego_config = ego_config or {}
        id_config = id_config or {}
        
        self.ego = EgoAgent(llm=llm, **ego_config)
        self.id_agent = IdAgent(llm=llm, **id_config)
        
        # 工作流状态
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
            
            # 第一步：生成本我，设定价值标准和目标
            self._log("第一步：初始化本我价值系统")
            value_system_result = self.id_agent.initialize_value_system(instruction)
            self._log(f"价值系统初始化完成：{value_system_result}")
            
            # 开始认知循环
            self.workflow_status = "运行中"
            self.current_cycle_count = 0
            
            current_context = f"用户指令：{instruction}\n价值系统：{value_system_result}"
            
            while self.current_cycle_count < self.max_cycles:
                self.current_cycle_count += 1
                self._log(f"\n=== 认知循环第 {self.current_cycle_count} 轮 ===")
                
                # 自我分析当前状态
                state_analysis = self.ego.analyze_current_state(current_context)
                self._log(f"自我状态分析：{state_analysis}")
                
                # 自我决策下一步行动
                next_action = self.ego.decide_next_action(state_analysis)
                self._log(f"自我决策：{next_action}")
                
                if next_action == "请求评估":
                    # 请求本我评估
                    cycle_result = self._handle_evaluation_request(state_analysis)
                    if cycle_result:
                        return cycle_result
                
                elif next_action == "判断失败":
                    # 工作流失败
                    self._log("自我判断工作流失败，目标无法达成")
                    self.workflow_status = "失败"
                    return Result(False, "", "", None, 
                                f"工作流失败：自我判断目标无法达成。状态分析：{state_analysis}")
                
                elif next_action == "继续循环":
                    # 继续执行循环
                    cycle_result = self._execute_cognitive_step(state_analysis)
                    if cycle_result:
                        current_context = self._update_context(current_context, cycle_result)
                    else:
                        # 执行失败，需要错误处理
                        continue
                
                else:
                    self._log(f"未知的决策结果：{next_action}，默认请求评估")
                    cycle_result = self._handle_evaluation_request(state_analysis)
                    if cycle_result:
                        return cycle_result
            
            # 超过最大循环次数
            self._log(f"达到最大循环次数 {self.max_cycles}，工作流终止")
            self.workflow_status = "超时"
            return Result(False, "", "", None, 
                        f"工作流超时：达到最大循环次数 {self.max_cycles}")
            
        except Exception as e:
            self._log(f"工作流执行出现异常：{str(e)}")
            self.workflow_status = "异常"
            return Result(False, "", "", None, f"工作流执行异常：{str(e)}")
    
    def _handle_evaluation_request(self, state_analysis: str) -> Optional[Result]:
        """
        处理自我的评估请求
        
        Args:
            state_analysis: 当前状态分析
            
        Returns:
            Optional[Result]: 如果工作流结束则返回最终结果，否则返回None
        """
        # 自我请求本我评估
        evaluation_request = self.ego.request_id_evaluation(state_analysis)
        self._log(f"自我评估请求：{evaluation_request}")
        
        # 本我生成评估指令
        evaluation_instruction = self.id_agent.generate_evaluation_instruction(evaluation_request)
        self._log(f"本我评估指令：{evaluation_instruction}")
        
        # 身体执行评估指令（观察）
        observation_result = self.body.chat_sync(evaluation_instruction)
        self._log(f"身体观察结果：{observation_result.return_value}")
        
        # 本我评估目标达成情况
        evaluation_conclusion = self.id_agent.evaluate_goal_achievement(observation_result.return_value)
        self._log(f"本我评估结论：{evaluation_conclusion}")
        
        if evaluation_conclusion.strip() == "工作流结束":
            # 目标达成，工作流成功结束
            self._log("本我确认目标达成，工作流成功结束")
            self.workflow_status = "成功"
            
            # 获取最终状态作为结果
            final_status_query = "请查看当前的工作成果和状态，提供一个完整的总结"
            final_result = self.body.chat_sync(final_status_query)
            
            return Result(True, "", "", None, 
                        f"工作流成功完成。目标达成确认：{evaluation_conclusion}\n最终状态：{final_result.return_value}")
        else:
            # 目标未达成，继续循环
            self._log(f"目标未达成，继续循环。原因：{evaluation_conclusion}")
            return None
    
    def _execute_cognitive_step(self, state_analysis: str) -> Optional[str]:
        """
        执行一个认知步骤（观察或执行）
        
        Args:
            state_analysis: 当前状态分析
            
        Returns:
            Optional[str]: 执行结果，失败时返回None
        """
        try:
            # 自我决定是生成观察指令还是执行指令
            # 这里可以让自我根据状态分析来决定
            decision_message = f"""基于当前状态分析，决定下一步需要观察还是执行：

状态分析：
{state_analysis}

请选择：
1. "观察" - 如果需要了解更多信息
2. "执行" - 如果需要执行具体操作

只返回"观察"或"执行"，不要其他内容。"""
            
            decision_result = self.ego.chat_sync(decision_message)
            action_type = decision_result.return_value.strip().strip('"').strip("'")
            
            if "观察" in action_type:
                # 生成观察指令
                observation_instruction = self.ego.generate_observation_instruction(state_analysis)
                self._log(f"生成观察指令：{observation_instruction}")
                
                # 身体执行观察（使用chat_sync）
                observation_result = self.body.chat_sync(observation_instruction)
                if observation_result.success:
                    self._log(f"观察成功：{observation_result.return_value}")
                    return f"观察结果：{observation_result.return_value}"
                else:
                    self._log(f"观察失败：{observation_result.stderr}")
                    return None
            
            else:  # 默认执行
                # 生成执行指令
                execution_instruction = self.ego.generate_execution_instruction(state_analysis)
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
    
    def _update_context(self, current_context: str, new_result: str) -> str:
        """
        更新上下文信息
        
        Args:
            current_context: 当前的上下文
            new_result: 新的执行结果
            
        Returns:
            str: 更新后的上下文
        """
        return f"{current_context}\n\n第{self.current_cycle_count}轮结果：{new_result}"
    
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
        self.workflow_status = "未开始"
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