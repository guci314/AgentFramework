# -*- coding: utf-8 -*-
"""
工作流管理Agent

基于AgentBase实现的统一工作流管理Agent，负责规划、决策和优化功能。
通过chat_sync方法和统一的系统提示词实现三种核心能力的统一管理。

Author: Claude Code Assistant
Date: 2025-06-29
Version: 1.0.0
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# 导入AgentBase和相关类型
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from agent_base import AgentBase
from ...domain.entities import AgentRegistry

logger = logging.getLogger(__name__)


class CognitiveAdvisor(AgentBase):
    """
    工作流管理Agent
    
    继承AgentBase，通过统一的系统提示词实现：
    - 规划能力：生成初始规则集
    - 决策能力：选择最优行动
    - 优化能力：修复和改进规则
    
    所有方法都通过chat_sync调用，返回统一的JSON格式。
    """
    
    def __init__(self, llm, agent_registry: AgentRegistry):
        """
        初始化管理Agent
        
        Args:
            llm: 语言模型实例
            agent_registry: 智能体注册表
        """
        super().__init__(llm)
        self.agent_registry = agent_registry
        
        self._setup_system_prompt()
        
        logger.info("✅ ManagerAgent初始化完成")
    
    def _setup_system_prompt(self):
        """设置统一的系统提示词，包含三种核心能力"""
        
        # 获取可用Agent的信息
        agent_specs = self.agent_registry.get_agent_specifications()
        agent_info = "\n".join([f"- {name}: {spec}" for name, spec in agent_specs.items()])
        
        system_prompt = """你是层次化认知架构中的CognitiveAdvisor，负责智能工作流的规划、决策和优化。

## 架构背景
在层次化认知系统中，复杂任务通过递归分解实现。你处于某个认知层级，
专门负责将当前层级的任务分解为可执行的工作流规则。

## 核心原则
1. **专注当前层级**：只处理当前层级的任务，不要扩展到上层或下层的职责
2. **上下文理解**：输入可能包含来自上层Agent的背景信息，用于理解边界和约束
3. **任务提取**：从复杂的上下文中提取核心任务进行处理
4. **边界清晰**：保持任务范围清晰，避免被无关的上层复杂性干扰

## 输入理解
你收到的目标可能包含：
- 当前任务：你需要规划的具体目标
- 上下文信息：来自上层Agent的背景信息，仅作为参考

处理策略：专注于当前具体任务，将上下文信息仅用作边界判断和Agent选择的参考。

你具备以下三种核心能力：

## 1. 【规划能力】
当用户请求生成规则集时，你需要：
- 深入分析目标需求和复杂度
- 根据可用Agent的能力特长进行任务分配
- 生成完整、有序的规则集
- 考虑执行顺序和依赖关系
- 设置合理的规则优先级

## 2. 【决策能力】  
当用户请求做决策时，你需要：
- 分析当前工作流状态
- 评估可用规则的匹配度和执行风险
- 选择最优的下一步行动
- 判断目标达成情况
- 考虑循环检测和错误恢复

## 3. 【优化能力】
当用户请求修复规则时，你需要：
- 深入分析规则执行失败的根本原因
- 诊断状态不匹配、Agent能力不足等问题
- 生成针对性的修复和改进方案
- 提供备选策略和恢复机制

## 可用Agent信息：
{}

## 输出格式要求

**绝对要求**：你必须始终返回严格的JSON格式，不能有任何额外文字！

**根据方法返回相应格式**：

### plan_workflow 格式：
```json
{{
  "rules": [...],
  "confidence": 0.85,
  "reasoning": "规划分析过程"
}}
```

### make_decision 格式：
```json
{{
  "decision": {{
    "type": "EXECUTE_SELECTED_RULE",
    "selected_rule_id": "rule_001",
    "reasoning": "决策理由"
  }},
  "confidence": 0.80,
  "reasoning": "决策分析过程"
}}
```

### optimize_rules 格式：
```json
{{
  "rules": [...],
  "confidence": 0.75,
  "reasoning": "优化分析过程"
}}
```

**错误示例**（绝对禁止）：
- 缺少任何必需字段
- 在JSON外添加解释文字
- 使用不完整的JSON格式

## 严格约束条件

1. **方法职责分离**：
   - `plan_workflow`：专注规划，返回规则集
   - `make_decision`：专注决策，返回执行决策
   - `optimize_rules`：专注优化，返回修复规则

2. **决策类型约束**（仅适用于make_decision）：
   - `EXECUTE_SELECTED_RULE`：选择并执行特定规则
   - `ADD_RULE`：需要添加新规则
   - `GOAL_ACHIEVED`：目标已完成
   - `GOAL_FAILED`：目标执行失败

3. **规则格式要求**：
   每个规则必须包含：
   - `id`: 唯一标识符
   - `name`: 规则名称
   - `condition`: IF条件（自然语言）
   - `action`: THEN动作（自然语言）
   - `agent_name`: 执行的Agent名称
   - `priority`: 优先级（1-100）
   - `phase`: 执行阶段

3. **质量要求**：
   - 条件描述要具体明确
   - 动作描述要可执行
   - Agent选择要合理匹配
   - 优先级设置要有依据

请严格按照上述要求响应用户的每个请求。""".format(agent_info)
        
        # 设置系统消息
        self.system_message = system_prompt
        logger.debug("🔧 ManagerAgent系统提示词已设置")
    
    def plan_workflow(self, goal: str) -> dict:
        """
        规划工作流，生成初始规则集
        
        Args:
            goal: 工作流目标描述
            
        Returns:
            dict: 包含规则集的JSON格式
        """
        logger.info(f"🧠 开始规划工作流: {goal}")
        
        # 直接处理目标
        logger.info("📝 开始处理目标")
        prompt = self._build_planning_prompt(goal)
        
        try:
            # 使用DeepSeek API的JSON格式
            response = self.chat_sync(prompt, response_format={"type": "json_object"})
            result = self._parse_response(response)
            
            logger.info(f"✅ 工作流规划完成，生成了 {len(result.get('rules', []))} 个规则")
            return result
            
        except Exception as e:
            logger.error(f"❌ 工作流规划失败: {e}")
            # 返回失败结果
            return {
                "rules": [],
                "confidence": 0.0,
                "reasoning": f"无法生成规则集，错误: {str(e)}"
            }
    
    def _build_planning_prompt(self, goal: str) -> str:
        """构建规划提示词"""
        return f"""请为以下目标生成完整的初始规则集：

目标: {goal}

请根据系统提示词中的核心原则，专注于当前任务进行规划。

**严格JSON Schema要求**：
```json
{{
  "rules": [
    {{
      "id": "rule_001",
      "name": "规则名称",
      "condition": "触发条件描述",
      "action": "执行动作描述",
      "agent_name": "coder或tester",
      "priority": 85,
      "phase": "execution",
      "expected_outcome": "期望结果"
    }}
  ],
  "confidence": 0.85,
  "reasoning": "完整的规划分析和推理"
}}
```

**严格要求**：
- rules数组必须包含至少1个规则
- 必须包含confidence和reasoning字段
- 只返回纯JSON，不要任何其他文字！"""
    
    def make_decision(self, state: Any, available_rules: List[Any], goal: str) -> dict:
        """
        基于当前状态和可用规则��出决策
        
        Args:
            state: 当前工作流状态 (可以是dict或GlobalState对象)
            available_rules: 可用规则列表 (ProductionRule对象)
            
        Returns:
            dict: 包含decision的统一JSON格式
        """
        logger.info("🤔 开始决策分析")
        
        try:
            # 格式化状态信息
            state_desc = state.state
            iteration_count = state.iteration_count
            goal_achieved = state.goal_achieved
        except AttributeError as e:
            logger.error(f"CRITICAL: 'state' object is not a GlobalState instance as expected.")
            logger.error(f"Error: {e}")
            logger.error(f"Object type: {type(state)}")
            logger.error(f"Object attributes: {dir(state)}")
            # Re-raise the exception to halt execution, as this is a critical error
            raise

        # 格式化规则信息
        rules_info = []
        for rule in available_rules:
            rule_info = f"- ID: {rule.id}, 名称: {rule.name}"
            rule_info += f", 条件: {rule.condition[:100]}..."
            rules_info.append(rule_info)
        
        prompt = f"""请基于当前状态分析并做出最优决策：

当前状态信息：
- 目标: {goal}
- 状态描述: {state_desc}
- 迭代次数: {iteration_count}
- 目标是否达成: {goal_achieved}

可用规则列表:
{chr(10).join(rules_info) if rules_info else "无可用规则"}

请基于系统提示词中的核心原则分析：
1. 当前状态是否匹配某个规则的条件
2. 如果有多个匹配规则，选择最优的一个
3. 评估当前层级的目标达成情况
4. 专注于当前任务，不要被复杂的上下文干扰

**严格JSON Schema要求**：
```json
{{
  "rules": [],
  "decision": {{
    "type": "EXECUTE_SELECTED_RULE",
    "selected_rule_id": "rule_001",
    "reasoning": "详细的决策推理"
  }},
  "confidence": 0.80,
  "reasoning": "完整的分析过程"
}}
```

**严格要求**：
- 决策阶段rules数组必须为空[]
- decision.type必须是EXECUTE_SELECTED_RULE、ADD_RULE、GOAL_ACHIEVED或GOAL_FAILED之一
- EXECUTE_SELECTED_RULE时必须提供selected_rule_id
- 必须包含所有必需字段
- 只返回纯JSON，不要任何其他文字！"""
        
        try:
            # 使用DeepSeek API的JSON格式
            response = self.chat_sync(prompt, response_format={"type": "json_object"})
            result = self._parse_response(response)
            
            decision_type = result.get('decision', {}).get('type', 'unknown')
            logger.info(f"✅ 决策完成: {decision_type}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 决策失败: {e}")
            # 返回保守的默认决策
            return {
                "rules": [],
                "decision": {
                    "type": "GOAL_FAILED",
                    "selected_rule_id": None,
                    "reasoning": f"决策过程出错: {str(e)}"
                },
                "confidence": 0.0,
                "reasoning": f"无法完成决策分析，错误: {str(e)}"
            }
    
    def optimize_rules(self, context: dict) -> dict:
        """
        基于失败上下文优化和修复规则
        
        Args:
            context: 包含失败信息的上下文
            
        Returns:
            dict: 包含修复规则的统一JSON格式
        """
        logger.info("🔧 开始规则优化")
        
        failed_rule = context.get('failed_rule', {})
        error_message = context.get('error_message', '未知错误')
        execution_result = context.get('execution_result', {})
        current_state = context.get('current_state', {})
        
        prompt = f"""请分析以下规则执行失败的情况，并提供修复方案：

失败规则信息：
- 规则ID: {failed_rule.get('id', 'unknown')}
- 规则名称: {failed_rule.get('name', 'unknown')}
- 条件: {failed_rule.get('condition', 'unknown')}
- 动作: {failed_rule.get('action', 'unknown')}
- 执行Agent: {failed_rule.get('agent_name', 'unknown')}

错误信息: {error_message}

执行结果: {execution_result}

当前状态: {current_state.get('description', '未知状态')}

请基于系统提示词中的核心原则分析：
1. 失败的根本原因（聚焦当前层级的问题）
2. 如何修复或改进这个规则（保持任务边界清晰）
3. 是否需要添加辅助规则（仅限当前层级）
4. 如何避免类似问题再次发生

**严格JSON Schema要求**：
```json
{{
  "rules": [
    {{
      "id": "fix_rule_001",
      "name": "修复规则名称",
      "condition": "修复触发条件",
      "action": "修复动作描述",
      "agent_name": "coder或tester",
      "priority": 90,
      "phase": "execution",
      "expected_outcome": "期望的修复结果"
    }}
  ],
  "decision": {{
    "type": "ADD_RULE",
    "selected_rule_id": null,
    "reasoning": "详细的修复推理"
  }},
  "confidence": 0.75,
  "reasoning": "完整的问题分析和解决方案"
}}
```

**严格要求**：
- 优化阶段rules数组可以包含修复规则
- decision.type必须是"ADD_RULE"或"GOAL_FAILED"
- 必须包含所有必需字段
- 只返回纯JSON，不要任何其他文字！"""
        
        try:
            # 使用DeepSeek API的JSON格式
            response = self.chat_sync(prompt, response_format={"type": "json_object"})
            result = self._parse_response(response)
            
            rules_count = len(result.get('rules', []))
            logger.info(f"✅ 规则优化完成，生成了 {rules_count} 个修复规则")
            return result
            
        except Exception as e:
            logger.error(f"❌ 规则优化失败: {e}")
            # 返回失败结果
            return {
                "rules": [],
                "decision": {
                    "type": "GOAL_FAILED",
                    "selected_rule_id": None,
                    "reasoning": f"优化失败: {str(e)}"
                },
                "confidence": 0.0,
                "reasoning": f"无法完成规则优化，错误: {str(e)}"
            }
    
    def _parse_response(self, response) -> dict:
        """
        解析chat_sync返回的JSON响应
        
        Args:
            response: chat_sync返回的响应
            
        Returns:
            dict: 解析后的标准格式字典
            
        Raises:
            ValueError: JSON格式不正确或约束验证失败
        """
        try:
            # 提取响应内容
            if hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, str):
                content = response
            else:
                content = str(response)
            
            logger.debug(f"原始响应内容: {content[:200]}...")
            
            # 更强健的JSON提取
            import re
            
            # 清理可能的markdown格式
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            elif content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # 尝试提取JSON对象
            json_pattern = r'\{.*\}'
            json_match = re.search(json_pattern, content, re.DOTALL)
            if json_match:
                content = json_match.group()
            
            logger.debug(f"清理后的JSON内容: {content[:200]}...")
            
            # 解析JSON
            result = json.loads(content)
            
            # 验证并补全必要字段
            if 'rules' not in result:
                logger.warning("响应缺少rules字段，设置为空数组")
                result['rules'] = []
            if 'decision' not in result:
                logger.warning("响应缺少decision字段，设置为默认值")
                result['decision'] = {
                    'type': 'GOAL_FAILED',
                    'selected_rule_id': None,
                    'reasoning': '响应格式错误，缺少decision字段'
                }
            if 'confidence' not in result:
                logger.warning("响应缺少confidence字段，设置为0.0")
                result['confidence'] = 0.0
            if 'reasoning' not in result:
                logger.warning("响应缺少reasoning字段，设置为默认值")
                result['reasoning'] = '响应格式错误，缺少reasoning字段'
            
            # 验证decision字段
            decision = result['decision']
            if 'type' not in decision:
                raise ValueError("decision缺少type字段")
            
            decision_type = decision['type']
            
            # 兼容性处理：映射常见的错误类型
            type_mapping = {
                'EXECUTE_RULE': 'EXECUTE_SELECTED_RULE',
                'EXECUTE': 'EXECUTE_SELECTED_RULE',
                'SELECT_RULE': 'EXECUTE_SELECTED_RULE',
                'ADD_NEW_RULE': 'ADD_RULE',
                'GOAL_COMPLETE': 'GOAL_ACHIEVED',
                'COMPLETE': 'GOAL_ACHIEVED',
                'FAILED': 'GOAL_FAILED'
            }
            
            if decision_type in type_mapping:
                logger.info(f"自动映射decision.type: {decision_type} -> {type_mapping[decision_type]}")
                decision['type'] = type_mapping[decision_type]
                decision_type = type_mapping[decision_type]
            
            valid_types = ['INITIALIZE_WORKFLOW', 'EXECUTE_SELECTED_RULE', 'ADD_RULE', 'GOAL_ACHIEVED', 'GOAL_FAILED']
            if decision_type not in valid_types:
                raise ValueError(f"无效的decision.type: {decision_type}")
            
            # 验证约束条件
            rules = result['rules']
            if decision_type == 'EXECUTE_SELECTED_RULE' and len(rules) > 0:
                logger.warning(f"EXECUTE_SELECTED_RULE时检测到非空rules，自动清空")
                result['rules'] = []
                rules = []
            
            if decision_type == 'INITIALIZE_WORKFLOW' and len(rules) == 0:
                logger.warning(f"警告: INITIALIZE_WORKFLOW时rules为空，这可能不是预期行为")
                
            if decision_type == 'ADD_RULE' and len(rules) == 0:
                logger.warning(f"警告: ADD_RULE时rules为空，这可能不是预期行为")
            
            # 验证confidence范围
            confidence = result['confidence']
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                logger.warning(f"警告: confidence值异常: {confidence}")
                result['confidence'] = max(0.0, min(1.0, float(confidence)))
            
            logger.debug(f"✅ JSON响应解析成功: decision.type={decision_type}, rules_count={len(rules)}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON解析失败: {e}")
            logger.debug(f"原始响应内容: {content}")
            raise ValueError(f"无效的JSON格式: {str(e)}")
        
        except Exception as e:
            logger.error(f"❌ 响应验证失败: {e}")
            raise ValueError(f"响应格式不符合要求: {str(e)}")
    
    def get_performance_stats(self) -> dict:
        """
        获取ManagerAgent的性能统计信息
        
        Returns:
            dict: 性能统计数据
        """
        # 基础统计信息
        stats = {
            "manager_agent_status": "active",
            "available_agents": len(self.agent_registry.agents),
            "agent_specs": self.agent_registry.get_agent_specifications()
        }
        
        # 如果父类有性能统计，也包含进来
        if hasattr(super(), 'get_performance_stats'):
            parent_stats = super().get_performance_stats()
            stats.update(parent_stats)
        
        return stats
    
    def __repr__(self) -> str:
        """返回ManagerAgent的字符串表示"""
        agent_count = len(self.agent_registry.agents)
        return f"ManagerAgent(agents={agent_count}, capabilities=['planning', 'decision', 'optimization'])"