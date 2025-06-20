#!/usr/bin/env python3
"""
全局状态更新器模块
================

使用LLM智能更新工作流的自然语言全局状态。
"""

import logging
import json
from typing import Any, Optional, Dict
from datetime import datetime

try:
    # 尝试相对导入（当作为包使用时）
    from .workflow_definitions import StepExecution, WorkflowStep
except ImportError:
    # 回退到绝对导入（当直接运行时）
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from workflow_definitions import StepExecution, WorkflowStep

logger = logging.getLogger(__name__)


class GlobalStateUpdater:
    """全局状态更新器
    
    使用LLM智能地基于步骤执行结果更新工作流的全局状态。
    """
    
    def __init__(self, llm=None, enable_updates: bool = True):
        """
        初始化状态更新器
        
        Args:
            llm: 语言模型实例，用于状态更新
            enable_updates: 是否启用状态更新（可用于调试/性能优化）
        """
        self.llm = llm
        self.enable_updates = enable_updates
        
    def should_update_state(self, step: WorkflowStep, execution: StepExecution) -> bool:
        """
        判断是否需要更新全局状态
        
        Args:
            step: 执行的步骤定义
            execution: 步骤执行实例
            
        Returns:
            是否需要更新状态
        """
        if not self.enable_updates:
            return False
            
        # 只有成功完成的步骤才更新状态
        from .workflow_definitions import StepExecutionStatus
        if execution.status != StepExecutionStatus.COMPLETED:
            return False
            
        # 可以根据步骤类型或重要性进一步筛选
        # 例如：跳过某些辅助性步骤
        return True
    
    def update_state(self, 
                    current_state: str,
                    step: WorkflowStep, 
                    execution: StepExecution,
                    workflow_context: str = "") -> str:
        """
        基于步骤执行结果更新全局状态
        
        Args:
            current_state: 当前全局状态
            step: 执行的步骤定义
            execution: 步骤执行实例
            workflow_context: 额外的工作流上下文信息
            
        Returns:
            更新后的全局状态
        """
        
        if not self.should_update_state(step, execution):
            logger.debug(f"跳过状态更新：步骤 {step.name} ({step.id})")
            return current_state
            
        if not self.llm:
            # 回退到简单的状态更新
            return self._simple_state_update(current_state, step, execution)
            
        try:
            # 使用LLM进行智能状态更新
            return self._llm_state_update(current_state, step, execution, workflow_context)
        except Exception as e:
            logger.warning(f"LLM状态更新失败，使用简单更新: {e}")
            return self._simple_state_update(current_state, step, execution)
    
    def _simple_state_update(self, 
                            current_state: str,
                            step: WorkflowStep, 
                            execution: StepExecution) -> str:
        """
        简单的状态更新逻辑（不依赖LLM）
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not current_state:
            # 初始状态
            new_state = f"""工作流开始执行 ({timestamp})
            
已完成步骤：
- {step.name} ({step.id}): {step.expected_output or '执行完成'}
"""
        else:
            # 追加新完成的步骤
            new_state = current_state + f"""
- {step.name} ({step.id}): {step.expected_output or '执行完成'} ({timestamp})
"""
        
        return new_state.strip()
    
    def _llm_state_update(self,
                         current_state: str,
                         step: WorkflowStep,
                         execution: StepExecution,
                         workflow_context: str = "") -> str:
        """
        使用LLM进行智能状态更新
        """
        
        # 构建更新提示
        update_prompt = self._build_update_prompt(
            current_state, step, execution, workflow_context
        )
        
        # 调用LLM
        messages = [
            {
                "role": "system",
                "content": """你是一个工作流状态管理专家，负责基于步骤执行结果智能更新工作流的全局状态。

要求：
1. 用自然语言描述当前工作流的整体状态
2. 集成新完成步骤的结果和影响
3. 保持状态描述的连贯性和完整性
4. 突出重要的进展和成果
5. 简洁明了，避免冗余信息
"""
            },
            {
                "role": "user", 
                "content": update_prompt
            }
        ]
        
        # 使用不同的LLM接口
        if hasattr(self.llm, 'invoke'):
            # LangChain 接口
            response = self.llm.invoke(messages)
            if hasattr(response, 'content'):
                return response.content.strip()
            else:
                return str(response).strip()
        elif hasattr(self.llm, 'chat'):
            # 原始LLM接口
            response = self.llm.chat(update_prompt)
            return response.strip()
        else:
            # 其他接口
            response = self.llm(update_prompt)
            return response.strip()
    
    def _build_update_prompt(self,
                            current_state: str,
                            step: WorkflowStep,
                            execution: StepExecution,
                            workflow_context: str = "") -> str:
        """
        构建状态更新的提示词
        """
        
        # 获取执行结果信息
        result_info = ""
        if execution.result:
            result_info = f"执行结果: {str(execution.result)[:500]}"
        
        duration_info = ""
        if execution.duration:
            duration_info = f"执行耗时: {execution.duration:.2f}秒"
            
        prompt = f"""# 工作流状态更新任务

## 当前全局状态
{current_state if current_state else "工作流刚开始，尚无状态信息"}

## 新完成的步骤信息
- 步骤名称: {step.name}
- 步骤ID: {step.id}
- 执行者: {step.agent_name}
- 指令: {step.instruction}
- 预期输出: {step.expected_output}
- 迭代次数: {execution.iteration}
{result_info}
{duration_info}

## 工作流上下文
{workflow_context}

## 更新要求
请基于以上信息，更新工作流的全局状态描述。新的状态应该：

1. **整合新步骤的成果** - 将刚完成步骤的结果融入整体状态
2. **保持连贯性** - 与之前的状态描述保持逻辑连贯
3. **突出进展** - 明确展示工作流的进展情况
4. **展望后续** - 如果可能，简要说明接下来的方向
5. **简洁明了** - 避免冗余，保持状态描述的简洁性

请直接返回更新后的全局状态描述，不需要额外的解释或格式。
"""
        
        return prompt
    
    def extract_structured_data(self, global_state: str) -> Dict[str, Any]:
        """
        从自然语言全局状态中提取结构化数据
        
        这个方法用于向后兼容，从自然语言状态中提取传统的变量值。
        
        Args:
            global_state: 自然语言描述的全局状态
            
        Returns:
            提取出的结构化数据字典
        """
        
        if not self.llm:
            # 简单的规则提取
            return self._simple_data_extraction(global_state)
            
        try:
            return self._llm_data_extraction(global_state)
        except Exception as e:
            logger.warning(f"LLM数据提取失败，使用简单提取: {e}")
            return self._simple_data_extraction(global_state)
    
    def _simple_data_extraction(self, global_state: str) -> Dict[str, Any]:
        """
        简单的规则化数据提取
        """
        extracted = {}
        
        # 提取时间信息
        import re
        time_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
        times = re.findall(time_pattern, global_state)
        if times:
            extracted['last_update_time'] = times[-1]
            
        # 提取步骤数量
        step_pattern = r'已完成.*?(\d+).*?步骤'
        step_match = re.search(step_pattern, global_state)
        if step_match:
            extracted['completed_steps'] = int(step_match.group(1))
            
        # 提取状态关键词
        if '成功' in global_state or '完成' in global_state:
            extracted['status'] = 'success'
        elif '失败' in global_state or '错误' in global_state:
            extracted['status'] = 'failed'
        else:
            extracted['status'] = 'in_progress'
            
        return extracted
    
    def _llm_data_extraction(self, global_state: str) -> Dict[str, Any]:
        """
        使用LLM进行结构化数据提取
        """
        
        extraction_prompt = f"""# 数据提取任务

从以下工作流状态描述中提取结构化信息：

{global_state}

请以JSON格式返回提取的信息，包括但不限于：
- 完成的步骤数量
- 当前状态（成功/进行中/失败）
- 最后更新时间
- 重要的数值和进度信息
- 关键的状态变量

示例格式：
{{
    "completed_steps": 3,
    "status": "in_progress",
    "last_update_time": "2024-01-15 14:30:00",
    "progress_percentage": 60,
    "key_variables": {{
        "user_count": 1250,
        "processing_time": 15
    }}
}}

只返回JSON，不要额外的解释。
"""
        
        messages = [
            {
                "role": "system",
                "content": "你是数据提取专家，从自然语言中提取结构化信息。只返回JSON格式的结果。"
            },
            {
                "role": "user",
                "content": extraction_prompt
            }
        ]
        
        # 调用LLM
        if hasattr(self.llm, 'invoke'):
            response = self.llm.invoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)
        else:
            content = self.llm(extraction_prompt)
            
        try:
            # 尝试解析JSON
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}, 内容: {content[:200]}")
            return self._simple_data_extraction(global_state)


# 便捷函数
def create_state_updater(llm=None, enable_updates: bool = True) -> GlobalStateUpdater:
    """
    创建全局状态更新器的便捷函数
    
    Args:
        llm: 语言模型实例
        enable_updates: 是否启用更新
        
    Returns:
        GlobalStateUpdater实例
    """
    return GlobalStateUpdater(llm=llm, enable_updates=enable_updates)