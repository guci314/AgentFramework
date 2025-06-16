"""
数据格式转换器

在 MultiStepAgent 和 Task Master AI 之间进行数据格式转换，
确保两个系统的数据结构能够无缝对接。
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TaskMasterDataMapper:
    """
    MultiStepAgent 和 Task Master AI 之间的数据转换器
    
    处理以下转换：
    - AgentSpecification -> Task Master AI 智能体格式
    - MultiStepAgent 步骤格式 <-> Task Master AI 任务格式
    - 状态映射和字段转换
    """
    
    # 状态映射
    STATUS_MAPPING = {
        # MultiStepAgent -> Task Master AI
        "pending": "pending",
        "running": "in-progress", 
        "completed": "done",
        "failed": "failed",
        "skipped": "cancelled",
        
        # Task Master AI -> MultiStepAgent  
        "in-progress": "running",
        "done": "completed",
        "cancelled": "skipped",
        "deferred": "pending"
    }
    
    # 指令类型映射
    INSTRUCTION_TYPE_MAPPING = {
        "execution": "execution",
        "information": "information"
    }
    
    # 阶段映射
    PHASE_MAPPING = {
        "information": "information",
        "execution": "execution", 
        "verification": "verification"
    }
    
    @staticmethod
    def agent_specs_to_tm_format(agent_specs: List[Any]) -> str:
        """
        将 AgentSpecification 列表转换为 Task Master AI 格式
        
        Args:
            agent_specs: AgentSpecification 对象列表
            
        Returns:
            格式化的智能体描述字符串
        """
        if not agent_specs:
            return "无可用智能体"
        
        agent_descriptions = []
        for spec in agent_specs:
            name = getattr(spec, 'name', 'unknown')
            description = getattr(spec, 'description', '通用智能体')
            agent_descriptions.append(f"- {name}: {description}")
        
        return "\n".join(agent_descriptions)
    
    @staticmethod
    def agent_specs_to_name_list(agent_specs: List[Any]) -> List[str]:
        """
        提取智能体名称列表
        
        Args:
            agent_specs: AgentSpecification 对象列表
            
        Returns:
            智能体名称列表
        """
        if not agent_specs:
            return ["general_agent"]
        
        return [getattr(spec, 'name', f'agent_{i}') for i, spec in enumerate(agent_specs)]
    
    @staticmethod
    def tm_task_to_step_format(tm_task: Dict[str, Any]) -> Dict[str, Any]:
        """
        将 Task Master AI 任务转换为 MultiStepAgent 步骤格式
        
        Args:
            tm_task: Task Master AI 任务对象
            
        Returns:
            MultiStepAgent 步骤格式
        """
        try:
            step = {
                "id": str(tm_task.get("id", "")),
                "name": tm_task.get("title", tm_task.get("name", "未命名任务")),
                "instruction": tm_task.get("description", ""),
                "agent_name": tm_task.get("agent_name", "general_agent"),
                "instruction_type": TaskMasterDataMapper._map_instruction_type_to_multistep(
                    tm_task.get("instruction_type", "execution")
                ),
                "phase": TaskMasterDataMapper._map_phase_to_multistep(
                    tm_task.get("phase", "execution")
                ),
                "expected_output": tm_task.get("expected_output", "任务执行结果"),
                "prerequisites": tm_task.get("prerequisites", "无"),
                "status": TaskMasterDataMapper._map_status_to_multistep(
                    tm_task.get("status", "pending")
                )
            }
            
            # 处理依赖关系
            dependencies = tm_task.get("dependencies", [])
            if dependencies:
                if isinstance(dependencies, list):
                    step["dependencies"] = [str(dep) for dep in dependencies]
                else:
                    step["dependencies"] = [str(dependencies)]
            else:
                step["dependencies"] = []
            
            # 处理详细信息
            if "details" in tm_task:
                step["details"] = tm_task["details"]
            
            # 处理测试策略
            if "test_strategy" in tm_task:
                step["test_strategy"] = tm_task["test_strategy"]
            elif "testStrategy" in tm_task:
                step["test_strategy"] = tm_task["testStrategy"]
            
            # 处理子任务
            if "subtasks" in tm_task and tm_task["subtasks"]:
                step["subtasks"] = [
                    TaskMasterDataMapper.tm_task_to_step_format(subtask) 
                    for subtask in tm_task["subtasks"]
                ]
            else:
                step["subtasks"] = []
            
            # 处理优先级
            if "priority" in tm_task:
                step["priority"] = tm_task["priority"]
                
            return step
            
        except Exception as e:
            logger.error(f"转换 Task Master AI 任务到步骤格式失败: {e}")
            # 返回最小化的步骤格式
            return {
                "id": str(tm_task.get("id", "unknown")),
                "name": tm_task.get("title", tm_task.get("name", "转换失败的任务")),
                "instruction": "任务转换失败，请检查原始数据",
                "agent_name": "general_agent",
                "instruction_type": "execution",
                "phase": "execution",
                "expected_output": "错误处理结果",
                "prerequisites": "无",
                "status": "pending",
                "dependencies": [],
                "subtasks": []
            }
    
    @staticmethod
    def step_to_tm_task_format(step: Dict[str, Any], task_id: Optional[int] = None) -> Dict[str, Any]:
        """
        将 MultiStepAgent 步骤转换为 Task Master AI 任务格式
        
        Args:
            step: MultiStepAgent 步骤对象
            task_id: 可选的任务ID，如果不提供则使用步骤中的ID
            
        Returns:
            Task Master AI 任务格式
        """
        try:
            tm_task = {
                "id": task_id if task_id is not None else step.get("id", 1),
                "title": step.get("name", "未命名任务"),
                "description": step.get("instruction", ""),
                "status": TaskMasterDataMapper._map_status_to_tm(step.get("status", "pending")),
                "priority": step.get("priority", "medium"),
                "agent_name": step.get("agent_name", "general_agent"),
                "instruction_type": TaskMasterDataMapper._map_instruction_type_to_tm(
                    step.get("instruction_type", "execution")
                ),
                "phase": TaskMasterDataMapper._map_phase_to_tm(step.get("phase", "execution")),
                "expected_output": step.get("expected_output", "任务执行结果"),
                "prerequisites": step.get("prerequisites", "无")
            }
            
            # 处理依赖关系
            dependencies = step.get("dependencies", [])
            if dependencies:
                tm_task["dependencies"] = [str(dep) for dep in dependencies]
            else:
                tm_task["dependencies"] = []
            
            # 处理详细信息
            if "details" in step:
                tm_task["details"] = step["details"]
            
            # 处理测试策略
            if "test_strategy" in step:
                tm_task["testStrategy"] = step["test_strategy"]
            
            # 处理子任务
            if "subtasks" in step and step["subtasks"]:
                tm_task["subtasks"] = [
                    TaskMasterDataMapper.step_to_tm_task_format(subtask) 
                    for subtask in step["subtasks"]
                ]
            else:
                tm_task["subtasks"] = []
            
            return tm_task
            
        except Exception as e:
            logger.error(f"转换步骤到 Task Master AI 任务格式失败: {e}")
            # 返回最小化的任务格式
            return {
                "id": 1,
                "title": step.get("name", "转换失败的任务"),
                "description": "步骤转换失败，请检查原始数据",
                "status": "pending",
                "priority": "medium",
                "agent_name": "general_agent",
                "instruction_type": "execution",
                "phase": "execution",
                "expected_output": "错误处理结果",
                "prerequisites": "无",
                "dependencies": [],
                "subtasks": []
            }
    
    @staticmethod
    def tm_tasks_to_plan_format(tm_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        将 Task Master AI 任务列表转换为 MultiStepAgent 计划格式
        
        Args:
            tm_tasks: Task Master AI 任务列表
            
        Returns:
            MultiStepAgent 计划格式的步骤列表
        """
        if not tm_tasks:
            return []
        
        plan = []
        for tm_task in tm_tasks:
            step = TaskMasterDataMapper.tm_task_to_step_format(tm_task)
            plan.append(step)
        
        return plan
    
    @staticmethod
    def plan_to_tm_tasks_format(plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        将 MultiStepAgent 计划转换为 Task Master AI 任务格式
        
        Args:
            plan: MultiStepAgent 计划（步骤列表）
            
        Returns:
            Task Master AI 任务列表
        """
        if not plan:
            return []
        
        tm_tasks = []
        for i, step in enumerate(plan):
            tm_task = TaskMasterDataMapper.step_to_tm_task_format(step, task_id=i+1)
            tm_tasks.append(tm_task)
        
        return tm_tasks
    
    @staticmethod
    def _map_status_to_multistep(tm_status: str) -> str:
        """将 Task Master AI 状态映射到 MultiStepAgent 状态"""
        return TaskMasterDataMapper.STATUS_MAPPING.get(tm_status, tm_status)
    
    @staticmethod
    def _map_status_to_tm(step_status: str) -> str:
        """将 MultiStepAgent 状态映射到 Task Master AI 状态"""
        # 直接映射 MultiStepAgent -> Task Master AI
        mapping = {
            "pending": "pending",
            "running": "in-progress",
            "completed": "done",
            "failed": "failed",
            "skipped": "cancelled"
        }
        return mapping.get(step_status, step_status)
    
    @staticmethod
    def _map_instruction_type_to_multistep(tm_type: str) -> str:
        """将 Task Master AI 指令类型映射到 MultiStepAgent"""
        return TaskMasterDataMapper.INSTRUCTION_TYPE_MAPPING.get(tm_type, tm_type)
    
    @staticmethod
    def _map_instruction_type_to_tm(step_type: str) -> str:
        """将 MultiStepAgent 指令类型映射到 Task Master AI"""
        return TaskMasterDataMapper.INSTRUCTION_TYPE_MAPPING.get(step_type, step_type)
    
    @staticmethod
    def _map_phase_to_multistep(tm_phase: str) -> str:
        """将 Task Master AI 阶段映射到 MultiStepAgent"""
        return TaskMasterDataMapper.PHASE_MAPPING.get(tm_phase, tm_phase)
    
    @staticmethod
    def _map_phase_to_tm(step_phase: str) -> str:
        """将 MultiStepAgent 阶段映射到 Task Master AI"""
        return TaskMasterDataMapper.PHASE_MAPPING.get(step_phase, step_phase)
    
    @staticmethod
    def create_tm_compatible_instruction(step: Dict[str, Any], agent_specs: List[Any]) -> str:
        """
        为 Task Master AI 创建兼容的指令描述
        
        Args:
            step: MultiStepAgent 步骤
            agent_specs: 智能体规格列表
            
        Returns:
            格式化的指令描述
        """
        instruction = step.get("instruction", "")
        agent_name = step.get("agent_name", "general_agent")
        
        # 查找智能体描述
        agent_desc = "通用智能体"
        for spec in agent_specs:
            if getattr(spec, 'name', '') == agent_name:
                agent_desc = getattr(spec, 'description', agent_desc)
                break
        
        # 构建详细指令
        detailed_instruction = f"""
# 任务执行指令

## 执行者
{agent_name} - {agent_desc}

## 具体任务
{instruction}

## 执行类型
{step.get('instruction_type', 'execution')}

## 预期输出
{step.get('expected_output', '任务完成结果')}

## 先决条件
{step.get('prerequisites', '无')}
""".strip()
        
        return detailed_instruction
    
    @staticmethod
    def validate_step_format(step: Dict[str, Any]) -> bool:
        """
        验证步骤格式是否完整
        
        Args:
            step: 步骤对象
            
        Returns:
            是否为有效格式
        """
        required_fields = ["id", "name", "instruction", "agent_name"]
        
        for field in required_fields:
            if field not in step or not step[field]:
                logger.warning(f"步骤缺少必需字段: {field}")
                return False
        
        return True
    
    @staticmethod
    def validate_tm_task_format(tm_task: Dict[str, Any]) -> bool:
        """
        验证 Task Master AI 任务格式是否完整
        
        Args:
            tm_task: Task Master AI 任务对象
            
        Returns:
            是否为有效格式
        """
        required_fields = ["id", "title", "description", "status"]
        
        for field in required_fields:
            if field not in tm_task or tm_task[field] is None:
                logger.warning(f"Task Master AI 任务缺少必需字段: {field}")
                return False
        
        return True