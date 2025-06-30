# -*- coding: utf-8 -*-
"""
团队协调器服务 (Team Orchestrator)

作为多智能体协作的指挥中心，负责接收高级目标，
协调团队中的CognitiveAgent共同完成任务。
"""

import logging
from typing import Dict, Any

from ..domain.entities import AgentRegistry, WorkflowExecutionResult, RuleSet
from ..domain.value_objects import DecisionType
from .cognitive_advisor import CognitiveAdvisor
from .state_service import StateService
from .rule_engine_service import RuleEngineService # 导入以获取类型提示

logger = logging.getLogger(__name__)

class TeamOrchestrator:
    """
    协调多个CognitiveAgent实例以完成复杂目标的顶层服务。
    """

    def __init__(self, agents: Dict[str, Any], llm: Any, state_service: StateService, rule_engine_service: RuleEngineService, agent_service: Any):
        """
        初始化团队协调器

        Args:
            agents: 一个包含所有CognitiveAgent实例的字典，键为agent_name。
            llm: 语言模型实例。
            state_service: 状态服务实例。
            rule_engine_service: 规则引擎服务实例。
        """
        self.team = agents
        self.state_service = state_service
        self.rule_engine_service = rule_engine_service
        self.agent_service = agent_service # 保存agent_service引用
        self.agent_registry = self._build_agent_registry()
        self.cognitive_advisor = CognitiveAdvisor(llm, self.agent_registry)
        logger.info(f"✅ TeamOrchestrator 初始化完成，管理 {len(self.team)} 个Agent。")

    def _build_agent_registry(self) -> AgentRegistry:
        """从团队字典构建AgentRegistry。"""
        registry = AgentRegistry()
        for name, agent in self.team.items():
            # 假设agent实例有api_specification属性
            registry.register_agent(name, agent.base_agent)
        return registry

    def execute_team_goal(self, goal: str) -> WorkflowExecutionResult:
        """
        执行一个需要多智能体协作的团队目标。

        Args:
            goal: 团队的宏观目标。

        Returns:
            WorkflowExecutionResult: 整个团队任务的最终执行结果。
        """
        logger.info(f"🚀 TeamOrchestrator 开始执行团队目标: {goal}")

        # 1. 获取计划
        plan_result = self.cognitive_advisor.plan_workflow(goal)
        rules_data = plan_result.get("rules", [])
        if not rules_data:
            logger.error("❌ 规划失败，CognitiveAdvisor未能生成任何规则。")
            return self._create_failure_result(goal, "规划失败，未能生成规则。")
        
        # 注意：这里的RuleSet是临时的，只用于持有规则列表
        rule_set = RuleSet(id="plan_set", goal=goal, rules=[self.rule_engine_service.rule_generation._create_rule_from_data(r) for r in rules_data])

        # 2. 初始化全局状态
        workflow_id = self.rule_engine_service._workflow_id or "team_workflow"
        global_state = self.state_service.create_initial_state(goal, workflow_id)

        # 3. 开始主执行循环
        while not global_state.goal_achieved and global_state.iteration_count < self.rule_engine_service.max_iterations:
            print(f"\n{'='*20} TeamOrchestrator Loop: Iteration {global_state.iteration_count + 1} {'='*20}")
            
            # a. 决策：选择下一个要执行的规则
            # 注意：这里的决策逻辑可以更复杂，甚至可以再次调用CognitiveAdvisor
            decision = self.cognitive_advisor.make_decision(global_state.to_dict(), [r.to_dict() for r in rule_set.rules])
            
            if decision.get('decision', {}).get('type') == 'GOAL_ACHIEVED':
                global_state.goal_achieved = True
                logger.info("✅ 目标已达成（由CognitiveAdvisor判断）。")
                break

            if decision.get('decision', {}).get('type') != 'EXECUTE_SELECTED_RULE':
                logger.warning(f"🚦 决策不是执行规则，而是 {decision.get('decision', {}).get('type')}。工作流暂停。")
                break

            selected_rule_id = decision.get('decision', {}).get('selected_rule_id')
            rule_to_execute = next((r for r in rule_set.rules if r.id == selected_rule_id), None)

            if not rule_to_execute:
                logger.error(f"❌ 找不到ID为 {selected_rule_id} 的规则，工作流终止。")
                break

            # b. 找到对应的Agent
            agent_name = rule_to_execute.agent_name
            target_agent = self.team.get(agent_name)

            if not target_agent:
                logger.error(f"❌ 找不到名为 {agent_name} 的Agent，工作流终止。")
                break

            # c. 分发并执行任务
            logger.info(f" delegating task '{rule_to_execute.name}' to {agent_name}")
            raw_execution_result = target_agent.execute_instruction_syn(rule_to_execute.action)
            execution_result = self.agent_service._convert_to_result(raw_execution_result, rule_to_execute.action)

            # d. 更新全局状态
            global_state = self.state_service.update_state(execution_result, global_state, goal)

            print(f"{'-'*20} Iteration {global_state.iteration_count} End {'-'*20}")
            print(f"[INFO] Executed Rule: {rule_to_execute.name}")
            print(f"[INFO] Agent: {agent_name}")
            print(f"[INFO] New State: {global_state.state[:100]}...")
            print(f"[INFO] Goal Achieved: {global_state.goal_achieved}")

        # 4. 返回最终结果
        return self._create_final_result(global_state, goal)

    def _create_failure_result(self, goal: str, message: str) -> WorkflowExecutionResult:
        """创建一个表示失败的WorkflowExecutionResult。"""
        from ..domain.value_objects import ExecutionMetrics
        return WorkflowExecutionResult(
            goal=goal,
            is_successful=False,
            final_state=message,
            total_iterations=0,
            execution_metrics=ExecutionMetrics(0, 0, 1, 0.0, 0.0, 0.0),
            final_message=message,
            completion_timestamp=__import__('datetime').datetime.now()
        )

    def _create_final_result(self, state: Any, goal: str) -> WorkflowExecutionResult:
        """根据最终状态创建WorkflowExecutionResult。"""
        from ..domain.value_objects import ExecutionMetrics
        metrics = self.rule_engine_service._calculate_execution_metrics(state.workflow_id)
        return WorkflowExecutionResult(
            goal=goal,
            is_successful=state.goal_achieved,
            final_state=state.state,
            total_iterations=state.iteration_count,
            execution_metrics=metrics,
            final_message="Workflow completed successfully." if state.goal_achieved else "Workflow failed or was terminated.",
            completion_timestamp=__import__('datetime').datetime.now()
        )
