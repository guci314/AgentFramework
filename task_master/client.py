"""
Task Master AI MCP 工具的 Python 封装客户端

这个模块提供了与 Task Master AI MCP 工具的完整集成，
封装了所有的任务管理操作为易用的 Python API。
"""

import json
import os
import subprocess
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class TaskMasterClientError(Exception):
    """Task Master Client 相关错误"""
    pass


class TaskMasterClient:
    """
    Task Master AI MCP 工具的 Python 封装客户端
    
    提供与 Task Master AI 的完整集成功能，包括项目初始化、
    任务管理、依赖处理、复杂度分析等功能。
    """
    
    def __init__(self, project_root: str, auto_create: bool = True):
        """
        初始化 Task Master 客户端
        
        Args:
            project_root: 项目根目录路径
            auto_create: 如果项目不存在是否自动创建
        """
        self.project_root = Path(project_root).resolve()
        self.taskmaster_dir = self.project_root / ".taskmaster"
        self.tasks_file = self.taskmaster_dir / "tasks" / "tasks.json"
        
        if auto_create and not self.is_initialized():
            self.initialize_project()
    
    def is_initialized(self) -> bool:
        """检查项目是否已初始化"""
        return self.taskmaster_dir.exists() and self.tasks_file.exists()
    
    def _run_mcp_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        运行 MCP 工具并返回结果
        
        Args:
            tool_name: MCP 工具名称
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
            
        Raises:
            TaskMasterClientError: 工具执行失败时抛出
        """
        try:
            # 这里是模拟实现，实际应该调用 MCP 工具
            # 在真实环境中，这将通过 MCP 协议与 Claude Code 通信
            
            # 模拟不同工具的响应
            if tool_name == "mcp__taskmaster-ai__initialize_project":
                return self._mock_initialize_project(**kwargs)
            elif tool_name == "mcp__taskmaster-ai__parse_prd":
                return self._mock_parse_prd(**kwargs)
            elif tool_name == "mcp__taskmaster-ai__add_task":
                return self._mock_add_task(**kwargs)
            elif tool_name == "mcp__taskmaster-ai__get_tasks":
                return self._mock_get_tasks(**kwargs)
            elif tool_name == "mcp__taskmaster-ai__next_task":
                return self._mock_next_task(**kwargs)
            elif tool_name == "mcp__taskmaster-ai__set_task_status":
                return self._mock_set_task_status(**kwargs)
            elif tool_name == "mcp__taskmaster-ai__expand_task":
                return self._mock_expand_task(**kwargs)
            elif tool_name == "mcp__taskmaster-ai__analyze_project_complexity":
                return self._mock_analyze_complexity(**kwargs)
            elif tool_name == "mcp__taskmaster-ai__add_dependency":
                return self._mock_add_dependency(**kwargs)
            elif tool_name == "mcp__taskmaster-ai__research":
                return self._mock_research(**kwargs)
            else:
                raise TaskMasterClientError(f"未知的 MCP 工具: {tool_name}")
                
        except Exception as e:
            logger.error(f"MCP 工具执行失败 {tool_name}: {e}")
            raise TaskMasterClientError(f"工具执行失败: {e}")
    
    def initialize_project(self, skip_install: bool = False, yes: bool = True) -> bool:
        """
        初始化 Task Master AI 项目
        
        Args:
            skip_install: 跳过依赖安装
            yes: 跳过确认提示
            
        Returns:
            初始化是否成功
        """
        try:
            result = self._run_mcp_tool(
                "mcp__taskmaster-ai__initialize_project",
                projectRoot=str(self.project_root),
                skipInstall=skip_install,
                yes=yes
            )
            return result.get("success", False)
        except TaskMasterClientError as e:
            logger.error(f"项目初始化失败: {e}")
            return False
    
    def parse_prd(self, prd_content: str, num_tasks: str = "10", 
                  research: bool = True) -> List[Dict]:
        """
        解析 PRD 生成任务
        
        Args:
            prd_content: PRD 内容
            num_tasks: 生成任务数量
            research: 是否启用研究功能
            
        Returns:
            生成的任务列表
        """
        # 先保存 PRD 内容到文件
        prd_file = self.taskmaster_dir / "docs" / "prd.txt"
        prd_file.parent.mkdir(parents=True, exist_ok=True)
        prd_file.write_text(prd_content, encoding='utf-8')
        
        try:
            result = self._run_mcp_tool(
                "mcp__taskmaster-ai__parse_prd",
                projectRoot=str(self.project_root),
                input=str(prd_file),
                numTasks=num_tasks,
                research=research
            )
            return result.get("tasks", [])
        except TaskMasterClientError as e:
            logger.error(f"PRD 解析失败: {e}")
            return []
    
    def add_task(self, prompt: str, dependencies: Optional[List[str]] = None,
                 priority: str = "medium", research: bool = False) -> Optional[Dict]:
        """
        添加新任务
        
        Args:
            prompt: 任务描述
            dependencies: 依赖任务ID列表
            priority: 任务优先级 (high/medium/low)
            research: 是否启用研究功能
            
        Returns:
            创建的任务信息
        """
        try:
            deps_str = ",".join(dependencies) if dependencies else ""
            result = self._run_mcp_tool(
                "mcp__taskmaster-ai__add_task",
                projectRoot=str(self.project_root),
                prompt=prompt,
                dependencies=deps_str,
                priority=priority,
                research=research
            )
            return result.get("task")
        except TaskMasterClientError as e:
            logger.error(f"添加任务失败: {e}")
            return None
    
    def get_tasks(self, status: Optional[str] = None, 
                  with_subtasks: bool = False) -> List[Dict]:
        """
        获取任务列表
        
        Args:
            status: 过滤状态 (pending/in_progress/done/failed)
            with_subtasks: 是否包含子任务
            
        Returns:
            任务列表
        """
        try:
            result = self._run_mcp_tool(
                "mcp__taskmaster-ai__get_tasks",
                projectRoot=str(self.project_root),
                status=status,
                withSubtasks=with_subtasks
            )
            return result.get("tasks", [])
        except TaskMasterClientError as e:
            logger.error(f"获取任务失败: {e}")
            return []
    
    def next_task(self) -> Optional[Dict]:
        """
        获取下一个可执行任务
        
        Returns:
            下一个任务信息，如果没有返回 None
        """
        try:
            result = self._run_mcp_tool(
                "mcp__taskmaster-ai__next_task",
                projectRoot=str(self.project_root)
            )
            return result.get("task")
        except TaskMasterClientError as e:
            logger.error(f"获取下一个任务失败: {e}")
            return None
    
    def set_task_status(self, task_id: str, status: str) -> bool:
        """
        设置任务状态
        
        Args:
            task_id: 任务ID (支持子任务格式如 "1.2")
            status: 新状态 (pending/in_progress/done/failed)
            
        Returns:
            操作是否成功
        """
        try:
            result = self._run_mcp_tool(
                "mcp__taskmaster-ai__set_task_status",
                projectRoot=str(self.project_root),
                id=task_id,
                status=status
            )
            return result.get("success", False)
        except TaskMasterClientError as e:
            logger.error(f"设置任务状态失败: {e}")
            return False
    
    def expand_task(self, task_id: str, num_subtasks: Optional[str] = None,
                    prompt: Optional[str] = None, research: bool = False,
                    force: bool = False) -> List[Dict]:
        """
        展开任务为子任务
        
        Args:
            task_id: 要展开的任务ID
            num_subtasks: 子任务数量
            prompt: 额外上下文提示
            research: 是否启用研究功能
            force: 是否强制重新生成
            
        Returns:
            生成的子任务列表
        """
        try:
            kwargs = {
                "projectRoot": str(self.project_root),
                "id": task_id,
                "research": research,
                "force": force
            }
            if num_subtasks:
                kwargs["num"] = num_subtasks
            if prompt:
                kwargs["prompt"] = prompt
                
            result = self._run_mcp_tool(
                "mcp__taskmaster-ai__expand_task",
                **kwargs
            )
            return result.get("subtasks", [])
        except TaskMasterClientError as e:
            logger.error(f"展开任务失败: {e}")
            return []
    
    def analyze_complexity(self, threshold: int = 5, research: bool = True) -> Dict:
        """
        分析项目复杂度
        
        Args:
            threshold: 复杂度阈值 (1-10)
            research: 是否启用研究分析
            
        Returns:
            复杂度分析报告
        """
        try:
            result = self._run_mcp_tool(
                "mcp__taskmaster-ai__analyze_project_complexity",
                projectRoot=str(self.project_root),
                threshold=threshold,
                research=research
            )
            return result.get("analysis", {})
        except TaskMasterClientError as e:
            logger.error(f"复杂度分析失败: {e}")
            return {}
    
    def add_dependency(self, task_id: str, depends_on: str) -> bool:
        """
        添加任务依赖关系
        
        Args:
            task_id: 依赖任务的ID
            depends_on: 被依赖任务的ID
            
        Returns:
            操作是否成功
        """
        try:
            result = self._run_mcp_tool(
                "mcp__taskmaster-ai__add_dependency",
                projectRoot=str(self.project_root),
                id=task_id,
                dependsOn=depends_on
            )
            return result.get("success", False)
        except TaskMasterClientError as e:
            logger.error(f"添加依赖失败: {e}")
            return False
    
    def research(self, query: str, task_ids: Optional[List[str]] = None,
                 save_to: Optional[str] = None, detail_level: str = "medium") -> str:
        """
        AI 研究功能
        
        Args:
            query: 研究查询
            task_ids: 相关任务ID列表
            save_to: 保存到指定任务ID
            detail_level: 详细程度 (low/medium/high)
            
        Returns:
            研究结果
        """
        try:
            kwargs = {
                "projectRoot": str(self.project_root),
                "query": query,
                "detailLevel": detail_level
            }
            if task_ids:
                kwargs["taskIds"] = ",".join(task_ids)
            if save_to:
                kwargs["saveTo"] = save_to
                
            result = self._run_mcp_tool(
                "mcp__taskmaster-ai__research",
                **kwargs
            )
            return result.get("research_result", "")
        except TaskMasterClientError as e:
            logger.error(f"研究功能失败: {e}")
            return ""
    
    # 以下是模拟实现方法，在实际环境中应该移除
    def _mock_initialize_project(self, **kwargs) -> Dict:
        """模拟项目初始化"""
        self.taskmaster_dir.mkdir(parents=True, exist_ok=True)
        (self.taskmaster_dir / "tasks").mkdir(exist_ok=True)
        (self.taskmaster_dir / "docs").mkdir(exist_ok=True)
        (self.taskmaster_dir / "reports").mkdir(exist_ok=True)
        
        # 创建空的 tasks.json
        if not self.tasks_file.exists():
            tasks_data = {"tasks": [], "metadata": {"version": "1.0"}}
            self.tasks_file.write_text(json.dumps(tasks_data, indent=2, ensure_ascii=False))
        
        return {"success": True, "message": "项目初始化成功"}
    
    def _mock_parse_prd(self, **kwargs) -> Dict:
        """模拟 PRD 解析"""
        # 模拟生成一些任务
        tasks = [
            {
                "id": 1,
                "title": "项目架构设计",
                "description": "设计整体系统架构",
                "status": "pending",
                "priority": "high",
                "dependencies": [],
                "phase": "information"
            },
            {
                "id": 2,
                "title": "核心功能实现",
                "description": "实现核心业务逻辑",
                "status": "pending", 
                "priority": "high",
                "dependencies": [1],
                "phase": "execution"
            }
        ]
        return {"success": True, "tasks": tasks}
    
    def _mock_add_task(self, **kwargs) -> Dict:
        """模拟添加任务"""
        prompt = kwargs.get("prompt", "")
        task = {
            "id": 100,  # 模拟新ID
            "title": prompt[:50],
            "description": prompt,
            "status": "pending",
            "priority": kwargs.get("priority", "medium"),
            "dependencies": kwargs.get("dependencies", "").split(",") if kwargs.get("dependencies") else [],
            "phase": "execution"
        }
        return {"success": True, "task": task}
    
    def _mock_get_tasks(self, **kwargs) -> Dict:
        """模拟获取任务列表"""
        # 从 tasks.json 读取实际任务
        if self.tasks_file.exists():
            try:
                data = json.loads(self.tasks_file.read_text())
                tasks = data.get("tasks", [])
                
                # 应用状态过滤
                status_filter = kwargs.get("status")
                if status_filter:
                    tasks = [t for t in tasks if t.get("status") == status_filter]
                
                return {"success": True, "tasks": tasks}
            except Exception as e:
                logger.error(f"读取任务文件失败: {e}")
        
        return {"success": True, "tasks": []}
    
    def _mock_next_task(self, **kwargs) -> Dict:
        """模拟获取下一个任务"""
        tasks = self._mock_get_tasks(**kwargs).get("tasks", [])
        pending_tasks = [t for t in tasks if t.get("status") == "pending"]
        
        if pending_tasks:
            return {"success": True, "task": pending_tasks[0]}
        return {"success": True, "task": None}
    
    def _mock_set_task_status(self, **kwargs) -> Dict:
        """模拟设置任务状态"""
        # 这里应该实际更新 tasks.json 文件
        return {"success": True, "message": "状态更新成功"}
    
    def _mock_expand_task(self, **kwargs) -> Dict:
        """模拟任务展开"""
        subtasks = [
            {
                "id": f"{kwargs.get('id', '1')}.1",
                "title": "子任务1",
                "description": "第一个子任务",
                "status": "pending",
                "priority": "medium"
            },
            {
                "id": f"{kwargs.get('id', '1')}.2", 
                "title": "子任务2",
                "description": "第二个子任务",
                "status": "pending",
                "priority": "medium"
            }
        ]
        return {"success": True, "subtasks": subtasks}
    
    def _mock_analyze_complexity(self, **kwargs) -> Dict:
        """模拟复杂度分析"""
        analysis = {
            "total_tasks": 5,
            "complex_tasks": 2,
            "recommendations": ["任务1需要分解", "任务3复杂度过高"],
            "average_complexity": 6.5
        }
        return {"success": True, "analysis": analysis}
    
    def _mock_add_dependency(self, **kwargs) -> Dict:
        """模拟添加依赖"""
        return {"success": True, "message": "依赖添加成功"}
    
    def _mock_research(self, **kwargs) -> Dict:
        """模拟研究功能"""
        query = kwargs.get("query", "")
        research_result = f"关于 '{query}' 的研究结果：这是一个模拟的研究回复。"
        return {"success": True, "research_result": research_result}