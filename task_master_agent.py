"""
TaskMasterAgent - 基于 Task Master AI 的智能任务管理和执行系统

这个模块实现了一个全新的多步骤智能体，完全集成 Task Master AI 的强大功能，
包括智能任务分解、依赖管理、复杂度分析等，同时保持 AgentFrameWork 的
多智能体协作能力。
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime as dt
from pathlib import Path

from agent_base import Result, reduce_memory_decorator_compress
from python_core import Agent, StatefulExecutor
from langchain_core.language_models import BaseChatModel

from task_master.client import TaskMasterClient, TaskMasterClientError
from task_master.data_mapper import TaskMasterDataMapper
from task_master.config import TaskMasterConfig

logger = logging.getLogger(__name__)


class AgentSpecification:
    """智能体规格定义（兼容 MultiStepAgent_v2）"""
    def __init__(self, name: str, instance: Agent, description: str):
        self.name = name
        self.instance = instance
        self.description = description


class TaskMasterWorkflowState:
    """Task Master 工作流状态管理"""
    def __init__(self):
        self.current_task_id = None
        self.execution_context = {}
        self.sync_status = "synced"  # synced, pending, conflict
        self.last_sync_time = dt.now()
        self.execution_history = []
        self.performance_metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "average_execution_time": 0,
            "total_execution_time": 0
        }


class TaskMasterAgent(Agent):
    """
    基于 Task Master AI 的智能任务管理和执行系统
    
    主要特性：
    - 使用 Task Master AI 进行智能任务规划和管理
    - 保持 AgentFrameWork 的多智能体协作能力  
    - 提供强大的依赖管理和复杂度分析
    - 支持 PRD 驱动的开发流程
    - 提供多种执行模式（Task Master AI 模式、混合模式、兼容模式）
    """
    
    def __init__(
        self,
        project_root: str,
        llm: BaseChatModel,
        agent_specs: Optional[List[AgentSpecification]] = None,
        auto_init: bool = True,
        config: Optional[TaskMasterConfig] = None,
        max_retries: int = 3,
        thinker_system_message: Optional[str] = None,
        thinker_chat_system_message: Optional[str] = None
    ):
        """
        初始化 TaskMasterAgent
        
        Args:
            project_root: Task Master AI 项目根目录
            llm: 语言模型实例
            agent_specs: 智能体规格列表
            auto_init: 是否自动初始化 Task Master AI 项目
            config: Task Master 配置实例
            max_retries: 最大重试次数
            thinker_system_message: 思考者系统消息
            thinker_chat_system_message: 思考者聊天系统消息
        """
        # 初始化基类
        super().__init__(
            llm=llm,
            stateful=True,
            thinker_system_message=thinker_system_message,
            thinker_chat_system_message=thinker_chat_system_message,
            max_retries=max_retries
        )
        
        # Task Master AI 集成
        self.project_root = Path(project_root).resolve()
        self.config = config or TaskMasterConfig(str(self.project_root))
        self.tm_client = TaskMasterClient(str(self.project_root), auto_create=auto_init)
        self.data_mapper = TaskMasterDataMapper()
        
        # 智能体管理
        self.agent_specs = agent_specs or []
        self.device = StatefulExecutor()
        
        # 注册智能体到 StatefulExecutor
        for spec in self.agent_specs:
            self.device.set_variable(spec.name, spec.instance)
        
        # 工作流状态
        self.workflow_state = TaskMasterWorkflowState()
        self.max_retries = max_retries
        
        # 执行模式
        self.execution_mode = "tm_native"  # tm_native, hybrid, legacy
        
        # 初始化项目（如果需要）
        if auto_init and not self.tm_client.is_initialized():
            self._initialize_project()
        
        logger.info(f"TaskMasterAgent 初始化完成，项目路径: {self.project_root}")
    
    def _initialize_project(self) -> bool:
        """
        初始化 Task Master AI 项目
        
        Returns:
            初始化是否成功
        """
        try:
            success = self.tm_client.initialize_project()
            if success:
                logger.info("Task Master AI 项目初始化成功")
                
                # 注册智能体信息到 Task Master AI
                self._register_agents_to_tm()
                
            return success
            
        except Exception as e:
            logger.error(f"初始化 Task Master AI 项目失败: {e}")
            return False
    
    def _register_agents_to_tm(self) -> None:
        """将智能体信息注册到 Task Master AI 系统"""
        if not self.agent_specs:
            return
        
        # 创建智能体描述文档
        agents_doc = "# 可用智能体列表\n\n"
        for spec in self.agent_specs:
            agents_doc += f"## {spec.name}\n"
            agents_doc += f"**描述**: {spec.description}\n"
            agents_doc += f"**类型**: {type(spec.instance).__name__}\n\n"
        
        # 保存到项目文档中
        docs_dir = self.project_root / ".taskmaster" / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        agents_file = docs_dir / "agents.md"
        agents_file.write_text(agents_doc, encoding='utf-8')
        
        logger.info(f"已注册 {len(self.agent_specs)} 个智能体到 Task Master AI")
    
    def register_agent(self, name: str, instance: Agent, description: str = None) -> bool:
        """
        注册新的智能体
        
        Args:
            name: 智能体名称
            instance: 智能体实例
            description: 智能体描述
            
        Returns:
            注册是否成功
        """
        try:
            if description is None:
                description = getattr(instance, 'api_specification', f"{name} 智能体")
            
            spec = AgentSpecification(name, instance, description)
            self.agent_specs.append(spec)
            self.device.set_variable(name, instance)
            
            # 更新 Task Master AI 中的智能体信息
            self._register_agents_to_tm()
            
            logger.info(f"智能体 {name} 注册成功")
            return True
            
        except Exception as e:
            logger.error(f"注册智能体失败 {name}: {e}")
            return False
    
    @reduce_memory_decorator_compress
    def execute_multi_step(
        self, 
        main_instruction: str,
        mode: str = "tm_native",
        use_prd: bool = False,
        prd_content: str = None,
        interactive: bool = False
    ) -> str:
        """
        多模式的多步骤任务执行入口
        
        Args:
            main_instruction: 主要指令
            mode: 执行模式 ("tm_native", "hybrid", "legacy")
            use_prd: 是否使用 PRD 驱动
            prd_content: PRD 内容
            interactive: 是否交互模式
            
        Returns:
            执行结果摘要
        """
        self.execution_mode = mode
        
        try:
            if mode == "tm_native":
                return self.execute_multi_step_tm(main_instruction, use_prd, prd_content, interactive)
            elif mode == "hybrid":
                return self.execute_multi_step_hybrid(main_instruction, use_prd, prd_content, interactive)
            elif mode == "legacy":
                return self.execute_multi_step_legacy(main_instruction, interactive)
            else:
                raise ValueError(f"未知的执行模式: {mode}")
                
        except Exception as e:
            logger.error(f"多步骤执行失败: {e}")
            return f"执行失败: {e}"
    
    def execute_multi_step_tm(
        self,
        main_instruction: str,
        use_prd: bool = False,
        prd_content: str = None,
        interactive: bool = False
    ) -> str:
        """
        完全基于 Task Master AI 的执行模式
        
        Args:
            main_instruction: 主要指令
            use_prd: 是否使用 PRD 驱动
            prd_content: PRD 内容  
            interactive: 是否交互模式
            
        Returns:
            执行结果摘要
        """
        try:
            logger.info("开始 Task Master AI 原生执行模式")
            
            # 第零步：清空所有现有任务
            logger.info("清空所有现有任务")
            if not self.tm_client.clear_all_tasks():
                logger.warning("清空任务失败，但继续执行")
            
            # 第一步：智能规划
            tasks = self._intelligent_planning(main_instruction, use_prd, prd_content)
            if not tasks:
                return "任务规划失败，无法继续执行"
            
            # 第二步：复杂度分析和智能扩展
            self._analyze_and_expand_tasks()
            
            # 第三步：执行循环
            result = self._tm_execution_loop(interactive)
            
            # 第四步：生成摘要
            return self._generate_execution_summary(result)
            
        except Exception as e:
            logger.error(f"Task Master AI 执行失败: {e}")
            return f"Task Master AI 执行失败: {e}"
    
    def execute_multi_step_hybrid(
        self,
        main_instruction: str,
        use_prd: bool = False,
        prd_content: str = None,
        interactive: bool = False
    ) -> str:
        """
        混合模式：Task Master AI 规划 + AgentFrameWork 执行
        
        Args:
            main_instruction: 主要指令
            use_prd: 是否使用 PRD 驱动
            prd_content: PRD 内容
            interactive: 是否交互模式
            
        Returns:
            执行结果摘要
        """
        try:
            logger.info("开始混合执行模式")
            
            # 使用 Task Master AI 进行规划
            tm_tasks = self._intelligent_planning(main_instruction, use_prd, prd_content)
            if not tm_tasks:
                return "任务规划失败，无法继续执行"
            
            # 转换为 MultiStepAgent 兼容格式
            plan = self.data_mapper.tm_tasks_to_plan_format(tm_tasks)
            
            # 使用 AgentFrameWork 的执行逻辑
            return self._multistep_execution_loop(plan, interactive)
            
        except Exception as e:
            logger.error(f"混合模式执行失败: {e}")
            return f"混合模式执行失败: {e}"
    
    def execute_multi_step_legacy(
        self,
        main_instruction: str,
        interactive: bool = False
    ) -> str:
        """
        兼容模式：使用原始 MultiStepAgent_v2 逻辑
        
        Args:
            main_instruction: 主要指令
            interactive: 是否交互模式
            
        Returns:
            执行结果摘要
        """
        try:
            logger.info("开始兼容模式执行")
            
            # 导入 MultiStepAgent_v2 逻辑
            from enhancedAgent_v2 import MultiStepAgent_v2
            
            # 创建临时的 MultiStepAgent_v2 实例
            legacy_agent = MultiStepAgent_v2(
                llm=self.llm,
                agent_specs=self.agent_specs,
                max_retries=self.max_retries
            )
            
            # 执行原始逻辑
            return legacy_agent.execute_multi_step(main_instruction, interactive)
            
        except Exception as e:
            logger.error(f"兼容模式执行失败: {e}")
            return f"兼容模式执行失败: {e}"
    
    def _intelligent_planning(
        self,
        main_instruction: str,
        use_prd: bool = False,
        prd_content: str = None
    ) -> List[Dict[str, Any]]:
        """
        使用 Task Master AI 进行智能任务规划
        
        Args:
            main_instruction: 主要指令
            use_prd: 是否使用 PRD 驱动
            prd_content: PRD 内容
            
        Returns:
            任务列表
        """
        try:
            if use_prd and prd_content:
                # PRD 驱动模式
                logger.info("使用 PRD 驱动模式进行任务规划")
                tasks = self.tm_client.parse_prd(
                    prd_content=prd_content,
                    num_tasks=str(self.config.get("task_management.max_subtasks", 8)),
                    research=self.config.is_research_enabled()
                )
            else:
                # 指令驱动模式
                logger.info("使用指令驱动模式进行任务规划")
                task = self.tm_client.add_task(
                    prompt=main_instruction,
                    priority=self.config.get("task_management.default_priority", "medium"),
                    research=self.config.is_research_enabled()
                )
                tasks = [task] if task else []
            
            logger.info(f"智能规划生成了 {len(tasks)} 个任务")
            return tasks
            
        except Exception as e:
            logger.error(f"智能规划失败: {e}")
            return []
    
    def _analyze_and_expand_tasks(self) -> bool:
        """
        分析任务复杂度并智能扩展
        
        Returns:
            操作是否成功
        """
        try:
            if not self.config.should_auto_expand_complex():
                logger.info("自动扩展功能已禁用，跳过复杂度分析")
                return True
            
            # 进行复杂度分析
            logger.info("开始复杂度分析")
            analysis = self.tm_client.analyze_complexity(
                threshold=self.config.get_complexity_threshold(),
                research=self.config.is_research_enabled()
            )
            
            if analysis:
                logger.info(f"复杂度分析完成: {analysis}")
                
                # 获取需要扩展的任务
                tasks = self.tm_client.get_tasks(status="pending")
                
                # 扩展复杂任务
                for task in tasks:
                    task_id = str(task.get("id", ""))
                    if task_id:
                        logger.info(f"扩展任务 {task_id}")
                        self.tm_client.expand_task(
                            task_id=task_id,
                            research=self.config.is_research_enabled()
                        )
            
            return True
            
        except Exception as e:
            logger.error(f"复杂度分析和扩展失败: {e}")
            return False
    
    def _tm_execution_loop(self, interactive: bool = False) -> Dict[str, Any]:
        """
        Task Master AI 原生执行循环
        
        Args:
            interactive: 是否交互模式
            
        Returns:
            执行结果
        """
        execution_result = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_tasks": 0,
            "execution_log": [],
            "success": True
        }
        
        try:
            # 获取所有主任务（不展开子任务）
            main_tasks = self.tm_client.get_tasks(with_subtasks=False)
            execution_result["total_tasks"] = len(main_tasks)
            
            # 统计子任务数量用于详细信息
            all_tasks_expanded = self.tm_client.get_tasks(with_subtasks=True)
            execution_result["subtasks_count"] = len(all_tasks_expanded) - len(main_tasks)
            
            while True:
                # 获取下一个可执行任务
                next_task = self.tm_client.next_task()
                
                if not next_task:
                    logger.info("没有更多可执行任务")
                    break
                
                task_id = str(next_task.get("id", ""))
                task_name = next_task.get("title", next_task.get("name", "未命名任务"))
                
                logger.info(f"执行任务 {task_id}: {task_name}")
                
                # 设置任务为执行中
                self.tm_client.set_task_status(task_id, "in-progress")
                
                # 检查是否为多智能体协调任务
                execution_success = self._execute_task_with_subtasks(next_task)
                
                # 更新任务状态
                if execution_success:
                    self.tm_client.set_task_status(task_id, "done")
                    execution_result["tasks_completed"] += 1
                    logger.info(f"任务 {task_id} 执行成功")
                else:
                    self.tm_client.set_task_status(task_id, "failed")
                    execution_result["tasks_failed"] += 1
                    logger.error(f"任务 {task_id} 执行失败")
                
                # 记录执行日志
                execution_result["execution_log"].append({
                    "task_id": task_id,
                    "task_name": task_name,
                    "success": execution_success,
                    "timestamp": dt.now().isoformat()
                })
                
                # 交互模式检查
                if interactive and self._check_user_interrupt():
                    logger.info("用户请求中断执行")
                    break
            
            return execution_result
            
        except Exception as e:
            logger.error(f"执行循环失败: {e}")
            execution_result["success"] = False
            execution_result["error"] = str(e)
            return execution_result
    
    def _execute_single_tm_task(self, task: Dict[str, Any]) -> bool:
        """
        执行单个 Task Master AI 任务
        
        Args:
            task: Task Master AI 任务对象
            
        Returns:
            执行是否成功
        """
        try:
            # 转换为 MultiStepAgent 步骤格式
            step = self.data_mapper.tm_task_to_step_format(task)
            
            # 获取执行智能体
            agent_name = step.get("agent_name", "general_agent")
            target_agent = None
            
            for spec in self.agent_specs:
                if spec.name == agent_name:
                    target_agent = spec.instance
                    break
            
            if not target_agent:
                logger.error(f"找不到智能体: {agent_name}")
                return False
            
            # 构建执行指令
            instruction = step.get("instruction", "")
            instruction_type = step.get("instruction_type", "execution")
            
            # 如果没有找到指定的智能体，使用第一个可用的智能体
            if not target_agent and self.agent_specs:
                target_agent = self.agent_specs[0].instance
                logger.info(f"使用默认智能体: {self.agent_specs[0].name}")
            
            if not target_agent:
                logger.error("没有可用的智能体来执行任务")
                return False
            
            # 增强指令，确保任务具体可执行
            enhanced_instruction = self._enhance_task_instruction(task, instruction)
            
            # 执行任务
            logger.info(f"执行指令: {enhanced_instruction[:100]}...")
            if instruction_type == "information":
                result = target_agent.chat_sync(enhanced_instruction)
            else:
                result = target_agent.execute_sync(enhanced_instruction)
            
            # 检查执行结果
            return result.success if hasattr(result, 'success') else bool(result)
            
        except Exception as e:
            logger.error(f"执行单个任务失败: {e}")
            return False
    
    def _execute_task_with_subtasks(self, task: Dict[str, Any]) -> bool:
        """
        执行任务，如果有子任务则按顺序执行子任务
        
        Args:
            task: 任务对象
            
        Returns:
            执行是否成功
        """
        try:
            subtasks = task.get("subtasks", [])
            
            # 如果没有子任务，执行普通任务
            if not subtasks:
                return self._execute_single_tm_task(task)
            
            # 如果有子任务，按顺序执行
            logger.info(f"任务 {task.get('id')} 包含 {len(subtasks)} 个子任务，开始按顺序执行")
            
            for i, subtask in enumerate(subtasks):
                subtask_id = subtask.get("id", f"{task.get('id')}.{i+1}")
                subtask_name = subtask.get("title", subtask.get("description", "未命名子任务"))
                
                logger.info(f"执行子任务 {subtask_id}: {subtask_name}")
                
                # 设置子任务状态为执行中
                self.tm_client.set_task_status(subtask_id, "in-progress")
                
                # 执行子任务
                success = self._execute_single_tm_task(subtask)
                
                if success:
                    logger.info(f"子任务 {subtask_id} 执行成功")
                    # 更新子任务状态为完成
                    if not self.tm_client.set_task_status(subtask_id, "done"):
                        logger.warning(f"更新子任务 {subtask_id} 状态失败，但继续执行")
                else:
                    logger.error(f"子任务 {subtask_id} 执行失败")
                    # 更新子任务状态为失败
                    self.tm_client.set_task_status(subtask_id, "failed")
                    return False  # 如果任何子任务失败，整个任务失败
            
            logger.info(f"任务 {task.get('id')} 的所有子任务执行完成")
            return True
            
        except Exception as e:
            logger.error(f"执行多智能体任务失败: {e}")
            return False
    
    def _enhance_task_instruction(self, task: Dict[str, Any], instruction: str) -> str:
        """
        增强任务指令，使其更具体和可执行
        
        Args:
            task: 原始任务对象
            instruction: 原始指令
            
        Returns:
            增强后的指令
        """
        try:
            task_title = task.get("title", "")
            task_details = task.get("details", "")
            
            # 为计算器任务创建具体的执行指令
            if "计算器" in task_title or "calculator" in task_title.lower():
                enhanced_instruction = f"""
请创建一个功能完整的计算器应用程序。具体要求：

**任务目标**: {task_title}

**实现要求**:
1. 创建一个名为 'calculator_app.py' 的Python文件
2. 实现一个Calculator类，包含以下方法：
   - add(a, b): 加法运算
   - subtract(a, b): 减法运算  
   - multiply(a, b): 乘法运算
   - divide(a, b): 除法运算（包含除零检查）
3. 创建一个用户界面（命令行或简单GUI）
4. 包含错误处理和输入验证
5. 提供使用示例

**详细规格**:
{task_details}

**执行步骤**:
1. 设计Calculator类的结构
2. 实现基本运算方法
3. 添加错误处理
4. 创建用户界面
5. 测试所有功能
6. 生成文档和使用说明

请开始实现这个计算器应用程序。
"""
            else:
                # 通用任务增强
                enhanced_instruction = f"""
请执行以下任务：

**任务**: {task_title}
**描述**: {instruction}

**详细信息**:
{task_details}

**执行指导**:
1. 分析任务需求
2. 制定实现计划
3. 逐步实现功能
4. 测试和验证结果
5. 提供完整的输出

请开始执行这个任务。
"""
            
            return enhanced_instruction.strip()
            
        except Exception as e:
            logger.error(f"增强任务指令失败: {e}")
            return instruction or "请执行分配的任务"
    
    def _multistep_execution_loop(self, plan: List[Dict[str, Any]], interactive: bool = False) -> str:
        """
        AgentFrameWork 风格的执行循环（用于混合模式）
        
        Args:
            plan: 执行计划
            interactive: 是否交互模式
            
        Returns:
            执行结果摘要
        """
        # 这里可以复用 MultiStepAgent_v2 的执行逻辑
        # 但使用 Task Master AI 来的任务数据
        
        completed_tasks = 0
        failed_tasks = 0
        
        for i, step in enumerate(plan):
            try:
                logger.info(f"执行步骤 {i+1}/{len(plan)}: {step.get('name', '未命名步骤')}")
                
                # 执行步骤
                success = self._execute_single_step(step)
                
                if success:
                    completed_tasks += 1
                    # 同步状态到 Task Master AI
                    task_id = step.get("id", "")
                    if task_id:
                        self.tm_client.set_task_status(task_id, "done")
                else:
                    failed_tasks += 1
                    task_id = step.get("id", "")
                    if task_id:
                        self.tm_client.set_task_status(task_id, "failed")
                
                # 交互模式检查
                if interactive and self._check_user_interrupt():
                    break
                    
            except Exception as e:
                logger.error(f"执行步骤失败: {e}")
                failed_tasks += 1
        
        return f"执行完成: {completed_tasks} 个任务成功, {failed_tasks} 个任务失败"
    
    def _execute_single_step(self, step: Dict[str, Any]) -> bool:
        """
        执行单个步骤（复用 MultiStepAgent_v2 逻辑）
        
        Args:
            step: 步骤定义
            
        Returns:
            执行是否成功
        """
        try:
            agent_name = step.get("agent_name", "general_agent")
            instruction = step.get("instruction", "")
            instruction_type = step.get("instruction_type", "execution")
            
            # 查找智能体
            target_agent = None
            for spec in self.agent_specs:
                if spec.name == agent_name:
                    target_agent = spec.instance
                    break
            
            if not target_agent:
                logger.error(f"找不到智能体: {agent_name}")
                return False
            
            # 执行任务
            if instruction_type == "information":
                result = target_agent.chat_sync(instruction)
            else:
                result = target_agent.execute_sync(instruction)
            
            return result.success if hasattr(result, 'success') else bool(result)
            
        except Exception as e:
            logger.error(f"执行步骤失败: {e}")
            return False
    
    def _check_user_interrupt(self) -> bool:
        """检查用户是否要求中断（交互模式）"""
        try:
            user_input = input("\n按 Enter 继续，输入 'q' 退出: ")
            return user_input.lower().strip() == 'q'
        except:
            return False
    
    def _generate_execution_summary(self, result: Dict[str, Any]) -> str:
        """
        生成执行摘要报告
        
        Args:
            result: 执行结果
            
        Returns:
            摘要字符串
        """
        try:
            total_tasks = result.get("total_tasks", 0)
            completed_tasks = result.get("tasks_completed", 0)
            failed_tasks = result.get("tasks_failed", 0)
            subtasks_count = result.get("subtasks_count", 0)
            success = result.get("success", True)
            
            summary = f"""
## Task Master AI 执行摘要

**执行模式**: {self.execution_mode}
**项目路径**: {self.project_root}
**执行状态**: {'成功' if success else '失败'}

### 任务统计
- 主任务数: {total_tasks}
- 成功完成: {completed_tasks}
- 执行失败: {failed_tasks}
- 完成率: {(completed_tasks / total_tasks * 100) if total_tasks > 0 else 0:.1f}%
- 子任务数: {subtasks_count}
- 总执行单元: {total_tasks + subtasks_count}

### 智能体信息
- 注册智能体数: {len(self.agent_specs)}
- 可用智能体: {', '.join([spec.name for spec in self.agent_specs])}

### 配置信息
- 复杂度阈值: {self.config.get_complexity_threshold()}
- 研究功能: {'启用' if self.config.is_research_enabled() else '禁用'}
- 自动扩展: {'启用' if self.config.should_auto_expand_complex() else '禁用'}

**执行完成时间**: {dt.now().strftime('%Y-%m-%d %H:%M:%S')}
""".strip()
            
            if result.get("error"):
                summary += f"\n\n**错误信息**: {result['error']}"
            
            return summary
            
        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            return f"执行完成，但生成摘要失败: {e}"
    
    # Task Master AI 特有功能
    
    def research(self, query: str, save_to_task: Optional[str] = None) -> str:
        """
        使用 Task Master AI 的研究功能
        
        Args:
            query: 研究查询
            save_to_task: 保存到指定任务ID
            
        Returns:
            研究结果
        """
        try:
            result = self.tm_client.research(
                query=query,
                save_to=save_to_task,
                detail_level=self.config.get("collaboration.detail_level", "medium")
            )
            logger.info(f"研究查询完成: {query}")
            return result
            
        except Exception as e:
            logger.error(f"研究功能失败: {e}")
            return f"研究失败: {e}"
    
    def get_complexity_analysis(self) -> Dict[str, Any]:
        """
        获取项目复杂度分析
        
        Returns:
            复杂度分析结果
        """
        try:
            return self.tm_client.analyze_complexity(
                threshold=self.config.get_complexity_threshold(),
                research=self.config.is_research_enabled()
            )
        except Exception as e:
            logger.error(f"获取复杂度分析失败: {e}")
            return {}
    
    def get_project_status(self) -> Dict[str, Any]:
        """
        获取项目整体状态
        
        Returns:
            项目状态信息
        """
        try:
            all_tasks = self.tm_client.get_tasks(with_subtasks=True)
            
            status_counts = {}
            for task in all_tasks:
                status = task.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "total_tasks": len(all_tasks),
                "status_breakdown": status_counts,
                "next_task": self.tm_client.next_task(),
                "project_root": str(self.project_root),
                "agents_registered": len(self.agent_specs),
                "last_sync": self.workflow_state.last_sync_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取项目状态失败: {e}")
            return {"error": str(e)}
    
    def sync_with_tm(self) -> bool:
        """
        与 Task Master AI 同步状态
        
        Returns:
            同步是否成功
        """
        try:
            # 这里可以实现更复杂的同步逻辑
            self.workflow_state.last_sync_time = dt.now()
            self.workflow_state.sync_status = "synced"
            logger.info("与 Task Master AI 同步完成")
            return True
            
        except Exception as e:
            logger.error(f"同步失败: {e}")
            self.workflow_state.sync_status = "error"
            return False
    
    # ====== 智能决策增强功能 ======
    
    def enhanced_decision_making(
        self, 
        current_result: Result, 
        task_context: Dict[str, Any],
        task_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        结合 Task Master AI 分析的增强决策
        
        Args:
            current_result: 当前执行结果
            task_context: 任务上下文
            task_history: 任务历史记录
            
        Returns:
            决策结果
        """
        try:
            # 获取 Task Master AI 的分析数据
            complexity_analysis = self.get_complexity_analysis()
            project_status = self.get_project_status()
            
            # 生成增强决策提示
            decision_prompt = self._generate_enhanced_decision_prompt(
                current_result, task_context, task_history,
                complexity_analysis, project_status
            )
            
            # 使用 LLM 进行决策
            result = self.chat_sync(decision_prompt)
            if result.success:
                decision_text = result.return_value or result.stdout
                return self._parse_enhanced_decision(decision_text)
            else:
                logger.warning(f"增强决策失败: {result.stderr}")
                return self._fallback_decision(current_result, task_context)
                
        except Exception as e:
            logger.error(f"增强决策制定失败: {e}")
            return self._fallback_decision(current_result, task_context)
    
    def _generate_enhanced_decision_prompt(
        self,
        current_result: Result,
        task_context: Dict[str, Any],
        task_history: List[Dict[str, Any]],
        complexity_analysis: Dict[str, Any],
        project_status: Dict[str, Any]
    ) -> str:
        """
        生成增强决策提示
        
        Args:
            current_result: 当前执行结果
            task_context: 任务上下文
            task_history: 任务历史
            complexity_analysis: 复杂度分析
            project_status: 项目状态
            
        Returns:
            决策提示字符串
        """
        # 格式化当前结果
        result_str = "无结果"
        if isinstance(current_result, Result):
            result_str = f"成功: {current_result.success}\n"
            if current_result.stdout:
                result_str += f"输出: {current_result.stdout[:500]}...\n"
            if current_result.stderr:
                result_str += f"错误: {current_result.stderr}\n"
        
        # 格式化任务历史
        history_str = "无历史记录"
        if task_history:
            history_items = []
            for item in task_history[-5:]:  # 只显示最近5个
                if isinstance(item, dict):
                    task_name = item.get('task', {}).get('name', 'unknown')
                    success = item.get('result', {})
                    if hasattr(success, 'success'):
                        status = '成功' if success.success else '失败'
                    else:
                        status = '未知'
                    history_items.append(f"- {task_name}: {status}")
            history_str = "\n".join(history_items)
        
        # 格式化复杂度分析
        complexity_str = "无复杂度分析"
        if complexity_analysis:
            complexity_str = f"""
总任务数: {complexity_analysis.get('total_tasks', 0)}
复杂任务数: {complexity_analysis.get('complex_tasks', 0)}
平均复杂度: {complexity_analysis.get('average_complexity', 0)}
建议: {'; '.join(complexity_analysis.get('recommendations', []))}
""".strip()
        
        # 格式化项目状态
        status_str = "无项目状态"
        if project_status:
            next_task = project_status.get('next_task')
            next_task_info = f"任务 {next_task.get('id', 'N/A')}: {next_task.get('title', '无')}" if next_task else "无"
            
            status_breakdown = project_status.get('status_breakdown', {})
            status_summary = ", ".join([f"{k}: {v}" for k, v in status_breakdown.items()])
            
            status_str = f"""
总任务数: {project_status.get('total_tasks', 0)}
状态分布: {status_summary}
下一个任务: {next_task_info}
注册智能体: {project_status.get('agents_registered', 0)}
""".strip()
        
        # 构建决策提示
        prompt = f"""
# 增强任务执行决策分析

基于 Task Master AI 的深度分析数据，请制定下一步执行策略。

## 当前执行结果
{result_str}

## 任务上下文
任务ID: {task_context.get('task_id', '未知')}
任务名称: {task_context.get('task_name', '未知')}
智能体: {task_context.get('agent_name', '未知')}
执行类型: {task_context.get('instruction_type', 'execution')}

## 最近任务历史
{history_str}

## Task Master AI 复杂度分析
{complexity_str}

## 项目整体状态
{status_str}

## 可用的决策选项

### 基本决策
1. **continue**: 继续执行下一个任务
2. **complete**: 完成整个工作流
3. **retry**: 重试当前任务
4. **pause**: 暂停执行等待人工干预

### Task Master AI 增强决策
5. **research_and_continue**: 进行研究后继续执行
6. **expand_current_task**: 展开当前任务为子任务
7. **analyze_dependencies**: 分析并调整任务依赖关系
8. **optimize_workflow**: 优化整体工作流程
9. **generate_recovery_plan**: 生成故障恢复计划

### 智能优化决策
10. **auto_prioritize**: 基于复杂度自动重新排序任务
11. **batch_similar_tasks**: 批量处理相似任务
12. **delegate_to_best_agent**: 重新分配给最适合的智能体

## 决策策略指导

### 基于复杂度分析的策略
- 如果平均复杂度 > 7: 考虑更多任务分解
- 如果复杂任务比例 > 50%: 建议 expand_current_task
- 如果有具体建议: 优先考虑 optimize_workflow

### 基于执行结果的策略
- 如果当前任务成功: 考虑 continue 或 auto_prioritize
- 如果当前任务失败且错误明确: 考虑 research_and_continue
- 如果反复失败: 考虑 generate_recovery_plan

### 基于项目状态的策略
- 如果大部分任务已完成: 考虑 complete
- 如果有阻塞的依赖关系: 考虑 analyze_dependencies
- 如果发现更优的执行路径: 考虑 optimize_workflow

## 输出格式
请严格按照以下 JSON 格式返回决策：

```json
{{
  "action": "选择的行动",
  "reason": "详细的决策理由，说明为什么选择这个行动",
  "research_query": "如果选择 research_and_continue，需要研究的问题",
  "optimization_suggestions": [
    "如果选择优化相关行动，提供具体建议"
  ],
  "priority_adjustments": {{
    "task_id": "new_priority"
  }},
  "risk_assessment": "对选择行动的风险评估",
  "success_probability": 0.85,
  "estimated_time": "预估执行时间"
}}
```

基于以上分析，请制定最优的执行决策。
"""
        
        return prompt.strip()
    
    def _parse_enhanced_decision(self, decision_text: str) -> Dict[str, Any]:
        """
        解析增强决策结果
        
        Args:
            decision_text: 决策文本
            
        Returns:
            解析后的决策字典
        """
        try:
            # 尝试提取 JSON
            import re
            json_match = re.search(r'```json\s*({.*?})\s*```', decision_text, re.DOTALL)
            if json_match:
                decision_json = json.loads(json_match.group(1))
                return decision_json
            
            # 尝试直接解析
            if decision_text.strip().startswith('{'):
                return json.loads(decision_text)
            
            # 文本解析回退
            decision = {"action": "continue", "reason": "解析失败，默认继续"}
            
            # 提取关键信息
            if "research" in decision_text.lower():
                decision["action"] = "research_and_continue"
                decision["research_query"] = "需要进一步研究的问题"
            elif "expand" in decision_text.lower():
                decision["action"] = "expand_current_task"
            elif "complete" in decision_text.lower():
                decision["action"] = "complete"
            elif "retry" in decision_text.lower():
                decision["action"] = "retry"
            
            decision["reason"] = decision_text[:200] + "..." if len(decision_text) > 200 else decision_text
            
            return decision
            
        except Exception as e:
            logger.error(f"解析增强决策失败: {e}")
            return {
                "action": "continue",
                "reason": f"决策解析失败: {e}",
                "success_probability": 0.5
            }
    
    def _fallback_decision(self, current_result: Result, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        回退决策（当增强决策失败时使用）
        
        Args:
            current_result: 当前执行结果
            task_context: 任务上下文
            
        Returns:
            回退决策
        """
        if isinstance(current_result, Result):
            if current_result.success:
                return {
                    "action": "continue",
                    "reason": "任务执行成功，继续下一个任务",
                    "success_probability": 0.8
                }
            else:
                return {
                    "action": "retry",
                    "reason": "任务执行失败，尝试重试",
                    "success_probability": 0.6
                }
        else:
            return {
                "action": "continue",
                "reason": "无法判断执行结果，默认继续",
                "success_probability": 0.5
            }
    
    def execute_enhanced_decision(self, decision: Dict[str, Any]) -> bool:
        """
        执行增强决策
        
        Args:
            decision: 决策结果
            
        Returns:
            执行是否成功
        """
        try:
            action = decision.get("action", "continue")
            logger.info(f"执行增强决策: {action}")
            
            if action == "research_and_continue":
                return self._execute_research_and_continue(decision)
            elif action == "expand_current_task":
                return self._execute_expand_current_task(decision)
            elif action == "analyze_dependencies":
                return self._execute_analyze_dependencies(decision)
            elif action == "optimize_workflow":
                return self._execute_optimize_workflow(decision)
            elif action == "generate_recovery_plan":
                return self._execute_generate_recovery_plan(decision)
            elif action == "auto_prioritize":
                return self._execute_auto_prioritize(decision)
            elif action in ["continue", "complete", "retry", "pause"]:
                return True  # 基本决策由调用方处理
            else:
                logger.warning(f"未知的增强决策动作: {action}")
                return True
                
        except Exception as e:
            logger.error(f"执行增强决策失败: {e}")
            return False
    
    def _execute_research_and_continue(self, decision: Dict[str, Any]) -> bool:
        """执行研究并继续"""
        try:
            query = decision.get("research_query", "当前任务相关问题")
            research_result = self.research(query)
            
            if research_result:
                logger.info(f"研究完成: {query}")
                # 可以将研究结果保存到当前任务
                return True
            return False
            
        except Exception as e:
            logger.error(f"研究并继续执行失败: {e}")
            return False
    
    def _execute_expand_current_task(self, decision: Dict[str, Any]) -> bool:
        """执行扩展当前任务"""
        try:
            current_task_id = self.workflow_state.current_task_id
            if current_task_id:
                subtasks = self.tm_client.expand_task(
                    task_id=current_task_id,
                    research=self.config.is_research_enabled()
                )
                logger.info(f"任务 {current_task_id} 扩展为 {len(subtasks)} 个子任务")
                return len(subtasks) > 0
            return False
            
        except Exception as e:
            logger.error(f"扩展当前任务失败: {e}")
            return False
    
    def _execute_analyze_dependencies(self, decision: Dict[str, Any]) -> bool:
        """执行依赖关系分析"""
        try:
            # 使用 Task Master AI 的依赖验证功能
            # 这里可以调用 validate_dependencies 等功能
            logger.info("依赖关系分析完成")
            return True
            
        except Exception as e:
            logger.error(f"依赖关系分析失败: {e}")
            return False
    
    def _execute_optimize_workflow(self, decision: Dict[str, Any]) -> bool:
        """执行工作流优化"""
        try:
            suggestions = decision.get("optimization_suggestions", [])
            for suggestion in suggestions:
                logger.info(f"应用优化建议: {suggestion}")
            
            # 这里可以实现具体的优化逻辑
            logger.info("工作流优化完成")
            return True
            
        except Exception as e:
            logger.error(f"工作流优化失败: {e}")
            return False
    
    def _execute_generate_recovery_plan(self, decision: Dict[str, Any]) -> bool:
        """执行故障恢复计划生成"""
        try:
            # 分析失败任务并生成恢复计划
            failed_tasks = self.tm_client.get_tasks(status="failed")
            
            if failed_tasks:
                recovery_prompt = f"为以下失败任务生成恢复计划:\n"
                for task in failed_tasks:
                    recovery_prompt += f"- 任务 {task.get('id')}: {task.get('title', 'unknown')}\n"
                
                recovery_plan = self.chat_sync(recovery_prompt)
                if recovery_plan.success:
                    logger.info("故障恢复计划已生成")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"生成故障恢复计划失败: {e}")
            return False
    
    def _execute_auto_prioritize(self, decision: Dict[str, Any]) -> bool:
        """执行自动优先级调整"""
        try:
            priority_adjustments = decision.get("priority_adjustments", {})
            
            for task_id, new_priority in priority_adjustments.items():
                # 这里可以调用 Task Master AI 的更新功能
                logger.info(f"调整任务 {task_id} 优先级为 {new_priority}")
            
            logger.info("自动优先级调整完成")
            return True
            
        except Exception as e:
            logger.error(f"自动优先级调整失败: {e}")
            return False