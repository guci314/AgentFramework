#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多方案响应解析器 v2.0
支持符号主义、连接主义等多种解析方法的统一接口

Author: Claude
Date: 2024-06-21
"""

import re
import json
import logging
import time
import numpy as np
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, NamedTuple, Union
from dataclasses import dataclass
from datetime import datetime as dt

# 复用原有的数据结构
class ResponseQuality(Enum):
    """响应质量等级"""
    EXCELLENT = "excellent"    # 极佳
    GOOD = "good"             # 良好  
    ACCEPTABLE = "acceptable" # 可接受
    POOR = "poor"             # 较差
    INVALID = "invalid"       # 无效


class ParsedStateInfo(NamedTuple):
    """解析后的状态信息结构"""
    main_content: str                      # 主要状态内容
    confidence_score: float               # 置信度评分 (0.0-1.0)
    extracted_entities: Dict[str, str]    # 提取的实体信息
    sentiment: Optional[str] = None       # 情感分析结果
    intent: Optional[str] = None          # 意图识别结果
    quality_metrics: Dict[str, Any] = {}  # 质量指标


class ParserMethod(Enum):
    """解析方法枚举"""
    RULE = "rule"                    # 符号主义规则方法
    TRANSFORMER = "transformer"     # 本地Transformer模型
    DEEPSEEK = "deepseek"           # DeepSeek API
    EMBEDDING = "embedding"         # 轻量级嵌入模型


@dataclass
class ParserConfig:
    """解析器配置"""
    method: ParserMethod = ParserMethod.RULE
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 缓存时间(秒)
    fallback_chain: List[ParserMethod] = None
    confidence_threshold: float = 0.6
    max_retries: int = 3
    timeout: int = 30
    enable_sentiment_analysis: bool = True
    enable_intent_recognition: bool = True
    proxy: Optional[str] = None  # 代理服务器配置
    cache_dir: Optional[str] = None  # 模型缓存目录
    
    def __post_init__(self):
        if self.fallback_chain is None:
            self.fallback_chain = [ParserMethod.RULE]  # 默认降级到规则方法


class BaseResponseParser(ABC):
    """响应解析器基类"""
    
    def __init__(self, config: ParserConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._cache = {} if config.cache_enabled else None
        
    @abstractmethod
    def _parse_internal(self, response: str, context: Optional[Dict[str, Any]] = None) -> ParsedStateInfo:
        """内部解析实现"""
        pass
    
    def parse_response(self, response: str, context: Optional[Dict[str, Any]] = None) -> ParsedStateInfo:
        """解析响应的统一接口"""
        if not response or not response.strip():
            return self._create_empty_parsed_info("空响应")
        
        # 检查缓存
        cache_key = self._get_cache_key(response, context)
        if self._cache and cache_key in self._cache:
            cached_result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.config.cache_ttl:
                self.logger.debug(f"使用缓存结果: {cache_key[:50]}...")
                return cached_result
        
        try:
            result = self._parse_internal(response, context)
            
            # 缓存结果
            if self._cache:
                self._cache[cache_key] = (result, time.time())
            
            return result
            
        except Exception as e:
            self.logger.error(f"解析失败: {e}")
            return self._create_empty_parsed_info(f"解析异常: {str(e)}")
    
    def _get_cache_key(self, response: str, context: Optional[Dict[str, Any]] = None) -> str:
        """生成缓存键"""
        context_str = json.dumps(context, sort_keys=True) if context else ""
        return f"{hash(response)}_{hash(context_str)}"
    
    def _create_empty_parsed_info(self, reason: str) -> ParsedStateInfo:
        """创建空的解析信息"""
        return ParsedStateInfo(
            main_content=f"解析失败: {reason}",
            confidence_score=0.0,
            extracted_entities={"status_type": "error", "error_reason": reason},
            sentiment="negative",
            intent="signal_error",
            quality_metrics={"overall_quality": ResponseQuality.INVALID.value, "is_valid": False}
        )


class RuleBasedParser(BaseResponseParser):
    """基于规则的符号主义解析器"""
    
    def __init__(self, config: ParserConfig):
        super().__init__(config)
        
        # 预定义关键词集合
        self._success_keywords = {
            "成功", "完成", "实现", "创建", "建立", "生成", "构建", "达成", 
            "获得", "解决", "修复", "正常", "顺利", "有效", "可用"
        }
        
        self._error_keywords = {
            "错误", "失败", "异常", "故障", "问题", "无法", "不能", "中断",
            "崩溃", "超时", "拒绝", "丢失", "损坏", "无效", "不可用"
        }
        
        self._progress_keywords = {
            "正在", "开始", "进行", "处理", "执行", "运行", "加载", "准备",
            "初始化", "配置", "等待", "尝试", "检查", "验证"
        }
        
        # 情感关键词
        self._positive_sentiment_keywords = {
            "顺利", "流畅", "高效", "优秀", "稳定", "可靠", "满意", "理想"
        }
        
        self._negative_sentiment_keywords = {
            "困难", "复杂", "缓慢", "不稳定", "繁琐", "挫折", "障碍", "瓶颈"
        }
        
        # 意图关键词
        self._intent_patterns = {
            "request_action": ["需要", "请", "要求", "希望", "建议"],
            "report_status": ["当前", "目前", "现在", "状态", "情况"],
            "indicate_completion": ["完成", "结束", "完毕", "达成", "实现"],
            "signal_error": ["出现", "发生", "遇到", "错误", "问题", "异常"],
            "describe_progress": ["正在", "进行中", "开始", "继续", "处理"]
        }
    
    def _parse_internal(self, response: str, context: Optional[Dict[str, Any]] = None) -> ParsedStateInfo:
        """基于规则的内部解析实现"""
        # 预处理
        cleaned_content = self._preprocess_response(response)
        
        # 提取主要内容
        main_content = self._extract_main_content(cleaned_content)
        
        # 实体提取
        entities = self._extract_entities(cleaned_content, context)
        
        # 计算置信度
        confidence = self._calculate_confidence(cleaned_content, entities)
        
        # 情感分析
        sentiment = None
        if self.config.enable_sentiment_analysis:
            sentiment = self._analyze_sentiment(cleaned_content)
        
        # 意图识别
        intent = None  
        if self.config.enable_intent_recognition:
            intent = self._recognize_intent(cleaned_content)
        
        # 质量评估
        quality_metrics = self._assess_quality(cleaned_content, entities, confidence)
        
        return ParsedStateInfo(
            main_content=main_content,
            confidence_score=confidence,
            extracted_entities=entities,
            sentiment=sentiment,
            intent=intent,
            quality_metrics=quality_metrics
        )
    
    def _preprocess_response(self, response: str) -> str:
        """预处理响应文本"""
        # 移除多余空白字符
        cleaned = re.sub(r'\s+', ' ', response.strip())
        
        # 移除常见的格式化字符
        cleaned = re.sub(r'[*_`~]', '', cleaned)
        
        # 移除HTML标签（如果存在）
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        
        return cleaned
    
    def _extract_main_content(self, content: str) -> str:
        """提取主要状态内容"""
        # 如果内容很短，直接返回
        if len(content) <= 100:
            return content
        
        # 尝试提取第一个完整句子或段落
        sentences = re.split(r'[。！？.!?]\s*', content)
        if sentences:
            # 选择最有信息量的句子
            main_sentence = max(sentences, key=lambda s: len(s.strip()) if len(s.strip()) > 10 else 0)
            if main_sentence.strip():
                return main_sentence.strip()
        
        # 如果没有明显句子结构，返回前100个字符
        return content[:100] + "..." if len(content) > 100 else content
    
    def _extract_entities(self, content: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """提取关键实体信息"""
        entities = {}
        
        # 提取状态类型
        if any(keyword in content for keyword in self._success_keywords):
            entities["status_type"] = "success"
        elif any(keyword in content for keyword in self._error_keywords):
            entities["status_type"] = "error"  
        elif any(keyword in content for keyword in self._progress_keywords):
            entities["status_type"] = "progress"
        else:
            entities["status_type"] = "neutral"
        
        # 提取时间相关信息
        time_patterns = [
            r'(\d+)\s*分钟',
            r'(\d+)\s*秒',
            r'(\d+)\s*小时',
            r'(\d+)\s*天'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, content)
            if match:
                entities["time_reference"] = match.group(0)
                break
        
        # 提取数字信息
        numbers = re.findall(r'\d+', content)
        if numbers:
            entities["numeric_values"] = ",".join(numbers[:3])  # 最多保留3个数字
        
        # 从上下文中提取相关信息
        if context:
            if "step_name" in context:
                entities["related_step"] = str(context["step_name"])
            if "execution_success" in context:
                entities["execution_result"] = str(context["execution_success"])
        
        return entities
    
    def _calculate_confidence(self, content: str, entities: Dict[str, str]) -> float:
        """计算置信度评分"""
        confidence = 0.5  # 基础分数
        
        # 长度因子（合理长度加分）
        length = len(content)
        if 20 <= length <= 200:
            confidence += 0.2
        elif 10 <= length < 20 or 200 < length <= 300:
            confidence += 0.1
        elif length < 10:
            confidence -= 0.2
        
        # 实体提取质量
        entity_score = len(entities) * 0.05
        confidence += min(entity_score, 0.2)
        
        # 关键词匹配
        all_keywords = self._success_keywords | self._error_keywords | self._progress_keywords
        keyword_matches = sum(1 for keyword in all_keywords if keyword in content)
        keyword_score = keyword_matches * 0.03
        confidence += min(keyword_score, 0.15)
        
        # 句子结构完整性
        if re.search(r'[。！？.!?]', content):
            confidence += 0.1
        
        return min(max(confidence, 0.0), 1.0)
    
    def _analyze_sentiment(self, content: str) -> Optional[str]:
        """分析情感倾向"""
        positive_count = sum(1 for keyword in self._positive_sentiment_keywords if keyword in content)
        negative_count = sum(1 for keyword in self._negative_sentiment_keywords if keyword in content)
        
        # 也考虑成功/错误关键词的情感倾向
        success_count = sum(1 for keyword in self._success_keywords if keyword in content)
        error_count = sum(1 for keyword in self._error_keywords if keyword in content)
        
        total_positive = positive_count + success_count
        total_negative = negative_count + error_count
        
        if total_positive > total_negative:
            return "positive"
        elif total_negative > total_positive:
            return "negative"
        else:
            return "neutral"
    
    def _recognize_intent(self, content: str) -> Optional[str]:
        """识别意图"""
        intent_scores = {}
        
        for intent_type, keywords in self._intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in content)
            if score > 0:
                intent_scores[intent_type] = score
        
        if intent_scores:
            # 返回得分最高的意图
            return max(intent_scores, key=intent_scores.get)
        
        return None
    
    def _assess_quality(self, content: str, entities: Dict[str, str], confidence: float) -> Dict[str, Any]:
        """评估响应质量"""
        metrics = {
            "content_length": len(content),
            "entity_count": len(entities),
            "confidence_score": confidence
        }
        
        # 确定整体质量等级
        if confidence >= 0.8 and len(content) >= 20 and len(entities) >= 2:
            overall_quality = ResponseQuality.EXCELLENT
        elif confidence >= 0.6 and len(content) >= 15:
            overall_quality = ResponseQuality.GOOD
        elif confidence >= 0.4 and len(content) >= 10:
            overall_quality = ResponseQuality.ACCEPTABLE
        elif confidence >= 0.2:
            overall_quality = ResponseQuality.POOR
        else:
            overall_quality = ResponseQuality.INVALID
        
        metrics["overall_quality"] = overall_quality.value
        metrics["is_valid"] = overall_quality != ResponseQuality.INVALID
        
        return metrics


class TransformerParser(BaseResponseParser):
    """基于Transformer的本地模型解析器"""
    
    def __init__(self, config: ParserConfig):
        super().__init__(config)
        self._model = None
        self._tokenizer = None
        self._initialized = False
        
        # 延迟初始化，避免导入错误
        self._init_model()
    
    def _init_model(self):
        """初始化模型"""
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            import torch
            import os
            
            # 设置代理环境变量（如果需要）
            if not os.environ.get('http_proxy') and not os.environ.get('https_proxy'):
                # 检查是否有代理配置
                proxy_config = getattr(self.config, 'proxy', None)
                if proxy_config:
                    os.environ['http_proxy'] = proxy_config
                    os.environ['https_proxy'] = proxy_config
                    self.logger.info(f"设置代理: {proxy_config}")
                else:
                    # 设置默认代理（如果可用）
                    default_proxy = 'http://127.0.0.1:7890'
                    try:
                        import requests
                        # 测试代理是否可用
                        response = requests.get('http://www.google.com', 
                                              proxies={'http': default_proxy, 'https': default_proxy}, 
                                              timeout=5)
                        if response.status_code == 200:
                            os.environ['http_proxy'] = default_proxy
                            os.environ['https_proxy'] = default_proxy
                            self.logger.info(f"自动设置代理: {default_proxy}")
                    except:
                        self.logger.warning("未检测到可用代理，直连下载模型")
            
            model_name = self.config.model_name or 'hfl/chinese-bert-wwm-ext'
            
            self.logger.info(f"正在加载Transformer模型: {model_name}")
            
            # 设置缓存目录
            cache_dir = getattr(self.config, 'cache_dir', None)
            if cache_dir:
                self._tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
            else:
                self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # 这里简化处理，实际应该是训练好的分类模型
            # 为了演示，我们使用预训练的特征提取模型
            try:
                from transformers import AutoModel
                if cache_dir:
                    self._model = AutoModel.from_pretrained(model_name, cache_dir=cache_dir)
                else:
                    self._model = AutoModel.from_pretrained(model_name)
            except Exception as e:
                self.logger.warning(f"加载分类模型失败，使用基础模型: {e}")
                if cache_dir:
                    self._model = AutoModel.from_pretrained(model_name, cache_dir=cache_dir)
                else:
                    self._model = AutoModel.from_pretrained(model_name)
            
            self._initialized = True
            self.logger.info("Transformer模型初始化完成")
            
        except ImportError:
            self.logger.error("transformers库未安装，请执行: pip install transformers torch")
            self._initialized = False
        except Exception as e:
            self.logger.error(f"模型初始化失败: {e}")
            self._initialized = False
    
    def _parse_internal(self, response: str, context: Optional[Dict[str, Any]] = None) -> ParsedStateInfo:
        """基于Transformer的内部解析实现"""
        if not self._initialized:
            self.logger.warning("Transformer模型未初始化，降级到规则方法")
            # 降级到规则方法
            rule_parser = RuleBasedParser(self.config)
            return rule_parser._parse_internal(response, context)
        
        try:
            # 文本编码
            inputs = self._tokenizer(response, return_tensors="pt", 
                                   max_length=512, truncation=True, padding=True)
            
            # 特征提取
            import torch
            with torch.no_grad():
                outputs = self._model(**inputs)
                # 使用[CLS]标记的隐藏状态作为句子表示
                sentence_embedding = outputs.last_hidden_state[:, 0, :].numpy()
            
            # 基于嵌入向量进行分析
            # 这里简化实现，实际应该训练专门的分类头
            confidence = self._calculate_transformer_confidence(sentence_embedding)
            sentiment = self._analyze_transformer_sentiment(sentence_embedding)
            intent = self._recognize_transformer_intent(sentence_embedding)
            entities = self._extract_transformer_entities(response, sentence_embedding)
            
            # 提取主要内容
            main_content = response[:200] if len(response) > 200 else response
            
            # 质量评估
            quality_metrics = {
                "content_length": len(response),
                "entity_count": len(entities),
                "confidence_score": confidence,
                "embedding_norm": float(np.linalg.norm(sentence_embedding)),
                "overall_quality": "good" if confidence > 0.6 else "acceptable",
                "is_valid": True
            }
            
            return ParsedStateInfo(
                main_content=main_content,
                confidence_score=confidence,
                extracted_entities=entities,
                sentiment=sentiment,
                intent=intent,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            self.logger.error(f"Transformer解析失败: {e}")
            # 降级到规则方法
            rule_parser = RuleBasedParser(self.config)
            return rule_parser._parse_internal(response, context)
    
    def _calculate_transformer_confidence(self, embedding) -> float:
        """基于嵌入向量计算置信度"""
        import numpy as np
        import torch
        
        if isinstance(embedding, torch.Tensor):
            embedding = embedding.numpy()
        
        # 简化实现：基于嵌入向量的范数
        norm = np.linalg.norm(embedding)
        return min(max(norm / 100.0, 0.0), 1.0)
    
    def _analyze_transformer_sentiment(self, embedding) -> str:
        """基于嵌入向量分析情感"""
        import numpy as np
        # 简化实现：基于嵌入向量的某些维度
        # 实际应该训练专门的情感分类器
        avg_value = np.mean(embedding)
        if avg_value > 0.1:
            return "positive"
        elif avg_value < -0.1:
            return "negative"
        else:
            return "neutral"
    
    def _recognize_transformer_intent(self, embedding) -> str:
        """基于嵌入向量识别意图"""
        import numpy as np
        # 简化实现
        max_dim = np.argmax(np.abs(embedding))
        intent_map = {
            0: "request_action",
            1: "report_status", 
            2: "indicate_completion",
            3: "signal_error",
            4: "describe_progress"
        }
        return intent_map.get(max_dim % 5, "unknown")
    
    def _extract_transformer_entities(self, response: str, embedding) -> Dict[str, str]:
        """基于Transformer提取实体"""
        entities = {}
        
        # 简化实现，结合规则和向量特征
        import numpy as np
        avg_embedding = np.mean(embedding)
        
        if avg_embedding > 0.05:
            entities["status_type"] = "success"
        elif avg_embedding < -0.05:
            entities["status_type"] = "error"
        else:
            entities["status_type"] = "neutral"
        
        # 添加更多实体提取逻辑...
        entities["extraction_method"] = "transformer"
        
        return entities


class DeepSeekParser(BaseResponseParser):
    """基于DeepSeek API的解析器"""
    
    def __init__(self, config: ParserConfig):
        super().__init__(config)
        self._client = None
        self._initialized = False
        self._init_client()
    
    def _init_client(self):
        """初始化DeepSeek客户端"""
        try:
            # 尝试使用langchain_openai兼容的客户端
            from langchain_openai import ChatOpenAI
            
            api_key = self.config.api_key
            if not api_key:
                # 尝试从环境变量获取
                import os
                api_key = os.getenv('DEEPSEEK_API_KEY')
            
            if not api_key:
                self.logger.error("DeepSeek API密钥未配置")
                return
            
            base_url = self.config.api_base or "https://api.deepseek.com"
            
            self._client = ChatOpenAI(
                model="deepseek-chat",
                api_key=api_key,
                base_url=base_url,
                temperature=0.1,
                max_tokens=1000,
                timeout=self.config.timeout
            )
            
            self._initialized = True
            self.logger.info("DeepSeek客户端初始化完成")
            
        except ImportError:
            self.logger.error("langchain_openai未安装，请执行: pip install langchain-openai")
        except Exception as e:
            self.logger.error(f"DeepSeek客户端初始化失败: {e}")
    
    def _parse_internal(self, response: str, context: Optional[Dict[str, Any]] = None) -> ParsedStateInfo:
        """基于DeepSeek API的内部解析实现"""
        if not self._initialized:
            self.logger.warning("DeepSeek客户端未初始化，降级到规则方法")
            rule_parser = RuleBasedParser(self.config)
            return rule_parser._parse_internal(response, context)
        
        try:
            # 构建分析提示
            analysis_prompt = self._build_analysis_prompt(response, context)
            
            # 调用DeepSeek API
            from langchain_core.messages import HumanMessage
            
            for attempt in range(self.config.max_retries):
                try:
                    result = self._client.invoke([HumanMessage(content=analysis_prompt)])
                    analysis_result = result.content
                    break
                except Exception as e:
                    self.logger.warning(f"DeepSeek API调用失败 (尝试 {attempt + 1}/{self.config.max_retries}): {e}")
                    if attempt == self.config.max_retries - 1:
                        raise
                    time.sleep(1)  # 等待重试
            
            # 解析DeepSeek的分析结果
            parsed_info = self._parse_deepseek_result(response, analysis_result)
            return parsed_info
            
        except Exception as e:
            self.logger.error(f"DeepSeek解析失败: {e}")
            # 降级到规则方法
            rule_parser = RuleBasedParser(self.config)
            return rule_parser._parse_internal(response, context)
    
    def _build_analysis_prompt(self, response: str, context: Optional[Dict[str, Any]] = None) -> str:
        """构建分析提示"""
        prompt = f"""请分析以下响应文本，并提供结构化的分析结果：

响应文本：
{response}

"""
        
        if context:
            prompt += f"上下文信息：\n{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
        
        prompt += """请按照以下JSON格式返回分析结果：
{
    "main_content": "主要内容摘要（1-2句话）",
    "confidence_score": 0.85,
    "sentiment": "positive/negative/neutral",
    "intent": "request_action/report_status/indicate_completion/signal_error/describe_progress",
    "status_type": "success/error/progress/neutral",
    "extracted_entities": {
        "key1": "value1",
        "key2": "value2"
    },
    "quality_assessment": "excellent/good/acceptable/poor"
}

要求：
1. main_content必须简洁明了
2. confidence_score范围0.0-1.0
3. 如果无法确定某项，请标注为null
4. extracted_entities提取关键信息如文件名、错误信息、数值等
5. 只返回JSON，不要其他文字"""
        
        return prompt
    
    def _parse_deepseek_result(self, original_response: str, analysis_result: str) -> ParsedStateInfo:
        """解析DeepSeek的分析结果"""
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', analysis_result, re.DOTALL)
            if not json_match:
                raise ValueError("未找到有效的JSON响应")
            
            json_str = json_match.group(0)
            analysis_data = json.loads(json_str)
            
            # 构建ParsedStateInfo
            main_content = analysis_data.get("main_content", original_response[:100])
            confidence_score = float(analysis_data.get("confidence_score", 0.5))
            sentiment = analysis_data.get("sentiment")
            intent = analysis_data.get("intent")
            
            # 处理实体信息
            entities = analysis_data.get("extracted_entities", {})
            if analysis_data.get("status_type"):
                entities["status_type"] = analysis_data["status_type"]
            entities["extraction_method"] = "deepseek"
            
            # 质量指标
            quality_metrics = {
                "content_length": len(original_response),
                "entity_count": len(entities),
                "confidence_score": confidence_score,
                "overall_quality": analysis_data.get("quality_assessment", "acceptable"),
                "is_valid": True,
                "api_method": "deepseek"
            }
            
            return ParsedStateInfo(
                main_content=main_content,
                confidence_score=confidence_score,
                extracted_entities=entities,
                sentiment=sentiment,
                intent=intent,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            self.logger.error(f"解析DeepSeek结果失败: {e}")
            # 返回基础信息
            return ParsedStateInfo(
                main_content=original_response[:100],
                confidence_score=0.3,
                extracted_entities={"status_type": "unknown", "error": str(e)},
                sentiment="neutral",
                intent="unknown",
                quality_metrics={"overall_quality": "poor", "is_valid": False}
            )


class EmbeddingParser(BaseResponseParser):
    """基于轻量级嵌入模型的解析器"""
    
    def __init__(self, config: ParserConfig):
        super().__init__(config)
        self._model = None
        self._initialized = False
        self._semantic_templates = {}
        self._init_model()
    
    def _init_model(self):
        """初始化嵌入模型"""
        try:
            from sentence_transformers import SentenceTransformer
            
            model_name = self.config.model_name or 'paraphrase-multilingual-MiniLM-L12-v2'
            
            self.logger.info(f"正在加载嵌入模型: {model_name}")
            self._model = SentenceTransformer(model_name)
            
            # 初始化语义模板
            self._init_semantic_templates()
            
            self._initialized = True
            self.logger.info("嵌入模型初始化完成")
            
        except ImportError:
            self.logger.error("sentence-transformers未安装，请执行: pip install sentence-transformers")
        except Exception as e:
            self.logger.error(f"嵌入模型初始化失败: {e}")
    
    def _init_semantic_templates(self):
        """初始化语义模板"""
        # 定义各种语义模板
        templates = {
            "success": [
                "任务成功完成", "操作执行成功", "工作顺利完成", "目标已达成",
                "处理成功", "运行正常", "创建成功", "更新完成"
            ],
            "error": [
                "出现错误", "执行失败", "发生异常", "操作失败",
                "系统故障", "处理失败", "无法完成", "运行异常"
            ],
            "progress": [
                "正在处理", "开始执行", "进行中", "正在运行",
                "开始工作", "处理中", "执行中", "运行中"
            ],
            "request_action": [
                "请执行操作", "需要处理", "要求完成", "希望执行",
                "建议进行", "请求帮助", "需要支持", "要求处理"
            ],
            "report_status": [
                "当前状态", "目前情况", "状态报告", "情况说明",
                "现在状态", "当前进展", "目前进度", "状态更新"
            ]
        }
        
        # 计算模板嵌入
        for category, template_list in templates.items():
            embeddings = self._model.encode(template_list)
            self._semantic_templates[category] = {
                "templates": template_list,
                "embeddings": embeddings
            }
    
    def _parse_internal(self, response: str, context: Optional[Dict[str, Any]] = None) -> ParsedStateInfo:
        """基于嵌入模型的内部解析实现"""
        if not self._initialized:
            self.logger.warning("嵌入模型未初始化，降级到规则方法")
            rule_parser = RuleBasedParser(self.config)
            return rule_parser._parse_internal(response, context)
        
        try:
            # 计算响应的嵌入向量
            response_embedding = self._model.encode([response])[0]
            
            # 语义相似度分析
            semantic_analysis = self._analyze_semantic_similarity(response_embedding)
            
            # 提取主要内容
            main_content = response[:200] if len(response) > 200 else response
            
            # 基于语义相似度确定各项属性
            status_type = self._determine_status_type(semantic_analysis)
            sentiment = self._determine_sentiment(semantic_analysis)
            intent = self._determine_intent(semantic_analysis)
            confidence = self._calculate_embedding_confidence(semantic_analysis)
            
            # 构建实体信息
            entities = {
                "status_type": status_type,
                "extraction_method": "embedding",
                "max_similarity": max(semantic_analysis.values()) if semantic_analysis else 0.0
            }
            
            # 质量评估
            quality_metrics = {
                "content_length": len(response),
                "entity_count": len(entities),
                "confidence_score": confidence,
                "max_similarity": entities["max_similarity"],
                "overall_quality": "good" if confidence > 0.6 else "acceptable",
                "is_valid": True
            }
            
            return ParsedStateInfo(
                main_content=main_content,
                confidence_score=confidence,
                extracted_entities=entities,
                sentiment=sentiment,
                intent=intent,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            self.logger.error(f"嵌入模型解析失败: {e}")
            # 降级到规则方法
            rule_parser = RuleBasedParser(self.config)
            return rule_parser._parse_internal(response, context)
    
    def _analyze_semantic_similarity(self, response_embedding) -> Dict[str, float]:
        """分析语义相似度"""
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        similarities = {}
        
        for category, template_data in self._semantic_templates.items():
            template_embeddings = template_data["embeddings"]
            
            # 计算与所有模板的相似度
            sims = cosine_similarity([response_embedding], template_embeddings)[0]
            
            # 取最大相似度
            max_sim = np.max(sims)
            similarities[category] = float(max_sim)
        
        return similarities
    
    def _determine_status_type(self, similarities: Dict[str, float]) -> str:
        """基于相似度确定状态类型"""
        status_categories = ["success", "error", "progress"]
        
        max_category = None
        max_score = 0.0
        
        for category in status_categories:
            if category in similarities and similarities[category] > max_score:
                max_score = similarities[category]
                max_category = category
        
        return max_category if max_category and max_score > 0.3 else "neutral"
    
    def _determine_sentiment(self, similarities: Dict[str, float]) -> str:
        """基于相似度确定情感"""
        success_score = similarities.get("success", 0.0)
        error_score = similarities.get("error", 0.0)
        
        if success_score > error_score and success_score > 0.4:
            return "positive"
        elif error_score > success_score and error_score > 0.4:
            return "negative"
        else:
            return "neutral"
    
    def _determine_intent(self, similarities: Dict[str, float]) -> str:
        """基于相似度确定意图"""
        intent_categories = ["request_action", "report_status"]
        
        max_category = None
        max_score = 0.0
        
        for category in intent_categories:
            if category in similarities and similarities[category] > max_score:
                max_score = similarities[category]
                max_category = category
        
        # 如果相似度不高，基于状态类型推断意图
        if not max_category or max_score < 0.3:
            status_type = self._determine_status_type(similarities)
            if status_type == "success":
                return "indicate_completion"
            elif status_type == "error":
                return "signal_error"
            elif status_type == "progress":
                return "describe_progress"
        
        return max_category or "unknown"
    
    def _calculate_embedding_confidence(self, similarities: Dict[str, float]) -> float:
        """基于语义相似度计算置信度"""
        if not similarities:
            return 0.0
        
        max_similarity = max(similarities.values())
        
        # 基于最大相似度计算置信度
        confidence = max_similarity * 0.8  # 基础置信度
        
        # 如果多个类别都有较高相似度，降低置信度
        high_sim_count = sum(1 for sim in similarities.values() if sim > 0.4)
        if high_sim_count > 1:
            confidence *= 0.8
        
        return min(max(confidence, 0.0), 1.0)


class MultiMethodResponseParser:
    """多方法响应解析器主类"""
    
    def __init__(self, config: ParserConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.MultiMethodResponseParser")
        
        # 解析器实例缓存
        self._parsers = {}
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "method_usage": {},
            "fallback_usage": {},
            "average_confidence": 0.0,
            "success_rate": 0.0
        }
        
        self.logger.info(f"多方法响应解析器初始化完成，主方法: {config.method.value}")
    
    def parse_response(self, response: str, context: Optional[Dict[str, Any]] = None) -> ParsedStateInfo:
        """解析响应的统一接口"""
        self.stats["total_requests"] += 1
        
        if not response or not response.strip():
            return self._create_empty_parsed_info("空响应")
        
        # 尝试使用主方法
        result = self._try_parse_with_method(self.config.method, response, context)
        
        # 如果主方法失败或置信度不够，尝试降级
        if (result.confidence_score < self.config.confidence_threshold and 
            self.config.fallback_chain and len(self.config.fallback_chain) > 1):
            
            for fallback_method in self.config.fallback_chain[1:]:
                self.logger.info(f"降级到方法: {fallback_method.value}")
                fallback_result = self._try_parse_with_method(fallback_method, response, context)
                
                if fallback_result.confidence_score > result.confidence_score:
                    result = fallback_result
                    self.stats["fallback_usage"][fallback_method.value] = (
                        self.stats["fallback_usage"].get(fallback_method.value, 0) + 1
                    )
                    break
        
        # 更新统计信息
        self._update_stats(result)
        
        return result
    
    def _try_parse_with_method(self, method: ParserMethod, response: str, context: Optional[Dict[str, Any]] = None) -> ParsedStateInfo:
        """尝试使用指定方法解析"""
        try:
            parser = self._get_parser(method)
            result = parser.parse_response(response, context)
            
            # 更新方法使用统计
            self.stats["method_usage"][method.value] = (
                self.stats["method_usage"].get(method.value, 0) + 1
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"方法 {method.value} 解析失败: {e}")
            return self._create_empty_parsed_info(f"方法 {method.value} 解析失败: {str(e)}")
    
    def _get_parser(self, method: ParserMethod) -> BaseResponseParser:
        """获取解析器实例"""
        if method not in self._parsers:
            if method == ParserMethod.RULE:
                self._parsers[method] = RuleBasedParser(self.config)
            elif method == ParserMethod.TRANSFORMER:
                self._parsers[method] = TransformerParser(self.config)
            elif method == ParserMethod.DEEPSEEK:
                self._parsers[method] = DeepSeekParser(self.config)
            elif method == ParserMethod.EMBEDDING:
                self._parsers[method] = EmbeddingParser(self.config)
            else:
                raise ValueError(f"不支持的解析方法: {method}")
        
        return self._parsers[method]
    
    def _create_empty_parsed_info(self, reason: str) -> ParsedStateInfo:
        """创建空的解析信息"""
        return ParsedStateInfo(
            main_content=f"解析失败: {reason}",
            confidence_score=0.0,
            extracted_entities={"status_type": "error", "error_reason": reason},
            sentiment="negative",
            intent="signal_error",
            quality_metrics={"overall_quality": ResponseQuality.INVALID.value, "is_valid": False}
        )
    
    def _update_stats(self, result: ParsedStateInfo):
        """更新统计信息"""
        # 更新平均置信度
        total_confidence = self.stats["average_confidence"] * (self.stats["total_requests"] - 1)
        self.stats["average_confidence"] = (total_confidence + result.confidence_score) / self.stats["total_requests"]
        
        # 更新成功率
        is_success = result.quality_metrics.get("is_valid", False)
        total_success = self.stats["success_rate"] * (self.stats["total_requests"] - 1)
        self.stats["success_rate"] = (total_success + (1 if is_success else 0)) / self.stats["total_requests"]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "method_usage": {},
            "fallback_usage": {},
            "average_confidence": 0.0,
            "success_rate": 0.0
        }


class ParserFactory:
    """解析器工厂类"""
    
    @staticmethod
    def create_parser(method: Union[str, ParserMethod], **kwargs) -> MultiMethodResponseParser:
        """创建解析器实例"""
        if isinstance(method, str):
            method = ParserMethod(method)
        
        config = ParserConfig(method=method, **kwargs)
        return MultiMethodResponseParser(config)
    
    @staticmethod
    def create_rule_parser(**kwargs) -> MultiMethodResponseParser:
        """创建规则解析器"""
        return ParserFactory.create_parser(ParserMethod.RULE, **kwargs)
    
    @staticmethod
    def create_transformer_parser(model_name: str = None, **kwargs) -> MultiMethodResponseParser:
        """创建Transformer解析器"""
        return ParserFactory.create_parser(
            ParserMethod.TRANSFORMER, 
            model_name=model_name or 'hfl/chinese-bert-wwm-ext',
            **kwargs
        )
    
    @staticmethod
    def create_deepseek_parser(api_key: str, api_base: str = None, **kwargs) -> MultiMethodResponseParser:
        """创建DeepSeek解析器"""
        return ParserFactory.create_parser(
            ParserMethod.DEEPSEEK,
            api_key=api_key,
            api_base=api_base or "https://api.deepseek.com",
            **kwargs
        )
    
    @staticmethod
    def create_embedding_parser(model_name: str = None, **kwargs) -> MultiMethodResponseParser:
        """创建嵌入解析器"""
        return ParserFactory.create_parser(
            ParserMethod.EMBEDDING,
            model_name=model_name or 'paraphrase-multilingual-MiniLM-L12-v2',
            **kwargs
        )
    
    @staticmethod
    def create_hybrid_parser(primary_method: Union[str, ParserMethod], 
                           fallback_chain: List[Union[str, ParserMethod]] = None,
                           **kwargs) -> MultiMethodResponseParser:
        """创建混合解析器"""
        if isinstance(primary_method, str):
            primary_method = ParserMethod(primary_method)
        
        if fallback_chain:
            fallback_chain = [ParserMethod(m) if isinstance(m, str) else m for m in fallback_chain]
        else:
            fallback_chain = [ParserMethod.RULE]  # 默认降级到规则方法
        
        return ParserFactory.create_parser(
            primary_method,
            fallback_chain=fallback_chain,
            **kwargs
        )


# 使用示例和测试函数
def demo_usage():
    """演示用法"""
    print("=== 多方法响应解析器演示 ===")
    
    # 测试响应
    test_responses = [
        "任务已成功完成，所有文件都已创建。",
        "出现了一个严重错误，无法继续执行。",
        "正在处理数据，请稍等...",
        "需要您提供更多信息才能继续。",
        "当前系统运行正常，没有发现问题。"
    ]
    
    # 创建不同类型的解析器
    parsers = {
        "规则解析器": ParserFactory.create_rule_parser(),
        "混合解析器": ParserFactory.create_hybrid_parser(
            ParserMethod.RULE,
            fallback_chain=[ParserMethod.RULE]
        )
    }
    
    # 测试每个解析器
    for parser_name, parser in parsers.items():
        print(f"\n--- {parser_name} ---")
        
        for i, response in enumerate(test_responses, 1):
            result = parser.parse_response(response)
            print(f"测试 {i}: {response[:30]}...")
            print(f"  状态类型: {result.extracted_entities.get('status_type', 'unknown')}")
            print(f"  情感: {result.sentiment}")
            print(f"  意图: {result.intent}")
            print(f"  置信度: {result.confidence_score:.2f}")
            print(f"  质量: {result.quality_metrics.get('overall_quality', 'unknown')}")
    
    # 显示统计信息
    print(f"\n--- 解析器统计信息 ---")
    for parser_name, parser in parsers.items():
        stats = parser.get_stats()
        print(f"{parser_name}: 请求数={stats['total_requests']}, 平均置信度={stats['average_confidence']:.2f}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 运行演示
    demo_usage()