# -*- coding: utf-8 -*-
"""
基于产生式规则的Agent包装器

使用包装器设计模式，通过RuleEngineService将基础Agent类包装成具备认知工作流能力的智能体。
实现智能指令分类和执行路由，支持信息性指令、单步执行和多步骤认知工作流。

Author: Claude Code Assistant
Date: 2025-06-28
Version: 1.0.0
"""

import logging
from typing import Iterator, Any, Dict, Optional, Tuple, Union
from datetime import datetime

# 导入必要的类型和接口
import sys
import os

logger = logging.getLogger(__name__)

# 添加项目路径到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from cognitive_workflow_rule_base import create_production_rule_system
    from cognitive_workflow_rule_base.domain.value_objects import WorkflowExecutionResult
except ImportError as e:
    logger.warning(f"无法导入认知工作流组件: {e}")
    # 定义虚拟类以保证包装器基本功能可用
    create_production_rule_system = None
    
    class WorkflowExecutionResult:
        def __init__(self, goal="", is_successful=False, final_state="", total_iterations=0, execution_metrics=None, final_message="", completion_timestamp=None):
            self.goal = goal
            self.is_successful = is_successful
            self.final_state = final_state
            self.total_iterations = total_iterations
            self.execution_metrics = execution_metrics
            self.final_message = final_message
            self.completion_timestamp = completion_timestamp


class CognitiveAgent:
    """
    基于产生式规则的Agent包装器
    
    使用包装器模式将基础Agent增强为具备认知工作流能力的智能体。
    通过智能指令分类系统，自动选择最优的执行方式：
    - 信息性指令 → chat_sync/stream
    - 单步骤指令 → execute_sync/stream  
    - 多步骤指令 → 认知工作流
    
    Attributes:
        base_agent: 被包装的基础Agent实例
        api_specification: API规范说明，自动从base_agent获取
        workflow_engine: 认知工作流引擎实例
        enable_auto_recovery: 是否启用自动错误恢复
    """
    
    def __init__(self, 
                 base_agent: Any,
                 enable_auto_recovery: bool = True,
                 classification_cache_size: int = 100):
        """
        初始化认知Agent包装器
        
        Args:
            base_agent: 基础Agent实例（来自pythonTask.Agent）
            enable_auto_recovery: 是否启用自动错误恢复
            classification_cache_size: 指令分类结果缓存大小
        """
        self.base_agent = base_agent
        self.enable_auto_recovery = enable_auto_recovery
        
        # 指令分类缓存
        self._classification_cache: Dict[str, Tuple[str, str]] = {}
        self._cache_max_size = classification_cache_size
        
        # 性能统计
        self._classification_stats = {
            "total_classifications": 0,
            "cache_hits": 0,
            "classification_errors": 0,
            "execution_stats": {
                "informational": 0,
                "single_step": 0,
                "multi_step": 0
            }
        }
        
        # 构建Agent集合
        self.agents = {"main_agent": base_agent}
        
        # 创建认知工作流引擎
        if create_production_rule_system is not None:
            try:
                self.workflow_engine = create_production_rule_system(
                    llm=base_agent.llm,
                    agents=self.agents,
                    enable_auto_recovery=enable_auto_recovery
                )
                logger.info("✅ 认知工作流引擎初始化成功")
            except Exception as e:
                logger.error(f"❌ 认知工作流引擎初始化失败: {e}")
                self.workflow_engine = None
        else:
            logger.warning("⚠️ 认知工作流系统不可用，将使用降级模式")
            self.workflow_engine = None
    
    @property
    def api_specification(self) -> Optional[str]:
        """
        获取API规范说明
        
        Returns:
            Optional[str]: 从base_agent获取的API规范说明，如果base_agent没有此属性则返回None
        """
        return getattr(self.base_agent, 'api_specification', None)
    
    @api_specification.setter
    def api_specification(self, value: Optional[str]) -> None:
        """
        设置API规范说明
        
        Args:
            value: API规范说明字符串
        """
        if hasattr(self.base_agent, 'api_specification'):
            self.base_agent.api_specification = value
        else:
            logger.warning("⚠️ base_agent没有api_specification属性，无法设置")
            
    def _update_classification_cache(self, instruction: str, result: Tuple[str, str]) -> None:
        """更新指令分类缓存"""
        # 如果缓存已满，删除最旧的条目
        if len(self._classification_cache) >= self._cache_max_size:
            oldest_key = next(iter(self._classification_cache))
            del self._classification_cache[oldest_key]
        
        self._classification_cache[instruction] = result
        
    def _get_optimized_classification_prompt(self, instruction: str) -> str:
        """
        获取优化的指令分类提示
        
        Args:
            instruction: 输入指令
            
        Returns:
            str: 优化的分类提示
        """
        return f"""
分析以下指令的类型和复杂度：

指令: "{instruction}"

请仔细分析并判断这是：

## 指令类型分析：

### 1. 信息性指令 (informational)
- **特征**: 询问、查询、解释、讨论、学习、说明等
- **行为**: 只涉及知识获取和信息交流，不对外部环境进行操作
- **示例**: 
  * "什么是机器学习？"
  * "解释Python装饰器的原理"
  * "讨论算法复杂度的概念"
  * "介绍Django框架的特点"

### 2. 执行性指令 (executable)
- **特征**: 创建、编写、实现、开发、运行、测试、部署等
- **行为**: 需要对外部环境进行观察或执行具体操作
- **包括**: 文件操作、代码执行、系统调用、网络请求等

## 复杂度分析（仅针对执行性指令）：

### 单步骤 (single_step)
- **特征**: 简单直接的任务，可以一步完成
- **示例**:
  * "打印hello world"
  * "计算1+1"
  * "显示当前时间"
  * "创建一个空文件"

### 多步骤 (multi_step)  
- **特征**: 复杂任务，需要多个步骤和规划
- **示例**:
  * "开发一个Web应用"
  * "创建包含测试的计算器程序"
  * "读取文件并执行其中的指令"
  * "实现数据分析项目"

## 分类规则：
1. 如果指令主要是获取信息或解释概念 → informational|chat
2. 如果指令是简单的单一操作 → executable|single_step
3. 如果指令是复杂的多步骤任务 → executable|multi_step

## 输出格式：
请只返回分类结果，格式：类型|步骤复杂度
例如：informational|chat 或 executable|single_step 或 executable|multi_step

分析结果："""

    def classify_instruction(self, instruction: str) -> Tuple[str, str]:
        """
        智能指令分类方法
        
        使用LLM分析指令类型和复杂度，支持缓存机制提升性能。
        
        Args:
            instruction: 输入指令
            
        Returns:
            Tuple[str, str]: (指令类型, 执行方式)
            - 指令类型: "informational" | "executable" 
            - 执行方式: "single_step" | "multi_step" | "chat"
        """
        self._classification_stats["total_classifications"] += 1
        
        # 检查缓存
        if instruction in self._classification_cache:
            self._classification_stats["cache_hits"] += 1
            return self._classification_cache[instruction]
        
        try:
            # 使用优化的分类提示
            classification_prompt = self._get_optimized_classification_prompt(instruction)
            
            # 调用LLM进行分类
            response = self.base_agent.llm.invoke(classification_prompt).content.strip()
            
            # 解析响应
            parts = response.split('|')
            if len(parts) == 2:
                instruction_type = parts[0].strip().lower()
                execution_mode = parts[1].strip().lower()
                
                # 验证分类结果的有效性
                valid_types = ["informational", "executable"]
                valid_modes = ["chat", "single_step", "multi_step"]
                
                if instruction_type in valid_types and execution_mode in valid_modes:
                    result = (instruction_type, execution_mode)
                    self._update_classification_cache(instruction, result)
                    logger.debug(f"🔍 指令分类: '{instruction}' → {result}")
                    return result
            
            # 如果解析失败，使用默认策略
            logger.warning(f"⚠️ 指令分类解析失败，使用默认策略: {response}")
            result = ("executable", "multi_step")
            self._update_classification_cache(instruction, result)
            return result
            
        except Exception as e:
            self._classification_stats["classification_errors"] += 1
            logger.error(f"❌ 指令分类异常: {e}")
            # 异常情况下默认为多步骤执行性指令
            result = ("executable", "multi_step")
            self._update_classification_cache(instruction, result)
            return result
    
    def execute_instruction_syn(self, instruction: str) -> Any:
        """
        智能执行指令（同步版本）
        
        根据指令分类自动选择最优执行方式：
        - 信息性指令 → chat_sync
        - 单步骤指令 → execute_sync  
        - 多步骤指令 → 认知工作流
        
        Args:
            instruction: 输入指令
            
        Returns:
            根据指令类型返回相应结果:
            - 信息性指令: chat_sync的返回值
            - 单步骤执行性指令: execute_sync的Result对象
            - 多步骤执行性指令: WorkflowExecutionResult对象
        """
        try:
            # 指令分类
            instruction_type, execution_mode = self.classify_instruction(instruction)
            logger.info(f"🎯 执行指令: '{instruction}' | 分类: {instruction_type}|{execution_mode}")
            
            # 更新执行统计
            if execution_mode in self._classification_stats["execution_stats"]:
                self._classification_stats["execution_stats"][execution_mode] += 1
            
            # 根据分类选择执行方式
            if instruction_type == "informational":
                # 信息性指令：使用chat_sync方法
                logger.debug("💬 使用chat_sync执行信息性指令")
                return self.base_agent.chat_sync(instruction)
                    
            elif instruction_type == "executable":
                if execution_mode == "single_step":
                    # 单步骤执行性指令：使用execute_sync方法
                    logger.debug("⚡ 使用execute_sync执行单步骤指令")
                    return self.base_agent.execute_sync(instruction)
                else:
                    # 多步骤执行性指令：使用认知工作流
                    logger.debug("🧠 使用认知工作流执行多步骤指令")
                    return self.execute_multi_step(instruction)
            
            # 默认情况：使用认知工作流
            logger.debug("🔄 使用默认认知工作流执行")
            return self.execute_multi_step(instruction)
            
        except Exception as e:
            logger.error(f"❌ 执行指令失败: {e}")
            if self.enable_auto_recovery:
                logger.info("🔧 尝试使用基础Agent执行...")
                try:
                    return self.base_agent.execute_sync(instruction)
                except Exception as recovery_error:
                    logger.error(f"❌ 恢复执行也失败: {recovery_error}")
            raise
    
    def execute_instruction_stream(self, instruction: str) -> Iterator[Any]:
        """
        智能执行指令（流式版本）
        
        Args:
            instruction: 输入指令
            
        Yields:
            Iterator[Any]: 流式输出迭代器
            - 前面的元素：中间过程信息（字符串状态、进度提示等）
            - 最后一个元素：Result对象（最终执行结果）
        """
        try:
            # 指令分类
            instruction_type, execution_mode = self.classify_instruction(instruction)
            
            yield f"🔍 指令分析: {instruction_type} | {execution_mode}"
            yield f"🎯 开始执行: {instruction}"
            
            # 更新执行统计
            if execution_mode in self._classification_stats["execution_stats"]:
                self._classification_stats["execution_stats"][execution_mode] += 1
            
            # 根据分类选择执行方式
            if instruction_type == "informational":
                # 信息性指令：使用chat_stream方法
                yield "💬 使用对话模式处理信息性指令..."
                for result in self.base_agent.chat_stream(instruction):
                    yield result
                    
            elif instruction_type == "executable":
                if execution_mode == "single_step":
                    # 单步骤执行性指令：使用execute_stream方法
                    yield "⚡ 使用单步执行模式..."
                    for result in self.base_agent.execute_stream(instruction):
                        yield result
                else:
                    # 多步骤执行性指令：使用认知工作流
                    yield "🧠 启动认知工作流引擎..."
                    for result in self.execute_multi_step_stream(instruction):
                        yield result
            else:
                # 默认情况：使用认知工作流
                yield "🔄 使用默认认知工作流模式..."
                for result in self.execute_multi_step_stream(instruction):
                    yield result
                    
        except Exception as e:
            yield f"❌ 执行异常: {e}"
            if self.enable_auto_recovery:
                yield "🔧 尝试使用基础Agent恢复执行..."
                try:
                    for result in self.base_agent.execute_stream(instruction):
                        yield result
                except Exception as recovery_error:
                    yield f"❌ 恢复执行失败: {recovery_error}"
                    raise
            else:
                raise
    
    def execute_multi_step(self, goal: str) -> WorkflowExecutionResult:
        """
        执行多步骤目标任务（使用认知工作流）
        
        Args:
            goal: 目标任务描述
            
        Returns:
            WorkflowExecutionResult: 工作流执行结果
        """
        if self.workflow_engine is None:
            logger.warning("⚠️ 认知工作流引擎不可用，使用基础Agent降级执行")
            # 降级到基础Agent执行
            try:
                result = self.base_agent.execute_sync(goal)
                
                # 包装为WorkflowExecutionResult格式
                return WorkflowExecutionResult(
                    goal=goal,
                    is_successful=True,
                    final_state="completed",
                    total_iterations=1,
                    execution_metrics=None,
                    final_message=str(result.return_value if hasattr(result, 'return_value') else result),
                    completion_timestamp=datetime.now()
                )
            except Exception as e:
                return WorkflowExecutionResult(
                    goal=goal,
                    is_successful=False,
                    final_state="failed",
                    total_iterations=1,
                    execution_metrics=None,
                    final_message=f"执行失败: {e}",
                    completion_timestamp=datetime.now()
                )
        
        logger.info(f"🧠 启动认知工作流: {goal}")
        start_time = datetime.now()
        
        try:
            result = self.workflow_engine.execute_goal(goal)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ 认知工作流完成 | 用时: {execution_time:.2f}s | 成功: {result.is_successful}")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ 认知工作流执行失败 | 用时: {execution_time:.2f}s | 错误: {e}")
            raise
    
    def execute_multi_step_stream(self, goal: str) -> Iterator[Any]:
        """
        执行多步骤目标任务（流式，使用认知工作流）
        
        Args:
            goal: 目标任务描述
            
        Yields:
            Iterator[Any]: 流式执行过程和结果
        """
        yield f"🧠 认知工作流分析: {goal}"
        yield f"📋 生成执行规则..."
        yield f"⚙️ 开始多步骤执行..."
        
        try:
            workflow_result = self.execute_multi_step(goal)
            
            yield f"📊 执行统计: {workflow_result.total_iterations}个步骤"
            yield f"⏱️ 执行时间: {workflow_result.execution_metrics.total_execution_time:.2f}s"
            yield f"✅ 认知工作流完成"
            yield workflow_result
            
        except Exception as e:
            yield f"❌ 认知工作流执行失败: {e}"
            raise
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns:
            Dict[str, Any]: 包含分类和执行统计的性能数据
        """
        total_executions = sum(self._classification_stats["execution_stats"].values())
        cache_hit_rate = (
            self._classification_stats["cache_hits"] / 
            max(1, self._classification_stats["total_classifications"])
        ) * 100
        
        return {
            "classification_stats": self._classification_stats.copy(),
            "cache_info": {
                "size": len(self._classification_cache),
                "max_size": self._cache_max_size,
                "hit_rate_percent": round(cache_hit_rate, 2)
            },
            "execution_distribution": {
                k: (v / max(1, total_executions)) * 100 
                for k, v in self._classification_stats["execution_stats"].items()
            },
            "workflow_engine_status": self.workflow_engine is not None
        }
    
    def clear_cache(self) -> None:
        """清空指令分类缓存"""
        self._classification_cache.clear()
        logger.info("🧹 已清空指令分类缓存")
    
    def reset_stats(self) -> None:
        """重置性能统计"""
        self._classification_stats = {
            "total_classifications": 0,
            "cache_hits": 0,
            "classification_errors": 0,
            "execution_stats": {
                "informational": 0,
                "single_step": 0,
                "multi_step": 0
            }
        }
        logger.info("📊 已重置性能统计")

    def __repr__(self) -> str:
        """返回包装器的字符串表示"""
        api_spec_preview = ""
        if self.api_specification:
            # 显示API规范的前50个字符作为预览
            preview = self.api_specification[:50].replace('\n', ' ')
            api_spec_preview = f", api_spec='{preview}...'" if len(self.api_specification) > 50 else f", api_spec='{preview}'"
        
        return (f"CognitiveAgent("
                f"base_agent={type(self.base_agent).__name__}, "
                f"workflow_engine={'✅' if self.workflow_engine else '❌'}, "
                f"cache_size={len(self._classification_cache)}"
                f"{api_spec_preview})")