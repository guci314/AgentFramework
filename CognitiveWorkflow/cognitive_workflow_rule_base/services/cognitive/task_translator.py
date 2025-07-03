# -*- coding: utf-8 -*-
"""
任务翻译层

解决层次化认知架构中的上下文污染问题，确保低层Agent对上层状态保持无知。
通过LLM驱动的智能翻译，实现：
1. 任务提取：从复杂嵌套目标中提取核心任务
2. 上下文过滤：移除无关上层信息，保留必要边界约束  
3. 粒度适配：自动确定任务分解的适当粒度级别

Author: Claude Code Assistant
Date: 2025-07-01
Version: 1.0.0
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# 导入AgentBase和相关类型
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from agent_base import AgentBase

logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    """翻译结果数据类"""
    extracted_task: str          # 提取的核心任务
    filtered_context: str        # 过滤后的上下文
    confidence: float            # 翻译置信度
    reasoning: str               # 翻译推理过程
    boundary_constraints: List[str]  # 边界约束条件




class TaskTranslator:
    """
    任务翻译层核心类
    
    使用LLM驱动的智能翻译，解决层次化认知架构中的上下文污染问题。
    实现低层Agent对上层状态的无知原则。
    """
    
    def __init__(self, llm):
        """
        初始化任务翻译器
        
        Args:
            llm: 语言模型实例
        """
        self.llm = llm
        
        # 设置翻译器的系统提示词
        self._setup_system_prompt()
        
        logger.info("✅ TaskTranslator初始化完成")
    
    def _setup_system_prompt(self):
        """设置任务翻译器的系统提示词"""
        self.system_prompt = """你是智能任务翻译器，专门负责解决复杂任务中的信息污染问题。

## 核心职责
你的使命是从复杂的嵌套任务描述中提取清晰、简洁的核心任务。

## 翻译原则
1. **任务提取**：从复杂目标中提取最重要的核心任务
2. **信息过滤**：移除冗余的背景信息和无关细节
3. **边界保护**：保留执行必需的约束条件和限制
4. **粒度适配**：智能判断任务分解的合适粒度级别

## 信息处理规则
- **信息简化**：过滤掉冗余的内部状态、决策过程或复杂背景
- **接口清晰**：只传递完成任务所必需的最小信息集
- **边界明确**：保留影响执行的约束条件，去除实现细节
- **自主执行**：翻译后的任务应该可以独立理解和执行

## 输出格式
必须返回严格的JSON格式：
```json
{
  "extracted_task": "提取的核心任务描述",
  "filtered_context": "过滤后的必要上下文",
  "confidence": 0.85,
  "reasoning": "翻译分析和推理过程",
  "boundary_constraints": ["约束条件1", "约束条件2"]
}
```

## 输出要求
**严格要求**：
1. 只返回纯JSON对象，不要任何解释文字
2. 不要包含markdown代码块标记
3. 不要在JSON前后添加任何说明
4. 确保JSON格式正确且完整
5. 所有字段都必须存在且格式正确

**错误示例**：
```json
{"extracted_task": "..."}
```
这样的任务是...

**正确示例**：
{"extracted_task": "...", "filtered_context": "...", "confidence": 0.85, "reasoning": "...", "boundary_constraints": []}

只返回JSON对象，没有任何其他内容！"""
    
    def translate_task(self, complex_goal: str) -> TranslationResult:
        """
        翻译复杂目标为简洁任务
        
        Args:
            complex_goal: 复杂的嵌套目标描述
            
        Returns:
            TranslationResult: 翻译结果
        """
        logger.info(f"🔄 开始任务翻译: {complex_goal[:100]}...")
        
        try:
            # 构建翻译提示词
            prompt = self._build_translation_prompt(complex_goal)
            
            # 调用LLM进行翻译
            response = self._call_llm_with_json_format(prompt)
            logger.debug(f"🔍 LLM原始响应: {response[:300]}...")
            
            # 解析翻译结果
            result = self._parse_translation_response(response)
            
            logger.info(f"✅ 任务翻译完成，置信度: {result.confidence}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 任务翻译失败: {e}")
            import traceback
            logger.error(f"完整错误堆栈: {traceback.format_exc()}")
            # 返回保守的回退结果
            return TranslationResult(
                extracted_task=complex_goal,  # 直接使用原始目标
                filtered_context="",
                confidence=0.0,
                reasoning=f"翻译失败: {str(e)}",
                boundary_constraints=[]
            )
    
    def _build_translation_prompt(self, complex_goal: str) -> str:
        """构建翻译提示词"""
        return f"""请对以下复杂目标进行智能翻译，提取核心任务：

输入的复杂目标:
{complex_goal}

## 翻译要求
1. **提取核心任务**：识别最重要的具体任务目标
2. **过滤无关信息**：移除冗余的内部状态、决策细节和复杂背景
3. **保留必要约束**：保留影响任务执行的边界条件和限制

## 分析维度
- 任务的核心目标是什么？
- 哪些信息是执行必需的？
- 哪些信息属于冗余背景？
- 存在哪些必须遵守的边界约束？

**重要提醒**：请严格按照系统提示词中的JSON格式返回翻译结果。
- 只返回JSON对象
- 不要任何解释或附加文字
- 不要使用代码块标记
- 确保JSON格式完整正确

请直接返回JSON响应："""
    
    def _call_llm_with_json_format(self, prompt: str) -> str:
        """调用LLM并要求JSON格式响应"""
        try:
            # 创建临时的AgentBase实例来调用LLM
            temp_agent = AgentBase(self.llm)
            temp_agent.system_message = self.system_prompt
            
            # 使用JSON格式调用
            response = temp_agent.chat_sync(prompt, response_format={"type": "json_object"})
            
            # 处理不同类型的响应
            if hasattr(response, 'content'):
                return response.content
            elif hasattr(response, 'return_value'):
                # 处理agent_base.Result对象
                if isinstance(response.return_value, str):
                    return response.return_value
                elif isinstance(response.return_value, dict):
                    import json
                    return json.dumps(response.return_value)
                else:
                    return str(response.return_value)
            else:
                return str(response)
            
        except Exception as e:
            logger.error(f"❌ LLM调用失败: {e}")
            raise
    
    def _parse_translation_response(self, response: str) -> TranslationResult:
        """解析翻译响应"""
        try:
            # 清理响应内容
            content = response.strip()
            
            # 移除markdown代码块标记
            if content.startswith('```json'):
                content = content[7:]
            elif content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # 尝试提取JSON部分 - 寻找第一个完整的JSON对象
            try:
                # 寻找JSON开始位置
                start_idx = content.find('{')
                if start_idx == -1:
                    raise ValueError("响应中未找到JSON对象")
                
                # 从开始位置解析JSON，处理可能的额外内容
                brace_count = 0
                end_idx = start_idx
                
                for i, char in enumerate(content[start_idx:], start_idx):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                # 提取JSON部分
                json_content = content[start_idx:end_idx]
                logger.debug(f"提取的JSON内容: {json_content[:200]}...")
                
                # 解析JSON
                data = json.loads(json_content)
                logger.debug(f"🔍 成功解析JSON数据: {data}")
                
            except (json.JSONDecodeError, ValueError) as json_err:
                # 如果仍然失败，尝试直接解析原始内容
                logger.warning(f"JSON提取失败: {json_err}，尝试直接解析")
                data = json.loads(content)
            
            # 字段映射 - 支持多种可能的字段名
            field_mappings = {
                'extracted_task': ['extracted_task', 'core_task', 'task', 'main_task', 'goal', 'objective'],
                'filtered_context': ['filtered_context', 'essential_information', 'context', 'necessary_context', 'filtered_info'],
                'confidence': ['confidence', 'certainty', 'score', 'probability'],
                'reasoning': ['reasoning', 'analysis', 'explanation', 'reason', 'rationale'],
                'boundary_constraints': ['boundary_constraints', 'constraints', 'limitations', 'requirements', 'rules']
            }
            
            # 使用映射提取字段值
            extracted_data = {}
            for target_field, possible_names in field_mappings.items():
                value = None
                for name in possible_names:
                    if name in data:
                        value = data[name]
                        break
                
                if value is None and target_field == 'extracted_task':
                    # 必需字段缺失时使用默认值
                    value = "任务提取失败"
                
                extracted_data[target_field] = value
            
            # 安全处理置信度
            confidence_value = extracted_data.get('confidence', 0.0)
            if confidence_value is None:
                confidence_value = 0.0
            try:
                confidence_float = float(confidence_value)
            except (ValueError, TypeError):
                confidence_float = 0.0
            
            # 安全处理字符串字段
            def safe_str_field(value, default=''):
                """安全转换为字符串类型"""
                if value is None:
                    return default
                elif isinstance(value, str):
                    return value
                elif isinstance(value, list):
                    return ' '.join(str(item) for item in value)
                else:
                    return str(value)
            
            # 安全处理列表字段
            def safe_list_field(value, default=None):
                """安全转换为列表类型"""
                if default is None:
                    default = []
                if value is None:
                    return default
                elif isinstance(value, list):
                    return value
                elif isinstance(value, str):
                    return [value] if value.strip() else default
                else:
                    return [str(value)]
            
            # 构建结果对象
            result = TranslationResult(
                extracted_task=safe_str_field(extracted_data.get('extracted_task'), ''),
                filtered_context=safe_str_field(extracted_data.get('filtered_context'), ''),
                confidence=confidence_float,
                reasoning=safe_str_field(extracted_data.get('reasoning'), ''),
                boundary_constraints=safe_list_field(extracted_data.get('boundary_constraints'))
            )
            
            # 验证置信度范围
            result.confidence = max(0.0, min(1.0, result.confidence))
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON解析失败: {e}")
            logger.error(f"响应内容: {response[:500]}...")
            import traceback
            logger.error(f"JSON解析错误堆栈: {traceback.format_exc()}")
            raise ValueError(f"无效的JSON格式: {str(e)}")
        except Exception as e:
            logger.error(f"❌ 响应解析失败: {e}")
            logger.error(f"响应内容: {response[:500]}...")
            import traceback
            logger.error(f"响应解析错误堆栈: {traceback.format_exc()}")
            raise ValueError(f"响应格式不符合要求: {str(e)}")
    


class TaskExtractor:
    """任务提取器 - 专门负责从复杂上下文中提取核心任务"""
    
    def __init__(self, translator: TaskTranslator):
        self.translator = translator
        
    def extract_core_task(self, complex_goal: str) -> str:
        """提取核心任务"""
        result = self.translator.translate_task(complex_goal)
        return result.extracted_task


class ContextFilter:
    """上下文过滤器 - 专门负责过滤无关信息"""
    
    def __init__(self, translator: TaskTranslator):
        self.translator = translator
        
    def filter_context(self, complex_goal: str) -> Tuple[str, List[str]]:
        """过滤上下文，返回(过滤后上下文, 边界约束)"""
        result = self.translator.translate_task(complex_goal)
        return result.filtered_context, result.boundary_constraints


class GranularityAdapter:
    """粒度适配器 - 专门负责确定任务粒度级别"""
    
    def __init__(self, translator: TaskTranslator):
        self.translator = translator
        
    def determine_granularity(self, complex_goal: str) -> str:
        """确定任务粒度级别"""
        result = self.translator.translate_task(complex_goal)
        return result.granularity_level