"""
元认知智能体 - 元认知监督层

基于具身认知理论的元认知智能体实现，作为四层认知架构的最高层，
负责认知错误识别、逻辑验证、道德引导和元认知监督。

元认知的核心功能：
- 认知偏差检测（确认偏差、锚定效应等）
- 逻辑错误识别（推理谬误、前提缺陷等）
- 一致性验证（目标对齐、价值一致性等）
- 道德约束（伦理评估、价值引导等）
- 元认知监督（策略优化、反思学习等）
"""

import sys
import os
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import logging

# 导入结构化响应优化器
try:
    from .structured_response_optimizer import (
        StructuredResponseOptimizer,
        STRATEGY_OPTIMIZATION_SCHEMA,
        STRATEGY_REGULATION_SCHEMA
    )
except ImportError:
    # 如果导入失败，将在类中处理
    StructuredResponseOptimizer = None
    STRATEGY_OPTIMIZATION_SCHEMA = None
    STRATEGY_REGULATION_SCHEMA = None

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_base import AgentBase, Result
from langchain_core.language_models import BaseChatModel


class CognitiveHealthStatus(Enum):
    """认知健康状态枚举"""
    EXCELLENT = "优秀"
    GOOD = "良好"
    FAIR = "一般"
    POOR = "较差"
    CRITICAL = "严重"


class BiasType(Enum):
    """认知偏差类型"""
    CONFIRMATION_BIAS = "确认偏差"
    ANCHORING_BIAS = "锚定偏差"
    AVAILABILITY_HEURISTIC = "可得性启发"
    OVERCONFIDENCE_BIAS = "过度自信偏差"
    REPRESENTATIVENESS_HEURISTIC = "代表性启发"
    FRAMING_EFFECT = "框架效应"


class LogicErrorType(Enum):
    """逻辑错误类型"""
    CIRCULAR_REASONING = "循环论证"
    FALSE_DICHOTOMY = "虚假二分法"
    AD_HOMINEM = "人身攻击"
    STRAWMAN = "稻草人谬误"
    SLIPPERY_SLOPE = "滑坡谬误"
    HASTY_GENERALIZATION = "草率概括"


@dataclass
class CognitiveBias:
    """认知偏差数据结构"""
    bias_type: BiasType
    severity: float  # 0.0-1.0
    evidence: str
    affected_reasoning: str
    suggested_correction: str
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class LogicError:
    """逻辑错误数据结构"""
    error_type: LogicErrorType
    severity: float  # 0.0-1.0
    premise: str
    conclusion: str
    explanation: str
    suggested_fix: str
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class ConsistencyIssue:
    """一致性问题数据结构"""
    issue_type: str
    description: str
    conflicting_elements: List[str]
    impact_assessment: str
    resolution_suggestion: str
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class CognitiveHealthAssessment:
    """认知健康评估结果"""
    overall_score: float  # 0.0-1.0
    status: CognitiveHealthStatus
    bias_count: int
    logic_errors: int
    consistency_issues: int
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    assessment_time: datetime = field(default_factory=datetime.now)


class CognitiveBiasDetector:
    """认知偏差检测器"""
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.detection_threshold = 0.6
        self.logger = logging.getLogger(__name__)
    
    def detect_confirmation_bias(self, reasoning_text: str, context: Dict[str, Any]) -> Optional[CognitiveBias]:
        """检测确认偏差"""
        try:
            prompt = f"""
            分析以下推理过程是否存在确认偏差：

            推理内容：{reasoning_text}
            上下文：{json.dumps(context, ensure_ascii=False)}

            确认偏差的特征：
            1. 只寻找支持既有观点的证据
            2. 忽略或贬低反对证据
            3. 选择性解释信息

            请分析并返回JSON格式：
            {{
                "has_bias": true/false,
                "severity": 0.0-1.0,
                "evidence": "具体证据",
                "affected_reasoning": "受影响的推理部分",
                "correction": "纠正建议"
            }}
            """
            
            response = self.llm.invoke(prompt).content
            analysis = json.loads(response.strip())
            
            if analysis.get('has_bias', False) and analysis.get('severity', 0) > self.detection_threshold:
                return CognitiveBias(
                    bias_type=BiasType.CONFIRMATION_BIAS,
                    severity=analysis.get('severity', 0.0),
                    evidence=analysis.get('evidence', ''),
                    affected_reasoning=analysis.get('affected_reasoning', ''),
                    suggested_correction=analysis.get('correction', '')
                )
            
        except Exception as e:
            self.logger.error(f"确认偏差检测失败: {e}")
        
        return None
    
    def detect_anchoring_bias(self, decision_process: str, initial_info: str) -> Optional[CognitiveBias]:
        """检测锚定偏差"""
        try:
            prompt = f"""
            分析以下决策过程是否存在锚定偏差：

            初始信息：{initial_info}
            决策过程：{decision_process}

            锚定偏差的特征：
            1. 过度依赖第一次获得的信息
            2. 后续判断被初始信息过度影响
            3. 调整不充分

            请分析并返回JSON格式：
            {{
                "has_bias": true/false,
                "severity": 0.0-1.0,
                "evidence": "具体证据",
                "affected_reasoning": "受影响的推理部分",
                "correction": "纠正建议"
            }}
            """
            
            response = self.llm.invoke(prompt).content
            analysis = json.loads(response.strip())
            
            if analysis.get('has_bias', False) and analysis.get('severity', 0) > self.detection_threshold:
                return CognitiveBias(
                    bias_type=BiasType.ANCHORING_BIAS,
                    severity=analysis.get('severity', 0.0),
                    evidence=analysis.get('evidence', ''),
                    affected_reasoning=analysis.get('affected_reasoning', ''),
                    suggested_correction=analysis.get('correction', '')
                )
                
        except Exception as e:
            self.logger.error(f"锚定偏差检测失败: {e}")
        
        return None


class LogicErrorIdentifier:
    """逻辑错误识别器"""
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
    
    def identify_circular_reasoning(self, argument: str) -> Optional[LogicError]:
        """识别循环论证"""
        try:
            prompt = f"""
            检查以下论证是否存在循环论证：

            论证：{argument}

            循环论证的特征：
            1. 结论被用来支持前提
            2. 前提和结论实质上是同一个命题
            3. 缺乏独立的支持证据

            请分析并返回JSON格式：
            {{
                "has_error": true/false,
                "severity": 0.0-1.0,
                "premise": "前提",
                "conclusion": "结论",
                "explanation": "错误解释",
                "fix": "修复建议"
            }}
            """
            
            response = self.llm.invoke(prompt).content
            analysis = json.loads(response.strip())
            
            if analysis.get('has_error', False):
                return LogicError(
                    error_type=LogicErrorType.CIRCULAR_REASONING,
                    severity=analysis.get('severity', 0.0),
                    premise=analysis.get('premise', ''),
                    conclusion=analysis.get('conclusion', ''),
                    explanation=analysis.get('explanation', ''),
                    suggested_fix=analysis.get('fix', '')
                )
                
        except Exception as e:
            self.logger.error(f"循环论证检测失败: {e}")
        
        return None
    
    def identify_false_dichotomy(self, argument: str) -> Optional[LogicError]:
        """识别虚假二分法"""
        try:
            prompt = f"""
            检查以下论证是否存在虚假二分法：

            论证：{argument}

            虚假二分法的特征：
            1. 将复杂问题简化为只有两个选择
            2. 忽略其他可能的选项
            3. 非黑即白的思维模式

            请分析并返回JSON格式：
            {{
                "has_error": true/false,
                "severity": 0.0-1.0,
                "premise": "前提",
                "conclusion": "结论",
                "explanation": "错误解释",
                "fix": "修复建议"
            }}
            """
            
            response = self.llm.invoke(prompt).content
            analysis = json.loads(response.strip())
            
            if analysis.get('has_error', False):
                return LogicError(
                    error_type=LogicErrorType.FALSE_DICHOTOMY,
                    severity=analysis.get('severity', 0.0),
                    premise=analysis.get('premise', ''),
                    conclusion=analysis.get('conclusion', ''),
                    explanation=analysis.get('explanation', ''),
                    suggested_fix=analysis.get('fix', '')
                )
                
        except Exception as e:
            self.logger.error(f"虚假二分法检测失败: {e}")
        
        return None


class ConsistencyChecker:
    """一致性检查器"""
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
    
    def check_goal_action_consistency(self, goals: List[str], actions: List[str]) -> Optional[ConsistencyIssue]:
        """检查目标-行动一致性"""
        try:
            prompt = f"""
            检查目标和行动之间的一致性：

            目标：{json.dumps(goals, ensure_ascii=False)}
            行动：{json.dumps(actions, ensure_ascii=False)}

            一致性评估要点：
            1. 行动是否有助于实现目标
            2. 是否存在冲突的行动
            3. 是否有遗漏的关键行动

            请分析并返回JSON格式：
            {{
                "has_inconsistency": true/false,
                "description": "问题描述",
                "conflicting_elements": ["冲突元素"],
                "impact": "影响评估",
                "resolution": "解决建议"
            }}
            """
            
            response = self.llm.invoke(prompt).content
            analysis = json.loads(response.strip())
            
            if analysis.get('has_inconsistency', False):
                return ConsistencyIssue(
                    issue_type="目标-行动不一致",
                    description=analysis.get('description', ''),
                    conflicting_elements=analysis.get('conflicting_elements', []),
                    impact_assessment=analysis.get('impact', ''),
                    resolution_suggestion=analysis.get('resolution', '')
                )
                
        except Exception as e:
            self.logger.error(f"目标-行动一致性检查失败: {e}")
        
        return None
    
    def check_value_consistency(self, decisions: List[str], stated_values: List[str]) -> Optional[ConsistencyIssue]:
        """检查价值一致性"""
        try:
            prompt = f"""
            检查决策和价值观之间的一致性：

            决策：{json.dumps(decisions, ensure_ascii=False)}
            价值观：{json.dumps(stated_values, ensure_ascii=False)}

            一致性评估要点：
            1. 决策是否体现了声明的价值观
            2. 是否存在价值冲突
            3. 是否有价值观被忽视

            请分析并返回JSON格式：
            {{
                "has_inconsistency": true/false,
                "description": "问题描述",
                "conflicting_elements": ["冲突元素"],
                "impact": "影响评估",
                "resolution": "解决建议"
            }}
            """
            
            response = self.llm.invoke(prompt).content
            analysis = json.loads(response.strip())
            
            if analysis.get('has_inconsistency', False):
                return ConsistencyIssue(
                    issue_type="价值一致性问题",
                    description=analysis.get('description', ''),
                    conflicting_elements=analysis.get('conflicting_elements', []),
                    impact_assessment=analysis.get('impact', ''),
                    resolution_suggestion=analysis.get('resolution', '')
                )
                
        except Exception as e:
            self.logger.error(f"价值一致性检查失败: {e}")
        
        return None


class MoralCompass:
    """道德指南针 - 提供伦理指导和价值约束"""
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        
        # 核心价值原则
        self.core_values = [
            "尊重人类尊严和权利",
            "促进人类福祉",
            "避免伤害",
            "公平和正义",
            "诚实和透明",
            "保护隐私",
            "负责任的AI使用"
        ]
    
    def evaluate_ethical_implications(self, decision_context: str, potential_actions: List[str]) -> Dict[str, Any]:
        """评估伦理影响"""
        try:
            prompt = f"""
            评估以下决策的伦理影响：

            决策背景：{decision_context}
            可能行动：{json.dumps(potential_actions, ensure_ascii=False)}

            核心价值原则：{json.dumps(self.core_values, ensure_ascii=False)}

            请从以下角度评估：
            1. 是否符合核心价值原则
            2. 潜在的伦理风险
            3. 对利益相关者的影响
            4. 长期道德后果

            返回JSON格式：
            {{
                "ethical_score": 0.0-1.0,
                "value_alignment": {{"principle": "score"}},
                "risks": ["风险列表"],
                "stakeholder_impact": "影响分析",
                "recommendations": ["建议列表"]
            }}
            """
            
            response = self.llm.invoke(prompt).content
            return json.loads(response.strip())
            
        except Exception as e:
            self.logger.error(f"伦理评估失败: {e}")
            return {
                "ethical_score": 0.5,
                "value_alignment": {},
                "risks": ["评估失败"],
                "stakeholder_impact": "无法评估",
                "recommendations": ["需要人工审核"]
            }
    
    def provide_moral_guidance(self, dilemma: str) -> str:
        """提供道德指导"""
        try:
            prompt = f"""
            针对以下道德困境提供指导：

            道德困境：{dilemma}

            核心价值原则：{json.dumps(self.core_values, ensure_ascii=False)}

            请提供：
            1. 困境分析
            2. 相关道德原则
            3. 可能的解决方案
            4. 推荐的行动方向

            以自然语言形式提供指导，重点关注如何在保持道德标准的同时找到平衡。
            """
            
            response = self.llm.invoke(prompt).content
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"道德指导生成失败: {e}")
            return "无法提供道德指导，建议寻求人工专家意见。"


class CognitiveMonitor:
    """认知监控器 - 实时监控认知过程"""
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        self.monitoring_active = False
        self.alert_thresholds = {
            'efficiency': 0.5,
            'error_rate': 0.3,
            'response_time': 30.0
        }
        self.alerts = []
    
    def start_monitoring(self):
        """启动监控"""
        self.monitoring_active = True
        self.logger.info("认知监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_active = False
        self.logger.info("认知监控已停止")
    
    def monitor_real_time(self, cognitive_data: Dict[str, Any]) -> Dict[str, Any]:
        """实时监控认知状态"""
        if not self.monitoring_active:
            return {'status': 'monitoring_disabled'}
        
        monitoring_result = {
            'timestamp': datetime.now(),
            'cognitive_status': self._assess_cognitive_status(cognitive_data),
            'alerts': [],
            'recommendations': []
        }
        
        # 检查警报条件
        if cognitive_data.get('efficiency', 1.0) < self.alert_thresholds['efficiency']:
            alert = {
                'type': 'efficiency_low',
                'message': f"认知效率过低: {cognitive_data.get('efficiency', 0):.2f}",
                'severity': 'medium'
            }
            self.alerts.append(alert)
            monitoring_result['alerts'].append(alert)
            monitoring_result['recommendations'].append("建议优化认知策略以提高效率")
        
        if cognitive_data.get('error_rate', 0.0) > self.alert_thresholds['error_rate']:
            alert = {
                'type': 'error_rate_high',
                'message': f"错误率过高: {cognitive_data.get('error_rate', 0):.2f}",
                'severity': 'high'
            }
            self.alerts.append(alert)
            monitoring_result['alerts'].append(alert)
            monitoring_result['recommendations'].append("建议检查认知过程，降低错误率")
        
        return monitoring_result
    
    def _assess_cognitive_status(self, cognitive_data: Dict[str, Any]) -> str:
        """评估认知状态"""
        efficiency = cognitive_data.get('efficiency', 1.0)
        error_rate = cognitive_data.get('error_rate', 0.0)
        
        if efficiency > 0.8 and error_rate < 0.1:
            return "excellent"
        elif efficiency > 0.6 and error_rate < 0.2:
            return "good"
        elif efficiency > 0.4 and error_rate < 0.3:
            return "fair"
        else:
            return "poor"


class StrategyOptimizer:
    """策略优化器 - 优化认知策略"""
    
    def __init__(self, llm: BaseChatModel, use_structured_output: bool = True):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        self.optimization_history = []
        self.strategy_bank = {}
        self.use_structured_output = use_structured_output and StructuredResponseOptimizer is not None
        
        # 初始化结构化响应优化器
        if self.use_structured_output:
            try:
                self.structured_optimizer = StructuredResponseOptimizer(llm, self.logger)
                self.logger.info("启用结构化JSON输出")
            except Exception as e:
                self.logger.warning(f"结构化输出初始化失败，降级到传统模式: {e}")
                self.use_structured_output = False
                self.structured_optimizer = None
        else:
            self.structured_optimizer = None
            self.logger.info("使用传统JSON解析模式")
    
    def _safe_json_parse(self, response: str, default_response: Dict[str, Any], method_name: str) -> Dict[str, Any]:
        """安全解析JSON响应"""
        try:
            if not response or not response.strip():
                self.logger.warning(f"{method_name} 收到空响应，使用默认响应")
                return default_response
            return json.loads(response.strip())
        except json.JSONDecodeError as json_error:
            self.logger.warning(f"{method_name} JSON解析失败，使用默认响应: {json_error}")
            self.logger.debug(f"原始响应长度: {len(response)}, 内容: {response}")
            return default_response
        except Exception as e:
            self.logger.error(f"{method_name} 响应处理失败: {e}")
            return default_response
    
    def _safe_json_dumps(self, data: Any) -> str:
        """安全序列化为JSON字符串，处理datetime等特殊对象"""
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        try:
            result = json.dumps(data, ensure_ascii=False, indent=2, default=json_serializer)
            # 限制输出长度以避免提示过长
            if len(result) > 2000:
                self.logger.debug(f"JSON序列化结果过长({len(result)}字符)，进行截断")
                return json.dumps(str(data)[:1000] + "...(截断)", ensure_ascii=False)
            return result
        except Exception as e:
            self.logger.warning(f"JSON序列化失败: {e}, 使用简化版本")
            return str(data)[:500]  # 限制长度
    
    def _invoke_llm_with_retry(self, prompt: str, max_retries: int = 2) -> str:
        """带重试机制的LLM调用"""
        for attempt in range(max_retries + 1):
            try:
                self.logger.debug(f"LLM调用尝试 {attempt + 1}/{max_retries + 1}, 提示长度: {len(prompt)}")
                response = self.llm.invoke(prompt)
                
                if hasattr(response, 'content'):
                    content = response.content
                else:
                    content = str(response)
                
                if content and content.strip():
                    self.logger.debug(f"LLM响应成功，长度: {len(content)}")
                    return content
                else:
                    self.logger.warning(f"LLM返回空响应，尝试 {attempt + 1}/{max_retries + 1}")
                    if attempt < max_retries:
                        continue
                    
            except Exception as e:
                self.logger.error(f"LLM调用失败，尝试 {attempt + 1}/{max_retries + 1}: {e}")
                if attempt < max_retries:
                    continue
                raise
        
        return ""  # 所有重试都失败
    
    def optimize_strategy(self, 
                         current_performance: Dict[str, float],
                         context: Dict[str, Any],
                         goals: List[str]) -> Dict[str, Any]:
        """优化认知策略"""
        try:
            # 尝试使用结构化输出
            if self.use_structured_output and self.structured_optimizer:
                try:
                    optimization_result = self.structured_optimizer.optimize_strategy_structured(
                        current_performance, context, goals
                    )
                    self.logger.debug("使用结构化JSON输出成功")
                except Exception as e:
                    self.logger.warning(f"结构化输出失败，降级到传统模式: {e}")
                    # 降级到传统模式
                    optimization_result = self._fallback_optimize_strategy(
                        current_performance, context, goals
                    )
            else:
                # 传统模式
                optimization_result = self._fallback_optimize_strategy(
                    current_performance, context, goals
                )
            
            # 记录优化历史
            optimization_record = {
                'timestamp': datetime.now(),
                'performance': current_performance,
                'optimization': optimization_result
            }
            self.optimization_history.append(optimization_record)
            
            # 更新策略库
            for strategy in optimization_result.get('strategies', []):
                if strategy not in self.strategy_bank:
                    self.strategy_bank[strategy] = {
                        'usage_count': 0,
                        'success_rate': 0.0,
                        'contexts': []
                    }
                self.strategy_bank[strategy]['contexts'].append(context)
            
            return optimization_result
            
        except Exception as e:
            self.logger.error(f"策略优化失败: {e}")
            return {'error': str(e)}
    
    def get_best_strategy(self, context: Dict[str, Any]) -> str:
        """获取最佳策略"""
        best_strategy = None
        best_score = 0.0
        
        for strategy, data in self.strategy_bank.items():
            # 简化的策略匹配逻辑
            score = data['success_rate'] * (data['usage_count'] / (data['usage_count'] + 1))
            if score > best_score:
                best_score = score
                best_strategy = strategy
        
        return best_strategy or "default_strategy"
    
    def _fallback_optimize_strategy(self, 
                                   current_performance: Dict[str, float],
                                   context: Dict[str, Any],
                                   goals: List[str]) -> Dict[str, Any]:
        """传统模式的策略优化（作为结构化输出的备选）"""
        try:
            # 使用简化的提示词但增加JSON Schema约束
            performance_str = str(current_performance).replace('{', '').replace('}', '')[:100]
            context_str = str(context).replace('{', '').replace('}', '')[:100]
            goals_str = str(goals)[:100]
            
            prompt = f"""请优化策略。

性能: {performance_str}
上下文: {context_str}
目标: {goals_str}

必须返回严格遵循JSON格式（不能有额外文本）：
{{
    "analysis": "对当前策略的分析(字符串)",
    "strategies": ["策略1", "策略2"],
    "priority": "high|medium|low",
    "confidence": 0.8
}}

JSON数据类型要求：
- analysis: string
- strategies: array of strings (1-5个元素)
- priority: 只能是 "high", "medium", 或 "low"
- confidence: number (0.0-1.0)。"""
            
            response = self._invoke_llm_with_retry(prompt)
            
            # 使用安全JSON解析，匹配简化响应格式
            default_response = {
                "analysis": "基础策略分析",
                "strategies": ["保持当前策略", "渐进改进"],
                "priority": "medium",
                "confidence": 0.7
            }
            
            return self._safe_json_parse(response, default_response, "策略优化")
            
        except Exception as e:
            self.logger.error(f"传统策略优化失败: {e}")
            return {
                "analysis": "系统错误，使用默认策略",
                "strategies": ["保持稳定", "监控系统"],
                "priority": "medium",
                "confidence": 0.5
            }


class ReflectionEngine:
    """反思引擎 - 认知反思和学习"""
    
    def __init__(self, llm: BaseChatModel, use_structured_output: bool = True):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        self.reflection_history = []
        self.learning_insights = []
        self.use_structured_output = use_structured_output and StructuredResponseOptimizer is not None
        
        # 初始化结构化响应优化器
        if self.use_structured_output:
            try:
                self.structured_optimizer = StructuredResponseOptimizer(llm, self.logger)
                self.logger.info("ReflectionEngine启用结构化JSON输出")
            except Exception as e:
                self.logger.warning(f"ReflectionEngine结构化输出初始化失败: {e}")
                self.use_structured_output = False
                self.structured_optimizer = None
        else:
            self.structured_optimizer = None
            self.logger.info("ReflectionEngine使用传统JSON解析模式")
    
    def _safe_json_parse(self, response: str, default_response: Dict[str, Any], method_name: str) -> Dict[str, Any]:
        """安全解析JSON响应"""
        try:
            if not response or not response.strip():
                self.logger.warning(f"{method_name} 收到空响应，使用默认响应")
                return default_response
            return json.loads(response.strip())
        except json.JSONDecodeError as json_error:
            self.logger.warning(f"{method_name} JSON解析失败，使用默认响应: {json_error}")
            self.logger.debug(f"原始响应长度: {len(response)}, 内容: {response}")
            return default_response
        except Exception as e:
            self.logger.error(f"{method_name} 响应处理失败: {e}")
            return default_response
    
    def _safe_json_dumps(self, data: Any) -> str:
        """安全序列化为JSON字符串，处理datetime等特殊对象"""
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        try:
            result = json.dumps(data, ensure_ascii=False, indent=2, default=json_serializer)
            # 限制输出长度以避免提示过长
            if len(result) > 2000:
                self.logger.debug(f"JSON序列化结果过长({len(result)}字符)，进行截断")
                return json.dumps(str(data)[:1000] + "...(截断)", ensure_ascii=False)
            return result
        except Exception as e:
            self.logger.warning(f"JSON序列化失败: {e}, 使用简化版本")
            return str(data)[:500]  # 限制长度
    
    def _invoke_llm_with_retry(self, prompt: str, max_retries: int = 2) -> str:
        """带重试机制的LLM调用"""
        for attempt in range(max_retries + 1):
            try:
                self.logger.debug(f"LLM调用尝试 {attempt + 1}/{max_retries + 1}, 提示长度: {len(prompt)}")
                response = self.llm.invoke(prompt)
                
                if hasattr(response, 'content'):
                    content = response.content
                else:
                    content = str(response)
                
                if content and content.strip():
                    self.logger.debug(f"LLM响应成功，长度: {len(content)}")
                    return content
                else:
                    self.logger.warning(f"LLM返回空响应，尝试 {attempt + 1}/{max_retries + 1}")
                    if attempt < max_retries:
                        continue
                    
            except Exception as e:
                self.logger.error(f"LLM调用失败，尝试 {attempt + 1}/{max_retries + 1}: {e}")
                if attempt < max_retries:
                    continue
                raise
        
        return ""  # 所有重试都失败
    
    def reflect_on_experience(self, 
                            experience_data: Dict[str, Any],
                            outcome: Dict[str, Any]) -> Dict[str, Any]:
        """对经验进行反思"""
        try:
            # 尝试使用结构化输出
            if self.use_structured_output and self.structured_optimizer:
                try:
                    reflection_result = self.structured_optimizer.reflect_structured(
                        experience_data, outcome
                    )
                    self.logger.debug("反思分析使用结构化JSON输出成功")
                except Exception as e:
                    self.logger.warning(f"反思分析结构化输出失败，降级到传统模式: {e}")
                    # 降级到传统模式
                    reflection_result = self._fallback_reflect_on_experience(experience_data, outcome)
            else:
                # 传统模式
                reflection_result = self._fallback_reflect_on_experience(experience_data, outcome)
            
            # 记录反思历史
            reflection_record = {
                'timestamp': datetime.now(),
                'experience': experience_data,
                'outcome': outcome,
                'reflection': reflection_result
            }
            self.reflection_history.append(reflection_record)
            
            # 提取学习洞察
            for lesson in reflection_result.get('lessons_learned', []):
                if lesson not in self.learning_insights:
                    self.learning_insights.append(lesson)
            
            return reflection_result
            
        except Exception as e:
            self.logger.error(f"反思失败: {e}")
            return {'error': str(e)}
    
    def _fallback_reflect_on_experience(self, 
                                       experience_data: Dict[str, Any],
                                       outcome: Dict[str, Any]) -> Dict[str, Any]:
        """传统模式的经验反思（作为结构化输出的备选）"""
        try:
            prompt = f"""对以下认知经验进行反思。

经验: {self._safe_json_dumps(experience_data)}
结果: {self._safe_json_dumps(outcome)}

必须返回严格遵循JSON格式（不能有额外文本）：
{{
    "lessons": ["经验1", "经验2"],
    "suggestions": ["建议1", "建议2"],
    "quality": 0.8,
    "insights": "关键洞察"
}}

JSON数据类型要求：
- lessons: array of strings (1-5个元素)
- suggestions: array of strings (1-5个元素)
- quality: number (0.0-1.0)
- insights: string。"""
            
            response = self._invoke_llm_with_retry(prompt)
            
            # 使用安全JSON解析
            default_response = {
                "lessons": ["经验积累很重要", "需要持续改进"],
                "suggestions": ["加强监控", "优化流程"],
                "quality": 0.6,
                "insights": "由于系统错误，反思不完整"
            }
            
            return self._safe_json_parse(response, default_response, "反思分析")
            
        except Exception as e:
            self.logger.error(f"传统反思分析失败: {e}")
            return {
                "lessons": ["系统错误中的经验"],
                "suggestions": ["检查系统状态"],
                "quality": 0.3,
                "insights": "系统错误导致反思不可用"
            }
    
    def generate_learning_summary(self) -> Dict[str, Any]:
        """生成学习总结"""
        if not self.reflection_history:
            return {'message': 'no_reflection_data'}
        
        try:
            recent_reflections = self.reflection_history[-10:]
            
            prompt = f"""
            基于最近的反思历史，生成学习总结：
            
            反思历史：{self._safe_json_dumps([r['reflection'] for r in recent_reflections])}
            
            请总结：
            1. 主要的学习模式
            2. 重复出现的问题
            3. 成功的认知策略
            4. 需要持续改进的领域
            
            返回JSON格式：
            {{
                "learning_patterns": ["模式1", "模式2"],
                "recurring_issues": ["问题1", "问题2"],
                "successful_strategies": ["策略1", "策略2"],
                "improvement_areas": ["领域1", "领域2"],
                "overall_progress": "进步评估"
            }}
            """
            
            response = self.llm.invoke(prompt).content
            
            # 使用安全JSON解析
            default_response = {
                "learning_patterns": ["经验积累", "错误纠正", "策略优化"],
                "recurring_issues": ["响应格式问题", "JSON解析错误"],
                "successful_strategies": ["分步骤处理", "错误后恢复"],
                "improvement_areas": ["提示词优化", "响应格式稳定性"],
                "overall_progress": "稳步改进中，需要关注响应格式稳定性"
            }
            return self._safe_json_parse(response, default_response, "学习总结")
            
        except Exception as e:
            self.logger.error(f"学习总结生成失败: {e}")
            return {'error': str(e)}


class UltraThinkEngine:
    """UltraThink元认知引擎 - 元认知层的核心认知能力"""
    
    def __init__(self, llm: BaseChatModel, use_structured_output: bool = True):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        self.use_structured_output = use_structured_output and StructuredResponseOptimizer is not None
        
        # 初始化结构化响应优化器
        if self.use_structured_output:
            try:
                self.structured_optimizer = StructuredResponseOptimizer(llm, self.logger)
                self.logger.info("UltraThink启用结构化JSON输出")
            except Exception as e:
                self.logger.warning(f"UltraThink结构化输出初始化失败，降级到传统模式: {e}")
                self.use_structured_output = False
                self.structured_optimizer = None
        else:
            self.structured_optimizer = None
            self.logger.info("UltraThink使用传统JSON解析模式")
        
        # 元认知状态
        self.meta_cognitive_state = {
            'current_strategy': None,
            'cognitive_load': 0.0,
            'efficiency_score': 1.0,
            'last_optimization': None
        }
        
        # 认知监控历史
        self.monitoring_history = []
        self.strategy_performance = {}
    
    def _safe_json_parse(self, response: str, default_response: Dict[str, Any], method_name: str) -> Dict[str, Any]:
        """
        安全解析JSON响应，如果失败则返回默认响应
        
        Args:
            response: LLM的原始响应
            default_response: 解析失败时的默认响应
            method_name: 调用方法名（用于日志）
            
        Returns:
            解析后的字典或默认响应
        """
        try:
            if not response or not response.strip():
                self.logger.warning(f"{method_name} 收到空响应，使用默认响应")
                return default_response
            return json.loads(response.strip())
        except json.JSONDecodeError as json_error:
            self.logger.warning(f"{method_name} JSON解析失败，使用默认响应: {json_error}")
            self.logger.debug(f"原始响应长度: {len(response)}, 内容: {response}")
            return default_response
        except Exception as e:
            self.logger.error(f"{method_name} 响应处理失败: {e}")
            return default_response
    
    def _safe_json_dumps(self, data: Any) -> str:
        """安全序列化为JSON字符串，处理datetime等特殊对象"""
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        try:
            result = json.dumps(data, ensure_ascii=False, indent=2, default=json_serializer)
            # 限制输出长度以避免提示过长
            if len(result) > 2000:
                self.logger.debug(f"JSON序列化结果过长({len(result)}字符)，进行截断")
                return json.dumps(str(data)[:1000] + "...(截断)", ensure_ascii=False)
            return result
        except Exception as e:
            self.logger.warning(f"JSON序列化失败: {e}, 使用简化版本")
            return str(data)[:500]  # 限制长度
    
    def _invoke_llm_with_retry(self, prompt: str, max_retries: int = 2) -> str:
        """带重试机制的LLM调用"""
        for attempt in range(max_retries + 1):
            try:
                self.logger.debug(f"LLM调用尝试 {attempt + 1}/{max_retries + 1}, 提示长度: {len(prompt)}")
                response = self.llm.invoke(prompt)
                
                if hasattr(response, 'content'):
                    content = response.content
                else:
                    content = str(response)
                
                if content and content.strip():
                    self.logger.debug(f"LLM响应成功，长度: {len(content)}")
                    return content
                else:
                    self.logger.warning(f"LLM返回空响应，尝试 {attempt + 1}/{max_retries + 1}")
                    if attempt < max_retries:
                        continue
                    
            except Exception as e:
                self.logger.error(f"LLM调用失败，尝试 {attempt + 1}/{max_retries + 1}: {e}")
                if attempt < max_retries:
                    continue
                raise
        
        return ""  # 所有重试都失败
        
    def monitor_cognitive_process(self, 
                                process_data: Dict[str, Any], 
                                performance_metrics: Dict[str, float]) -> Dict[str, Any]:
        """监控认知过程"""
        try:
            monitoring_result = {
                'timestamp': datetime.now(),
                'cognitive_efficiency': self._assess_cognitive_efficiency(process_data, performance_metrics),
                'resource_utilization': self._assess_resource_utilization(process_data),
                'strategy_effectiveness': self._assess_strategy_effectiveness(process_data),
                'anomaly_detected': self._detect_cognitive_anomalies(process_data),
                'recommendations': []
            }
            
            # 生成改进建议
            if monitoring_result['cognitive_efficiency'] < 0.7:
                monitoring_result['recommendations'].append("建议优化认知策略以提高效率")
            
            if monitoring_result['anomaly_detected']:
                monitoring_result['recommendations'].append("检测到认知异常，建议深入分析")
            
            self.monitoring_history.append(monitoring_result)
            return monitoring_result
            
        except Exception as e:
            self.logger.error(f"认知监控失败: {e}")
            return {'error': str(e)}
    
    def regulate_cognitive_strategy(self, 
                                  current_context: Dict[str, Any], 
                                  target_goals: List[str]) -> Dict[str, Any]:
        """调节认知策略"""
        try:
            # 尝试使用结构化输出
            if self.use_structured_output and self.structured_optimizer:
                try:
                    regulation_result = self.structured_optimizer.regulate_strategy_structured(
                        current_context, target_goals
                    )
                    self.logger.debug("策略调节使用结构化JSON输出成功")
                except Exception as e:
                    self.logger.warning(f"策略调节结构化输出失败，降级到传统模式: {e}")
                    # 降级到传统模式
                    regulation_result = self._fallback_regulate_strategy(current_context, target_goals)
            else:
                # 传统模式
                regulation_result = self._fallback_regulate_strategy(current_context, target_goals)
            
            # 更新元认知状态
            if regulation_result.get('adjustment_needed', False):
                self.meta_cognitive_state['current_strategy'] = regulation_result.get('recommended_strategy')
                self.meta_cognitive_state['last_optimization'] = datetime.now()
            
            return regulation_result
            
        except Exception as e:
            self.logger.error(f"策略调节失败: {e}")
            return {'error': str(e)}
    
    def _fallback_regulate_strategy(self, 
                                   current_context: Dict[str, Any], 
                                   target_goals: List[str]) -> Dict[str, Any]:
        """传统模式的策略调节（作为结构化输出的备选）"""
        try:
            # 使用简化提示词但增加JSON Schema约束
            context_str = str(current_context)[:100]
            goals_str = str(target_goals)[:100]
            
            prompt = f"""请评估策略。

上下文: {context_str}
目标: {goals_str}

必须返回严格遵循JSON格式（不能有额外文本）：
{{
    "assessment": "对当前策略的评估(字符串)",
    "adjustment_needed": false,
    "recommended_strategy": "推荐的策略(字符串)",
    "confidence": 0.7
}}

JSON数据类型要求：
- assessment: string
- adjustment_needed: boolean (true 或 false)
- recommended_strategy: string
- confidence: number (0.0-1.0)。"""
            
            response = self._invoke_llm_with_retry(prompt)
            
            # 使用安全JSON解析，匹配简化响应格式
            default_response = {
                "assessment": "策略基本适用",
                "adjustment_needed": False,
                "recommended_strategy": "继续当前策略",
                "confidence": 0.6
            }
            
            return self._safe_json_parse(response, default_response, "策略调节")
            
        except Exception as e:
            self.logger.error(f"传统策略调节失败: {e}")
            return {
                "assessment": "系统错误，策略评估不可用",
                "adjustment_needed": False,
                "recommended_strategy": "继续使用当前策略",
                "confidence": 0.5
            }
    
    def meta_learn_from_experience(self, experience_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从经验中进行元学习"""
        try:
            # 分析经验模式
            successful_patterns = []
            failure_patterns = []
            
            for experience in experience_data:
                if experience.get('success', False):
                    successful_patterns.append(experience)
                else:
                    failure_patterns.append(experience)
            
            prompt = f"""
            分析以下认知经验，提取可学习的模式：
            
            成功案例：{self._safe_json_dumps(successful_patterns)}
            失败案例：{self._safe_json_dumps(failure_patterns)}
            
            请提取：
            1. 成功模式的共同特征
            2. 失败的主要原因
            3. 可复用的认知策略
            4. 需要避免的认知陷阱
            
            返回JSON格式：
            {{
                "success_patterns": ["模式1", "模式2"],
                "failure_causes": ["原因1", "原因2"],
                "reusable_strategies": ["策略1", "策略2"],
                "cognitive_traps": ["陷阱1", "陷阱2"],
                "learning_insights": "学习洞察"
            }}
            """
            
            response = self.llm.invoke(prompt).content
            
            # 使用安全JSON解析
            default_response = {
                "success_patterns": ["系统性分析", "循序渐进"],
                "failure_causes": ["信息不足", "时间压力"],
                "reusable_strategies": ["多角度验证", "分步骤执行"],
                "cognitive_traps": ["过度自信", "确认偏差"],
                "learning_insights": "元学习过程中LLM响应格式异常，采用保守策略"
            }
            learning_result = self._safe_json_parse(response, default_response, "元学习")
            
            # 更新策略性能记录
            for pattern in learning_result.get('success_patterns', []):
                if pattern not in self.strategy_performance:
                    self.strategy_performance[pattern] = {'success_count': 0, 'total_count': 0}
                self.strategy_performance[pattern]['success_count'] += 1
                self.strategy_performance[pattern]['total_count'] += 1
            
            return learning_result
            
        except Exception as e:
            self.logger.error(f"元学习失败: {e}")
            return {'error': str(e)}
    
    def _assess_cognitive_efficiency(self, process_data: Dict[str, Any], metrics: Dict[str, float]) -> float:
        """评估认知效率"""
        try:
            # 基于多个指标计算综合效率分数
            execution_time = metrics.get('execution_time', 0.0)
            accuracy = metrics.get('accuracy', 1.0)
            resource_usage = metrics.get('resource_usage', 0.5)
            
            # 简化的效率计算公式
            if execution_time > 0:
                time_efficiency = min(1.0, 10.0 / execution_time)  # 10秒作为基准
            else:
                time_efficiency = 1.0
            
            efficiency = (time_efficiency * 0.4 + accuracy * 0.4 + (1 - resource_usage) * 0.2)
            return max(0.0, min(1.0, efficiency))
            
        except Exception:
            return 0.5  # 默认中等效率
    
    def _assess_resource_utilization(self, process_data: Dict[str, Any]) -> float:
        """评估资源利用率"""
        try:
            # 简化的资源利用率评估
            memory_usage = process_data.get('memory_usage', 0.5)
            cpu_usage = process_data.get('cpu_usage', 0.5)
            token_usage = process_data.get('token_usage', 0.5)
            
            return (memory_usage + cpu_usage + token_usage) / 3.0
        except Exception:
            return 0.5
    
    def _assess_strategy_effectiveness(self, process_data: Dict[str, Any]) -> float:
        """评估策略有效性"""
        try:
            strategy = process_data.get('strategy', 'default')
            if strategy in self.strategy_performance:
                perf = self.strategy_performance[strategy]
                return perf['success_count'] / max(1, perf['total_count'])
            return 0.5  # 未知策略的默认值
        except Exception:
            return 0.5
    
    def _detect_cognitive_anomalies(self, process_data: Dict[str, Any]) -> bool:
        """检测认知异常"""
        try:
            # 检查是否存在异常模式
            execution_time = process_data.get('execution_time', 0.0)
            error_rate = process_data.get('error_rate', 0.0)
            
            # 简单的异常检测规则
            if execution_time > 30.0:  # 执行时间过长
                return True
            if error_rate > 0.3:  # 错误率过高
                return True
                
            return False
        except Exception:
            return False


class MetaCognitiveAgent(AgentBase):
    """
    元认知智能体 - 元认知监督层
    
    作为四层认知架构的最高层，元认知层负责：
    1. 认知错误识别和诊断
    2. 逻辑验证和偏差检测
    3. 道德引导和价值约束
    4. 元认知监督和策略优化
    """
    
    def __init__(self, 
                 llm: BaseChatModel,
                 enable_bias_detection: bool = True,
                 enable_logic_validation: bool = True,
                 enable_consistency_check: bool = True,
                 enable_moral_guidance: bool = True,
                 enable_ultra_think: bool = True,
                 use_structured_output: bool = True,
                 system_message: Optional[str] = None):
        """
        初始化元认知智能体
        
        Args:
            llm: 语言模型
            enable_bias_detection: 是否启用偏差检测
            enable_logic_validation: 是否启用逻辑验证
            enable_consistency_check: 是否启用一致性检查
            enable_moral_guidance: 是否启用道德指导
            enable_ultra_think: 是否启用UltraThink元认知引擎
            use_structured_output: 是否使用结构化JSON输出
            system_message: 自定义系统消息
        """
        default_system = """你是具身认知工作流系统中的元认知智能体，负责元认知监督和认知质量控制。

你的核心使命：
1. 识别和纠正认知偏差（确认偏差、锚定效应等）
2. 检测逻辑错误和推理缺陷
3. 验证决策的一致性和价值对齐
4. 提供道德指导和伦理约束
5. 监督整个认知过程的质量

工作原则：
- 以提升认知质量为目标
- 保持客观和理性的监督态度
- 及时发现和纠正认知错误
- 确保决策符合道德标准
- 促进认知系统的持续改进

你的角色是认知系统的"内在监督者"，帮助其他认知层保持理性、客观和道德。"""
        
        super().__init__(llm, system_message or default_system)
        self.name = "元认知智能体"
        self.use_structured_output = use_structured_output
        
        # 初始化组件
        self.bias_detector = CognitiveBiasDetector(llm) if enable_bias_detection else None
        self.logic_identifier = LogicErrorIdentifier(llm) if enable_logic_validation else None
        self.consistency_checker = ConsistencyChecker(llm) if enable_consistency_check else None
        self.moral_compass = MoralCompass(llm) if enable_moral_guidance else None
        self.ultra_think = UltraThinkEngine(llm, use_structured_output) if enable_ultra_think else None
        
        # 初始化监控和优化组件（传递结构化输出配置）
        self.cognitive_monitor = CognitiveMonitor(llm)
        self.strategy_optimizer = StrategyOptimizer(llm, use_structured_output)
        self.reflection_engine = ReflectionEngine(llm, use_structured_output)
        
        # 认知监督历史
        self.supervision_history = []
        self.detected_biases = []
        self.detected_logic_errors = []
        self.consistency_issues = []
        
        # 性能指标
        self.supervision_metrics = {
            'total_supervisions': 0,
            'biases_detected': 0,
            'logic_errors_found': 0,
            'consistency_issues': 0,
            'moral_interventions': 0
        }
        
        self.logger = logging.getLogger(__name__)
    
    def _safe_json_parse(self, response: str, default_response: Dict[str, Any], method_name: str) -> Dict[str, Any]:
        """
        安全解析JSON响应，如果失败则返回默认响应
        
        Args:
            response: LLM的原始响应
            default_response: 解析失败时的默认响应
            method_name: 调用方法名（用于日志）
            
        Returns:
            解析后的字典或默认响应
        """
        try:
            if not response or not response.strip():
                self.logger.warning(f"{method_name} 收到空响应，使用默认响应")
                return default_response
            return json.loads(response.strip())
        except json.JSONDecodeError as json_error:
            self.logger.warning(f"{method_name} JSON解析失败，使用默认响应: {json_error}")
            self.logger.debug(f"原始响应长度: {len(response)}, 内容: {response}")
            return default_response
        except Exception as e:
            self.logger.error(f"{method_name} 响应处理失败: {e}")
            return default_response
    
    def supervise_cognitive_process(self, 
                                  reasoning_text: str, 
                                  context: Dict[str, Any],
                                  goals: Optional[List[str]] = None,
                                  actions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        监督认知过程
        
        Args:
            reasoning_text: 推理文本
            context: 上下文信息
            goals: 目标列表
            actions: 行动列表
            
        Returns:
            Dict: 监督结果
        """
        supervision_result = {
            'timestamp': datetime.now(),
            'biases_detected': [],
            'logic_errors': [],
            'consistency_issues': [],
            'ethical_assessment': None,
            'overall_health_score': 1.0,
            'recommendations': []
        }
        
        try:
            # 1. 偏差检测
            if self.bias_detector:
                # 检测确认偏差
                confirmation_bias = self.bias_detector.detect_confirmation_bias(reasoning_text, context)
                if confirmation_bias:
                    supervision_result['biases_detected'].append(confirmation_bias)
                    self.detected_biases.append(confirmation_bias)
                
                # 检测锚定偏差
                if context.get('initial_info'):
                    anchoring_bias = self.bias_detector.detect_anchoring_bias(
                        reasoning_text, context['initial_info']
                    )
                    if anchoring_bias:
                        supervision_result['biases_detected'].append(anchoring_bias)
                        self.detected_biases.append(anchoring_bias)
            
            # 2. 逻辑验证
            if self.logic_identifier:
                # 检测循环论证
                circular_reasoning = self.logic_identifier.identify_circular_reasoning(reasoning_text)
                if circular_reasoning:
                    supervision_result['logic_errors'].append(circular_reasoning)
                    self.detected_logic_errors.append(circular_reasoning)
                
                # 检测虚假二分法
                false_dichotomy = self.logic_identifier.identify_false_dichotomy(reasoning_text)
                if false_dichotomy:
                    supervision_result['logic_errors'].append(false_dichotomy)
                    self.detected_logic_errors.append(false_dichotomy)
            
            # 3. 一致性检查
            if self.consistency_checker and goals and actions:
                goal_action_issue = self.consistency_checker.check_goal_action_consistency(goals, actions)
                if goal_action_issue:
                    supervision_result['consistency_issues'].append(goal_action_issue)
                    self.consistency_issues.append(goal_action_issue)
            
            # 4. 道德评估
            if self.moral_compass and actions:
                ethical_assessment = self.moral_compass.evaluate_ethical_implications(
                    reasoning_text, actions
                )
                supervision_result['ethical_assessment'] = ethical_assessment
            
            # 5. 计算整体健康分数
            health_score = self._calculate_cognitive_health_score(supervision_result)
            supervision_result['overall_health_score'] = health_score
            
            # 6. 生成建议
            recommendations = self._generate_recommendations(supervision_result)
            supervision_result['recommendations'] = recommendations
            
            # 更新指标
            self._update_supervision_metrics(supervision_result)
            
            # 记录监督历史
            self.supervision_history.append(supervision_result)
            
        except Exception as e:
            self.logger.error(f"认知监督过程失败: {e}")
            supervision_result['error'] = str(e)
        
        return supervision_result
    
    def assess_cognitive_health(self) -> CognitiveHealthAssessment:
        """评估整体认知健康状况"""
        # 计算各项指标
        total_issues = (len(self.detected_biases) + 
                       len(self.detected_logic_errors) + 
                       len(self.consistency_issues))
        
        # 计算健康分数
        if total_issues == 0:
            score = 1.0
            status = CognitiveHealthStatus.EXCELLENT
        elif total_issues <= 2:
            score = 0.8
            status = CognitiveHealthStatus.GOOD
        elif total_issues <= 5:
            score = 0.6
            status = CognitiveHealthStatus.FAIR
        elif total_issues <= 10:
            score = 0.4
            status = CognitiveHealthStatus.POOR
        else:
            score = 0.2
            status = CognitiveHealthStatus.CRITICAL
        
        # 识别优势和劣势
        strengths = []
        weaknesses = []
        recommendations = []
        
        if len(self.detected_biases) == 0:
            strengths.append("偏差控制良好")
        else:
            weaknesses.append(f"检测到{len(self.detected_biases)}个认知偏差")
            recommendations.append("加强批判性思维训练")
        
        if len(self.detected_logic_errors) == 0:
            strengths.append("逻辑推理清晰")
        else:
            weaknesses.append(f"发现{len(self.detected_logic_errors)}个逻辑错误")
            recommendations.append("重视逻辑验证步骤")
        
        if len(self.consistency_issues) == 0:
            strengths.append("决策一致性良好")
        else:
            weaknesses.append(f"存在{len(self.consistency_issues)}个一致性问题")
            recommendations.append("加强目标-行动对齐检查")
        
        return CognitiveHealthAssessment(
            overall_score=score,
            status=status,
            bias_count=len(self.detected_biases),
            logic_errors=len(self.detected_logic_errors),
            consistency_issues=len(self.consistency_issues),
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
    
    def provide_cognitive_correction(self, issue_type: str, specific_issue: Any) -> str:
        """提供认知纠正建议"""
        try:
            if issue_type == "bias":
                return f"认知偏差纠正：{specific_issue.suggested_correction}"
            elif issue_type == "logic_error":
                return f"逻辑错误修复：{specific_issue.suggested_fix}"
            elif issue_type == "consistency":
                return f"一致性改进：{specific_issue.resolution_suggestion}"
            else:
                return "建议进行全面的认知反思和检查。"
        except Exception as e:
            self.logger.error(f"认知纠正建议生成失败: {e}")
            return "无法生成具体建议，建议寻求专业指导。"
    
    def _calculate_cognitive_health_score(self, supervision_result: Dict[str, Any]) -> float:
        """计算认知健康分数"""
        base_score = 1.0
        
        # 偏差扣分
        bias_penalty = len(supervision_result['biases_detected']) * 0.1
        
        # 逻辑错误扣分
        logic_penalty = len(supervision_result['logic_errors']) * 0.15
        
        # 一致性问题扣分
        consistency_penalty = len(supervision_result['consistency_issues']) * 0.1
        
        # 道德问题扣分
        ethical_penalty = 0.0
        if supervision_result['ethical_assessment']:
            ethical_score = supervision_result['ethical_assessment'].get('ethical_score', 1.0)
            if ethical_score < 0.7:
                ethical_penalty = (0.7 - ethical_score) * 0.5
        
        final_score = max(0.0, base_score - bias_penalty - logic_penalty - consistency_penalty - ethical_penalty)
        return final_score
    
    def _generate_recommendations(self, supervision_result: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于检测到的问题生成建议
        if supervision_result['biases_detected']:
            recommendations.append("建议采用多角度分析方法，避免认知偏差")
        
        if supervision_result['logic_errors']:
            recommendations.append("建议加强逻辑推理验证，确保论证严谨")
        
        if supervision_result['consistency_issues']:
            recommendations.append("建议检查目标与行动的对齐性，保持决策一致")
        
        if supervision_result['ethical_assessment']:
            ethical_score = supervision_result['ethical_assessment'].get('ethical_score', 1.0)
            if ethical_score < 0.8:
                recommendations.append("建议重新评估决策的伦理影响")
        
        if supervision_result['overall_health_score'] < 0.7:
            recommendations.append("建议进行全面的认知反思和改进")
        
        return recommendations
    
    def _update_supervision_metrics(self, supervision_result: Dict[str, Any]):
        """更新监督指标"""
        self.supervision_metrics['total_supervisions'] += 1
        self.supervision_metrics['biases_detected'] += len(supervision_result['biases_detected'])
        self.supervision_metrics['logic_errors_found'] += len(supervision_result['logic_errors'])
        self.supervision_metrics['consistency_issues'] += len(supervision_result['consistency_issues'])
        
        if (supervision_result['ethical_assessment'] and 
            supervision_result['ethical_assessment'].get('ethical_score', 1.0) < 0.8):
            self.supervision_metrics['moral_interventions'] += 1
    
    def get_supervision_summary(self) -> Dict[str, Any]:
        """获取监督摘要"""
        return {
            'metrics': self.supervision_metrics,
            'recent_supervisions': len(self.supervision_history),
            'active_issues': {
                'biases': len(self.detected_biases),
                'logic_errors': len(self.detected_logic_errors),
                'consistency_issues': len(self.consistency_issues)
            },
            'cognitive_health': self.assess_cognitive_health()
        }
    
    def meta_cognitive_analysis(self, 
                               process_data: Dict[str, Any], 
                               performance_metrics: Dict[str, float] = None,
                               context: Dict[str, Any] = None,
                               goals: List[str] = None) -> Dict[str, Any]:
        """执行元认知分析"""
        if not self.ultra_think:
            return {'error': 'UltraThink引擎未启用'}
        
        try:
            meta_analysis = {
                'timestamp': datetime.now(),
                'monitoring_result': None,
                'strategy_regulation': None,
                'meta_learning': None
            }
            
            # 1. 认知监控
            if performance_metrics:
                monitoring_result = self.ultra_think.monitor_cognitive_process(
                    process_data, performance_metrics
                )
                meta_analysis['monitoring_result'] = monitoring_result
            
            # 2. 策略调节
            if context and goals:
                regulation_result = self.ultra_think.regulate_cognitive_strategy(
                    context, goals
                )
                meta_analysis['strategy_regulation'] = regulation_result
            
            # 3. 元学习（如果有足够的历史数据）
            if len(self.supervision_history) >= 3:
                recent_experiences = [
                    {
                        'success': result.get('overall_health_score', 0) > 0.7,
                        'strategy': result.get('strategy_used', 'unknown'),
                        'outcome': result.get('recommendations', [])
                    }
                    for result in self.supervision_history[-10:]
                ]
                learning_result = self.ultra_think.meta_learn_from_experience(recent_experiences)
                meta_analysis['meta_learning'] = learning_result
            
            return meta_analysis
            
        except Exception as e:
            self.logger.error(f"元认知分析失败: {e}")
            return {'error': str(e)}
    
    def optimize_cognitive_strategy(self, 
                                  current_performance: Dict[str, float],
                                  target_improvements: List[str]) -> Dict[str, Any]:
        """优化认知策略"""
        if not self.ultra_think:
            return {'error': 'UltraThink引擎未启用'}
        
        try:
            # 分析当前认知状态
            cognitive_state = {
                'performance_metrics': current_performance,
                'recent_supervision': self.supervision_history[-5:] if self.supervision_history else [],
                'improvement_targets': target_improvements
            }
            
            # 使用UltraThink进行策略调节
            optimization_result = self.ultra_think.regulate_cognitive_strategy(
                cognitive_state, target_improvements
            )
            
            # 记录优化历史
            self.supervision_metrics['optimization_count'] = self.supervision_metrics.get('optimization_count', 0) + 1
            
            return optimization_result
            
        except Exception as e:
            self.logger.error(f"认知策略优化失败: {e}")
            return {'error': str(e)}
    
    def start_cognitive_monitoring(self):
        """启动认知监控"""
        self.cognitive_monitor.start_monitoring()
        self.logger.info("元认知监控已启动")
    
    def stop_cognitive_monitoring(self):
        """停止认知监控"""
        self.cognitive_monitor.stop_monitoring()
        self.logger.info("元认知监控已停止")
    
    def comprehensive_cognitive_supervision(self, 
                                          cognitive_data: Dict[str, Any],
                                          context: Dict[str, Any] = None,
                                          goals: List[str] = None) -> Dict[str, Any]:
        """综合认知监督 - 整合所有监督能力"""
        supervision_result = {
            'timestamp': datetime.now(),
            'basic_supervision': None,
            'real_time_monitoring': None,
            'strategy_optimization': None,
            'meta_cognitive_analysis': None,
            'overall_assessment': None
        }
        
        try:
            # 1. 基础认知监督
            if 'reasoning_text' in cognitive_data:
                basic_result = self.supervise_cognitive_process(
                    cognitive_data['reasoning_text'],
                    context or {},
                    goals,
                    cognitive_data.get('actions', [])
                )
                supervision_result['basic_supervision'] = basic_result
            
            # 2. 实时监控
            monitoring_result = self.cognitive_monitor.monitor_real_time(cognitive_data)
            supervision_result['real_time_monitoring'] = monitoring_result
            
            # 3. 策略优化
            if context and goals:
                performance_metrics = {
                    'efficiency': cognitive_data.get('efficiency', 0.8),
                    'accuracy': cognitive_data.get('accuracy', 0.9),
                    'error_rate': cognitive_data.get('error_rate', 0.1)
                }
                optimization_result = self.strategy_optimizer.optimize_strategy(
                    performance_metrics, context, goals
                )
                supervision_result['strategy_optimization'] = optimization_result
            
            # 4. 元认知分析
            if self.ultra_think:
                meta_result = self.meta_cognitive_analysis(
                    cognitive_data,
                    cognitive_data.get('performance_metrics'),
                    context,
                    goals
                )
                supervision_result['meta_cognitive_analysis'] = meta_result
            
            # 5. 整体评估
            overall_assessment = self._generate_overall_assessment(supervision_result)
            supervision_result['overall_assessment'] = overall_assessment
            
            # 记录监督历史
            self.supervision_history.append(supervision_result)
            
            return supervision_result
            
        except Exception as e:
            self.logger.error(f"综合认知监督失败: {e}")
            supervision_result['error'] = str(e)
            return supervision_result
    
    def reflect_and_learn(self, experience_data: Dict[str, Any], outcome: Dict[str, Any]) -> Dict[str, Any]:
        """反思和学习"""
        try:
            # 使用反思引擎进行反思
            reflection_result = self.reflection_engine.reflect_on_experience(experience_data, outcome)
            
            # 更新监督指标
            self.supervision_metrics['reflection_count'] = self.supervision_metrics.get('reflection_count', 0) + 1
            
            return reflection_result
            
        except Exception as e:
            self.logger.error(f"反思学习失败: {e}")
            return {'error': str(e)}
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """获取学习总结"""
        return self.reflection_engine.generate_learning_summary()
    
    def get_meta_cognitive_state(self) -> Dict[str, Any]:
        """获取元认知状态"""
        state_info = {
            'cognitive_monitor': {
                'active': self.cognitive_monitor.monitoring_active,
                'alerts_count': len(self.cognitive_monitor.alerts),
                'recent_alerts': self.cognitive_monitor.alerts[-3:] if self.cognitive_monitor.alerts else []
            },
            'strategy_optimizer': {
                'optimization_history_count': len(self.strategy_optimizer.optimization_history),
                'strategy_bank_size': len(self.strategy_optimizer.strategy_bank),
                'available_strategies': list(self.strategy_optimizer.strategy_bank.keys())[:5]
            },
            'reflection_engine': {
                'reflection_count': len(self.reflection_engine.reflection_history),
                'learning_insights_count': len(self.reflection_engine.learning_insights),
                'recent_insights': self.reflection_engine.learning_insights[-3:] if self.reflection_engine.learning_insights else []
            }
        }
        
        if self.ultra_think:
            state_info['ultra_think'] = {
                'meta_cognitive_state': self.ultra_think.meta_cognitive_state,
                'monitoring_history_count': len(self.ultra_think.monitoring_history),
                'strategy_performance': self.ultra_think.strategy_performance
            }
        
        return state_info
    
    def _generate_overall_assessment(self, supervision_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成整体评估"""
        assessment = {
            'cognitive_health_level': 'good',
            'critical_issues': [],
            'priority_recommendations': [],
            'confidence_score': 0.8
        }
        
        # 基于各个监督结果生成整体评估
        if supervision_result.get('basic_supervision'):
            basic_score = supervision_result['basic_supervision'].get('overall_health_score', 0.8)
            if basic_score < 0.5:
                assessment['critical_issues'].append("基础认知质量较差")
                assessment['cognitive_health_level'] = 'poor'
        
        if supervision_result.get('real_time_monitoring'):
            alerts = supervision_result['real_time_monitoring'].get('alerts', [])
            if any(alert.get('severity') == 'high' for alert in alerts):
                assessment['critical_issues'].append("检测到高严重性认知警报")
        
        if supervision_result.get('strategy_optimization'):
            priority = supervision_result['strategy_optimization'].get('implementation_priority', 'low')
            if priority == 'high':
                assessment['priority_recommendations'].append("紧急需要策略优化")
        
        # 调整整体健康等级
        if len(assessment['critical_issues']) > 2:
            assessment['cognitive_health_level'] = 'critical'
        elif len(assessment['critical_issues']) > 0:
            assessment['cognitive_health_level'] = 'fair'
        
        return assessment
    
    def clear_supervision_history(self):
        """清除监督历史"""
        self.supervision_history.clear()
        self.detected_biases.clear()
        self.detected_logic_errors.clear()
        self.consistency_issues.clear()
        
        # 重置指标
        for key in self.supervision_metrics:
            self.supervision_metrics[key] = 0
        
        # 清除UltraThink历史
        if self.ultra_think:
            self.ultra_think.monitoring_history.clear()
            self.ultra_think.strategy_performance.clear()