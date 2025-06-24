# -*- coding: utf-8 -*-
"""
认知工作流系统 - 真正的动态导航实现

基于认知工作流核心理念：
1. 计划是线性的，导航是动态的
2. 三大核心角色的清晰分离：规划者、决策者、执行者
3. 基于状态满足性检查而非固定依赖关系
4. 具备动态计划修正和自我修复能力

作者：Claude
日期：2024-12-21
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from datetime import datetime as dt
import re
import asyncio
import copy
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from agent_base import Result
from pythonTask import Agent, StatefulExecutor

def safe_get_result_return_value(result):
    """安全获取Result对象的返回值内容，优先获取return_value字段"""
    if hasattr(result, 'return_value') and result.return_value is not None:
        return str(result.return_value)
    elif hasattr(result, 'output'):
        return result.output or ""
    elif hasattr(result, 'stdout'):
        return result.stdout or ""
    else:
        return ""

def safe_get_result_error(result):
    """安全获取Result对象的错误内容"""
    if hasattr(result, 'error'):
        return result.error or ""
    elif hasattr(result, 'stderr'):
        return result.stderr or ""
    else:
        return ""

# 配置日志
logger = logging.getLogger(__name__)

class TaskPhase(Enum):
    """任务阶段枚举"""
    INFORMATION = "information"    # 信息收集阶段
    EXECUTION = "execution"        # 执行阶段  
    VERIFICATION = "verification"  # 验证阶段

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"           # 待执行
    EXECUTABLE = "executable"     # 可执行（先决条件已满足）
    RUNNING = "running"           # 执行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"            # 失败
    SKIPPED = "skipped"          # 跳过
    CANCELLED = "cancelled"       # 取消

@dataclass
class CognitiveTask:
    """认知任务数据结构 - 基于先决条件而非依赖关系"""
    id: str
    name: str
    instruction: str
    agent_name: str
    instruction_type: str  # execution/information
    phase: TaskPhase
    expected_output: str
    precondition: str      # 自然语言描述的先决条件，替代传统的dependencies
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Result] = None
    created_at: dt = field(default_factory=dt.now)
    updated_at: dt = field(default_factory=dt.now)
    execution_context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'instruction': self.instruction,
            'agent_name': self.agent_name,
            'instruction_type': self.instruction_type,
            'phase': self.phase.value,
            'expected_output': self.expected_output,
            'precondition': self.precondition,
            'status': self.status.value,
            'result': self.result.to_dict() if self.result else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'execution_context': self.execution_context
        }

@dataclass
class GlobalState:
    """全局状态 - 自然语言描述的工作流状态"""
    current_state: str
    state_history: List[Tuple[str, str, dt]] = field(default_factory=list)  # (state, source, timestamp)
    context_variables: Dict[str, Any] = field(default_factory=dict)
    original_goal: str = ""  # 用户的原始目标指令
    _llm: Optional[BaseChatModel] = field(default=None, init=False)  # 用于智能状态生成
    
    def set_llm(self, llm: BaseChatModel):
        """设置语言模型用于智能状态生成"""
        self._llm = llm
    
    def set_original_goal(self, goal: str):
        """设置用户的原始目标指令"""
        self.original_goal = goal
    
    def _update_state_internal(self, new_state: str, source: str = "system"):
        """内部状态更新方法 - 仅供update_state内部调用"""
        timestamp = dt.now()
        old_state = self.current_state
        self.state_history.append((self.current_state, source, timestamp))
        self.current_state = new_state
        
        # 简化的状态更新日志，避免过度复杂的处理
        logger.info(f"状态更新 [{source}]: {new_state}")
        
        # 基本状态信息（简化版）
        logger.info(f"原始目标: {self.original_goal}")
        if self.context_variables:
            logger.info(f"上下文变量数量: {len(self.context_variables)}")
        logger.info("---")
    
    def update_state(self, new_state: str = None, source: str = "system", 
                   task: Optional['CognitiveTask'] = None, 
                   result: Optional[Result] = None,
                   intelligent: bool = True) -> str:
        """
        更新全局状态 - 统一的状态更新接口
        
        Args:
            new_state: 新状态描述（当intelligent=False时必须提供，intelligent=True时作为fallback）
            source: 状态来源
            task: 执行的任务（智能模式使用）
            result: 执行结果（智能模式使用）
            intelligent: 是否使用智能状态生成，默认True
            
        Returns:
            生成的新状态描述
        """
        # 简单模式：直接使用提供的状态
        if not intelligent:
            if not new_state:
                raise ValueError("简单模式下必须提供new_state参数")
            self._update_state_internal(new_state, source)
            return new_state
        
        # 智能模式：使用LLM生成状态
        fallback_state = new_state or "状态更新"
        
        if not self._llm:
            # 如果没有LLM，使用传统方式
            self._update_state_internal(fallback_state, source)
            return fallback_state
            
        try:
            # 构建状态生成提示
            system_message = """你是一个工作流状态描述专家，负责根据任务执行情况生成详细、有意义的状态描述。

状态描述要求：
1. 详细描述当前工作流进展，控制在500字以内
2. 必须包含用户的原始目标指令，体现目标导向性
3. 准确反映当前工作流进展和已完成的关键步骤
4. 突出关键信息、成果和里程碑
5. 使用自然语言，避免过多技术术语
6. 体现工作流的整体推进情况和距离目标的进度
7. 如果有错误或问题，要明确指出并说明影响

请只返回状态描述文本，不要包含其他内容。"""

            # 构建用户消息
            context_parts = []
            
            # 添加用户原始目标
            if self.original_goal:
                context_parts.append(f"用户原始目标: {self.original_goal}")
                context_parts.append("")
            
            context_parts.append(f"当前状态: {self.current_state}")
            
            if self.state_history:
                context_parts.append("\n最近状态历史:")
                for state, src, ts in self.state_history[-3:]:  # 显示最近3条历史
                    context_parts.append(f"  - [{ts.strftime('%H:%M:%S')}] {state}")
            
            if task:
                context_parts.append(f"\n刚完成任务:")
                context_parts.append(f"  任务名称: {task.name}")
                context_parts.append(f"  任务指令: {task.instruction}")
                context_parts.append(f"  任务阶段: {task.phase.value}")
                context_parts.append(f"  执行代理: {task.agent_name}")
                context_parts.append(f"  预期输出: {task.expected_output}")
                
            if result:
                context_parts.append(f"\n执行结果: {'✅ 成功' if result.success else '❌ 失败'}")
                if result.success:
                    output = safe_get_result_return_value(result)
                    if output:
                        # 截取输出的前500个字符，给状态描述更多空间
                        output_preview = output[:500] + "..." if len(output) > 500 else output
                        context_parts.append(f"输出内容: {output_preview}")
                else:
                    error = safe_get_result_error(result)
                    if error:
                        error_preview = error[:500] + "..." if len(error) > 500 else error
                        context_parts.append(f"错误信息: {error_preview}")
            
            if self.context_variables:
                context_parts.append(f"\n上下文变量: {len(self.context_variables)} 个")
                # 显示一些关键的上下文变量
                if len(self.context_variables) <= 3:
                    for key, value in list(self.context_variables.items())[:3]:
                        value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                        context_parts.append(f"  - {key}: {value_preview}")
                
            user_message = "\n".join(context_parts)
            user_message += "\n\n请生成新的工作流状态描述，必须包含用户原始目标，详细描述当前进展："
            
            # 调用LLM生成状态
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message)
            ]
            
            response = self._llm.invoke(messages)
            generated_state = response.content.strip()
            
            # 确保状态描述不为空且合理，放宽长度限制
            if generated_state and len(generated_state) > 10:
                self._update_state_internal(generated_state, source)
                return generated_state
            else:
                # 如果生成的状态不合理，使用备用状态
                enhanced_fallback = f"目标: {self.original_goal} | {fallback_state}" if self.original_goal else fallback_state
                self._update_state_internal(enhanced_fallback, source)
                return enhanced_fallback
                
        except Exception as e:
            logger.warning(f"智能状态生成失败: {e}，使用备用状态")
            enhanced_fallback = f"目标: {self.original_goal} | {fallback_state}" if self.original_goal else fallback_state
            self._update_state_internal(enhanced_fallback, source)
            return enhanced_fallback
    
    def get_recent_history(self, limit: int = 5) -> List[str]:
        """获取最近的状态历史"""
        recent_states = []
        for state, source, timestamp in self.state_history[-limit:]:
            recent_states.append(f"[{timestamp.strftime('%H:%M:%S')}] {state}")
        return recent_states
    
    def get_state_summary(self) -> str:
        """获取状态摘要"""
        summary = f"当前状态: {self.current_state}\n"
        if self.state_history:
            summary += "最近历史:\n"
            for history_item in self.get_recent_history(3):
                summary += f"  - {history_item}\n"
        return summary

class StateConditionChecker:
    """状态满足性检查器 - 核心的认知决策机制"""
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.similarity_threshold = 0.7
        
    def check_precondition_satisfied(self, precondition: str, global_state: GlobalState) -> Tuple[bool, float, str]:
        """
        检查先决条件是否被全局状态满足
        
        Args:
            precondition: 自然语言描述的先决条件
            global_state: 当前全局状态
            
        Returns:
            (是否满足, 置信度, 解释)
        """
        if precondition == "无" or precondition.lower() in ["none", "null", ""]:
            return True, 1.0, "无先决条件"
            
        system_message = """你是一个状态满足性检查专家，负责判断当前工作流状态是否满足任务的先决条件。

请仔细分析当前状态和先决条件，判断：
1. 先决条件是否被当前状态满足
2. 给出0-1之间的置信度分数
3. 提供简明的解释

返回格式：
{
  "satisfied": true/false,
  "confidence": 0.85,
  "explanation": "解释为什么满足或不满足"
}"""
        
        user_message = f"""## 先决条件
{precondition}

## 当前全局状态
{global_state.get_state_summary()}

## 上下文变量
{json.dumps(global_state.context_variables, ensure_ascii=False, indent=2)}

请判断当前状态是否满足先决条件。"""
        
        try:
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm.invoke(messages)
            result_text = response.content.strip()
            
            # 解析结果
            try:
                result_json = json.loads(result_text)
                satisfied = result_json.get('satisfied', False)
                confidence = float(result_json.get('confidence', 0.0))
                explanation = result_json.get('explanation', '无解释')
                
                return satisfied, confidence, explanation
                
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试简单的文本解析
                if "满足" in result_text or "true" in result_text.lower():
                    return True, 0.6, result_text
                else:
                    return False, 0.6, result_text
                    
        except Exception as e:
            logger.error(f"先决条件检查失败: {e}")
            return False, 0.0, f"检查失败: {str(e)}"

class CognitiveManager:
    """认知管理者 - 统一的工作流认知管理
    
    整合了原 CognitivePlanner 和 CognitiveDecider 的功能：
    1. 任务规划管理：初始任务生成、修复任务、动态任务
    2. 任务决策管理：可执行任务查找、下一任务选择
    3. 工作流状态管理：状态评估、修正需求分析
    """
    
    def __init__(self, llm: BaseChatModel, available_agents: Dict[str, 'Agent'], 
                 condition_checker: StateConditionChecker, interactive_mode: bool = False):
        """
        初始化认知管理者
        
        Args:
            llm: 语言模型
            available_agents: 可用智能体字典
            condition_checker: 状态条件检查器
            interactive_mode: 是否启用交互模式
        """
        self.llm = llm
        self.available_agents = available_agents
        self.condition_checker = condition_checker
        self.interactive_mode = interactive_mode
        self.decision_history: List[Dict[str, Any]] = []
        self.management_statistics = {
            'tasks_generated': 0,
            'decisions_made': 0,
            'recovery_attempts': 0,
            'dynamic_tasks_added': 0
        }
        
    # ====== 任务规划管理 ======
    
    def generate_initial_tasks(self, goal: str, context: Dict[str, Any] = None) -> List[CognitiveTask]:
        """
        生成初始任务列表 - 整合原CognitivePlanner.generate_task_list()
        
        Args:
            goal: 高层次目标描述
            context: 额外上下文信息
            
        Returns:
            任务列表
        """
        logger.info(f"🎯 认知管理者开始生成初始任务列表")
        logger.info(f"   📋 目标: {goal}")
        
        # 根据交互模式调整系统提示词
        interaction_guidance = ""
        if not self.interactive_mode:
            interaction_guidance = """
**重要约束：非交互模式**
- 不要生成任何询问用户、咨询用户、收集用户需求的任务
- 所有任务都应该基于已有信息或合理假设来执行
- 如果需要信息，应该通过分析、推理或使用默认值来获取
- 专注于自动化执行，避免人工干预
"""
        else:
            interaction_guidance = """
**交互模式启用**
- 可以生成询问用户、收集需求的信息型任务
- 通过用户交互来明确需求和获取反馈
"""

        system_message = f"""你是一个认知工作流规划专家，专注于将高层次目标分解为精准、必要的任务列表。

核心原则：
1. **严格按照用户目标规划**：只生成实现用户明确目标所必需的任务
2. **避免过度工程化**：不要添加用户未要求的"最佳实践"或"额外功能"
3. **保持简洁高效**：优先考虑最直接的实现路径
4. **三阶段规划模式**：按照"收集→执行→验证"的标准流程组织任务

## 三阶段规划模式详解

**阶段1：信息收集（information）**
- 目标：收集实现目标所需的所有必要信息
- 任务类型：需求分析、环境检查、资源准备、技术调研等
- 输出：为后续执行提供明确的指导和依据
- 先决条件：通常基于用户提供的初始信息

**阶段2：核心执行（execution）**  
- 目标：基于收集的信息，执行核心业务逻辑
- 任务类型：代码编写、文件操作、数据处理、系统配置等
- 输出：实现用户目标的具体成果
- 先决条件：信息收集阶段完成，必要信息已获取

**阶段3：结果验证（verification）**
- 目标：确保执行结果符合用户期望和质量标准
- 任务类型：功能测试、结果检查、输出验证、质量评估等
- 输出：验证报告和最终确认
- 先决条件：核心执行阶段完成，有具体成果可验证

{interaction_guidance}

指令类型详解：
- **information（信息型）**：调用智能体的 chat_sync() 方法，纯对话交互
- **execution（执行型）**：调用智能体的 execute_sync() 方法，生成并执行Python代码

任务结构要求：
- id: 唯一标识符（建议格式：阶段前缀_序号，如collect_1, exec_1, verify_1）
- name: 简短名称  
- instruction: 详细指令（根据instruction_type和阶段特点编写）
- agent_name: 执行者（从可用智能体中选择最适合的）
- instruction_type: execution/information（根据任务性质选择）
- phase: information/execution/verification（严格按照三阶段分配）
- expected_output: 预期输出（要明确、可验证）
- precondition: 自然语言描述的先决条件（体现阶段间的逻辑关系）

重要：不要使用传统的依赖关系（dependencies），而是用自然语言描述什么状态下该任务才能执行。"""

        try:
            # 构建智能体信息
            available_agents_str = self._build_agent_info_string()
            
            user_message = f"""## 高层次目标
{goal}

## 可用智能体
{available_agents_str}

## 额外上下文
{json.dumps(context or {}, ensure_ascii=False, indent=2)}

请按照"收集→执行→验证"三阶段模式生成任务列表，以JSON格式返回：
{{
  "tasks": [
    {{
      "id": "collect_1",
      "name": "需求信息收集",
      "instruction": "分析用户目标，明确具体需求和技术要求...",
      "agent_name": "analyst",
      "instruction_type": "information",
      "phase": "information", 
      "expected_output": "明确的需求规格说明",
      "precondition": "用户已提供初始目标描述"
    }}
  ]
}}"""

            tasks = self._generate_tasks_from_prompt(system_message, user_message, "initial")
            self.management_statistics['tasks_generated'] += len(tasks)
            
            logger.info(f"   ✅ 成功生成 {len(tasks)} 个初始任务")
            return tasks
            
        except Exception as e:
            logger.error(f"   ❌ 初始任务生成失败: {e}")
            return []
    
    def generate_recovery_tasks(self, failed_task: CognitiveTask, error_context: str, 
                              global_state: GlobalState) -> List[CognitiveTask]:
        """
        生成修复任务 - 整合原CognitivePlanner.generate_recovery_tasks()
        
        Args:
            failed_task: 失败的任务
            error_context: 错误上下文
            global_state: 当前全局状态
            
        Returns:
            修复任务列表
        """
        logger.info(f"🔧 认知管理者开始生成修复任务")
        logger.info(f"   📋 失败任务: {failed_task.name} (ID: {failed_task.id})")
        
        # 根据交互模式调整修复策略
        interaction_constraint = ""
        if not self.interactive_mode:
            interaction_constraint = """
**重要约束：非交互模式**
- 修复任务不能包含询问用户或需要用户干预的步骤
- 应该通过自动化方式解决问题，如重试、调整参数、使用默认值等
"""

        system_message = f"""你是一个错误修复专家，负责为失败的任务生成修复任务序列。

修复策略：
1. 分析失败原因
2. 生成针对性的修复任务
3. 确保修复任务能够解决根本问题
4. 考虑重试原任务的可能性

{interaction_constraint}"""

        # 构建智能体信息
        available_agents_str = self._build_agent_info_string()

        user_message = f"""## 失败任务信息
任务ID: {failed_task.id}
任务名称: {failed_task.name}
原始指令: {failed_task.instruction}
先决条件: {failed_task.precondition}

## 错误上下文
{error_context}

## 当前全局状态
{global_state.get_state_summary()}

## 可用智能体
{available_agents_str}

请生成修复任务序列，解决失败问题并允许重试原任务。"""

        try:
            # TODO: [优先级：中] 智能修复任务解析 - 完善修复任务生成
            # 当前实现：简化版本，只生成基本重试任务
            # 返回一个基本的重试任务
            retry_task = CognitiveTask(
                id=f"retry_{failed_task.id}_{dt.now().strftime('%H%M%S')}",
                name=f"重试：{failed_task.name}",
                instruction=f"重新执行失败的任务：{failed_task.instruction}",
                agent_name=failed_task.agent_name,
                instruction_type=failed_task.instruction_type,
                phase=failed_task.phase,
                expected_output=failed_task.expected_output,
                precondition=f"错误已修复，原先决条件满足：{failed_task.precondition}"
            )
            
            self.management_statistics['recovery_attempts'] += 1
            logger.info(f"   ✅ 生成了 1 个修复任务: {retry_task.id}")
            return [retry_task]
            
        except Exception as e:
            logger.error(f"   ❌ 修复任务生成失败: {e}")
            return []
    
    def generate_dynamic_tasks(self, modification_context: Dict[str, Any], 
                             global_state: GlobalState) -> List[CognitiveTask]:
        """
        生成动态任务 - 新增方法，整合动态任务生成逻辑
        
        Args:
            modification_context: 修正上下文信息
            global_state: 当前全局状态
            
        Returns:
            动态任务列表
        """
        logger.info(f"🚀 认知管理者开始生成动态任务")
        
        try:
            details = modification_context.get('details', {})
            new_tasks_data = details.get('new_tasks', [])
            
            if not new_tasks_data:
                logger.warning("   ⚠️ 没有提供新任务数据")
                return []
            
            dynamic_tasks = []
            for task_data in new_tasks_data:
                try:
                    # 验证任务数据
                    is_valid, errors = self._validate_new_task_data(task_data)
                    if not is_valid:
                        logger.error(f"   ❌ 任务数据验证失败: {errors}")
                        continue
                    
                    # 创建任务对象
                    new_task = self._create_task_from_data(task_data)
                    dynamic_tasks.append(new_task)
                    
                except Exception as e:
                    logger.error(f"   ❌ 创建动态任务失败: {e}")
                    continue
            
            self.management_statistics['dynamic_tasks_added'] += len(dynamic_tasks)
            logger.info(f"   ✅ 成功生成 {len(dynamic_tasks)} 个动态任务")
            return dynamic_tasks
            
        except Exception as e:
            logger.error(f"   ❌ 动态任务生成失败: {e}")
            return []
    
    # ====== 任务决策管理 ======
    
    def find_executable_tasks(self, task_list: List[CognitiveTask], 
                            global_state: GlobalState) -> List[Tuple[CognitiveTask, float]]:
        """
        找到所有可执行的任务 - 整合原CognitiveDecider.find_executable_tasks()
        
        Args:
            task_list: 任务列表
            global_state: 全局状态
            
        Returns:
            (任务, 置信度) 列表，按置信度排序
        """
        pending_tasks = [task for task in task_list if task.status == TaskStatus.PENDING]
        
        if not pending_tasks:
            return []
        
        # 少于3个任务时使用串行执行
        if len(pending_tasks) <= 2:
            return self._find_executable_tasks_serial(pending_tasks, global_state)
        
        # 多任务时使用并行执行
        return self._find_executable_tasks_parallel(pending_tasks, global_state)
    
    def select_next_task(self, executable_tasks: List[Tuple[CognitiveTask, float]], 
                        global_state: GlobalState, execution_history: List[Dict]) -> Optional[CognitiveTask]:
        """
        从可执行任务中选择下一个要执行的任务 - 整合原CognitiveDecider.select_next_task()
        
        Args:
            executable_tasks: 可执行任务列表
            global_state: 全局状态
            execution_history: 执行历史
            
        Returns:
            选择的任务，如果没有则返回None
        """
        if not executable_tasks:
            return None
            
        if len(executable_tasks) == 1:
            return executable_tasks[0][0]
            
        # 多个可执行任务时，使用LLM进行智能选择
        system_message = """你是一个认知决策专家，负责从多个可执行任务中选择最适合当前情况的下一步。

选择原则：
1. 考虑任务的紧急性和重要性
2. 考虑任务间的逻辑关系
3. 优先选择能够推进整体目标的任务
4. 考虑执行历史和当前状态

返回选择的任务ID和理由。"""

        task_options = []
        for i, (task, confidence) in enumerate(executable_tasks):
            task_options.append(f"{i+1}. {task.id} - {task.name} (置信度: {confidence:.2f})")
            task_options.append(f"   指令: {task.instruction}")
            task_options.append(f"   阶段: {task.phase.value}")
            task_options.append("")
            
        user_message = f"""## 当前全局状态
{global_state.get_state_summary()}

## 可执行任务选项
{chr(10).join(task_options)}

## 执行历史
{self._format_execution_history(execution_history)}

请选择最适合的下一个任务，返回格式：
{{
  "selected_task_id": "task_id",
  "reason": "选择理由"
}}"""

        try:
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm.invoke(messages)
            result_text = response.content.strip()
            
            # 解析选择结果
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group())
                selected_id = result_json.get('selected_task_id')
                reason = result_json.get('reason', '无理由')
                
                # 找到选中的任务
                for task, confidence in executable_tasks:
                    if task.id == selected_id:
                        self._record_decision('task_selection', {
                            'selected_task': selected_id,
                            'reason': reason,
                            'options_count': len(executable_tasks)
                        })
                        logger.info(f"决策者选择任务 {selected_id}: {reason}")
                        return task
                        
            # 如果解析失败，返回置信度最高的任务
            logger.warning("决策解析失败，返回置信度最高的任务")
            return executable_tasks[0][0]
            
        except Exception as e:
            logger.error(f"任务选择失败: {e}")
            return executable_tasks[0][0]  # 返回置信度最高的任务
    
    # ====== 工作流状态管理 ======
    
    def evaluate_workflow_status(self, task_list: List[CognitiveTask], 
                               global_state: GlobalState) -> Dict[str, Any]:
        """
        评估工作流状态 - 整合原CognitiveDecider.evaluate_workflow_status()
        
        Args:
            task_list: 任务列表
            global_state: 全局状态
            
        Returns:
            工作流状态评估结果
        """
        status_counts = {}
        for task in task_list:
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
        total_tasks = len(task_list)
        completed_tasks = status_counts.get('completed', 0)
        failed_tasks = status_counts.get('failed', 0)
        pending_tasks = status_counts.get('pending', 0)
        
        # 检查是否有可执行任务
        executable_tasks = self.find_executable_tasks(task_list, global_state)
        has_executable = len(executable_tasks) > 0
        
        evaluation = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'pending_tasks': pending_tasks,
            'has_executable_tasks': has_executable,
            'completion_rate': completed_tasks / total_tasks if total_tasks > 0 else 0,
            'status_counts': status_counts
        }
        
        # 判断工作流状态
        if completed_tasks == total_tasks:
            evaluation['workflow_status'] = 'completed'
            evaluation['recommendation'] = 'workflow_complete'
        elif has_executable:
            evaluation['workflow_status'] = 'active'
            evaluation['recommendation'] = 'continue_execution'
        elif pending_tasks > 0:
            evaluation['workflow_status'] = 'blocked'
            evaluation['recommendation'] = 'generate_new_tasks'
        else:
            evaluation['workflow_status'] = 'failed'
            evaluation['recommendation'] = 'workflow_failed'
            
        return evaluation
    
    def analyze_modification_needs(self, task_list: List[CognitiveTask], 
                                 global_state: GlobalState, 
                                 last_execution_result: Optional[Result] = None) -> Dict[str, Any]:
        """
        分析修正需求 - 整合原plan_modification_decision()逻辑
        
        Args:
            task_list: 当前任务列表
            global_state: 全局状态
            last_execution_result: 最后执行结果
            
        Returns:
            修正需求分析结果
        """
        logger.info("🔄 开始分析工作流修正需求")
        
        # 统计任务状态
        task_status_counts = {}
        for task in task_list:
            status = task.status.value
            task_status_counts[status] = task_status_counts.get(status, 0) + 1
        
        logger.info(f"   📋 任务状态分布: {dict(task_status_counts)}")
        
        system_message = """你是一个动态计划修正专家，负责分析当前情况并决定是否需要修改工作流计划。

可能的修正动作：
1. add_tasks - 添加新任务序列
2. remove_tasks - 移除无效任务
3. modify_tasks - 修改现有任务
4. no_change - 不需要修改

请综合考虑执行结果、当前状态和任务情况做出决策。"""

        # 安全地获取执行结果的字典表示
        result_info = "无"
        if last_execution_result:
            try:
                if hasattr(last_execution_result, 'to_dict'):
                    result_info = last_execution_result.to_dict()
                else:
                    result_info = {
                        'success': getattr(last_execution_result, 'success', False),
                        'stdout': getattr(last_execution_result, 'stdout', ''),
                        'stderr': getattr(last_execution_result, 'stderr', ''),
                        'return_value': getattr(last_execution_result, 'return_value', '')
                    }
            except Exception as e:
                result_info = f"结果获取失败: {str(e)}"

        user_message = f"""## 当前任务状态
{self._format_task_status(task_list)}

## 全局状态
{global_state.get_state_summary()}

## 最后执行结果
{result_info}

请决定是否需要修正计划，返回格式：
{{
  "action": "add_tasks/remove_tasks/modify_tasks/no_change",
  "reason": "决策理由",
  "details": "具体修正内容"
}}"""

        try:
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm.invoke(messages)
            result_text = response.content.strip()
            
            # 解析决策结果
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group())
                
                decision = {
                    'action': result_json.get('action', 'no_change'),
                    'reason': result_json.get('reason', '无理由'),
                    'details': result_json.get('details', ''),
                    'timestamp': dt.now()
                }
                
                self._record_decision('modification_analysis', decision)
                logger.info(f"   🎯 修正需求分析结果: {decision['action']}")
                logger.info(f"   💡 分析理由: {decision['reason']}")
                
                return decision
            else:
                logger.error("   ❌ LLM响应中未找到有效的JSON格式")
                
        except Exception as e:
            logger.error(f"   ❌ 修正需求分析失败: {e}")
            
        # 返回默认决策
        return {
            'action': 'no_change',
            'reason': '分析失败，保持现状',
            'details': '',
            'timestamp': dt.now()
        }
    
    # ====== 内部工具方法 ======
    
    def _generate_tasks_from_prompt(self, system_prompt: str, user_prompt: str, 
                                   task_type: str = "general") -> List[CognitiveTask]:
        """通用任务生成方法 - 统一LLM调用和JSON解析逻辑"""
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            result_text = response.content.strip()
            
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group())
                tasks_data = result_json.get('tasks', [])
                
                tasks = []
                for task_data in tasks_data:
                    task = self._create_task_from_data(task_data)
                    tasks.append(task)
                
                return tasks
            else:
                logger.error(f"{task_type}任务生成返回结果中没有找到有效的JSON")
                return []
                
        except Exception as e:
            logger.error(f"{task_type}任务生成失败: {e}")
            return []
    
    def _create_task_from_data(self, task_data: Dict[str, Any]) -> CognitiveTask:
        """从数据字典创建 CognitiveTask 对象 - 统一任务对象创建逻辑"""
        return CognitiveTask(
            id=task_data.get('id', f"task_{dt.now().strftime('%H%M%S')}"),
            name=task_data['name'],
            instruction=task_data['instruction'],
            agent_name=task_data['agent_name'],
            instruction_type=task_data.get('instruction_type', 'execution'),
            phase=TaskPhase(task_data.get('phase', 'execution')),
            expected_output=task_data['expected_output'],
            precondition=task_data.get('precondition', '无特殊先决条件')
        )
    
    def _build_agent_info_string(self) -> str:
        """构建智能体信息字符串 - 复用代码"""
        available_agents_info = []
        for agent_name, agent in self.available_agents.items():
            agent_info = f"{agent_name}"
            if hasattr(agent, 'api_specification') and agent.api_specification:
                agent_info += f": {agent.api_specification}"
            elif hasattr(agent, 'name') and agent.name:
                agent_info += f" ({agent.name})"
            available_agents_info.append(agent_info)
        
        return "、".join(available_agents_info)
    
    def _format_task_status(self, task_list: List[CognitiveTask]) -> str:
        """格式化任务状态 - 复用代码"""
        status_lines = []
        for task in task_list:
            status_lines.append(f"- {task.id} ({task.name}): {task.status.value}")
        return "\n".join(status_lines)
    
    def _format_execution_history(self, execution_history: List[Dict]) -> str:
        """格式化执行历史 - 复用代码"""
        if not execution_history:
            return "无执行历史"
            
        history_lines = []
        for i, record in enumerate(execution_history[-5:]):  # 只显示最近5条
            task = record.get('task')
            if task:
                task_name = task.name if hasattr(task, 'name') else '未知任务'
            else:
                task_name = '未知任务'
                
            result = record.get('result')
            if result:
                status = "成功" if result.success else "失败"
                history_lines.append(f"{i+1}. {task_name} - {status}")
            else:
                history_lines.append(f"{i+1}. {task_name} - 未知状态")
                
        return "\n".join(history_lines)
    
    def _record_decision(self, decision_type: str, decision_data: Dict[str, Any]):
        """记录决策历史 - 统一决策记录"""
        self.decision_history.append({
            'timestamp': dt.now(),
            'decision_type': decision_type,
            'data': decision_data
        })
        self.management_statistics['decisions_made'] += 1
    
    def _find_executable_tasks_serial(self, pending_tasks: List[CognitiveTask], 
                                    global_state: GlobalState) -> List[Tuple[CognitiveTask, float]]:
        """串行版本的可执行任务查找"""
        executable_tasks = []
        
        for task in pending_tasks:
            satisfied, confidence, explanation = self.condition_checker.check_precondition_satisfied(
                task.precondition, global_state
            )
            
            if satisfied and confidence > 0.5:
                executable_tasks.append((task, confidence))
                logger.debug(f"任务 {task.id} 可执行 (置信度: {confidence:.2f}): {explanation}")
            else:
                logger.debug(f"任务 {task.id} 不可执行 (置信度: {confidence:.2f}): {explanation}")
                
        # 按置信度排序
        executable_tasks.sort(key=lambda x: x[1], reverse=True)
        return executable_tasks
    
    def _find_executable_tasks_parallel(self, pending_tasks: List[CognitiveTask], 
                                      global_state: GlobalState) -> List[Tuple[CognitiveTask, float]]:
        """并行版本的可执行任务查找"""
        executable_tasks = []
        
        # 创建全局状态的快照，避免并发修改问题
        # 避免深拷贝LLM对象（包含不可序列化的线程锁）
        global_state_snapshot = GlobalState(
            current_state=global_state.current_state,
            state_history=copy.deepcopy(global_state.state_history),
            context_variables=copy.deepcopy(global_state.context_variables),
            original_goal=global_state.original_goal
        )
        
        # 限制并发数量，避免API限制
        max_workers = min(5, len(pending_tasks))
        
        def check_single_task(task):
            """检查单个任务的可执行性"""
            try:
                satisfied, confidence, explanation = self.condition_checker.check_precondition_satisfied(
                    task.precondition, global_state_snapshot
                )
                return task, satisfied, confidence, explanation
            except Exception as e:
                logger.error(f"检查任务 {task.id} 时发生错误: {e}")
                return task, False, 0.0, f"检查失败: {str(e)}"
        
        # 使用线程池并行执行
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_task = {executor.submit(check_single_task, task): task for task in pending_tasks}
            
            # 收集结果
            for future in as_completed(future_to_task):
                try:
                    task, satisfied, confidence, explanation = future.result()
                    
                    if satisfied and confidence > 0.5:
                        executable_tasks.append((task, confidence))
                        logger.debug(f"任务 {task.id} 可执行 (置信度: {confidence:.2f}): {explanation}")
                    else:
                        logger.debug(f"任务 {task.id} 不可执行 (置信度: {confidence:.2f}): {explanation}")
                        
                except Exception as e:
                    task = future_to_task[future]
                    logger.error(f"处理任务 {task.id} 结果时发生错误: {e}")
        
        # 按置信度排序
        executable_tasks.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"并行检查 {len(pending_tasks)} 个任务，找到 {len(executable_tasks)} 个可执行任务")
        return executable_tasks
    
    def _validate_new_task_data(self, task_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证新任务数据的有效性"""
        errors = []
        
        # 必填字段检查
        required_fields = ['name', 'instruction', 'agent_name', 'expected_output']
        for field in required_fields:
            if field not in task_data or not task_data[field]:
                errors.append(f"缺少必填字段: {field}")
        
        # Agent存在性检查
        agent_name = task_data.get('agent_name')
        if agent_name and agent_name not in self.available_agents:
            available_agents = ', '.join(self.available_agents.keys())
            errors.append(f"智能体 '{agent_name}' 不存在，可用智能体: {available_agents}")
        
        # 任务阶段检查
        phase = task_data.get('phase')
        if phase:
            try:
                TaskPhase(phase)
            except ValueError:
                valid_phases = ', '.join([p.value for p in TaskPhase])
                errors.append(f"无效的任务阶段 '{phase}'，有效值: {valid_phases}")
        
        # 指令类型检查
        instruction_type = task_data.get('instruction_type')
        if instruction_type:
            valid_types = ['execution', 'information']
            if instruction_type not in valid_types:
                errors.append(f"无效的指令类型 '{instruction_type}'，有效值: {', '.join(valid_types)}")
        
        return len(errors) == 0, errors
    
    def get_management_statistics(self) -> Dict[str, Any]:
        """获取管理统计信息"""
        return {
            **self.management_statistics,
            'total_decisions': len(self.decision_history),
            'interactive_mode': self.interactive_mode
        }

class CognitiveExecutor:
    """认知执行者 - 纯粹的执行单元"""
    
    def __init__(self, agents: Dict[str, Agent]):
        self.agents = agents
        self.execution_history: List[Dict[str, Any]] = []
        
    def execute_task(self, task: CognitiveTask, global_state: GlobalState) -> Result:
        """
        执行单个任务
        
        Args:
            task: 要执行的任务
            global_state: 全局状态
            
        Returns:
            执行结果
        """
        logger.info(f"开始执行任务: {task.id} - {task.name}")
        
        # 更新任务状态
        task.status = TaskStatus.RUNNING
        task.updated_at = dt.now()
        
        try:
            # 获取执行者
            agent = self.agents.get(task.agent_name)
            if not agent:
                raise ValueError(f"找不到智能体: {task.agent_name}")
            
            # 根据指令类型选择执行方式
            if task.instruction_type == "execution":
                # 执行性任务 - 调用jupyter notebook
                result = agent.execute_sync(task.instruction)
            else:
                # 信息性任务 - 仅对话
                result = agent.chat_sync(task.instruction)
            
            # 更新任务状态
            if result and result.success:
                task.status = TaskStatus.COMPLETED
                task.result = result
                logger.info(f"任务执行成功: {task.id}")
            else:
                task.status = TaskStatus.FAILED
                task.result = result
                logger.error(f"任务执行失败: {task.id}")
                
            task.updated_at = dt.now()
            
            # 记录执行历史
            self.execution_history.append({
                'task_id': task.id,
                'task_name': task.name,
                'agent_name': task.agent_name,
                'result': result,
                'timestamp': dt.now(),
                'duration': (dt.now() - task.created_at).total_seconds()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"任务执行异常: {task.id} - {str(e)}")
            
            # 创建失败结果 - 兼容原有Result类
            error_result = Result(
                success=False,
                code="",
                stdout=f"执行异常: {str(e)}",
                stderr=str(e)
            )
            
            task.status = TaskStatus.FAILED
            task.result = error_result
            task.updated_at = dt.now()
            
            return error_result
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        if not self.execution_history:
            return {'total_executions': 0}
            
        successful = sum(1 for record in self.execution_history 
                        if record['result'] and record['result'].success)
        failed = len(self.execution_history) - successful
        
        durations = [record['duration'] for record in self.execution_history]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            'total_executions': len(self.execution_history),
            'successful_executions': successful,
            'failed_executions': failed,
            'success_rate': successful / len(self.execution_history),
            'average_duration': avg_duration
        }

class CognitiveWorkflowEngine:
    """
    认知工作流引擎 - 整合三大角色的协作机制
    
    真正实现了认知工作流的核心理念：
    1. 动态导航而非静态图
    2. 三角色协作
    3. 状态满足性检查
    4. 动态计划修正
    """
    
    def __init__(self, llm: BaseChatModel, agents: Dict[str, Agent], 
                 max_iterations: int = 50, enable_auto_recovery: bool = True,
                 interactive_mode: bool = False):
        """
        初始化认知工作流引擎
        
        Args:
            llm: 语言模型
            agents: 可用的智能体字典 {name: agent_instance}
            max_iterations: 最大迭代次数
            enable_auto_recovery: 是否启用自动恢复
            interactive_mode: 是否启用交互模式，默认False不生成询问用户的任务
        """
        self.llm = llm
        self.agents = agents
        self.max_iterations = max_iterations
        self.enable_auto_recovery = enable_auto_recovery
        self.interactive_mode = interactive_mode
        
        # 初始化两大角色 - 重构后的架构
        self.condition_checker = StateConditionChecker(llm)
        self.manager = CognitiveManager(llm, agents, self.condition_checker, interactive_mode)
        self.executor = CognitiveExecutor(agents)
        
        # 新架构组件完全替代旧架构
        
        # 工作流状态 - 启用智能状态生成
        self.global_state = GlobalState(current_state="工作流初始化")
        self.global_state.set_llm(llm)  # 设置LLM用于智能状态生成
        self.task_list: List[CognitiveTask] = []
        self.execution_log: List[Dict[str, Any]] = []
        self.iteration_count = 0
        
        logger.info("认知工作流引擎初始化完成")
        
    def set_interactive_mode(self, interactive: bool):
        """
        设置交互模式
        
        Args:
            interactive: True启用交互模式，False禁用用户交互
        """
        self.interactive_mode = interactive
        self.manager.interactive_mode = interactive
        logger.info(f"交互模式已设置为: {'启用' if interactive else '禁用'}")
        
    def is_interactive_mode(self) -> bool:
        """
        检查当前是否为交互模式
        
        Returns:
            bool: True表示交互模式启用，False表示禁用
        """
        return self.interactive_mode
        
    def execute_cognitive_workflow(self, goal: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行认知工作流 - 主入口方法
        
        Args:
            goal: 高层次目标
            context: 额外上下文
            
        Returns:
            执行结果摘要
        """
        logger.info(f"开始执行认知工作流: {goal}")
        
        # 1. 初始化阶段
        self._initialize_workflow(goal, context)
        
        # 2. 主执行循环 - 真正的动态导航
        while self.iteration_count < self.max_iterations:
            self.iteration_count += 1
            logger.debug(f"工作流迭代 {self.iteration_count}")
            
            # 2.1 找到可执行任务（状态满足性检查）
            executable_tasks = self.manager.find_executable_tasks(self.task_list, self.global_state)
            
            if not executable_tasks:
                # 没有可执行任务，评估工作流状态
                status_eval = self.manager.evaluate_workflow_status(self.task_list, self.global_state)
                
                if status_eval['recommendation'] == 'workflow_complete':
                    logger.info("工作流完成")
                    break
                elif status_eval['recommendation'] == 'generate_new_tasks':
                    # 动态生成新任务
                    if self._handle_no_executable_tasks():
                        continue
                    else:
                        logger.warning("无法生成新任务，工作流结束")
                        break
                else:
                    logger.warning(f"工作流状态异常: {status_eval['workflow_status']}")
                    break
            
            # 2.2 管理者选择下一个任务（认知导航）
            selected_task = self.manager.select_next_task(
                executable_tasks, self.global_state, self.execution_log
            )
            
            if not selected_task:
                logger.warning("管理者未能选择任务")
                break
                
            # 2.3 执行者执行任务
            result = self.executor.execute_task(selected_task, self.global_state)
            
            # 2.4 更新全局状态
            self._update_global_state(selected_task, result)
            
            # 2.5 记录执行日志
            self.execution_log.append({
                'iteration': self.iteration_count,
                'task': selected_task,
                'result': result,
                'timestamp': dt.now()
            })
            
            # 2.6 动态计划修正决策
            logger.info(f"🤔 开始第 {self.iteration_count} 轮动态计划修正决策")
            logger.info(f"   📝 刚完成任务: {selected_task.name} (ID: {selected_task.id})")
            logger.info(f"   🎯 执行结果: {'✅ 成功' if result.success else '❌ 失败'}")
            
            modification_decision = self.manager.analyze_modification_needs(
                self.task_list, self.global_state, result
            )
            
            if modification_decision['action'] != 'no_change':
                logger.info(f"   🚨 检测到需要计划修正: {modification_decision['action']}")
                self._apply_plan_modification(modification_decision)
            else:
                logger.info("   ✅ 计划无需修正，继续当前流程")
            
            # 2.7 错误恢复处理
            if not result.success and self.enable_auto_recovery:
                logger.info(f"   🔧 任务失败，启动自动恢复机制")
                self._handle_task_failure(selected_task, result)
            else:
                logger.info(f"   ➡️ 继续执行下一轮迭代")
        
        logger.info(f"🏁 工作流执行完成，共进行了 {self.iteration_count} 次迭代")
        # 3. 生成执行摘要
        return self._generate_workflow_summary()
        
    def _initialize_workflow(self, goal: str, context: Dict[str, Any] = None):
        """初始化工作流"""
        # 设置用户原始目标
        self.global_state.set_original_goal(goal)
        # 使用智能状态更新而不是简单状态更新
        self.global_state.update_state(
            new_state=f"开始执行目标: {goal}",
            source="user"
        )
        
        # 管理者生成初始任务列表
        self.task_list = self.manager.generate_initial_tasks(goal, context)
        # 记录初始任务列表到日志
        logger.info("=== 初始任务列表 ===")
        for i, task in enumerate(self.task_list, 1):
            logger.info(f"任务 {i}: {task.name} (ID: {task.id})")
            logger.info(f"  指令: {task.instruction}")
            logger.info(f"  代理: {task.agent_name}")
            logger.info(f"  先决条件: {task.precondition}")
            logger.info(f"  预期输出: {task.expected_output}")
            logger.info(f"  阶段: {task.phase.value}")
            logger.info(f"  类型: {task.instruction_type}")
            logger.info("---")
        
        logger.info(f"管理者生成了 {len(self.task_list)} 个初始任务")
        
        # 恢复智能状态更新
        self.global_state.update_state(
            new_state=f"已生成 {len(self.task_list)} 个任务，准备开始执行",
            source="manager"
        )
        
    def _update_global_state(self, task: CognitiveTask, result: Result):
        """根据任务执行结果更新全局状态"""
        # 使用智能状态生成
        source = f"executor_{task.agent_name}"
        
        # 构建备用状态（如果智能生成失败时使用）
        output = safe_get_result_return_value(result)
        error = safe_get_result_error(result)
        
        if result.success:
            fallback_state = f"成功完成任务 '{task.name}'"
        else:
            fallback_state = f"任务 '{task.name}' 执行失败"
            
        # 调用智能状态更新
        new_state = self.global_state.update_state(
            new_state=fallback_state,
            source=source,
            task=task,
            result=result
        )
        
        # 更新上下文变量
        if result.success and task.expected_output:
            # 将执行结果存储为上下文变量
            variable_name = f"result_{task.id}"
            self.global_state.context_variables[variable_name] = output
        
    def _handle_no_executable_tasks(self) -> bool:
        """
        处理没有可执行任务的情况 - 动态生成新任务
        
        Returns:
            是否成功生成新任务
        """
        logger.info("没有可执行任务，尝试动态生成新任务")
        
        # 分析当前状况
        pending_tasks = [task for task in self.task_list if task.status == TaskStatus.PENDING]
        failed_tasks = [task for task in self.task_list if task.status == TaskStatus.FAILED]
        
        # 如果有失败任务，尝试生成修复任务
        if failed_tasks and self.enable_auto_recovery:
            latest_failed = failed_tasks[-1]
            error_context = "未知错误"
            if latest_failed.result:
                error_context = safe_get_result_error(latest_failed.result) or safe_get_result_return_value(latest_failed.result) or "未知错误"
            
            recovery_tasks = self.manager.generate_recovery_tasks(
                latest_failed, 
                error_context,
                self.global_state
            )
            
            if recovery_tasks:
                self.task_list.extend(recovery_tasks)
                logger.info(f"生成了 {len(recovery_tasks)} 个修复任务")
                return True
        
        # TODO: [优先级：中] 智能补充任务生成 - 增强复杂场景处理能力
        # 当前实现：仅处理失败任务的修复，无法生成新的补充任务
        # 需要实现：
        # 1. 基于当前状态和原始目标分析缺失的任务
        # 2. 检测是否需要额外的信息收集任务
        # 3. 生成前置条件准备任务（如环境配置、依赖安装）
        # 4. 支持目标细化：将模糊目标分解为具体任务
        # 5. 智能任务推荐：基于上下文变量推荐相关任务
        # 示例实现：
        # if not failed_tasks and pending_tasks:
        #     # 分析阻塞原因
        #     blocked_analysis = self._analyze_blocked_tasks(pending_tasks)
        #     if blocked_analysis['needs_new_tasks']:
        #         new_tasks = self.planner.generate_supplementary_tasks(
        #             self.global_state.original_goal,
        #             blocked_analysis,
        #             self.global_state
        #         )
        #         if new_tasks:
        #             self.task_list.extend(new_tasks)
        #             return True
        
        return False
        
    def _apply_plan_modification(self, modification_decision: Dict[str, Any]):
        """应用计划修正决策"""
        action = modification_decision['action']
        reason = modification_decision['reason']
        
        logger.info(f"🚀 开始应用计划修正: {action}")
        logger.info(f"   📋 修正原因: {reason}")
        
        if action == 'add_tasks':
            logger.info("   🔥 触发动态任务添加流程")
            # 使用管理者进行动态任务添加
            dynamic_tasks = self.manager.generate_dynamic_tasks(modification_decision, self.global_state)
            if dynamic_tasks:
                self.task_list.extend(dynamic_tasks)
                task_names = [task.name for task in dynamic_tasks]
                logger.info(f"   ✅ 动态任务添加成功: {', '.join(task_names)}")
            else:
                logger.warning("   ⚠️ 动态任务添加失败")
        elif action == 'remove_tasks':
            logger.info("   🗑️ 触发动态任务移除流程（TODO：未实现）")
            # TODO: [优先级：中] 动态任务移除 - 计划优化功能
            pass
        elif action == 'modify_tasks':
            logger.info("   ✏️ 触发动态任务修改流程（TODO：未实现）")
            # TODO: [优先级：中] 动态任务修改 - 计划适应功能
            pass
            
        self.global_state.update_state(
            new_state=f"计划修正: {reason}",
            source="manager"
        )
        logger.info("✅ 计划修正应用完成")
    
    def _handle_task_failure(self, failed_task: CognitiveTask, result: Result):
        """处理任务失败 - 自动恢复机制"""
        logger.warning(f"任务失败，启动自动恢复: {failed_task.id}")
        
        # 生成修复任务
        error_context = safe_get_result_error(result) or safe_get_result_return_value(result) or "未知错误"
        recovery_tasks = self.manager.generate_recovery_tasks(
            failed_task, 
            error_context,
            self.global_state
        )
        
        if recovery_tasks:
            self.task_list.extend(recovery_tasks)
            logger.info(f"生成了 {len(recovery_tasks)} 个修复任务")
            
    def _generate_workflow_summary(self) -> Dict[str, Any]:
        """生成工作流执行摘要"""
        completed_tasks = [task for task in self.task_list if task.status == TaskStatus.COMPLETED]
        failed_tasks = [task for task in self.task_list if task.status == TaskStatus.FAILED]
        pending_tasks = [task for task in self.task_list if task.status == TaskStatus.PENDING]
        
        summary = {
            'workflow_status': 'completed' if len(pending_tasks) == 0 else 'partial',
            'total_iterations': self.iteration_count,
            'total_tasks': len(self.task_list),
            'completed_tasks': len(completed_tasks),
            'failed_tasks': len(failed_tasks),
            'pending_tasks': len(pending_tasks),
            'success_rate': len(completed_tasks) / len(self.task_list) if self.task_list else 0,
            'final_state': self.global_state.current_state,
            'execution_time': self.execution_log[-1]['timestamp'] - self.execution_log[0]['timestamp'] if self.execution_log else None,
            'executor_stats': self.executor.get_execution_statistics(),
            'decision_count': len(self.manager.decision_history),
            'interactive_mode': self.interactive_mode
        }
        
        logger.info(f"工作流执行完成: {summary['success_rate']:.2%} 成功率")
        return summary
        
    def get_task_status_report(self) -> str:
        """获取任务状态报告"""
        report_lines = ["=== 认知工作流任务状态报告 ==="]
        
        for phase in TaskPhase:
            phase_tasks = [task for task in self.task_list if task.phase == phase]
            if phase_tasks:
                report_lines.append(f"\n【{phase.value.upper()}阶段】")
                for task in phase_tasks:
                    status_icon = {
                        TaskStatus.COMPLETED: "✅",
                        TaskStatus.FAILED: "❌", 
                        TaskStatus.RUNNING: "🔄",
                        TaskStatus.PENDING: "⏳",
                        TaskStatus.EXECUTABLE: "🚀"
                    }.get(task.status, "❓")
                    
                    report_lines.append(f"  {status_icon} {task.id}: {task.name}")
                    if task.status == TaskStatus.FAILED and task.result:
                        error_msg = safe_get_result_error(task.result) or safe_get_result_return_value(task.result) or "未知错误"
                        report_lines.append(f"    错误: {error_msg}")
                        
        report_lines.append(f"\n当前状态: {self.global_state.current_state}")
        return "\n".join(report_lines)

if __name__ == "__main__":
    # 基本测试代码
    print("认知工作流系统模块已加载")
    print("核心组件:")
    print("- CognitiveManager (认知管理者) [重构后的统一管理组件]")
    print("- CognitiveExecutor (执行者)")
    print("- StateConditionChecker (状态满足性检查器)")
    print("- CognitiveTask (认知任务)")
    print("- GlobalState (全局状态)")
    print("- CognitiveWorkflowEngine (认知工作流引擎)")
    print()
    print("兼容性组件 (已整合到CognitiveManager):")
    print("- CognitivePlanner (规划者)")
    print("- CognitiveDecider (决策者)")