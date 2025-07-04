#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ResourceManager测试示例

演示如何使用ResourceManager进行智能体的动态分配，展示类型层与实例层的分离架构。
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from datetime import datetime
from typing import Dict, Any

# 导入领域实体
from CognitiveWorkflow.cognitive_workflow_rule_base.domain.entities import (
    ProductionRule, 
    RuleSet,
    RuleSetExecution,
    GlobalState,
    AgentRegistry
)
from CognitiveWorkflow.cognitive_workflow_rule_base.domain.value_objects import (
    RulePhase,
    RuleSetStatus,
    ExecutionStatus
)

# 导入服务
from CognitiveWorkflow.cognitive_workflow_rule_base.services.core import (
    ResourceManager,
    LanguageModelService,
    AgentService
)

# 导入基础智能体
from agent_base import AgentBase


class CalculatorAgent(AgentBase):
    """计算器智能体示例"""
    
    def __init__(self, llm):
        super().__init__(name="CalculatorAgent", llm=llm)
        self.api_specification = "数学计算智能体，能够处理各种数学运算和公式计算"
    
    def execute_sync(self, instruction: str) -> str:
        """执行计算任务"""
        try:
            # 简单的计算示例
            if "计算" in instruction:
                # 这里可以使用eval或更安全的计算库
                return f"计算结果: [模拟计算结果]"
            return f"执行了计算任务: {instruction}"
        except Exception as e:
            return f"计算失败: {str(e)}"


class DataAnalyzer(AgentBase):
    """数据分析智能体示例"""
    
    def __init__(self, llm):
        super().__init__(name="DataAnalyzer", llm=llm)
        self.api_specification = "数据分析智能体，擅长数据统计、趋势分析和报告生成"
    
    def execute_sync(self, instruction: str) -> str:
        """执行数据分析任务"""
        return f"执行了数据分析任务: {instruction}"


class ReportGenerator(AgentBase):
    """报告生成智能体示例"""
    
    def __init__(self, llm):
        super().__init__(name="ReportGenerator", llm=llm)
        self.api_specification = "报告生成智能体，能够生成各种格式的专业报告和文档"
    
    def execute_sync(self, instruction: str) -> str:
        """执行报告生成任务"""
        return f"生成了报告: {instruction}"


class MockLanguageModelService(LanguageModelService):
    """模拟的语言模型服务"""
    
    def invoke(self, prompt: str) -> str:
        """模拟LLM响应"""
        # 模拟智能分配决策
        if "计算" in prompt or "加法" in prompt or "数学" in prompt:
            return '''
            {
                "agent_name": "CalculatorAgent",
                "confidence": 0.95,
                "reasoning": "该任务涉及数学计算，CalculatorAgent是专门的数学计算智能体"
            }
            '''
        elif "分析" in prompt or "统计" in prompt:
            return '''
            {
                "agent_name": "DataAnalyzer",
                "confidence": 0.92,
                "reasoning": "该任务需要数据分析能力，DataAnalyzer擅长数据统计和分析"
            }
            '''
        elif "报告" in prompt or "文档" in prompt:
            return '''
            {
                "agent_name": "ReportGenerator",
                "confidence": 0.90,
                "reasoning": "该任务需要生成报告，ReportGenerator专门负责报告生成"
            }
            '''
        else:
            # 默认返回第一个可用的智能体
            return '''
            {
                "agent_name": "CalculatorAgent",
                "confidence": 0.60,
                "reasoning": "没有找到明确匹配的智能体，使用默认的CalculatorAgent"
            }
            '''


def demonstrate_resource_manager():
    """演示ResourceManager的使用"""
    
    print("=== ResourceManager 智能体动态分配演示 ===\n")
    
    # 1. 创建模拟的LLM服务
    llm_service = MockLanguageModelService(
        llm=None,  # 在实际使用中应该传入真实的LLM
        system_prompt="你是一个智能资源分配器"
    )
    
    # 2. 创建智能体注册表并注册智能体
    agent_registry = AgentRegistry()
    
    # 创建并注册智能体实例
    calculator = CalculatorAgent(llm=None)
    analyzer = DataAnalyzer(llm=None)
    generator = ReportGenerator(llm=None)
    
    agent_registry.register_agent("CalculatorAgent", calculator)
    agent_registry.register_agent("DataAnalyzer", analyzer)
    agent_registry.register_agent("ReportGenerator", generator)
    
    print("已注册的智能体:")
    for name, spec in agent_registry.get_agent_specifications().items():
        print(f"  - {name}: {spec}")
    print()
    
    # 3. 创建ResourceManager
    resource_manager = ResourceManager(
        agent_registry=agent_registry,
        llm_service=llm_service
    )
    
    # 4. 创建规则集（类型层）
    rule_set = RuleSet(
        id="sales_analysis_ruleset",
        goal="分析销售数据并生成月度报告"
    )
    
    # 创建规则（注意：没有agent_name字段）
    rules = [
        ProductionRule(
            id="rule_001",
            name="计算销售总额",
            condition="当需要统计销售数据时",
            action="计算所有产品的销售总额",
            expected_outcome="得到本月销售总额",
            priority=100,
            phase=RulePhase.EXECUTION
        ),
        ProductionRule(
            id="rule_002", 
            name="分析销售趋势",
            condition="当销售总额计算完成时",
            action="分析销售数据的趋势和模式",
            expected_outcome="识别出销售趋势",
            priority=90,
            phase=RulePhase.EXECUTION
        ),
        ProductionRule(
            id="rule_003",
            name="生成月度报告",
            condition="当销售分析完成时",
            action="生成包含销售数据和分析的月度报告",
            expected_outcome="生成完整的月度销售报告",
            priority=80,
            phase=RulePhase.EXECUTION
        )
    ]
    
    for rule in rules:
        rule_set.add_rule(rule)
    
    # 5. 创建全局状态
    global_state = GlobalState(
        id="state_001",
        state="准备开始销售数据分析",
        workflow_id="sales_workflow_001"
    )
    
    # 6. 创建规则集执行实例（实例层）
    rule_set_execution = RuleSetExecution(
        id=f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        rule_set_id=rule_set.id,
        global_state=global_state,
        context={'goal': rule_set.goal}
    )
    
    print(f"创建规则集执行实例: {rule_set_execution.id}")
    print(f"工作流目标: {rule_set.goal}\n")
    
    # 7. 演示智能体分配
    print("=== 开始智能体分配 ===\n")
    
    for rule in rules:
        print(f"处理规则: {rule.name}")
        print(f"  条件: {rule.condition}")
        print(f"  动作: {rule.action}")
        
        # 使用ResourceManager创建规则执行实例
        try:
            rule_execution = resource_manager.create_rule_execution(
                rule=rule,
                rule_set_execution=rule_set_execution
            )
            
            print(f"  分配的智能体: {rule_execution.assigned_agent}")
            print(f"  执行ID: {rule_execution.id}")
            
            # 将执行实例添加到规则集执行中
            rule_set_execution.add_rule_execution(rule_execution)
            
            # 模拟执行
            assigned_agent = agent_registry.get_agent(rule_execution.assigned_agent)
            result = assigned_agent.execute_sync(rule.action)
            print(f"  执行结果: {result}")
            
        except Exception as e:
            print(f"  分配失败: {str(e)}")
        
        print()
    
    # 8. 展示执行统计
    print("=== 执行统计 ===")
    print(f"总规则数: {len(rules)}")
    print(f"已执行规则数: {len(rule_set_execution.rule_executions)}")
    
    # 统计每个智能体的使用情况
    agent_usage = {}
    for exec in rule_set_execution.rule_executions:
        agent = exec.assigned_agent
        agent_usage[agent] = agent_usage.get(agent, 0) + 1
    
    print("\n智能体使用统计:")
    for agent, count in agent_usage.items():
        print(f"  - {agent}: {count} 次")
    
    # 9. 标记执行完成
    rule_set_execution.mark_completed(success=True)
    print(f"\n规则集执行状态: {rule_set_execution.status.value}")
    
    print("\n=== 演示完成 ===")


def demonstrate_fallback_allocation():
    """演示后备分配策略"""
    
    print("\n=== 后备分配策略演示 ===\n")
    
    # 创建一个会失败的LLM服务来触发后备策略
    class FailingLLMService(LanguageModelService):
        def invoke(self, prompt: str) -> str:
            # 返回无效的JSON来触发后备策略
            return "Invalid response"
    
    llm_service = FailingLLMService(llm=None, system_prompt="")
    
    # 创建智能体注册表
    agent_registry = AgentRegistry()
    agent_registry.register_agent("CalculatorAgent", CalculatorAgent(llm=None))
    agent_registry.register_agent("WriterAgent", None)  # 模拟WriterAgent
    
    # 创建ResourceManager
    resource_manager = ResourceManager(
        agent_registry=agent_registry,
        llm_service=llm_service
    )
    
    # 创建测试规则
    test_rules = [
        ProductionRule(
            id="test_001",
            name="计算任务",
            condition="需要计算时",
            action="calculate the sum of numbers",  # 包含关键词 'calculate'
            expected_outcome="得到计算结果"
        ),
        ProductionRule(
            id="test_002",
            name="写作任务", 
            condition="需要写作时",
            action="write a report about sales",  # 包含关键词 'write'
            expected_outcome="生成报告",
            metadata={'suggested_agent': 'WriterAgent'}  # 元数据中的建议
        ),
        ProductionRule(
            id="test_003",
            name="通用任务",
            condition="其他情况",
            action="perform a general task",  # 没有明确关键词
            expected_outcome="完成任务"
        )
    ]
    
    # 创建执行上下文
    global_state = GlobalState(
        id="state_fallback",
        state="测试后备分配"
    )
    
    rule_set_execution = RuleSetExecution(
        id="exec_fallback",
        rule_set_id="test_ruleset",
        global_state=global_state
    )
    
    print("测试后备分配策略:")
    for rule in test_rules:
        print(f"\n规则: {rule.name}")
        print(f"动作: {rule.action}")
        
        allocated = resource_manager.allocate_agent_for_rule(
            rule=rule,
            rule_set_execution=rule_set_execution
        )
        
        print(f"分配结果: {allocated}")


if __name__ == "__main__":
    # 运行主要演示
    demonstrate_resource_manager()
    
    # 运行后备策略演示
    demonstrate_fallback_allocation()