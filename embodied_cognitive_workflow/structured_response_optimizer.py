#!/usr/bin/env python3
"""
结构化响应优化器
使用 response_format 和 JSON schema 确保稳定的 JSON 输出

这个模块演示了如何使用 OpenAI 的 response_format 参数
和完整的 JSON schema 来获得稳定可靠的 JSON 响应。
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging

# JSON Schema 定义
STRATEGY_OPTIMIZATION_SCHEMA = {
    "type": "object",
    "properties": {
        "analysis": {
            "type": "string",
            "description": "对当前策略的分析结果"
        },
        "strategies": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "建议的优化策略列表",
            "minItems": 1,
            "maxItems": 5
        },
        "priority": {
            "type": "string",
            "enum": ["high", "medium", "low"],
            "description": "实施优先级"
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "建议的置信度分数"
        }
    },
    "required": ["analysis", "strategies", "priority", "confidence"],
    "additionalProperties": False
}

STRATEGY_REGULATION_SCHEMA = {
    "type": "object",
    "properties": {
        "assessment": {
            "type": "string",
            "description": "对当前策略的评估"
        },
        "adjustment_needed": {
            "type": "boolean",
            "description": "是否需要调整策略"
        },
        "recommended_strategy": {
            "type": "string",
            "description": "推荐的策略"
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "评估的置信度"
        },
        "reasoning": {
            "type": "string",
            "description": "评估的理由"
        }
    },
    "required": ["assessment", "adjustment_needed", "recommended_strategy", "confidence"],
    "additionalProperties": False
}

REFLECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "lessons": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "从经验中学到的经验教训",
            "minItems": 1,
            "maxItems": 5
        },
        "suggestions": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "改进建议",
            "minItems": 1,
            "maxItems": 5
        },
        "quality": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "反思质量评分"
        },
        "insights": {
            "type": "string",
            "description": "关键洞察"
        }
    },
    "required": ["lessons", "suggestions", "quality"],
    "additionalProperties": False
}

META_LEARNING_SCHEMA = {
    "type": "object",
    "properties": {
        "success_patterns": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "成功模式列表",
            "minItems": 1
        },
        "failure_causes": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "失败原因列表",
            "minItems": 1
        },
        "insights": {
            "type": "string",
            "description": "学习洞察"
        },
        "recommendations": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "基于学习的建议",
            "minItems": 1
        }
    },
    "required": ["success_patterns", "failure_causes", "insights"],
    "additionalProperties": False
}


class StructuredResponseOptimizer:
    """结构化响应优化器"""
    
    def __init__(self, llm, logger: Optional[logging.Logger] = None):
        self.llm = llm
        self.logger = logger or logging.getLogger(__name__)
    
    def _safe_json_dumps(self, data: Any) -> str:
        """安全序列化为JSON字符串，处理datetime等特殊对象"""
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        try:
            result = json.dumps(data, ensure_ascii=False, indent=2, default=json_serializer)
            # 限制输出长度以避免提示过长
            if len(result) > 1000:
                self.logger.debug(f"JSON序列化结果过长({len(result)}字符)，进行截断")
                return json.dumps(str(data)[:500] + "...(截断)", ensure_ascii=False)
            return result
        except Exception as e:
            self.logger.warning(f"JSON序列化失败: {e}, 使用简化版本")
            return str(data)[:300]  # 限制长度
    
    def _call_llm_with_schema(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """使用 JSON schema 调用 LLM"""
        try:
            # 尝试使用 OpenAI 的 response_format
            if hasattr(self.llm, 'client') and hasattr(self.llm.client, 'chat'):
                try:
                    # 直接使用 OpenAI 客户端的 JSON mode
                    response = self.llm.client.chat.completions.create(
                        model=self.llm.model_name or "gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt + "\n\n必须返回JSON格式。"}],
                        response_format={"type": "json_object"},
                        temperature=0.3
                    )
                    return json.loads(response.choices[0].message.content)
                except Exception as api_error:
                    self.logger.warning(f"OpenAI API结构化输出失败: {api_error}")
            
            # 降级到传统方法，但使用更强的JSON提示
            self.logger.info("使用增强型JSON提示模式")
            
            # 添加更强的JSON格式要求
            enhanced_prompt = f"""{prompt}

重要：你必须只返回纯 JSON 格式，不能有任何其他文本。
示例格式：
{json.dumps(self._get_example_for_schema(schema), ensure_ascii=False, indent=2)}

请现在返回你的JSON响应："""
            
            response = self.llm.invoke(enhanced_prompt)
            content = response.content.strip()
            
            # 尝试提取JSON
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            return json.loads(content.strip())
                
        except Exception as e:
            self.logger.error(f"结构化响应调用失败: {e}")
            raise
    
    def _get_example_for_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """根据JSON schema生成示例"""
        example = {}
        properties = schema.get('properties', {})
        
        for field, field_schema in properties.items():
            field_type = field_schema.get('type')
            if field_type == 'string':
                if 'enum' in field_schema:
                    example[field] = field_schema['enum'][0]
                else:
                    example[field] = "示例文本"
            elif field_type == 'number':
                example[field] = 0.8
            elif field_type == 'boolean':
                example[field] = False
            elif field_type == 'array':
                example[field] = ["示例项目1", "示例项目2"]
            else:
                example[field] = "示例值"
        
        return example
    
    def optimize_strategy_structured(self, 
                                   current_performance: Dict[str, float],
                                   context: Dict[str, Any],
                                   goals: List[str]) -> Dict[str, Any]:
        """使用结构化输出优化策略"""
        try:
            prompt = f"""基于以下信息优化认知策略：

当前性能指标：
{self._safe_json_dumps(current_performance)}

上下文信息：
{self._safe_json_dumps(context)}

目标：
{self._safe_json_dumps(goals)}

请分析当前策略并提供优化建议。你的响应必须严格遵循以下JSON格式：

- analysis: 对当前策略的详细分析
- strategies: 1-5个具体的优化策略建议
- priority: 实施优先级（high/medium/low）
- confidence: 0.0-1.0的置信度分数

请确保提供实用、可执行的建议。"""

            return self._call_llm_with_schema(prompt, STRATEGY_OPTIMIZATION_SCHEMA)
            
        except Exception as e:
            self.logger.error(f"结构化策略优化失败: {e}")
            # 返回符合 schema 的默认响应
            return {
                "analysis": "由于系统错误，使用默认策略分析",
                "strategies": ["保持当前策略", "监控性能指标"],
                "priority": "medium",
                "confidence": 0.5
            }
    
    def regulate_strategy_structured(self, 
                                   current_context: Dict[str, Any], 
                                   target_goals: List[str]) -> Dict[str, Any]:
        """使用结构化输出调节策略"""
        try:
            prompt = f"""评估当前认知策略并确定是否需要调整：

当前上下文：
{self._safe_json_dumps(current_context)}

目标：
{self._safe_json_dumps(target_goals)}

请评估当前策略的适用性。你的响应必须严格遵循以下JSON格式：

- assessment: 对当前策略的评估
- adjustment_needed: 是否需要调整（true/false）
- recommended_strategy: 推荐的策略
- confidence: 0.0-1.0的置信度分数
- reasoning: 评估的理由（可选）

请基于当前上下文和目标进行客观评估。"""

            return self._call_llm_with_schema(prompt, STRATEGY_REGULATION_SCHEMA)
            
        except Exception as e:
            self.logger.error(f"结构化策略调节失败: {e}")
            # 返回符合 schema 的默认响应
            return {
                "assessment": "由于系统错误，策略评估不可用",
                "adjustment_needed": False,
                "recommended_strategy": "继续使用当前策略",
                "confidence": 0.5,
                "reasoning": "系统错误导致无法完成评估"
            }
    
    def reflect_structured(self, 
                          experience: Dict[str, Any], 
                          outcome: Dict[str, Any]) -> Dict[str, Any]:
        """使用结构化输出进行反思"""
        try:
            prompt = f"""基于以下经验和结果进行反思：

经验：
{self._safe_json_dumps(experience)}

结果：
{self._safe_json_dumps(outcome)}

请从这次经验中提取学习内容。你的响应必须严格遵循以下JSON格式：

- lessons: 1-5个从经验中学到的教训
- suggestions: 1-5个改进建议
- quality: 0.0-1.0的反思质量评分
- insights: 关键洞察（可选）

请提供具体、可操作的学习内容。"""

            return self._call_llm_with_schema(prompt, REFLECTION_SCHEMA)
            
        except Exception as e:
            self.logger.error(f"结构化反思失败: {e}")
            # 返回符合 schema 的默认响应
            return {
                "lessons": ["经验积累很重要", "需要持续改进"],
                "suggestions": ["加强监控", "优化流程"],
                "quality": 0.6,
                "insights": "由于系统错误，反思不完整"
            }
    
    def meta_learn_structured(self, 
                            success_cases: List[Dict[str, Any]], 
                            failure_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """使用结构化输出进行元学习"""
        try:
            prompt = f"""基于成功和失败案例进行元学习分析：

成功案例：
{self._safe_json_dumps(success_cases)}

失败案例：
{self._safe_json_dumps(failure_cases)}

请提取学习模式和洞察。你的响应必须严格遵循以下JSON格式：

- success_patterns: 成功模式列表
- failure_causes: 失败原因列表  
- insights: 学习洞察
- recommendations: 基于学习的建议（可选）

请提供深入的分析和可操作的建议。"""

            return self._call_llm_with_schema(prompt, META_LEARNING_SCHEMA)
            
        except Exception as e:
            self.logger.error(f"结构化元学习失败: {e}")
            # 返回符合 schema 的默认响应
            return {
                "success_patterns": ["系统化方法", "持续监控"],
                "failure_causes": ["准备不足", "沟通不畅"],
                "insights": "由于系统错误，元学习分析不完整",
                "recommendations": ["建立更好的监控", "改进沟通机制"]
            }


def test_structured_responses():
    """测试结构化响应"""
    import os
    from langchain_openai import ChatOpenAI
    
    # 初始化 LLM
    if os.getenv('DEEPSEEK_API_KEY'):
        llm = ChatOpenAI(
            model="deepseek-chat",
            openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
            openai_api_base="https://api.deepseek.com",
            max_tokens=1000,
            temperature=0.3
        )
    elif os.getenv('OPENAI_API_KEY'):
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            max_tokens=1000,
            temperature=0.3
        )
    else:
        print("❌ 未找到API密钥")
        return
    
    # 创建优化器
    optimizer = StructuredResponseOptimizer(llm)
    
    print("🧪 测试结构化响应...")
    
    # 测试策略优化
    try:
        result = optimizer.optimize_strategy_structured(
            current_performance={"efficiency": 0.8, "accuracy": 0.9},
            context={"task": "认知监督", "complexity": "高"},
            goals=["提高效率", "保持准确性"]
        )
        print("✅ 结构化策略优化成功")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"❌ 结构化策略优化失败: {e}")


if __name__ == "__main__":
    test_structured_responses()