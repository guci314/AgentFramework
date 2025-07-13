# -*- coding: utf-8 -*-
"""
认知工作流适配器 - 提供与现有系统的兼容性

这个适配器允许：
1. 现有代码继续使用MultiStepAgent_v2接口
2. 在底层使用认知工作流引擎
3. 渐进式迁移到认知工作流

作者：Claude
日期：2024-12-21
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from langchain_core.language_models import BaseChatModel

from agent_base import Result
from python_core import Agent, StatefulExecutor
from .cognitive_workflow import (
    CognitiveWorkflowEngine, CognitiveTask, TaskPhase, TaskStatus, GlobalState
)

logger = logging.getLogger(__name__)

@dataclass
class RegisteredAgent:
    """注册的智能体规格 - 兼容现有接口"""
    name: str
    instance: Agent
    description: str = ""

class CognitiveMultiStepAgent(Agent):
    """
    认知多步骤智能体 - 兼容MultiStepAgent_v2接口的认知工作流实现
    
    这个类提供了与原有MultiStepAgent_v2相同的接口，
    但底层使用了全新的认知工作流引擎。
    """
    
    def __init__(
        self,
        llm: BaseChatModel,
        registered_agents: Optional[List[RegisteredAgent]] = None,
        max_retries: int = 3,
        thinker_system_message: Optional[str] = None,
        thinker_chat_system_message: Optional[str] = None,
        use_cognitive_workflow: bool = True,  # 新参数：是否使用认知工作流
    ):
        """
        初始化认知多步骤智能体
        
        Args:
            llm: 语言模型
            registered_agents: 注册的智能体列表
            max_retries: 最大重试次数
            thinker_system_message: 思考者系统消息
            thinker_chat_system_message: 思考者对话系统消息
            use_cognitive_workflow: 是否使用认知工作流（False时回退到传统模式）
        """
        # 调用父类初始化
        super().__init__(
            llm=llm,
            stateful=True,
            thinker_system_message=thinker_system_message,
            thinker_chat_system_message=thinker_chat_system_message,
            max_retries=max_retries,
        )
        
        self.registered_agents = registered_agents if registered_agents is not None else []
        self.max_retries = max_retries
        self.use_cognitive_workflow = use_cognitive_workflow
        
        # 创建智能体字典
        self.agents_dict = {}
        for spec in self.registered_agents:
            self.agents_dict[spec.name] = spec.instance
            
        # 初始化认知工作流引擎（如果启用）
        if self.use_cognitive_workflow and self.agents_dict:
            self.cognitive_engine = CognitiveWorkflowEngine(
                llm=llm,
                agents=self.agents_dict,
                max_iterations=max_retries * 10,
                enable_auto_recovery=True
            )
            logger.info("认知工作流引擎已启用")
        else:
            self.cognitive_engine = None
            logger.info("使用传统工作流模式")
            
        # 兼容原有属性
        self.device = StatefulExecutor()
        for spec in self.registered_agents:
            self.device.set_variable(spec.name, spec.instance)
        self.device.set_variable("current_plan", [])
        
    def execute_multi_step(self, main_instruction: str, interactive: bool = False) -> str:
        """
        执行多步骤任务 - 兼容原有接口
        
        Args:
            main_instruction: 主要指令
            interactive: 是否交互模式
            
        Returns:
            执行结果字符串
        """
        if self.use_cognitive_workflow and self.cognitive_engine:
            return self._execute_with_cognitive_workflow(main_instruction, interactive)
        else:
            return self._execute_with_traditional_workflow(main_instruction, interactive)
    
    def _execute_with_cognitive_workflow(self, main_instruction: str, interactive: bool = False) -> str:
        """使用认知工作流执行"""
        logger.info("使用认知工作流引擎执行任务")
        
        try:
            # 执行认知工作流
            result_summary = self.cognitive_engine.execute_cognitive_workflow(main_instruction)
            
            # 格式化返回结果以兼容原有接口
            status = "成功完成" if result_summary['workflow_status'] == 'completed' else "部分完成"
            
            result_text = f"""=== 认知工作流执行结果 ===

状态: {status}
总任务数: {result_summary['total_tasks']}
已完成: {result_summary['completed_tasks']}
成功率: {result_summary['success_rate']:.2%}
迭代次数: {result_summary['total_iterations']}

最终状态: {result_summary['final_state']}

=== 详细任务报告 ===
{self.cognitive_engine.get_task_status_report()}
"""
            
            return result_text
            
        except Exception as e:
            logger.error(f"认知工作流执行失败: {e}")
            return f"认知工作流执行失败: {str(e)}"
    
    def _execute_with_traditional_workflow(self, main_instruction: str, interactive: bool = False) -> str:
        """使用传统工作流执行（回退模式）"""
        logger.info("使用传统工作流模式执行任务")
        
        # 这里可以调用原有的MultiStepAgent_v2逻辑
        # 为了演示，返回一个简单的结果
        return f"传统模式执行结果: {main_instruction}\n注意：建议启用认知工作流以获得更好的体验。"
    
    def get_cognitive_engine(self) -> Optional[CognitiveWorkflowEngine]:
        """获取认知工作流引擎实例 - 用于高级操作"""
        return self.cognitive_engine
    
    def switch_to_cognitive_mode(self) -> bool:
        """切换到认知工作流模式"""
        if not self.agents_dict:
            logger.warning("没有注册的智能体，无法启用认知工作流")
            return False
            
        if not self.cognitive_engine:
            self.cognitive_engine = CognitiveWorkflowEngine(
                llm=self.llm,
                agents=self.agents_dict,
                max_iterations=self.max_retries * 10,
                enable_auto_recovery=True
            )
            
        self.use_cognitive_workflow = True
        logger.info("已切换到认知工作流模式")
        return True
    
    def switch_to_traditional_mode(self):
        """切换到传统工作流模式"""
        self.use_cognitive_workflow = False
        logger.info("已切换到传统工作流模式")
    
    def get_mode_info(self) -> Dict[str, Any]:
        """获取当前模式信息"""
        return {
            'mode': 'cognitive' if self.use_cognitive_workflow else 'traditional',
            'cognitive_engine_available': self.cognitive_engine is not None,
            'registered_agents_count': len(self.registered_agents),
            'agents_available': list(self.agents_dict.keys())
        }

def convert_legacy_plan_to_cognitive_tasks(legacy_plan: List[Dict[str, Any]]) -> List[CognitiveTask]:
    """
    将传统计划格式转换为认知任务格式
    
    Args:
        legacy_plan: 传统格式的计划
        
    Returns:
        认知任务列表
    """
    cognitive_tasks = []
    
    for i, step in enumerate(legacy_plan):
        # 映射传统字段到认知任务
        task_id = step.get('id', f'legacy_task_{i}')
        name = step.get('name', f'Task {i+1}')
        instruction = step.get('instruction', '')
        agent_name = step.get('agent_name', 'default')
        
        # 推测任务类型和阶段
        instruction_type = step.get('instruction_type', 'execution')
        if 'information' in instruction_type.lower() or '查询' in instruction or '分析' in instruction:
            phase = TaskPhase.INFORMATION
        elif '验证' in instruction or '测试' in instruction or '检查' in instruction:
            phase = TaskPhase.VERIFICATION
        else:
            phase = TaskPhase.EXECUTION
            
        # 转换依赖关系为先决条件
        dependencies = step.get('dependencies', [])
        if dependencies:
            precondition = f"任务 {', '.join(dependencies)} 已成功完成"
        else:
            precondition = "无特殊先决条件" if i == 0 else f"前序任务已准备就绪"
            
        # 创建认知任务
        cognitive_task = CognitiveTask(
            id=task_id,
            name=name,
            instruction=instruction,
            agent_name=agent_name,
            instruction_type=instruction_type,
            phase=phase,
            expected_output=step.get('expected_output', '任务执行结果'),
            precondition=precondition
        )
        
        cognitive_tasks.append(cognitive_task)
    
    return cognitive_tasks

def create_migration_guide() -> str:
    """创建迁移指南"""
    
    guide = """
=== 认知工作流迁移指南 ===

## 1. 简单迁移（最小改动）

原有代码：
```python
from enhancedAgent_v2 import MultiStepAgent_v2

agent = MultiStepAgent_v2(llm=llm, registered_agents=agents)
result = agent.execute_multi_step("开发计算器")
```

迁移后：
```python
from cognitive_workflow_adapter import CognitiveMultiStepAgent

agent = CognitiveMultiStepAgent(llm=llm, registered_agents=agents)
result = agent.execute_multi_step("开发计算器")  # 自动使用认知工作流
```

## 2. 渐进式迁移

```python
# 创建适配器实例
agent = CognitiveMultiStepAgent(llm=llm, registered_agents=agents)

# 检查当前模式
print(agent.get_mode_info())

# 可以在运行时切换模式
agent.switch_to_cognitive_mode()    # 启用认知工作流
agent.switch_to_traditional_mode()  # 回退到传统模式

# 获取认知引擎进行高级操作
engine = agent.get_cognitive_engine()
if engine:
    print(engine.get_task_status_report())
```

## 3. 完全迁移到认知工作流

```python
from cognitive_workflow import CognitiveWorkflowEngine

# 直接使用认知工作流引擎
engine = CognitiveWorkflowEngine(llm=llm, agents=agents_dict)
result = engine.execute_cognitive_workflow("开发计算器")
```

## 4. 主要差异对比

| 方面 | 传统工作流 | 认知工作流 |
|------|------------|------------|
| 计划方式 | 静态流程图 | 动态任务列表 |
| 执行控制 | 固定依赖关系 | 状态满足性检查 |
| 错误处理 | 预设错误路径 | 动态生成修复任务 |
| 适应能力 | 有限 | 自适应和自修复 |
| 用户体验 | 需要详细规划 | 只需高层次目标 |

## 5. 注意事项

1. 认知工作流需要更多的LLM调用，成本可能增加
2. 首次运行可能需要更长时间来学习和适应
3. 建议先在非关键任务上测试
4. 可以保留传统模式作为备用方案

"""
    return guide

if __name__ == "__main__":
    print("认知工作流适配器")
    print(create_migration_guide())