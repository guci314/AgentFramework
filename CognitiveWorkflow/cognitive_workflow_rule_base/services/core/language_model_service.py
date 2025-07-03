# -*- coding: utf-8 -*-
"""
语言模型服务

提供统一的LLM服务抽象层，支持语义匹配、自然语言生成、
文本分类等核心AI能力。这是整个产生式规则系统的AI引擎。
"""

from typing import Dict, List, Any, Optional, Tuple
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
import json
import logging

from ...domain.value_objects import MatchingResult, MatchingConstants

logger = logging.getLogger(__name__)


class LanguageModelService:
    """语言模型服务 - 统一的LLM服务抽象"""
    
    def __init__(self, 
                 primary_llm: BaseChatModel,
                 fallback_llm: Optional[BaseChatModel] = None):
        """
        初始化语言模型服务
        
        Args:
            primary_llm: 主要的语言模型
            fallback_llm: 备用的语言模型（可选）
        """
        self.primary_llm = primary_llm
        self.fallback_llm = fallback_llm
        
    def semantic_match(self, condition: str, state_description: str) -> MatchingResult:
        """
        语义匹配：判断条件是否与状态描述匹配
        
        Args:
            condition: 规则条件（自然语言）
            state_description: 当前状态描述（自然语言）
            
        Returns:
            MatchingResult: 匹配结果，包含是否匹配、置信度、推理等
        """
        try:
            prompt = f"""
你是一个专业的语义匹配专家。请判断给定的条件是否与当前状态匹配。

条件: {condition}
当前状态: {state_description}

请分析这两个文本的语义关系，并按以下JSON格式返回结果：
{{
    "is_match": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "详细的匹配分析和推理过程",
    "semantic_similarity": 0.0-1.0
}}

分析要点：
1. 语义相似性：条件和状态是否表达相似的含义
2. 逻辑关系：当前状态是否满足条件的要求
3. 上下文一致性：在当前上下文中条件是否适用
4. 置信度评估：基于以上分析给出匹配的置信度

请确保返回有效的JSON格式。
"""
            
            response = self._call_llm(prompt)
            result_data = self._parse_json_response(response)
            
            return MatchingResult(
                is_match=result_data.get('is_match', False),
                confidence=float(result_data.get('confidence', 0.0)),
                reasoning=result_data.get('reasoning', ''),
                semantic_similarity=float(result_data.get('semantic_similarity', 0.0))
            )
            
        except Exception as e:
            logger.error(f"语义匹配失败: {e}")
            return MatchingResult(
                is_match=False,
                confidence=0.0,
                reasoning=f"匹配过程中发生错误: {str(e)}",
                semantic_similarity=0.0
            )
    
    def generate_natural_language_response(self, 
                                         prompt: str, 
                                         context: Optional[Dict[str, Any]] = None) -> str:
        """
        生成自然语言响应
        
        Args:
            prompt: 输入提示
            context: 可选的上下文信息
            
        Returns:
            str: 生成的自然语言响应
        """
        try:
            # 构建完整的提示
            full_prompt = prompt
            if context:
                context_str = self._format_context(context)
                full_prompt = f"上下文信息：\n{context_str}\n\n{prompt}"
            
            response = self._call_llm(full_prompt)
            return response
            
        except Exception as e:
            logger.error(f"自然语言生成失败: {e}")
            return f"生成失败: {str(e)}"
    
    def evaluate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        评估两个文本的语义相似度
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            
        Returns:
            float: 相似度分数（0.0-1.0）
        """
        try:
            prompt = f"""
请评估以下两个文本的语义相似度，返回0.0到1.0之间的分数：

文本1: {text1}
文本2: {text2}

评估标准：
- 1.0: 语义完全相同
- 0.8-0.9: 语义非常相似，表达基本相同的意思
- 0.6-0.7: 语义相似，有共同主题
- 0.4-0.5: 有一定相关性，但含义不同
- 0.2-0.3: 相关性较低
- 0.0-0.1: 完全无关

请只返回一个数字（0.0-1.0）。
"""
            
            response = self._call_llm(prompt)
            # 提取数字
            import re
            numbers = re.findall(r'0\.\d+|1\.0|0|1', response)
            if numbers:
                return float(numbers[0])
            return 0.0
            
        except Exception as e:
            logger.error(f"语义相似度评估失败: {e}")
            return 0.0
    
    def explain_reasoning(self, decision_context: str) -> str:
        """
        解释推理过程
        
        Args:
            decision_context: 决策上下文
            
        Returns:
            str: 推理解释
        """
        try:
            prompt = f"""
请对以下决策过程进行详细解释：

{decision_context}

请提供清晰、逻辑性强的解释，包括：
1. 分析的关键因素
2. 决策的依据
3. 可能的替代方案
4. 决策的合理性

解释应该简洁明了，便于理解。
"""
            
            response = self._call_llm(prompt)
            return response
            
        except Exception as e:
            logger.error(f"推理解释失败: {e}")
            return f"解释生成失败: {str(e)}"
    
    def classify_text(self, text: str, categories: List[str]) -> Tuple[str, float]:
        """
        文本分类
        
        Args:
            text: 要分类的文本
            categories: 分类类别列表
            
        Returns:
            Tuple[str, float]: (分类结果, 置信度)
        """
        try:
            categories_str = "、".join(categories)
            prompt = f"""
请将以下文本分类到这些类别中的一个：{categories_str}

文本: {text}

请返回最合适的类别名称和置信度（0.0-1.0），格式如下：
类别: [类别名称]
置信度: [0.0-1.0]
"""
            
            response = self._call_llm(prompt)
            
            # 解析响应
            lines = response.strip().split('\n')
            category = ""
            confidence = 0.0
            
            for line in lines:
                if line.startswith('类别:'):
                    category = line.split(':', 1)[1].strip()
                elif line.startswith('置信度:'):
                    try:
                        confidence = float(line.split(':', 1)[1].strip())
                    except ValueError:
                        confidence = 0.5
            
            if not category or category not in categories:
                category = categories[0]  # 默认第一个类别
                confidence = 0.3
            
            return category, confidence
            
        except Exception as e:
            logger.error(f"文本分类失败: {e}")
            return categories[0] if categories else "unknown", 0.0
    
    def extract_key_information(self, text: str, schema: Dict[str, str]) -> Dict[str, Any]:
        """
        提取关键信息
        
        Args:
            text: 输入文本
            schema: 提取模式，格式为 {字段名: 字段描述}
            
        Returns:
            Dict[str, Any]: 提取的信息
        """
        try:
            schema_desc = ""
            for field, desc in schema.items():
                schema_desc += f"- {field}: {desc}\n"
            
            prompt = f"""
请从以下文本中提取关键信息：

文本: {text}

需要提取的信息：
{schema_desc}

请以JSON格式返回提取的信息，如果某个字段无法提取则设为null。
示例格式：
{{
    "字段1": "提取的值1",
    "字段2": "提取的值2",
    "字段3": null
}}
"""
            
            response = self._call_llm(prompt)
            extracted_data = self._parse_json_response(response)
            
            # 确保所有字段都存在
            result = {}
            for field in schema.keys():
                result[field] = extracted_data.get(field)
            
            return result
            
        except Exception as e:
            logger.error(f"信息提取失败: {e}")
            return {field: None for field in schema.keys()}
    
    def evaluate_goal_achievement(self, goal: str, current_state: str) -> Tuple[bool, float, str]:
        """
        评估目标是否达成
        
        Args:
            goal: 目标描述
            current_state: 当前状态描述
            
        Returns:
            Tuple[bool, float, str]: (是否达成, 置信度, 分析说明)
        """
        try:
            prompt = f"""
请评估目标是否已经达成：

目标: {goal}
当前状态: {current_state}

请分析当前状态是否满足目标要求，返回JSON格式：
{{
    "goal_achieved": true/false,
    "confidence": 0.0-1.0,
    "analysis": "详细的分析说明"
}}

分析要点：
1. 目标的具体要求是什么
2. 当前状态满足了哪些要求
3. 还有哪些要求未满足
4. 总体完成度评估
"""
            
            response = self._call_llm(prompt)
            result_data = self._parse_json_response(response)
            
            return (
                result_data.get('goal_achieved', False),
                float(result_data.get('confidence', 0.0)),
                result_data.get('analysis', '')
            )
            
        except Exception as e:
            logger.error(f"目标达成评估失败: {e}")
            return False, 0.0, f"评估失败: {str(e)}"
    
    def validate_execution_result(self, 
                                action: str, 
                                actual_result: str, 
                                expected_outcome: str) -> Tuple[bool, float, str]:
        """
        验证执行结果是否符合期望
        
        Args:
            action: 执行的动作描述
            actual_result: 实际执行结果
            expected_outcome: 期望的结果
            
        Returns:
            Tuple[bool, float, str]: (是否符合期望, 置信度, 验证说明)
        """
        try:
            prompt = f"""
请验证执行结果是否符合期望：

执行的动作: {action}
实际结果: {actual_result}
期望结果: {expected_outcome}

请分析实际结果是否满足期望，返回JSON格式：
{{
    "result_valid": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "详细的验证分析"
}}

验证要点：
1. 实际结果是否包含期望结果的关键要素
2. 实际结果的质量和完整性
3. 是否存在明显的错误或遗漏
4. 语义上是否达到了期望的效果

注意：
- 不要过分拘泥于字面匹配，重点关注语义和实际效果
- 如果实际结果在语义上满足期望，即使表述不同也应认为有效
- 考虑动作的性质和上下文来判断结果的合理性
"""
            
            response = self._call_llm(prompt)
            result_data = self._parse_json_response(response)
            
            return (
                result_data.get('result_valid', False),
                float(result_data.get('confidence', 0.0)),
                result_data.get('reasoning', '')
            )
            
        except Exception as e:
            logger.error(f"执行结果验证失败: {e}")
            return True, 0.5, f"验证失败，默认通过: {str(e)}"  # 验证失败时默认通过，避免阻塞
    
    def _call_llm(self, prompt: str) -> str:
        """
        调用语言模型
        
        Args:
            prompt: 输入提示
            
        Returns:
            str: 模型响应
        """
        try:
            # 尝试主要模型
            messages = [HumanMessage(content=prompt)]
            response = self.primary_llm.invoke(messages)
            return response.content
            
        except Exception as e:
            logger.warning(f"主要模型调用失败: {e}")
            
            # 尝试备用模型
            if self.fallback_llm:
                try:
                    messages = [HumanMessage(content=prompt)]
                    response = self.fallback_llm.invoke(messages)
                    return response.content
                except Exception as e2:
                    logger.error(f"备用模型也调用失败: {e2}")
            
            raise Exception(f"所有模型调用都失败了: {e}")
    
    def _parse_json_response(self, response: str):
        """
        解析JSON响应，支持对象和数组格式
        
        Args:
            response: 模型响应
            
        Returns:
            Union[Dict[str, Any], List[Any]]: 解析后的JSON数据
        """
        try:
            # 清理响应中的markdown格式
            import re
            cleaned_response = response.strip()
            
            # 移除markdown代码块标记
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # 尝试直接解析清理后的响应
            try:
                return json.loads(cleaned_response)
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试提取JSON部分
                
                # 先尝试提取JSON对象
                json_object_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                if json_object_match:
                    json_str = json_object_match.group()
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
                
                # 再尝试提取JSON数组
                json_array_match = re.search(r'\[.*\]', cleaned_response, re.DOTALL)
                if json_array_match:
                    json_str = json_array_match.group()
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
                
                # 最后尝试原始响应
                return json.loads(response)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 响应内容: {response[:500]}...")
            return {}
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        格式化上下文信息
        
        Args:
            context: 上下文字典
            
        Returns:
            str: 格式化后的上下文字符串
        """
        formatted_items = []
        for key, value in context.items():
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                value_str = str(value)
            formatted_items.append(f"- {key}: {value_str}")
        
        return "\n".join(formatted_items)