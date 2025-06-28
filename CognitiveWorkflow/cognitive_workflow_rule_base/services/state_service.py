# -*- coding: utf-8 -*-
"""
状态服务

专注于自然语言状态管理，提供状态更新、状态检查、
状态持久化和状态分析等核心功能。
"""

from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
import logging
from datetime import datetime
import uuid

from ..domain.entities import GlobalState, WorkflowResult, ProductionRule
from ..domain.repositories import StateRepository
from ..domain.value_objects import StateChangeAnalysis, MatchingResult
from .language_model_service import LanguageModelService

if TYPE_CHECKING:
    from ..domain.entities import RuleSet

logger = logging.getLogger(__name__)


class StateService:
    """状态服务 - 专注于自然语言状态管理"""
    
    def __init__(self, 
                 llm_service: LanguageModelService,
                 state_repository: StateRepository):
        """
        初始化状态服务
        
        Args:
            llm_service: 语言模型服务
            state_repository: 状态仓储
        """
        self.llm_service = llm_service
        self.state_repository = state_repository
        self._current_state: Optional[GlobalState] = None
        
    def update_state(self, execution_result: WorkflowResult, global_state: GlobalState, goal: str = None, rule_set: 'RuleSet' = None) -> GlobalState:
        """
        更新全局状态并检查目标达成
        
        Args:
            execution_result: 执行结果
            global_state: 当前全局状态
            goal: 工作流目标（可选，用于目标达成检查）
            rule_set: 当前规则集（可选，用于智能状态生成和数据收集）
            
        Returns:
            GlobalState: 更新后的全局状态，包含目标达成信息
        """
        try:
            # 生成新的状态描述（考虑规则集上下文）
            new_description = self._generate_new_state_description(
                execution_result, global_state, rule_set
            )
            
            # 创建新的状态实例
            new_state = GlobalState(
                id=f"{global_state.id}_iter_{global_state.iteration_count + 1}",  # Use deterministic ID
                state=new_description,
                context_variables=global_state.context_variables.copy(),
                execution_history=global_state.execution_history.copy(),
                # timestamp=datetime.now(),  # Removed for LLM caching
                workflow_id=global_state.workflow_id,
                iteration_count=global_state.iteration_count + 1,
                goal_achieved=global_state.goal_achieved
            )
            
            # 更新执行历史
            history_entry = self._create_history_entry(execution_result)
            new_state.execution_history.append(history_entry)
            
            # 更新上下文变量
            self._update_context_variables(new_state, execution_result)
            
            # 检查目标达成（如果提供了目标）
            if goal and not new_state.goal_achieved:
                is_goal_achieved = self.evaluate_goal_achievement(goal, new_state)
                if is_goal_achieved:
                    new_state.goal_achieved = True
                    logger.info(f"检测到目标已达成: {goal}")
                    # 添加目标达成记录到历史
                    new_state.execution_history.append("[目标达成] 工作流目标已成功完成")
            
            # 保存状态
            self.state_repository.save_state(new_state)
            self._current_state = new_state
            
            # 使用红色字体打印状态更新信息
            self._print_state_update_in_red(new_state, execution_result)
            
            goal_status = " [目标已达成]" if new_state.goal_achieved else ""
            logger.info(f"状态已更新: {new_description[:100]}...{goal_status}")
            return new_state
            
        except Exception as e:
            logger.error(f"状态更新失败: {e}")
            # 返回原状态，避免破坏工作流
            return global_state
    
    def get_current_state(self) -> Optional[GlobalState]:
        """
        获取当前状态
        
        Returns:
            Optional[GlobalState]: 当前状态，可能为None
        """
        return self._current_state
    
    def get_state_history(self, workflow_id: str) -> List[GlobalState]:
        """
        获取状态历史
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            List[GlobalState]: 状态历史列表
        """
        try:
            return self.state_repository.get_state_history(workflow_id)
        except Exception as e:
            logger.error(f"获取状态历史失败: {e}")
            return []
    
    def check_rule_condition_satisfied(self, 
                                     condition: str, 
                                     global_state: GlobalState) -> Tuple[bool, float, str]:
        """
        检查规则条件是否满足
        
        Args:
            condition: 规则条件（自然语言）
            global_state: 全局状态
            
        Returns:
            Tuple[bool, float, str]: (是否满足, 置信度, 解释)
        """
        try:
            # 使用语言模型进行语义匹配
            matching_result = self.llm_service.semantic_match(
                condition, global_state.state
            )
            
            return (
                matching_result.is_match,
                matching_result.confidence,
                matching_result.reasoning
            )
            
        except Exception as e:
            logger.error(f"条件检查失败: {e}")
            return False, 0.0, f"检查失败: {str(e)}"
    
    def find_applicable_rules(self, 
                            rules: List[ProductionRule], 
                            global_state: GlobalState) -> List[ProductionRule]:
        """
        查找适用规则
        
        Args:
            rules: 规则列表
            global_state: 全局状态
            
        Returns:
            List[ProductionRule]: 适用的规则列表
        """
        applicable_rules = []
        
        for rule in rules:
            try:
                is_satisfied, confidence, _ = self.check_rule_condition_satisfied(
                    rule.condition, global_state
                )
                
                # 只有高置信度的匹配才认为是适用的
                if is_satisfied and confidence >= 0.7:
                    applicable_rules.append(rule)
                    logger.debug(f"规则适用: {rule.name} (置信度: {confidence:.2f})")
                
            except Exception as e:
                logger.error(f"规则适用性检查失败: {rule.id}, {e}")
                continue
        
        # 按优先级排序
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)
        
        logger.info(f"找到 {len(applicable_rules)} 个适用规则")
        return applicable_rules
    
    def evaluate_goal_achievement(self, goal: str, global_state: GlobalState) -> bool:
        """
        评估目标达成
        
        Args:
            goal: 目标描述
            global_state: 全局状态
            
        Returns:
            bool: 是否达成目标
        """
        try:
            is_achieved, confidence, analysis = self.llm_service.evaluate_goal_achievement(
                goal, global_state.state
            )
            
            logger.info(f"目标达成评估: {is_achieved} (置信度: {confidence:.2f})")
            logger.debug(f"分析: {analysis}")
            
            # 只有高置信度的判断才认为是可靠的
            return is_achieved and confidence >= 0.8
            
        except Exception as e:
            logger.error(f"目标达成评估失败: {e}")
            return False
    
    def save_state(self, global_state: GlobalState) -> bool:
        """
        保存状态
        
        Args:
            global_state: 要保存的状态
            
        Returns:
            bool: 是否保存成功
        """
        try:
            self.state_repository.save_state(global_state)
            self._current_state = global_state
            return True
        except Exception as e:
            logger.error(f"状态保存失败: {e}")
            return False
    
    def load_state(self, state_id: str) -> Optional[GlobalState]:
        """
        加载状态
        
        Args:
            state_id: 状态ID
            
        Returns:
            Optional[GlobalState]: 加载的状态，可能为None
        """
        try:
            state = self.state_repository.load_state(state_id)
            self._current_state = state
            return state
        except Exception as e:
            logger.error(f"状态加载失败: {e}")
            return None
    
    def analyze_state_changes(self, 
                            before: GlobalState, 
                            after: GlobalState) -> StateChangeAnalysis:
        """
        分析状态变化
        
        Args:
            before: 变化前状态
            after: 变化后状态
            
        Returns:
            StateChangeAnalysis: 状态变化分析
        """
        try:
            # 计算语义相似度
            similarity = self.llm_service.evaluate_semantic_similarity(
                before.state, after.state
            )
            
            # 识别关键变化
            key_changes = self._identify_key_changes(before, after)
            
            # 评估变化重要性
            change_significance = self._evaluate_change_significance(
                before, after, similarity
            )
            
            return StateChangeAnalysis(
                before_state=before.state,
                after_state=after.state,
                key_changes=key_changes,
                semantic_similarity=similarity,
                change_significance=change_significance,
                timestamp=datetime.now()  # Keep this as it's part of analysis, not state
            )
            
        except Exception as e:
            logger.error(f"状态变化分析失败: {e}")
            return StateChangeAnalysis(
                before_state=before.state,
                after_state=after.state,
                key_changes=[],
                semantic_similarity=0.0,
                change_significance='unknown',
                timestamp=datetime.now()  # Keep this as it's part of analysis, not state
            )
    
    def create_initial_state(self, goal: str, workflow_id: str) -> GlobalState:
        """
        创建初始状态
        
        Args:
            goal: 工作流目标
            workflow_id: 工作流ID
            
        Returns:
            GlobalState: 初始状态
        """
        initial_description = f"工作流已启动，目标：{goal}。当前处于初始状态，等待规则生成和执行。"
        
        initial_state = GlobalState(
            id=f"{workflow_id}_initial",  # Use deterministic ID
            state=initial_description,
            context_variables={'goal': goal},
            execution_history=[f"[iter_0] 工作流启动"],  # Use iteration instead of timestamp
            # timestamp=datetime.now(),  # Removed for LLM caching
            workflow_id=workflow_id,
            iteration_count=0,
            goal_achieved=False
        )
        
        # 保存初始状态
        self.save_state(initial_state)
        
        logger.info(f"初始状态已创建: {workflow_id}")
        return initial_state
    
    def _generate_new_state_description(self, 
                                       execution_result: WorkflowResult, 
                                       current_state: GlobalState,
                                       rule_set: 'RuleSet' = None) -> str:
        """
        生成新的状态描述，考虑规则集上下文
        
        Args:
            execution_result: 执行结果
            current_state: 当前状态
            rule_set: 当前规则集（用于了解可能需要的数据和后续规则）
            
        Returns:
            str: 新的状态描述
        """
        try:
            # 构建规则集上下文信息
            rule_context = ""
            if rule_set:
                rule_context = f"""

## 当前规则集上下文
目标: {rule_set.goal}
可用规则概览:
{self._format_rules_for_context(rule_set.rules)}

## 数据收集指导
请在状态描述中特别关注和收集以下类型的信息：
1. 规则执行相关的关键数据和变量
2. 可能触发后续规则的状态变化
3. 目标达成进度的具体指标
4. 可能影响规则选择的环境因素
"""
            
            prompt = f"""
基于以下信息，生成新的系统状态描述：

当前状态: {current_state.state}

执行结果:
- 成功: {'是' if execution_result.success else '否'}
- 消息: {execution_result.message}
- 数据: {execution_result.data if execution_result.data else '无'}
{rule_context}

请生成一个简洁、准确的新状态描述，重点说明：
1. 执行的操作和结果
2. 当前系统的主要状态
3. 下一步可能的行动方向
4. 【重要】收集并提及规则集可能用到的关键数据和状态信息

状态描述应该清晰、客观，便于后续的规则匹配和决策。
"""
            
            new_description = self.llm_service.generate_natural_language_response(prompt)
            
            # 确保描述不为空
            if not new_description.strip():
                new_description = f"执行完成: {execution_result.message}"
            
            return new_description
            
        except Exception as e:
            logger.error(f"状态描述生成失败: {e}")
            # 回退到简单的描述
            status = "成功" if execution_result.success else "失败"
            return f"上一步执行{status}: {execution_result.message}"
    
    def _create_history_entry(self, execution_result: WorkflowResult) -> str:
        """
        创建历史记录条目
        
        Args:
            execution_result: 执行结果
            
        Returns:
            str: 历史记录条目
        """
        # Use deterministic identifier instead of timestamp
        status = "成功" if execution_result.success else "失败"
        return f"[执行{status}] {execution_result.message}"
    
    def _update_context_variables(self, state: GlobalState, execution_result: WorkflowResult) -> None:
        """
        更新上下文变量
        
        Args:
            state: 要更新的状态
            execution_result: 执行结果
        """
        # 从执行结果的元数据中更新上下文
        if execution_result.metadata:
            for key, value in execution_result.metadata.items():
                if key.startswith('context_'):
                    # 移除前缀并添加到上下文
                    context_key = key[8:]  # 移除 'context_' 前缀
                    state.context_variables[context_key] = value
        
        # 更新执行统计
        state.context_variables['last_execution_success'] = execution_result.success
        # state.context_variables['last_execution_time'] = execution_result.timestamp.isoformat()  # Removed for LLM caching
        
        # 如果执行结果包含数据，可能需要更新特定的上下文变量
        if execution_result.data and isinstance(execution_result.data, dict):
            for key, value in execution_result.data.items():
                if key.startswith('state_'):
                    # 状态相关的数据
                    context_key = key[6:]  # 移除 'state_' 前缀
                    state.context_variables[context_key] = value
    
    def _identify_key_changes(self, before: GlobalState, after: GlobalState) -> List[str]:
        """
        识别关键变化
        
        Args:
            before: 变化前状态
            after: 变化后状态
            
        Returns:
            List[str]: 关键变化列表
        """
        changes = []
        
        # 比较上下文变量
        before_context = before.context_variables
        after_context = after.context_variables
        
        # 新增的变量
        new_keys = set(after_context.keys()) - set(before_context.keys())
        for key in new_keys:
            changes.append(f"新增上下文变量: {key} = {after_context[key]}")
        
        # 修改的变量
        common_keys = set(before_context.keys()) & set(after_context.keys())
        for key in common_keys:
            if before_context[key] != after_context[key]:
                changes.append(f"更新上下文变量: {key} = {after_context[key]}")
        
        # 删除的变量
        removed_keys = set(before_context.keys()) - set(after_context.keys())
        for key in removed_keys:
            changes.append(f"删除上下文变量: {key}")
        
        # 迭代次数变化
        if after.iteration_count != before.iteration_count:
            changes.append(f"迭代次数: {before.iteration_count} -> {after.iteration_count}")
        
        return changes
    
    def _evaluate_change_significance(self, 
                                    before: GlobalState, 
                                    after: GlobalState, 
                                    similarity: float) -> str:
        """
        评估变化重要性
        
        Args:
            before: 变化前状态
            after: 变化后状态
            similarity: 语义相似度
            
        Returns:
            str: 变化重要性级别
        """
        # 基于语义相似度判断
        if similarity >= 0.9:
            return 'minor'
        elif similarity >= 0.7:
            return 'moderate'
        else:
            return 'major'
    
    def _print_state_update_in_red(self, new_state: GlobalState, execution_result: WorkflowResult) -> None:
        """
        使用红色字体打印状态更新信息
        
        Args:
            new_state: 更新后的全局状态
            execution_result: 执行结果
        """
        # ANSI红色字体代码
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BOLD = '\033[1m'
        RESET = '\033[0m'
        
        try:
            print(f"\n{RED}{BOLD}🔄 状态管理器 - 状态更新{RESET}")
            print(f"{RED}{'=' * 50}{RESET}")
            
            # 打印执行结果状态
            status_color = GREEN if execution_result.success else RED
            status_icon = "✅" if execution_result.success else "❌"
            print(f"{RED}{BOLD}📊 执行状态:{RESET} {status_color}{status_icon} {'成功' if execution_result.success else '失败'}{RESET}")
            
            # 打印执行消息
            print(f"{RED}{BOLD}💬 执行消息:{RESET}")
            print(f"{RED}   {execution_result.message}{RESET}")
            
            # 打印新状态描述
            print(f"{RED}{BOLD}🎯 新状态描述:{RESET}")
            # 限制显示长度，避免输出过长
            state_desc = new_state.state
            if len(state_desc) > 150:
                state_desc = state_desc[:150] + "..."
            print(f"{RED}   {state_desc}{RESET}")
            
            # 打印迭代信息
            print(f"{RED}{BOLD}🔢 迭代次数:{RESET} {RED}{new_state.iteration_count}{RESET}")
            
            # 打印目标达成状态
            goal_color = GREEN if new_state.goal_achieved else YELLOW
            goal_icon = "🎉" if new_state.goal_achieved else "⏳"
            goal_text = "已达成" if new_state.goal_achieved else "进行中"
            print(f"{RED}{BOLD}🎯 目标状态:{RESET} {goal_color}{goal_icon} {goal_text}{RESET}")
            
            # 打印上下文变量变化（如果有的话）
            if execution_result.metadata:
                context_changes = []
                for key, value in execution_result.metadata.items():
                    if key.startswith('context_'):
                        context_key = key[8:]  # 移除 'context_' 前缀
                        context_changes.append(f"{context_key}={value}")
                
                if context_changes:
                    print(f"{RED}{BOLD}📝 上下文更新:{RESET}")
                    for change in context_changes[:3]:  # 最多显示3个变化
                        print(f"{RED}   + {change}{RESET}")
                    if len(context_changes) > 3:
                        print(f"{RED}   ... 还有 {len(context_changes) - 3} 个变化{RESET}")
            
            # 打印最近的执行历史（最后2条）
            if new_state.execution_history:
                recent_history = new_state.execution_history[-2:]
                print(f"{RED}{BOLD}📚 最近历史:{RESET}")
                for history_item in recent_history:
                    # 限制历史条目长度
                    history_display = history_item[:80] + "..." if len(history_item) > 80 else history_item
                    print(f"{RED}   • {history_display}{RESET}")
            
            # 如果有错误详情，显示错误信息
            if not execution_result.success and execution_result.error_details:
                print(f"{RED}{BOLD}⚠️  错误详情:{RESET}")
                error_details = execution_result.error_details
                if len(error_details) > 100:
                    error_details = error_details[:100] + "..."
                print(f"{RED}   {error_details}{RESET}")
            
            print(f"{RED}{'=' * 50}{RESET}\n")
            
        except Exception as e:
            # 如果打印失败，至少记录到日志
            logger.error(f"红色状态打印失败: {e}")
            # 简单的备用打印
            status = "成功" if execution_result.success else "失败"
            goal_status = " [目标已达成]" if new_state.goal_achieved else ""
            print(f"\n🔄 状态更新: {status} | 迭代 {new_state.iteration_count}{goal_status}")
            print(f"描述: {new_state.state[:100]}...\n")
    
    def _format_rules_for_context(self, rules) -> str:
        """
        格式化规则信息供状态生成上下文使用
        
        Args:
            rules: 规则列表
            
        Returns:
            str: 格式化的规则概览信息
        """
        if not rules:
            return "无可用规则"
        
        # 按阶段分组规则
        phases = {}
        for rule in rules:
            phase = rule.phase.value
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(rule)
        
        formatted_lines = []
        for phase, phase_rules in phases.items():
            formatted_lines.append(f"【{phase}阶段】")
            for rule in phase_rules[:3]:  # 每个阶段最多显示3个规则
                formatted_lines.append(f"  - {rule.name}: {rule.condition[:50]}...")
            if len(phase_rules) > 3:
                formatted_lines.append(f"  - ... 还有{len(phase_rules) - 3}个规则")
        
        return '\n'.join(formatted_lines)