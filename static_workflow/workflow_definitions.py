"""
工作流定义和Schema模块
===================

定义静态工作流的数据结构、Schema验证和配置解析功能。
"""

import json
import yaml
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ControlFlowType(Enum):
    """控制流类型枚举"""
    SEQUENTIAL = "sequential"      # 顺序执行
    CONDITIONAL = "conditional"    # 条件分支
    LOOP = "loop"                 # 循环控制
    PARALLEL = "parallel"         # 并行执行
    TERMINAL = "terminal"         # 终止执行


class StepStatus(Enum):
    """步骤状态枚举"""
    PENDING = "pending"           # 待执行
    RUNNING = "running"           # 运行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"            # 执行失败
    SKIPPED = "skipped"          # 已跳过
    BLOCKED = "blocked"          # 被阻塞


@dataclass
class ControlFlow:
    """控制流配置"""
    type: ControlFlowType
    success_next: Optional[str] = None        # 成功后的下一步
    failure_next: Optional[str] = None        # 失败后的下一步
    condition: Optional[str] = None           # 条件表达式
    loop_condition: Optional[str] = None      # 循环条件
    loop_target: Optional[str] = None         # 循环目标
    max_iterations: Optional[Union[str, int]] = None  # 最大迭代次数
    exit_on_max: Optional[str] = None         # 达到最大次数后的跳转
    parallel_steps: Optional[List[str]] = None # 并行步骤列表
    join_condition: Optional[str] = None      # 并行合并条件
    timeout: Optional[int] = None             # 超时时间（秒）
    
    def __post_init__(self):
        """后处理：类型转换和验证"""
        if isinstance(self.type, str):
            self.type = ControlFlowType(self.type)


@dataclass 
class WorkflowStep:
    """工作流步骤定义"""
    id: str                                   # 步骤唯一标识
    name: str                                # 步骤名称
    agent_name: str                          # 执行智能体名称
    instruction: str                         # 执行指令
    instruction_type: str = "execution"      # 指令类型
    expected_output: str = ""                # 预期输出
    control_flow: Optional[ControlFlow] = None # 控制流配置
    timeout: Optional[int] = None            # 步骤超时
    retry_count: int = 0                     # 重试次数
    max_retries: int = 3                     # 最大重试次数
    
    # 运行时状态
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Any] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """后处理：类型转换和验证"""
        if isinstance(self.status, str):
            self.status = StepStatus(self.status)
        if isinstance(self.control_flow, dict):
            self.control_flow = ControlFlow(**self.control_flow)


@dataclass
class ControlRule:
    """全局控制规则"""
    trigger: str                             # 触发条件
    action: str                              # 执行动作
    target: Optional[str] = None             # 目标步骤
    priority: int = 1                        # 优先级
    cleanup_steps: Optional[List[str]] = None # 清理步骤


@dataclass
class ErrorHandling:
    """错误处理配置"""
    default_strategy: str = "retry_with_backoff"  # 默认策略
    escalation_rules: Optional[List[Dict]] = None # 升级规则
    
    def __post_init__(self):
        if self.escalation_rules is None:
            self.escalation_rules = []


@dataclass
class WorkflowMetadata:
    """工作流元数据"""
    name: str
    version: str = "1.0"
    description: str = ""
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class WorkflowDefinition:
    """完整的工作流定义"""
    workflow_metadata: WorkflowMetadata
    steps: List[WorkflowStep]
    global_variables: Dict[str, Any] = field(default_factory=dict)
    control_rules: List[ControlRule] = field(default_factory=list)
    error_handling: ErrorHandling = field(default_factory=ErrorHandling)
    
    def __post_init__(self):
        """后处理：类型转换和验证"""
        # 转换metadata
        if isinstance(self.workflow_metadata, dict):
            self.workflow_metadata = WorkflowMetadata(**self.workflow_metadata)
        
        # 转换steps
        for i, step in enumerate(self.steps):
            if isinstance(step, dict):
                self.steps[i] = WorkflowStep(**step)
        
        # 转换control_rules
        for i, rule in enumerate(self.control_rules):
            if isinstance(rule, dict):
                self.control_rules[i] = ControlRule(**rule)
        
        # 转换error_handling
        if isinstance(self.error_handling, dict):
            self.error_handling = ErrorHandling(**self.error_handling)
    
    def get_step_by_id(self, step_id: str) -> Optional[WorkflowStep]:
        """根据ID获取步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_step_index(self, step_id: str) -> int:
        """获取步骤在列表中的索引"""
        for i, step in enumerate(self.steps):
            if step.id == step_id:
                return i
        return -1
    
    def validate(self) -> List[str]:
        """验证工作流定义的完整性"""
        errors = []
        
        # 检查步骤ID唯一性
        step_ids = [step.id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append("步骤ID必须唯一")
        
        # 检查控制流引用
        for step in self.steps:
            if step.control_flow:
                cf = step.control_flow
                
                # 检查success_next引用
                if cf.success_next and cf.success_next not in step_ids:
                    errors.append(f"步骤 {step.id} 的 success_next 引用了不存在的步骤: {cf.success_next}")
                
                # 检查failure_next引用
                if cf.failure_next and cf.failure_next not in step_ids:
                    errors.append(f"步骤 {step.id} 的 failure_next 引用了不存在的步骤: {cf.failure_next}")
                
                # 检查loop_target引用
                if cf.loop_target and cf.loop_target not in step_ids:
                    errors.append(f"步骤 {step.id} 的 loop_target 引用了不存在的步骤: {cf.loop_target}")
                
                # 检查parallel_steps引用
                if cf.parallel_steps:
                    for parallel_step in cf.parallel_steps:
                        if parallel_step not in step_ids:
                            errors.append(f"步骤 {step.id} 的 parallel_steps 引用了不存在的步骤: {parallel_step}")
        
        # 检查控制规则引用
        for rule in self.control_rules:
            if rule.target and rule.target not in step_ids:
                errors.append(f"控制规则的 target 引用了不存在的步骤: {rule.target}")
        
        return errors


class WorkflowLoader:
    """工作流配置加载器"""
    
    @staticmethod
    def load_from_file(file_path: str) -> WorkflowDefinition:
        """从文件加载工作流定义"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                elif file_path.endswith(('.yml', '.yaml')):
                    data = yaml.safe_load(f)
                else:
                    raise ValueError(f"不支持的文件格式: {file_path}")
            
            workflow = WorkflowDefinition(**data)
            
            # 验证工作流定义
            errors = workflow.validate()
            if errors:
                raise ValueError(f"工作流定义验证失败:\n" + "\n".join(errors))
            
            logger.info(f"成功加载工作流: {workflow.workflow_metadata.name}")
            return workflow
            
        except Exception as e:
            logger.error(f"加载工作流文件失败 {file_path}: {e}")
            raise
    
    @staticmethod
    def load_from_dict(data: Dict[str, Any]) -> WorkflowDefinition:
        """从字典加载工作流定义"""
        try:
            workflow = WorkflowDefinition(**data)
            
            # 验证工作流定义
            errors = workflow.validate()
            if errors:
                raise ValueError(f"工作流定义验证失败:\n" + "\n".join(errors))
            
            return workflow
            
        except Exception as e:
            logger.error(f"从字典加载工作流失败: {e}")
            raise
    
    @staticmethod
    def save_to_file(workflow: WorkflowDefinition, file_path: str) -> None:
        """保存工作流定义到文件"""
        try:
            # 转换为字典
            data = {
                'workflow_metadata': {
                    'name': workflow.workflow_metadata.name,
                    'version': workflow.workflow_metadata.version,
                    'description': workflow.workflow_metadata.description,
                    'author': workflow.workflow_metadata.author,
                    'created_at': workflow.workflow_metadata.created_at.isoformat() if workflow.workflow_metadata.created_at else None
                },
                'global_variables': workflow.global_variables,
                'steps': [],
                'control_rules': [],
                'error_handling': {
                    'default_strategy': workflow.error_handling.default_strategy,
                    'escalation_rules': workflow.error_handling.escalation_rules
                }
            }
            
            # 转换步骤
            for step in workflow.steps:
                step_dict = {
                    'id': step.id,
                    'name': step.name,
                    'agent_name': step.agent_name,
                    'instruction': step.instruction,
                    'instruction_type': step.instruction_type,
                    'expected_output': step.expected_output,
                    'timeout': step.timeout,
                    'max_retries': step.max_retries
                }
                
                if step.control_flow:
                    cf = step.control_flow
                    step_dict['control_flow'] = {
                        'type': cf.type.value,
                        'success_next': cf.success_next,
                        'failure_next': cf.failure_next,
                        'condition': cf.condition,
                        'loop_condition': cf.loop_condition,
                        'loop_target': cf.loop_target,
                        'max_iterations': cf.max_iterations,
                        'exit_on_max': cf.exit_on_max,
                        'parallel_steps': cf.parallel_steps,
                        'join_condition': cf.join_condition,
                        'timeout': cf.timeout
                    }
                    # 移除None值
                    step_dict['control_flow'] = {k: v for k, v in step_dict['control_flow'].items() if v is not None}
                
                data['steps'].append(step_dict)
            
            # 转换控制规则
            for rule in workflow.control_rules:
                rule_dict = {
                    'trigger': rule.trigger,
                    'action': rule.action,
                    'target': rule.target,
                    'priority': rule.priority,
                    'cleanup_steps': rule.cleanup_steps
                }
                # 移除None值
                rule_dict = {k: v for k, v in rule_dict.items() if v is not None}
                data['control_rules'].append(rule_dict)
            
            # 保存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.endswith('.json'):
                    json.dump(data, f, ensure_ascii=False, indent=2)
                elif file_path.endswith(('.yml', '.yaml')):
                    yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
                else:
                    raise ValueError(f"不支持的文件格式: {file_path}")
            
            logger.info(f"工作流已保存到: {file_path}")
            
        except Exception as e:
            logger.error(f"保存工作流文件失败 {file_path}: {e}")
            raise