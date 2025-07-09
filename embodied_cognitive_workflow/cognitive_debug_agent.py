"""
认知调试智能体 - 认知工作流调试与监控层

提供认知工作流的调试、监控和分析功能，包含智能断点、异步Bug检测、
单步跟踪等高级调试能力。集成Gemini Flash进行智能分析。
"""

import sys
import os
import asyncio
import threading
import time
from typing import Dict, List, Optional, Any, Iterator, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import logging
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_base import AgentBase, Result
from langchain_core.language_models import BaseChatModel

# 处理相对导入问题
try:
    from .embodied_cognitive_workflow import CognitiveAgent
except ImportError:
    # 当作为独立模块运行时，使用绝对导入
    from embodied_cognitive_workflow import CognitiveAgent


class CognitiveState(Enum):
    """认知状态枚举"""
    IDLE = "空闲"
    PLANNING = "规划中"
    EXECUTING = "执行中"
    MONITORING = "监控中"
    REFLECTING = "反思中"
    OPTIMIZING = "优化中"
    ERROR = "错误"


class DebugLevel(Enum):
    """调试级别枚举"""
    NONE = "无调试"
    BASIC = "基础调试"
    DETAILED = "详细调试"
    FULL = "完整调试"


@dataclass
class CognitiveStep:
    """认知步骤数据结构"""
    step_id: str
    timestamp: datetime
    layer: str  # 自我、本我、身体
    action: str
    input_data: Any
    output_data: Any
    state_before: Dict[str, Any]
    state_after: Dict[str, Any]
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CognitiveBreakpoint:
    """认知断点数据结构"""
    breakpoint_id: str
    layer: str
    condition: str  # 自然语言条件
    is_active: bool = True
    hit_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BugReport:
    """Bug报告数据结构"""
    bug_id: str
    timestamp: datetime
    severity: str  # low, medium, high, critical
    description: str
    affected_layer: str
    context: Dict[str, Any]
    suggested_fix: Optional[str] = None
    status: str = "open"  # open, investigating, fixed, closed


class CognitiveDebugger:
    """认知工作流调试器"""
    
    def __init__(self, gemini_flash_client=None, enable_step_tracking=True):
        self.gemini_flash_client = gemini_flash_client
        self.enable_step_tracking = enable_step_tracking
        self.debug_level = DebugLevel.BASIC
        
        # 调试数据存储
        self.cognitive_steps: List[CognitiveStep] = []
        self.breakpoints: Dict[str, CognitiveBreakpoint] = {}
        self.bug_reports: List[BugReport] = []
        
        # 调试状态
        self.is_debugging = False
        self.is_paused = False
        self.current_step_id = None
        
        # 异步监控
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # 日志配置
        self.logger = logging.getLogger(__name__)
    
    def set_cognitive_breakpoint(self, layer: str, condition: str, 
                               metadata: Dict[str, Any] = None) -> str:
        """设置认知断点"""
        breakpoint_id = f"bp_{layer}_{len(self.breakpoints)}"
        breakpoint = CognitiveBreakpoint(
            breakpoint_id=breakpoint_id,
            layer=layer,
            condition=condition,
            metadata=metadata or {}
        )
        self.breakpoints[breakpoint_id] = breakpoint
        self.logger.info(f"设置认知断点: {breakpoint_id} - {condition}")
        return breakpoint_id
    
    def remove_breakpoint(self, breakpoint_id: str) -> bool:
        """移除断点"""
        if breakpoint_id in self.breakpoints:
            del self.breakpoints[breakpoint_id]
            self.logger.info(f"移除断点: {breakpoint_id}")
            return True
        return False
    
    def evaluate_breakpoint_condition(self, breakpoint: CognitiveBreakpoint, 
                                    context: Dict[str, Any]) -> bool:
        """评估断点条件（使用Gemini Flash）"""
        if not self.gemini_flash_client:
            # 简单的关键词匹配作为fallback
            return any(keyword in str(context.values()) 
                      for keyword in breakpoint.condition.split())
        
        try:
            # 使用Gemini Flash进行智能条件评估
            prompt = f"""
            请评估以下断点条件是否在当前上下文中满足：
            
            断点条件：{breakpoint.condition}
            当前上下文：{json.dumps(context, ensure_ascii=False, indent=2)}
            
            请只返回 'true' 或 'false'，不要其他解释。
            """
            
            response = self.gemini_flash_client.generate_content(prompt)
            return response.text.strip().lower() == 'true'
            
        except Exception as e:
            self.logger.error(f"断点条件评估失败: {e}")
            return False
    
    def record_cognitive_step(self, step: CognitiveStep):
        """记录认知步骤"""
        if not self.enable_step_tracking:
            return
            
        self.cognitive_steps.append(step)
        self.current_step_id = step.step_id
        
        # 检查断点
        if self.is_debugging:
            self._check_breakpoints(step)
    
    def _check_breakpoints(self, step: CognitiveStep):
        """检查断点条件"""
        context = {
            'layer': step.layer,
            'action': step.action,
            'input_data': step.input_data,
            'output_data': step.output_data,
            'state_before': step.state_before,
            'state_after': step.state_after,
            'success': step.success,
            'error_message': step.error_message
        }
        
        for bp_id, breakpoint in self.breakpoints.items():
            if (breakpoint.is_active and 
                breakpoint.layer == step.layer and
                self.evaluate_breakpoint_condition(breakpoint, context)):
                
                breakpoint.hit_count += 1
                self.logger.info(f"断点触发: {bp_id} - {breakpoint.condition}")
                self._pause_execution()
                break
    
    def _pause_execution(self):
        """暂停执行"""
        self.is_paused = True
        self.logger.info("认知流程已暂停，等待调试命令...")
    
    def resume_execution(self):
        """恢复执行"""
        self.is_paused = False
        self.logger.info("认知流程已恢复")
    
    def start_async_monitoring(self):
        """启动异步bug监控"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._async_bug_monitoring,
            daemon=True
        )
        self.monitoring_thread.start()
        self.logger.info("异步bug监控已启动")
    
    def stop_async_monitoring(self):
        """停止异步bug监控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
        self.logger.info("异步bug监控已停止")
    
    def _async_bug_monitoring(self):
        """异步bug监控主循环"""
        while self.monitoring_active:
            try:
                # 分析最近的认知步骤
                recent_steps = self.cognitive_steps[-10:] if self.cognitive_steps else []
                
                for step in recent_steps:
                    if not step.success or step.error_message:
                        self._analyze_potential_bug(step)
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                self.logger.error(f"异步监控错误: {e}")
                time.sleep(5)  # 错误后等待5秒再继续
    
    def _analyze_potential_bug(self, step: CognitiveStep):
        """分析潜在的bug（使用Gemini Flash）"""
        if not self.gemini_flash_client:
            return
        
        try:
            prompt = f"""
            请分析以下认知步骤是否存在软件缺陷：
            
            步骤信息：
            - 层级: {step.layer}
            - 动作: {step.action}
            - 成功: {step.success}
            - 错误信息: {step.error_message}
            - 输入数据: {json.dumps(step.input_data, ensure_ascii=False)}
            - 输出数据: {json.dumps(step.output_data, ensure_ascii=False)}
            - 执行时间: {step.execution_time}秒
            
            请判断：
            1. 是否存在缺陷 (true/false)
            2. 缺陷严重程度 (low/medium/high/critical)
            3. 问题描述 (简短描述)
            4. 建议修复方案 (如果有)
            
            请以JSON格式返回：
            {{"has_bug": true/false, "severity": "level", "description": "desc", "fix_suggestion": "suggestion"}}
            """
            
            response = self.gemini_flash_client.generate_content(prompt)
            analysis = json.loads(response.text.strip())
            
            if analysis.get('has_bug', False):
                bug_report = BugReport(
                    bug_id=f"bug_{step.step_id}_{int(time.time())}",
                    timestamp=datetime.now(),
                    severity=analysis.get('severity', 'medium'),
                    description=analysis.get('description', '未知问题'),
                    affected_layer=step.layer,
                    context={'step': step.__dict__},
                    suggested_fix=analysis.get('fix_suggestion')
                )
                self.bug_reports.append(bug_report)
                self.logger.warning(f"发现潜在bug: {bug_report.description}")
                
        except Exception as e:
            self.logger.error(f"Bug分析失败: {e}")
    
    def get_debug_summary(self) -> Dict[str, Any]:
        """获取调试摘要"""
        return {
            'total_steps': len(self.cognitive_steps),
            'active_breakpoints': len([bp for bp in self.breakpoints.values() if bp.is_active]),
            'bug_reports': len(self.bug_reports),
            'is_debugging': self.is_debugging,
            'is_paused': self.is_paused,
            'current_step': self.current_step_id,
            'monitoring_active': self.monitoring_active
        }


class CognitiveDebugAgent(AgentBase):
    """认知调试智能体 - 认知工作流调试与监控层"""
    
    def __init__(self, 
                 cognitive_agent: CognitiveAgent,
                 llm: BaseChatModel,
                 gemini_flash_client=None,
                 enable_debugging=True,
                 enable_step_tracking=True):
        """
        初始化认知调试智能体
        
        Args:
            cognitive_agent: 被调试的认知智能体
            llm: 语言模型
            gemini_flash_client: Gemini Flash客户端
            enable_debugging: 是否启用调试功能
            enable_step_tracking: 是否启用步骤跟踪
        """
        super().__init__(llm)
        
        self.cognitive_agent = cognitive_agent
        self.gemini_flash_client = gemini_flash_client
        
        # 调试代理状态
        self.state = CognitiveState.IDLE
        self.debug_memory = []
        
        # 调试器
        self.debugger = CognitiveDebugger(
            gemini_flash_client=gemini_flash_client,
            enable_step_tracking=enable_step_tracking
        ) if enable_debugging else None
        
        # 性能监控
        self.performance_metrics = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'average_execution_time': 0,
            'optimization_count': 0
        }
        
        # 日志配置
        self.logger = logging.getLogger(__name__)
        
        # 启动异步监控
        if self.debugger:
            self.debugger.start_async_monitoring()
    
    def execute_with_debugging(self, instruction: str, 
                               debug_level: DebugLevel = DebugLevel.BASIC) -> Result:
        """在调试监控下执行指令"""
        start_time = time.time()
        
        try:
            # 设置调试级别
            if self.debugger:
                self.debugger.debug_level = debug_level
                self.debugger.is_debugging = (debug_level != DebugLevel.NONE)
            
            # 调试预处理
            self._debug_preprocessing(instruction)
            
            # 执行认知任务
            self.state = CognitiveState.EXECUTING
            result = self.cognitive_agent.execute_sync(instruction)
            
            # 调试后处理
            self._debug_postprocessing(result)
            
            # 更新性能指标
            execution_time = time.time() - start_time
            self._update_performance_metrics(True, execution_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"执行失败: {e}")
            self._update_performance_metrics(False, time.time() - start_time)
            return Result(
                success=False,
                code="",
                stderr=str(e),
                return_value=f"执行失败: {e}"
            )
        finally:
            self.state = CognitiveState.IDLE
    
    def _debug_preprocessing(self, instruction: str):
        """调试预处理"""
        self.state = CognitiveState.PLANNING
        
        # 记录调试步骤
        if self.debugger:
            step = CognitiveStep(
                step_id=f"debug_pre_{int(time.time())}",
                timestamp=datetime.now(),
                layer="调试层",
                action="调试预处理",
                input_data={"instruction": instruction},
                output_data={"status": "预处理完成"},
                state_before={"state": self.state.value},
                state_after={"state": CognitiveState.EXECUTING.value},
                execution_time=0.01,
                success=True
            )
            self.debugger.record_cognitive_step(step)
        
        # 任务分析和调试策略
        debug_analysis = self._analyze_task_complexity(instruction)
        self.debug_memory.append({
            'timestamp': datetime.now(),
            'instruction': instruction,
            'analysis': debug_analysis
        })
    
    def _debug_postprocessing(self, result: Result):
        """调试后处理"""
        self.state = CognitiveState.REFLECTING
        
        # 记录调试步骤
        if self.debugger:
            step = CognitiveStep(
                step_id=f"debug_post_{int(time.time())}",
                timestamp=datetime.now(),
                layer="调试层",
                action="调试后处理",
                input_data={"result": result.__dict__},
                output_data={"status": "后处理完成"},
                state_before={"state": CognitiveState.EXECUTING.value},
                state_after={"state": CognitiveState.REFLECTING.value},
                execution_time=0.01,
                success=True
            )
            self.debugger.record_cognitive_step(step)
        
        # 性能分析和反思
        self._analyze_performance(result)
    
    def _analyze_task_complexity(self, instruction: str) -> Dict[str, Any]:
        """分析任务复杂度"""
        try:
            prompt = f"""
            分析以下任务的复杂度和最佳策略：
            
            任务: {instruction}
            
            请评估：
            1. 复杂度等级 (1-10)
            2. 预估执行时间
            3. 建议策略
            4. 潜在风险
            
            请以JSON格式返回结果。
            """
            
            response = self.llm.invoke(prompt)
            # 简化处理，实际应该解析JSON
            return {
                'complexity': 5,
                'estimated_time': '中等',
                'strategy': '标准执行',
                'risks': '无特殊风险'
            }
            
        except Exception as e:
            self.logger.error(f"任务复杂度分析失败: {e}")
            return {'complexity': 5, 'strategy': '标准执行'}
    
    def _analyze_performance(self, result: Result):
        """分析执行性能"""
        analysis = {
            'success': result.success,
            'timestamp': datetime.now(),
            'performance_notes': "执行完成" if result.success else "发现问题",
            'debug_opportunities': []
        }
        
        self.debug_memory.append(analysis)
        
        # 限制记忆大小
        if len(self.debug_memory) > 100:
            self.debug_memory = self.debug_memory[-50:]
    
    def _update_performance_metrics(self, success: bool, execution_time: float):
        """更新性能指标"""
        self.performance_metrics['total_tasks'] += 1
        
        if success:
            self.performance_metrics['successful_tasks'] += 1
        else:
            self.performance_metrics['failed_tasks'] += 1
        
        # 更新平均执行时间
        total_time = (self.performance_metrics['average_execution_time'] * 
                     (self.performance_metrics['total_tasks'] - 1) + execution_time)
        self.performance_metrics['average_execution_time'] = total_time / self.performance_metrics['total_tasks']
    
    def get_debug_summary(self) -> Dict[str, Any]:
        """获取调试摘要"""
        return {
            'state': self.state.value,
            'performance_metrics': self.performance_metrics,
            'memory_entries': len(self.debug_memory),
            'debugger_summary': self.debugger.get_debug_summary() if self.debugger else None,
            'recent_analysis': self.debug_memory[-5:] if self.debug_memory else []
        }
    
    def set_debug_breakpoint(self, layer: str, condition: str) -> str:
        """设置调试断点"""
        if not self.debugger:
            raise ValueError("调试器未启用")
        return self.debugger.set_cognitive_breakpoint(layer, condition)
    
    def get_bug_reports(self) -> List[BugReport]:
        """获取bug报告"""
        return self.debugger.bug_reports if self.debugger else []
    
    def get_cognitive_trace(self) -> List[CognitiveStep]:
        """获取认知轨迹"""
        return self.debugger.cognitive_steps if self.debugger else []
    
    def __del__(self):
        """析构函数"""
        if self.debugger:
            self.debugger.stop_async_monitoring()