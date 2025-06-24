# -*- coding: utf-8 -*-
"""
规则匹配服务

专注于语义匹配和规则选择，是产生式规则系统的核心决策组件。
负责条件匹配、冲突解决、规则选择和决策推理。
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime

from ..domain.entities import ProductionRule, GlobalState, DecisionResult, RuleSet
from ..domain.value_objects import DecisionType, MatchingConstants
from .language_model_service import LanguageModelService

logger = logging.getLogger(__name__)


class RuleMatchingService:
    """规则匹配服务 - 专注于语义匹配和规则选择"""
    
    def __init__(self, llm_service: LanguageModelService):
        """
        初始化规则匹配服务
        
        Args:
            llm_service: 语言模型服务
        """
        self.llm_service = llm_service
        
    def find_applicable_rules(self, 
                            global_state: GlobalState, 
                            rule_set: RuleSet) -> List[ProductionRule]:
        """
        查找适用的规则
        
        Args:
            global_state: 全局状态
            rule_set: 规则集
            
        Returns:
            List[ProductionRule]: 适用的规则列表，按优先级排序
        """
        try:
            logger.info("开始查找适用规则")
            applicable_rules = []
            
            for rule in rule_set.rules:
                try:
                    # 评估规则条件匹配度
                    is_match, confidence = self.evaluate_rule_conditions(rule, global_state)
                    
                    # 只有高置信度的匹配才认为是适用的
                    if is_match and confidence >= MatchingConstants.MEDIUM_CONFIDENCE_THRESHOLD:
                        applicable_rules.append(rule)
                        logger.debug(f"规则适用: {rule.name} (置信度: {confidence:.2f})")
                    
                except Exception as e:
                    logger.error(f"规则条件评估失败: {rule.id}, {e}")
                    continue
            
            # 按优先级排序（高优先级在前）
            applicable_rules.sort(key=lambda r: r.priority, reverse=True)
            
            logger.info(f"找到 {len(applicable_rules)} 个适用规则")
            return applicable_rules
            
        except Exception as e:
            logger.error(f"查找适用规则失败: {e}")
            return []
    
    def evaluate_rule_conditions(self, 
                                rule: ProductionRule, 
                                global_state: GlobalState) -> Tuple[bool, float]:
        """
        评估规则条件匹配度
        
        Args:
            rule: 要评估的规则
            global_state: 全局状态
            
        Returns:
            Tuple[bool, float]: (是否匹配, 置信度)
        """
        try:
            # 使用语言模型进行语义匹配
            matching_result = self.llm_service.semantic_match(
                rule.condition, 
                global_state.description
            )
            
            # 考虑上下文变量的影响
            context_boost = self._evaluate_context_relevance(rule, global_state)
            
            # 调整置信度
            adjusted_confidence = min(1.0, matching_result.confidence + context_boost)
            
            logger.debug(f"规则条件评估: {rule.name} -> {matching_result.is_match} "
                        f"(置信度: {adjusted_confidence:.2f})")
            
            return matching_result.is_match, adjusted_confidence
            
        except Exception as e:
            logger.error(f"规则条件评估失败: {e}")
            return False, 0.0
    
    def select_best_rule(self, 
                        applicable_rules: List[ProductionRule], 
                        global_state: GlobalState) -> DecisionResult:
        """
        选择最佳规则
        
        Args:
            applicable_rules: 适用的规则列表
            global_state: 全局状态
            
        Returns:
            DecisionResult: 决策结果
        """
        try:
            if not applicable_rules:
                # 没有适用规则，需要生成新规则
                return DecisionResult(
                    selected_rule=None,
                    decision_type=DecisionType.ADD_RULE,
                    confidence=0.8,
                    reasoning="当前状态没有找到适用的规则，需要生成新规则",
                    context={'state_description': global_state.description}
                )
            
            if len(applicable_rules) == 1:
                # 只有一个适用规则，直接选择
                selected_rule = applicable_rules[0]
                return DecisionResult(
                    selected_rule=selected_rule,
                    decision_type=DecisionType.EXECUTE_SELECTED_RULE,
                    confidence=0.9,
                    reasoning=f"只有一个适用规则: {selected_rule.name}",
                    alternative_rules=[]
                )
            
            # 多个适用规则，需要智能选择
            return self._select_from_multiple_rules(applicable_rules, global_state)
            
        except Exception as e:
            logger.error(f"规则选择失败: {e}")
            return DecisionResult(
                selected_rule=None,
                decision_type=DecisionType.ADD_RULE,
                confidence=0.3,
                reasoning=f"规则选择过程中发生错误: {str(e)}"
            )
    
    def resolve_conflicts(self, conflicting_rules: List[ProductionRule]) -> ProductionRule:
        """
        解决规则冲突
        
        Args:
            conflicting_rules: 冲突的规则列表
            
        Returns:
            ProductionRule: 解决冲突后选择的规则
        """
        try:
            if not conflicting_rules:
                raise ValueError("冲突规则列表不能为空")
            
            if len(conflicting_rules) == 1:
                return conflicting_rules[0]
            
            logger.info(f"解决 {len(conflicting_rules)} 个规则的冲突")
            
            # 优先级解决：选择优先级最高的规则
            highest_priority_rules = self._filter_by_highest_priority(conflicting_rules)
            
            if len(highest_priority_rules) == 1:
                selected_rule = highest_priority_rules[0]
                logger.info(f"通过优先级解决冲突，选择: {selected_rule.name}")
                return selected_rule
            
            # 如果优先级相同，使用其他策略
            return self._resolve_same_priority_conflict(highest_priority_rules)
            
        except Exception as e:
            logger.error(f"冲突解决失败: {e}")
            # 回退到选择第一个规则
            return conflicting_rules[0]
    
    def should_add_new_rules(self, 
                           execution_result: Any, 
                           global_state: GlobalState) -> bool:
        """
        判断是否需要添加新规则
        
        Args:
            execution_result: 执行结果
            global_state: 全局状态
            
        Returns:
            bool: 是否需要添加新规则
        """
        try:
            # 检查执行结果
            if hasattr(execution_result, 'success') and not execution_result.success:
                # 执行失败，可能需要新的恢复规则
                error_message = getattr(execution_result, 'error_details', '')
                if self._is_novel_error(error_message):
                    logger.info("检测到新型错误，需要生成恢复规则")
                    return True
            
            # 检查状态是否出现新情况
            if self._is_novel_state(global_state):
                logger.info("检测到新的状态情况，需要生成相应规则")
                return True
            
            # 检查是否达到迭代上限仍未完成目标
            if global_state.iteration_count > 50 and not global_state.goal_achieved:
                logger.info("迭代次数过多但目标未达成，需要策略调整规则")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"新规则需求判断失败: {e}")
            return False
    
    def _llm_match_condition_to_state(self, 
                                    condition: str, 
                                    state_description: str) -> Tuple[bool, float, str]:
        """
        LLM驱动的条件匹配
        
        Args:
            condition: 规则条件
            state_description: 状态描述
            
        Returns:
            Tuple[bool, float, str]: (是否匹配, 置信度, 推理)
        """
        try:
            matching_result = self.llm_service.semantic_match(condition, state_description)
            return (
                matching_result.is_match,
                matching_result.confidence,
                matching_result.reasoning
            )
        except Exception as e:
            logger.error(f"LLM条件匹配失败: {e}")
            return False, 0.0, f"匹配失败: {str(e)}"
    
    def _llm_compare_rule_relevance(self, 
                                  rules: List[ProductionRule], 
                                  state_description: str) -> List[Tuple[ProductionRule, float]]:
        """
        LLM驱动的规则相关性比较
        
        Args:
            rules: 规则列表
            state_description: 状态描述
            
        Returns:
            List[Tuple[ProductionRule, float]]: 规则和相关性分数的列表
        """
        try:
            rule_relevance = []
            
            for rule in rules:
                # 计算规则与当前状态的相关性
                relevance_score = self.llm_service.evaluate_semantic_similarity(
                    rule.condition, state_description
                )
                rule_relevance.append((rule, relevance_score))
            
            # 按相关性排序
            rule_relevance.sort(key=lambda x: x[1], reverse=True)
            
            return rule_relevance
            
        except Exception as e:
            logger.error(f"规则相关性比较失败: {e}")
            return [(rule, 0.5) for rule in rules]
    
    def _llm_explain_rule_selection(self, 
                                  selected_rule: ProductionRule, 
                                  state_description: str) -> str:
        """
        LLM驱动的规则选择解释
        
        Args:
            selected_rule: 选择的规则
            state_description: 状态描述
            
        Returns:
            str: 选择解释
        """
        try:
            prompt = f"""
请解释为什么在当前状态下选择了这个规则：

当前状态: {state_description}

选择的规则:
- 名称: {selected_rule.name}
- 条件: {selected_rule.condition}
- 动作: {selected_rule.action}
- 优先级: {selected_rule.priority}

请提供清晰、逻辑性强的解释，说明选择的理由。
"""
            
            explanation = self.llm_service.generate_natural_language_response(prompt)
            return explanation
            
        except Exception as e:
            logger.error(f"规则选择解释失败: {e}")
            return f"选择规则 {selected_rule.name}，因为它的条件与当前状态最匹配"
    
    def _evaluate_context_relevance(self, 
                                   rule: ProductionRule, 
                                   global_state: GlobalState) -> float:
        """
        评估上下文相关性
        
        Args:
            rule: 规则
            global_state: 全局状态
            
        Returns:
            float: 上下文相关性提升分数（0.0-0.2）
        """
        boost = 0.0
        
        try:
            # 检查规则是否与当前阶段匹配
            context_phase = global_state.context_variables.get('current_phase')
            if context_phase and str(rule.phase.value) == str(context_phase):
                boost += 0.1
            
            # 检查是否有相关的上下文变量
            for key, value in global_state.context_variables.items():
                if isinstance(value, str) and len(value) > 0:
                    # 简单的关键词匹配
                    if any(word in rule.condition.lower() 
                          for word in value.lower().split()[:5]):  # 只检查前5个词
                        boost += 0.05
                        break
            
            # 检查执行历史相关性
            if len(global_state.execution_history) > 0:
                recent_history = global_state.execution_history[-3:]  # 最近3条历史
                for history_entry in recent_history:
                    if any(word in rule.condition.lower() 
                          for word in history_entry.lower().split()[:10]):
                        boost += 0.03
                        break
            
            return min(0.2, boost)  # 最大提升0.2
            
        except Exception as e:
            logger.error(f"上下文相关性评估失败: {e}")
            return 0.0
    
    def _select_from_multiple_rules(self, 
                                  applicable_rules: List[ProductionRule], 
                                  global_state: GlobalState) -> DecisionResult:
        """
        从多个适用规则中选择最佳规则
        
        Args:
            applicable_rules: 适用的规则列表
            global_state: 全局状态
            
        Returns:
            DecisionResult: 决策结果
        """
        try:
            # 使用LLM比较规则相关性
            rule_relevance = self._llm_compare_rule_relevance(
                applicable_rules, global_state.description
            )
            
            # 选择最相关的规则
            best_rule, relevance_score = rule_relevance[0]
            
            # 生成选择解释
            reasoning = self._llm_explain_rule_selection(best_rule, global_state.description)
            
            # 准备备选规则
            alternative_rules = [rule for rule, _ in rule_relevance[1:3]]  # 最多3个备选
            
            # 计算置信度
            confidence = min(0.95, 0.7 + relevance_score * 0.25)
            
            return DecisionResult(
                selected_rule=best_rule,
                decision_type=DecisionType.EXECUTE_SELECTED_RULE,
                confidence=confidence,
                reasoning=reasoning,
                alternative_rules=alternative_rules,
                context={
                    'total_applicable_rules': len(applicable_rules),
                    'relevance_score': relevance_score,
                    'selection_method': 'llm_relevance_comparison'
                }
            )
            
        except Exception as e:
            logger.error(f"多规则选择失败: {e}")
            # 回退到简单的优先级选择
            best_rule = applicable_rules[0]  # 已经按优先级排序
            return DecisionResult(
                selected_rule=best_rule,
                decision_type=DecisionType.EXECUTE_SELECTED_RULE,
                confidence=0.6,
                reasoning=f"选择最高优先级规则: {best_rule.name}",
                alternative_rules=applicable_rules[1:3]
            )
    
    def _filter_by_highest_priority(self, rules: List[ProductionRule]) -> List[ProductionRule]:
        """
        过滤出最高优先级的规则
        
        Args:
            rules: 规则列表
            
        Returns:
            List[ProductionRule]: 最高优先级的规则列表
        """
        if not rules:
            return []
        
        max_priority = max(rule.priority for rule in rules)
        return [rule for rule in rules if rule.priority == max_priority]
    
    def _resolve_same_priority_conflict(self, rules: List[ProductionRule]) -> ProductionRule:
        """
        解决相同优先级的规则冲突
        
        Args:
            rules: 相同优先级的规则列表
            
        Returns:
            ProductionRule: 选择的规则
        """
        try:
            # 策略1: 选择最近创建的规则
            newest_rule = max(rules, key=lambda r: r.created_at)
            
            logger.info(f"通过创建时间解决冲突，选择最新规则: {newest_rule.name}")
            return newest_rule
            
        except Exception as e:
            logger.error(f"相同优先级冲突解决失败: {e}")
            return rules[0]
    
    def _is_novel_error(self, error_message: str) -> bool:
        """
        判断是否为新型错误
        
        Args:
            error_message: 错误消息
            
        Returns:
            bool: 是否为新型错误
        """
        if not error_message:
            return False
        
        # 简单的新型错误检测逻辑
        # 实际实现可以更复杂，比如维护已知错误的数据库
        
        common_errors = [
            'network', 'connection', 'timeout', 'permission', 'access',
            'file not found', 'directory', 'syntax error', 'import error'
        ]
        
        error_lower = error_message.lower()
        
        # 如果错误消息包含常见错误关键词，认为不是新型错误
        for common_error in common_errors:
            if common_error in error_lower:
                return False
        
        # 如果错误消息很长且包含特殊字符，可能是新型错误
        if len(error_message) > 100 and any(char in error_message for char in ['[', ']', '{', '}']):
            return True
        
        return False
    
    def _is_novel_state(self, global_state: GlobalState) -> bool:
        """
        判断是否为新型状态
        
        Args:
            global_state: 全局状态
            
        Returns:
            bool: 是否为新型状态
        """
        try:
            # 检查状态描述的复杂性
            state_desc = global_state.description
            
            # 如果状态描述包含"未知"、"新的"、"意外"等词汇
            novel_indicators = ['未知', '新的', '意外', '异常', '预期之外', 'unknown', 'unexpected', 'novel']
            
            state_lower = state_desc.lower()
            for indicator in novel_indicators:
                if indicator in state_lower:
                    return True
            
            # 检查上下文变量是否包含异常值
            context_vars = global_state.context_variables
            
            # 如果有"error_count"且数值较高
            error_count = context_vars.get('error_count', 0)
            if isinstance(error_count, (int, float)) and error_count > 3:
                return True
            
            # 如果迭代次数很多但进展有限
            if global_state.iteration_count > 20:
                progress_indicators = ['完成', '成功', '达成', 'completed', 'success', 'achieved']
                if not any(indicator in state_lower for indicator in progress_indicators):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"新型状态判断失败: {e}")
            return False