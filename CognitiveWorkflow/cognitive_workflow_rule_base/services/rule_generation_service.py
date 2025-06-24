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

from ..domain.entities import ProductionRule, RuleSet, AgentRegistry, AgentCapability
from ..domain.value_objects import RulePhase, RuleSetStatus, RuleConstants
from .language_model_service import LanguageModelService

logger = logging.getLogger(__name__)


class RuleGenerationService:
    """规则生成服务 - 专注于智能规则创建"""
    
    def __init__(self, llm_service: LanguageModelService):
        """
        初始化规则生成服务
        
        Args:
            llm_service: 语言模型服务
        """
        self.llm_service = llm_service
        
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
            
            # 获取可用的智能体能力
            available_capabilities = agent_registry.list_all_capabilities()
            capabilities_desc = self._format_capabilities(available_capabilities)
            
            # 生成规则
            rules = self._generate_initial_rules(goal, capabilities_desc)
            
            # 创建规则集
            rule_set = RuleSet(
                id=str(uuid.uuid4()),
                goal=goal,
                rules=rules,
                status=RuleSetStatus.ACTIVE
            )
            
            logger.info(f"规则集生成完成，包含 {len(rules)} 个规则")
            return rule_set
            
        except Exception as e:
            logger.error(f"规则集生成失败: {e}")
            # 返回一个基本的规则集
            return self._create_fallback_rule_set(goal, agent_registry)
    
    def generate_recovery_rules(self, failure_context: Dict[str, Any]) -> List[ProductionRule]:
        """
        生成错误恢复规则（技术修复规则）
        
        Args:
            failure_context: 失败上下文信息
            
        Returns:
            List[ProductionRule]: 恢复规则列表
        """
        try:
            logger.info("开始生成错误恢复规则")
            
            # 分析失败原因
            failure_analysis = self._analyze_failure(failure_context)
            
            # 生成恢复策略
            recovery_rules = self._generate_technical_recovery_rules(failure_analysis)
            
            logger.info(f"生成了 {len(recovery_rules)} 个恢复规则")
            return recovery_rules
            
        except Exception as e:
            logger.error(f"恢复规则生成失败: {e}")
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
                agent_capability_id=rule.agent_capability_id,
                priority=rule.priority,
                phase=rule.phase,
                expected_outcome=detailed_outcome,
                created_at=rule.created_at,
                updated_at=datetime.now(),
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
    
    def _generate_initial_rules(self, goal: str, capabilities_desc: str) -> List[ProductionRule]:
        """
        生成初始规则
        
        Args:
            goal: 目标描述
            capabilities_desc: 可用能力描述
            
        Returns:
            List[ProductionRule]: 生成的规则列表
        """
        prompt = f"""
请为以下目标生成一套完整的产生式规则：

目标: {goal}

可用的智能体能力:
{capabilities_desc}

请生成6-10个产生式规则，覆盖完整的执行流程。每个规则需要包含：
1. 规则名称
2. 触发条件（IF部分，自然语言描述）
3. 执行动作（THEN部分，自然语言指令）
4. 适用的智能体能力ID
5. 执行阶段（information_gathering/problem_solving/verification/cleanup）
6. 优先级（1-100）
7. 期望结果

请确保规则：
- 覆盖从信息收集到最终验证的完整流程
- 条件描述清晰，便于语义匹配
- 动作指令具体，便于智能体执行
- 优先级合理，重要规则优先级更高

请以JSON格式返回规则列表。
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
            
            # 如果生成失败，创建基础规则
            if not rules:
                rules = self._create_basic_rules(goal)
            
            return rules
            
        except Exception as e:
            logger.error(f"初始规则生成失败: {e}")
            return self._create_basic_rules(goal)
    
    def _create_rule_from_data(self, rule_data: Dict[str, Any]) -> Optional[ProductionRule]:
        """
        从数据字典创建规则
        
        Args:
            rule_data: 规则数据字典
            
        Returns:
            Optional[ProductionRule]: 创建的规则，失败时返回None
        """
        try:
            # 解析阶段
            phase_str = rule_data.get('phase', 'problem_solving')
            try:
                phase = RulePhase(phase_str)
            except ValueError:
                phase = RulePhase.PROBLEM_SOLVING
            
            # 创建规则
            rule = ProductionRule(
                id=str(uuid.uuid4()),
                name=rule_data.get('name', '未命名规则'),
                condition=rule_data.get('condition', ''),
                action=rule_data.get('action', ''),
                agent_capability_id=rule_data.get('agent_capability_id', ''),
                priority=int(rule_data.get('priority', RuleConstants.DEFAULT_RULE_PRIORITY)),
                phase=phase,
                expected_outcome=rule_data.get('expected_outcome', '')
            )
            
            return rule
            
        except Exception as e:
            logger.error(f"规则创建失败: {e}, 数据: {rule_data}")
            return None
    
    def _create_basic_rules(self, goal: str) -> List[ProductionRule]:
        """
        创建基础规则集合
        
        Args:
            goal: 目标描述
            
        Returns:
            List[ProductionRule]: 基础规则列表
        """
        basic_rules = [
            {
                'name': '分析目标需求',
                'condition': f'需要分析目标：{goal}',
                'action': f'分析目标"{goal}"的具体需求和实现步骤',
                'agent_capability_id': 'analyst',
                'phase': RulePhase.INFORMATION_GATHERING,
                'priority': 90,
                'expected_outcome': '明确的需求分析和实现计划'
            },
            {
                'name': '执行主要任务',
                'condition': '需求分析已完成，可以开始实现',
                'action': '根据需求分析结果，执行主要的实现任务',
                'agent_capability_id': 'coder',
                'phase': RulePhase.PROBLEM_SOLVING,
                'priority': 80,
                'expected_outcome': '完成主要功能实现'
            },
            {
                'name': '验证结果',
                'condition': '主要任务已完成，需要验证结果',
                'action': '验证实现结果是否满足目标要求',
                'agent_capability_id': 'tester',
                'phase': RulePhase.VERIFICATION,
                'priority': 70,
                'expected_outcome': '确认结果符合预期'
            }
        ]
        
        rules = []
        for rule_data in basic_rules:
            rule = ProductionRule(
                id=str(uuid.uuid4()),
                name=rule_data['name'],
                condition=rule_data['condition'],
                action=rule_data['action'],
                agent_capability_id=rule_data['agent_capability_id'],
                priority=rule_data['priority'],
                phase=rule_data['phase'],
                expected_outcome=rule_data['expected_outcome']
            )
            rules.append(rule)
        
        return rules
    
    def _format_capabilities(self, capabilities: List[AgentCapability]) -> str:
        """
        格式化智能体能力描述
        
        Args:
            capabilities: 智能体能力列表
            
        Returns:
            str: 格式化的能力描述
        """
        if not capabilities:
            return "无可用智能体能力"
        
        formatted_lines = []
        for cap in capabilities:
            actions_str = ', '.join(cap.supported_actions[:5])  # 只显示前5个动作
            if len(cap.supported_actions) > 5:
                actions_str += '...'
            
            formatted_lines.append(
                f"- {cap.id}: {cap.name} - {cap.description}\n"
                f"  支持的动作: {actions_str}"
            )
        
        return '\n'.join(formatted_lines)
    
    def _analyze_failure(self, failure_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析失败原因
        
        Args:
            failure_context: 失败上下文
            
        Returns:
            Dict[str, Any]: 失败分析结果
        """
        # 提取关键信息
        error_message = failure_context.get('error_message', '')
        failed_rule = failure_context.get('failed_rule', {})
        execution_context = failure_context.get('execution_context', {})
        
        # 基本分析
        analysis = {
            'error_type': self._classify_error_type(error_message),
            'failed_action': failed_rule.get('action', ''),
            'error_message': error_message,
            'context': execution_context,
            'suggested_fixes': []
        }
        
        return analysis
    
    def _classify_error_type(self, error_message: str) -> str:
        """
        分类错误类型
        
        Args:
            error_message: 错误消息
            
        Returns:
            str: 错误类型
        """
        error_message_lower = error_message.lower()
        
        if 'network' in error_message_lower or 'connection' in error_message_lower:
            return 'network_error'
        elif 'permission' in error_message_lower or 'access' in error_message_lower:
            return 'permission_error'
        elif 'file' in error_message_lower or 'directory' in error_message_lower:
            return 'file_system_error'
        elif 'timeout' in error_message_lower:
            return 'timeout_error'
        else:
            return 'general_error'
    
    def _generate_technical_recovery_rules(self, failure_analysis: Dict[str, Any]) -> List[ProductionRule]:
        """
        生成技术恢复规则
        
        Args:
            failure_analysis: 失败分析结果
            
        Returns:
            List[ProductionRule]: 恢复规则列表
        """
        recovery_rules = []
        error_type = failure_analysis.get('error_type', 'general_error')
        
        # 根据错误类型生成相应的恢复规则
        if error_type == 'network_error':
            rule = ProductionRule(
                id=str(uuid.uuid4()),
                name='网络错误恢复',
                condition='检测到网络连接错误',
                action='检查网络连接状态，尝试重新连接或使用备用网络',
                agent_capability_id='system',
                priority=95,
                phase=RulePhase.PROBLEM_SOLVING,
                expected_outcome='网络连接恢复正常'
            )
            recovery_rules.append(rule)
        
        elif error_type == 'permission_error':
            rule = ProductionRule(
                id=str(uuid.uuid4()),
                name='权限错误恢复',
                condition='检测到权限不足错误',
                action='检查并调整文件或系统权限，必要时请求管理员权限',
                agent_capability_id='system',
                priority=90,
                phase=RulePhase.PROBLEM_SOLVING,
                expected_outcome='获得必要的访问权限'
            )
            recovery_rules.append(rule)
        
        # 通用重试规则
        retry_rule = ProductionRule(
            id=str(uuid.uuid4()),
            name='重试失败操作',
            condition='上次操作失败且可以重试',
            action='重新执行失败的操作，使用更保守的参数',
            agent_capability_id='system',
            priority=60,
            phase=RulePhase.PROBLEM_SOLVING,
            expected_outcome='操作成功完成'
        )
        recovery_rules.append(retry_rule)
        
        return recovery_rules
    
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
        生成策略调整规则
        
        Args:
            goal_analysis: 目标分析结果
            
        Returns:
            List[ProductionRule]: 策略调整规则列表
        """
        strategy_rules = []
        
        # 生成重新规划规则
        replan_rule = ProductionRule(
            id=str(uuid.uuid4()),
            name='重新规划执行策略',
            condition='当前执行策略遇到重大障碍',
            action='分析当前障碍，重新制定更适合的执行策略',
            agent_capability_id='analyst',
            priority=85,
            phase=RulePhase.INFORMATION_GATHERING,
            expected_outcome='制定新的可行执行策略'
        )
        strategy_rules.append(replan_rule)
        
        # 生成简化目标规则
        simplify_rule = ProductionRule(
            id=str(uuid.uuid4()),
            name='简化目标范围',
            condition='原目标过于复杂难以实现',
            action='将复杂目标分解为更小、更可管理的子目标',
            agent_capability_id='analyst',
            priority=75,
            phase=RulePhase.INFORMATION_GATHERING,
            expected_outcome='确定简化后的可执行目标'
        )
        strategy_rules.append(simplify_rule)
        
        return strategy_rules
    
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
                agent_capability_id=rule.agent_capability_id,
                priority=rule.priority,
                phase=rule.phase,
                expected_outcome=rule.expected_outcome,
                created_at=rule.created_at,
                updated_at=datetime.now(),
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
        创建回退规则集
        
        Args:
            goal: 目标描述
            agent_registry: 智能体注册表
            
        Returns:
            RuleSet: 回退规则集
        """
        logger.warning("使用回退规则集")
        
        # 创建基础规则
        basic_rules = self._create_basic_rules(goal)
        
        # 修正智能体能力ID
        available_capabilities = agent_registry.list_all_capabilities()
        if available_capabilities:
            default_capability = available_capabilities[0].id
            for rule in basic_rules:
                if not rule.agent_capability_id or rule.agent_capability_id not in [cap.id for cap in available_capabilities]:
                    rule.agent_capability_id = default_capability
        
        return RuleSet(
            id=str(uuid.uuid4()),
            goal=goal,
            rules=basic_rules,
            status=RuleSetStatus.ACTIVE
        )