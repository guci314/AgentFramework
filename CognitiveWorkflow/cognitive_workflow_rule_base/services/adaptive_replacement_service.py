# -*- coding: utf-8 -*-
"""
自适应规则替换服务

实现智能的规则替换策略，根据当前系统状态动态选择最优的替换方案。
支持多种替换策略，包括情境感知、性能导向和自主学习能力。
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime

from ..domain.entities import ProductionRule, RuleSet, GlobalState
from ..domain.value_objects import (
    RulePhase, ReplacementStrategyType, SituationScore, ReplacementStrategy, 
    StrategyEffectiveness, ExecutionMetrics, AdaptiveReplacementConstants,
    SituationContext
)
from .language_model_service import LanguageModelService
from .strategy_effectiveness_tracker import StrategyEffectivenessTracker

logger = logging.getLogger(__name__)


class AdaptiveReplacementService:
    """自适应规则替换服务 - 核心智能替换引擎"""
    
    def __init__(self, llm_service: LanguageModelService, enable_effectiveness_tracking: bool = True):
        """
        初始化自适应替换服务
        
        Args:
            llm_service: 语言模型服务，用于语义分析和决策支持
            enable_effectiveness_tracking: 是否启用策略效果跟踪
        """
        self.llm_service = llm_service
        self.strategy_history: List[StrategyEffectiveness] = []
        self.replacement_config = self._load_default_config()
        
        # 集成策略效果跟踪器
        self.effectiveness_tracker = StrategyEffectivenessTracker() if enable_effectiveness_tracking else None
        
    def execute_adaptive_replacement(self, 
                                   existing_rules: List[ProductionRule],
                                   new_rules: List[ProductionRule],
                                   global_state: GlobalState,
                                   context: Dict[str, Any]) -> List[ProductionRule]:
        """
        执行自适应规则替换
        
        Args:
            existing_rules: 现有规则列表
            new_rules: 新生成的规则列表
            global_state: 当前全局状态
            context: 执行上下文信息
            
        Returns:
            List[ProductionRule]: 优化后的规则列表
        """
        try:
            logger.info(f"开始自适应规则替换: 现有规则{len(existing_rules)}个, 新规则{len(new_rules)}个")
            
            # 1. 评估当前情境
            situation_score = self._assess_current_situation(
                existing_rules, global_state, context
            )
            
            # 2. 选择最优替换策略（集成历史学习）
            selected_strategy = self._select_optimal_strategy(situation_score, context)
            
            # 3. 执行规则替换
            optimized_rules = self._execute_replacement_strategy(
                existing_rules, new_rules, selected_strategy, situation_score
            )
            
            # 4. 记录策略应用效果（用于后续学习）
            self._record_strategy_effectiveness(
                selected_strategy, situation_score, existing_rules, optimized_rules, context
            )
            
            logger.info(f"自适应替换完成: {selected_strategy.strategy_type.value}, "
                       f"规则数量: {len(existing_rules)} -> {len(optimized_rules)}")
            
            return optimized_rules
            
        except Exception as e:
            logger.error(f"自适应替换失败: {e}")
            # 失败时返回保守的合并结果
            return self._conservative_merge(existing_rules, new_rules)
    
    def _assess_current_situation(self, 
                                rules: List[ProductionRule], 
                                global_state: GlobalState,
                                context: Dict[str, Any]) -> SituationScore:
        """
        评估当前系统情境
        
        Args:
            rules: 当前规则列表
            global_state: 全局状态
            context: 执行上下文
            
        Returns:
            SituationScore: 情境评估分数
        """
        try:
            # 计算规则密度 (规则数量相对于目标复杂度)
            goal_complexity = self._estimate_goal_complexity(context.get('goal', ''))
            rule_density = len(rules) / max(goal_complexity * 2, 5)  # 理想规则数为复杂度*2
            rule_density = min(1.0, rule_density)
            
            # 计算执行效率 (基于历史执行数据)
            execution_efficiency = self._calculate_execution_efficiency(global_state)
            
            # 计算目标进度 (基于迭代次数和状态分析)
            goal_progress = self._estimate_goal_progress(global_state, context)
            
            # 计算失败频率 (最近执行的失败率)
            failure_frequency = self._calculate_failure_frequency(global_state)
            
            # 计算智能体利用率 (智能体分工均衡度)
            agent_utilization = self._calculate_agent_utilization(rules)
            
            # 计算阶段分布不平衡度
            phase_distribution = self._calculate_phase_imbalance(rules)
            
            situation_score = SituationScore(
                rule_density=rule_density,
                execution_efficiency=execution_efficiency,
                goal_progress=goal_progress,
                failure_frequency=failure_frequency,
                agent_utilization=agent_utilization,
                phase_distribution=phase_distribution
            )
            
            logger.debug(f"情境评估完成: 健康度={situation_score.get_overall_health():.2f}, "
                        f"关键问题={situation_score.get_critical_issues()}")
            
            return situation_score
            
        except Exception as e:
            logger.error(f"情境评估失败: {e}")
            # 返回中性评估结果
            return SituationScore(0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
    
    def _select_optimal_strategy(self, 
                               situation_score: SituationScore,
                               context: Dict[str, Any]) -> ReplacementStrategy:
        """
        选择最优替换策略（集成历史学习）
        
        Args:
            situation_score: 情境评估分数
            context: 执行上下文
            
        Returns:
            ReplacementStrategy: 选择的替换策略
        """
        try:
            # 如果有效果跟踪器，优先使用历史学习数据
            if self.effectiveness_tracker:
                recommended_strategy, confidence = self.effectiveness_tracker.recommend_optimal_strategy(
                    situation_score, context
                )
                
                # 如果推荐置信度足够高，使用推荐策略
                if confidence > 0.7:
                    logger.info(f"使用历史学习推荐策略: {recommended_strategy.value} (置信度: {confidence:.2f})")
                    return self._generate_strategy_config(recommended_strategy, situation_score)
                else:
                    logger.info(f"历史推荐置信度较低 ({confidence:.2f})，使用传统策略选择")
            
            # 传统策略选择方法：基于情境评估选择策略类型
            strategy_type = self._determine_strategy_type(situation_score, context)
            
            # 根据策略类型生成具体配置
            strategy_config = self._generate_strategy_config(strategy_type, situation_score)
            
            # 使用LLM验证策略合理性（如果启用）
            if self.replacement_config.get('enable_llm_analysis', True):
                validated_strategy = self._validate_strategy_with_llm(
                    strategy_config, situation_score, context
                )
                if validated_strategy:
                    strategy_config = validated_strategy
            
            logger.info(f"选择替换策略: {strategy_type.value} - {strategy_config.get_strategy_description()}")
            
            return strategy_config
            
        except Exception as e:
            logger.error(f"策略选择失败: {e}")
            # 默认返回保守策略
            return self._get_default_strategy()
    
    def _validate_strategy_with_llm(self, 
                                  strategy: ReplacementStrategy,
                                  situation_score: SituationScore,
                                  context: Dict[str, Any]) -> Optional[ReplacementStrategy]:
        """
        使用LLM验证和优化策略选择
        
        Args:
            strategy: 初步选择的策略
            situation_score: 当前情境评估
            context: 执行上下文
            
        Returns:
            Optional[ReplacementStrategy]: 验证后的策略（如果验证失败返回None）
        """
        try:
            validation_prompt = f"""
你是一个专业的策略评估专家。请评估以下自适应规则替换策略的合理性，并提供优化建议。

## 当前情境分析
- 规则密度: {situation_score.rule_density:.2f} (0=稀少, 1=过密)
- 执行效率: {situation_score.execution_efficiency:.2f} (0=低效, 1=高效)
- 目标进度: {situation_score.goal_progress:.2f} (0=停滞, 1=完成)
- 失败频率: {situation_score.failure_frequency:.2f} (0=无失败, 1=频繁失败)
- 智能体利用率: {situation_score.agent_utilization:.2f} (0=不均衡, 1=均衡)
- 阶段分布: {situation_score.phase_distribution:.2f} (0=均衡, 1=不均衡)
- 整体健康度: {situation_score.get_overall_health():.2f}
- 关键问题: {situation_score.get_critical_issues()}

## 执行上下文
- 目标: {context.get('goal', '未知')}
- 迭代次数: {context.get('iteration_count', 0)}
- 上下文类型: {context.get('context_type', '未知')}

## 当前选择的策略
- 策略类型: {strategy.strategy_type.value}
- 策略描述: {strategy.get_strategy_description()}
- 替换比例: {strategy.replacement_ratio:.2f}
- 相似性阈值: {strategy.similarity_threshold:.2f}
- 性能阈值: {strategy.performance_threshold:.2f}
- 保守模式: {strategy.conservative_mode}
- 每阶段最大规则数: {strategy.max_rules_per_phase}
- 每智能体最大规则数: {strategy.max_rules_per_agent}

## 评估要求
请从以下角度评估策略合理性：

1. **情境匹配度**: 策略是否适合当前系统状态？
2. **风险评估**: 策略执行可能带来的风险？
3. **效果预期**: 策略预期能解决哪些问题？
4. **参数合理性**: 策略参数设置是否合理？

## 输出格式
请严格按照以下JSON格式返回评估结果：

```json
{{
    "validation_result": "approved/rejected/modified",
    "confidence": 置信度分数(0.0-1.0),
    "risk_level": "low/medium/high",
    "expected_improvement": 预期改进度(0.0-1.0),
    "recommended_adjustments": {{
        "replacement_ratio": 建议的替换比例(可选),
        "similarity_threshold": 建议的相似性阈值(可选),
        "performance_threshold": 建议的性能阈值(可选),
        "conservative_mode": 建议的保守模式(可选),
        "max_rules_per_phase": 建议的每阶段最大规则数(可选),
        "max_rules_per_agent": 建议的每智能体最大规则数(可选)
    }},
    "reasoning": "详细的评估理由和建议",
    "alternative_strategy": "如果当前策略不合适，推荐的替代策略类型(可选)"
}}
```

请基于专业判断给出准确的评估。
"""

            response = self.llm_service.generate_natural_language_response(validation_prompt)
            validation_result = self.llm_service._parse_json_response(response)
            
            if not validation_result:
                logger.warning("LLM策略验证返回空结果")
                return None
            
            result_type = validation_result.get('validation_result', 'rejected')
            confidence = validation_result.get('confidence', 0.0)
            reasoning = validation_result.get('reasoning', '无理由')
            
            logger.info(f"LLM策略验证: {result_type} (置信度: {confidence:.2f})")
            logger.debug(f"验证理由: {reasoning}")
            
            if result_type == 'approved' and confidence > 0.7:
                # 策略通过验证
                return strategy
                
            elif result_type == 'modified' and confidence > 0.6:
                # 策略需要调整
                adjustments = validation_result.get('recommended_adjustments', {})
                if adjustments:
                    modified_strategy = self._apply_strategy_adjustments(strategy, adjustments)
                    logger.info(f"策略已根据LLM建议调整: {adjustments}")
                    return modified_strategy
                else:
                    return strategy
                    
            elif result_type == 'rejected':
                # 策略被拒绝，尝试使用替代策略
                alternative = validation_result.get('alternative_strategy')
                if alternative:
                    logger.warning(f"当前策略被拒绝，尝试替代策略: {alternative}")
                    try:
                        alt_strategy_type = ReplacementStrategyType(alternative)
                        return self._generate_strategy_config(alt_strategy_type, situation_score)
                    except ValueError:
                        logger.error(f"无效的替代策略类型: {alternative}")
                        return None
                else:
                    logger.warning("策略被拒绝且无替代方案")
                    return None
            else:
                logger.warning(f"LLM验证结果置信度过低: {confidence:.2f}")
                return None
                
        except Exception as e:
            logger.error(f"LLM策略验证失败: {e}")
            return None
    
    def _apply_strategy_adjustments(self, 
                                  original_strategy: ReplacementStrategy,
                                  adjustments: Dict[str, Any]) -> ReplacementStrategy:
        """
        应用LLM建议的策略调整
        
        Args:
            original_strategy: 原始策略
            adjustments: 调整建议
            
        Returns:
            ReplacementStrategy: 调整后的策略
        """
        try:
            # 创建调整后的策略配置
            updated_config = {
                'strategy_type': original_strategy.strategy_type,
                'replacement_ratio': adjustments.get('replacement_ratio', original_strategy.replacement_ratio),
                'similarity_threshold': adjustments.get('similarity_threshold', original_strategy.similarity_threshold),
                'performance_threshold': adjustments.get('performance_threshold', original_strategy.performance_threshold),
                'priority_adjustment': original_strategy.priority_adjustment,
                'conservative_mode': adjustments.get('conservative_mode', original_strategy.conservative_mode),
                'max_rules_per_phase': adjustments.get('max_rules_per_phase', original_strategy.max_rules_per_phase),
                'max_rules_per_agent': adjustments.get('max_rules_per_agent', original_strategy.max_rules_per_agent)
            }
            
            # 验证调整后的参数范围
            updated_config['replacement_ratio'] = max(0.1, min(0.8, float(updated_config['replacement_ratio'])))
            updated_config['similarity_threshold'] = max(0.0, min(1.0, float(updated_config['similarity_threshold'])))
            updated_config['performance_threshold'] = max(0.0, min(1.0, float(updated_config['performance_threshold'])))
            updated_config['max_rules_per_phase'] = max(1, min(10, int(updated_config['max_rules_per_phase'])))
            updated_config['max_rules_per_agent'] = max(1, min(10, int(updated_config['max_rules_per_agent'])))
            
            return ReplacementStrategy(
                strategy_type=updated_config['strategy_type'],
                replacement_ratio=updated_config['replacement_ratio'],
                similarity_threshold=updated_config['similarity_threshold'],
                performance_threshold=updated_config['performance_threshold'],
                priority_adjustment=updated_config['priority_adjustment'],
                conservative_mode=updated_config['conservative_mode'],
                max_rules_per_phase=updated_config['max_rules_per_phase'],
                max_rules_per_agent=updated_config['max_rules_per_agent']
            )
            
        except Exception as e:
            logger.error(f"应用策略调整失败: {e}")
            return original_strategy
    
    def _determine_strategy_type(self, 
                               situation_score: SituationScore,
                               context: Dict[str, Any]) -> ReplacementStrategyType:
        """
        确定策略类型
        
        Args:
            situation_score: 情境评估分数
            context: 执行上下文
            
        Returns:
            ReplacementStrategyType: 策略类型
        """
        iteration_count = context.get('iteration_count', 0)
        
        # 紧急情况：失败频率过高
        if situation_score.failure_frequency > AdaptiveReplacementConstants.HIGH_FAILURE_FREQUENCY_THRESHOLD:
            return ReplacementStrategyType.EMERGENCY_REPLACEMENT
        
        # 规则冗余：规则密度过高
        if situation_score.rule_density > AdaptiveReplacementConstants.HIGH_RULE_DENSITY_THRESHOLD:
            return ReplacementStrategyType.AGGRESSIVE_CLEANUP
        
        # 目标偏离：进度停滞且迭代次数较多
        if (situation_score.goal_progress < AdaptiveReplacementConstants.STALLED_PROGRESS_THRESHOLD and 
            iteration_count > 5):
            return ReplacementStrategyType.STRATEGIC_PIVOT
        
        # 智能体不平衡
        if situation_score.agent_utilization < AdaptiveReplacementConstants.LOW_AGENT_UTILIZATION_THRESHOLD:
            return ReplacementStrategyType.AGENT_REBALANCING
        
        # 阶段分布不平衡
        if situation_score.phase_distribution > AdaptiveReplacementConstants.UNBALANCED_PHASE_DISTRIBUTION_THRESHOLD:
            return ReplacementStrategyType.PHASE_OPTIMIZATION
        
        # 执行效率低下
        if situation_score.execution_efficiency < AdaptiveReplacementConstants.LOW_EXECUTION_EFFICIENCY_THRESHOLD:
            return ReplacementStrategyType.PERFORMANCE_FOCUSED
        
        # 启动阶段：规则较少
        if len(context.get('existing_rules', [])) < 3:
            return ReplacementStrategyType.MINIMAL_REPLACEMENT
        
        # 默认：渐进改进
        return ReplacementStrategyType.INCREMENTAL_IMPROVEMENT
    
    def _generate_strategy_config(self, 
                                strategy_type: ReplacementStrategyType,
                                situation_score: SituationScore) -> ReplacementStrategy:
        """
        生成策略配置
        
        Args:
            strategy_type: 策略类型
            situation_score: 情境评估分数
            
        Returns:
            ReplacementStrategy: 策略配置
        """
        config_map = {
            ReplacementStrategyType.MINIMAL_REPLACEMENT: {
                'replacement_ratio': 0.1,
                'similarity_threshold': 0.9,
                'performance_threshold': 0.8,
                'priority_adjustment': False,
                'conservative_mode': True,
                'max_rules_per_phase': 5,
                'max_rules_per_agent': 6
            },
            ReplacementStrategyType.PERFORMANCE_FOCUSED: {
                'replacement_ratio': 0.4,
                'similarity_threshold': 0.7,
                'performance_threshold': 0.7,
                'priority_adjustment': True,
                'conservative_mode': False,
                'max_rules_per_phase': 4,
                'max_rules_per_agent': 5
            },
            ReplacementStrategyType.AGGRESSIVE_CLEANUP: {
                'replacement_ratio': 0.6,
                'similarity_threshold': 0.8,
                'performance_threshold': 0.6,
                'priority_adjustment': True,
                'conservative_mode': False,
                'max_rules_per_phase': 3,
                'max_rules_per_agent': 4
            },
            ReplacementStrategyType.INCREMENTAL_IMPROVEMENT: {
                'replacement_ratio': 0.2,
                'similarity_threshold': 0.8,
                'performance_threshold': 0.7,
                'priority_adjustment': False,
                'conservative_mode': True,
                'max_rules_per_phase': 4,
                'max_rules_per_agent': 5
            },
            ReplacementStrategyType.EMERGENCY_REPLACEMENT: {
                'replacement_ratio': 0.7,
                'similarity_threshold': 0.6,
                'performance_threshold': 0.5,
                'priority_adjustment': True,
                'conservative_mode': False,
                'max_rules_per_phase': 4,
                'max_rules_per_agent': 5
            },
            ReplacementStrategyType.STRATEGIC_PIVOT: {
                'replacement_ratio': 0.8,
                'similarity_threshold': 0.5,
                'performance_threshold': 0.4,
                'priority_adjustment': True,
                'conservative_mode': False,
                'max_rules_per_phase': 3,
                'max_rules_per_agent': 4
            },
            ReplacementStrategyType.AGENT_REBALANCING: {
                'replacement_ratio': 0.5,
                'similarity_threshold': 0.7,
                'performance_threshold': 0.6,
                'priority_adjustment': True,
                'conservative_mode': False,
                'max_rules_per_phase': 4,
                'max_rules_per_agent': 3  # 限制单个智能体规则数
            },
            ReplacementStrategyType.PHASE_OPTIMIZATION: {
                'replacement_ratio': 0.4,
                'similarity_threshold': 0.8,
                'performance_threshold': 0.7,
                'priority_adjustment': True,
                'conservative_mode': False,
                'max_rules_per_phase': 3,  # 严格限制每阶段规则数
                'max_rules_per_agent': 5
            }
        }
        
        config = config_map.get(strategy_type, config_map[ReplacementStrategyType.INCREMENTAL_IMPROVEMENT])
        
        return ReplacementStrategy(
            strategy_type=strategy_type,
            replacement_ratio=config['replacement_ratio'],
            similarity_threshold=config['similarity_threshold'],
            performance_threshold=config['performance_threshold'],
            priority_adjustment=config['priority_adjustment'],
            conservative_mode=config['conservative_mode'],
            max_rules_per_phase=config['max_rules_per_phase'],
            max_rules_per_agent=config['max_rules_per_agent']
        )
    
    def _execute_replacement_strategy(self,
                                    existing_rules: List[ProductionRule],
                                    new_rules: List[ProductionRule],
                                    strategy: ReplacementStrategy,
                                    situation_score: SituationScore) -> List[ProductionRule]:
        """
        执行替换策略
        
        Args:
            existing_rules: 现有规则
            new_rules: 新规则
            strategy: 替换策略
            situation_score: 情境评估
            
        Returns:
            List[ProductionRule]: 优化后的规则列表
        """
        try:
            # 1. 分析规则特征
            rule_analysis = self._analyze_rule_characteristics(existing_rules + new_rules)
            
            # 2. 找到替换候选项
            replacement_candidates = self._find_replacement_candidates(
                existing_rules, new_rules, strategy
            )
            
            # 3. 执行智能替换
            optimized_rules = self._perform_intelligent_replacement(
                existing_rules, new_rules, replacement_candidates, strategy
            )
            
            # 4. 应用数量约束
            final_rules = self._apply_quantity_constraints(optimized_rules, strategy)
            
            return final_rules
            
        except Exception as e:
            logger.error(f"执行替换策略失败: {e}")
            return self._conservative_merge(existing_rules, new_rules)
    
    # 辅助方法实现
    def _estimate_goal_complexity(self, goal: str) -> float:
        """估算目标复杂度"""
        if not goal:
            return 3.0
        
        # 简单的复杂度估算：基于目标长度和关键词
        complexity_indicators = ['实现', '测试', '文档', '部署', '优化', '分析']
        base_complexity = len(goal) / 50  # 基础复杂度
        keyword_complexity = sum(1 for keyword in complexity_indicators if keyword in goal)
        
        return max(2.0, min(8.0, base_complexity + keyword_complexity))
    
    def _calculate_execution_efficiency(self, global_state: GlobalState) -> float:
        """计算执行效率"""
        history = global_state.execution_history
        if not history or len(history) < 2:
            return 0.5  # 默认中等效率
        
        # 分析最近的执行历史
        recent_history = history[-5:]  # 最近5次执行
        success_count = sum(1 for entry in recent_history if '成功' in entry or 'success' in entry.lower())
        
        return success_count / len(recent_history)
    
    def _estimate_goal_progress(self, global_state: GlobalState, context: Dict[str, Any]) -> float:
        """估算目标进度"""
        # 基于迭代次数和状态变化估算进度
        iteration_count = global_state.iteration_count
        max_iterations = context.get('max_iterations', 20)
        
        # 基础进度：基于迭代比例
        base_progress = min(0.8, iteration_count / max_iterations)
        
        # 状态分析调整
        if global_state.goal_achieved:
            return 1.0
        
        # 基于执行历史的进度调整
        if global_state.execution_history:
            recent_progress_indicators = sum(
                1 for entry in global_state.execution_history[-3:]
                if any(keyword in entry for keyword in ['完成', '成功', '达成', 'completed'])
            )
            progress_adjustment = recent_progress_indicators * 0.1
            base_progress += progress_adjustment
        
        return max(0.0, min(1.0, base_progress))
    
    def _calculate_failure_frequency(self, global_state: GlobalState) -> float:
        """计算失败频率"""
        history = global_state.execution_history
        if not history:
            return 0.0
        
        recent_history = history[-10:]  # 最近10次执行
        failure_count = sum(
            1 for entry in recent_history 
            if any(keyword in entry for keyword in ['失败', '错误', 'failed', 'error'])
        )
        
        return failure_count / len(recent_history)
    
    def _calculate_agent_utilization(self, rules: List[ProductionRule]) -> float:
        """计算智能体利用率"""
        if not rules:
            return 0.0
        
        # 统计每个智能体的规则数量
        agent_counts = {}
        for rule in rules:
            agent_name = rule.agent_name
            agent_counts[agent_name] = agent_counts.get(agent_name, 0) + 1
        
        if not agent_counts:
            return 0.0
        
        # 计算分布的均衡度
        total_agents = len(agent_counts)
        avg_rules_per_agent = len(rules) / total_agents
        
        # 计算方差，方差越小说明分布越均匀
        variance = sum((count - avg_rules_per_agent) ** 2 for count in agent_counts.values()) / total_agents
        
        # 将方差转换为利用率分数 (方差越小，利用率越高)
        max_possible_variance = (avg_rules_per_agent) ** 2
        normalized_variance = variance / max(max_possible_variance, 1)
        utilization = 1.0 - min(1.0, normalized_variance)
        
        return utilization
    
    def _calculate_phase_imbalance(self, rules: List[ProductionRule]) -> float:
        """计算阶段分布不平衡度"""
        if not rules:
            return 0.0
        
        # 统计每个阶段的规则数量
        phase_counts = {phase: 0 for phase in RulePhase}
        for rule in rules:
            phase_counts[rule.phase] = phase_counts.get(rule.phase, 0) + 1
        
        total_rules = len(rules)
        ideal_per_phase = total_rules / len(RulePhase)
        
        # 计算不平衡度：各阶段与理想分布的偏差
        imbalance = sum(
            abs(count - ideal_per_phase) for count in phase_counts.values()
        ) / (total_rules * 2)  # 归一化到0-1
        
        return min(1.0, imbalance)
    
    def _analyze_rule_characteristics(self, rules: List[ProductionRule]) -> Dict[str, Any]:
        """分析规则特征"""
        if not rules:
            return {}
        
        return {
            'total_count': len(rules),
            'phase_distribution': self._get_phase_distribution(rules),
            'agent_distribution': self._get_agent_distribution(rules),
            'priority_distribution': self._get_priority_distribution(rules)
        }
    
    def _get_phase_distribution(self, rules: List[ProductionRule]) -> Dict[str, int]:
        """获取阶段分布"""
        distribution = {}
        for rule in rules:
            phase = rule.phase.value
            distribution[phase] = distribution.get(phase, 0) + 1
        return distribution
    
    def _get_agent_distribution(self, rules: List[ProductionRule]) -> Dict[str, int]:
        """获取智能体分布"""
        distribution = {}
        for rule in rules:
            agent = rule.agent_name
            distribution[agent] = distribution.get(agent, 0) + 1
        return distribution
    
    def _get_priority_distribution(self, rules: List[ProductionRule]) -> Dict[str, int]:
        """获取优先级分布"""
        distribution = {'high': 0, 'medium': 0, 'low': 0}
        for rule in rules:
            if rule.priority >= 80:
                distribution['high'] += 1
            elif rule.priority >= 60:
                distribution['medium'] += 1
            else:
                distribution['low'] += 1
        return distribution
    
    def _find_replacement_candidates(self,
                                   existing_rules: List[ProductionRule],
                                   new_rules: List[ProductionRule],
                                   strategy: ReplacementStrategy) -> List[Tuple[ProductionRule, ProductionRule, float]]:
        """
        找到替换候选项
        
        Returns:
            List[Tuple[ProductionRule, ProductionRule, float]]: (现有规则, 新规则, 替换分数)
        """
        candidates = []
        
        for new_rule in new_rules:
            for existing_rule in existing_rules:
                # 计算替换分数
                replacement_score = self._calculate_replacement_score(
                    existing_rule, new_rule, strategy
                )
                
                if replacement_score > 0.3:  # 只考虑有意义的替换
                    candidates.append((existing_rule, new_rule, replacement_score))
        
        # 按替换分数排序
        candidates.sort(key=lambda x: x[2], reverse=True)
        return candidates
    
    def _calculate_replacement_score(self,
                                   existing_rule: ProductionRule,
                                   new_rule: ProductionRule,
                                   strategy: ReplacementStrategy) -> float:
        """计算替换分数"""
        score = 0.0
        
        # 1. 相似性分数 (0.4权重)
        similarity = self._calculate_semantic_similarity(existing_rule, new_rule)
        if similarity >= strategy.similarity_threshold:
            score += 0.4 * similarity
        
        # 2. 性能预期分数 (0.3权重)
        if new_rule.priority > existing_rule.priority:
            score += 0.3
        
        # 3. 阶段匹配分数 (0.2权重)
        if new_rule.phase == existing_rule.phase:
            score += 0.2
        
        # 4. 智能体匹配分数 (0.1权重)
        if new_rule.agent_name == existing_rule.agent_name:
            score += 0.1
        
        return score
    
    def _calculate_semantic_similarity(self, rule1: ProductionRule, rule2: ProductionRule) -> float:
        """计算语义相似度（LLM增强版本）"""
        try:
            # 使用LLM进行深度语义分析
            if self.replacement_config.get('enable_llm_analysis', True):
                return self._llm_semantic_similarity(rule1, rule2)
            else:
                return self._simple_text_similarity(rule1, rule2)
        except Exception as e:
            logger.warning(f"LLM语义分析失败，回退到简单方法: {e}")
            return self._simple_text_similarity(rule1, rule2)
    
    def _llm_semantic_similarity(self, rule1: ProductionRule, rule2: ProductionRule) -> float:
        """使用LLM计算语义相似度"""
        similarity_prompt = f"""
你是一个专业的规则语义分析专家。请分析以下两个产生式规则的语义相似度。

## 规则1
名称: {rule1.name}
条件: {rule1.condition}
动作: {rule1.action}
智能体: {rule1.agent_name}
阶段: {rule1.phase.value}

## 规则2  
名称: {rule2.name}
条件: {rule2.condition}
动作: {rule2.action}
智能体: {rule2.agent_name}
阶段: {rule2.phase.value}

## 分析要求
请从以下维度分析两个规则的相似度：

1. **功能相似度**: 两个规则要解决的问题是否相似？
2. **执行相似度**: 两个规则的具体执行动作是否相似？
3. **上下文相似度**: 两个规则的触发条件和执行环境是否相似？
4. **语义重叠度**: 两个规则在语言表达上的重叠程度？

## 输出格式
请严格按照以下JSON格式返回分析结果：

```json
{{
    "overall_similarity": 相似度分数(0.0-1.0的浮点数),
    "functional_similarity": 功能相似度(0.0-1.0),
    "execution_similarity": 执行相似度(0.0-1.0),
    "context_similarity": 上下文相似度(0.0-1.0),
    "semantic_overlap": 语义重叠度(0.0-1.0),
    "replacement_recommendation": "是否推荐替换(recommended/not_recommended/conditional)",
    "reasoning": "详细的分析理由"
}}
```

请确保相似度分数准确反映两个规则的实际关系。
"""

        try:
            response = self.llm_service.generate_natural_language_response(similarity_prompt)
            analysis_result = self.llm_service._parse_json_response(response)
            
            if analysis_result and 'overall_similarity' in analysis_result:
                similarity_score = float(analysis_result['overall_similarity'])
                logger.debug(f"LLM语义分析: {rule1.name} vs {rule2.name} = {similarity_score:.2f}")
                logger.debug(f"分析理由: {analysis_result.get('reasoning', '无')}")
                
                return max(0.0, min(1.0, similarity_score))  # 确保在有效范围内
            else:
                logger.warning("LLM返回格式不正确，使用简单方法")
                return self._simple_text_similarity(rule1, rule2)
                
        except Exception as e:
            logger.error(f"LLM语义分析失败: {e}")
            return self._simple_text_similarity(rule1, rule2)
    
    def _simple_text_similarity(self, rule1: ProductionRule, rule2: ProductionRule) -> float:
        """简单的文本相似度计算（后备方案）"""
        def text_similarity(text1: str, text2: str) -> float:
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            if not words1 or not words2:
                return 0.0
            return len(words1 & words2) / len(words1 | words2)
        
        condition_sim = text_similarity(rule1.condition, rule2.condition)
        action_sim = text_similarity(rule1.action, rule2.action)
        
        return (condition_sim + action_sim) / 2
    
    def _perform_intelligent_replacement(self,
                                       existing_rules: List[ProductionRule],
                                       new_rules: List[ProductionRule],
                                       candidates: List[Tuple[ProductionRule, ProductionRule, float]],
                                       strategy: ReplacementStrategy) -> List[ProductionRule]:
        """执行智能替换"""
        result_rules = existing_rules.copy()
        replaced_rules = set()
        added_new_rules = set()
        
        # 计算允许替换的数量
        max_replacements = int(len(existing_rules) * strategy.replacement_ratio)
        replacement_count = 0
        
        # 执行高分替换
        for existing_rule, new_rule, score in candidates:
            if (replacement_count >= max_replacements or 
                existing_rule.id in replaced_rules or
                new_rule.id in added_new_rules):
                continue
            
            # 执行替换
            result_rules = [r if r.id != existing_rule.id else new_rule for r in result_rules]
            replaced_rules.add(existing_rule.id)
            added_new_rules.add(new_rule.id)
            replacement_count += 1
            
            logger.debug(f"替换规则: {existing_rule.name} -> {new_rule.name} (分数: {score:.2f})")
        
        # 添加未被替换的新规则（如果空间允许）
        for new_rule in new_rules:
            if new_rule.id not in added_new_rules:
                result_rules.append(new_rule)
        
        return result_rules
    
    def _apply_quantity_constraints(self, 
                                  rules: List[ProductionRule],
                                  strategy: ReplacementStrategy) -> List[ProductionRule]:
        """应用数量约束"""
        # 1. 总数量控制
        if len(rules) > AdaptiveReplacementConstants.ABSOLUTE_MAX_TOTAL_RULES:
            # 按优先级保留最高的规则
            rules = sorted(rules, key=lambda r: r.priority, reverse=True)
            rules = rules[:AdaptiveReplacementConstants.ABSOLUTE_MAX_TOTAL_RULES]
        
        # 2. 按阶段控制
        rules = self._limit_rules_per_phase(rules, strategy.max_rules_per_phase)
        
        # 3. 按智能体控制
        rules = self._limit_rules_per_agent(rules, strategy.max_rules_per_agent)
        
        return rules
    
    def _limit_rules_per_phase(self, rules: List[ProductionRule], max_per_phase: int) -> List[ProductionRule]:
        """限制每阶段规则数量"""
        phase_groups = {}
        for rule in rules:
            phase = rule.phase
            if phase not in phase_groups:
                phase_groups[phase] = []
            phase_groups[phase].append(rule)
        
        limited_rules = []
        for phase, phase_rules in phase_groups.items():
            # 按优先级排序，保留最高优先级的规则
            phase_rules.sort(key=lambda r: r.priority, reverse=True)
            limited_rules.extend(phase_rules[:max_per_phase])
        
        return limited_rules
    
    def _limit_rules_per_agent(self, rules: List[ProductionRule], max_per_agent: int) -> List[ProductionRule]:
        """限制每智能体规则数量"""
        agent_groups = {}
        for rule in rules:
            agent = rule.agent_name
            if agent not in agent_groups:
                agent_groups[agent] = []
            agent_groups[agent].append(rule)
        
        limited_rules = []
        for agent, agent_rules in agent_groups.items():
            # 按优先级排序，保留最高优先级的规则
            agent_rules.sort(key=lambda r: r.priority, reverse=True)
            limited_rules.extend(agent_rules[:max_per_agent])
        
        return limited_rules
    
    def _conservative_merge(self, existing_rules: List[ProductionRule], new_rules: List[ProductionRule]) -> List[ProductionRule]:
        """保守的规则合并（失败时的后备方案）"""
        # 简单合并，避免重复
        all_rules = existing_rules + new_rules
        seen_ids = set()
        unique_rules = []
        
        for rule in all_rules:
            if rule.id not in seen_ids:
                unique_rules.append(rule)
                seen_ids.add(rule.id)
        
        return unique_rules
    
    def _record_strategy_application(self,
                                   strategy: ReplacementStrategy,
                                   situation_score: SituationScore,
                                   before_count: int,
                                   after_count: int):
        """记录策略应用（用于后续学习） - 保持向后兼容性"""
        # 简化的效果记录
        improvement_score = 0.5  # 默认中等效果，实际应该基于后续执行结果
        if after_count < before_count:
            improvement_score += 0.2  # 减少规则数量通常是好的
        
        logger.info(f"记录策略应用: {strategy.strategy_type.value}, "
                   f"规则变化: {before_count} -> {after_count}")
    
    def _record_strategy_effectiveness(self,
                                     strategy: ReplacementStrategy,
                                     situation_score: SituationScore,
                                     existing_rules: List[ProductionRule],
                                     optimized_rules: List[ProductionRule],
                                     context: Dict[str, Any]):
        """
        记录策略执行效果到跟踪器
        
        Args:
            strategy: 执行的策略
            situation_score: 应用时的情境
            existing_rules: 应用前的规则
            optimized_rules: 应用后的规则
            context: 执行上下文
        """
        try:
            # 计算执行前后的指标
            before_metrics = self._calculate_rule_metrics(existing_rules)
            after_metrics = self._calculate_rule_metrics(optimized_rules)
            
            # 计算改进分数
            improvement_score = self._calculate_improvement_score(
                before_metrics, after_metrics, situation_score
            )
            
            # 记录到历史（保持原有逻辑）
            effectiveness = StrategyEffectiveness(
                strategy_type=strategy.strategy_type,
                applied_context=situation_score,
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                improvement_score=improvement_score,
                application_timestamp=datetime.now()
            )
            self.strategy_history.append(effectiveness)
            
            # 如果有效果跟踪器，也记录到跟踪器
            if self.effectiveness_tracker:
                additional_data = {
                    'goal': context.get('goal', ''),
                    'iteration_count': context.get('iteration_count', 0),
                    'context_type': context.get('context_type', ''),
                    'rules_before': len(existing_rules),
                    'rules_after': len(optimized_rules)
                }
                
                self.effectiveness_tracker.record_strategy_application(
                    strategy_type=strategy.strategy_type,
                    applied_context=situation_score,
                    before_metrics=before_metrics,
                    after_metrics=after_metrics,
                    improvement_score=improvement_score,
                    additional_data=additional_data
                )
                
            logger.info(f"策略效果已记录: {strategy.strategy_type.value} - 改进分数: {improvement_score:.2f}")
            
        except Exception as e:
            logger.error(f"记录策略效果失败: {e}")
    
    def _calculate_improvement_score(self, 
                                   before_metrics: ExecutionMetrics, 
                                   after_metrics: ExecutionMetrics, 
                                   situation: SituationScore) -> float:
        """
        计算策略改进分数
        
        Args:
            before_metrics: 应用前的执行指标
            after_metrics: 应用后的执行指标
            situation: 当前情境
            
        Returns:
            float: 改进分数 (0.0-1.0)
        """
        try:
            # 1. 成功率改进评分
            before_success_rate = before_metrics.success_rate if before_metrics.total_rules_executed > 0 else 0
            after_success_rate = after_metrics.success_rate if after_metrics.total_rules_executed > 0 else 0
            success_improvement = after_success_rate - before_success_rate
            
            # 2. 规则数量变化评分
            before_count = before_metrics.total_rules_executed
            after_count = after_metrics.total_rules_executed
            count_change_score = 0.0
            
            if before_count > 0:
                change_ratio = (before_count - after_count) / before_count
                # 适度减少规则数量得分较高
                if -0.2 <= change_ratio <= 0.3:
                    count_change_score = 0.8
                elif -0.5 <= change_ratio <= 0.5:
                    count_change_score = 0.6
                else:
                    count_change_score = 0.4
            
            # 3. 执行效率改进评分
            efficiency_improvement = 0.0
            if before_metrics.average_execution_time > 0 and after_metrics.average_execution_time > 0:
                efficiency_improvement = (before_metrics.average_execution_time - after_metrics.average_execution_time) / before_metrics.average_execution_time
                efficiency_improvement = max(-1.0, min(1.0, efficiency_improvement))  # 限制在[-1, 1]范围内
            
            # 4. 情境匹配评分
            situation_score = situation.get_overall_health()
            
            # 5. 综合评分（加权平均）
            improvement_score = (
                success_improvement * 0.4 +  # 成功率改进权重最高
                count_change_score * 0.3 +   # 规则数量优化
                efficiency_improvement * 0.2 + # 效率改进
                situation_score * 0.1         # 情境适应性
            )
            
            # 确保分数在合理范围内
            improvement_score = max(0.0, min(1.0, improvement_score + 0.5))  # 基础分数0.5
            
            return improvement_score
            
        except Exception as e:
            logger.error(f"计算改进分数失败: {e}")
            return 0.5  # 默认分数
    
    def _calculate_rule_metrics(self, rules: List[ProductionRule]) -> ExecutionMetrics:
        """
        计算规则集的执行指标
        
        Args:
            rules: 规则列表
            
        Returns:
            ExecutionMetrics: 执行指标
        """
        try:
            if not rules:
                return ExecutionMetrics(
                    total_rules_executed=0,
                    successful_executions=0,
                    failed_executions=0,
                    average_execution_time=0.0,
                    total_execution_time=0.0,
                    rule_match_accuracy=0.0
                )
            
            # 计算规则质量指标
            total_rules = len(rules)
            
            # 分析规则优先级分布
            priorities = [rule.priority for rule in rules]
            avg_priority = sum(priorities) / len(priorities) if priorities else 0
            
            # 分析阶段分布均衡性
            phase_counts = {}
            for rule in rules:
                phase = rule.phase.value
                phase_counts[phase] = phase_counts.get(phase, 0) + 1
            
            phase_balance = len(phase_counts) / 4.0 if phase_counts else 0  # 假设有4个主要阶段
            
            # 分析智能体分布均衡性
            agent_counts = {}
            for rule in rules:
                agent = rule.agent_name
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
            
            agent_balance = 1.0 / max(agent_counts.values()) if agent_counts else 0
            
            # 综合质量分数（模拟成功率）
            quality_score = (avg_priority / 100.0 + phase_balance + agent_balance) / 3.0
            successful_count = int(total_rules * min(1.0, quality_score))
            
            return ExecutionMetrics(
                total_rules_executed=total_rules,
                successful_executions=successful_count,
                failed_executions=total_rules - successful_count,
                average_execution_time=1.0,  # 模拟执行时间
                total_execution_time=float(total_rules),
                rule_match_accuracy=quality_score
            )
            
        except Exception as e:
            logger.error(f"计算规则指标失败: {e}")
            return ExecutionMetrics(
                total_rules_executed=0,
                successful_executions=0,
                failed_executions=0,
                average_execution_time=0.0,
                total_execution_time=0.0,
                rule_match_accuracy=0.0
            )
    
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            'enable_llm_analysis': True,
            'max_replacement_ratio': AdaptiveReplacementConstants.MAX_REPLACEMENT_RATIO,
            'min_similarity_threshold': 0.5,
            'strategy_learning_enabled': True
        }
    
    def _get_default_strategy(self) -> ReplacementStrategy:
        """获取默认策略"""
        return ReplacementStrategy(
            strategy_type=ReplacementStrategyType.INCREMENTAL_IMPROVEMENT,
            replacement_ratio=AdaptiveReplacementConstants.DEFAULT_REPLACEMENT_RATIO,
            similarity_threshold=AdaptiveReplacementConstants.DEFAULT_SIMILARITY_THRESHOLD,
            performance_threshold=AdaptiveReplacementConstants.DEFAULT_PERFORMANCE_THRESHOLD,
            priority_adjustment=False,
            conservative_mode=True,
            max_rules_per_phase=AdaptiveReplacementConstants.DEFAULT_MAX_RULES_PER_PHASE,
            max_rules_per_agent=AdaptiveReplacementConstants.DEFAULT_MAX_RULES_PER_AGENT
        )
    
    def get_effectiveness_tracker(self) -> Optional[StrategyEffectivenessTracker]:
        """
        获取策略效果跟踪器
        
        Returns:
            Optional[StrategyEffectivenessTracker]: 效果跟踪器实例
        """
        return self.effectiveness_tracker
    
    def get_strategy_performance_summary(self) -> Dict[str, Any]:
        """
        获取策略性能摘要
        
        Returns:
            Dict[str, Any]: 性能摘要数据
        """
        # 优先使用效果跟踪器的数据
        if self.effectiveness_tracker:
            return self.effectiveness_tracker.get_strategy_performance_summary()
        
        # 回退到本地历史数据
        if not self.strategy_history:
            return {'message': '暂无策略应用历史'}
        
        # 按策略类型分组统计
        strategy_stats = {}
        for effectiveness in self.strategy_history:
            strategy_type = effectiveness.strategy_type.value
            if strategy_type not in strategy_stats:
                strategy_stats[strategy_type] = {
                    'count': 0,
                    'total_improvement': 0.0,
                    'successful_applications': 0
                }
            
            stats = strategy_stats[strategy_type]
            stats['count'] += 1
            stats['total_improvement'] += effectiveness.improvement_score
            if effectiveness.is_successful_application():
                stats['successful_applications'] += 1
        
        # 计算平均值和成功率
        for strategy_type, stats in strategy_stats.items():
            stats['average_improvement'] = stats['total_improvement'] / stats['count']
            stats['success_rate'] = stats['successful_applications'] / stats['count']
        
        return {
            'total_applications': len(self.strategy_history),
            'strategy_statistics': strategy_stats,
            'overall_success_rate': sum(1 for eff in self.strategy_history if eff.is_successful_application()) / len(self.strategy_history),
            'best_performing_strategy': max(strategy_stats.items(), key=lambda x: x[1]['average_improvement'])[0] if strategy_stats else None
        }
    
    def analyze_strategy_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        分析策略趋势
        
        Args:
            days: 分析天数
            
        Returns:
            Dict[str, Any]: 趋势分析结果
        """
        # 优先使用效果跟踪器的数据
        if self.effectiveness_tracker:
            return self.effectiveness_tracker.analyze_strategy_trends(days)
        
        # 回退到本地历史数据
        if not self.strategy_history:
            return {'message': f'暂无{days}天内的策略应用记录'}
        
        # 简化的趋势分析
        recent_history = self.strategy_history[-min(10, len(self.strategy_history)):]
        
        return {
            'period_days': days,
            'recent_applications': len(recent_history),
            'average_improvement': sum(eff.improvement_score for eff in recent_history) / len(recent_history),
            'most_used_strategy': max(set(eff.strategy_type.value for eff in recent_history), 
                                    key=lambda x: sum(1 for eff in recent_history if eff.strategy_type.value == x))
        }
    
    def get_improvement_recommendations(self) -> List[Dict[str, Any]]:
        """
        获取策略改进建议
        
        Returns:
            List[Dict[str, Any]]: 改进建议列表
        """
        # 优先使用效果跟踪器的建议
        if self.effectiveness_tracker:
            return self.effectiveness_tracker.get_improvement_recommendations()
        
        # 回退到基础建议
        return [
            {
                'type': 'data_collection',
                'priority': 'medium',
                'recommendation': '启用策略效果跟踪器以获得更智能的改进建议'
            }
        ]
    
    def export_performance_data(self, format_type: str = 'summary') -> Dict[str, Any]:
        """
        导出性能数据
        
        Args:
            format_type: 导出格式
            
        Returns:
            Dict[str, Any]: 性能数据
        """
        # 优先使用效果跟踪器的导出功能
        if self.effectiveness_tracker:
            return self.effectiveness_tracker.export_performance_data(format_type)
        
        # 回退到基础导出
        summary = self.get_strategy_performance_summary()
        trends = self.analyze_strategy_trends()
        
        return {
            'export_format': format_type,
            'export_timestamp': datetime.now().isoformat(),
            'performance_summary': summary,
            'strategy_trends': trends,
            'total_history_entries': len(self.strategy_history)
        }
    
    def enable_llm_enhanced_similarity(self, enable: bool = True):
        """
        启用或禁用LLM增强的相似性分析
        
        Args:
            enable: 是否启用
        """
        self.replacement_config['enable_llm_similarity'] = enable
        logger.info(f"LLM增强相似性分析: {'启用' if enable else '禁用'}")
    
    def get_strategy_recommendation_confidence(self, situation_score: SituationScore) -> float:
        """
        获取策略推荐的置信度
        
        Args:
            situation_score: 当前情境评估
            
        Returns:
            float: 推荐置信度 (0.0-1.0)
        """
        if self.effectiveness_tracker:
            _, confidence = self.effectiveness_tracker.recommend_optimal_strategy(
                situation_score, {}
            )
            return confidence
        else:
            # 基于情境健康度估算置信度
            health = situation_score.get_overall_health()
            if health > 0.8:
                return 0.9  # 情境良好，推荐置信度高
            elif health > 0.5:
                return 0.7  # 情境一般，推荐置信度中等
            else:
                return 0.5  # 情境较差，推荐置信度较低