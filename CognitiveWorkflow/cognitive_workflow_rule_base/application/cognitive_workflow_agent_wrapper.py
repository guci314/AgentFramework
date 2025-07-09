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
    from ..domain.value_objects import WorkflowExecutionResult
    WORKFLOW_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"无法导入认知工作流组件: {e}")
    # 认知工作流组件不可用时的降级模式
    WorkflowExecutionResult = None
    WORKFLOW_COMPONENTS_AVAILABLE = False

# 延迟导入避免循环导入
def _get_production_rule_system():
    """延迟导入工厂函数"""
    try:
        from .. import create_production_rule_system
        return create_production_rule_system
    except ImportError as e:
        logger.warning(f"无法导入create_production_rule_system: {e}")
        return None


class IntelligentAgentWrapper:
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
        enable_adaptive_replacement: 是否启用自适应规则替换
    """
    
    def __init__(self, 
                 base_agent: Any,
                 agent_name: Optional[str] = None,
                 team_members: Optional[Dict[str, 'IntelligentAgentWrapper']] = None,
                 enable_auto_recovery: bool = True,
                 enable_adaptive_replacement: bool = True):
        """
        初始化认知Agent包装器
        
        Args:
            base_agent: 基础Agent实例（来自pythonTask.Agent）
            agent_name: Agent名称，如果不提供则尝试从base_agent.name获取，否则使用"main_agent"
            team_members: 该Agent管理的下属Agent团队
            enable_auto_recovery: 是否启用自动错误恢复
            enable_adaptive_replacement: 是否启用自适应规则替换
        """
        self.base_agent = base_agent
        self.enable_auto_recovery = enable_auto_recovery
        self.enable_adaptive_replacement = enable_adaptive_replacement
        
        # 统一Agent池管理
        self.team = team_members or {}
        
        # 性能统计
        self._classification_stats = {
            "total_classifications": 0,
            "classification_errors": 0,
            "execution_stats": {
                "chat": 0,
                "single_step": 0,
                "multi_step": 0
            }
        }
        
        # 确定Agent名称
        if agent_name:
            self.agent_name = agent_name
        elif hasattr(base_agent, 'name') and base_agent.name:
            self.agent_name = base_agent.name
        else:
            self.agent_name = "main_agent"
        
        # 统一的Agent池：自己 + 团队成员
        self.available_agents = {self.agent_name: self, **self.team}
        
        # 创建认知工作流引擎 - 每个IntelligentAgentWrapper都有自己的认知引擎
        # 这体现了层次化认知架构：每个Agent独立思考，然后协作
        create_production_rule_system = _get_production_rule_system()
        if create_production_rule_system is not None:
            try:
                self.workflow_engine = create_production_rule_system(
                    llm=base_agent.llm,
                    agents=self.available_agents,  # 使用统一的Agent池
                    enable_auto_recovery=enable_auto_recovery,
                    enable_adaptive_replacement=self.enable_adaptive_replacement
                )
                logger.info(f"✅ {self.agent_name}的认知工作流引擎初始化成功")
            except Exception as e:
                logger.error(f"❌ {self.agent_name}的认知工作流引擎初始化失败: {e}")
                self.workflow_engine = None
        else:
            logger.warning(f"⚠️ {self.agent_name}的认知工作流系统不可用，将使用降级模式")
            self.workflow_engine = None
    
    def set_workflow_engine(self, workflow_engine: Any) -> None:
        """
        设置外部的workflow_engine实例
        
        Args:
            workflow_engine: 外部创建的workflow_engine实例
        """
        self.workflow_engine = workflow_engine
        logger.info(f"✅ 为 {self.agent_name} 设置了外部workflow_engine")
    
    
    
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
        
    def _get_optimized_classification_prompt_for_single_agent(self, instruction: str) -> str:
        """
        获取优化的指令分类提示（使用JSON Schema约束输出）
        
        Args:
            instruction: 输入指令
            
        Returns:
            str: 优化的分类提示，包含JSON Schema约束
        """
        return f"""
分析以下指令的类型和复杂度：

指令: "{instruction}"

## 🧠 核心判定标准：认知上是否需要探索未知

## ⚡ 优先原则：尽量判断为单步骤 (single_step)
**设计哲学**: 系统采用"乐观执行"策略，优先假设任务可以直接完成。
- 如果单步骤执行失败，advisor会自动生成修复规则将其分解为多个单步骤
- 这种策略避免过度复杂化，让系统通过实际执行获得反馈并自适应优化

请从认知哲学的角度分析指令，判断执行者需要什么样的认知过程：

## 指令类型分析：

### 1. 信息性指令 (informational)
- **认知特征**: 寻求已有知识的传递和解释
- **认知过程**: 检索、组织和表达既有认知内容
- **示例**: 
  * "什么是机器学习？"
  * "解释Python装饰器的原理"
  * "讨论算法复杂度的概念"

### 2. 执行性指令 (executable)
- **认知特征**: 需要对外部世界进行观察、理解或改变
- **认知过程**: 涉及感知、分析、决策和行动的循环

## 🔍 认知复杂度分析（执行性指令）：

### 单步骤 (single_step)：确定性执行
- **认知本质**: 在**已知认知框架**内的机械性操作
- **认知过程**: 
  * 应用既有知识和规则
  * 执行预定义的操作序列
  * 无需获取新的认知内容
- **哲学特征**: 
  * **确定性**: 输入条件完全已知
  * **演绎性**: 从已知前提推导结论
  * **封闭性**: 在信息完备的环境中操作
- **认知标识**: 
  * 所有必要信息都已给定
  * 执行路径唯一且可预测
  * 不需要理解或适应未知情况

### 多步骤 (multi_step)：探索性理解
- **认知本质**: 需要**探索未知**并构建新的认知框架
- **认知过程**: 
  * 观察和感知未知环境/数据
  * 构建对新对象的理解
  * 根据新认知调整行动策略
- **哲学特征**: 
  * **不确定性**: 面对未知信息和情况
  * **归纳性**: 从特定观察中发现模式
  * **开放性**: 在信息不完备的环境中探索
- **认知标识**: 
  * 存在认知上的未知元素
  * 需要先理解后行动
  * 可能存在多种认知路径

## 🎯 关键判断问题：

### 执行这个指令时，认知主体是否需要：
1. **探索数据特征**？（文件结构、内容格式、数据分布等）
2. **理解环境状态**？（系统状况、网络环境、API特性等）
3. **发现隐藏模式**？（错误规律、性能瓶颈、用户行为等）
4. **适应动态变化**？（根据中间结果调整策略）
5. **构建新认知**？（对问题领域形成新理解）

**如果以上任何一个答案是"是"，则为多步骤任务**

## 📋 认知复杂度判定实例：

### 明确的多步骤任务（需要探索未知）：
* **"读取CSV文件并计算总和"**
  - 认知未知：CSV的结构、字段含义、数据质量
  - 探索过程：检查schema → 理解数据特征 → 制定计算策略
  
* **"分析销售数据并生成报告"**
  - 认知未知：数据分布、业务模式、关键指标
  - 探索过程：数据探索 → 模式发现 → 洞察提取 → 报告构建

* **"优化系统性能"**
  - 认知未知：性能瓶颈位置、资源使用模式
  - 探索过程：性能分析 → 问题定位 → 优化策略 → 效果验证

* **"处理用户上传的文件"**
  - 认知未知：文件格式、数据结构、内容特征
  - 探索过程：格式识别 → 结构分析 → 处理策略 → 数据转换

### 明确的单步骤任务（无需探索未知）：
* **"实现快速排序算法"**
  - 认知已知：算法逻辑完全确定
  - 执行过程：直接按算法规范实现

* **"创建包含name和age字段的User类"**
  - 认知已知：类结构和字段完全明确
  - 执行过程：按规范创建代码结构

* **"计算数组[1,2,3,4,5]的平均值"**
  - 认知已知：数据和操作完全确定
  - 执行过程：应用数学公式计算

* **"生成1到100之间的10个随机数"**
  - 认知已知：需求规范完全明确
  - 执行过程：调用随机数生成函数

* **"为计算器函数创建单元测试"**
  - 认知已知：基础数学运算(add/subtract/multiply/divide)的行为完全可预测
  - 执行过程：按标准测试模式创建确定性测试用例

* **"写一个函数把字符串转换为大写"**
  - 认知已知：字符串操作的标准功能
  - 执行过程：调用内置的字符串方法

## 🧭 认知复杂度识别指南：

### 多步骤的认知信号：
- **探索性词汇**: "分析"、"发现"、"理解"、"探索"、"优化"
- **未知数据源**: "文件"、"数据"、"网站"、"API"、"日志"
- **适应性需求**: "根据情况"、"动态"、"自动调整"、"灵活处理"
- **创造性要求**: "设计"、"规划"、"策略"、"方案"

### 单步骤的认知信号：
- **确定性词汇**: "创建"、"实现"、"计算"、"生成"、"转换"、"写"、"添加"
- **明确规范**: 具体的数据结构、算法名称、格式要求、函数签名
- **预定义操作**: 标准的编程任务、数学计算、格式转换、单元测试编写
- **已知目标**: 对于标准库函数、基础算法、常见模式的操作

## 🎨 认知哲学视角的最终判断：

**单步骤**：执行者作为**工具**，在已知框架内机械操作
**多步骤**：执行者作为**认知主体**，需要理解、探索和创造

## ⚖️ 边界情况判断原则：
**当存疑时，优先选择single_step**
- 测试编写：除非是对完全未知系统的测试，否则为single_step
- 代码实现：除非涉及复杂算法设计，否则为single_step  
- 数据处理：除非需要探索数据模式，否则为single_step
- 记住：失败时系统会自动分解任务，无需过度预判复杂度

## 输出要求：
请严格按照以下JSON Schema格式返回分类结果：

```json
{{
  "type": "object",
  "properties": {{
    "instruction_type": {{
      "type": "string",
      "enum": ["informational", "executable"],
      "description": "指令的基本类型"
    }},
    "execution_mode": {{
      "type": ["string", "null"], 
      "enum": ["single_step", "multi_step", null],
      "description": "执行方式，informational类型时为null"
    }},
    "confidence": {{
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "分类置信度（0-1）"
    }},
    "reasoning": {{
      "type": "string",
      "description": "从认知哲学角度说明分类理由，重点分析是否需要探索未知"
    }}
  }},
  "required": ["instruction_type", "execution_mode", "confidence", "reasoning"]
}}
```

**示例输出：**
```json
{{
  "instruction_type": "executable",
  "execution_mode": "multi_step",
  "confidence": 0.95,
  "reasoning": "从认知角度分析，执行者需要先探索CSV文件的未知结构和数据特征，构建对数据的认知理解，然后根据这种理解制定计算策略。这是一个从未知到已知的认知建构过程，符合多步骤的探索性理解特征。"
}}
```

请从认知哲学的角度分析指令，判断是否需要探索未知，并返回JSON格式的结果："""

    def classify_instruction(self, instruction: str) -> tuple[str, str]:
        """
        智能指令分类方法
        
        分类逻辑：
        1. 团队判断：如果当前Agent有团队成员，直接判定为多步骤任务（需要协作）
        2. 单Agent判断：使用LLM基于认知哲学进行分类
           - 信息性指令：获取知识、询问问题、解释概念等，无需外部操作
           - 执行性指令：需要对外部环境进行操作的任务
             * 单步骤：确定性执行，无需探索未知
             * 多步骤：探索性理解，需要探索未知并构建认知
        
        Args:
            instruction: 输入指令字符串
            
        Returns:
            tuple[str, str]: (指令类型, 执行方式)
            - 指令类型: "informational" | "executable" 
            - 执行方式: "chat" | "single_step" | "multi_step"
              * "chat": 信息性指令
              * "single_step": 单步骤执行性指令  
              * "multi_step": 多步骤执行性指令
              
        Raises:
            Exception: 当LLM调用失败时，会记录错误并返回默认分类
            
        Note:
            - 有团队成员时优先考虑协作需求
            - 单Agent时基于认知哲学进行深度分析
        """
        self._classification_stats["total_classifications"] += 1
        
        # 1. 团队判断：如果有团队成员，直接判定为多步骤（需要协作）
        if self.team:
            logger.debug(f"🔍 团队协作模式: '{instruction}' → 检测到团队成员 {list(self.team.keys())}，直接判定为多步骤")
            return ("executable", "multi_step")
        
        # 2. 单Agent模式：使用认知哲学分类
        try:
            # 使用优化的分类提示（包含JSON Schema）
            classification_prompt = self._get_optimized_classification_prompt_for_single_agent(instruction)
            
            # 调用LLM进行分类
            response = self.base_agent.llm.invoke(classification_prompt).content.strip()
            
            # 尝试解析JSON响应
            try:
                import json
                
                # 提取JSON部分（去除可能的markdown标记）
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    classification_data = json.loads(json_str)
                    
                    # 提取分类结果
                    instruction_type = classification_data.get("instruction_type", "").lower()
                    execution_mode = classification_data.get("execution_mode")
                    confidence = classification_data.get("confidence", 0)
                    reasoning = classification_data.get("reasoning", "")
                    
                    # 处理execution_mode的逻辑
                    if instruction_type == "informational":
                        execution_mode = "chat"  # informational类型统一使用chat
                    elif execution_mode:
                        execution_mode = execution_mode.lower()
                    else:
                        execution_mode = "single_step"  # 默认值
                    
                    # 验证分类结果的有效性
                    valid_types = ["informational", "executable"]
                    valid_modes = ["chat", "single_step", "multi_step"]
                    
                    if instruction_type in valid_types and execution_mode in valid_modes:
                        result = (instruction_type, execution_mode)
                        logger.debug(f"🔍 指令分类 (JSON): '{instruction}' → {result} | 置信度: {confidence:.2f} | 理由: {reasoning}")
                        return result
                
            except (json.JSONDecodeError, KeyError) as json_error:
                logger.debug(f"JSON解析失败，尝试传统格式解析: {json_error}")
                
                # 回退到传统的 "|" 分隔格式解析
                parts = response.split('|')
                if len(parts) == 2:
                    instruction_type = parts[0].strip().lower()
                    execution_mode = parts[1].strip().lower()
                    
                    # 处理execution_mode的逻辑（与JSON格式保持一致）
                    if instruction_type == "informational":
                        execution_mode = "chat"  # informational类型统一使用chat
                    elif instruction_type == "executable":
                        # 验证executable类型的execution_mode有效性
                        if execution_mode not in ["single_step", "multi_step"]:
                            execution_mode = "single_step"  # 默认值
                    
                    # 验证分类结果的有效性
                    valid_types = ["informational", "executable"]
                    valid_modes = ["chat", "single_step", "multi_step"]
                    
                    if instruction_type in valid_types and execution_mode in valid_modes:
                        result = (instruction_type, execution_mode)
                        logger.debug(f"🔍 指令分类 (传统): '{instruction}' → {result}")
                        return result
            
            # 如果解析失败，使用默认策略
            logger.warning(f"⚠️ 指令分类解析失败，使用默认策略。响应内容: {response[:100]}...")
            result = ("executable", "single_step")
            return result
            
        except Exception as e:
            self._classification_stats["classification_errors"] += 1
            logger.error(f"❌ 指令分类异常: {e}")
            # 异常情况下默认为单步骤执行性指令
            result = ("executable", "single_step")
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
        logger.info(f"[{self.agent_name}] 接收到指令: '{instruction}'")
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
            
            # 默认情况：使用基础Agent执行
            logger.debug("🔄 使用默认execute_sync执行")
            return self.base_agent.execute_sync(instruction)
            
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
                # 默认情况：使用基础Agent执行
                yield "🔄 使用默认execute_stream模式..."
                for result in self.base_agent.execute_stream(instruction):
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
    
    def execute_multi_step(self, goal: str):
        """
        执行多步骤目标任务（使用认知工作流）
        
        Args:
            goal: 目标任务描述
            
        Returns:
            WorkflowExecutionResult: 工作流执行结果
            
        Raises:
            RuntimeError: 当认知工作流组件不可用时
        """
        if not WORKFLOW_COMPONENTS_AVAILABLE:
            raise RuntimeError(
                "认知工作流组件不可用，无法执行多步骤任务。"
                "请确保cognitive_workflow_rule_base模块及其依赖项已正确安装。"
            )
        
        if self.workflow_engine is None:
            logger.warning("⚠️ 认知工作流引擎不可用，无法执行多步骤任务")
            raise RuntimeError(
                "认知工作流引擎初始化失败，无法执行多步骤任务。"
                "请检查系统配置和依赖项。"
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
        
        return {
            "classification_stats": self._classification_stats.copy(),
            "execution_distribution": {
                k: (v / max(1, total_executions)) * 100 
                for k, v in self._classification_stats["execution_stats"].items()
            },
            "workflow_engine_status": self.workflow_engine is not None
        }
    
    
    def reset_stats(self) -> None:
        """重置性能统计"""
        self._classification_stats = {
            "total_classifications": 0,
            "classification_errors": 0,
            "execution_stats": {
                "chat": 0,
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
        
        return (f"IntelligentAgentWrapper("
                f"base_agent={type(self.base_agent).__name__}, "
                f"workflow_engine={'✅' if self.workflow_engine else '❌'}"
                f"{api_spec_preview})")


# Backward compatibility alias
CognitiveAgent = IntelligentAgentWrapper