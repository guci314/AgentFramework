# -*- coding: utf-8 -*-
"""
规则生成服务

专注于智能规则创建，支持基于目标的初始规则生成、
错误恢复规则生成、策略调整规则生成等功能。
"""

from typing import Dict, List, Any, Optional
import logging
import uuid
from datetime import datetime

from ..domain.entities import ProductionRule, RuleSet, AgentRegistry, GlobalState, DecisionResult
from ..domain.value_objects import RulePhase, RuleSetStatus, RuleConstants, DecisionType
from .language_model_service import LanguageModelService

logger = logging.getLogger(__name__)


class RuleGenerationService:
    """规则生成服务 - 专注于智能规则创建"""
    
    def __init__(self, llm_service: LanguageModelService, agent_registry: AgentRegistry = None):
        """
        初始化规则生成服务
        
        Args:
            llm_service: 语言模型服务
            agent_registry: 智能体注册表（用于决策功能）
        """
        self.llm_service = llm_service
        self._agent_registry = agent_registry
        
    def generate_rule_set(self, goal: str, agent_registry: AgentRegistry) -> RuleSet:
        """
        根据目标生成初始规则集
        
        Args:
            goal: 目标描述
            agent_registry: 智能体注册表
            
        Returns:
            RuleSet: 生成的规则集
        """
        try:
            logger.info(f"开始生成规则集，目标: {goal}")
            
            # 获取可用的智能体信息
            available_agents = agent_registry.list_all_agents()
            agents_desc = self._format_agents_for_rule_generation(available_agents)
            
            # 生成规则
            rules = self._generate_initial_rules(goal, agents_desc)
            
            # 创建规则集
            rule_set = RuleSet(
                id=f"ruleset_{hash(goal) % 1000000:06d}",
                goal=goal,
                rules=rules,
                status=RuleSetStatus.ACTIVE
            )
            
            logger.info(f"规则集生成完成，包含 {len(rules)} 个规则")
            return rule_set
            
        except Exception as e:
            logger.error(f"规则集生成失败: {e}")
            # 直接重新抛出异常，不再使用回退规则集
            raise
    
    def generate_recovery_rules(self, failure_context: Dict[str, Any]) -> List[ProductionRule]:
        """
        使用语言模型生成错误恢复规则
        
        Args:
            failure_context: 失败上下文信息
            
        Returns:
            List[ProductionRule]: 恢复规则列表
        """
        try:
            logger.info("开始使用LLM生成错误恢复规则")
            
            # 使用LLM分析失败并生成恢复规则
            recovery_rules = self._generate_llm_recovery_rules(failure_context)
            
            logger.info(f"LLM生成了 {len(recovery_rules)} 个恢复规则")
            return recovery_rules
            
        except Exception as e:
            logger.error(f"LLM恢复规则生成失败: {e}")
            return []
    
    def _generate_llm_recovery_rules(self, failure_context: Dict[str, Any]) -> List[ProductionRule]:
        """
        使用语言模型智能生成错误恢复规则
        
        Args:
            failure_context: 失败上下文信息
            
        Returns:
            List[ProductionRule]: LLM生成的恢复规则列表
        """
        try:
            # 获取可用智能体信息
            available_agents = []
            if hasattr(self, '_current_agent_registry') and self._current_agent_registry:
                agents_list = self._current_agent_registry.list_all_agents()
                for name, agent in agents_list:
                    specification = getattr(agent, 'api_specification', f'{name} Agent')
                    available_agents.append(f"- {name}: {specification}")
            
            agents_desc = "\n".join(available_agents) if available_agents else "- coder: 代码专家，擅长编写、调试和优化代码"
            
            # 安全地提取上下文信息，避免格式化复杂对象
            rule_id_str = str(failure_context.get('rule_id', 'unknown'))
            failure_reason_str = str(failure_context.get('failure_reason', '未知错误'))
            error_message_str = str(failure_context.get('error_message', '无详细信息'))
            
            # 安全地处理执行上下文
            execution_context = failure_context.get('execution_context', {})
            if isinstance(execution_context, dict):
                context_str = str({k: str(v) for k, v in execution_context.items()})
            else:
                context_str = str(execution_context)
            
            global_state_str = str(failure_context.get('global_state', '状态不可用'))
            
            # 构建智能恢复规则生成提示词
            recovery_prompt = f"""
你是一个专业的错误恢复规则生成专家。请根据以下失败情况，生成具体的恢复规则来解决问题。

## 失败上下文信息
规则ID: {rule_id_str}
失败原因: {failure_reason_str}
错误消息: {error_message_str}
执行上下文: {context_str}
当前状态: {global_state_str}

## 可用智能体
{agents_desc}

## 恢复规则生成指导

请分析失败原因并生成2-4个恢复规则，按以下优先级策略：

1. **直接修复规则** (priority: 90-95): 针对具体错误的直接解决方案
2. **环境检查规则** (priority: 80-85): 检查和修复环境问题
3. **重试策略规则** (priority: 70-75): 智能重试机制
4. **降级方案规则** (priority: 60-65): 备用解决方案

## JSON Schema

请严格按照以下JSON格式返回恢复规则：

```json
{{
  "recovery_rules": [
    {{
      "rule_name": "具体的恢复规则名称",
      "trigger_condition": "触发条件（描述什么情况下使用此恢复规则）",
      "action": "恢复动作（具体的修复操作指令）",
      "agent_name": "负责执行的智能体名称（从上述可用智能体中选择）",
      "execution_phase": "execution",
      "priority": 优先级数字（60-95），
      "expected_result": "期望的恢复结果描述"
    }}
  ]
}}
```

## 生成要求

1. **针对性强**: 恢复规则必须针对具体的失败原因
2. **可执行性**: 动作描述要具体明确，智能体能够理解执行
3. **智能体选择**: 根据恢复任务特点选择最合适的智能体
4. **优先级合理**: 更直接有效的解决方案优先级更高
5. **完整覆盖**: 提供从直接修复到降级方案的完整恢复路径

请分析失败情况并生成专业的恢复规则集。
"""

            # 调用LLM生成恢复规则
            try:
                response = self.llm_service.generate_natural_language_response(recovery_prompt)
                recovery_data = self.llm_service._parse_json_response(response)
            except Exception as llm_error:
                logger.error(f"LLM服务调用失败: {llm_error}")
                recovery_data = None
            
            # 解析生成的恢复规则
            recovery_rules = []
            if recovery_data and isinstance(recovery_data, dict) and 'recovery_rules' in recovery_data:
                rules_data = recovery_data['recovery_rules']
                
                for i, rule_data in enumerate(rules_data):
                    try:
                        # 生成确定性ID
                        rule_name = rule_data.get('rule_name', f'恢复规则_{i+1}')
                        # 确保rule_id是字符串格式，避免hash错误
                        original_rule_id = failure_context.get('rule_id', 'unknown')
                        if isinstance(original_rule_id, dict):
                            original_rule_id = str(original_rule_id)
                        rule_id = f"recovery_{hash(str(original_rule_id) + rule_name) % 1000000:06d}"
                        
                        # 解析阶段
                        phase_str = rule_data.get('execution_phase', 'execution')
                        try:
                            phase = RulePhase(phase_str)
                        except ValueError:
                            phase = RulePhase.EXECUTION
                        
                        # 创建恢复规则
                        recovery_rule = ProductionRule(
                            id=rule_id,
                            name=rule_name,
                            condition=rule_data.get('trigger_condition', '需要恢复操作'),
                            action=rule_data.get('action', '执行恢复操作'),
                            agent_name=rule_data.get('agent_name', 'coder'),
                            priority=int(rule_data.get('priority', 75)),
                            phase=phase,
                            expected_outcome=rule_data.get('expected_result', '问题得到解决')
                        )
                        
                        recovery_rules.append(recovery_rule)
                        logger.debug(f"生成恢复规则: {rule_name}")
                        
                    except Exception as e:
                        logger.warning(f"恢复规则解析失败: {e}, 数据: {rule_data}")
                        continue
            
            if not recovery_rules:
                logger.warning("LLM未生成有效的恢复规则，使用基础恢复规则")
                # 基础恢复规则作为后备
                # 确保rule_id是字符串格式，避免hash错误
                original_rule_id = failure_context.get('rule_id', 'unknown')
                if isinstance(original_rule_id, dict):
                    original_rule_id = str(original_rule_id)
                basic_recovery_rule = ProductionRule(
                    id=f"basic_recovery_{hash(str(original_rule_id)) % 1000000:06d}",
                    name="基础错误恢复",
                    condition="检测到执行失败需要恢复",
                    action=f"分析失败原因: {failure_context.get('failure_reason', '未知错误')}，并尝试修复问题",
                    agent_name='coder',
                    priority=70,
                    phase=RulePhase.EXECUTION,
                    expected_outcome="问题得到识别和修复"
                )
                recovery_rules.append(basic_recovery_rule)
            
            return recovery_rules
            
        except Exception as e:
            logger.error(f"LLM恢复规则生成异常: {e}")
            return []
    
    def generate_strategy_adjustment_rules(self, goal_context: Dict[str, Any]) -> List[ProductionRule]:
        """
        生成策略调整规则（目标级失败响应）
        
        Args:
            goal_context: 目标上下文信息
            
        Returns:
            List[ProductionRule]: 策略调整规则列表
        """
        try:
            logger.info("开始生成策略调整规则")
            
            # 分析目标执行情况
            goal_analysis = self._analyze_goal_progress(goal_context)
            
            # 生成新的策略
            strategy_rules = self._generate_strategic_adjustment_rules(goal_analysis)
            
            logger.info(f"生成了 {len(strategy_rules)} 个策略调整规则")
            return strategy_rules
            
        except Exception as e:
            logger.error(f"策略调整规则生成失败: {e}")
            return []
    
    def expand_rule_details(self, rule: ProductionRule) -> ProductionRule:
        """
        扩展规则细节
        
        Args:
            rule: 要扩展的规则
            
        Returns:
            ProductionRule: 扩展后的规则
        """
        try:
            # 生成更详细的期望结果
            detailed_outcome = self._generate_detailed_outcome(rule)
            
            # 优化动作描述
            optimized_action = self._optimize_action_description(rule)
            
            # 创建扩展后的规则
            expanded_rule = ProductionRule(
                id=rule.id,
                name=rule.name,
                condition=rule.condition,
                action=optimized_action,
                agent_name=rule.agent_name,
                priority=rule.priority,
                phase=rule.phase,
                expected_outcome=detailed_outcome,
                metadata=rule.metadata.copy()
            )
            
            logger.debug(f"规则细节已扩展: {rule.name}")
            return expanded_rule
            
        except Exception as e:
            logger.error(f"规则细节扩展失败: {e}")
            return rule
    
    def validate_rule_set(self, rule_set: RuleSet) -> List[str]:
        """
        验证规则集有效性
        
        Args:
            rule_set: 要验证的规则集
            
        Returns:
            List[str]: 验证问题列表，空列表表示无问题
        """
        issues = []
        
        try:
            # 检查规则集基本信息
            if not rule_set.goal.strip():
                issues.append("规则集目标不能为空")
            
            if len(rule_set.rules) == 0:
                issues.append("规则集不能为空")
            
            # 检查每个规则
            for i, rule in enumerate(rule_set.rules):
                rule_issues = self._validate_single_rule(rule, i)
                issues.extend(rule_issues)
            
            # 检查规则优先级冲突
            priority_issues = self._check_priority_conflicts(rule_set.rules)
            issues.extend(priority_issues)
            
            # 检查规则覆盖度
            coverage_issues = self._check_rule_coverage(rule_set)
            issues.extend(coverage_issues)
            
            logger.info(f"规则集验证完成，发现 {len(issues)} 个问题")
            return issues
            
        except Exception as e:
            logger.error(f"规则集验证失败: {e}")
            return [f"验证过程中发生错误: {str(e)}"]
    
    def optimize_rule_priorities(self, rules: List[ProductionRule]) -> List[ProductionRule]:
        """
        优化规则优先级
        
        Args:
            rules: 要优化的规则列表
            
        Returns:
            List[ProductionRule]: 优化后的规则列表
        """
        try:
            logger.info("开始优化规则优先级")
            
            # 按阶段分组
            phase_groups = {}
            for rule in rules:
                if rule.phase not in phase_groups:
                    phase_groups[rule.phase] = []
                phase_groups[rule.phase].append(rule)
            
            optimized_rules = []
            
            # 为每个阶段优化优先级
            for phase, phase_rules in phase_groups.items():
                optimized_phase_rules = self._optimize_phase_priorities(phase_rules, phase)
                optimized_rules.extend(optimized_phase_rules)
            
            logger.info("规则优先级优化完成")
            return optimized_rules
            
        except Exception as e:
            logger.error(f"规则优先级优化失败: {e}")
            return rules
    
    def _generate_initial_rules(self, goal: str, agents_desc: str) -> List[ProductionRule]:
        """
        生成初始规则
        
        Args:
            goal: 目标描述
            agents_desc: 可用智能体描述
            
        Returns:
            List[ProductionRule]: 生成的规则列表
        """
        prompt = f"""
请为以下目标生成一套产生式规则：

目标: {goal}

可用的智能体:
{agents_desc}

## 三阶段执行模式

请基于以下三阶段模式生成规则：

1. **收集阶段 (information_gathering)**: 分析需求、收集信息、理解问题
2. **执行阶段 (execution)**: 实现主要功能、解决核心问题
3. **验证阶段 (verification)**: 测试结果、验证正确性、完善细节

**重要说明**: 简单直接的任务可以跳过收集阶段，直接从执行阶段开始。

## JSON Schema

请严格按照以下JSON schema返回规则：

```json
{{
  "rules": [
    {{
      "rule_name": "规则名称（字符串）",
      "trigger_condition": "触发条件（IF部分，自然语言描述）",
      "action": "执行动作（THEN部分，自然语言指令）",
      "agent_name": "智能体名称（必须从上述可用智能体中选择）",
      "execution_phase": "执行阶段（information_gathering|execution|verification）",
      "priority": 优先级数字（1-100，数字越大优先级越高）,
      "expected_result": "期望结果描述（字符串）"
    }}
  ]
}}
```

## 生成要求

1. **规则数量**: 根据任务复杂度自行判断，简单任务2-3个规则，复杂任务可以更多
2. **阶段分布**: 
   - 简单任务：可以只有执行和验证阶段
   - 复杂任务：包含完整的收集、执行、验证三阶段
3. **条件描述**: 使用自然语言，便于语义匹配
4. **动作指令**: 具体明确，便于智能体理解和执行
5. **智能体匹配**: agent_name必须从可用智能体列表中选择
6. **优先级**: 收集>执行>验证，同阶段内按重要性排序

请分析目标复杂度，生成适合的规则集合，严格按照JSON schema格式返回。
"""
        
        try:
            response = self.llm_service.generate_natural_language_response(prompt)
            rules_data = self.llm_service._parse_json_response(response)
            
            rules = []
            if isinstance(rules_data, dict) and 'rules' in rules_data:
                rules_data = rules_data['rules']
            
            if isinstance(rules_data, list):
                for rule_data in rules_data:
                    rule = self._create_rule_from_data(rule_data)
                    if rule:
                        rules.append(rule)
            
            # 如果生成失败，直接抛出异常
            if not rules:
                raise ValueError(f"LLM未能生成有效的规则，目标: {goal}")
            
            return rules
            
        except Exception as e:
            logger.error(f"初始规则生成失败: {e}")
            raise ValueError(f"规则生成失败: {str(e)}")
    
    def _create_rule_from_data(self, rule_data: Dict[str, Any]) -> Optional[ProductionRule]:
        """
        从数据字典创建规则
        
        Args:
            rule_data: 规则数据字典
            
        Returns:
            Optional[ProductionRule]: 创建的规则，失败时返回None
        """
        try:
            # 解析阶段 - 支持新旧字段名和值
            phase_str = rule_data.get('execution_phase') or rule_data.get('phase', 'execution')
            
            # 支持旧的 problem_solving 值
            if phase_str == 'problem_solving':
                phase_str = 'execution'
            
            try:
                phase = RulePhase(phase_str)
            except ValueError:
                phase = RulePhase.EXECUTION
            
            # 生成确定性ID
            rule_name = rule_data.get('rule_name') or rule_data.get('name', '未命名规则')
            rule_id = f"rule_{hash(rule_name + str(rule_data)) % 1000000:06d}"
            
            # 创建规则 - 支持新旧字段名
            rule = ProductionRule(
                id=rule_id,
                name=rule_name,
                condition=rule_data.get('trigger_condition') or rule_data.get('condition', ''),
                action=rule_data.get('action', ''),
                agent_name=rule_data.get('agent_name', ''),
                priority=int(rule_data.get('priority', RuleConstants.DEFAULT_RULE_PRIORITY)),
                phase=phase,
                expected_outcome=rule_data.get('expected_result') or rule_data.get('expected_outcome', '')
            )
            
            return rule
            
        except Exception as e:
            logger.error(f"规则创建失败: {e}, 数据: {rule_data}")
            return None
    
    
    def _format_agents_for_rule_generation(self, agents_list: List[tuple]) -> str:
        """
        格式化智能体信息供规则生成使用
        
        Args:
            agents_list: 智能体列表，格式为[(name, agent), ...]
            
        Returns:
            str: 格式化的智能体描述
        """
        if not agents_list:
            return "无可用智能体"
        
        formatted_lines = []
        for name, agent in agents_list:
            # 获取智能体的api_specification作为能力描述
            specification = getattr(agent, 'api_specification', f'{name} Agent')
            
            formatted_lines.append(
                f"- {name}: {specification}"
            )
        
        return '\n'.join(formatted_lines)
    
    
    def _analyze_goal_progress(self, goal_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析目标执行进度
        
        Args:
            goal_context: 目标上下文
            
        Returns:
            Dict[str, Any]: 进度分析结果
        """
        return {
            'goal': goal_context.get('goal', ''),
            'current_state': goal_context.get('current_state', ''),
            'execution_history': goal_context.get('execution_history', []),
            'obstacles': goal_context.get('obstacles', []),
            'progress_rate': goal_context.get('progress_rate', 0.0)
        }
    
    def _generate_strategic_adjustment_rules(self, goal_analysis: Dict[str, Any]) -> List[ProductionRule]:
        """
        使用语言模型智能生成策略调整规则
        
        Args:
            goal_analysis: 目标分析结果
            
        Returns:
            List[ProductionRule]: 策略调整规则列表
        """
        try:
            logger.info("开始使用LLM生成策略调整规则")
            
            # 使用LLM分析目标并生成策略调整规则
            strategy_rules = self._generate_llm_strategic_rules(goal_analysis)
            
            logger.info(f"LLM生成了 {len(strategy_rules)} 个策略调整规则")
            return strategy_rules
            
        except Exception as e:
            logger.error(f"LLM策略调整规则生成失败: {e}")
            return []
    
    def _generate_llm_strategic_rules(self, goal_analysis: Dict[str, Any]) -> List[ProductionRule]:
        """
        使用语言模型智能生成策略调整规则
        
        Args:
            goal_analysis: 目标分析结果
            
        Returns:
            List[ProductionRule]: 智能生成的策略调整规则列表
        """
        try:
            # 构建策略调整提示词
            strategy_prompt = f"""
你是一个专业的策略调整规则生成专家。请根据以下目标分析信息，生成具体的策略调整规则来优化目标执行。

## 目标分析信息
目标描述: {goal_analysis.get('goal', '未知目标')}
当前进度: {goal_analysis.get('progress_rate', 0.0):.1%}
执行历史: {goal_analysis.get('execution_history', [])}
遇到障碍: {goal_analysis.get('obstacles', [])}
分析结果: {goal_analysis.get('analysis_summary', '无详细分析')}

## 策略调整规则生成指导
请分析目标执行情况并生成2-4个策略调整规则，按以下优先级策略：

1. **高优先级策略规则** (priority: 85-95): 针对关键障碍的策略重构
2. **中优先级优化规则** (priority: 70-84): 执行路径和方法优化
3. **低优先级辅助规则** (priority: 60-69): 支持性策略调整

每个规则必须包含以下信息，请严格按照JSON格式输出：

```json
[
  {{
    "id": "rule_strategic_XXX",
    "name": "规则名称",
    "condition": "触发条件的自然语言描述",
    "action": "具体执行动作的自然语言描述",
    "agent_name": "最适合的智能体名称(coder/tester/analyst等)",
    "priority": 优先级数值(60-95),
    "phase": "execution/information_gathering/verification之一",
    "expected_outcome": "期望结果的具体描述"
  }}
]
```

## 策略调整规则类型参考
- **重新规划策略**: 当遇到重大障碍时，重新分析和制定执行策略
- **目标分解优化**: 将复杂目标分解为更可管理的子目标
- **执行路径调整**: 改变执行顺序或方法来提高成功率
- **资源重新分配**: 调整智能体分工和任务分配
- **风险规避策略**: 识别和规避潜在风险点
- **进度加速策略**: 优化执行效率和速度

请确保生成的规则：
1. 针对具体的目标分析结果
2. 条件描述清晰，可以语义匹配
3. 动作描述具体，可以直接执行
4. 优先级合理，反映规则重要性
5. 智能体选择恰当，匹配规则需求

生成规则数量: 2-4个
输出格式: 严格的JSON数组格式
"""

            # 调用语言模型生成策略调整规则
            try:
                response = self.llm_service.generate_response(strategy_prompt)
                logger.debug(f"LLM策略调整响应: {response[:500]}...")
                
                # 解析LLM响应为ProductionRule对象
                strategy_rules = self._parse_rules_from_llm_response(response, "strategic")
                
                if not strategy_rules:
                    logger.warning("LLM未生成有效的策略调整规则，使用默认规则")
                    return self._get_default_strategic_rules(goal_analysis)
                
                logger.info(f"成功解析 {len(strategy_rules)} 个策略调整规则")
                return strategy_rules
                
            except Exception as e:
                logger.error(f"调用LLM生成策略调整规则失败: {e}")
                return self._get_default_strategic_rules(goal_analysis)
                
        except Exception as e:
            logger.error(f"构建策略调整提示词失败: {e}")
            return []
    
    def _get_default_strategic_rules(self, goal_analysis: Dict[str, Any]) -> List[ProductionRule]:
        """
        获取默认的策略调整规则（当LLM生成失败时使用）
        
        Args:
            goal_analysis: 目标分析结果
            
        Returns:
            List[ProductionRule]: 默认策略调整规则列表
        """
        try:
            # 提取目标信息用于个性化默认规则
            goal = goal_analysis.get('goal', '未知目标')
            progress_rate = goal_analysis.get('progress_rate', 0.0)
            
            # 确保goal是字符串格式，避免hash错误
            if not isinstance(goal, str):
                goal = str(goal)
            
            default_rules = []
            
            # 根据进度率生成不同的默认策略
            if progress_rate < 0.3:  # 进度较慢
                default_rules.append(ProductionRule(
                    id=f'rule_strategic_replan_{hash(goal) % 1000:03d}',
                    name='重新规划执行策略',
                    condition='当前执行进度缓慢或遇到重大障碍',
                    action=f'重新分析目标"{goal[:50]}..."的执行策略，制定更有效的实施方案',
                    agent_name='coder',
                    priority=90,
                    phase=RulePhase.INFORMATION_GATHERING,
                    expected_outcome='制定优化的执行策略，提高执行效率'
                ))
            
            # 通用目标分解规则
            default_rules.append(ProductionRule(
                id=f'rule_strategic_decompose_{hash(goal) % 1000:03d}',
                name='目标分解和优先级调整',
                condition='当前目标过于复杂或执行困难',
                action=f'将目标"{goal[:50]}..."分解为更小的可管理子目标，重新排列优先级',
                agent_name='coder',
                priority=75,
                phase=RulePhase.INFORMATION_GATHERING,
                expected_outcome='确定分解后的子目标和执行优先级'
            ))
            
            logger.info(f"生成了 {len(default_rules)} 个默认策略调整规则")
            return default_rules
            
        except Exception as e:
            logger.error(f"生成默认策略调整规则失败: {e}")
            return []
    
    def _generate_detailed_outcome(self, rule: ProductionRule) -> str:
        """
        生成详细的期望结果
        
        Args:
            rule: 规则
            
        Returns:
            str: 详细的期望结果
        """
        if rule.expected_outcome:
            return rule.expected_outcome
        
        # 基于动作生成期望结果
        prompt = f"""
对于以下执行动作，请生成详细的期望结果描述：

动作: {rule.action}

期望结果应该：
1. 具体明确，可以验证
2. 描述成功完成的状态
3. 便于后续规则匹配

请只返回期望结果的描述。
"""
        
        try:
            outcome = self.llm_service.generate_natural_language_response(prompt)
            return outcome.strip()
        except Exception as e:
            logger.error(f"期望结果生成失败: {e}")
            return f"完成动作: {rule.action}"
    
    def _optimize_action_description(self, rule: ProductionRule) -> str:
        """
        优化动作描述
        
        Args:
            rule: 规则
            
        Returns:
            str: 优化后的动作描述
        """
        if not rule.action:
            return rule.action
        
        prompt = f"""
请优化以下动作描述，使其更加具体和可执行：

原动作: {rule.action}
规则条件: {rule.condition}

优化要求：
1. 指令清晰具体
2. 便于智能体理解和执行
3. 包含必要的上下文信息

请只返回优化后的动作描述。
"""
        
        try:
            optimized_action = self.llm_service.generate_natural_language_response(prompt)
            return optimized_action.strip()
        except Exception as e:
            logger.error(f"动作描述优化失败: {e}")
            return rule.action
    
    def _validate_single_rule(self, rule: ProductionRule, index: int) -> List[str]:
        """
        验证单个规则
        
        Args:
            rule: 要验证的规则
            index: 规则索引
            
        Returns:
            List[str]: 问题列表
        """
        issues = []
        
        if not rule.name.strip():
            issues.append(f"规则 {index}: 名称不能为空")
        
        if not rule.condition.strip():
            issues.append(f"规则 {index}: 条件不能为空")
        
        if not rule.action.strip():
            issues.append(f"规则 {index}: 动作不能为空")
        
        if not rule.agent_capability_id.strip():
            issues.append(f"规则 {index}: 智能体能力ID不能为空")
        
        if not (RuleConstants.MIN_RULE_PRIORITY <= rule.priority <= RuleConstants.MAX_RULE_PRIORITY):
            issues.append(f"规则 {index}: 优先级必须在 {RuleConstants.MIN_RULE_PRIORITY}-{RuleConstants.MAX_RULE_PRIORITY} 之间")
        
        return issues
    
    def _check_priority_conflicts(self, rules: List[ProductionRule]) -> List[str]:
        """
        检查优先级冲突
        
        Args:
            rules: 规则列表
            
        Returns:
            List[str]: 冲突问题列表
        """
        issues = []
        
        # 按阶段分组检查
        phase_priorities = {}
        for rule in rules:
            if rule.phase not in phase_priorities:
                phase_priorities[rule.phase] = {}
            
            if rule.priority in phase_priorities[rule.phase]:
                existing_rule = phase_priorities[rule.phase][rule.priority]
                issues.append(f"优先级冲突: 规则 '{rule.name}' 和 '{existing_rule.name}' 在阶段 {rule.phase.value} 中具有相同优先级 {rule.priority}")
            else:
                phase_priorities[rule.phase][rule.priority] = rule
        
        return issues
    
    def _check_rule_coverage(self, rule_set: RuleSet) -> List[str]:
        """
        检查规则覆盖度
        
        Args:
            rule_set: 规则集
            
        Returns:
            List[str]: 覆盖度问题列表
        """
        issues = []
        
        # 检查是否覆盖了所有阶段
        covered_phases = set(rule.phase for rule in rule_set.rules)
        all_phases = set(RulePhase)
        
        missing_phases = all_phases - covered_phases
        if missing_phases:
            missing_phase_names = [phase.value for phase in missing_phases]
            issues.append(f"缺少以下阶段的规则: {', '.join(missing_phase_names)}")
        
        return issues
    
    def _optimize_phase_priorities(self, rules: List[ProductionRule], phase: RulePhase) -> List[ProductionRule]:
        """
        优化阶段内的规则优先级
        
        Args:
            rules: 阶段内的规则列表
            phase: 执行阶段
            
        Returns:
            List[ProductionRule]: 优化后的规则列表
        """
        if len(rules) <= 1:
            return rules
        
        # 为避免修改原规则，创建副本
        optimized_rules = []
        for rule in rules:
            optimized_rule = ProductionRule(
                id=rule.id,
                name=rule.name,
                condition=rule.condition,
                action=rule.action,
                agent_name=rule.agent_name,
                priority=rule.priority,
                phase=rule.phase,
                expected_outcome=rule.expected_outcome,
                metadata=rule.metadata.copy()
            )
            optimized_rules.append(optimized_rule)
        
        # 重新分配优先级，避免冲突
        sorted_rules = sorted(optimized_rules, key=lambda r: r.priority, reverse=True)
        
        for i, rule in enumerate(sorted_rules):
            # 确保优先级在有效范围内且不冲突
            new_priority = RuleConstants.MAX_RULE_PRIORITY - i * 5
            if new_priority < RuleConstants.MIN_RULE_PRIORITY:
                new_priority = RuleConstants.MIN_RULE_PRIORITY + i
            
            rule.update_priority(new_priority)
        
        return optimized_rules
    
    def _create_fallback_rule_set(self, goal: str, agent_registry: AgentRegistry) -> RuleSet:
        """
        回退规则集创建方法（已废弃，直接抛出异常）
        
        Args:
            goal: 目标描述
            agent_registry: 智能体注册表
            
        Returns:
            RuleSet: 不会返回，直接抛出异常
            
        Raises:
            RuntimeError: 规则生成失败时直接报错
        """
        logger.error("规则生成完全失败，无法创建有效的规则集")
        raise RuntimeError(f"无法为目标 '{goal}' 生成有效的规则集。请检查：\n"
                         f"1. 语言模型是否正常工作\n"
                         f"2. 目标描述是否清晰\n"
                         f"3. 智能体能力是否配置正确")
    
    # ======================== 决策功能（从RuleEngineService迁移） ========================
    
    def make_decision(self, 
                     global_state: GlobalState, 
                     rule_set: RuleSet) -> DecisionResult:
        """
        进行工作流决策 - 使用单次LLM调用完成所有决策逻辑
        
        Args:
            global_state: 当前全局状态
            rule_set: 规则集
            
        Returns:
            DecisionResult: 工作流决策结果，包含决策类型和相关信息
        """
        try:
            logger.debug("开始单次LLM工作流决策")
            
            # 1. 快速检查目标是否已达成（从状态中直接读取）
            if global_state.goal_achieved:
                logger.info("目标已达成")
                return DecisionResult(
                    selected_rule=None,
                    decision_type=DecisionType.GOAL_ACHIEVED,
                    confidence=1.0,
                    reasoning="目标已成功达成"
                )
            
            # 2. 使用单次LLM调用进行智能决策
            return self._make_llm_decision(global_state, rule_set)
            
        except Exception as e:
            logger.error(f"工作流决策失败: {e}")
            return DecisionResult(
                selected_rule=None,
                decision_type=DecisionType.GOAL_FAILED,
                confidence=0.0,
                reasoning=f"决策过程异常: {str(e)}"
            )
    
    def _make_llm_decision(self, global_state, rule_set):
        """
        使用单次LLM调用进行智能工作流决策
        
        这是系统的核心决策方法，通过LLM分析当前状态和可用规则，
        决定下一步应该采取的行动：执行规则、生成新规则、或判断目标达成。
        
        决策过程包括：
        1. 分析当前状态和历史执行情况
        2. 评估所有可用规则的适用性
        3. 检查目标达成情况
        4. 做出最优决策并生成详细推理
        
        Args:
            global_state: 当前全局状态，包含状态描述、上下文变量和执行历史
            rule_set: 完整的规则集，包含所有可用的产生式规则
            
        Returns:
            DecisionResult: 决策结果，包含：
                - decision_type: 决策类型（执行规则/生成规则/目标达成/失败）
                - selected_rule: 如果是执行决策，包含选中的规则
                - new_rules: 如果是生成决策，包含新生成的规则
                - confidence: 决策置信度 (0.0-1.0)
                - reasoning: 详细的决策推理过程
                - context: 决策上下文信息
        
        Raises:
            Exception: 当LLM调用失败或解析结果异常时
        """
        try:
            # 准备决策所需的所有信息
            rules_info = self._format_rules_for_decision(rule_set.rules)
            available_agents = self._get_available_agents_for_decision(global_state)
            
            # 构建综合决策prompt
            decision_prompt = f"""
你是一个产生式规则工作流决策引擎。请根据当前状态和可用规则，做出最佳决策。

## 当前状态
目标: {rule_set.goal}
当前状态: {global_state.state}
迭代次数: {global_state.iteration_count}
执行历史: {chr(10).join(global_state.execution_history[-3:]) if global_state.execution_history else '无'}
上下文变量: {global_state.context_variables}

## 可用规则
{rules_info}

## 可用智能体
{available_agents}

## 双维度智能体选择策略
为任务选择最合适的智能体时，请综合考虑：

**维度一：能力匹配（权重60%）**
- 基于智能体的api_specification分析能力匹配度
- 判断智能体是否具备执行任务的能力

**维度二：数据亲和性（权重40%）**
- 从执行历史分析智能体的数据处理经验
- 从上下文变量推断当前数据流向和智能体的数据处理偏好

## 决策指南
1. **优先考虑现有规则**: 如果有规则的条件与当前状态匹配，应该选择最合适的规则执行
2. **生成新规则**: 如果没有现有规则适用，且可以通过新规则推进目标完成，则生成新规则
3. **目标失败**: 如果无法通过现有规则或新规则继续推进，则判断目标失败

如果没有智能体同时满足两个维度，选择能力匹配的智能体并在执行指令中包含数据传输说明。

请严格按照以下JSON格式返回决策：

```json
{{
  "decision_type": "EXECUTE_SELECTED_RULE | ADD_RULE | GOAL_FAILED",
  "selected_rule_id": "规则ID（仅当decision_type为EXECUTE_SELECTED_RULE时）",
  "confidence": 0.0-1.0之间的数字,
  "reasoning": "决策理由的详细说明",
  "new_rules": [
    {{
      "rule_name": "新规则名称",
      "trigger_condition": "触发条件（IF部分）",
      "action": "执行动作（THEN部分）", 
      "agent_name": "智能体名称",
      "execution_phase": "information_gathering|execution|verification",
      "priority": 1-100的数字,
      "expected_result": "期望结果描述"
    }}
  ]
}}
```

**重要说明**:
- 如果decision_type为EXECUTE_SELECTED_RULE，则new_rules应为空数组
- 如果decision_type为ADD_RULE，则selected_rule_id应为null，new_rules包含生成的规则
- 如果decision_type为GOAL_FAILED，则selected_rule_id为null，new_rules为空数组
- 新规则的agent_name必须从可用智能体列表中选择
- 优先级: 收集阶段(90-100) > 执行阶段(70-89) > 验证阶段(50-69)

请分析当前情况并返回最佳决策。
"""

            # 调用LLM获取决策
            response = self.llm_service.generate_natural_language_response(decision_prompt)
            decision_data = self.llm_service._parse_json_response(response)
            
            # 解析决策结果
            decision_result = self._parse_llm_decision(decision_data, rule_set)
            
            # 使用红色字体打印决策信息
            self._print_decision_in_red(decision_result, decision_data)
            
            return decision_result
            
        except Exception as e:
            logger.error(f"LLM决策失败: {e}")
            # 回退到目标失败
            return DecisionResult(
                selected_rule=None,
                decision_type=DecisionType.GOAL_FAILED,
                confidence=0.0,
                reasoning=f"LLM决策失败: {str(e)}"
            )
    
    def _format_rules_for_decision(self, rules) -> str:
        """
        格式化规则信息供决策使用
        
        Args:
            rules: 规则列表
            
        Returns:
            str: 格式化的规则信息
        """
        if not rules:
            return "无可用规则"
        
        formatted_rules = []
        for rule in rules:
            rule_info = f"""
规则ID: {rule.id}
名称: {rule.name}
条件: {rule.condition}
动作: {rule.action}
阶段: {rule.phase.value}
优先级: {rule.priority}
智能体: {rule.agent_name}
期望结果: {rule.expected_outcome}
"""
            formatted_rules.append(rule_info.strip())
        
        return "\n\n".join(formatted_rules)
    
    def _get_available_agents_for_decision(self, global_state: GlobalState) -> str:
        """
        获取可用的智能体信息，包含双维度分析数据
        
        Args:
            global_state: 全局状态，用于分析数据亲和性
        
        Returns:
            str: 格式化的智能体信息，包含能力和历史分析
        """
        try:
            # 从智能体注册表获取智能体
            if hasattr(self, '_current_agent_registry') and self._current_agent_registry:
                agents_list = self._current_agent_registry.list_all_agents()
                if agents_list:
                    agent_info = []
                    for name, agent in agents_list:
                        # 获取智能体能力描述
                        specification = getattr(agent, 'api_specification', f'{name} Agent')
                        
                        # 分析数据亲和性（从执行历史中分析该智能体的使用情况）
                        data_affinity = self._analyze_agent_data_affinity(name, global_state)
                        
                        agent_info.append(f"""
- {name}: {specification}
  数据亲和性: {data_affinity}""")
                    return "\n".join(agent_info)
            
            # 默认智能体列表（如果没有注册表）
            return """
- coder: 代码专家，擅长编写、调试和优化代码。支持多种编程语言，特别是Python。
  数据亲和性: 代码文件、编程任务
- tester: 测试专家，擅长编写测试用例和验证代码质量。熟悉各种测试框架和测试策略。
  数据亲和性: 测试文件、质量验证任务
"""
        except Exception as e:
            logger.error(f"获取智能体信息失败: {e}")
            return "coder, tester"
    
    def _analyze_agent_data_affinity(self, agent_name: str, global_state: GlobalState) -> str:
        """
        分析智能体的数据亲和性
        
        Args:
            agent_name: 智能体名称
            global_state: 全局状态
            
        Returns:
            str: 数据亲和性分析结果
        """
        try:
            # 从执行历史中查找该智能体的使用记录
            agent_history = []
            for history_item in global_state.execution_history:
                if agent_name in history_item:
                    agent_history.append(history_item)
            
            if agent_history:
                # 基于历史记录分析数据类型偏好
                recent_tasks = agent_history[-3:]  # 最近3次使用
                task_types = []
                for task in recent_tasks:
                    if '文件' in task or '代码' in task:
                        task_types.append('文件处理')
                    elif '测试' in task or '验证' in task:
                        task_types.append('质量验证')
                    elif '分析' in task or '设计' in task:
                        task_types.append('需求分析')
                
                if task_types:
                    return f"经验: {', '.join(set(task_types))}"
            
            # 如果没有历史记录，基于名称推断
            if 'coder' in agent_name.lower() or 'code' in agent_name.lower():
                return "适合: 代码编写、文件操作"
            elif 'test' in agent_name.lower():
                return "适合: 测试验证、质量检查"
            elif 'analyst' in agent_name.lower():
                return "适合: 需求分析、技术评估"
            else:
                return "通用任务处理"
                
        except Exception as e:
            logger.error(f"数据亲和性分析失败: {e}")
            return "数据分析暂不可用"
    
    def _parse_llm_decision(self, decision_data, rule_set):
        """
        解析LLM决策结果
        
        Args:
            decision_data: LLM返回的决策数据
            rule_set: 规则集
            
        Returns:
            DecisionResult: 解析后的决策结果
        """
        try:
            decision_type_str = decision_data.get('decision_type', 'GOAL_FAILED')
            confidence = float(decision_data.get('confidence', 0.0))
            reasoning = decision_data.get('reasoning', '无决策理由')
            
            # 解析决策类型
            if decision_type_str == 'EXECUTE_SELECTED_RULE':
                selected_rule_id = decision_data.get('selected_rule_id')
                if selected_rule_id:
                    # 查找对应的规则
                    selected_rule = None
                    for rule in rule_set.rules:
                        if rule.id == selected_rule_id:
                            selected_rule = rule
                            break
                    
                    if selected_rule:
                        logger.info(f"LLM决策：执行规则 {selected_rule.name}")
                        return DecisionResult(
                            selected_rule=selected_rule,
                            decision_type=DecisionType.EXECUTE_SELECTED_RULE,
                            confidence=confidence,
                            reasoning=reasoning
                        )
                
                # 如果没找到规则，回退到目标失败
                return DecisionResult(
                    selected_rule=None,
                    decision_type=DecisionType.GOAL_FAILED,
                    confidence=0.3,
                    reasoning=f"指定的规则ID {selected_rule_id} 不存在"
                )
            
            elif decision_type_str == 'ADD_RULE':
                # 解析新规则
                new_rules_data = decision_data.get('new_rules', [])
                new_rules = []
                
                for rule_data in new_rules_data:
                    try:
                        new_rule = self._create_rule_from_data(rule_data)
                        if new_rule:
                            new_rules.append(new_rule)
                    except Exception as e:
                        logger.warning(f"创建新规则失败: {e}")
                        continue
                
                logger.info(f"LLM决策：生成 {len(new_rules)} 个新规则")
                return DecisionResult(
                    selected_rule=None,
                    decision_type=DecisionType.ADD_RULE,
                    confidence=confidence,
                    reasoning=reasoning,
                    new_rules=new_rules
                )
            
            else:  # GOAL_FAILED
                logger.warning("LLM决策：目标失败")
                return DecisionResult(
                    selected_rule=None,
                    decision_type=DecisionType.GOAL_FAILED,
                    confidence=confidence,
                    reasoning=reasoning
                )
                
        except Exception as e:
            logger.error(f"解析LLM决策失败: {e}")
            return DecisionResult(
                selected_rule=None,
                decision_type=DecisionType.GOAL_FAILED,
                confidence=0.0,
                reasoning=f"决策解析失败: {str(e)}"
            )
    
    def _print_decision_in_red(self, decision_result, decision_data) -> None:
        """
        使用红色字体打印LLM决策信息
        
        Args:
            decision_result: 解析后的决策结果
            decision_data: 原始决策数据
        """
        # ANSI红色字体代码
        RED = '\033[91m'
        BOLD = '\033[1m'
        RESET = '\033[0m'
        
        try:
            print(f"\n{RED}{BOLD}🤖 LLM决策引擎 - 决策结果{RESET}")
            print(f"{RED}{'=' * 50}{RESET}")
            
            # 打印决策类型
            decision_type = decision_data.get('decision_type', 'UNKNOWN')
            print(f"{RED}{BOLD}📋 决策类型:{RESET} {RED}{decision_type}{RESET}")
            
            # 打印置信度
            confidence = decision_data.get('confidence', 0.0)
            print(f"{RED}{BOLD}🎯 置信度:{RESET} {RED}{confidence:.2f}{RESET}")
            
            # 打印决策理由
            reasoning = decision_data.get('reasoning', '无理由说明')
            print(f"{RED}{BOLD}💭 决策理由:{RESET}")
            print(f"{RED}   {reasoning}{RESET}")
            
            # 根据决策类型打印不同的详细信息
            if decision_type == 'EXECUTE_SELECTED_RULE':
                selected_rule_id = decision_data.get('selected_rule_id')
                if selected_rule_id and decision_result.selected_rule:
                    print(f"{RED}{BOLD}⚡ 选择的规则:{RESET}")
                    print(f"{RED}   ID: {selected_rule_id}{RESET}")
                    print(f"{RED}   名称: {decision_result.selected_rule.name}{RESET}")
                    print(f"{RED}   条件: {decision_result.selected_rule.condition[:60]}...{RESET}")
                    print(f"{RED}   动作: {decision_result.selected_rule.action[:60]}...{RESET}")
                
            elif decision_type == 'ADD_RULE':
                new_rules = decision_data.get('new_rules', [])
                print(f"{RED}{BOLD}📝 生成新规则数量:{RESET} {RED}{len(new_rules)}{RESET}")
                for i, rule_data in enumerate(new_rules[:2]):  # 最多显示前2个规则
                    print(f"{RED}   规则 {i+1}:{RESET}")
                    print(f"{RED}     名称: {rule_data.get('rule_name', 'Unknown')}{RESET}")
                    print(f"{RED}     条件: {rule_data.get('trigger_condition', 'Unknown')[:50]}...{RESET}")
                    print(f"{RED}     动作: {rule_data.get('action', 'Unknown')[:50]}...{RESET}")
                if len(new_rules) > 2:
                    print(f"{RED}   ... 还有 {len(new_rules) - 2} 个规则{RESET}")
                
            elif decision_type == 'GOAL_FAILED':
                print(f"{RED}{BOLD}❌ 目标执行失败{RESET}")
                print(f"{RED}   系统判断无法继续推进目标完成{RESET}")
            
            print(f"{RED}{'=' * 50}{RESET}\n")
            
        except Exception as e:
            # 如果打印失败，至少记录到日志
            logger.error(f"红色决策打印失败: {e}")
            # 简单的备用打印
            print(f"\n🤖 LLM决策: {decision_result.get_decision_summary()}")
            print(f"置信度: {decision_result.confidence:.2f}")
            print(f"理由: {decision_result.reasoning}\n")