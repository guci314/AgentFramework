# %%
from agent_base import Result, reduce_memory_decorator_compress
from pythonTask import StatefulExecutor, Agent, llm_deepseek
from langchain_core.language_models import BaseChatModel
from typing import Dict, List, Any, Optional, Tuple, NamedTuple
import json
import re
import random
from datetime import datetime as dt
from collections import deque, OrderedDict
import copy
from abc import ABC, abstractmethod
import threading
import time
import asyncio
from typing import Union, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from prompts import team_manager_system_message_share_state, team_manager_system_message_no_share_state
import logging
import sys
from enum import Enum
from string import Template

# 导入多方案响应解析器
try:
    from response_parser_v2 import (
        ParserFactory, ParserMethod, ParserConfig,
        MultiMethodResponseParser, ParsedStateInfo, ResponseQuality
    )
    RESPONSE_PARSER_AVAILABLE = True
except ImportError as e:
    RESPONSE_PARSER_AVAILABLE = False
    logging.warning(f"多方案响应解析器不可用: {e}")

# 配置日志输出到控制台 - 只在没有配置过时才配置
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

logger = logging.getLogger(__name__)
# 只设置当前模块的日志级别，不影响全局配置
logger.setLevel(logging.DEBUG)

# 导入配置系统
try:
    from config_system import (
        get_config, initialize_config, ApplicationConfig,
        StateHistoryConfig, AIUpdaterConfig, MonitoringConfig, OptimizationConfig
    )
    CONFIG_SYSTEM_AVAILABLE = True
except ImportError:
    CONFIG_SYSTEM_AVAILABLE = False
    logger.warning("配置系统不可用，将使用默认配置")

# 导入性能监控系统
try:
    from performance_monitor import (
        get_performance_monitor, configure_performance_monitoring,
        PerformanceMonitor, monitor_performance
    )
    PERFORMANCE_MONITOR_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITOR_AVAILABLE = False
    logger.warning("性能监控系统不可用，将跳过性能监控功能")

class StateHistoryEntry(NamedTuple):
    """状态历史条目"""
    timestamp: dt
    state_snapshot: str
    source: Optional[str] = None

class PromptScenario(Enum):
    """提示模板场景枚举"""
    INITIALIZATION = "initialization"          # 初始化场景
    SUCCESS_COMPLETION = "success_completion"  # 成功完成场景
    ERROR_HANDLING = "error_handling"          # 错误处理场景
    STATE_TRANSITION = "state_transition"      # 状态转换场景
    PROGRESS_UPDATE = "progress_update"        # 进度更新场景
    SUMMARY = "summary"                        # 总结场景
    CUSTOM = "custom"                          # 自定义场景

class PromptTemplate:
    """提示模板类"""
    
    def __init__(self, 
                 scenario: PromptScenario,
                 system_message: str,
                 user_template: str,
                 version: str = "1.0",
                 description: str = ""):
        """
        初始化提示模板
        
        Args:
            scenario: 模板使用场景
            system_message: 系统消息模板
            user_template: 用户消息模板（支持变量替换）
            version: 模板版本
            description: 模板描述
        """
        self.scenario = scenario
        self.system_message = system_message
        self.user_template = Template(user_template)
        self.version = version
        self.description = description
        self.created_at = dt.now()
        
    def render(self, variables: Dict[str, Any]) -> Tuple[str, str]:
        """
        渲染模板
        
        Args:
            variables: 模板变量字典
            
        Returns:
            (system_message, user_message) 元组
        """
        try:
            # 处理缺失变量的默认值
            safe_variables = self._prepare_safe_variables(variables)
            user_message = self.user_template.safe_substitute(safe_variables)
            return self.system_message, user_message
        except Exception as e:
            raise ValueError(f"模板渲染失败: {e}")
    
    def _prepare_safe_variables(self, variables: Dict[str, Any]) -> Dict[str, str]:
        """
        准备安全的变量字典，为缺失变量提供默认值
        
        Args:
            variables: 原始变量字典
            
        Returns:
            安全的变量字典
        """
        safe_vars = {}
        for key, value in variables.items():
            if value is None:
                safe_vars[key] = "未提供"
            elif isinstance(value, str):
                safe_vars[key] = value
            else:
                safe_vars[key] = str(value)
        
        # 为常用变量提供默认值
        defaults = {
            'current_state': '无当前状态',
            'step_description': '未知步骤',
            'step_status': '未知',
            'step_type': '未知类型',
            'execution_success': '未知',
            'execution_output': '无输出',
            'error_message': '无错误信息',
            'previous_state': '无前置状态',
            'workflow_progress': '进度未知'
        }
        
        for key, default_value in defaults.items():
            if key not in safe_vars:
                safe_vars[key] = default_value
                
        return safe_vars
    
    def get_required_variables(self) -> List[str]:
        """
        获取模板所需的变量列表
        
        Returns:
            变量名列表
        """
        import re
        # 使用正则表达式提取模板中的变量
        pattern = r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)'
        matches = re.findall(pattern, self.user_template.template)
        variables = []
        for match in matches:
            var_name = match[0] if match[0] else match[1]
            if var_name and var_name not in variables:
                variables.append(var_name)
        return variables

class PromptTemplateManager:
    """提示模板管理器"""
    
    def __init__(self):
        """初始化模板管理器"""
        self._templates: Dict[PromptScenario, PromptTemplate] = {}
        self._logger = logging.getLogger(f"{__name__}.PromptTemplateManager")
        
        # 初始化默认模板
        self._initialize_default_templates()
        
        self._logger.info(f"提示模板管理器初始化完成，加载了{len(self._templates)}个模板")
    
    def _initialize_default_templates(self):
        """初始化默认模板"""
        
        # 初始化场景模板
        initialization_template = PromptTemplate(
            scenario=PromptScenario.INITIALIZATION,
            system_message="""你是一个工作流状态管理专家，负责为新开始的工作流生成初始状态描述。

要求：
1. 状态描述应该简洁明了（1-2句话）
2. 重点描述工作流的目标和初始阶段
3. 体现工作流刚开始的状态
4. 使用积极的语调表达开始的意图""",
            user_template="""工作流初始化信息：

## 工作流目标
主要指令：$main_instruction

## 当前情况
- 工作流状态：刚开始
- 初始步骤：$step_description
- 步骤类型：$step_type

请生成一个简洁的初始状态描述（1-2句话），说明工作流刚开始，准备执行什么任务。""",
            version="1.0",
            description="用于工作流初始化时的状态描述生成"
        )
        
        # 成功完成场景模板
        success_template = PromptTemplate(
            scenario=PromptScenario.SUCCESS_COMPLETION,
            system_message="""你是一个工作流状态管理专家，负责为成功完成的步骤生成状态更新。

要求：
1. 状态描述应该简洁明了（1-3句话）
2. 重点描述完成的成果和进展
3. 体现连贯的状态演进
4. 使用积极的语调表达成功""",
            user_template="""步骤成功完成信息：

## 当前状态
当前状态：$current_state

## 完成的步骤
步骤描述：$step_description
步骤类型：$step_type
执行结果：$execution_output

## 状态历史
$state_history

请生成一个简洁的状态描述（1-3句话），反映这个步骤的成功完成和当前工作流的进展。""",
            version="1.0",
            description="用于步骤成功完成时的状态描述生成"
        )
        
        # 错误处理场景模板
        error_template = PromptTemplate(
            scenario=PromptScenario.ERROR_HANDLING,
            system_message="""你是一个工作流状态管理专家，负责为遇到错误的步骤生成状态更新。

要求：
1. 状态描述应该简洁明了（1-3句话）
2. 明确指出遇到的问题但不过分强调失败
3. 如果可能，暗示解决方向或下一步计划
4. 保持专业和建设性的语调""",
            user_template="""步骤执行遇到错误：

## 当前状态
当前状态：$current_state

## 遇到问题的步骤
步骤描述：$step_description
步骤类型：$step_type
错误信息：$error_message
执行输出：$execution_output

## 状态历史
$state_history

请生成一个简洁的状态描述（1-3句话），说明遇到的问题和当前的工作流状态，避免过度强调失败。""",
            version="1.0",
            description="用于步骤执行失败时的状态描述生成"
        )
        
        # 状态转换场景模板
        transition_template = PromptTemplate(
            scenario=PromptScenario.STATE_TRANSITION,
            system_message="""你是一个工作流状态管理专家，负责为复杂状态转换生成描述。

要求：
1. 状态描述应该简洁明了（2-3句话）
2. 清楚地表达从一个阶段到另一个阶段的转换
3. 体现工作流的连续性和进展
4. 突出关键的转换节点""",
            user_template="""工作流状态转换信息：

## 转换前状态
前一状态：$previous_state

## 当前状态
当前状态：$current_state

## 转换触发步骤
步骤描述：$step_description
步骤类型：$step_type
执行结果：$execution_output

## 工作流进展
整体进度：$workflow_progress

请生成一个简洁的状态描述（2-3句话），清楚地表达这次状态转换和工作流的进展情况。""",
            version="1.0",
            description="用于复杂状态转换时的状态描述生成"
        )
        
        # 进度更新场景模板
        progress_template = PromptTemplate(
            scenario=PromptScenario.PROGRESS_UPDATE,
            system_message="""你是一个工作流状态管理专家，负责生成中间进度的状态更新。

要求：
1. 状态描述应该简洁明了（1-2句话）
2. 重点体现当前的进展情况
3. 保持与之前状态的连贯性
4. 体现积极的推进态度""",
            user_template="""工作流进度更新：

## 当前状态
当前状态：$current_state

## 最新步骤
步骤描述：$step_description
步骤类型：$step_type
执行情况：$execution_success

## 整体进展
工作流进度：$workflow_progress

请生成一个简洁的状态描述（1-2句话），反映当前的进展情况。""",
            version="1.0",
            description="用于中间进度更新时的状态描述生成"
        )
        
        # 总结场景模板
        summary_template = PromptTemplate(
            scenario=PromptScenario.SUMMARY,
            system_message="""你是一个工作流状态管理专家，负责生成工作流完成或阶段性总结的状态描述。

要求：
1. 状态描述应该简洁明了（2-4句话）
2. 总结主要成果和完成情况
3. 体现工作流的整体价值
4. 使用积极和总结性的语调""",
            user_template="""工作流总结信息：

## 最终/阶段状态
当前状态：$current_state

## 完成情况
主要成果：$execution_output
完成步骤：$step_description
整体进度：$workflow_progress

## 状态历史回顾
$state_history

请生成一个总结性的状态描述（2-4句话），概括工作流的主要成果和完成情况。""",
            version="1.0",
            description="用于工作流完成或阶段性总结时的状态描述生成"
        )
        
        # 注册所有模板
        self._templates[PromptScenario.INITIALIZATION] = initialization_template
        self._templates[PromptScenario.SUCCESS_COMPLETION] = success_template
        self._templates[PromptScenario.ERROR_HANDLING] = error_template
        self._templates[PromptScenario.STATE_TRANSITION] = transition_template
        self._templates[PromptScenario.PROGRESS_UPDATE] = progress_template
        self._templates[PromptScenario.SUMMARY] = summary_template
    
    def get_template(self, scenario: PromptScenario) -> Optional[PromptTemplate]:
        """
        获取指定场景的模板
        
        Args:
            scenario: 场景枚举值
            
        Returns:
            模板实例，如果不存在则返回None
        """
        return self._templates.get(scenario)
    
    def add_template(self, template: PromptTemplate) -> None:
        """
        添加新模板
        
        Args:
            template: 模板实例
        """
        self._templates[template.scenario] = template
        self._logger.info(f"添加新模板: {template.scenario.value} v{template.version}")
    
    def list_templates(self) -> List[Tuple[PromptScenario, str, str]]:
        """
        列出所有模板
        
        Returns:
            [(scenario, version, description), ...] 列表
        """
        return [(scenario, template.version, template.description) 
                for scenario, template in self._templates.items()]
    
    def render_template(self, scenario: PromptScenario, variables: Dict[str, Any]) -> Tuple[str, str]:
        """
        渲染指定场景的模板
        
        Args:
            scenario: 场景枚举值
            variables: 模板变量字典
            
        Returns:
            (system_message, user_message) 元组
            
        Raises:
            ValueError: 模板不存在或渲染失败
        """
        template = self.get_template(scenario)
        if template is None:
            raise ValueError(f"场景模板不存在: {scenario.value}")
        
        try:
            return template.render(variables)
        except Exception as e:
            self._logger.error(f"模板渲染失败 [{scenario.value}]: {e}")
            raise
    
    def get_template_variables(self, scenario: PromptScenario) -> List[str]:
        """
        获取指定场景模板所需的变量列表
        
        Args:
            scenario: 场景枚举值
            
        Returns:
            变量名列表
        """
        template = self.get_template(scenario)
        if template is None:
            return []
        return template.get_required_variables()
    
    def validate_variables(self, scenario: PromptScenario, variables: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证变量是否满足模板要求
        
        Args:
            scenario: 场景枚举值
            variables: 待验证的变量字典
            
        Returns:
            (是否通过验证, 缺失的变量列表)
        """
        required_vars = self.get_template_variables(scenario)
        provided_vars = set(variables.keys())
        required_vars_set = set(required_vars)
        
        missing_vars = list(required_vars_set - provided_vars)
        return len(missing_vars) == 0, missing_vars


class ParsedStateInfo(NamedTuple):
    """解析后的状态信息结构"""
    main_content: str                      # 主要状态内容
    confidence_score: float               # 置信度评分 (0.0-1.0)
    extracted_entities: Dict[str, str]    # 提取的实体信息
    sentiment: Optional[str] = None       # 情感分析结果
    intent: Optional[str] = None          # 意图识别结果
    quality_metrics: Dict[str, Any] = {}  # 质量指标


class ResponseQuality(Enum):
    """响应质量等级"""
    EXCELLENT = "excellent"    # 极佳
    GOOD = "good"             # 良好  
    ACCEPTABLE = "acceptable" # 可接受
    POOR = "poor"             # 较差
    INVALID = "invalid"       # 无效


class ResponseParser:
    """智能LLM响应解析器"""
    
    def __init__(self, enable_sentiment_analysis: bool = True, 
                 enable_intent_recognition: bool = True):
        """
        初始化响应解析器
        
        Args:
            enable_sentiment_analysis: 是否启用情感分析
            enable_intent_recognition: 是否启用意图识别
        """
        self.enable_sentiment_analysis = enable_sentiment_analysis
        self.enable_intent_recognition = enable_intent_recognition
        self._logger = logging.getLogger(f"{__name__}.ResponseParser")
        
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
        
        self._logger.debug(f"ResponseParser初始化完成 - 情感分析: {enable_sentiment_analysis}, 意图识别: {enable_intent_recognition}")

    def parse_response(self, raw_response: str, context: Optional[Dict[str, Any]] = None) -> ParsedStateInfo:
        """
        解析LLM响应并提取结构化信息
        
        Args:
            raw_response: 原始LLM响应
            context: 可选的上下文信息
            
        Returns:
            ParsedStateInfo: 解析后的结构化状态信息
        """
        try:
            self._logger.debug(f"开始解析响应，长度: {len(raw_response) if raw_response else 0}")
            
            if not raw_response:
                return self._create_empty_parsed_info("空响应")
            
            # 1. 基础清理和预处理
            cleaned_content = self._preprocess_response(raw_response)
            
            # 2. 提取主要内容
            main_content = self._extract_main_content(cleaned_content)
            
            # 3. 实体提取
            entities = self._extract_entities(cleaned_content, context)
            
            # 4. 计算置信度
            confidence = self._calculate_confidence(cleaned_content, entities)
            
            # 5. 情感分析（可选）
            sentiment = None
            if self.enable_sentiment_analysis:
                sentiment = self._analyze_sentiment(cleaned_content)
            
            # 6. 意图识别（可选）
            intent = None  
            if self.enable_intent_recognition:
                intent = self._recognize_intent(cleaned_content)
            
            # 7. 质量评估
            quality_metrics = self._assess_quality(cleaned_content, entities, confidence)
            
            parsed_info = ParsedStateInfo(
                main_content=main_content,
                confidence_score=confidence,
                extracted_entities=entities,
                sentiment=sentiment,
                intent=intent,
                quality_metrics=quality_metrics
            )
            
            self._logger.info(f"响应解析完成 - 置信度: {confidence:.2f}, 质量: {quality_metrics.get('overall_quality', 'unknown')}")
            return parsed_info
            
        except Exception as e:
            self._logger.error(f"响应解析失败: {e}")
            return self._create_empty_parsed_info(f"解析异常: {str(e)}")

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

    def validate_parsed_info(self, parsed_info: ParsedStateInfo, 
                           min_confidence: float = 0.3) -> Tuple[bool, List[str]]:
        """
        验证解析后的信息是否符合要求
        
        Args:
            parsed_info: 解析后的状态信息
            min_confidence: 最小置信度阈值
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 问题列表)
        """
        issues = []
        
        # 置信度检查
        if parsed_info.confidence_score < min_confidence:
            issues.append(f"置信度过低: {parsed_info.confidence_score:.2f} < {min_confidence}")
        
        # 内容长度检查
        if len(parsed_info.main_content) < 5:
            issues.append("主要内容过短")
        
        # 质量检查
        if not parsed_info.quality_metrics.get("is_valid", False):
            issues.append("响应质量不合格")
        
        # 实体检查
        if not parsed_info.extracted_entities:
            issues.append("未提取到有效实体")
        
        is_valid = len(issues) == 0
        return is_valid, issues

    def suggest_improvements(self, parsed_info: ParsedStateInfo) -> List[str]:
        """建议改进措施"""
        suggestions = []
        
        if parsed_info.confidence_score < 0.5:
            suggestions.append("建议重新生成更详细的状态描述")
        
        if len(parsed_info.extracted_entities) < 2:
            suggestions.append("建议在状态描述中包含更多具体信息")
        
        if parsed_info.quality_metrics.get("overall_quality") in ["poor", "invalid"]:
            suggestions.append("建议检查LLM提示模板和参数设置")
        
        return suggestions


class StateRelevanceType(Enum):
    """状态相关性类型枚举"""
    HIGH = "high"           # 高相关性 - 直接相关的状态信息
    MEDIUM = "medium"       # 中等相关性 - 可能有用的状态信息
    LOW = "low"             # 低相关性 - 次要的状态信息
    NONE = "none"           # 无相关性 - 不相关的状态信息


class InstructionOptimizationType(Enum):
    """指令优化类型枚举"""
    CONTEXT_ENHANCEMENT = "context_enhancement"       # 上下文增强
    ERROR_PREVENTION = "error_prevention"             # 错误预防
    EFFICIENCY_IMPROVEMENT = "efficiency_improvement" # 效率提升
    CLARITY_OPTIMIZATION = "clarity_optimization"     # 清晰度优化
    DEPENDENCY_AWARENESS = "dependency_awareness"     # 依赖关系感知
    PATTERN_LEARNING = "pattern_learning"             # 模式学习


class OptimizationStrategy(Enum):
    """优化策略枚举"""
    CONSERVATIVE = "conservative"         # 保守策略 - 最小化修改
    MODERATE = "moderate"                # 适中策略 - 平衡修改和原始意图
    AGGRESSIVE = "aggressive"            # 激进策略 - 最大化优化效果
    ADAPTIVE = "adaptive"                # 自适应策略 - 根据上下文动态调整


class DecisionNodeType(Enum):
    """决策节点类型枚举"""
    CONDITIONAL = "conditional"       # 条件决策 - if/else
    SWITCH = "switch"                # 多路决策 - switch/case
    LOOP_CONDITION = "loop_condition" # 循环条件 - while/for
    VALIDATION = "validation"        # 验证决策 - 数据验证
    APPROVAL = "approval"            # 审批决策 - 人工审批
    THRESHOLD = "threshold"          # 阈值决策 - 基于数值比较


class ConditionOperator(Enum):
    """条件操作符枚举"""
    EQUALS = "=="              # 等于
    NOT_EQUALS = "!="          # 不等于
    GREATER_THAN = ">"         # 大于
    LESS_THAN = "<"            # 小于
    GREATER_EQUAL = ">="       # 大于等于
    LESS_EQUAL = "<="          # 小于等于
    CONTAINS = "contains"      # 包含
    NOT_CONTAINS = "not_contains"  # 不包含
    STARTS_WITH = "starts_with"    # 开始于
    ENDS_WITH = "ends_with"        # 结束于
    IN = "in"                      # 在列表中
    NOT_IN = "not_in"              # 不在列表中
    IS_EMPTY = "is_empty"          # 为空
    IS_NOT_EMPTY = "is_not_empty"  # 不为空
    REGEX_MATCH = "regex_match"    # 正则匹配


class DecisionResult(NamedTuple):
    """决策结果结构"""
    next_step_id: Optional[str]           # 下一步ID
    decision_made: bool                   # 是否成功做出决策
    decision_reason: str                  # 决策理由
    evaluated_conditions: List[Dict[str, Any]]  # 评估的条件
    state_variables_used: List[str]       # 使用的状态变量
    confidence: float                     # 决策置信度 (0.0-1.0)
    additional_actions: List[str]         # 额外的行动建议


class InstructionOptimizationResult(NamedTuple):
    """指令优化结果结构"""
    original_instruction: str                      # 原始指令
    optimized_instruction: str                     # 优化后的指令
    optimization_types: List[InstructionOptimizationType]  # 应用的优化类型
    confidence_score: float                        # 优化置信度 (0.0-1.0)
    applied_enhancements: List[str]               # 应用的增强功能
    predicted_improvement: float                   # 预期改进程度 (0.0-1.0)
    optimization_reasoning: str                    # 优化理由
    risk_assessment: Dict[str, Any]               # 风险评估


class StateContextExtractor:
    """状态上下文提取器 - 智能分析和提取相关状态信息"""
    
    def __init__(self):
        # 定义关键词映射表，用于识别步骤类型和相关性
        self.step_type_keywords = {
            'file_operations': ['文件', '创建', '写入', '读取', '保存', '删除', 'file', 'create', 'write', 'read', 'save', 'delete'],
            'database': ['数据库', '连接', '查询', '插入', '更新', 'database', 'db', 'query', 'insert', 'update', 'mysql', 'postgres'],
            'api': ['API', 'HTTP', '请求', '响应', '接口', 'request', 'response', 'endpoint', 'service'],
            'configuration': ['配置', '设置', '参数', 'config', 'configuration', 'setting', 'parameter'],
            'testing': ['测试', '验证', '检查', 'test', 'verify', 'check', 'validation'],
            'deployment': ['部署', '发布', '上线', 'deploy', 'deployment', 'release', 'publish'],
            'security': ['安全', '认证', '授权', '加密', 'security', 'auth', 'authentication', 'encryption'],
            'ui': ['界面', 'UI', '前端', '页面', 'frontend', 'page', 'interface', 'view'],
            'data_processing': ['数据', '处理', '分析', '转换', 'data', 'process', 'analysis', 'transform'],
            'error_handling': ['错误', '异常', '失败', '修复', 'error', 'exception', 'failure', 'fix', 'debug']
        }
        
        # 状态信息优先级映射
        self.state_priority_patterns = {
            'error_context': ['错误', '失败', '异常', 'error', 'failed', 'exception'],
            'file_paths': ['路径', '文件名', '目录', 'path', 'file', 'directory', 'folder'],
            'api_endpoints': ['API', 'URL', '端点', 'endpoint', 'service'],
            'database_info': ['数据库', '连接字符串', 'database', 'connection'],
            'config_values': ['配置', '参数', '设置', 'config', 'parameter', 'setting'],
            'completion_status': ['完成', '成功', '状态', 'completed', 'success', 'status']
        }
    
    def extract_relevant_context(self, step: Dict[str, Any], global_state: 'WorkflowState') -> Dict[str, Any]:
        """
        提取与当前步骤相关的状态上下文
        
        Args:
            step: 当前步骤信息
            global_state: 全局工作流状态
            
        Returns:
            相关状态上下文字典
        """
        context = {
            'high_relevance': [],
            'medium_relevance': [],
            'low_relevance': [],
            'state_summary': '',
            'extracted_entities': {}
        }
        
        try:
            # 分析步骤类型和关键词
            step_analysis = self._analyze_step_requirements(step)
            
            # 获取当前全局状态
            current_state = global_state.get_global_state()
            if not current_state:
                return context
            
            # 提取状态实体
            context['extracted_entities'] = self._extract_state_entities(current_state, step_analysis)
            
            # 根据相关性分类状态信息
            context = self._categorize_state_relevance(current_state, step_analysis, context)
            
            # 生成状态摘要
            context['state_summary'] = self._generate_context_summary(context, step_analysis)
            
            return context
            
        except Exception as e:
            logger.error(f"状态上下文提取失败: {e}")
            return context
    
    def _analyze_step_requirements(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """分析步骤需求和类型"""
        analysis = {
            'step_types': [],
            'keywords': [],
            'instruction_content': step.get('instruction', '').lower(),
            'step_name': step.get('name', '').lower(),
            'expected_output': step.get('expected_output', '').lower(),
            'agent_type': step.get('agent_name', '').lower()
        }
        
        # 合并所有文本内容进行分析
        full_text = f"{analysis['instruction_content']} {analysis['step_name']} {analysis['expected_output']}"
        
        # 识别步骤类型
        for step_type, keywords in self.step_type_keywords.items():
            if any(keyword in full_text for keyword in keywords):
                analysis['step_types'].append(step_type)
                analysis['keywords'].extend([kw for kw in keywords if kw in full_text])
        
        return analysis
    
    def _extract_state_entities(self, state_content: str, step_analysis: Dict[str, Any]) -> Dict[str, str]:
        """从状态内容中提取实体信息"""
        entities = {}
        state_lower = state_content.lower()
        
        # 提取文件路径
        import re
        file_patterns = [
            r'[a-zA-Z]?[:/\\][^\\s]+\\.[a-zA-Z0-9]+',  # 文件路径
            r'[./][^\\s]+\\.[a-zA-Z0-9]+',             # 相对路径
            r'[a-zA-Z0-9_-]+\\.[a-zA-Z0-9]+',         # 文件名
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, state_content)
            if matches:
                entities['file_paths'] = matches[:3]  # 最多保留3个文件路径
        
        # 提取配置键值对
        config_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)[\\s]*[:=][\\s]*([^\\n,;]+)'
        config_matches = re.findall(config_pattern, state_content)
        if config_matches:
            entities['config_pairs'] = dict(config_matches[:5])  # 最多保留5个配置对
        
        # 提取错误信息
        error_patterns = [
            r'错误[：:][^\\n]+',
            r'error[:\\s]+[^\\n]+',
            r'失败[：:][^\\n]+',
            r'failed[:\\s]+[^\\n]+'
        ]
        
        for pattern in error_patterns:
            matches = re.findall(pattern, state_content, re.IGNORECASE)
            if matches:
                entities['errors'] = matches[:2]  # 最多保留2个错误信息
                break
        
        # 提取API相关信息
        api_pattern = r'(https?://[^\\s]+|/api/[^\\s]+|[a-zA-Z]+API)'
        api_matches = re.findall(api_pattern, state_content, re.IGNORECASE)
        if api_matches:
            entities['api_info'] = api_matches[:3]
        
        return entities
    
    def _categorize_state_relevance(self, state_content: str, step_analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """根据相关性对状态信息进行分类"""
        state_lines = [line.strip() for line in state_content.split('\\n') if line.strip()]
        step_keywords = set(step_analysis['keywords'])
        step_types = step_analysis['step_types']
        
        for line in state_lines:
            line_lower = line.lower()
            relevance_score = 0
            
            # 计算相关性得分
            # 1. 关键词匹配
            matching_keywords = sum(1 for keyword in step_keywords if keyword in line_lower)
            relevance_score += matching_keywords * 2
            
            # 2. 步骤类型相关性
            for step_type in step_types:
                type_keywords = self.step_type_keywords.get(step_type, [])
                type_matches = sum(1 for keyword in type_keywords if keyword in line_lower)
                relevance_score += type_matches
            
            # 3. 优先级模式匹配
            for priority_type, patterns in self.state_priority_patterns.items():
                if any(pattern in line_lower for pattern in patterns):
                    relevance_score += 3
            
            # 4. 实体提取相关性
            if context['extracted_entities']:
                for entity_type, entities in context['extracted_entities'].items():
                    if isinstance(entities, list):
                        for entity in entities:
                            if str(entity).lower() in line_lower:
                                relevance_score += 2
                    elif isinstance(entities, dict):
                        for key, value in entities.items():
                            if key.lower() in line_lower or str(value).lower() in line_lower:
                                relevance_score += 2
            
            # 根据得分分类
            if relevance_score >= 5:
                context['high_relevance'].append(line)
            elif relevance_score >= 2:
                context['medium_relevance'].append(line)
            elif relevance_score >= 1:
                context['low_relevance'].append(line)
        
        return context
    
    def _generate_context_summary(self, context: Dict[str, Any], step_analysis: Dict[str, Any]) -> str:
        """生成上下文摘要"""
        summary_parts = []
        
        # 高相关性信息摘要
        if context['high_relevance']:
            summary_parts.append(f"**关键状态** ({len(context['high_relevance'])}项):")
            summary_parts.extend([f"• {item}" for item in context['high_relevance'][:3]])
        
        # 提取的实体摘要
        if context['extracted_entities']:
            entity_summary = []
            for entity_type, entities in context['extracted_entities'].items():
                if isinstance(entities, list) and entities:
                    entity_summary.append(f"{entity_type}: {', '.join(str(e) for e in entities[:2])}")
                elif isinstance(entities, dict) and entities:
                    pairs = [f"{k}={v}" for k, v in list(entities.items())[:2]]
                    entity_summary.append(f"{entity_type}: {', '.join(pairs)}")
            
            if entity_summary:
                summary_parts.append("**提取实体**: " + "; ".join(entity_summary))
        
        # 步骤类型相关提示
        if step_analysis['step_types']:
            summary_parts.append(f"**步骤类型**: {', '.join(step_analysis['step_types'])}")
        
        return "\n".join(summary_parts) if summary_parts else "无特别相关的状态信息"


class InstructionOptimizer(ABC):
    """指令优化器抽象接口"""
    
    @abstractmethod
    def can_optimize(self, instruction: str, step: Dict[str, Any], 
                    global_state: 'WorkflowState', context: Dict[str, Any]) -> bool:
        """
        判断是否可以优化指定的指令
        
        Args:
            instruction: 原始指令
            step: 步骤信息
            global_state: 全局状态
            context: 执行上下文
            
        Returns:
            是否可以优化
        """
        pass
    
    @abstractmethod
    def optimize_instruction(self, instruction: str, step: Dict[str, Any], 
                           global_state: 'WorkflowState', context: Dict[str, Any]) -> InstructionOptimizationResult:
        """
        优化指令
        
        Args:
            instruction: 原始指令
            step: 步骤信息
            global_state: 全局状态
            context: 执行上下文
            
        Returns:
            指令优化结果
        """
        pass
    
    @abstractmethod
    def get_optimization_priority(self) -> int:
        """
        获取优化器优先级 (数值越小优先级越高)
        
        Returns:
            优先级数值
        """
        pass


class StateAwareInstructionOptimizer(InstructionOptimizer):
    """状态感知的指令优化器"""
    
    def __init__(self, strategy: OptimizationStrategy = OptimizationStrategy.MODERATE):
        self.strategy = strategy
        self.logger = logging.getLogger(f"{__name__}.StateAwareInstructionOptimizer")
        
        # 优化规则配置
        self.optimization_rules = {
            InstructionOptimizationType.CONTEXT_ENHANCEMENT: True,
            InstructionOptimizationType.ERROR_PREVENTION: True,
            InstructionOptimizationType.EFFICIENCY_IMPROVEMENT: True,
            InstructionOptimizationType.CLARITY_OPTIMIZATION: True,
            InstructionOptimizationType.DEPENDENCY_AWARENESS: True,
            InstructionOptimizationType.PATTERN_LEARNING: False,  # 默认关闭，可根据需要启用
        }
        
        # 优化统计
        self.optimization_stats = {
            'total_optimizations': 0,
            'successful_optimizations': 0,
            'optimization_types_used': {},
            'average_confidence': 0.0,
            'average_improvement': 0.0
        }
        
        # 错误模式学习
        self.error_patterns = []
        self.success_patterns = []
        
    def can_optimize(self, instruction: str, step: Dict[str, Any], 
                    global_state: 'WorkflowState', context: Dict[str, Any]) -> bool:
        """判断是否可以优化指令"""
        if not instruction or not instruction.strip():
            return False
            
        # 检查是否有全局状态信息可用于优化
        state_content = global_state.get_global_state()
        if not state_content or len(state_content.strip()) < 10:
            return False
            
        # 检查是否有足够的上下文信息
        if not step or not context:
            return False
            
        # 如果指令已经很详细（包含状态感知信息），降低优化优先级
        if "状态感知" in instruction or "## 🎯" in instruction:
            return len(instruction) < 1000  # 只有当指令不是太长时才优化
            
        return True
    
    def optimize_instruction(self, instruction: str, step: Dict[str, Any], 
                           global_state: 'WorkflowState', context: Dict[str, Any]) -> InstructionOptimizationResult:
        """优化指令"""
        self.optimization_stats['total_optimizations'] += 1
        
        try:
            # 分析指令和上下文
            analysis = self._analyze_instruction_context(instruction, step, global_state, context)
            
            # 确定需要应用的优化类型
            optimization_types = self._determine_optimization_types(analysis)
            
            # 应用优化
            optimized_instruction = self._apply_optimizations(
                instruction, step, global_state, context, analysis, optimization_types
            )
            
            # 计算置信度和预期改进
            confidence_score = self._calculate_optimization_confidence(analysis, optimization_types)
            predicted_improvement = self._predict_improvement(analysis, optimization_types)
            
            # 进行风险评估
            risk_assessment = self._assess_optimization_risk(instruction, optimized_instruction, analysis)
            
            # 生成优化理由
            reasoning = self._generate_optimization_reasoning(optimization_types, analysis)
            
            # 创建结果
            result = InstructionOptimizationResult(
                original_instruction=instruction,
                optimized_instruction=optimized_instruction,
                optimization_types=optimization_types,
                confidence_score=confidence_score,
                applied_enhancements=self._get_applied_enhancements(optimization_types),
                predicted_improvement=predicted_improvement,
                optimization_reasoning=reasoning,
                risk_assessment=risk_assessment
            )
            
            # 更新统计
            self._update_optimization_stats(result)
            
            self.logger.info(f"指令优化完成 - 置信度: {confidence_score:.2f}, 预期改进: {predicted_improvement:.2f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"指令优化失败: {e}")
            # 返回未优化的结果
            return InstructionOptimizationResult(
                original_instruction=instruction,
                optimized_instruction=instruction,
                optimization_types=[],
                confidence_score=0.0,
                applied_enhancements=[],
                predicted_improvement=0.0,
                optimization_reasoning=f"优化失败: {str(e)}",
                risk_assessment={'error': str(e)}
            )
    
    def get_optimization_priority(self) -> int:
        """获取优化器优先级"""
        return 10  # 中等优先级
    
    def _analyze_instruction_context(self, instruction: str, step: Dict[str, Any], 
                                   global_state: 'WorkflowState', context: Dict[str, Any]) -> Dict[str, Any]:
        """分析指令和上下文"""
        analysis = {
            'instruction_length': len(instruction),
            'instruction_complexity': self._assess_instruction_complexity(instruction),
            'has_state_info': "状态" in instruction.lower(),
            'has_context_info': any(word in instruction.lower() for word in ['上下文', '背景', '环境']),
            'has_error_handling': any(word in instruction.lower() for word in ['错误', '异常', '失败']),
            'step_type': step.get('type', 'unknown'),
            'step_complexity': self._assess_step_complexity(step),
            'state_richness': len(global_state.get_global_state()),
            'context_richness': len(str(context)),
            'historical_errors': self._get_historical_errors(context),
            'recent_failures': self._get_recent_failures(global_state),
            'dependency_info': self._analyze_dependencies(step, context),
        }
        
        return analysis
    
    def _determine_optimization_types(self, analysis: Dict[str, Any]) -> List[InstructionOptimizationType]:
        """确定需要应用的优化类型"""
        optimization_types = []
        
        # 上下文增强
        if (not analysis['has_context_info'] and analysis['state_richness'] > 50 
            and self.optimization_rules[InstructionOptimizationType.CONTEXT_ENHANCEMENT]):
            optimization_types.append(InstructionOptimizationType.CONTEXT_ENHANCEMENT)
        
        # 错误预防
        if ((analysis['historical_errors'] or analysis['recent_failures']) 
            and self.optimization_rules[InstructionOptimizationType.ERROR_PREVENTION]):
            optimization_types.append(InstructionOptimizationType.ERROR_PREVENTION)
        
        # 效率提升
        if (analysis['instruction_complexity'] < 0.3 and analysis['step_complexity'] > 0.7
            and self.optimization_rules[InstructionOptimizationType.EFFICIENCY_IMPROVEMENT]):
            optimization_types.append(InstructionOptimizationType.EFFICIENCY_IMPROVEMENT)
        
        # 清晰度优化
        if (analysis['instruction_length'] < 100 and analysis['step_complexity'] > 0.5
            and self.optimization_rules[InstructionOptimizationType.CLARITY_OPTIMIZATION]):
            optimization_types.append(InstructionOptimizationType.CLARITY_OPTIMIZATION)
        
        # 依赖关系感知
        if (analysis['dependency_info']['has_dependencies'] 
            and self.optimization_rules[InstructionOptimizationType.DEPENDENCY_AWARENESS]):
            optimization_types.append(InstructionOptimizationType.DEPENDENCY_AWARENESS)
        
        return optimization_types
    
    def _apply_optimizations(self, instruction: str, step: Dict[str, Any], 
                           global_state: 'WorkflowState', context: Dict[str, Any],
                           analysis: Dict[str, Any], optimization_types: List[InstructionOptimizationType]) -> str:
        """应用指令优化"""
        optimized_instruction = instruction
        
        for opt_type in optimization_types:
            if opt_type == InstructionOptimizationType.CONTEXT_ENHANCEMENT:
                optimized_instruction = self._enhance_context(optimized_instruction, global_state, context)
            elif opt_type == InstructionOptimizationType.ERROR_PREVENTION:
                optimized_instruction = self._add_error_prevention(optimized_instruction, analysis)
            elif opt_type == InstructionOptimizationType.EFFICIENCY_IMPROVEMENT:
                optimized_instruction = self._improve_efficiency(optimized_instruction, step, context)
            elif opt_type == InstructionOptimizationType.CLARITY_OPTIMIZATION:
                optimized_instruction = self._optimize_clarity(optimized_instruction, step)
            elif opt_type == InstructionOptimizationType.DEPENDENCY_AWARENESS:
                optimized_instruction = self._add_dependency_awareness(optimized_instruction, analysis)
        
        return optimized_instruction
    
    def _enhance_context(self, instruction: str, global_state: 'WorkflowState', context: Dict[str, Any]) -> str:
        """增强上下文信息"""
        state_content = global_state.get_global_state()
        
        # 提取关键状态信息
        key_info = []
        if "配置" in state_content.lower():
            key_info.append("📋 当前有相关配置信息可用")
        if "错误" in state_content.lower():
            key_info.append("⚠️ 注意之前出现的错误")
        if "完成" in state_content.lower():
            key_info.append("✅ 某些前置任务已完成")
        if "文件" in state_content.lower():
            key_info.append("📁 涉及文件操作相关的状态")
        
        if key_info:
            enhanced = f"{instruction}\n\n**🎯 重要上下文提示:**\n"
            for info in key_info:
                enhanced += f"- {info}\n"
            enhanced += f"\n**请结合上述上下文信息执行任务，确保与当前工作流状态保持一致。**"
            return enhanced
        
        return instruction
    
    def _add_error_prevention(self, instruction: str, analysis: Dict[str, Any]) -> str:
        """添加错误预防信息"""
        prevention_tips = []
        
        if analysis['historical_errors']:
            prevention_tips.append("🚨 **错误预防**: 之前执行中出现过错误，请特别注意错误处理")
        
        if analysis['recent_failures']:
            prevention_tips.append("🔧 **故障预防**: 近期有任务失败，建议验证前置条件")
        
        if prevention_tips:
            enhanced = f"{instruction}\n\n"
            for tip in prevention_tips:
                enhanced += f"{tip}\n"
            return enhanced
        
        return instruction
    
    def _improve_efficiency(self, instruction: str, step: Dict[str, Any], context: Dict[str, Any]) -> str:
        """提升效率"""
        efficiency_tips = []
        
        step_name = step.get('name', '').lower()
        if 'test' in step_name or 'verify' in step_name:
            efficiency_tips.append("⚡ **效率提示**: 这是测试/验证步骤，可以并行或批量执行")
        
        if 'install' in step_name or 'setup' in step_name:
            efficiency_tips.append("📦 **效率提示**: 安装/配置任务，建议检查缓存以避免重复工作")
        
        if efficiency_tips:
            enhanced = f"{instruction}\n\n"
            for tip in efficiency_tips:
                enhanced += f"{tip}\n"
            return enhanced
        
        return instruction
    
    def _optimize_clarity(self, instruction: str, step: Dict[str, Any]) -> str:
        """优化清晰度"""
        # 如果指令太短，添加更详细的说明
        if len(instruction) < 50:
            step_name = step.get('name', '未知步骤')
            step_desc = step.get('description', '')
            
            enhanced = f"**任务**: {instruction}\n\n"
            enhanced += f"**详细说明**: 执行'{step_name}'步骤"
            if step_desc:
                enhanced += f"，具体要求：{step_desc}"
            enhanced += f"\n\n**执行标准**: 请确保任务完成质量符合预期，并提供清晰的执行结果反馈。"
            
            return enhanced
        
        return instruction
    
    def _add_dependency_awareness(self, instruction: str, analysis: Dict[str, Any]) -> str:
        """添加依赖关系感知"""
        dep_info = analysis['dependency_info']
        
        if dep_info['has_dependencies']:
            enhanced = f"{instruction}\n\n"
            enhanced += f"**🔗 依赖关系提示**: 此任务依赖于其他步骤的完成状态"
            
            if dep_info['blocking_dependencies']:
                enhanced += f"，注意检查前置条件是否满足"
            
            enhanced += f"。请确保按照依赖顺序执行。"
            return enhanced
        
        return instruction
    
    def _assess_instruction_complexity(self, instruction: str) -> float:
        """评估指令复杂度 (0.0-1.0)"""
        complexity_factors = 0.0
        
        # 长度因素
        if len(instruction) > 200:
            complexity_factors += 0.3
        elif len(instruction) > 100:
            complexity_factors += 0.2
        
        # 技术术语因素
        tech_terms = ['API', 'database', 'config', 'install', 'deploy', 'test']
        tech_count = sum(1 for term in tech_terms if term.lower() in instruction.lower())
        complexity_factors += min(tech_count * 0.1, 0.3)
        
        # 条件语句因素
        conditions = ['if', 'when', 'unless', 'should', 'might']
        condition_count = sum(1 for cond in conditions if cond in instruction.lower())
        complexity_factors += min(condition_count * 0.1, 0.2)
        
        return min(complexity_factors, 1.0)
    
    def _assess_step_complexity(self, step: Dict[str, Any]) -> float:
        """评估步骤复杂度 (0.0-1.0)"""
        complexity = 0.0
        
        # 步骤名称复杂度
        step_name = step.get('name', '').lower()
        complex_words = ['configure', 'integrate', 'implement', 'deploy', 'optimize']
        if any(word in step_name for word in complex_words):
            complexity += 0.3
        
        # 步骤描述复杂度
        description = step.get('description', '')
        if len(description) > 100:
            complexity += 0.2
        
        # 预期输出复杂度
        expected_output = step.get('expected_output', '')
        if expected_output:
            complexity += 0.2
        
        # 依赖关系复杂度
        dependencies = step.get('dependencies', [])
        if len(dependencies) > 2:
            complexity += 0.3
        
        return min(complexity, 1.0)
    
    def _get_historical_errors(self, context: Dict[str, Any]) -> List[str]:
        """获取历史错误信息"""
        errors = []
        summary = context.get('summary', '')
        if '错误' in summary or '失败' in summary:
            errors.append('execution_error')
        return errors
    
    def _get_recent_failures(self, global_state: 'WorkflowState') -> List[str]:
        """获取近期失败信息"""
        failures = []
        state_content = global_state.get_global_state()
        if '失败' in state_content or '错误' in state_content:
            failures.append('state_failure')
        return failures
    
    def _analyze_dependencies(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """分析依赖关系"""
        dependencies = step.get('dependencies', [])
        
        return {
            'has_dependencies': len(dependencies) > 0,
            'dependency_count': len(dependencies),
            'blocking_dependencies': len(dependencies) > 2,
        }
    
    def _calculate_optimization_confidence(self, analysis: Dict[str, Any], 
                                         optimization_types: List[InstructionOptimizationType]) -> float:
        """计算优化置信度"""
        if not optimization_types:
            return 0.0
        
        confidence = 0.5  # 基础置信度
        
        # 基于分析结果调整置信度
        if analysis['state_richness'] > 100:
            confidence += 0.2
        if analysis['context_richness'] > 200:
            confidence += 0.1
        if analysis['instruction_complexity'] < 0.5:
            confidence += 0.1
        
        # 基于优化类型数量调整
        confidence += min(len(optimization_types) * 0.05, 0.2)
        
        return min(confidence, 1.0)
    
    def _predict_improvement(self, analysis: Dict[str, Any], 
                           optimization_types: List[InstructionOptimizationType]) -> float:
        """预测改进程度"""
        if not optimization_types:
            return 0.0
        
        improvement = 0.3  # 基础改进
        
        # 根据优化类型预测改进
        type_improvements = {
            InstructionOptimizationType.CONTEXT_ENHANCEMENT: 0.2,
            InstructionOptimizationType.ERROR_PREVENTION: 0.3,
            InstructionOptimizationType.EFFICIENCY_IMPROVEMENT: 0.15,
            InstructionOptimizationType.CLARITY_OPTIMIZATION: 0.1,
            InstructionOptimizationType.DEPENDENCY_AWARENESS: 0.1,
        }
        
        for opt_type in optimization_types:
            improvement += type_improvements.get(opt_type, 0.05)
        
        return min(improvement, 1.0)
    
    def _assess_optimization_risk(self, original: str, optimized: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """评估优化风险"""
        risk_factors = []
        risk_score = 0.0
        
        # 长度变化风险
        length_ratio = len(optimized) / len(original) if len(original) > 0 else 1.0
        if length_ratio > 3.0:
            risk_factors.append("指令长度显著增加")
            risk_score += 0.2
        
        # 复杂度风险
        if analysis['instruction_complexity'] > 0.7:
            risk_factors.append("原始指令已较复杂")
            risk_score += 0.1
        
        # 策略风险
        if self.strategy == OptimizationStrategy.AGGRESSIVE:
            risk_score += 0.1
        
        return {
            'risk_score': min(risk_score, 1.0),
            'risk_factors': risk_factors,
            'recommendation': 'proceed' if risk_score < 0.3 else 'caution' if risk_score < 0.6 else 'avoid'
        }
    
    def _generate_optimization_reasoning(self, optimization_types: List[InstructionOptimizationType], 
                                       analysis: Dict[str, Any]) -> str:
        """生成优化理由"""
        if not optimization_types:
            return "无需优化或无法确定优化方案"
        
        reasons = []
        
        type_reasons = {
            InstructionOptimizationType.CONTEXT_ENHANCEMENT: "丰富的状态信息可用于增强上下文",
            InstructionOptimizationType.ERROR_PREVENTION: "历史错误模式提示需要预防措施",
            InstructionOptimizationType.EFFICIENCY_IMPROVEMENT: "可以通过优化提升执行效率",
            InstructionOptimizationType.CLARITY_OPTIMIZATION: "指令过于简洁，需要澄清",
            InstructionOptimizationType.DEPENDENCY_AWARENESS: "存在依赖关系需要明确",
        }
        
        for opt_type in optimization_types:
            if opt_type in type_reasons:
                reasons.append(type_reasons[opt_type])
        
        return "；".join(reasons) + "。"
    
    def _get_applied_enhancements(self, optimization_types: List[InstructionOptimizationType]) -> List[str]:
        """获取应用的增强功能列表"""
        enhancements = []
        
        enhancement_names = {
            InstructionOptimizationType.CONTEXT_ENHANCEMENT: "上下文信息增强",
            InstructionOptimizationType.ERROR_PREVENTION: "错误预防提示",
            InstructionOptimizationType.EFFICIENCY_IMPROVEMENT: "效率提升建议",
            InstructionOptimizationType.CLARITY_OPTIMIZATION: "清晰度优化",
            InstructionOptimizationType.DEPENDENCY_AWARENESS: "依赖关系提示",
        }
        
        for opt_type in optimization_types:
            if opt_type in enhancement_names:
                enhancements.append(enhancement_names[opt_type])
        
        return enhancements
    
    def _update_optimization_stats(self, result: InstructionOptimizationResult) -> None:
        """更新优化统计"""
        # 如果有优化类型，认为是成功的优化
        if result.optimization_types:
            self.optimization_stats['successful_optimizations'] += 1
        
        # 更新优化类型使用统计
        for opt_type in result.optimization_types:
            type_name = opt_type.value
            self.optimization_stats['optimization_types_used'][type_name] = \
                self.optimization_stats['optimization_types_used'].get(type_name, 0) + 1
        
        # 更新平均置信度
        total_opts = self.optimization_stats['total_optimizations']
        current_avg_conf = self.optimization_stats['average_confidence']
        self.optimization_stats['average_confidence'] = \
            ((current_avg_conf * (total_opts - 1)) + result.confidence_score) / total_opts
        
        # 更新平均改进度
        current_avg_imp = self.optimization_stats['average_improvement']
        self.optimization_stats['average_improvement'] = \
            ((current_avg_imp * (total_opts - 1)) + result.predicted_improvement) / total_opts
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        total = self.optimization_stats['total_optimizations']
        successful = self.optimization_stats['successful_optimizations']
        
        return {
            'total_optimizations': total,
            'successful_optimizations': successful,
            'success_rate': successful / total if total > 0 else 0.0,
            'optimization_types_used': self.optimization_stats['optimization_types_used'].copy(),
            'average_confidence': self.optimization_stats['average_confidence'],
            'average_improvement': self.optimization_stats['average_improvement']
        }
    
    def reset_optimization_statistics(self) -> None:
        """重置优化统计"""
        self.optimization_stats = {
            'total_optimizations': 0,
            'successful_optimizations': 0,
            'optimization_types_used': {},
            'average_confidence': 0.0,
            'average_improvement': 0.0
        }
        
        self.logger.info("指令优化统计信息已重置")


class StateCondition:
    """状态条件类 - 表示一个可评估的状态条件"""
    
    def __init__(self, state_path: str, operator: ConditionOperator, 
                 expected_value: Any, description: str = ""):
        """
        初始化状态条件
        
        Args:
            state_path: 状态路径，如 'data.user_approval' 或直接的状态键
            operator: 条件操作符
            expected_value: 预期值
            description: 条件描述
        """
        self.state_path = state_path
        self.operator = operator
        self.expected_value = expected_value
        self.description = description
    
    def evaluate(self, global_state: 'WorkflowState') -> Tuple[bool, Dict[str, Any]]:
        """
        评估条件
        
        Args:
            global_state: 全局工作流状态
            
        Returns:
            (是否满足条件, 评估详情)
        """
        try:
            # 获取状态值
            state_value = self._extract_state_value(global_state)
            
            # 执行条件评估
            result = self._evaluate_condition(state_value)
            
            evaluation_details = {
                'state_path': self.state_path,
                'operator': self.operator.value,
                'expected_value': self.expected_value,
                'actual_value': state_value,
                'result': result,
                'description': self.description
            }
            
            return result, evaluation_details
            
        except Exception as e:
            logger.error(f"状态条件评估失败: {e}")
            return False, {
                'state_path': self.state_path,
                'operator': self.operator.value,
                'error': str(e),
                'result': False
            }
    
    def _extract_state_value(self, global_state: 'WorkflowState') -> Any:
        """从全局状态中提取值"""
        state_content = global_state.get_global_state()
        
        if not state_content:
            return None
        
        # 如果是简单的键查找
        if '.' not in self.state_path:
            # 尝试直接匹配状态内容中的键值对
            import re
            patterns = [
                rf'{re.escape(self.state_path)}\s*[:=]\s*([^\n,;]+)',  # key: value 或 key = value
                rf'\[{re.escape(self.state_path)}\]\s*([^\n,;]+)',    # [key] value
                rf'{re.escape(self.state_path)}\s*:\s*([^\n,;]+)'     # key: value
            ]
            
            for pattern in patterns:
                match = re.search(pattern, state_content, re.IGNORECASE)
                if match:
                    value_str = match.group(1).strip().strip('"\'')
                    return self._parse_value(value_str)
        
        # 复杂路径解析（如 data.user.approval）
        path_parts = self.state_path.split('.')
        
        # 尝试从状态内容中解析嵌套结构
        import json
        try:
            # 尝试解析为JSON
            state_data = json.loads(state_content)
            value = state_data
            for part in path_parts:
                value = value.get(part) if isinstance(value, dict) else None
                if value is None:
                    break
            return value
        except:
            pass
        
        # 回退：在状态内容中查找文本模式
        for part in path_parts:
            if part.lower() in state_content.lower():
                # 简化处理：如果路径部分出现在状态中，返回True
                return True
        
        return None
    
    def _parse_value(self, value_str: str) -> Any:
        """解析字符串值为适当的类型"""
        if not value_str:
            return None
        
        value_lower = value_str.lower()
        
        # 布尔值
        if value_lower in ['true', 'yes', '是', '已完成', 'completed', 'success']:
            return True
        elif value_lower in ['false', 'no', '否', '未完成', 'pending', 'failed']:
            return False
        
        # 数字
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass
        
        # 字符串（保持原样）
        return value_str
    
    def _evaluate_condition(self, actual_value: Any) -> bool:
        """评估具体的条件"""
        if actual_value is None:
            return self.operator in [ConditionOperator.IS_EMPTY, ConditionOperator.NOT_EQUALS]
        
        if self.operator == ConditionOperator.EQUALS:
            return actual_value == self.expected_value
        elif self.operator == ConditionOperator.NOT_EQUALS:
            return actual_value != self.expected_value
        elif self.operator == ConditionOperator.GREATER_THAN:
            return self._safe_compare(actual_value, self.expected_value, lambda a, b: a > b)
        elif self.operator == ConditionOperator.LESS_THAN:
            return self._safe_compare(actual_value, self.expected_value, lambda a, b: a < b)
        elif self.operator == ConditionOperator.GREATER_EQUAL:
            return self._safe_compare(actual_value, self.expected_value, lambda a, b: a >= b)
        elif self.operator == ConditionOperator.LESS_EQUAL:
            return self._safe_compare(actual_value, self.expected_value, lambda a, b: a <= b)
        elif self.operator == ConditionOperator.CONTAINS:
            return self._safe_contains(actual_value, self.expected_value)
        elif self.operator == ConditionOperator.NOT_CONTAINS:
            return not self._safe_contains(actual_value, self.expected_value)
        elif self.operator == ConditionOperator.STARTS_WITH:
            return str(actual_value).startswith(str(self.expected_value))
        elif self.operator == ConditionOperator.ENDS_WITH:
            return str(actual_value).endswith(str(self.expected_value))
        elif self.operator == ConditionOperator.IN:
            return actual_value in self.expected_value if hasattr(self.expected_value, '__contains__') else False
        elif self.operator == ConditionOperator.NOT_IN:
            return actual_value not in self.expected_value if hasattr(self.expected_value, '__contains__') else True
        elif self.operator == ConditionOperator.IS_EMPTY:
            return not actual_value or (isinstance(actual_value, str) and not actual_value.strip())
        elif self.operator == ConditionOperator.IS_NOT_EMPTY:
            return bool(actual_value) and not (isinstance(actual_value, str) and not actual_value.strip())
        elif self.operator == ConditionOperator.REGEX_MATCH:
            import re
            try:
                return bool(re.search(str(self.expected_value), str(actual_value)))
            except:
                return False
        
        return False
    
    def _safe_compare(self, a: Any, b: Any, comparison_func) -> bool:
        """安全的数值比较"""
        try:
            # 尝试转换为数字进行比较
            if isinstance(a, str) and isinstance(b, str):
                try:
                    a_num = float(a)
                    b_num = float(b)
                    return comparison_func(a_num, b_num)
                except ValueError:
                    pass
            
            return comparison_func(a, b)
        except (TypeError, ValueError):
            return False
    
    def _safe_contains(self, container: Any, item: Any) -> bool:
        """安全的包含检查"""
        try:
            if hasattr(container, '__contains__'):
                return item in container
            else:
                return str(item) in str(container)
        except:
            return False


class DecisionNode:
    """决策节点类 - 基于状态进行条件决策"""
    
    def __init__(self, node_id: str, node_type: DecisionNodeType, 
                 description: str = ""):
        """
        初始化决策节点
        
        Args:
            node_id: 节点ID
            node_type: 节点类型
            description: 节点描述
        """
        self.node_id = node_id
        self.node_type = node_type
        self.description = description
        self.conditions: List[StateCondition] = []
        self.decision_paths: Dict[str, str] = {}  # 条件结果 -> 下一步ID
        self.default_path: Optional[str] = None
        self.logic_operator = "AND"  # AND 或 OR
    
    def add_condition(self, condition: StateCondition) -> None:
        """添加条件"""
        self.conditions.append(condition)
    
    def add_decision_path(self, condition_result: str, next_step_id: str) -> None:
        """添加决策路径"""
        self.decision_paths[condition_result] = next_step_id
    
    def set_default_path(self, next_step_id: str) -> None:
        """设置默认路径"""
        self.default_path = next_step_id
    
    def set_logic_operator(self, operator: str) -> None:
        """设置逻辑操作符（AND/OR）"""
        if operator.upper() in ["AND", "OR"]:
            self.logic_operator = operator.upper()
    
    def evaluate_decision(self, global_state: 'WorkflowState') -> DecisionResult:
        """
        评估决策
        
        Args:
            global_state: 全局工作流状态
            
        Returns:
            决策结果
        """
        try:
            evaluated_conditions = []
            state_variables_used = []
            
            # 评估所有条件
            condition_results = []
            for condition in self.conditions:
                result, details = condition.evaluate(global_state)
                condition_results.append(result)
                evaluated_conditions.append(details)
                state_variables_used.append(condition.state_path)
            
            # 根据逻辑操作符组合结果
            if self.logic_operator == "AND":
                overall_result = all(condition_results) if condition_results else False
            else:  # OR
                overall_result = any(condition_results) if condition_results else False
            
            # 确定下一步
            next_step_id = None
            decision_reason = ""
            confidence = 0.0
            
            if self.node_type == DecisionNodeType.CONDITIONAL:
                if overall_result:
                    next_step_id = self.decision_paths.get("true", self.default_path)
                    decision_reason = f"条件评估为真，执行真分支"
                    confidence = 0.9
                else:
                    next_step_id = self.decision_paths.get("false", self.default_path)
                    decision_reason = f"条件评估为假，执行假分支"
                    confidence = 0.9
            
            elif self.node_type == DecisionNodeType.VALIDATION:
                if overall_result:
                    next_step_id = self.decision_paths.get("valid", self.default_path)
                    decision_reason = f"验证通过，继续执行"
                    confidence = 0.95
                else:
                    next_step_id = self.decision_paths.get("invalid", self.default_path)
                    decision_reason = f"验证失败，执行错误处理"
                    confidence = 0.95
            
            elif self.node_type == DecisionNodeType.SWITCH:
                # 对于switch类型，查找第一个为true的条件对应的路径
                for i, result in enumerate(condition_results):
                    if result:
                        condition_key = f"case_{i}"
                        next_step_id = self.decision_paths.get(condition_key, self.default_path)
                        decision_reason = f"匹配条件 {i+1}，执行对应分支"
                        confidence = 0.85
                        break
                
                if next_step_id is None:
                    next_step_id = self.default_path
                    decision_reason = f"无匹配条件，执行默认分支"
                    confidence = 0.8
            
            else:
                # 其他类型使用基本的条件逻辑
                next_step_id = self.decision_paths.get("true" if overall_result else "false", self.default_path)
                decision_reason = f"基于{self.node_type.value}类型的决策结果"
                confidence = 0.8
            
            # 如果没有找到合适的路径，使用默认路径
            if next_step_id is None:
                next_step_id = self.default_path
                decision_reason += " (使用默认路径)"
                confidence = max(0.5, confidence - 0.2)
            
            return DecisionResult(
                next_step_id=next_step_id,
                decision_made=next_step_id is not None,
                decision_reason=decision_reason,
                evaluated_conditions=evaluated_conditions,
                state_variables_used=state_variables_used,
                confidence=confidence,
                additional_actions=[]
            )
            
        except Exception as e:
            logger.error(f"决策节点评估失败: {e}")
            return DecisionResult(
                next_step_id=self.default_path,
                decision_made=False,
                decision_reason=f"决策评估出错: {str(e)}",
                evaluated_conditions=[],
                state_variables_used=[],
                confidence=0.0,
                additional_actions=["检查决策节点配置", "验证状态数据格式"]
            )


class StateAwareDecisionManager:
    """状态感知决策管理器"""
    
    def __init__(self):
        """初始化决策管理器"""
        self.decision_nodes: Dict[str, DecisionNode] = {}
        self.decision_statistics = {
            'total_decisions': 0,
            'successful_decisions': 0,
            'failed_decisions': 0,
            'average_confidence': 0.0,
            'decision_types_used': {},
            'most_used_variables': {}
        }
    
    def register_decision_node(self, node: DecisionNode) -> None:
        """注册决策节点"""
        self.decision_nodes[node.node_id] = node
        logger.info(f"决策节点已注册: {node.node_id} ({node.node_type.value})")
    
    def create_conditional_node(self, node_id: str, condition: StateCondition, 
                              true_step: str, false_step: str, description: str = "") -> DecisionNode:
        """创建条件决策节点的快捷方法"""
        node = DecisionNode(node_id, DecisionNodeType.CONDITIONAL, description)
        node.add_condition(condition)
        node.add_decision_path("true", true_step)
        node.add_decision_path("false", false_step)
        self.register_decision_node(node)
        return node
    
    def create_validation_node(self, node_id: str, condition: StateCondition,
                             valid_step: str, invalid_step: str, description: str = "") -> DecisionNode:
        """创建验证决策节点的快捷方法"""
        node = DecisionNode(node_id, DecisionNodeType.VALIDATION, description)
        node.add_condition(condition)
        node.add_decision_path("valid", valid_step)
        node.add_decision_path("invalid", invalid_step)
        self.register_decision_node(node)
        return node
    
    def evaluate_decision(self, node_id: str, global_state: 'WorkflowState') -> DecisionResult:
        """
        评估指定决策节点
        
        Args:
            node_id: 决策节点ID
            global_state: 全局工作流状态
            
        Returns:
            决策结果
        """
        if node_id not in self.decision_nodes:
            logger.error(f"决策节点不存在: {node_id}")
            return DecisionResult(
                next_step_id=None,
                decision_made=False,
                decision_reason=f"决策节点 {node_id} 不存在",
                evaluated_conditions=[],
                state_variables_used=[],
                confidence=0.0,
                additional_actions=["检查决策节点配置"]
            )
        
        node = self.decision_nodes[node_id]
        result = node.evaluate_decision(global_state)
        
        # 更新统计信息
        self._update_decision_statistics(node, result)
        
        logger.info(f"决策节点 {node_id} 评估完成: {result.next_step_id} (置信度: {result.confidence:.2f})")
        
        return result
    
    def list_decision_nodes(self) -> List[Dict[str, Any]]:
        """获取所有决策节点的信息"""
        nodes_info = []
        for node_id, node in self.decision_nodes.items():
            nodes_info.append({
                'node_id': node_id,
                'node_type': node.node_type.value,
                'description': node.description,
                'condition_count': len(node.conditions),
                'decision_paths': node.decision_paths,
                'default_path': node.default_path,
                'logic_operator': node.logic_operator
            })
        return nodes_info
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """获取决策统计信息"""
        return self.decision_statistics.copy()
    
    def reset_decision_statistics(self) -> None:
        """重置决策统计信息"""
        self.decision_statistics = {
            'total_decisions': 0,
            'successful_decisions': 0,
            'failed_decisions': 0,
            'average_confidence': 0.0,
            'decision_types_used': {},
            'most_used_variables': {}
        }
        logger.info("决策统计信息已重置")
    
    def _update_decision_statistics(self, node: DecisionNode, result: DecisionResult) -> None:
        """更新决策统计信息"""
        self.decision_statistics['total_decisions'] += 1
        
        if result.decision_made:
            self.decision_statistics['successful_decisions'] += 1
        else:
            self.decision_statistics['failed_decisions'] += 1
        
        # 更新平均置信度
        total = self.decision_statistics['total_decisions']
        current_avg = self.decision_statistics['average_confidence']
        new_avg = (current_avg * (total - 1) + result.confidence) / total
        self.decision_statistics['average_confidence'] = new_avg
        
        # 更新节点类型使用统计
        node_type = node.node_type.value
        if node_type not in self.decision_statistics['decision_types_used']:
            self.decision_statistics['decision_types_used'][node_type] = 0
        self.decision_statistics['decision_types_used'][node_type] += 1
        
        # 更新变量使用统计
        for var in result.state_variables_used:
            if var not in self.decision_statistics['most_used_variables']:
                self.decision_statistics['most_used_variables'][var] = 0
            self.decision_statistics['most_used_variables'][var] += 1


class WorkflowErrorType(Enum):
    """工作流错误类型枚举"""
    API_ERROR = "api_error"                       # API调用错误
    TIMEOUT_ERROR = "timeout_error"               # 超时错误
    VALIDATION_ERROR = "validation_error"         # 验证错误
    FILE_ERROR = "file_error"                     # 文件操作错误
    DATABASE_ERROR = "database_error"             # 数据库错误
    NETWORK_ERROR = "network_error"               # 网络错误
    AUTHENTICATION_ERROR = "authentication_error" # 认证错误
    PERMISSION_ERROR = "permission_error"         # 权限错误
    CONFIGURATION_ERROR = "configuration_error"   # 配置错误
    AGENT_EXECUTION_ERROR = "agent_execution_error" # 代理执行错误
    UNKNOWN_ERROR = "unknown_error"               # 未知错误


class WorkflowErrorContext:
    """工作流错误上下文"""
    
    def __init__(self, error: Exception, error_type: WorkflowErrorType, step: Dict[str, Any], 
                 global_state: 'WorkflowState', execution_context: Dict[str, Any] = None):
        self.error = error
        self.error_type = error_type
        self.step = step
        self.global_state = global_state
        self.execution_context = execution_context or {}
        self.timestamp = dt.now()
        
        # 提取错误详细信息
        self.error_message = str(error)
        self.error_class = error.__class__.__name__
        self.step_id = step.get('id', 'unknown')
        self.step_name = step.get('name', 'Unknown Step')
        self.agent_name = step.get('agent_name', 'unknown')
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'error_type': self.error_type.value,
            'error_class': self.error_class,
            'error_message': self.error_message,
            'step_id': self.step_id,
            'step_name': self.step_name,
            'agent_name': self.agent_name,
            'timestamp': self.timestamp.isoformat(),
            'global_state_summary': self.global_state.get_state_summary() if self.global_state else 'N/A',
            'execution_context': self.execution_context
        }


class StateAwareErrorHandler(ABC):
    """状态感知错误处理器的抽象基类"""
    
    @abstractmethod
    def can_handle(self, error_context: WorkflowErrorContext) -> bool:
        """
        判断是否能处理指定的错误上下文
        
        Args:
            error_context: 错误上下文
            
        Returns:
            bool: 是否能处理
        """
        pass
    
    @abstractmethod
    def handle_error(self, error_context: WorkflowErrorContext) -> Dict[str, Any]:
        """
        处理错误
        
        Args:
            error_context: 错误上下文
            
        Returns:
            处理结果字典，包含recovery_action, new_state, retry_possible等
        """
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """
        获取处理器优先级
        
        Returns:
            int: 优先级数字，数字越小优先级越高
        """
        pass


class GenericErrorHandler(StateAwareErrorHandler):
    """通用错误处理器"""
    
    def __init__(self):
        self.handled_errors = []
        self.recovery_strategies = {
            WorkflowErrorType.API_ERROR: self._handle_api_error,
            WorkflowErrorType.TIMEOUT_ERROR: self._handle_timeout_error,
            WorkflowErrorType.VALIDATION_ERROR: self._handle_validation_error,
            WorkflowErrorType.FILE_ERROR: self._handle_file_error,
            WorkflowErrorType.DATABASE_ERROR: self._handle_database_error,
            WorkflowErrorType.NETWORK_ERROR: self._handle_network_error,
            WorkflowErrorType.AUTHENTICATION_ERROR: self._handle_auth_error,
            WorkflowErrorType.PERMISSION_ERROR: self._handle_permission_error,
            WorkflowErrorType.CONFIGURATION_ERROR: self._handle_config_error,
            WorkflowErrorType.AGENT_EXECUTION_ERROR: self._handle_agent_error,
            WorkflowErrorType.UNKNOWN_ERROR: self._handle_unknown_error
        }
    
    def can_handle(self, error_context: WorkflowErrorContext) -> bool:
        """通用处理器可以处理所有类型的错误"""
        return True
    
    def get_priority(self) -> int:
        """通用处理器优先级最低"""
        return 1000
    
    def handle_error(self, error_context: WorkflowErrorContext) -> Dict[str, Any]:
        """处理错误"""
        # 记录错误
        self.handled_errors.append(error_context)
        
        # 根据错误类型选择处理策略
        handler_func = self.recovery_strategies.get(
            error_context.error_type, 
            self._handle_unknown_error
        )
        
        try:
            result = handler_func(error_context)
            
            # 标记错误已被处理
            result['handled'] = True
            result['error_type'] = error_context.error_type.value
            result['handler'] = self.__class__.__name__
            result['message'] = f"错误已被 {self.__class__.__name__} 处理: {error_context.error_type.value}"
            
            # 更新全局状态
            if result.get('new_state'):
                error_context.global_state.set_global_state(
                    result['new_state'], 
                    f"error_handler_{error_context.error_type.value}"
                )
            
            return result
            
        except Exception as handler_error:
            logger.error(f"错误处理器自身发生错误: {handler_error}")
            return self._create_fallback_result(error_context, handler_error)
    
    def _handle_api_error(self, error_context: WorkflowErrorContext) -> Dict[str, Any]:
        """处理API错误"""
        current_state = error_context.global_state.get_global_state()
        
        # 分析API错误
        error_msg = error_context.error_message.lower()
        if 'timeout' in error_msg or 'connection' in error_msg:
            recovery_action = 'retry_with_backoff'
            new_state = f"{current_state}\\n[错误恢复] API连接问题，建议检查网络连接后重试。"
        elif 'unauthorized' in error_msg or '401' in error_msg:
            recovery_action = 'refresh_auth'
            new_state = f"{current_state}\\n[错误恢复] API认证失败，需要刷新认证令牌。"
        elif 'rate limit' in error_msg or '429' in error_msg:
            recovery_action = 'wait_and_retry'
            new_state = f"{current_state}\\n[错误恢复] API调用频率限制，需要等待后重试。"
        else:
            recovery_action = 'check_api_params'
            new_state = f"{current_state}\\n[错误恢复] API调用参数可能有误，需要检查请求参数。"
        
        return {
            'recovery_action': recovery_action,
            'new_state': new_state,
            'retry_possible': True,
            'suggested_delay': 5.0,
            'error_analysis': f"API错误分析: {error_context.error_message}"
        }
    
    def _handle_timeout_error(self, error_context: WorkflowErrorContext) -> Dict[str, Any]:
        """处理超时错误"""
        current_state = error_context.global_state.get_global_state()
        
        return {
            'recovery_action': 'retry_with_longer_timeout',
            'new_state': f"{current_state}\\n[错误恢复] 操作超时，建议增加超时时间后重试。",
            'retry_possible': True,
            'suggested_delay': 10.0,
            'timeout_multiplier': 2.0,
            'error_analysis': f"超时错误: {error_context.step_name}执行超时"
        }
    
    def _handle_validation_error(self, error_context: WorkflowErrorContext) -> Dict[str, Any]:
        """处理验证错误"""
        current_state = error_context.global_state.get_global_state()
        
        return {
            'recovery_action': 'fix_input_validation',
            'new_state': f"{current_state}\\n[错误恢复] 输入验证失败: {error_context.error_message}。需要检查输入参数格式。",
            'retry_possible': True,
            'suggested_delay': 0.0,
            'error_analysis': f"验证错误: 输入参数不符合要求"
        }
    
    def _handle_file_error(self, error_context: WorkflowErrorContext) -> Dict[str, Any]:
        """处理文件错误"""
        current_state = error_context.global_state.get_global_state()
        error_msg = error_context.error_message.lower()
        
        if 'not found' in error_msg or 'no such file' in error_msg:
            recovery_action = 'create_missing_file'
            analysis = "文件不存在"
        elif 'permission denied' in error_msg:
            recovery_action = 'fix_file_permissions'
            analysis = "文件权限不足"
        elif 'disk full' in error_msg or 'no space' in error_msg:
            recovery_action = 'clean_disk_space'
            analysis = "磁盘空间不足"
        else:
            recovery_action = 'check_file_system'
            analysis = "文件系统错误"
        
        return {
            'recovery_action': recovery_action,
            'new_state': f"{current_state}\\n[错误恢复] 文件操作失败: {analysis}。{error_context.error_message}",
            'retry_possible': True,
            'suggested_delay': 2.0,
            'error_analysis': f"文件错误: {analysis}"
        }
    
    def _handle_database_error(self, error_context: WorkflowErrorContext) -> Dict[str, Any]:
        """处理数据库错误"""
        current_state = error_context.global_state.get_global_state()
        
        return {
            'recovery_action': 'check_database_connection',
            'new_state': f"{current_state}\\n[错误恢复] 数据库操作失败: {error_context.error_message}。检查数据库连接和权限。",
            'retry_possible': True,
            'suggested_delay': 3.0,
            'error_analysis': f"数据库错误: 连接或查询失败"
        }
    
    def _handle_network_error(self, error_context: WorkflowErrorContext) -> Dict[str, Any]:
        """处理网络错误"""
        current_state = error_context.global_state.get_global_state()
        
        return {
            'recovery_action': 'retry_with_backoff',
            'new_state': f"{current_state}\\n[错误恢复] 网络连接失败，建议检查网络状态后重试。",
            'retry_possible': True,
            'suggested_delay': 8.0,
            'error_analysis': f"网络错误: {error_context.error_message}"
        }
    
    def _handle_auth_error(self, error_context: WorkflowErrorContext) -> Dict[str, Any]:
        """处理认证错误"""
        current_state = error_context.global_state.get_global_state()
        
        return {
            'recovery_action': 'refresh_credentials',
            'new_state': f"{current_state}\\n[错误恢复] 认证失败，需要刷新或重新获取认证凭据。",
            'retry_possible': True,
            'suggested_delay': 1.0,
            'error_analysis': f"认证错误: 凭据无效或过期"
        }
    
    def _handle_permission_error(self, error_context: WorkflowErrorContext) -> Dict[str, Any]:
        """处理权限错误"""
        current_state = error_context.global_state.get_global_state()
        
        return {
            'recovery_action': 'escalate_permissions',
            'new_state': f"{current_state}\\n[错误恢复] 权限不足，需要提升权限或联系管理员。",
            'retry_possible': False,
            'suggested_delay': 0.0,
            'error_analysis': f"权限错误: 操作被拒绝"
        }
    
    def _handle_config_error(self, error_context: WorkflowErrorContext) -> Dict[str, Any]:
        """处理配置错误"""
        current_state = error_context.global_state.get_global_state()
        
        return {
            'recovery_action': 'fix_configuration',
            'new_state': f"{current_state}\\n[错误恢复] 配置错误: {error_context.error_message}。需要检查和修正配置文件。",
            'retry_possible': True,
            'suggested_delay': 1.0,
            'error_analysis': f"配置错误: 配置参数无效"
        }
    
    def _handle_agent_error(self, error_context: WorkflowErrorContext) -> Dict[str, Any]:
        """处理代理执行错误"""
        current_state = error_context.global_state.get_global_state()
        
        return {
            'recovery_action': 'retry_with_different_agent',
            'new_state': f"{current_state}\\n[错误恢复] 代理执行失败: {error_context.agent_name}无法完成任务。考虑使用备用代理或调整任务参数。",
            'retry_possible': True,
            'suggested_delay': 2.0,
            'error_analysis': f"代理错误: {error_context.agent_name}执行失败"
        }
    
    def _handle_unknown_error(self, error_context: WorkflowErrorContext) -> Dict[str, Any]:
        """处理未知错误"""
        current_state = error_context.global_state.get_global_state()
        
        return {
            'recovery_action': 'manual_intervention',
            'new_state': f"{current_state}\\n[错误恢复] 未知错误: {error_context.error_message}。需要人工干预进行诊断。",
            'retry_possible': False,
            'suggested_delay': 0.0,
            'error_analysis': f"未知错误: {error_context.error_class}"
        }
    
    def _create_fallback_result(self, error_context: WorkflowErrorContext, handler_error: Exception) -> Dict[str, Any]:
        """创建回退结果"""
        current_state = error_context.global_state.get_global_state()
        
        return {
            'recovery_action': 'error_handler_failed',
            'new_state': f"{current_state}\\n[系统错误] 错误处理器失败: {str(handler_error)}。原始错误: {error_context.error_message}",
            'retry_possible': False,
            'suggested_delay': 0.0,
            'error_analysis': f"错误处理器故障: {str(handler_error)}"
        }
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误处理统计信息"""
        if not self.handled_errors:
            return {'total_errors': 0}
        
        error_types = {}
        for error_ctx in self.handled_errors:
            error_type = error_ctx.error_type.value
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.handled_errors),
            'error_types': error_types,
            'recent_errors': [ctx.to_dict() for ctx in self.handled_errors[-5:]]  # 最近5个错误
        }


class WorkflowErrorDispatcher:
    """工作流错误分发器"""
    
    def __init__(self):
        self.error_handlers: List[StateAwareErrorHandler] = []
        self.error_type_mapping = {
            # Exception类名到WorkflowErrorType的映射
            'ConnectionError': WorkflowErrorType.NETWORK_ERROR,
            'TimeoutError': WorkflowErrorType.TIMEOUT_ERROR,
            'Timeout': WorkflowErrorType.TIMEOUT_ERROR,
            'HTTPError': WorkflowErrorType.API_ERROR,
            'RequestException': WorkflowErrorType.API_ERROR,
            'FileNotFoundError': WorkflowErrorType.FILE_ERROR,
            'PermissionError': WorkflowErrorType.PERMISSION_ERROR,
            'ValidationError': WorkflowErrorType.VALIDATION_ERROR,
            'ValueError': WorkflowErrorType.VALIDATION_ERROR,
            'AuthenticationError': WorkflowErrorType.AUTHENTICATION_ERROR,
            'DatabaseError': WorkflowErrorType.DATABASE_ERROR,
            'ConfigurationError': WorkflowErrorType.CONFIGURATION_ERROR,
        }
        
        # 注册默认的通用错误处理器
        self.register_handler(GenericErrorHandler())
    
    def register_handler(self, handler: StateAwareErrorHandler) -> None:
        """注册错误处理器"""
        self.error_handlers.append(handler)
        # 按优先级排序
        self.error_handlers.sort(key=lambda h: h.get_priority())
    
    def classify_error(self, error: Exception) -> WorkflowErrorType:
        """分类错误类型"""
        error_class_name = error.__class__.__name__
        
        # 首先尝试直接匹配
        if error_class_name in self.error_type_mapping:
            return self.error_type_mapping[error_class_name]
        
        # 基于错误消息进行模糊匹配
        error_msg = str(error).lower()
        
        if any(keyword in error_msg for keyword in ['timeout', 'timed out']):
            return WorkflowErrorType.TIMEOUT_ERROR
        elif any(keyword in error_msg for keyword in ['connection', 'network', 'unreachable']):
            return WorkflowErrorType.NETWORK_ERROR
        elif any(keyword in error_msg for keyword in ['unauthorized', 'authentication', 'login']):
            return WorkflowErrorType.AUTHENTICATION_ERROR
        elif any(keyword in error_msg for keyword in ['permission denied', 'forbidden', 'access denied']):
            return WorkflowErrorType.PERMISSION_ERROR
        elif any(keyword in error_msg for keyword in ['file not found', 'no such file']):
            return WorkflowErrorType.FILE_ERROR
        elif any(keyword in error_msg for keyword in ['database', 'sql', 'query']):
            return WorkflowErrorType.DATABASE_ERROR
        elif any(keyword in error_msg for keyword in ['api', 'http', 'rest']):
            return WorkflowErrorType.API_ERROR
        elif any(keyword in error_msg for keyword in ['config', 'configuration', 'setting']):
            return WorkflowErrorType.CONFIGURATION_ERROR
        elif any(keyword in error_msg for keyword in ['validation', 'invalid', 'format']):
            return WorkflowErrorType.VALIDATION_ERROR
        else:
            return WorkflowErrorType.UNKNOWN_ERROR
    
    def dispatch_error(self, error: Exception, step: Dict[str, Any], 
                      global_state: 'WorkflowState', execution_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """分发错误到适当的处理器"""
        # 分类错误
        error_type = self.classify_error(error)
        
        # 创建错误上下文
        error_context = WorkflowErrorContext(
            error=error,
            error_type=error_type,
            step=step,
            global_state=global_state,
            execution_context=execution_context
        )
        
        # 寻找能处理此错误的处理器
        for handler in self.error_handlers:
            if handler.can_handle(error_context):
                try:
                    result = handler.handle_error(error_context)
                    logger.info(f"错误已被 {handler.__class__.__name__} 处理: {error_type.value}")
                    return result
                except Exception as handler_error:
                    logger.error(f"错误处理器 {handler.__class__.__name__} 执行失败: {handler_error}")
                    continue
        
        # 如果没有处理器能处理，返回默认结果
        logger.error(f"没有找到合适的错误处理器处理错误: {error_type.value}")
        return {
            'handled': False,
            'error_type': error_type.value,
            'handler': 'no_handler',
            'message': f"无法处理的错误: {error_type.value}",
            'recovery_action': 'no_handler_available',
            'new_state': f"{global_state.get_global_state()}\\n[系统错误] 无法处理的错误: {str(error)}",
            'retry_possible': False,
            'suggested_delay': 0.0,
            'error_analysis': f"无处理器: {error.__class__.__name__}"
        }


class FallbackStrategy(Enum):
    """回退策略枚举"""
    RETRY_SIMPLIFIED = "retry_simplified"          # 使用简化提示重试
    TEMPLATE_BASED = "template_based"              # 使用模板化默认状态
    RULE_BASED = "rule_based"                      # 使用基于规则的逻辑
    NOTIFY_OPERATOR = "notify_operator"            # 通知人工操作员
    MINIMAL_STATE = "minimal_state"                # 生成最小状态描述


class FallbackStateGenerator:
    """回退状态生成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.FallbackStateGenerator")
        
        # 预定义的状态模板
        self.success_templates = [
            "步骤 '{step_name}' 执行完成",
            "任务处理成功，已完成相关操作",
            "系统运行正常，当前操作已完成"
        ]
        
        self.error_templates = [
            "步骤 '{step_name}' 执行过程中遇到问题",
            "处理任务时发生错误，需要关注",
            "系统遇到异常情况，正在处理中"
        ]
        
        self.progress_templates = [
            "正在执行步骤 '{step_name}'",
            "任务进行中，系统正在处理相关操作",
            "工作流正在进行，当前步骤处理中"
        ]
        
        self.minimal_templates = [
            "系统状态更新",
            "工作流程进行中",
            "任务处理状态更新"
        ]
    
    def generate_fallback_state(self, strategy: FallbackStrategy, 
                               current_state: 'WorkflowState', 
                               context: Dict[str, Any],
                               failure_reason: str = "") -> str:
        """
        根据指定策略生成回退状态
        
        Args:
            strategy: 回退策略
            current_state: 当前工作流状态
            context: 上下文信息
            failure_reason: 失败原因
            
        Returns:
            生成的回退状态描述
        """
        try:
            self.logger.info(f"使用回退策略生成状态: {strategy.value}")
            
            if strategy == FallbackStrategy.TEMPLATE_BASED:
                return self._generate_template_based_state(context)
            elif strategy == FallbackStrategy.RULE_BASED:
                return self._generate_rule_based_state(current_state, context)
            elif strategy == FallbackStrategy.MINIMAL_STATE:
                return self._generate_minimal_state(context)
            elif strategy == FallbackStrategy.NOTIFY_OPERATOR:
                return self._generate_notification_state(failure_reason)
            else:
                # 默认使用最小状态
                return self._generate_minimal_state(context)
                
        except Exception as e:
            self.logger.error(f"回退状态生成失败: {e}")
            return "系统状态更新"  # 最后的保底状态
    
    def _generate_template_based_state(self, context: Dict[str, Any]) -> str:
        """基于模板生成状态"""
        step_info = context.get('step_info', {})
        step_name = step_info.get('description', step_info.get('name', '未知步骤'))
        step_status = context.get('step_status', 'unknown')
        execution_result = context.get('execution_result', {})
        error_info = context.get('error_info')
        
        # 根据执行状态选择模板类型
        if error_info or (execution_result and not execution_result.get('success', True)):
            template = random.choice(self.error_templates)
        elif step_status == 'completed':
            template = random.choice(self.success_templates)
        else:
            template = random.choice(self.progress_templates)
        
        # 替换变量
        try:
            return template.format(step_name=step_name)
        except:
            return template.replace("{step_name}", step_name)
    
    def _generate_rule_based_state(self, current_state: 'WorkflowState', context: Dict[str, Any]) -> str:
        """基于规则生成状态"""
        parts = []
        
        # 获取步骤信息
        step_info = context.get('step_info', {})
        step_name = step_info.get('description', '当前步骤')
        step_status = context.get('step_status')
        
        # 检查错误情况
        error_info = context.get('error_info')
        if error_info:
            parts.append(f"{step_name}执行遇到问题")
            if "网络" in str(error_info).lower():
                parts.append("网络连接异常")
            elif "权限" in str(error_info).lower():
                parts.append("权限验证失败")
            else:
                parts.append("需要进一步处理")
        else:
            # 检查执行结果
            execution_result = context.get('execution_result', {})
            if execution_result.get('success'):
                parts.append(f"{step_name}执行成功")
                
                # 添加输出信息
                output = execution_result.get('output')
                if output:
                    output_str = str(output)[:50]
                    if "完成" in output_str or "成功" in output_str:
                        parts.append("操作顺利完成")
                    elif len(output_str) > 10:
                        parts.append("已生成处理结果")
            else:
                parts.append(f"{step_name}正在执行")
        
        return "，".join(parts) if parts else "工作流状态更新"
    
    def _generate_minimal_state(self, context: Dict[str, Any]) -> str:
        """生成最小状态描述"""
        timestamp = dt.now().strftime("%H:%M")
        template = random.choice(self.minimal_templates)
        return f"{template} ({timestamp})"
    
    def _generate_notification_state(self, failure_reason: str) -> str:
        """生成通知操作员的状态"""
        return f"AI状态更新失败，需要人工介入 - 原因: {failure_reason[:50]}..."


class AICallCacheEntry(NamedTuple):
    """AI调用缓存条目"""
    response: str                    # LLM响应
    timestamp: dt                   # 创建时间
    context_hash: str               # 上下文哈希
    confidence_score: float         # 置信度评分
    usage_count: int                # 使用次数
    
class LRUCache:
    """LRU缓存实现，用于AI调用结果缓存"""
    
    def __init__(self, max_size: int = 100):
        """
        初始化LRU缓存
        
        Args:
            max_size: 缓存最大容量
        """
        self.max_size = max_size
        self.cache = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
        
    def get(self, key: str) -> Optional[AICallCacheEntry]:
        """获取缓存项"""
        with self._lock:
            self._stats['total_requests'] += 1
            
            if key in self.cache:
                # 移动到末尾（最近使用）
                entry = self.cache.pop(key)
                # 增加使用次数
                updated_entry = entry._replace(usage_count=entry.usage_count + 1)
                self.cache[key] = updated_entry
                self._stats['hits'] += 1
                return updated_entry
            else:
                self._stats['misses'] += 1
                return None
    
    def put(self, key: str, entry: AICallCacheEntry) -> None:
        """添加缓存项"""
        with self._lock:
            if key in self.cache:
                # 更新现有项
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # 移除最少使用的项
                self.cache.popitem(last=False)
                self._stats['evictions'] += 1
            
            self.cache[key] = entry
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            hit_rate = (self._stats['hits'] / max(self._stats['total_requests'], 1)) * 100
            return {
                **self._stats,
                'hit_rate_percent': hit_rate,
                'cache_size': len(self.cache),
                'max_size': self.max_size
            }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        with self._lock:
            self._stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'total_requests': 0
            }

class ContextHasher:
    """上下文哈希生成器"""
    
    @staticmethod
    def hash_context(current_state: 'WorkflowState', context: Dict[str, Any], 
                    include_timestamp: bool = False) -> str:
        """
        生成上下文的哈希值
        
        Args:
            current_state: 当前工作流状态
            context: 上下文信息
            include_timestamp: 是否包含时间戳（影响缓存有效性）
            
        Returns:
            上下文哈希字符串
        """
        import hashlib
        
        # 收集关键上下文信息
        hash_components = []
        
        # 1. 当前全局状态
        if current_state:
            global_state = current_state.get_global_state()
            hash_components.append(f"global_state:{global_state}")
            
            # 添加最近的状态历史（限制数量避免哈希过长）
            recent_history = current_state.get_state_history(limit=3)
            for i, entry in enumerate(recent_history):
                hash_components.append(f"history_{i}:{entry.state_snapshot[:100]}")
        
        # 2. 步骤信息
        step_info = context.get('step_info', {})
        if step_info:
            hash_components.append(f"step_action:{step_info.get('action', '')}")
            hash_components.append(f"step_type:{step_info.get('type', '')}")
            hash_components.append(f"step_id:{step_info.get('step_id', '')}")
        
        # 3. 执行结果（关键部分）
        execution_result = context.get('execution_result', '')
        if execution_result:
            # 截取前200个字符避免哈希过长
            result_summary = str(execution_result)[:200]
            hash_components.append(f"exec_result:{result_summary}")
        
        # 4. 步骤状态
        step_status = context.get('step_status', '')
        hash_components.append(f"step_status:{step_status}")
        
        # 5. 错误信息
        error_info = context.get('error_info')
        if error_info:
            error_summary = str(error_info)[:100]
            hash_components.append(f"error:{error_summary}")
        
        # 6. 时间戳（可选）
        if include_timestamp:
            timestamp = context.get('timestamp', dt.now().isoformat())
            hash_components.append(f"timestamp:{timestamp}")
        
        # 生成哈希
        combined_string = "|".join(hash_components)
        return hashlib.md5(combined_string.encode('utf-8')).hexdigest()

class AICallConditionChecker:
    """AI调用条件检查器"""
    
    def __init__(self):
        """初始化条件检查器"""
        self._significance_threshold = 0.3  # 显著性阈值
        self._time_threshold = 300  # 时间阈值（秒）
        
    def should_make_ai_call(self, current_state: 'WorkflowState', 
                           context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        判断是否应该进行AI调用
        
        Args:
            current_state: 当前工作流状态
            context: 上下文信息
            
        Returns:
            (should_call, reason) 元组
        """
        # 1. 检查首次初始化（最高优先级）
        if self._is_initialization(current_state):
            return True, "工作流初始化，需要设置初始状态"
        
        # 2. 检查是否有重大变化
        has_significant_change, change_reason = self._has_significant_change(context)
        if has_significant_change:
            return True, f"检测到重大变化: {change_reason}"
        
        # 3. 检查错误状态
        if self._has_error_condition(context):
            return True, "检测到错误状态，需要AI分析"
        
        # 4. 检查状态转换
        if self._is_state_transition(context):
            return True, "检测到状态转换，需要AI更新"
        
        # 5. 检查时间间隔
        if self._should_update_by_time(current_state):
            return True, "基于时间间隔的定期更新"
        
        return False, "无需AI调用：变化不显著且无特殊条件"
    
    def _has_significant_change(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """检查是否有显著变化"""
        # 检查执行结果变化
        execution_result = context.get('execution_result', '')
        if execution_result:
            result_str = str(execution_result)
            # 检查结果长度（更长可能意味着更多信息）
            if len(result_str) > 100:
                return True, "执行结果信息丰富"
        
        # 检查步骤类型
        step_info = context.get('step_info', {})
        step_type = step_info.get('type', '').lower()
        
        # 重要步骤类型总是触发AI调用
        important_types = ['critical', 'important', 'decision', 'approval', 'validation']
        if any(important_type in step_type for important_type in important_types):
            return True, f"重要步骤类型: {step_type}"
        
        return False, "无显著变化"
    
    def _has_error_condition(self, context: Dict[str, Any]) -> bool:
        """检查是否有错误条件"""
        # 检查错误信息
        error_info = context.get('error_info')
        if error_info:
            return True
        
        # 检查执行状态
        step_status = context.get('step_status', '').lower()
        if 'fail' in step_status or 'error' in step_status:
            return True
        
        # 检查执行结果中的失败标识
        execution_result = context.get('execution_result', '')
        if execution_result:
            result_str = str(execution_result).lower()
            error_keywords = ['error', 'failed', 'exception', 'timeout', 'denied']
            if any(keyword in result_str for keyword in error_keywords):
                return True
        
        return False
    
    def _is_state_transition(self, context: Dict[str, Any]) -> bool:
        """检查是否为状态转换"""
        step_status = context.get('step_status', '').lower()
        transition_statuses = ['completed', 'success', 'finished', 'done']
        return any(status in step_status for status in transition_statuses)
    
    def _should_update_by_time(self, current_state: 'WorkflowState') -> bool:
        """检查是否应基于时间进行更新"""
        if not current_state:
            return True
        
        history = current_state.get_state_history(limit=1)
        if not history:
            return True
        
        last_update = history[0].timestamp
        time_since_last = (dt.now() - last_update).total_seconds()
        
        return time_since_last > self._time_threshold
    
    def _is_initialization(self, current_state: 'WorkflowState') -> bool:
        """检查是否为初始化状态"""
        if not current_state:
            return True
        
        global_state = current_state.get_global_state()
        return not global_state.strip() or current_state.get_state_history_count() == 0
    
    def set_significance_threshold(self, threshold: float) -> None:
        """设置显著性阈值"""
        self._significance_threshold = max(0.0, min(1.0, threshold))
    
    def set_time_threshold(self, seconds: int) -> None:
        """设置时间阈值"""
        self._time_threshold = max(60, seconds)  # 最小1分钟
    
    def get_configuration(self) -> Dict[str, Any]:
        """获取配置信息"""
        return {
            'significance_threshold': self._significance_threshold,
            'time_threshold_seconds': self._time_threshold
        }

class AIStateUpdater(ABC):
    """AI状态更新器抽象接口"""
    
    @abstractmethod
    def update_state(self, current_state: 'WorkflowState', context: Dict[str, Any]) -> Optional[str]:
        """
        基于当前状态和上下文更新全局状态
        
        Args:
            current_state: 当前的WorkflowState实例
            context: 包含步骤信息、执行结果等的上下文字典
            
        Returns:
            新的状态字符串，如果不需要更新则返回None
        """
        pass
    
    @abstractmethod
    def should_update(self, current_state: 'WorkflowState', context: Dict[str, Any]) -> bool:
        """
        判断是否应该更新状态
        
        Args:
            current_state: 当前的WorkflowState实例
            context: 包含步骤信息、执行结果等的上下文字典
            
        Returns:
            是否需要更新状态
        """
        pass

class AIStateUpdaterService(AIStateUpdater):
    """基于DeepSeek的AI状态更新器服务实现"""
    
    def __init__(self, llm: ChatOpenAI, max_retries: int = None, retry_delay: float = None,
                 enable_sentiment_analysis: bool = None, enable_intent_recognition: bool = None,
                 fallback_strategies: List[FallbackStrategy] = None, enable_notifications: bool = None,
                 enable_caching: bool = None, cache_size: int = None, 
                 enable_conditional_logic: bool = None):
        """
        初始化AI状态更新器服务（支持配置系统）
        
        Args:
            llm: DeepSeek LLM实例 (llm_deepseek)
            max_retries: 最大重试次数（None则使用配置文件）
            retry_delay: 重试延迟时间（秒）（None则使用配置文件）
            enable_sentiment_analysis: 是否启用情感分析（None则使用配置文件）
            enable_intent_recognition: 是否启用意图识别（None则使用配置文件）
            fallback_strategies: 回退策略列表，按优先级排序（None则使用配置文件）
            enable_notifications: 是否启用失败通知（None则使用配置文件）
            enable_caching: 是否启用缓存（None则使用配置文件）
            cache_size: 缓存大小（None则使用配置文件）
            enable_conditional_logic: 是否启用条件逻辑（None则使用配置文件）
        """
        self.llm = llm
        self._logger = logging.getLogger(f"{__name__}.AIStateUpdaterService")
        
        # 加载配置系统参数
        if CONFIG_SYSTEM_AVAILABLE:
            try:
                config = get_config()
                ai_config = config.ai_updater
                
                # 使用配置系统的参数（如果没有显式指定）
                self.max_retries = max_retries if max_retries is not None else ai_config.max_retries
                self.retry_delay = retry_delay if retry_delay is not None else ai_config.timeout_seconds / 10.0  # 简单计算
                self.enable_notifications = enable_notifications if enable_notifications is not None else False  # 默认关闭通知
                enable_caching = enable_caching if enable_caching is not None else ai_config.enable_caching
                cache_size = cache_size if cache_size is not None else ai_config.cache_ttl_minutes * 2  # 简单计算
                enable_conditional_logic = enable_conditional_logic if enable_conditional_logic is not None else True
                enable_sentiment_analysis = enable_sentiment_analysis if enable_sentiment_analysis is not None else True
                enable_intent_recognition = enable_intent_recognition if enable_intent_recognition is not None else True
                
                self._logger.info(f"使用配置系统参数: 重试次数={self.max_retries}, 缓存={enable_caching}, 模型={ai_config.model_name}")
            except Exception as e:
                self._logger.warning(f"加载AI配置失败，使用默认参数: {e}")
                # 使用默认值
                self.max_retries = max_retries if max_retries is not None else 3
                self.retry_delay = retry_delay if retry_delay is not None else 1.0
                self.enable_notifications = enable_notifications if enable_notifications is not None else False
                enable_caching = enable_caching if enable_caching is not None else True
                cache_size = cache_size if cache_size is not None else 100
                enable_conditional_logic = enable_conditional_logic if enable_conditional_logic is not None else True
                enable_sentiment_analysis = enable_sentiment_analysis if enable_sentiment_analysis is not None else True
                enable_intent_recognition = enable_intent_recognition if enable_intent_recognition is not None else True
        else:
            # 配置系统不可用，使用传入参数或默认值
            self.max_retries = max_retries if max_retries is not None else 3
            self.retry_delay = retry_delay if retry_delay is not None else 1.0
            self.enable_notifications = enable_notifications if enable_notifications is not None else False
            enable_caching = enable_caching if enable_caching is not None else True
            cache_size = cache_size if cache_size is not None else 100
            enable_conditional_logic = enable_conditional_logic if enable_conditional_logic is not None else True
            enable_sentiment_analysis = enable_sentiment_analysis if enable_sentiment_analysis is not None else True
            enable_intent_recognition = enable_intent_recognition if enable_intent_recognition is not None else True
        
        # 初始化模板管理器
        self.template_manager = PromptTemplateManager()
        
        # 初始化响应解析器
        self.response_parser = ResponseParser(
            enable_sentiment_analysis=enable_sentiment_analysis,
            enable_intent_recognition=enable_intent_recognition
        )
        
        # 初始化回退状态生成器
        self.fallback_generator = FallbackStateGenerator()
        
        # 配置回退策略（如果没有指定，使用默认策略）
        self.fallback_strategies = fallback_strategies or [
            FallbackStrategy.RETRY_SIMPLIFIED,
            FallbackStrategy.TEMPLATE_BASED,
            FallbackStrategy.RULE_BASED,
            FallbackStrategy.MINIMAL_STATE
        ]
        
        # 缓存和条件逻辑配置
        self.enable_caching = enable_caching
        self.enable_conditional_logic = enable_conditional_logic
        
        # 初始化缓存系统
        if self.enable_caching:
            self.cache = LRUCache(max_size=cache_size)
            self.context_hasher = ContextHasher()
            self._logger.info(f"AI调用缓存已启用，缓存大小: {cache_size}")
        else:
            self.cache = None
            self.context_hasher = None
            self._logger.info("AI调用缓存已禁用")
        
        # 初始化条件检查器
        if self.enable_conditional_logic:
            self.condition_checker = AICallConditionChecker()
            self._logger.info("AI调用条件逻辑已启用")
        else:
            self.condition_checker = None
            self._logger.info("AI调用条件逻辑已禁用")
        
        # 存储最后一次解析信息和失败记录
        self._last_parsed_info = None
        self._parsed_info_lock = threading.Lock()
        self._failure_count = 0
        self._last_failure_reason = ""
        
        # 验证LLM连接
        self._validate_llm_connection()
        
        model_name = getattr(llm, 'model_name', getattr(llm, 'model', 'unknown'))
        self._logger.info(f"AIStateUpdaterService初始化完成 - 模型: {model_name}, 最大重试: {self.max_retries}, "
                         f"模板数: {len(self.template_manager.list_templates())}, 响应解析器: 已启用, "
                         f"回退策略: {len(self.fallback_strategies)}个, 通知: {'启用' if self.enable_notifications else '禁用'}, "
                         f"缓存: {'启用' if self.enable_caching else '禁用'}, "
                         f"条件逻辑: {'启用' if self.enable_conditional_logic else '禁用'}")
    
    def _validate_llm_connection(self) -> None:
        """验证LLM连接是否正常"""
        try:
            test_message = [SystemMessage(content="你是一个AI助手"), HumanMessage(content="请回复'连接正常'")]
            response = self.llm.invoke(test_message)
            if response and response.content:
                self._logger.info("LLM连接验证成功")
            else:
                raise ValueError("LLM响应为空")
        except Exception as e:
            self._logger.error(f"LLM连接验证失败: {e}")
            raise RuntimeError(f"无法连接到DeepSeek服务: {e}")
    
    def should_update(self, current_state: 'WorkflowState', context: Dict[str, Any]) -> bool:
        """
        判断是否应该更新状态
        
        简单策略：
        1. 如果步骤执行完成（成功或失败）则更新
        2. 如果状态为空则更新
        3. 如果上下文包含重要变化则更新
        """
        try:
            # 检查基本条件
            if not current_state.is_state_update_enabled():
                self._logger.debug("状态更新被禁用，跳过更新判断")
                return False
            
            # 如果当前状态为空，应该更新
            current_global_state = current_state.get_global_state()
            if not current_global_state.strip():
                self._logger.debug("当前状态为空，需要更新")
                return True
            
            # 检查上下文中的重要信息
            step_status = context.get('step_status')
            if step_status in ['completed', 'failed']:
                self._logger.debug(f"步骤状态为{step_status}，需要更新")
                return True
            
            # 检查是否有执行结果
            if context.get('execution_result') is not None:
                self._logger.debug("存在执行结果，需要更新")
                return True
            
            # 检查是否有错误信息
            if context.get('error_info'):
                self._logger.debug("存在错误信息，需要更新")
                return True
            
            self._logger.debug("无需更新状态")
            return False
            
        except Exception as e:
            self._logger.error(f"状态更新判断失败: {e}")
            return False
    
    def update_state(self, current_state: 'WorkflowState', context: Dict[str, Any]) -> Optional[str]:
        """
        使用DeepSeek和动态模板生成新的状态描述，集成缓存和条件逻辑
        
        Args:
            current_state: 当前工作流状态
            context: 上下文信息
            
        Returns:
            新的状态描述字符串，失败时返回None
        """
        # 1. 基本可用性检查
        if not self.should_update(current_state, context):
            return None
        
        # 2. 条件逻辑检查（如果启用）
        if self.enable_conditional_logic and self.condition_checker:
            should_call, reason = self.condition_checker.should_make_ai_call(current_state, context)
            if not should_call:
                self._logger.debug(f"条件逻辑检查决定跳过AI调用: {reason}")
                return None
            else:
                self._logger.debug(f"条件逻辑检查决定进行AI调用: {reason}")
        
        # 3. 缓存检查（如果启用）
        cache_key = None
        if self.enable_caching and self.cache and self.context_hasher:
            cache_key = self.context_hasher.hash_context(current_state, context)
            cached_entry = self.cache.get(cache_key)
            if cached_entry:
                self._logger.info(f"使用缓存响应 [缓存命中, 使用次数: {cached_entry.usage_count}]")
                return cached_entry.response
        
        # 检测场景类型
        scenario = self._detect_scenario(current_state, context)
        self._logger.debug(f"检测到场景类型: {scenario.value}")
        
        for attempt in range(self.max_retries + 1):
            try:
                # 准备模板变量
                variables = self._prepare_template_variables(current_state, context)
                
                # 使用模板生成提示
                system_message, user_message = self.template_manager.render_template(scenario, variables)
                
                # 调用DeepSeek生成状态描述
                messages = [
                    SystemMessage(content=system_message),
                    HumanMessage(content=user_message)
                ]
                
                self._logger.debug(f"第{attempt + 1}次尝试调用DeepSeek更新状态 [场景: {scenario.value}]")
                response = self.llm.invoke(messages)
                
                if response and response.content:
                    new_state = response.content.strip()
                    
                    # 首先解析响应以获取详细信息
                    parsed_info = self.response_parser.parse_response(new_state, context)
                    self._store_parsed_info(parsed_info)
                    
                    # 验证生成的状态描述
                    if self._validate_generated_state(new_state, context):
                        self._logger.info(f"成功生成新状态描述 [场景: {scenario.value}, 尝试次数: {attempt + 1}, "
                                        f"置信度: {parsed_info.confidence_score:.2f}, 质量: {parsed_info.quality_metrics.get('overall_quality', 'unknown')}]")
                        
                        # 缓存成功的响应（如果启用）
                        if self.enable_caching and self.cache and cache_key:
                            cache_entry = AICallCacheEntry(
                                response=new_state,
                                timestamp=dt.now(),
                                context_hash=cache_key,
                                confidence_score=parsed_info.confidence_score,
                                usage_count=1
                            )
                            self.cache.put(cache_key, cache_entry)
                            self._logger.debug(f"响应已缓存 [key: {cache_key[:8]}...]")
                        
                        return new_state
                    else:
                        self._logger.warning(f"生成的状态描述验证失败 (尝试次数: {attempt + 1})")
                        
                else:
                    self._logger.warning(f"DeepSeek返回空响应 (尝试次数: {attempt + 1})")
                    
            except Exception as e:
                self._logger.error(f"DeepSeek调用失败 (尝试次数: {attempt + 1}): {e}")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (attempt + 1))  # 指数退避
        
        # 所有LLM重试失败，启动多层回退机制
        self._failure_count += 1
        self._last_failure_reason = f"LLM调用失败，已重试{self.max_retries + 1}次"
        self._logger.error(f"所有LLM重试尝试失败，启动回退机制 (失败次数: {self._failure_count})")
        
        # 执行回退策略
        fallback_state = self._execute_fallback_strategies(current_state, context)
        if fallback_state:
            self._logger.info(f"回退机制成功生成状态: {fallback_state[:50]}...")
            return fallback_state
        
        self._logger.error("所有回退策略失败，无法生成状态更新")
        return None
    
    def _get_system_message(self) -> str:
        """获取状态更新的系统提示消息"""
        return """你是一个专业的工作流状态管理专家，负责根据工作流执行情况生成简洁准确的状态描述。

要求：
1. 状态描述应该是自然语言，简洁明了（1-3句话）
2. 重点描述当前工作流的核心进展和状态
3. 如果有错误，简要说明问题所在
4. 如果成功完成，描述实现的主要功能
5. 避免技术细节，关注业务层面的状态
6. 状态描述应该连贯，体现工作流的演进过程

示例：
- "开始创建计算器应用，正在设计基础架构"
- "计算器核心功能实现完成，包含加减乘除运算"
- "测试阶段发现除零错误，正在修复异常处理"
- "计算器应用开发完成，所有功能测试通过"
"""
    
    def _build_state_update_prompt(self, current_state: 'WorkflowState', context: Dict[str, Any]) -> str:
        """构建状态更新提示"""
        # 获取当前状态信息
        current_global_state = current_state.get_global_state()
        state_history = current_state.get_state_history(limit=3)  # 获取最近3条历史
        
        # 从上下文提取关键信息
        step_info = context.get('step_info', {})
        execution_result = context.get('execution_result')
        step_status = context.get('step_status', 'unknown')
        error_info = context.get('error_info')
        
        # 构建提示
        prompt_parts = [
            "请根据以下信息更新工作流状态描述：",
            "",
            "## 当前状态",
            f"当前状态: {current_global_state if current_global_state else '无'}",
            "",
            "## 最近状态历史"
        ]
        
        if state_history:
            for i, entry in enumerate(reversed(state_history), 1):
                prompt_parts.append(f"{i}. {entry.state_snapshot} (时间: {entry.timestamp.strftime('%H:%M:%S')})")
        else:
            prompt_parts.append("无历史记录")
        
        prompt_parts.extend([
            "",
            "## 当前步骤信息",
            f"步骤状态: {step_status}",
            f"步骤描述: {step_info.get('description', '未知')}",
            f"步骤类型: {step_info.get('type', '未知')}",
            ""
        ])
        
        # 添加执行结果信息
        if execution_result:
            prompt_parts.extend([
                "## 执行结果",
                f"执行成功: {'是' if execution_result.get('success', False) else '否'}"
            ])
            
            if execution_result.get('output'):
                output_preview = str(execution_result['output'])[:200]
                prompt_parts.append(f"输出预览: {output_preview}...")
        
        # 添加错误信息
        if error_info:
            prompt_parts.extend([
                "",
                "## 错误信息",
                f"错误详情: {error_info}"
            ])
        
        prompt_parts.extend([
            "",
            "请生成一个简洁的状态描述（1-3句话），反映当前工作流的实际进展和状态。"
        ])
        
        return "\n".join(prompt_parts)
    
    def _detect_scenario(self, current_state: 'WorkflowState', context: Dict[str, Any]) -> PromptScenario:
        """
        检测当前场景类型
        
        Args:
            current_state: 当前工作流状态
            context: 上下文信息
        
        Returns:
            检测到的场景类型
        """
        # 获取基本信息
        current_global_state = current_state.get_global_state()
        step_status = context.get('step_status', '').lower()
        error_info = context.get('error_info')
        execution_result = context.get('execution_result')
        step_info = context.get('step_info', {})
        
        # 1. 初始化场景：如果当前状态为空且是第一次执行
        if not current_global_state.strip() and current_state.get_state_history_count() == 0:
            return PromptScenario.INITIALIZATION
        
        # 2. 错误处理场景：如果有错误信息或执行失败
        execution_failed = False
        if isinstance(execution_result, dict):
            execution_failed = not execution_result.get('success', True)
        elif isinstance(execution_result, str):
            execution_failed = execution_result.lower() in ['failed', 'error', 'failure']
        
        if error_info or execution_failed:
            return PromptScenario.ERROR_HANDLING
        
        # 3. 成功完成场景：如果步骤成功完成
        if step_status in ['completed', 'success']:
            return PromptScenario.SUCCESS_COMPLETION
        
        # 4. 状态转换场景：如果历史记录表明有重要转换
        history_count = current_state.get_state_history_count()
        if history_count > 1 and step_info.get('type') in ['control', 'decision', 'transition']:
            return PromptScenario.STATE_TRANSITION
        
        # 5. 总结场景：如果是最后一步或包含总结信息
        if (step_info.get('type') == 'summary' or 
            context.get('is_final_step', False) or 
            'complete' in step_status or 
            'finish' in step_status):
            return PromptScenario.SUMMARY
        
        # 6. 默认为进度更新场景
        return PromptScenario.PROGRESS_UPDATE
    
    def _prepare_template_variables(self, current_state: 'WorkflowState', context: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备模板变量
        
        Args:
            current_state: 当前工作流状态
            context: 上下文信息
            
        Returns:
            模板变量字典
        """
        # 获取基本状态信息
        current_global_state = current_state.get_global_state()
        state_history = current_state.get_state_history(limit=3)
        
        # 获取上下文信息
        step_info = context.get('step_info', {})
        execution_result = context.get('execution_result')
        error_info = context.get('error_info')
        main_instruction = context.get('main_instruction', '')
        
        # 构建状态历史摘要
        state_history_text = ""
        if state_history:
            history_items = []
            for i, entry in enumerate(reversed(state_history), 1):
                timestamp_str = entry.timestamp.strftime('%H:%M:%S')
                history_items.append(f"{i}. {entry.state_snapshot} (时间: {timestamp_str})")
            state_history_text = "\n".join(history_items)
        else:
            state_history_text = "无历史记录"
        
        # 处理执行输出 - 支持字符串和字典两种格式
        execution_output = ""
        execution_success = False
        if execution_result:
            if isinstance(execution_result, dict):
                if execution_result.get('output'):
                    output_str = str(execution_result['output'])
                    # 限制输出长度以避免提示过长
                    execution_output = output_str[:300] + ("..." if len(output_str) > 300 else "")
                elif execution_result.get('success'):
                    execution_output = "执行成功，无特定输出"
                else:
                    execution_output = "执行失败"
                execution_success = execution_result.get('success', False)
            elif isinstance(execution_result, str):
                execution_output = execution_result[:300] + ("..." if len(execution_result) > 300 else "")
                execution_success = execution_result.lower() not in ['failed', 'error', 'failure']
            else:
                execution_output = str(execution_result)
                execution_success = True
        else:
            execution_output = "无执行信息"
            execution_success = False
        
        # 准备变量字典
        variables = {
            # 状态相关
            'current_state': current_global_state or "工作流刚开始",
            'previous_state': state_history[0].state_snapshot if state_history else "无前置状态",
            'state_history': state_history_text,
            
            # 步骤相关
            'step_description': step_info.get('description', '未知步骤'),
            'step_type': step_info.get('type', '未知类型'),
            'step_status': context.get('step_status', '未知'),
            
            # 执行相关
            'execution_success': str(execution_success),
            'execution_output': execution_output,
            'error_message': str(error_info) if error_info else '无错误信息',
            
            # 工作流相关
            'main_instruction': main_instruction,
            'workflow_progress': f"已执行{current_state.get_state_history_count()}个状态更新"
        }
        
        return variables
    
    def _validate_generated_state(self, state: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """验证生成的状态描述是否有效（使用智能解析器）"""
        if not state or not isinstance(state, str):
            self._logger.warning("状态描述为空或非字符串类型")
            return False
        
        try:
            # 使用ResponseParser进行智能解析
            parsed_info = self.response_parser.parse_response(state, context)
            
            # 验证解析结果
            is_valid, issues = self.response_parser.validate_parsed_info(parsed_info, min_confidence=0.3)
            
            if not is_valid:
                self._logger.warning(f"状态描述验证失败: {'; '.join(issues)}")
                
                # 如果解析失败，提供改进建议
                suggestions = self.response_parser.suggest_improvements(parsed_info)
                if suggestions:
                    self._logger.info(f"改进建议: {'; '.join(suggestions)}")
                
                return False
            
            # 记录解析结果的详细信息
            self._logger.debug(f"状态解析成功 - 置信度: {parsed_info.confidence_score:.2f}, "
                             f"质量: {parsed_info.quality_metrics.get('overall_quality', 'unknown')}, "
                             f"情感: {parsed_info.sentiment}, 意图: {parsed_info.intent}")
            
            return True
            
        except Exception as e:
            self._logger.error(f"状态验证过程中发生异常: {e}")
            return False
    
    def get_last_parsed_info(self) -> Optional[ParsedStateInfo]:
        """获取最后一次解析的状态信息（用于调试和监控）"""
        # 这里可以存储最后一次解析的结果，供外部查询
        # 简单实现中直接返回None，实际可以添加缓存机制
        return getattr(self, '_last_parsed_info', None)
    
    def _store_parsed_info(self, parsed_info: ParsedStateInfo) -> None:
        """存储解析信息供后续查询"""
        with self._parsed_info_lock:
            self._last_parsed_info = parsed_info
    
    def _execute_fallback_strategies(self, current_state: 'WorkflowState', context: Dict[str, Any]) -> Optional[str]:
        """
        执行多层回退策略
        
        Args:
            current_state: 当前工作流状态
            context: 上下文信息
            
        Returns:
            生成的回退状态描述，失败时返回None
        """
        self._logger.info(f"开始执行回退策略，共{len(self.fallback_strategies)}个策略")
        
        for i, strategy in enumerate(self.fallback_strategies, 1):
            try:
                self._logger.debug(f"执行第{i}个回退策略: {strategy.value}")
                
                if strategy == FallbackStrategy.RETRY_SIMPLIFIED:
                    # 第1层：使用简化提示重试
                    fallback_state = self._retry_with_simplified_prompt(current_state, context)
                elif strategy == FallbackStrategy.TEMPLATE_BASED:
                    # 第2层：使用模板化默认状态
                    fallback_state = self.fallback_generator.generate_fallback_state(
                        strategy, current_state, context, self._last_failure_reason
                    )
                elif strategy == FallbackStrategy.RULE_BASED:
                    # 第3层：使用基于规则的逻辑
                    fallback_state = self.fallback_generator.generate_fallback_state(
                        strategy, current_state, context, self._last_failure_reason
                    )
                elif strategy == FallbackStrategy.MINIMAL_STATE:
                    # 第4层：生成最小状态描述
                    fallback_state = self.fallback_generator.generate_fallback_state(
                        strategy, current_state, context, self._last_failure_reason
                    )
                elif strategy == FallbackStrategy.NOTIFY_OPERATOR:
                    # 第5层：通知操作员
                    fallback_state = self.fallback_generator.generate_fallback_state(
                        strategy, current_state, context, self._last_failure_reason
                    )
                    if self.enable_notifications:
                        self._send_failure_notification(context)
                else:
                    self._logger.warning(f"未知的回退策略: {strategy}")
                    continue
                
                if fallback_state:
                    self._logger.info(f"回退策略 {strategy.value} 成功生成状态")
                    return fallback_state
                else:
                    self._logger.warning(f"回退策略 {strategy.value} 失败，尝试下一个策略")
                    
            except Exception as e:
                self._logger.error(f"回退策略 {strategy.value} 执行异常: {e}")
                continue
        
        self._logger.error("所有回退策略都失败了")
        return None
    
    def _retry_with_simplified_prompt(self, current_state: 'WorkflowState', context: Dict[str, Any]) -> Optional[str]:
        """
        使用简化提示重试LLM调用
        
        Args:
            current_state: 当前工作流状态
            context: 上下文信息
            
        Returns:
            生成的状态描述，失败时返回None
        """
        try:
            self._logger.debug("尝试使用简化提示重试LLM调用")
            
            # 构建简化的提示
            step_info = context.get('step_info', {})
            step_name = step_info.get('description', '当前步骤')
            step_status = context.get('step_status', 'unknown')
            error_info = context.get('error_info')
            
            if error_info:
                simple_prompt = f"步骤 '{step_name}' 执行遇到问题，请用一句话描述当前状态"
            elif step_status == 'completed':
                simple_prompt = f"步骤 '{step_name}' 执行完成，请用一句话描述当前状态"
            else:
                simple_prompt = f"步骤 '{step_name}' 正在进行，请用一句话描述当前状态"
            
            # 调用LLM
            messages = [
                SystemMessage(content="你是一个状态描述专家，请用简洁的中文回复。"),
                HumanMessage(content=simple_prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            if response and response.content:
                simplified_state = response.content.strip()
                if len(simplified_state) >= 5:  # 基本长度检查
                    self._logger.info("简化提示重试成功")
                    return simplified_state
            
            self._logger.warning("简化提示重试失败或响应过短")
            return None
            
        except Exception as e:
            self._logger.error(f"简化提示重试异常: {e}")
            return None
    
    def _send_failure_notification(self, context: Dict[str, Any]) -> None:
        """
        发送失败通知
        
        Args:
            context: 上下文信息
        """
        try:
            self._logger.warning(f"AI状态更新失败通知: 失败次数 {self._failure_count}, 原因: {self._last_failure_reason}")
            
            # 这里可以扩展为发送邮件、消息队列或其他通知方式
            # 目前只记录日志
            
            step_info = context.get('step_info', {})
            notification_details = {
                'timestamp': dt.now().isoformat(),
                'failure_count': self._failure_count,
                'failure_reason': self._last_failure_reason,
                'step_name': step_info.get('description', 'unknown'),
                'step_status': context.get('step_status', 'unknown')
            }
            
            self._logger.error(f"状态更新失败通知详情: {notification_details}")
            
        except Exception as e:
            self._logger.error(f"发送失败通知时出错: {e}")
    
    def get_fallback_statistics(self) -> Dict[str, Any]:
        """
        获取回退机制统计信息
        
        Returns:
            包含回退统计信息的字典
        """
        return {
            'failure_count': self._failure_count,
            'last_failure_reason': self._last_failure_reason,
            'fallback_strategies': [strategy.value for strategy in self.fallback_strategies],
            'notifications_enabled': self.enable_notifications
        }
    
    def reset_fallback_statistics(self) -> None:
        """重置回退统计信息"""
        self._failure_count = 0
        self._last_failure_reason = ""
        self._logger.info("回退统计信息已重置")

    def get_fallback_statistics(self) -> Dict[str, Any]:
        """获取回退统计信息"""
        return getattr(self, '_fallback_stats', {
            'total_fallbacks': 0,
            'strategies_used': {},
            'success_rate': 0.0,
            'last_failure_time': None
        })
    
    def reset_fallback_statistics(self) -> None:
        """重置回退统计信息"""
        self._fallback_stats = {
            'total_fallbacks': 0,
            'strategies_used': {},
            'success_rate': 0.0,
            'last_failure_time': None
        }
    
    def _update_fallback_statistics(self, strategy: FallbackStrategy, success: bool) -> None:
        """更新回退统计信息"""
        if not hasattr(self, '_fallback_stats'):
            self.reset_fallback_statistics()
        
        self._fallback_stats['total_fallbacks'] += 1
        
        strategy_name = strategy.value
        if strategy_name not in self._fallback_stats['strategies_used']:
            self._fallback_stats['strategies_used'][strategy_name] = {'count': 0, 'success': 0}
        
        self._fallback_stats['strategies_used'][strategy_name]['count'] += 1
        if success:
            self._fallback_stats['strategies_used'][strategy_name]['success'] += 1
        
        # 计算成功率
        total_attempts = sum(s['count'] for s in self._fallback_stats['strategies_used'].values())
        total_successes = sum(s['success'] for s in self._fallback_stats['strategies_used'].values())
        self._fallback_stats['success_rate'] = total_successes / total_attempts if total_attempts > 0 else 0.0
        
        if not success:
            from datetime import datetime
            self._fallback_stats['last_failure_time'] = datetime.now().isoformat()
    
    # === 缓存和条件逻辑管理方法 ===
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if not self.enable_caching or not self.cache:
            return {'enabled': False, 'message': '缓存未启用'}
        
        return {
            'enabled': True,
            **self.cache.get_stats()
        }
    
    def clear_cache(self) -> bool:
        """清空缓存"""
        if not self.enable_caching or not self.cache:
            return False
        
        self.cache.clear()
        self._logger.info("AI调用缓存已清空")
        return True
    
    def reset_cache_statistics(self) -> bool:
        """重置缓存统计信息"""
        if not self.enable_caching or not self.cache:
            return False
        
        self.cache.reset_stats()
        self._logger.info("缓存统计信息已重置")
        return True
    
    def get_condition_checker_config(self) -> Dict[str, Any]:
        """获取条件检查器配置"""
        if not self.enable_conditional_logic or not self.condition_checker:
            return {'enabled': False, 'message': '条件逻辑未启用'}
        
        return {
            'enabled': True,
            **self.condition_checker.get_configuration()
        }
    
    def update_condition_checker_config(self, 
                                       significance_threshold: Optional[float] = None,
                                       time_threshold_seconds: Optional[int] = None) -> bool:
        """更新条件检查器配置"""
        if not self.enable_conditional_logic or not self.condition_checker:
            return False
        
        if significance_threshold is not None:
            self.condition_checker.set_significance_threshold(significance_threshold)
            self._logger.info(f"显著性阈值已更新为: {significance_threshold}")
        
        if time_threshold_seconds is not None:
            self.condition_checker.set_time_threshold(time_threshold_seconds)
            self._logger.info(f"时间阈值已更新为: {time_threshold_seconds}秒")
        
        return True
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """获取综合性能统计信息"""
        stats = {
            'ai_updater_service': {
                'llm_model': getattr(self.llm, 'model_name', getattr(self.llm, 'model', 'unknown')),
                'max_retries': self.max_retries,
                'retry_delay': self.retry_delay,
                'template_count': len(self.template_manager.list_templates()),
                'fallback_strategies_count': len(self.fallback_strategies)
            },
            'caching': self.get_cache_statistics(),
            'conditional_logic': self.get_condition_checker_config(),
            'fallback_stats': self.get_fallback_statistics()
        }
        
        return stats

class RegisteredAgent:
    """存储已注册的 Agent 信息"""
    def __init__(self, name: str, instance: Agent, description: str):
        self.name = name
        self.instance = instance
        self.description = description

class WorkflowState:
    """工作流状态管理"""
    def __init__(self):
        # === 现有字段保持不变 ===
        self.current_step_index = 0
        self.loop_counters = {}      # {"loop_to_step3": 2}
        self.fix_counter = 0         # 修复任务计数
        self.loop_targets = []       # 循环目标历史
        self.max_loops = 5           # 最大循环次数限制
        self.context_variables = {}  # 上下文变量
        self.branch_history = []     # 分支历史
        
        # === 加载配置系统参数 ===
        if CONFIG_SYSTEM_AVAILABLE:
            try:
                config = get_config()
                state_config = config.state_history
                self._max_history_size = state_config.max_length
                self._auto_cleanup_enabled = state_config.auto_cleanup
                self._cleanup_interval_hours = state_config.cleanup_interval_hours
                self._compression_enabled = state_config.enable_compression
                self._compression_threshold = state_config.compression_threshold
                logger.info(f"使用配置系统参数: 历史长度={self._max_history_size}, 自动清理={self._auto_cleanup_enabled}")
            except Exception as e:
                logger.warning(f"加载配置系统失败，使用默认参数: {e}")
                self._max_history_size = 50
                self._auto_cleanup_enabled = True
                self._cleanup_interval_hours = 24
                self._compression_enabled = False
                self._compression_threshold = 1000
        else:
            # 使用默认配置
            self._max_history_size = 50
            self._auto_cleanup_enabled = True
            self._cleanup_interval_hours = 24
            self._compression_enabled = False
            self._compression_threshold = 1000
        
        # === 新增：全局状态管理 ===
        self._global_state = ""                    # 当前自然语言状态
        self._state_update_enabled = True         # 是否启用状态更新
        self._state_history = deque(maxlen=self._max_history_size)    # 状态历史，使用配置的长度
        
        # === 日志记录器 ===
        self._logger = logging.getLogger(f"{__name__}.WorkflowState")
        
        # === 并发保护 ===
        self._state_lock = threading.RLock()  # 可重入锁，支持同一线程多次获取
        
        # === 性能监控集成 ===
        self._performance_monitor = None
        if PERFORMANCE_MONITOR_AVAILABLE:
            try:
                self._performance_monitor = get_performance_monitor()
                self._logger.debug("性能监控系统已集成到WorkflowState")
            except Exception as e:
                self._logger.warning(f"性能监控系统集成失败: {e}")
        
        self._logger.debug(f"WorkflowState初始化完成 - 全局状态管理已启用，历史长度={self._max_history_size}，并发保护已激活")

    def should_break_loop(self, target_step_id):
        """检查是否应该退出循环（防止无限循环）"""
        loop_key = f"loop_to_{target_step_id}"
        return self.loop_counters.get(loop_key, 0) >= self.max_loops
    
    def increment_loop_counter(self, target_step_id):
        """增加循环计数器"""
        loop_key = f"loop_to_{target_step_id}"
        self.loop_counters[loop_key] = self.loop_counters.get(loop_key, 0) + 1
    
    def reset_step_status_from(self, start_index, plan):
        """重置从指定索引开始的步骤状态"""
        for i in range(start_index, len(plan)):
            if plan[i].get('status') in ['completed', 'failed']:
                plan[i]['status'] = 'pending'
    
    # === 全局状态管理方法 ===
    
    def get_global_state(self) -> str:
        """获取当前全局状态"""
        with self._state_lock:
            return self._global_state
    
    def set_global_state(self, new_state: str, source: Optional[str] = None) -> None:
        """设置全局状态（受更新开关控制）"""
        with self._state_lock:
            if not self._state_update_enabled:
                self._logger.debug("状态更新被禁用，跳过状态设置")
                return
            
            if not isinstance(new_state, str):
                raise TypeError("全局状态必须是字符串类型")
            
            
            # 如果状态实际发生了变化，记录到历史
            new_state = new_state.strip()
            if new_state != self._global_state:
                # 保存当前状态到历史（不可变副本）
                if self._global_state:  # 只有在当前状态非空时才保存
                    history_entry = StateHistoryEntry(
                        timestamp=dt.now(),
                        state_snapshot=copy.deepcopy(self._global_state),
                        source=source
                    )
                    self._state_history.append(history_entry)
                    self._logger.debug(f"状态历史已更新，历史记录数量: {len(self._state_history)}")
                
                # 更新当前状态
                self._global_state = new_state
                self._logger.info(f"全局状态已更新 (来源: {source or 'unknown'}) - 新状态长度: {len(new_state)}")
            else:
                self._logger.debug("状态未发生变化，跳过更新")
    
    def is_state_update_enabled(self) -> bool:
        """检查状态更新是否启用"""
        return self._state_update_enabled
    
    def enable_state_updates(self) -> None:
        """启用状态更新"""
        with self._state_lock:
            self._state_update_enabled = True
            self._logger.info("状态更新已启用")
    
    def disable_state_updates(self) -> None:
        """禁用状态更新"""
        with self._state_lock:
            self._state_update_enabled = False
            self._logger.info("状态更新已禁用")
    
    def clear_global_state(self) -> None:
        """清空全局状态"""
        with self._state_lock:
            if self._state_update_enabled:
                self._global_state = ""
                self._logger.info("全局状态已清空")
            else:
                self._logger.debug("状态更新被禁用，跳过状态清空")
    
    # === 状态历史管理方法 ===
    
    def get_state_history(self, limit: Optional[int] = None) -> List[StateHistoryEntry]:
        """获取状态历史记录"""
        with self._state_lock:
            history_list = list(self._state_history)
            if limit is not None and limit > 0:
                return history_list[-limit:]
            return history_list
    
    def get_state_history_count(self) -> int:
        """获取状态历史记录数量"""
        with self._state_lock:
            return len(self._state_history)
    
    def clear_state_history(self) -> None:
        """清空状态历史"""
        with self._state_lock:
            if self._state_update_enabled:
                old_count = len(self._state_history)
                self._state_history.clear()
                self._logger.info(f"状态历史已清空 (清空前记录数: {old_count})")
            else:
                self._logger.debug("状态更新被禁用，跳过历史清空")
    
    def get_state_summary(self) -> str:
        """获取状态摘要，包含当前状态和历史概览"""
        with self._state_lock:
            current = self._global_state if self._global_state else "无当前状态"
            history_count = len(self._state_history)
            
            if history_count == 0:
                return f"当前状态: {current}\n历史记录: 无"
            
            latest_history = self._state_history[-1] if self._state_history else None
            latest_time = latest_history.timestamp.strftime("%H:%M:%S") if latest_history else "未知"
            
            return f"""当前状态: {current}
历史记录: {history_count}条 (最新更新: {latest_time})"""
    
    def set_max_history_size(self, max_size: int) -> None:
        """设置最大历史记录数量"""
        if max_size <= 0:
            raise ValueError("最大历史记录数量必须大于0")
        
        with self._state_lock:
            old_size = self._max_history_size
            old_count = len(self._state_history)
            self._max_history_size = max_size
            
            # 如果需要，截断现有历史
            if len(self._state_history) > max_size:
                # 保留最新的记录
                new_history = deque(list(self._state_history)[-max_size:], maxlen=max_size)
                self._state_history = new_history
                self._logger.info(f"历史记录已截断 - 旧限制: {old_size}, 新限制: {max_size}, 记录数变化: {old_count} -> {len(self._state_history)}")
            else:
                self._logger.info(f"历史记录大小限制已更新 - 旧限制: {old_size}, 新限制: {max_size}, 当前记录数: {len(self._state_history)}")
    
    # === AI状态更新器集成方法 ===
    
    def __init_ai_updater(self) -> None:
        """初始化AI状态更新器（懒加载）"""
        if not hasattr(self, '_ai_updater') or self._ai_updater is None:
            try:
                self._ai_updater = AIStateUpdaterService(llm_deepseek)
                
                # 如果启用了新的响应解析器，将其传递给AI状态更新器
                if (hasattr(self, 'enable_response_analysis') and 
                    self.enable_response_analysis and 
                    hasattr(self, 'response_parser') and 
                    self.response_parser is not None):
                    # 替换AI状态更新器的解析器为新的多方案解析器
                    self._ai_updater.response_parser = self.response_parser
                    self._logger.info("AI状态更新器已同步使用新的多方案响应解析器")
                
                self._logger.info("AI状态更新器初始化成功")
            except Exception as e:
                self._logger.error(f"AI状态更新器初始化失败: {e}")
                self._ai_updater = None
    
    def update_state_with_ai(self, context: Dict[str, Any]) -> bool:
        """
        使用AI更新状态
        
        Args:
            context: 包含步骤信息、执行结果等的上下文字典
                    支持的字段：
                    - step_info: 步骤信息字典
                    - execution_result: 执行结果
                    - step_status: 步骤状态 ('completed', 'failed', etc.)
                    - error_info: 错误信息
        
        Returns:
            是否成功更新状态
        """
        try:
            # 懒加载AI更新器
            self.__init_ai_updater()
            
            if self._ai_updater is None:
                self._logger.warning("AI状态更新器不可用，跳过AI状态更新")
                return False
            
            # 使用AI生成新状态
            new_state = self._ai_updater.update_state(self, context)
            
            if new_state:
                # 更新状态，标记来源为AI
                self.set_global_state(new_state, source="AI_DeepSeek")
                self._logger.info("AI状态更新成功")
                return True
            else:
                self._logger.debug("AI判断无需更新状态或更新失败")
                return False
                
        except Exception as e:
            self._logger.error(f"AI状态更新过程出错: {e}")
            return False
    
    def set_ai_updater(self, updater: AIStateUpdater) -> None:
        """
        设置自定义AI状态更新器
        
        Args:
            updater: 实现AIStateUpdater接口的更新器实例
        """
        with self._state_lock:
            if not isinstance(updater, AIStateUpdater):
                raise TypeError("更新器必须实现AIStateUpdater接口")
            
            self._ai_updater = updater
            self._logger.info(f"自定义AI状态更新器设置成功: {type(updater).__name__}")
    
    def get_ai_updater_status(self) -> Dict[str, Any]:
        """
        获取AI状态更新器状态信息
        
        Returns:
            包含状态信息的字典
        """
        try:
            self.__init_ai_updater()
            
            if self._ai_updater is None:
                return {
                    "available": False,
                    "error": "AI状态更新器不可用",
                    "type": None
                }
            
            return {
                "available": True,
                "type": type(self._ai_updater).__name__,
                "model": getattr(self._ai_updater.llm, 'model', 'Unknown') if hasattr(self._ai_updater, 'llm') else 'Unknown',
                "max_retries": getattr(self._ai_updater, 'max_retries', 'Unknown'),
                "state_update_enabled": self.is_state_update_enabled()
            }
            
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "type": None
            }

    def __getstate__(self):
        """自定义序列化状态，排除不可序列化的对象"""
        state = self.__dict__.copy()
        # 移除线程锁，它不能被序列化 - 使用正确的属性名
        state.pop('_state_lock', None)
        return state
    
    def __setstate__(self, state):
        """自定义反序列化状态，重新创建线程锁"""
        self.__dict__.update(state)
        # 重新创建线程锁 - 使用正确的属性名
        self._state_lock = threading.RLock()
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用统计信息"""
        import sys
        import pickle
        
        try:
            # 计算对象大小
            global_state_size = sys.getsizeof(self._global_state)
            history_size = sys.getsizeof(self._state_history)
            
            # 计算序列化大小
            serialized_data = pickle.dumps(self)
            serialized_size = len(serialized_data)
            
            # 计算历史记录统计
            history_count = len(self._state_history)
            avg_state_size = 0
            if history_count > 0:
                total_state_size = sum(sys.getsizeof(entry.state_snapshot) for entry in self._state_history)
                avg_state_size = total_state_size / history_count
            
            return {
                'global_state_size_bytes': global_state_size,
                'history_total_size_bytes': history_size,
                'serialized_size_bytes': serialized_size,
                'history_count': history_count,
                'average_state_size_bytes': avg_state_size,
                'memory_efficiency': history_count / (serialized_size / 1024) if serialized_size > 0 else 0,
                'compression_ratio': (global_state_size + history_size) / serialized_size if serialized_size > 0 else 1.0
            }
        except Exception as e:
            logger.error(f"获取内存使用统计失败: {e}")
            return {
                'error': str(e),
                'global_state_size_bytes': sys.getsizeof(self._global_state),
                'history_count': len(self._state_history),
                'status': 'partial_data'
            }
    
    def compress_history(self, compression_level: int = 6) -> bool:
        """压缩历史记录以节省内存"""
        try:
            import gzip
            
            if not self._state_history:
                return True
                
            with self._state_lock:
                # 创建新的压缩历史记录列表
                compressed_history = deque(maxlen=self._max_history_size)
                compressed_count = 0
                
                for entry in self._state_history:
                    if isinstance(entry.state_snapshot, str) and not entry.state_snapshot.startswith("__COMPRESSED__"):
                        # 压缩字符串状态
                        original_data = entry.state_snapshot.encode('utf-8')
                        compressed_data = gzip.compress(original_data, compresslevel=compression_level)
                        
                        # 只有在压缩能显著减少大小时才使用压缩
                        if len(compressed_data) < len(original_data) * 0.8:
                            # 创建新的压缩条目
                            compressed_snapshot = f"__COMPRESSED__{compressed_data.hex()}"
                            compressed_entry = StateHistoryEntry(
                                timestamp=entry.timestamp,
                                state_snapshot=compressed_snapshot,
                                source=entry.source
                            )
                            compressed_history.append(compressed_entry)
                            compressed_count += 1
                        else:
                            # 压缩效果不显著，保持原样
                            compressed_history.append(entry)
                    else:
                        # 已经压缩或非字符串，保持原样
                        compressed_history.append(entry)
                
                # 替换原历史记录
                self._state_history = compressed_history
                logger.info(f"历史记录压缩完成，压缩了 {compressed_count}/{len(self._state_history)} 条记录")
                return True
                
        except Exception as e:
            logger.error(f"历史记录压缩失败: {e}")
            return False
    
    def decompress_history_entry(self, state_snapshot: str) -> str:
        """解压缩单个历史记录条目"""
        try:
            if state_snapshot.startswith("__COMPRESSED__"):
                import gzip
                
                # 提取压缩数据
                compressed_hex = state_snapshot[14:]  # 移除 "__COMPRESSED__" 前缀
                compressed_data = bytes.fromhex(compressed_hex)
                
                # 解压缩
                decompressed_data = gzip.decompress(compressed_data)
                return decompressed_data.decode('utf-8')
            else:
                # 未压缩的数据，直接返回
                return state_snapshot
        except Exception as e:
            logger.error(f"解压缩历史记录失败: {e}")
            return state_snapshot  # 返回原始数据作为fallback
    
    def get_decompressed_history(self, limit: Optional[int] = None) -> List[StateHistoryEntry]:
        """获取解压缩后的历史记录"""
        with self._state_lock:
            history = list(self._state_history)[:limit] if limit else list(self._state_history)
            
            # 解压缩状态快照
            decompressed_history = []
            for entry in history:
                decompressed_snapshot = self.decompress_history_entry(entry.state_snapshot)
                decompressed_entry = StateHistoryEntry(
                    timestamp=entry.timestamp,
                    state_snapshot=decompressed_snapshot,
                    source=entry.source
                )
                decompressed_history.append(decompressed_entry)
            
            return decompressed_history
    
    def optimize_memory(self, enable_compression: bool = True, compression_level: int = 6) -> Dict[str, Any]:
        """执行内存优化"""
        optimization_results = {
            'initial_usage': self.get_memory_usage(),
            'optimizations_applied': [],
            'final_usage': {},
            'success': False
        }
        
        try:
            # 1. 历史记录压缩
            if enable_compression:
                if self.compress_history(compression_level):
                    optimization_results['optimizations_applied'].append('history_compression')
                    logger.info("历史记录压缩优化已应用")
                
            # 2. 清理空字符串状态（如果存在）
            cleaned_count = 0
            with self._state_lock:
                original_count = len(self._state_history)
                self._state_history = deque(
                    [entry for entry in self._state_history if entry.state_snapshot.strip()],
                    maxlen=self._max_history_size
                )
                cleaned_count = original_count - len(self._state_history)
            
            if cleaned_count > 0:
                optimization_results['optimizations_applied'].append(f'cleaned_{cleaned_count}_empty_entries')
                logger.info(f"清理了 {cleaned_count} 个空历史记录条目")
            
            # 3. 获取优化后的内存使用情况
            optimization_results['final_usage'] = self.get_memory_usage()
            optimization_results['success'] = True
            
            # 计算优化效果
            initial_size = optimization_results['initial_usage'].get('serialized_size_bytes', 0)
            final_size = optimization_results['final_usage'].get('serialized_size_bytes', 0)
            
            if initial_size > 0:
                space_saved = initial_size - final_size
                percentage_saved = (space_saved / initial_size) * 100
                optimization_results['space_saved_bytes'] = space_saved
                optimization_results['percentage_saved'] = percentage_saved
                
                logger.info(f"内存优化完成，节省了 {space_saved} 字节 ({percentage_saved:.2f}%)")
            
        except Exception as e:
            logger.error(f"内存优化过程中出现错误: {e}")
            optimization_results['error'] = str(e)
        
        return optimization_results

class MultiStepAgent_v2(Agent):
    """
    新版多步骤智能体：不依赖 workflow engine、state manager、agent registry。
    只实现 execute_multi_step，计划和状态存储在 StatefulExecutor 的变量中，成员 Agent 通过变量注册。
    """

    def __init__(
        self,
        llm: BaseChatModel,
        registered_agents: Optional[List[RegisteredAgent]] = None,
        max_retries: int = 3,
        thinker_system_message: Optional[str] = None,
        thinker_chat_system_message: Optional[str] = None,
        planning_prompt_template: Optional[str] = None,  # 新增参数
        use_autonomous_planning: bool = True,  # 新增：是否使用自主规划模式
    ):
        team_system_message=thinker_system_message
        if team_system_message is None:
            team_system_message=team_manager_system_message_no_share_state
        
        super().__init__(
            llm=llm,
            stateful=True,
            thinker_system_message=team_system_message,
            thinker_chat_system_message=thinker_chat_system_message,
            max_retries=max_retries,
        )
        self.device = StatefulExecutor()
        self.registered_agents = registered_agents if registered_agents is not None else []
        self.max_retries = max_retries
        self.thinker_chat_system_message = thinker_chat_system_message
        # 注册成员 Agent 到 StatefulExecutor 的变量空间
        for spec in self.registered_agents:
            self.device.set_variable(spec.name, spec.instance)
        # 初始化 current_plan
        self.device.set_variable("current_plan", [])
        # 初始化工作流状态 (方案2)
        self.workflow_state = WorkflowState()
        self.original_goal = ""
        self.use_autonomous_planning = use_autonomous_planning
        
        # 初始化错误处理机制
        self.error_dispatcher = WorkflowErrorDispatcher()
        # 注册通用错误处理器
        self.error_dispatcher.register_handler(GenericErrorHandler())
        
        # 错误处理统计
        self.error_statistics = {
            'total_errors': 0,
            'handled_errors': 0,
            'unhandled_errors': 0,
            'error_types': {},
            'recovery_success_rate': 0.0
        }
        
        # 初始化指令优化系统
        self.instruction_optimizer = StateAwareInstructionOptimizer(
            strategy=OptimizationStrategy.MODERATE
        )
        self.optimization_enabled = True  # 默认启用指令优化
        
        # 初始化决策管理系统
        self.decision_manager = StateAwareDecisionManager()
        logger.info("状态感知决策管理器已初始化")
        
        # 设置默认的计划生成提示词模板
        if planning_prompt_template:
            # 用户提供了自定义模板，使用翻译模式
            self.planning_prompt_template = planning_prompt_template
            self.use_autonomous_planning = False
        elif use_autonomous_planning:
            # 使用自主规划模式的默认模板
            self.planning_prompt_template = """
# 任务背景
你是一个多智能体团队的协调者，负责将复杂任务分解为可执行的步骤，并为每个步骤分配合适的执行者。

# 可用智能体列表
{available_agents_str}

# 主任务
{main_instruction}

# 三阶段执行计划框架
请将任务分解为三个关键阶段：

1. 信息收集阶段: 明确为达成目标需要收集哪些信息，每条信息为什么必要
2. 执行阶段: 具体的实现步骤，每一步如何利用收集的信息
3. 验证与修复阶段: 如何验证结果，以及在失败时需要收集什么额外信息来修复问题

# 输出要求
请将主任务分解为有序的步骤，每个步骤必须指定以下信息:
1. id: 步骤唯一标识符(建议使用"info1", "exec2", "verify3"等形式，以表明所属阶段)
2. name: 简短的步骤名称
3. instruction: 详细的执行指令，需要清晰明确
4. agent_name: 执行该步骤的智能体名称，必须从以下列表中选择: {available_agent_names}
5. instruction_type: 指令类型(execution/information) - 见下方说明
6. phase: 步骤所属阶段(information/execution/verification)
7. expected_output: 预期输出，明确该步骤应该产生什么结果
8. prerequisites: 执行此步骤需要满足的先决条件(自然语言描述)，如无要求则为"无"

# 智能体构成说明
每个智能体由两部分组成：
1. 记忆：存储对话历史、知识和状态信息
2. 有状态的jupyter notebook kernel：用于执行代码和与外部环境交互

# 指令类型说明
- execution: 执行性任务，会调用jupyter notebook执行代码对外部世界产生行为或观察，同时改变智能体的记忆（如执行代码、文件操作、数据写入、观察外部环境等）
- information: 信息性任务，只是对智能体记忆的查询或修改，不会调用jupyter notebook（如查询历史对话、告知状态等）

# 规划规则
1. 分析任务特点，合理拆分步骤
2. 根据每个智能体的专长分配任务
3. 用自然语言描述每个步骤的先决条件，而非硬编码依赖关系
4. 为每个步骤提供足够详细的指令
5. 信息收集阶段应彻底，确保执行阶段有足够输入数据
6. 执行阶段应明确如何使用前面步骤收集的信息
7. 验证阶段应定义明确的成功标准，并预见可能的失败场景
"""
        else:
            # 使用翻译模式的默认模板 (方案2: 动态决策控制)
            self.planning_prompt_template = """
# 任务背景
你是一个工作流翻译器，负责将用户用自然语言描述的步骤翻译成简单的线性执行计划。复杂的控制流逻辑（如循环、条件分支）将由决策者在执行过程中动态处理。

# 重要原则
- **严格按照用户定义的步骤进行翻译，不要添加、删除或修改步骤数量和核心内容**
- **保持用户原始步骤的顺序和主要意图不变**
- **将复杂的控制流（如while循环、if条件）简化为基本的线性步骤**
- **对于缺失的字段信息，可以基于上下文进行合理推测和补充**

# 可用智能体列表
{available_agents_str}

# 用户原始步骤描述
{main_instruction}

# 翻译要求
请将用户描述的工作流翻译成简单的线性步骤序列，每个步骤包含:
1. id: 步骤唯一标识符(建议使用"step1", "step2"等形式，按用户步骤顺序)
2. name: 基于用户步骤内容的简短名称
3. instruction: 用户原始步骤的详细描述，保持原意不变
4. agent_name: 最适合执行该步骤的智能体名称，必须从以下列表中选择: {available_agent_names}
5. instruction_type: 指令类型(execution/information) - 见下方说明
6. phase: 步骤类型(information/execution/verification)
7. expected_output: 基于步骤内容推断的预期输出
8. prerequisites: 执行此步骤需要满足的先决条件(自然语言描述)，如无要求则为"无"

# 智能体构成说明
每个智能体由两部分组成：
1. 记忆：存储对话历史、知识和状态信息
2. 有状态的jupyter notebook kernel：用于执行代码和与外部环境交互

# 指令类型说明
- execution: 执行性任务，会调用jupyter notebook执行代码对外部世界产生行为或观察，同时改变智能体的记忆（如执行代码、文件操作、数据写入、观察外部环境等）
- information: 信息性任务，只是对智能体记忆的查询或修改，不会调用jupyter notebook（如查询历史对话、告知状态等）

# 控制流处理原则
- **while循环**: 将循环体内的步骤提取为普通步骤，循环控制由决策者处理
- **if条件**: 将条件判断和分支操作提取为普通步骤，条件判断由决策者处理
- **复杂逻辑**: 分解为基本的执行步骤和决策步骤

# 翻译规则
1. **严格遵循用户步骤的数量和顺序**
2. **不要合并、拆分或重新组织用户的步骤**
3. **保持每个步骤的核心意图和主要内容**
4. 根据步骤内容选择最合适的智能体
5. 根据步骤性质判断instruction_type和phase
6. 用自然语言描述每个步骤的先决条件，而非硬编码依赖关系
7. **对于缺失字段的推测原则**：
   - agent_name: 根据步骤内容推测最适合的智能体
   - instruction_type: 根据步骤性质推测(需要调用jupyter notebook执行代码、文件操作、数据写入等选execution，仅需查询或修改智能体记忆选information)
   - phase: 根据步骤在整体流程中的作用推测(收集信息选information，具体实施选execution，检查验证选verification)
   - expected_output: 根据步骤描述推测可能的输出结果
   - prerequisites: 根据步骤间的逻辑关系描述先决条件
8. **对于instruction字段的处理**：保持用户原始描述，必要时可适当补充执行细节以确保可操作性

# 示例翻译

## 用户输入：
```
1. 调用coder实现计算器
2. 调用coder保存代码  
while true {{
    3. 调用tester运行测试
    4. 如果运行正确: 终止工作流
    5. 如果报错: 发给coder修复
}}
```

## 翻译输出：
```json
{{
  "steps": [
    {{
      "id": "step1",
      "name": "实现计算器",
      "instruction": "调用coder实现一个简单的计算器类，要包含单元测试",
      "agent_name": "coder",
      "instruction_type": "execution",
      "phase": "execution",
      "expected_output": "计算器类代码",
      "prerequisites": "无"
    }},
    {{
      "id": "step2", 
      "name": "保存代码",
      "instruction": "调用coder把代码保存到文件",
      "agent_name": "coder",
      "instruction_type": "execution",
      "phase": "execution",
      "expected_output": "代码文件",
      "prerequisites": "计算器代码已实现"
    }},
    {{
      "id": "step3",
      "name": "运行测试",
      "instruction": "调用tester运行测试，检查代码是否正确",
      "agent_name": "tester",
      "instruction_type": "execution", 
      "phase": "verification",
      "expected_output": "测试结果",
      "prerequisites": "代码文件已保存"
    }},
    {{
      "id": "step4",
      "name": "分析测试结果并决策",
      "instruction": "分析测试结果，如果测试通过则完成工作流，如果测试失败则生成修复任务并循环回到测试步骤",
      "agent_name": "tester",
      "instruction_type": "information",
      "phase": "verification", 
      "expected_output": "决策结果",
      "prerequisites": "测试已完成并有结果"
    }}
  ]
}}
```
"""
        
        # 初始化多方案响应解析器
        self._init_response_parser()

    def _init_response_parser(self, 
                             parser_method: Union[str, ParserMethod] = "rule",
                             parser_config: Optional[Dict[str, Any]] = None,
                             enable_response_analysis: bool = True,
                             enable_execution_monitoring: bool = True):
        """
        初始化多方案响应解析器
        
        Args:
            parser_method: 解析器方法 ("rule", "transformer", "deepseek", "embedding", "hybrid")
            parser_config: 解析器配置参数
            enable_response_analysis: 是否启用响应分析
            enable_execution_monitoring: 是否启用执行监控
        """
        # 解析器配置
        self.enable_response_analysis = enable_response_analysis
        self.enable_execution_monitoring = enable_execution_monitoring
        
        if not RESPONSE_PARSER_AVAILABLE:
            logger.warning("多方案响应解析器不可用，跳过初始化")
            self.response_parser = None
            self.parsed_responses_history = []
            return
        
        try:
            # 初始化解析器
            if isinstance(parser_method, str):
                parser_method = ParserMethod(parser_method) if parser_method in ["rule", "transformer", "deepseek", "embedding", "hybrid"] else ParserMethod.RULE
            
            parser_config = parser_config or {}
            
            # 根据方法类型创建解析器
            if parser_method == ParserMethod.RULE:
                self.response_parser = ParserFactory.create_rule_parser(**parser_config)
            elif parser_method == ParserMethod.TRANSFORMER:
                model_name = parser_config.get('model_name', 'hfl/chinese-bert-wwm-ext')
                # 从parser_config中移除model_name以避免重复传递
                transformer_config = {k: v for k, v in parser_config.items() if k != 'model_name'}
                self.response_parser = ParserFactory.create_transformer_parser(model_name=model_name, **transformer_config)
            elif parser_method == ParserMethod.DEEPSEEK:
                api_key = parser_config.get('api_key') or parser_config.get('DEEPSEEK_API_KEY')
                if not api_key:
                    import os
                    api_key = os.getenv('DEEPSEEK_API_KEY')
                if api_key:
                    # 从parser_config中移除api_key和api_base以避免重复传递
                    deepseek_config = {k: v for k, v in parser_config.items() if k not in ['api_key', 'api_base', 'DEEPSEEK_API_KEY']}
                    api_base = parser_config.get('api_base')
                    self.response_parser = ParserFactory.create_deepseek_parser(api_key=api_key, api_base=api_base, **deepseek_config)
                else:
                    logger.warning("DeepSeek API密钥未配置，降级到规则解析器")
                    self.response_parser = ParserFactory.create_rule_parser(**parser_config)
            elif parser_method == ParserMethod.EMBEDDING:
                model_name = parser_config.get('model_name', 'paraphrase-multilingual-MiniLM-L12-v2')
                # 从parser_config中移除model_name以避免重复传递
                embedding_config = {k: v for k, v in parser_config.items() if k != 'model_name'}
                self.response_parser = ParserFactory.create_embedding_parser(model_name=model_name, **embedding_config)
            else:  # hybrid
                primary_method = parser_config.get('primary_method', ParserMethod.RULE)
                fallback_chain = parser_config.get('fallback_chain', [ParserMethod.RULE])
                filtered_config = {k: v for k, v in parser_config.items() if k not in ['primary_method', 'fallback_chain']}
                self.response_parser = ParserFactory.create_hybrid_parser(
                    primary_method=primary_method,
                    fallback_chain=fallback_chain,
                    **filtered_config
                )
                
            # 初始化解析历史
            self.parsed_responses_history = []
            
            # 解析器参数
            self.confidence_threshold = parser_config.get('confidence_threshold', 0.6)
            self.auto_retry_on_low_confidence = parser_config.get('auto_retry', False)
            
            logger.info(f"多方案响应解析器初始化完成，方法: {parser_method}")
            
        except Exception as e:
            logger.error(f"响应解析器初始化失败: {e}，禁用解析功能")
            self.response_parser = None
            self.parsed_responses_history = []

    def register_agent(self, name: str, instance: Agent):
        """注册一个新的 Agent。"""
        # 获取Agent的描述，如果没有api_specification属性则使用默认描述
        description = getattr(instance, 'api_specification', f"{name}智能体，通用任务执行者")
        spec = RegisteredAgent(name=name, instance=instance, description=description)
        self.registered_agents.append(spec)
        self.device.set_variable(spec.name, spec.instance)
        logger.debug(f"已注册 Agent: {name}")
    


    def plan_execution(self, main_instruction: str) -> List[Dict[str, Any]]:
        """
        根据主指令规划执行步骤，支持自定义提示词模板。
        """
        
        # 构建可用 Agent 的描述字符串
        available_agents_str = "\n".join(
            [f"- {spec.name}: {spec.description}" for spec in self.registered_agents]
        )
        if not available_agents_str:
            available_agents_str = "无可用 Agent。请确保已注册 Agent。"
            
        # 获取可用 Agent 名称列表
        available_agent_names = [spec.name for spec in self.registered_agents] or ["无"]
        
        # 检查是否有上一次失败的验证结果
        previous_attempt_failed = False
        previous_verification = None
        previous_plan = None
        
        if hasattr(self, 'device'):
            try:
                previous_attempt_failed_var = self.device.get_variable("previous_attempt_failed")
                previous_attempt_failed = previous_attempt_failed_var if previous_attempt_failed_var is not None else False
            except:
                previous_attempt_failed = False
                
            try:
                previous_verification = self.device.get_variable("previous_verification")
            except:
                previous_verification = None
                
            try:
                previous_plan = self.device.get_variable("previous_plan")
            except:
                previous_plan = None

        # 使用模板生成提示词
        planning_prompt = self.planning_prompt_template.format(
            available_agents_str=available_agents_str,
            main_instruction=main_instruction,
            available_agent_names=', '.join(available_agent_names)
        )

        # 如果有上一次失败的验证结果和执行计划，添加到提示中
        if previous_attempt_failed and previous_verification:
            if previous_plan:
                planning_prompt += f"""

# 上一次执行的计划
```json
{json.dumps(previous_plan, indent=2, ensure_ascii=False)}
```

⚠️ 注意：上一次执行计划未能达成目标，请仔细分析以下验证结果，并改进您的计划：

# 上一次验证失败的原因
{previous_verification}

# 改进建议
- 特别关注上一次失败的原因，确保新计划能解决这些问题
- 考虑添加更多的步骤或更健壮的验证方法
- 为已知的失败点设计专门的修复策略
"""

        # 添加输出格式要求
        first_agent_name = available_agent_names[0] if available_agent_names and available_agent_names[0] != "无" else "智能体名称"
        planning_prompt += f"""

# 输出格式
必须严格按照以下JSON格式输出:
```json
{{
  "steps": [
    {{
      "id": "step1",
      "name": "步骤名称",
      "instruction": "详细的执行指令...",
      "agent_name": "{first_agent_name}",
      "instruction_type": "execution",
      "expected_output": "预期输出",
      "dependencies": []
    }}
  ]
}}
```

# 重要提示
- 每个步骤都要指定指令类型(instruction_type)
- 确保步骤之间的数据流动清晰，后续步骤能够获取和使用前面步骤的输出结果
- 每个步骤都应有明确的目标和可验证的输出
- 步骤中的instruction不要使用三个双引号包裹
"""

        # 尝试使用更兼容的response_format（移除schema字段）
        response_format = {
            "type": "json_object"
        }

        try:
            # 使用chat_sync并添加response_format参数
            result = self.chat_sync(planning_prompt, response_format=response_format)
            # 从Result对象中提取内容
            if result.success:
                plan_result = result.return_value if result.return_value else result.stdout
            else:
                logger.warning(f"chat_sync返回失败: {result.stderr}")
                # 回退到无格式约束方式
                result = self.chat_sync(planning_prompt)
                plan_result = result.return_value if result.return_value else result.stdout

            from autogen.code_utils import extract_code
            
            # 判断是否接收到错误消息
            if isinstance(plan_result, str) and "error" in plan_result:
                error_obj = json.loads(plan_result)
                logger.warning(f"LLM响应包含错误: {error_obj.get('error')}")
                # 回退到再次尝试
                result = self.chat_sync(planning_prompt)
                plan_result = result.return_value if result.return_value else result.stdout
            
            # 尝试提取和解析JSON
            try:
                extracted_codes = extract_code(plan_result)
                if extracted_codes:
                    plan_data = json.loads(extracted_codes[0][1])
                else:
                    # 直接尝试解析整个响应
                    plan_data = json.loads(plan_result)
            except:
                # 如果提取失败，尝试直接解析
                plan_data = json.loads(plan_result)
                
            # 处理两种可能的格式：直接步骤数组或包含steps字段的对象
            if isinstance(plan_data, list):
                plan = plan_data  # 直接是步骤数组
                logger.debug(f"解析到步骤数组，共 {len(plan)} 个步骤")
            else:
                plan = plan_data.get("steps", [])  # 从对象中获取steps
                logger.debug(f"从对象中解析到步骤，共 {len(plan)} 个步骤")
        except Exception as e:
            logger.warning(f"计划生成第一次尝试失败: {e}")
            # 回退到普通方式再试一次
            try:
                from langchain_core.messages import HumanMessage
                # 检查thinker.memory最后一条是否为HumanMessage，如果是则删除
                if hasattr(self, "thinker") and hasattr(self.thinker, "memory") and self.thinker.memory:
                    last_msg = self.thinker.memory[-1]
                    if isinstance(last_msg, HumanMessage):
                        self.thinker.memory.pop()
                
                result = self.chat_sync(planning_prompt)
                plan_result = result.return_value if result.return_value else result.stdout
                
                # 尝试多种解析方式
                try:
                    # 首先判断plan_result是否以```json开头
                    if plan_result.startswith("```json"):
                        plan_result = plan_result[len("```json"):].strip()
                        # 去除结尾的```
                        if plan_result.endswith("```"):
                            plan_result = plan_result[:-len("```")]
                            
                    # 首先尝试直接解析
                    plan_data = json.loads(plan_result)
                    if isinstance(plan_data, list):
                        plan = plan_data
                    else:
                        plan = plan_data.get("steps", [])
                except:
                    # 尝试提取JSON部分
                    import re
                    json_matches = re.findall(r'\[[\s\S]*?\]|\{[\s\S]*?\}', plan_result)
                    if json_matches:
                        for json_str in json_matches:
                            try:
                                plan_data = json.loads(json_str)
                                if isinstance(plan_data, list):
                                    plan = plan_data
                                    break
                                elif isinstance(plan_data, dict) and "steps" in plan_data:
                                    plan = plan_data["steps"]
                                    break
                            except:
                                continue
                    
                    if not locals().get('plan'):
                        # 如果还是失败，尝试查找 JSON 数组格式
                        array_match = re.search(r'\[\s*\{.*?\}\s*\]', plan_result, re.DOTALL)
                        if array_match:
                            try:
                                plan = json.loads(array_match.group(0))
                            except:
                                plan = []
            except Exception as e2:
                logger.error(f"解析计划失败: {e2}")
                plan = []
        
        # 确保 plan 是列表且有内容
        if not isinstance(plan, list) or not plan:
            logger.warning("计划生成失败，使用单步回退计划")
            plan = [{
                "id": "fallback_step",
                "name": "执行完整任务",
                "instruction": main_instruction,
                "agent_name": self.registered_agents[0].name if self.registered_agents else "general_agent",
                "phase": "execution",
                "instruction_type": "execution",
                "expected_output": "任务完成结果",
                "prerequisites": "无"
            }]
        
        # 确保所有步骤都有必要的字段
        for i, step in enumerate(plan):
            if not isinstance(step, dict):
                logger.warning(f"步骤 {i} 不是字典格式，将被替换为默认步骤")
                plan[i] = {
                    "id": f"auto_{i}",
                    "name": f"自动步骤{i}",
                    "instruction": f"执行任务的第{i+1}部分",  # 避免直接使用原始指令
                    "agent_name": self.registered_agents[0].name if self.registered_agents else "general_agent",
                    "phase": "execution",
                    "instruction_type": "execution",
                    "expected_output": f"第{i+1}部分的执行结果",
                    "prerequisites": "无",
                    "status": "pending"
                }
                continue
                
            # 确保必要字段存在
            if "id" not in step:
                step["id"] = f"step_{i+1}"
            if "name" not in step:
                step["name"] = f"步骤{i+1}"
            if "instruction" not in step:
                step["instruction"] = f"执行任务的第{i+1}部分"  # 避免直接使用原始指令
            if "agent_name" not in step:
                step["agent_name"] = self.registered_agents[0].name if self.registered_agents else "general_agent"
            if "phase" not in step:
                step["phase"] = "execution"
            if "instruction_type" not in step:
                step["instruction_type"] = "execution"
            # 设置默认状态
            if "status" not in step:
                step["status"] = "pending"
            if "expected_output" not in step:
                step["expected_output"] = f"第{i+1}步的执行结果"
            # 向后兼容：将旧的dependencies转换为新的prerequisites
            if "dependencies" in step and not step.get("prerequisites"):
                deps = step["dependencies"]
                if deps:
                    step["prerequisites"] = f"需要完成步骤: {', '.join(deps)}"
                else:
                    step["prerequisites"] = "无"
                del step["dependencies"]
            elif "prerequisites" not in step:
                step["prerequisites"] = "无"
        
        self.device.set_variable("current_plan", plan)
        logger.debug(f"生成计划: {plan}")
        # 添加直接打印到控制台
        print(f"\n当前执行计划:\n{json.dumps(plan, ensure_ascii=False, indent=2)}\n")
        return plan

    # ====== 智能调度相关方法 ======
    
    # 注意：can_execute_step 方法已移除
    # 步骤可执行性判断现在统一由 make_decision 方法中的决策机制处理
    # 这避免了重复的LLM调用和决策逻辑分散的问题
    
    def select_next_executable_step(self, plan: List[Dict]) -> Optional[Tuple[int, Dict]]:
        """简化的步骤选择 - 统一决策机制方案2"""
        
        # 获取所有待执行步骤
        pending_steps = []
        for i, step in enumerate(plan):
            step_status = step.get('status')
            
            if step_status not in ('completed', 'skipped', 'running'):
                pending_steps.append((i, step))
        
        if not pending_steps:
            return None
        
        # 简化逻辑：按顺序返回第一个待执行步骤
        # 具体的可执行性判断和智能选择交由统一的决策机制处理
        return pending_steps[0]
    
    def _add_new_tasks(self, new_tasks: List[Dict]):
        """添加新任务到计划中"""
        if not new_tasks:
            return
            
        plan = self.get_plan()
        for new_task in new_tasks:
            # 确保新任务有必要的字段
            new_task_id = new_task.get('id', f"dynamic_{len(plan)}")
            new_task['id'] = new_task_id
            if 'status' not in new_task:
                new_task['status'] = 'pending'
            if 'prerequisites' not in new_task:
                new_task['prerequisites'] = '无'
            
            plan.append(new_task)
        
        # 更新计划
        self.device.set_variable("current_plan", plan)
        logger.debug(f"添加了 {len(new_tasks)} 个新任务")

    def get_plan(self) -> List[Dict[str, Any]]:
        """从 StatefulExecutor 获取当前计划。"""
        return self.device.get_variable("current_plan") or []

    def update_step_status(self, step_idx: int, status: str, result: Any = None):
        """更新 current_plan 中某一步骤的状态和结果。"""
        # 更新基本状态和结束时间
        code_base = f'''
current_plan[{step_idx}]["status"] = "{status}"
current_plan[{step_idx}]["end_time"] = "{dt.now().isoformat()}"
'''
        self.device.execute_code(code_base)

        if result is not None:
            # 创建结果字典 (使用 Python 布尔值)
            result_dict = {
                "success": bool(getattr(result, "success", False)), # 确保是 Python bool
                "stdout": getattr(result, "stdout", None),
                "stderr": getattr(result, "stderr", None),
                "return_value": getattr(result, "return_value", None),
            }
            # 将结果字典存入 Executor 临时变量
            temp_var_name = f"_temp_result_{step_idx}"
            self.device.set_variable(temp_var_name, result_dict)

            # 更新 plan 中的 result 字段，引用临时变量
            code_result_update = f'current_plan[{step_idx}]["result"] = {temp_var_name}'
            self.device.execute_code(code_result_update)

            # 可选：清理临时变量（如果担心命名空间污染）
            # self.device.execute_code(f'del {temp_var_name}')

    # ====== 方案2: 控制流处理方法 ======
    
    def find_step_index_by_id(self, step_id: str) -> int:
        """根据步骤ID查找索引"""
        plan = self.get_plan()
        for i, step in enumerate(plan):
            if step.get("id") == step_id:
                return i
        return -1
    
    def jump_to_step(self, target_step_id: str):
        """跳转到指定步骤"""
        target_index = self.find_step_index_by_id(target_step_id)
        if target_index >= 0:
            # 获取当前计划
            plan = self.get_plan()
            
            # 将当前步骤到目标步骤之间的所有步骤标记为已跳过(跳过依赖关系问题)
            current_index = self.workflow_state.current_step_index
            for i in range(current_index, target_index):
                if i < len(plan) and plan[i].get('status') not in ('completed', 'skipped'):
                    plan[i]['status'] = 'skipped'
                    logger.debug(f"跳过步骤 {i}: {plan[i].get('name', plan[i].get('id'))}")
            
            # 更新计划
            self.device.set_variable("current_plan", plan)
            
            # 设置当前步骤索引
            self.workflow_state.current_step_index = target_index
            logger.debug(f"跳转到步骤: {target_step_id} (索引: {target_index})")
        else:
            logger.warning(f"找不到步骤ID: {target_step_id}")
    
    def loop_back_to_step(self, target_step_id: str):
        """循环回到指定步骤"""
        # 检查是否应该退出循环
        if self.workflow_state.should_break_loop(target_step_id):
            logger.warning(f"达到最大循环次数，停止循环到步骤: {target_step_id}")
            return False
        
        target_index = self.find_step_index_by_id(target_step_id)
        if target_index >= 0:
            # 重置从目标步骤开始的所有步骤状态
            plan = self.get_plan()
            self.workflow_state.reset_step_status_from(target_index, plan)
            self.device.set_variable("current_plan", plan)
            
            # 跳转到目标步骤
            self.workflow_state.current_step_index = target_index
            
            # 增加循环计数器
            self.workflow_state.increment_loop_counter(target_step_id)
            
            logger.debug(f"循环回到步骤: {target_step_id} (第{self.workflow_state.loop_counters.get(f'loop_to_{target_step_id}', 0)}次)")
            return True
        else:
            logger.warning(f"找不到步骤ID: {target_step_id}")
            return False
    
    def handle_generate_fix_task_and_loop(self, decision: Dict[str, Any]) -> bool:
        """处理生成修复任务并循环的复合决策"""
        target_step_id = decision.get('loop_target')
        
        # 检查循环次数
        if self.workflow_state.should_break_loop(target_step_id):
            logger.warning(f"已尝试修复{self.workflow_state.max_loops}次，停止循环")
            return False
        
        # 1. 生成修复任务
        fix_task = {
            "id": f"fix_{self.workflow_state.fix_counter}",
            "name": "代码修复",
            "instruction": decision.get('fix_instruction', '修复代码中的问题'),
            "agent_name": decision.get('fix_agent', 'coder'),
            "instruction_type": "execution",
            "phase": "execution",
            "expected_output": "修复后的代码",
            "prerequisites": "检测到需要修复的问题",
            "status": "pending"
        }
        
        # 如果有错误详情，添加到指令中
        if decision.get('error_details'):
            fix_task['instruction'] += f"\n\n错误详情:\n{decision['error_details']}"
        
        # 2. 将修复任务插入到当前位置之后
        plan = self.get_plan()
        current_index = self.workflow_state.current_step_index
        plan.insert(current_index + 1, fix_task)
        self.device.set_variable("current_plan", plan)
        
        # 3. 更新状态
        self.workflow_state.fix_counter += 1
        
        logger.debug(f"生成修复任务: {fix_task['id']}")
        print(f"\n生成修复任务: {fix_task['name']}")
        print(f"修复指令: {fix_task['instruction'][:100]}...")
        
        return True

    #TODO: 是否区分执行性和信息性任务?
    def execute_single_step(self, step: Dict[str, Any], task_history=None, global_state: Optional['WorkflowState'] = None) -> Optional[Result]:
        """
        执行计划中的单个步骤。
        
        Args:
            step: 步骤定义
            task_history: 任务历史记录
            global_state: 全局工作流状态（可选）
            
        Returns:
            执行结果
        """
        
        agent_name = step.get("agent_name")
        instruction = step.get("instruction")
        instruction_type = step.get("instruction_type", "execution")  # 默认为execution类型
        if not agent_name or not instruction:
            return Result(False, instruction, "", "步骤缺少 agent_name 或 instruction")

        try:
            # 查找指定的智能体
            target_agent = None
            for spec in self.registered_agents:
                if spec.name == agent_name:
                    target_agent = spec.instance
                    break
            
            # 如果找不到指定的智能体，返回错误
            if target_agent is None:
                return Result(False, instruction, "", f"找不到名为 '{agent_name}' 的智能体")

            # 获取前序步骤的结果
            previous_results = []
            if task_history is None:
                task_history = []
            for task in task_history:
                if task.get('result') and getattr(task.get('result'), 'success', False):
                    task_name = task.get('task', {}).get('name', '')
                    return_value = getattr(task.get('result'), 'return_value', '')
                    previous_results.append(f"步骤 {task_name} 的结果:\n{return_value}")

            # 构建包含全局状态的增强指令
            prompt = self._generate_state_aware_instruction(
                step, instruction, previous_results, global_state or self.workflow_state
            )
            # 使用目标智能体执行任务
            if instruction_type == "information":
                response = target_agent.chat_stream(prompt)
            else:
                response = target_agent.execute_stream(prompt)
                
            # 处理响应流并收集结果
            response_text = ""
            for chunk in response:
                result=chunk
                if isinstance(chunk, str):
                    print(chunk,end="",flush=True)
                    response_text += chunk
                    
            # 根据指令类型解析结果
            if instruction_type == "information":
                result_obj = Result(True, instruction, response_text, "", response_text)
            else:
                if isinstance(result, Result):
                    result_obj = result
                elif hasattr(result, "return_value") and isinstance(result.return_value, Result):
                    result_obj = result.return_value
                else:
                    stdout = getattr(result, "stdout", str(result))
                    stderr = getattr(result, "stderr", None)
                    result_obj = Result(False, instruction, stdout, stderr, None)
            
            # 进行响应分析（如果启用）
            result_obj = self._analyze_step_response(result_obj, step, response_text)
            
            return result_obj
            
        except Exception as e:
            error_result = Result(False, instruction, "", str(e), None)
            # 分析错误响应
            error_result = self._analyze_step_response(error_result, step, str(e))
            return error_result

    #TODO: 整合到agent的execute方法
    @reduce_memory_decorator_compress
    def execute_multi_step(self, main_instruction: str, interactive: bool = False) -> str:
        """
        主入口：规划并执行多步骤任务 - 重构后的简化版本
        """
        # 初始化执行上下文
        context = self._initialize_execution_context(main_instruction)
        
        # 主执行循环
        while self._should_continue_execution(context):
            try:
                # 执行一个工作流迭代
                should_break = self._execute_workflow_iteration(context, interactive)
                if should_break:
                    break
            except Exception as e:
                logger.error(f"工作流迭代失败: {e}")
                self._handle_workflow_error(context, e)
                break
        
        return self._generate_execution_summary(context)
    
    def _initialize_execution_context(self, main_instruction: str) -> Dict[str, Any]:
        """初始化执行上下文"""
        # 存储原始目标
        self.original_goal = main_instruction
        
        # 重置工作流状态
        self.workflow_state = WorkflowState()
        
        # 规划步骤
        self.device.set_variable("previous_plan", None)
        plan = self.plan_execution(main_instruction)
        
        return {
            'main_instruction': main_instruction,
            'plan': plan,
            'task_history': [],
            'summary': "",
            'retries': 0,
            'workflow_iterations': 0,
            'context': {"original_goal": main_instruction},
            'max_workflow_iterations': 50
        }
    
    def _should_continue_execution(self, context: Dict[str, Any]) -> bool:
        """判断是否应该继续执行"""
        return (context['retries'] <= self.max_retries and 
                context['workflow_iterations'] < context['max_workflow_iterations'])
    
    def _execute_workflow_iteration(self, context: Dict[str, Any], interactive: bool) -> bool:
        """
        执行一个工作流迭代
        
        Returns:
            bool: 是否应该跳出主循环
        """
        context['workflow_iterations'] += 1
        
        context['plan'] = self.get_plan()
        
        # 选择下一个可执行步骤
        next_step_info = self.select_next_executable_step(context['plan'])
        
        if not next_step_info:
            # 没有可执行步骤，进行决策
            return self._handle_no_executable_steps(context)
        
        # 执行选定的步骤
        current_idx, current_step = next_step_info
        should_break = self._execute_single_workflow_step(current_idx, current_step, context)
        
        if should_break:
            return True
            
        # 交互模式处理
        if interactive and self._check_user_interrupt():
            context['summary'] += "\n用户请求退出。"
            return True
            
        return False
    
    def _handle_no_executable_steps(self, context: Dict[str, Any]) -> bool:
        """
        处理没有可执行步骤的情况
        
        Returns:
            bool: 是否应该跳出主循环
        """
        # 获取最后一个执行结果
        last_result = None
        if context['task_history']:
            last_result = context['task_history'][-1].get('result', None)
        
        # 进行决策
        decision = self.make_decision(
            current_result=last_result,
            task_history=context['task_history'],
            context=context['context']
        )
        
        print(f"\n决策结果: {decision['action']}")
        print(f"原因: {decision['reason']}")
        
        # 处理决策结果
        return self._process_no_steps_decision(decision, context)
    
    def _process_no_steps_decision(self, decision: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        处理没有可执行步骤时的决策结果
        
        Returns:
            bool: 是否应该跳出主循环
        """
        action = decision['action']
        
        if action == 'complete':
            context['summary'] += "\n全部步骤执行完成。"
            self._clear_failure_records()
            return True
            
        elif action == 'generate_new_task' and decision.get('new_tasks'):
            context['summary'] += "\n添加新任务并继续执行。"
            self._add_new_tasks(decision.get('new_tasks', []))
            context['plan'] = self.get_plan()
            return False
            
        else:
            context['summary'] += f"\n所有步骤已处理，决策为: {action}。"
            return True
    
    def _execute_single_workflow_step(self, current_idx: int, current_step: Dict, 
                                     context: Dict[str, Any]) -> bool:
        """
        执行单个工作流步骤
        
        Returns:
            bool: 是否应该跳出主循环
        """
        # 显示执行信息
        plan = context['plan']
        print(f"\n执行步骤 {current_idx+1}/{len(plan)}: {current_step.get('name')}")
        
        # 标记为运行中
        self.update_step_status(current_idx, "running")
        
        # 执行步骤
        exec_result = self.execute_single_step(current_step, context['task_history'], self.workflow_state)
        
        # 记录任务历史
        context['task_history'].append({
            'task': current_step,
            'result': exec_result,
            'timestamp': dt.now().isoformat()
        })
        
        # === AI状态更新器集成 ===
        # 在每个步骤执行后触发AI状态更新
        self._trigger_ai_state_update(current_step, exec_result, context)
        
        # 根据执行结果进行后续处理
        if exec_result and exec_result.success:
            return self._handle_step_success(current_idx, exec_result, context)
        else:
            return self._handle_step_failure(current_idx, current_step, exec_result, context)
    
    def _handle_step_success(self, current_idx: int, exec_result: Result, 
                           context: Dict[str, Any]) -> bool:
        """
        处理步骤执行成功的情况
        
        Returns:
            bool: 是否应该跳出主循环
        """
        self.update_step_status(current_idx, "completed", exec_result)
        
        # 执行成功后进行决策
        decision = self.make_decision(
            current_result=exec_result,
            task_history=context['task_history'],
            context=context['context']
        )
        
        print(f"\n决策结果: {decision['action']}")
        print(f"原因: {decision['reason']}")
        
        # 处理成功决策结果
        return self._process_success_decision(decision, context)
    
    def _handle_step_failure(self, current_idx: int, current_step: Dict, 
                           exec_result: Result, context: Dict[str, Any]) -> bool:
        """
        处理步骤执行失败的情况
        
        Returns:
            bool: 是否应该跳出主循环
        """
        # 更新步骤状态
        self.update_step_status(current_idx, "failed", exec_result)
        context['summary'] += f"\n步骤失败: {current_step.get('name')}"
        
        # 失败后进行决策
        decision = self.make_decision(
            current_result=exec_result,
            task_history=context['task_history'],
            context=context['context']
        )
        
        print(f"\n失败后决策: {decision['action']}")
        print(f"原因: {decision['reason']}")
        
        # 处理失败决策
        return self._process_failure_decision(decision, context, current_idx)
    
    def _process_success_decision(self, decision: Dict[str, Any], 
                                context: Dict[str, Any]) -> bool:
        """
        处理成功后的决策
        
        Returns:
            bool: 是否应该跳出主循环
        """
        action = decision['action']
        
        if action == 'complete':
            context['summary'] += "\n决策为完成执行。"
            self._clear_failure_records()
            return True
            
        elif action == 'continue':
            context['summary'] += "\n继续执行下一个步骤。"
            return False
            
        elif action == 'generate_new_task':
            return self._handle_generate_new_task_decision(decision, context)
            
        elif action in ['jump_to', 'loop_back']:
            return self._handle_navigation_decision(decision, context)
            
        elif action == 'generate_fix_task_and_loop':
            return self._handle_fix_task_decision(decision, context)
            
        elif action == 'skip_step':
            return self._handle_skip_step_decision(decision, context)
            
        return False
    
    def _process_failure_decision(self, decision: Dict[str, Any], context: Dict[str, Any], 
                                current_idx: int) -> bool:
        """
        处理失败后的决策
        
        Returns:
            bool: 是否应该跳出主循环
        """
        action = decision['action']
        
        if action == 'retry':
            self.update_step_status(current_idx, "pending")
            context['summary'] += "\n将重试当前步骤。"
            return False
            
        elif action == 'continue':
            context['summary'] += "\n继续执行下一个步骤。"
            return False
            
        elif action == 'generate_new_task':
            return self._handle_generate_new_task_decision(decision, context)
            
        elif action == 'skip_step':
            return self._handle_skip_step_decision(decision, context)
            
        else:
            # 默认处理：增加重试次数
            return self._handle_retry_logic(context)
    
    def _handle_generate_new_task_decision(self, decision: Dict[str, Any], 
                                         context: Dict[str, Any]) -> bool:
        """处理生成新任务的决策"""
        new_tasks = decision.get('new_tasks', [])
        if new_tasks:
            self._add_new_tasks(new_tasks)
            context['plan'] = self.get_plan()
            context['summary'] += "\n添加新任务并继续执行。"
        return False
    
    def _handle_navigation_decision(self, decision: Dict[str, Any], 
                                  context: Dict[str, Any]) -> bool:
        """处理跳转和循环决策"""
        action = decision['action']
        target_step_id = decision.get('target_step_id')
        
        if not target_step_id:
            logger.warning(f"{action}决策缺少target_step_id")
            return False
        
        if action == 'jump_to':
            if self.jump_to_step(target_step_id):
                context['summary'] += f"\n跳转到步骤: {target_step_id}"
            
        elif action == 'loop_back':
            if self.loop_back_to_step(target_step_id):
                context['summary'] += f"\n循环回到步骤: {target_step_id}"
            else:
                context['summary'] += "\n循环失败"
        
        return False
    
    def _handle_fix_task_decision(self, decision: Dict[str, Any], 
                                context: Dict[str, Any]) -> bool:
        """处理修复任务决策"""
        if self.handle_generate_fix_task_and_loop(decision):
            # 执行修复任务
            return self._execute_fix_task(decision, context)
        else:
            context['summary'] += "\n修复任务生成失败或达到最大重试次数"
            return True
    
    def _handle_skip_step_decision(self, decision: Dict[str, Any], 
                                 context: Dict[str, Any]) -> bool:
        """处理跳过步骤的决策"""
        target_step_id = decision.get('target_step_id')
        
        if not target_step_id:
            logger.warning("skip_step决策缺少target_step_id")
            return False
        
        # 查找目标步骤
        target_index = self.find_step_index_by_id(target_step_id)
        if target_index >= 0:
            plan = self.get_plan()
            
            # 将目标步骤标记为跳过
            if target_index < len(plan):
                plan[target_index]['status'] = 'skipped'
                self.device.set_variable("current_plan", plan)
                
                context['summary'] += f"\n跳过步骤: {target_step_id} - {decision.get('reason', '无原因')}"
                logger.debug(f"跳过步骤: {target_step_id}")
                print(f"\n跳过步骤: {plan[target_index].get('name', target_step_id)}")
                
                return False  # 继续执行工作流
            else:
                logger.warning(f"步骤索引越界: {target_index}")
                return False
        else:
            logger.warning(f"找不到要跳过的步骤ID: {target_step_id}")
            return False
    
    def _execute_fix_task(self, decision: Dict[str, Any], 
                         context: Dict[str, Any]) -> bool:
        """执行修复任务"""
        # 获取更新后的计划
        plan = self.get_plan()
        current_idx = self.workflow_state.current_step_index + 1
        
        if current_idx < len(plan):
            fix_task = plan[current_idx]
            print(f"\n执行修复任务: {fix_task.get('name')}")
            
            # 执行修复任务
            self.update_step_status(current_idx, "running")
            fix_result = self.execute_single_step(fix_task, context.get('task_history', []), self.workflow_state)
            
            # 记录修复任务历史
            context['task_history'].append({
                'task': fix_task,
                'result': fix_result,
                'timestamp': dt.now().isoformat()
            })
            
            # 更新修复任务状态
            if fix_result and fix_result.success:
                self.update_step_status(current_idx, "completed", fix_result)
                print(f"修复任务完成: {fix_task.get('name')}")
            else:
                self.update_step_status(current_idx, "failed", fix_result)
                print(f"修复任务失败: {fix_task.get('name')}")
        
        # 循环回到测试步骤
        loop_target = decision.get('loop_target')
        if loop_target and self.loop_back_to_step(loop_target):
            context['summary'] += f"\n生成修复任务并循环回到: {loop_target}"
        
        return False
    
    def _handle_retry_logic(self, context: Dict[str, Any]) -> bool:
        """
        处理重试逻辑
        
        Returns:
            bool: 是否应该跳出主循环
        """
        # 记录失败信息
        self._record_failure_information(context)
        
        # 增加重试计数
        context['retries'] += 1
        if context['retries'] <= self.max_retries:
            context['summary'] += f"\n第{context['retries']}次重试。"
            return False
        else:
            context['summary'] += "\n已达最大重试次数。"
            return True
    
    def _record_failure_information(self, context: Dict[str, Any]) -> None:
        """记录失败信息以供下次重试参考"""
        plan = context['plan']
        failures = [
            {
                "id": step.get("id"), 
                "name": step.get("name"), 
                "error": step.get("result", {}).get("stderr", "")
            }
            for step in plan if step.get("status") == "failed"
        ]
        
        failure_verification = f"执行失败的步骤: {json.dumps(failures, ensure_ascii=False, indent=2)}"
        
        try:
            self.device.set_variable("previous_attempt_failed", True)
            self.device.set_variable("previous_verification", failure_verification)
            self.device.set_variable("previous_plan", {"steps": plan})
        except Exception as e:
            logger.warning(f"设置失败记录时出错: {e}")
    
    def _check_user_interrupt(self) -> bool:
        """检查用户是否要求中断"""
        user_input = input("\n按Enter继续，输入'q'退出: ")
        return user_input.lower() == 'q'
    
    def _clear_failure_records(self) -> None:
        """清除失败记录"""
        try:
            self.device.set_variable("previous_attempt_failed", False)
            self.device.set_variable("previous_verification", None)
        except Exception as e:
            logger.warning(f"清除失败记录时出错: {e}")
    
    
    def _trigger_ai_state_update(self, step: Dict[str, Any], exec_result: Optional[Result], 
                                context: Dict[str, Any]) -> None:
        """
        触发AI状态更新器
        
        Args:
            step: 执行的步骤信息
            exec_result: 步骤执行结果
            context: 工作流执行上下文
        """
        try:
            # 检查是否启用状态更新
            if not self.workflow_state.is_state_update_enabled():
                logger.debug("AI状态更新已禁用，跳过状态更新")
                return
            
            # 构建状态更新上下文
            update_context = self._build_state_update_context(step, exec_result, context)
            
            # 调用WorkflowState的AI更新接口
            success = self.workflow_state.update_state_with_ai(update_context)
            
            if success:
                logger.info(f"AI状态更新成功 - 步骤: {step.get('name', 'unknown')}")
                # 可选：输出状态摘要到控制台
                if logger.isEnabledFor(logging.DEBUG):
                    state_summary = self.workflow_state.get_state_summary()
                    logger.debug(f"当前状态摘要: {state_summary}")
            else:
                logger.warning(f"AI状态更新失败 - 步骤: {step.get('name', 'unknown')}")
                
        except Exception as e:
            # 重要：状态更新失败不应影响工作流继续执行
            logger.error(f"AI状态更新过程异常 - 步骤: {step.get('name', 'unknown')}, 错误: {e}")
            # 可选：记录到执行上下文中
            context.setdefault('state_update_errors', []).append({
                'step': step.get('id', 'unknown'),
                'step_name': step.get('name', 'unknown'),
                'error': str(e),
                'timestamp': dt.now().isoformat()
            })
    
    def _generate_state_aware_instruction(self, step: Dict[str, Any], instruction: str, 
                                         previous_results: List[str], global_state: 'WorkflowState') -> str:
        """
        生成包含全局状态信息的状态感知指令，集成指令优化系统
        
        Args:
            step: 当前步骤信息
            instruction: 原始指令
            previous_results: 前序步骤结果
            global_state: 全局工作流状态
            
        Returns:
            增强和优化的状态感知指令
        """
        # 首先应用指令优化（如果启用）
        optimized_instruction = instruction
        optimization_result = None
        
        if self.optimization_enabled and hasattr(self, 'instruction_optimizer'):
            try:
                # 构建优化上下文
                optimization_context = {
                    'previous_results': previous_results,
                    'workflow_state': global_state,
                    'agent_instance': self
                }
                
                # 检查是否可以优化
                if self.instruction_optimizer.can_optimize(instruction, step, global_state, optimization_context):
                    optimization_result = self.instruction_optimizer.optimize_instruction(
                        instruction, step, global_state, optimization_context
                    )
                    
                    # 根据风险评估决定是否使用优化结果
                    risk_assessment = optimization_result.risk_assessment
                    if risk_assessment.get('recommendation') != 'avoid':
                        optimized_instruction = optimization_result.optimized_instruction
                        
                        logger.info(f"指令优化应用成功 - 置信度: {optimization_result.confidence_score:.2f}, "
                                  f"应用的优化: {', '.join(optimization_result.applied_enhancements)}")
                    else:
                        logger.warning(f"指令优化被跳过，风险评估建议避免: {risk_assessment.get('risk_factors', [])}")
                        
            except Exception as e:
                logger.error(f"指令优化过程出错: {e}")
                # 如果优化失败，使用原始指令继续
                optimized_instruction = instruction
        # 创建状态上下文提取器
        if not hasattr(self, '_state_extractor'):
            self._state_extractor = StateContextExtractor()
        
        # 提取相关状态上下文
        state_context = self._state_extractor.extract_relevant_context(step, global_state)
        
        # 构建基本指令信息
        enhanced_instruction = f"""# 状态感知任务执行

## 当前步骤信息
- 步骤ID: {step.get('id', 'unknown')}
- 步骤名称: {step.get('name', 'Unknown Step')}
- 执行者: {step.get('agent_name', 'unknown')}
- 指令类型: {step.get('instruction_type', 'execution')}"""
        
        # 添加预期输出（如果有）
        if step.get('expected_output'):
            enhanced_instruction += f"\n- 预期输出: {step.get('expected_output')}"
        
        # 添加任务指令（使用优化后的指令）
        enhanced_instruction += f"""

## 任务指令
{optimized_instruction}
"""
        
        # 如果使用了指令优化，添加优化信息
        if optimization_result and optimization_result.optimization_types:
            enhanced_instruction += f"""

## 🔧 指令优化信息
**应用的优化**: {', '.join(optimization_result.applied_enhancements)}
**优化理由**: {optimization_result.optimization_reasoning}
**置信度**: {optimization_result.confidence_score:.2f}
"""
        
        # 智能添加相关状态信息
        current_state = global_state.get_global_state()
        if current_state and current_state.strip():
            # 使用智能提取的上下文
            if state_context['state_summary']:
                enhanced_instruction += f"""
## 🎯 相关状态上下文
{state_context['state_summary']}
"""
            
            # 添加高相关性状态信息
            if state_context['high_relevance']:
                enhanced_instruction += f"""
## ⭐ 重点关注状态
以下状态信息与当前任务高度相关：
"""
                for item in state_context['high_relevance'][:5]:  # 最多显示5项
                    enhanced_instruction += f"• {item}\n"
            
            # 添加中等相关性状态信息（如果高相关性信息不足）
            if len(state_context['high_relevance']) < 3 and state_context['medium_relevance']:
                enhanced_instruction += f"""
## 📋 补充状态信息
"""
                for item in state_context['medium_relevance'][:3]:  # 最多显示3项
                    enhanced_instruction += f"• {item}\n"
            
            # 添加提取的实体信息
            if state_context['extracted_entities']:
                enhanced_instruction += f"""
## 🔍 提取的关键信息
"""
                for entity_type, entities in state_context['extracted_entities'].items():
                    if isinstance(entities, list) and entities:
                        enhanced_instruction += f"**{entity_type.replace('_', ' ').title()}**: {', '.join(str(e) for e in entities[:3])}\n"
                    elif isinstance(entities, dict) and entities:
                        pairs = [f"{k}={v}" for k, v in list(entities.items())[:3]]
                        enhanced_instruction += f"**{entity_type.replace('_', ' ').title()}**: {', '.join(pairs)}\n"
            
            # 如果没有相关信息，显示完整状态（保持向后兼容）
            if not any([state_context['high_relevance'], state_context['medium_relevance'], state_context['extracted_entities']]):
                enhanced_instruction += f"""
## 工作流当前状态
以下是工作流的当前整体状态：

{current_state[:800] + '...' if len(current_state) > 800 else current_state}
"""
        else:
            enhanced_instruction += f"""
## 工作流状态
工作流刚开始执行，这是早期步骤。当前没有记录的全局状态信息。
"""
        
        # 添加前序步骤结果（保持向后兼容）
        if previous_results:
            enhanced_instruction += f"""
## 前序步骤结果
{chr(10).join(previous_results[:3])}"""  # 限制显示数量
            if len(previous_results) > 3:
                enhanced_instruction += f"\n... (还有{len(previous_results)-3}个前序结果)"
        else:
            enhanced_instruction += f"""
## 前序步骤结果
无前序步骤结果
"""
        
        # 智能添加状态历史摘要
        history_count = global_state.get_state_history_count()
        if history_count > 0:
            recent_history = global_state.get_state_history(limit=2)  # 减少到2个，避免信息过载
            if recent_history:
                enhanced_instruction += f"""
## 📜 近期状态变化 ({history_count}次更新)
"""
                for i, entry in enumerate(reversed(recent_history)):  # 倒序显示，最新的在前
                    enhanced_instruction += f"**{i+1}. {entry.timestamp.strftime('%H:%M:%S')}** ({entry.source or 'AI'}): "
                    # 更严格的长度限制
                    snapshot = entry.state_snapshot[:200] + "..." if len(entry.state_snapshot) > 200 else entry.state_snapshot
                    enhanced_instruction += f"{snapshot}\n"
        
        # 添加基于步骤类型的定制化执行提示
        step_types = []
        if hasattr(self, '_state_extractor'):
            step_analysis = self._state_extractor._analyze_step_requirements(step)
            step_types = step_analysis.get('step_types', [])
        
        enhanced_instruction += f"""
## 💡 智能执行提示
- 🎯 **基于状态执行**: 特别关注上述标记的重点状态信息
- 🔄 **避免重复工作**: 检查已提取的关键信息，避免重复之前已完成的工作
- 🎨 **保持一致性**: 确保与提取的实体信息和配置保持一致"""
        
        # 根据步骤类型添加特定提示
        if 'file_operations' in step_types:
            enhanced_instruction += f"\n- 📁 **文件操作**: 注意已存在的文件路径和目录结构"
        if 'database' in step_types:
            enhanced_instruction += f"\n- 🗄️ **数据库操作**: 使用已配置的连接信息和参数"
        if 'api' in step_types:
            enhanced_instruction += f"\n- 🌐 **API操作**: 参考已有的端点和服务配置"
        if 'error_handling' in step_types:
            enhanced_instruction += f"\n- 🚨 **错误处理**: 基于上述错误信息进行针对性修复"
        if 'configuration' in step_types:
            enhanced_instruction += f"\n- ⚙️ **配置任务**: 保持与现有配置的兼容性"
        
        enhanced_instruction += f"""
- 📝 **质量保证**: 如果是代码相关任务，请确保代码的正确性和完整性
- 🔗 **引用信息**: 优先使用上述提取的关键信息和实体数据
- 💡 **状态更新**: 执行完成后，系统会自动更新全局状态
"""
        
        return enhanced_instruction
    
    def _build_state_update_context(self, step: Dict[str, Any], exec_result: Optional[Result], 
                                   workflow_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建AI状态更新器所需的上下文信息
        
        Args:
            step: 执行的步骤信息
            exec_result: 步骤执行结果
            workflow_context: 工作流执行上下文
            
        Returns:
            状态更新上下文字典
        """
        # 基础步骤信息
        step_info = {
            'step_id': step.get('id', 'unknown'),
            'step_name': step.get('name', 'unknown'),
            'step_type': step.get('type', 'unknown'),
            'step_description': step.get('description', ''),
            'step_expected_output': step.get('expected_output', ''),
        }
        
        # 执行结果信息
        result_info = {}
        if exec_result:
            result_info = {
                'success': getattr(exec_result, 'success', False),
                'stdout': getattr(exec_result, 'stdout', ''),
                'stderr': getattr(exec_result, 'stderr', ''),
                'return_value': getattr(exec_result, 'return_value', None),
                'execution_time': getattr(exec_result, 'execution_time', None),
            }
        
        # 工作流执行统计
        plan = workflow_context.get('plan', [])
        completed_steps = [s for s in plan if s.get('status') == 'completed']
        failed_steps = [s for s in plan if s.get('status') == 'failed']
        
        workflow_stats = {
            'total_steps': len(plan),
            'completed_steps': len(completed_steps),
            'failed_steps': len(failed_steps),
            'current_iteration': workflow_context.get('workflow_iterations', 0),
            'max_iterations': workflow_context.get('max_workflow_iterations', 50),
        }
        
        # 历史任务信息（最近的几个任务）
        task_history = workflow_context.get('task_history', [])
        recent_history = []
        if task_history:
            # 获取最近5个任务的简化信息
            for task_item in task_history[-5:]:
                if isinstance(task_item, dict):
                    task = task_item.get('task', {})
                    result = task_item.get('result', {})
                    recent_history.append({
                        'name': task.get('name', 'unknown'),
                        'success': getattr(result, 'success', False),
                        'timestamp': task_item.get('timestamp', '')
                    })
        
        # 错误信息（如果有）
        error_info = {}
        if hasattr(exec_result, 'stderr') and exec_result.stderr:
            error_info['error_message'] = exec_result.stderr
        if 'state_update_errors' in workflow_context:
            error_info['previous_update_errors'] = workflow_context['state_update_errors']
        
        # 组合完整上下文
        update_context = {
            'step_info': step_info,
            'execution_result': result_info,
            'workflow_stats': workflow_stats,
            'recent_history': recent_history,
            'error_info': error_info,
            'timestamp': dt.now().isoformat(),
            'original_goal': getattr(self, 'original_goal', ''),
            'workflow_summary': workflow_context.get('summary', ''),
        }
        
        return update_context
    
    def _handle_workflow_error(self, context: Dict[str, Any], error: Exception) -> None:
        """处理工作流执行错误，使用状态感知的错误处理机制"""
        try:
            # 更新错误统计
            self.error_statistics['total_errors'] += 1
            
            # 获取当前执行的步骤
            current_step = context.get('current_step', {})
            if not current_step:
                # 如果没有当前步骤，使用默认步骤信息
                current_step = {
                    'id': 'unknown',
                    'name': 'unknown_step',
                    'instruction': 'Unknown step',
                    'agent_name': 'unknown'
                }
            
            # 构建执行上下文
            execution_context = {
                'plan': context.get('plan', []),
                'completed_steps': context.get('completed_steps', 0),
                'failed_steps': context.get('failed_steps', 0),
                'summary': context.get('summary', ''),
                'start_time': context.get('start_time'),
                'retry_count': context.get('retry_count', 0),
                'workflow_state': self.workflow_state
            }
            
            # 使用错误分发器处理错误
            error_result = self.error_dispatcher.dispatch_error(
                error=error,
                step=current_step,
                global_state=self.workflow_state,
                execution_context=execution_context
            )
            
            # 处理错误处理结果
            if error_result.get('handled', False):
                self.error_statistics['handled_errors'] += 1
                
                # 应用恢复动作
                recovery_action = error_result.get('recovery_action')
                if recovery_action:
                    self._apply_recovery_action(recovery_action, context)
                
                # 添加处理结果到摘要
                context['summary'] += f"\n错误已处理: {error_result.get('message', '未知错误')}"
                
                # 日志记录
                logger.info(f"错误已成功处理: {error_result.get('message')}")
                
            else:
                self.error_statistics['unhandled_errors'] += 1
                context['summary'] += f"\n工作流执行出错: {str(error)}"
                logger.error(f"工作流执行出错（未处理）: {error}")
            
            # 更新错误类型统计
            error_type = error_result.get('error_type', 'unknown')
            self.error_statistics['error_types'][error_type] = \
                self.error_statistics['error_types'].get(error_type, 0) + 1
            
            # 计算恢复成功率
            if self.error_statistics['total_errors'] > 0:
                self.error_statistics['recovery_success_rate'] = \
                    self.error_statistics['handled_errors'] / self.error_statistics['total_errors']
            
        except Exception as handler_error:
            # 错误处理器本身出错的情况
            self.error_statistics['unhandled_errors'] += 1
            context['summary'] += f"\n错误处理失败: {str(handler_error)}"
            logger.error(f"错误处理器失败: {handler_error}")
            logger.error(f"原始错误: {error}")
    
    def _apply_recovery_action(self, action: str, context: Dict[str, Any]) -> None:
        """应用恢复动作"""
        try:
            if action == "retry_step":
                # 重试当前步骤
                context['should_retry'] = True
                logger.info("已标记重试当前步骤")
                
            elif action == "skip_step":
                # 跳过当前步骤
                context['should_skip'] = True
                logger.info("已标记跳过当前步骤")
                
            elif action == "pause_workflow":
                # 暂停工作流
                context['should_pause'] = True
                logger.info("已标记暂停工作流")
                
            elif action == "continue_workflow":
                # 继续工作流
                context['should_continue'] = True
                logger.info("已标记继续工作流")
                
            elif action.startswith("delay_"):
                # 延迟执行
                delay_seconds = int(action.split("_")[1])
                context['delay_seconds'] = delay_seconds
                logger.info(f"已设置延迟 {delay_seconds} 秒")
                
            elif action == "generate_fix_task":
                # 生成修复任务
                context['generate_fix_task'] = True
                logger.info("已标记生成修复任务")
                
            else:
                logger.warning(f"未知的恢复动作: {action}")
                
        except Exception as e:
            logger.error(f"应用恢复动作失败 [{action}]: {e}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误处理统计信息"""
        return self.error_statistics.copy()
    
    def reset_error_statistics(self) -> None:
        """重置错误处理统计信息"""
        self.error_statistics = {
            'total_errors': 0,
            'handled_errors': 0,
            'unhandled_errors': 0,
            'error_types': {},
            'recovery_success_rate': 0.0
        }
        logger.info("错误处理统计信息已重置")
    
    def enable_instruction_optimization(self) -> None:
        """启用指令优化"""
        self.optimization_enabled = True
        logger.info("指令优化系统已启用")
    
    def disable_instruction_optimization(self) -> None:
        """禁用指令优化"""
        self.optimization_enabled = False
        logger.info("指令优化系统已禁用")
    
    def set_optimization_strategy(self, strategy: OptimizationStrategy) -> None:
        """设置优化策略"""
        if hasattr(self, 'instruction_optimizer'):
            self.instruction_optimizer.strategy = strategy
            logger.info(f"指令优化策略已设置为: {strategy.value}")
        else:
            logger.warning("指令优化器未初始化")
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """获取指令优化统计信息"""
        if hasattr(self, 'instruction_optimizer'):
            stats = self.instruction_optimizer.get_optimization_statistics()
            stats['optimization_enabled'] = self.optimization_enabled
            stats['strategy'] = self.instruction_optimizer.strategy.value
            return stats
        else:
            return {
                'optimization_enabled': False,
                'message': '指令优化器未初始化'
            }
    
    def reset_optimization_statistics(self) -> None:
        """重置指令优化统计"""
        if hasattr(self, 'instruction_optimizer'):
            self.instruction_optimizer.reset_optimization_statistics()
            logger.info("指令优化统计信息已重置")
        else:
            logger.warning("指令优化器未初始化")
    
    def create_decision_node(self, node_id: str, node_type: DecisionNodeType, 
                           description: str = "") -> DecisionNode:
        """创建决策节点"""
        node = DecisionNode(node_id, node_type, description)
        self.decision_manager.register_decision_node(node)
        return node
    
    def add_conditional_decision(self, node_id: str, condition: StateCondition, 
                               true_step: str, false_step: str, description: str = "") -> DecisionNode:
        """添加条件决策节点的快捷方法"""
        return self.decision_manager.create_conditional_node(node_id, condition, true_step, false_step, description)
    
    def add_validation_decision(self, node_id: str, condition: StateCondition,
                              valid_step: str, invalid_step: str, description: str = "") -> DecisionNode:
        """添加验证决策节点的快捷方法"""
        return self.decision_manager.create_validation_node(node_id, condition, valid_step, invalid_step, description)
    
    def evaluate_workflow_decision(self, node_id: str) -> DecisionResult:
        """评估工作流决策节点"""
        return self.decision_manager.evaluate_decision(node_id, self.workflow_state)
    
    def list_decision_nodes(self) -> List[Dict[str, Any]]:
        """列出所有决策节点"""
        return self.decision_manager.list_decision_nodes()
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """获取决策统计信息"""
        return self.decision_manager.get_decision_statistics()
    
    def reset_decision_statistics(self) -> None:
        """重置决策统计信息"""
        self.decision_manager.reset_decision_statistics()
        logger.info("决策统计信息已重置")
    
    def _generate_execution_summary(self, context: Dict[str, Any]) -> str:
        """生成最终执行摘要（增强版，包含响应分析）"""
        all_steps = context['plan']
        completed_steps = [s for s in all_steps if s.get("status") == "completed"]
        failed_steps = [s for s in all_steps if s.get("status") == "failed"]
        pending_steps = [s for s in all_steps if s.get("status") not in ("completed", "failed", "skipped")]
        
        # 基础摘要
        summary = f"""
## 执行摘要
- 总步骤数: {len(all_steps)}
- 已完成: {len(completed_steps)}
- 失败: {len(failed_steps)}
- 未执行: {len(pending_steps)}

{context['summary']}
"""
        
        # 添加响应分析摘要
        if self.enable_response_analysis and self.response_parser and self.parsed_responses_history:
            analysis_summary = self._generate_response_analysis_summary()
            summary += f"\n## 🤖 智能分析摘要\n{analysis_summary}"
        
        return summary
    

    def make_decision(self, current_result, task_history=None, context=None):
        """
        分析当前执行结果并决定下一步操作（支持状态感知决策）
        
        Args:
            current_result: 当前执行结果（Result对象或其他结果）
            task_history: 任务执行历史记录（可选）
            context: 额外的上下文信息（可选）
            
        Returns:
            决策结果字典，包含action、reason和new_tasks
        """
        try:
            # 首先尝试使用状态感知决策系统
            state_decision = self._try_state_aware_decision(current_result, task_history, context)
            if state_decision:
                logger.info(f"使用状态感知决策: {state_decision['action']}")
                return state_decision
            
            # 回退到传统的LLM决策
            logger.debug("回退到传统LLM决策机制")
            return self._make_traditional_decision(current_result, task_history, context)
            
        except Exception as e:
            logger.error(f"决策过程异常: {e}")
            return self._get_fallback_decision(str(e))
    
    def _try_state_aware_decision(self, current_result, task_history=None, context=None) -> Optional[Dict[str, Any]]:
        """
        尝试使用状态感知决策系统
        
        Returns:
            决策结果字典或None（如果无法使用状态感知决策）
        """
        try:
            # 获取下一个可执行步骤以确定决策场景
            plan = self.get_plan()
            next_step_info = self.select_next_executable_step(plan)
            
            if next_step_info:
                current_idx, current_step = next_step_info
                step_id = current_step.get('id', f'step_{current_idx}')
                
                # 检查是否有针对该步骤的决策节点
                decision_node_id = f"decision_{step_id}"
                decision_nodes = self.decision_manager.list_decision_nodes()
                
                # 如果存在相关的决策节点，使用状态感知决策
                for node_info in decision_nodes:
                    if node_info['node_id'] == decision_node_id:
                        decision_result = self.decision_manager.evaluate_decision(
                            decision_node_id, self.workflow_state
                        )
                        
                        if decision_result.decision_made:
                            return self._convert_decision_result(decision_result, current_step)
                
                # 动态创建决策节点（基于步骤类型和当前状态）
                dynamic_decision = self._create_dynamic_decision(current_step, current_result, context)
                if dynamic_decision:
                    return dynamic_decision
            
            # 检查工作流级别的决策
            workflow_decision = self._evaluate_workflow_level_decisions(current_result, task_history, context)
            if workflow_decision:
                return workflow_decision
                
            return None
            
        except Exception as e:
            logger.warning(f"状态感知决策尝试失败: {e}")
            return None
    
    def _create_dynamic_decision(self, current_step: Dict[str, Any], current_result, context=None) -> Optional[Dict[str, Any]]:
        """
        基于步骤类型和全局状态动态创建决策
        
        Args:
            current_step: 当前步骤信息
            current_result: 执行结果
            context: 上下文信息
            
        Returns:
            决策结果或None
        """
        try:
            step_name = current_step.get('name', '').lower()
            step_instruction = current_step.get('instruction', '').lower()
            global_state_content = self.workflow_state.get_global_state().lower()
            
            # 检测测试步骤的成功/失败分支
            if any(keyword in step_name or keyword in step_instruction 
                   for keyword in ['test', '测试', 'verify', '验证', 'check', '检查']):
                return self._create_test_decision(current_step, current_result)
            
            # 检测数据验证步骤
            if any(keyword in step_name or keyword in step_instruction 
                   for keyword in ['validate', '验证', 'confirm', '确认']):
                return self._create_validation_decision(current_step, current_result)
            
            # 检测审批或人工确认步骤
            if any(keyword in step_name or keyword in step_instruction 
                   for keyword in ['approve', '审批', 'review', '审查', 'confirm', '确认']):
                return self._create_approval_decision(current_step, current_result)
            
            # 基于全局状态的条件决策
            if any(keyword in global_state_content 
                   for keyword in ['错误', 'error', '失败', 'fail', '异常', 'exception']):
                return self._create_error_recovery_decision(current_step, current_result)
            
            return None
            
        except Exception as e:
            logger.error(f"动态决策创建失败: {e}")
            return None
    
    def _create_test_decision(self, current_step: Dict[str, Any], current_result) -> Dict[str, Any]:
        """创建测试步骤的决策"""
        # 判断测试是否成功
        test_success = False
        if isinstance(current_result, Result):
            test_success = current_result.success
            # 进一步检查输出内容
            if current_result.stdout:
                output_lower = current_result.stdout.lower()
                if any(keyword in output_lower for keyword in ['pass', 'passed', '通过', '成功']):
                    test_success = True
                elif any(keyword in output_lower for keyword in ['fail', 'failed', 'error', '失败', '错误']):
                    test_success = False
        
        if test_success:
            return {
                'action': 'complete',
                'reason': '测试通过，工作流执行成功完成',
                'new_tasks': [],
                'decision_source': 'state_aware_test'
            }
        else:
            return {
                'action': 'generate_fix_task_and_loop',
                'reason': '测试失败，需要生成修复任务并重新测试',
                'new_tasks': [],
                'loop_target': current_step.get('id'),
                'fix_instruction': '分析测试失败原因并修复代码',
                'fix_agent': 'coder',
                'decision_source': 'state_aware_test'
            }
    
    def _create_validation_decision(self, current_step: Dict[str, Any], current_result) -> Dict[str, Any]:
        """创建验证步骤的决策"""
        # 简单的验证逻辑：检查执行结果
        validation_success = isinstance(current_result, Result) and current_result.success
        
        if validation_success:
            return {
                'action': 'continue',
                'reason': '验证成功，继续执行下一步',
                'new_tasks': [],
                'decision_source': 'state_aware_validation'
            }
        else:
            return {
                'action': 'retry',
                'reason': '验证失败，重试当前步骤',
                'new_tasks': [],
                'decision_source': 'state_aware_validation'
            }
    
    def _create_approval_decision(self, current_step: Dict[str, Any], current_result) -> Dict[str, Any]:
        """创建审批步骤的决策"""
        # 基于执行结果判断审批状态
        approval_granted = isinstance(current_result, Result) and current_result.success
        
        if approval_granted:
            return {
                'action': 'continue',
                'reason': '审批通过，继续执行',
                'new_tasks': [],
                'decision_source': 'state_aware_approval'
            }
        else:
            return {
                'action': 'complete',
                'reason': '审批未通过，终止工作流',
                'new_tasks': [],
                'decision_source': 'state_aware_approval'
            }
    
    def _create_error_recovery_decision(self, current_step: Dict[str, Any], current_result) -> Dict[str, Any]:
        """创建错误恢复决策"""
        return {
            'action': 'generate_new_task',
            'reason': '检测到错误状态，生成错误恢复任务',
            'new_tasks': [{
                'id': f'error_recovery_{len(self.get_plan()) + 1}',
                'name': '错误恢复处理',
                'instruction': '分析和处理当前工作流中的错误状态',
                'agent_name': 'coder',
                'instruction_type': 'execution',
                'phase': 'verification',
                'expected_output': '错误修复结果',
                'prerequisites': '无'
            }],
            'decision_source': 'state_aware_error_recovery'
        }
    
    def _evaluate_workflow_level_decisions(self, current_result, task_history=None, context=None) -> Optional[Dict[str, Any]]:
        """
        评估工作流级别的决策（如完成条件、循环控制等）
        
        Returns:
            工作流级别的决策结果或None
        """
        try:
            # 检查是否达到完成条件
            completion_decision = self._check_completion_conditions()
            if completion_decision:
                return completion_decision
            
            # 检查循环控制
            loop_decision = self._check_loop_conditions(current_result, task_history)
            if loop_decision:
                return loop_decision
            
            return None
            
        except Exception as e:
            logger.error(f"工作流级别决策评估失败: {e}")
            return None
    
    def _check_completion_conditions(self) -> Optional[Dict[str, Any]]:
        """检查工作流完成条件"""
        try:
            plan = self.get_plan()
            global_state = self.workflow_state.get_global_state().lower()
            
            # 检查是否所有核心步骤都已完成
            completed_steps = [step for step in plan if step.get('status') == 'completed']
            total_steps = len(plan)
            completion_rate = len(completed_steps) / total_steps if total_steps > 0 else 0
            
            # 如果完成率很高且全局状态显示成功
            if completion_rate >= 0.8 and any(keyword in global_state 
                                            for keyword in ['成功', 'success', 'complete', '完成', 'pass', '通过']):
                return {
                    'action': 'complete',
                    'reason': f'工作流完成率{completion_rate:.1%}，全局状态显示成功',
                    'new_tasks': [],
                    'decision_source': 'state_aware_completion'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"完成条件检查失败: {e}")
            return None
    
    def _check_loop_conditions(self, current_result, task_history=None) -> Optional[Dict[str, Any]]:
        """检查循环控制条件"""
        try:
            # 检查是否达到最大循环次数
            for loop_key, count in self.workflow_state.loop_counters.items():
                if count >= self.workflow_state.max_loops:
                    return {
                        'action': 'complete',
                        'reason': f'达到最大循环次数限制({self.workflow_state.max_loops})，终止执行',
                        'new_tasks': [],
                        'decision_source': 'state_aware_loop_limit'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"循环条件检查失败: {e}")
            return None
    
    def _convert_decision_result(self, decision_result: DecisionResult, current_step: Dict[str, Any]) -> Dict[str, Any]:
        """
        将StateAwareDecisionManager的DecisionResult转换为标准决策格式
        
        Args:
            decision_result: StateAwareDecisionManager的决策结果
            current_step: 当前步骤信息
            
        Returns:
            标准格式的决策字典
        """
        try:
            # 基础决策信息
            decision = {
                'reason': decision_result.decision_reason,
                'new_tasks': [],
                'decision_source': 'state_aware_manager',
                'confidence': decision_result.confidence,
                'state_variables_used': decision_result.state_variables_used
            }
            
            # 根据next_step_id确定action
            if decision_result.next_step_id:
                if decision_result.next_step_id == current_step.get('id'):
                    decision['action'] = 'retry'
                else:
                    decision['action'] = 'jump_to'
                    decision['target_step_id'] = decision_result.next_step_id
            else:
                decision['action'] = 'complete'
            
            # 添加额外的建议行动
            if decision_result.additional_actions:
                decision['additional_actions'] = decision_result.additional_actions
            
            return decision
            
        except Exception as e:
            logger.error(f"决策结果转换失败: {e}")
            return self._get_fallback_decision("决策结果转换失败")
    
    def _make_traditional_decision(self, current_result, task_history=None, context=None) -> Dict[str, Any]:
        """
        传统的基于LLM的决策方法
        
        Returns:
            决策结果字典
        """
        # 生成决策提示
        decision_prompt = self._generate_decision_prompt(current_result, task_history, context)
        
        # 调用LLM进行决策
        try:
            result = self.chat_sync(decision_prompt)
            if result.success:
                decision_text = result.return_value if result.return_value else result.stdout
                decision = self._parse_decision(decision_text)
                decision['decision_source'] = 'traditional_llm'
                return decision
            else:
                logger.warning(f"LLM决策失败: {result.stderr}")
                return self._get_fallback_decision("LLM决策过程出错")
        except Exception as e:
            logger.error(f"传统决策过程异常: {e}")
            return self._get_fallback_decision(f"传统决策过程异常: {e}")
    
    def _get_fallback_decision(self, reason: str) -> Dict[str, Any]:
        """
        获取回退决策
        
        Args:
            reason: 需要回退的原因
            
        Returns:
            回退决策结果
        """
        return {
            'action': 'continue',
            'reason': f'决策系统异常({reason})，默认继续执行',
            'new_tasks': [],
            'decision_source': 'fallback'
        }

    def _generate_decision_prompt(self, current_result, task_history=None, context=None):
        """
        生成用于决策的提示 (方案2: 支持循环和条件分支控制)
        
        Args:
            current_result: 当前执行结果
            task_history: 任务执行历史
            context: 额外的上下文信息
            
        Returns:
            决策提示字符串
        """
        # 获取当前计划和状态
        plan = self.get_plan()
        # 不再使用固定的current_step_index，而是基于任务历史确定当前状态
        
        # 获取可用智能体列表
        available_agents = "\n".join([
            f"- {spec.name}: {spec.description}" for spec in self.registered_agents
        ]) if self.registered_agents else "无可用智能体"
        
        # 格式化当前结果
        if isinstance(current_result, Result):
            result_str = f"成功: {current_result.success}\n"
            if current_result.stdout:
                result_str += f"输出: {current_result.stdout[:500]}{'...' if len(current_result.stdout) > 500 else ''}\n"
            if current_result.stderr:
                result_str += f"错误: {current_result.stderr}\n"
            if current_result.return_value:
                result_str += f"返回值: {current_result.return_value}\n"
        else:
            result_str = str(current_result)
        
        # 格式化任务历史（如果有）
        history_str = ""
        if task_history:
            try:
                history_items = []
                for item in task_history:
                    if isinstance(item, dict):
                        task = item.get('task', {})
                        task_id = task.get('id', 'unknown')
                        task_name = task.get('name', 'unnamed')
                        task_result = item.get('result', {})
                        task_success = getattr(task_result, 'success', False)
                        history_items.append(f"任务 {task_id} ({task_name}): {'成功' if task_success else '失败'}")
                history_str = "\n".join(history_items)
            except Exception as e:
                history_str = f"无法格式化任务历史: {e}"
        
        # 检查剩余任务
        completed_steps = [step for step in plan if step.get('status') == 'completed']
        pending_steps = [step for step in plan if step.get('status') not in ['completed', 'skipped']]
        remaining_steps_str = "\n".join([
            f"- {step.get('id')}: {step.get('name')}" for step in pending_steps
        ]) if pending_steps else "无剩余步骤"
        
        # 工作流状态信息  
        last_executed_step = None
        if task_history:
            last_executed_step = task_history[-1].get('task', {}).get('name', '无')
        
        workflow_state_str = f"""
最后执行步骤: {last_executed_step or '无'}
循环计数器: {self.workflow_state.loop_counters}
修复任务计数: {self.workflow_state.fix_counter}
"""
        
        # 格式化额外上下文（如果有）
        context_str = ""
        if context:
            if isinstance(context, dict):
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            else:
                context_str = str(context)
        
        # 生成决策提示
        prompt = f"""
# 执行决策分析 (方案2: 动态控制流)

## 当前执行状态
已完成步骤数: {len(completed_steps)}
剩余步骤数: {len(pending_steps)}

## 工作流状态
{workflow_state_str}

## 当前结果
{result_str}

## 任务历史
{history_str}

## 可用智能体
{available_agents}

## 剩余步骤
{remaining_steps_str}

## 原始目标
{getattr(self, 'original_goal', '未设置')}

## 额外上下文
{context_str}

## 决策任务
请分析当前执行状态和结果，决定下一步操作。可选的操作有：

### 基本决策类型：
1. **continue**: 继续执行下一个计划步骤
2. **complete**: 完成整个工作流（目标已达成）
3. **retry**: 重试当前步骤
4. **generate_new_task**: 生成新的任务

### 控制流决策类型（方案2新增）：
5. **jump_to**: 跳转到指定步骤ID
6. **loop_back**: 循环回到指定步骤ID
7. **generate_fix_task_and_loop**: 生成修复任务并循环回到测试步骤

## 决策策略

### 测试结果分析（针对测试步骤）
如果当前步骤是测试步骤，请根据测试结果决策：
- **测试成功**: 选择 `complete`
- **测试失败**: 选择 `generate_fix_task_and_loop`，生成修复任务并循环回到测试步骤

### 循环控制策略
- 检查循环次数是否超过限制（当前限制: {self.workflow_state.max_loops}次）
- 如果超过限制，选择 `complete` 并说明原因
- 如果需要修复错误，使用 `generate_fix_task_and_loop`

### 其他策略
- 信息不足: 生成信息收集任务
- 错误处理: 生成诊断和修复任务
- 替代方案: 尝试其他方法

## 输出格式
请以JSON格式返回你的决策：

```json
{{
  "action": "continue|complete|retry|generate_new_task|jump_to|loop_back|generate_fix_task_and_loop",
  "reason": "详细说明你的决策理由",
  "target_step_id": "目标步骤ID（仅用于jump_to和loop_back）",
  "loop_target": "循环目标步骤ID（仅用于generate_fix_task_and_loop）",
  "fix_instruction": "修复指令（仅用于generate_fix_task_and_loop）",
  "fix_agent": "修复智能体（仅用于generate_fix_task_and_loop）",
  "error_details": "错误详情（仅用于generate_fix_task_and_loop）",
  "new_tasks": [
    {{
      "id": "task_id",
      "name": "任务名称",
      "instruction": "详细指令",
      "agent_name": "执行智能体名称",
      "phase": "information|execution|verification",
      "prerequisites": "先决条件描述"
    }}
  ]
}}
```

重要提示：
1. 如果剩余步骤不为空且未达到目标，不要选择complete
2. 如果选择generate_new_task，必须提供完整的new_tasks数组
3. 如果选择控制流操作，必须提供相应的目标步骤ID
4. 新任务的agent_name必须从可用智能体列表中选择
5. 优先使用专门的控制流决策类型来处理循环和条件分支
"""
        return prompt
    
    def _parse_decision(self, decision_text):
        """
        解析决策文本为结构化决策
        
        Args:
            decision_text: 决策文本（可能包含JSON）
            
        Returns:
            解析后的决策字典
        """
        try:
            # 尝试提取JSON部分
            try:
                from autogen.code_utils import extract_code
                
                # 先尝试提取代码块
                extracted_json = extract_code(decision_text)
                if extracted_json:
                    # 找到了代码块
                    for lang, code in extracted_json:
                        if lang == "" or lang.lower() == "json":
                            try:
                                return json.loads(code)
                            except:
                                continue
            except ImportError:
                # autogen不可用，跳过这个方法
                pass
            
            # 如果没有提取到代码块或解析失败，尝试直接解析
            try:
                return json.loads(decision_text)
            except:
                # 尝试查找JSON格式部分
                import re
                json_pattern = r'\{{[\s\S]*\}}'
                match = re.search(json_pattern, decision_text)
                if match:
                    try:
                        return json.loads(match.group(0))
                    except:
                        pass
            
            # 所有JSON解析方法都失败，使用简单的文本分析
            decision = {}
            if 'generate_new_task' in decision_text.lower():
                decision['action'] = 'generate_new_task'
            elif 'retry' in decision_text.lower():
                decision['action'] = 'retry'
            elif 'complete' in decision_text.lower():
                decision['action'] = 'complete'
            else:
                decision['action'] = 'continue'
            
            decision['reason'] = "基于文本分析的决策（JSON解析失败）"
            decision['new_tasks'] = []
            
            return decision
            
        except Exception as e:
            logger.error(f"决策解析失败: {e}")
            # 返回默认决策
            return {
                'action': 'continue',
                'reason': f'决策解析失败: {e}',
                'new_tasks': []
            }

    # ===== 多方案响应解析器相关方法 =====
    
    def _analyze_step_response(self, result: Result, step: Dict[str, Any], response_text: str) -> Result:
        """
        分析步骤响应并增强结果
        
        Args:
            result: 原始执行结果
            step: 步骤信息
            response_text: 响应文本
            
        Returns:
            增强后的结果对象
        """
        if not self.enable_response_analysis or not self.response_parser:
            return result
        
        try:
            # 准备上下文信息
            context = {
                'step_name': step.get('name', ''),
                'step_type': step.get('instruction_type', ''),
                'agent_name': step.get('agent_name', ''),
                'instruction': step.get('instruction', ''),
                'execution_success': result.success
            }
            
            # 解析响应
            parsed_info = self.response_parser.parse_response(response_text, context)
            
            # 记录解析历史
            self.parsed_responses_history.append({
                'timestamp': dt.now().isoformat(),
                'step_name': step.get('name', ''),
                'instruction': step.get('instruction', ''),
                'response_text': response_text,
                'parsed_info': parsed_info,
                'original_success': result.success
            })
            
            # 增强结果对象
            if hasattr(result, 'details') and isinstance(result.details, dict):
                result.details['response_analysis'] = {
                    'main_content': parsed_info.main_content,
                    'confidence_score': parsed_info.confidence_score,
                    'extracted_entities': parsed_info.extracted_entities,
                    'sentiment': parsed_info.sentiment,
                    'intent': parsed_info.intent,
                    'quality_metrics': parsed_info.quality_metrics
                }
            else:
                # 如果 result.details 不存在或不是字典，创建新的
                result.details = {
                    'response_analysis': {
                        'main_content': parsed_info.main_content,
                        'confidence_score': parsed_info.confidence_score,
                        'extracted_entities': parsed_info.extracted_entities,
                        'sentiment': parsed_info.sentiment,
                        'intent': parsed_info.intent,
                        'quality_metrics': parsed_info.quality_metrics
                    }
                }
            
            # 检查置信度并记录警告
            if parsed_info.confidence_score < self.confidence_threshold:
                logger.warning(f"步骤 '{step.get('name', '')}' 响应置信度较低: {parsed_info.confidence_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"响应分析失败: {e}")
            return result
    
    def _generate_response_analysis_summary(self) -> str:
        """生成响应分析摘要"""
        if not self.parsed_responses_history:
            return "暂无响应分析数据"
        
        # 计算统计信息
        total_responses = len(self.parsed_responses_history)
        confidence_scores = [entry['parsed_info'].confidence_score for entry in self.parsed_responses_history]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        # 统计状态类型
        status_types = [entry['parsed_info'].extracted_entities.get('status_type', 'unknown') 
                       for entry in self.parsed_responses_history]
        status_counts = {}
        for status in status_types:
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # 统计情感倾向
        sentiments = [entry['parsed_info'].sentiment for entry in self.parsed_responses_history 
                     if entry['parsed_info'].sentiment]
        sentiment_counts = {}
        for sentiment in sentiments:
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # 获取解析器统计
        parser_stats = self.response_parser.get_stats() if self.response_parser else {}
        
        # 生成摘要
        summary = f"📊 **响应分析统计**\n"
        summary += f"- 总响应数: {total_responses}\n"
        summary += f"- 平均置信度: {avg_confidence:.1%}\n"
        summary += f"- 解析成功率: {parser_stats.get('success_rate', 0):.1%}\n"
        
        if status_counts:
            summary += f"- 状态分布: "
            status_desc = {"success": "成功", "error": "错误", "progress": "进行中", "neutral": "中性"}
            status_parts = [f"{status_desc.get(k, k)}({v})" for k, v in status_counts.items()]
            summary += ", ".join(status_parts) + "\n"
        
        if sentiment_counts:
            summary += f"- 情感分布: "
            sentiment_desc = {"positive": "积极", "negative": "消极", "neutral": "中性"}
            sentiment_parts = [f"{sentiment_desc.get(k, k)}({v})" for k, v in sentiment_counts.items()]
            summary += ", ".join(sentiment_parts) + "\n"
        
        # 最近一次分析结果
        if self.parsed_responses_history:
            last_entry = self.parsed_responses_history[-1]
            last_info = last_entry['parsed_info']
            summary += f"- 最近分析: {last_info.extracted_entities.get('status_type', '未知')}状态，"
            summary += f"置信度{last_info.confidence_score:.1%}\n"
        
        return summary
    
    def get_response_analysis_stats(self) -> Dict[str, Any]:
        """获取响应分析统计信息"""
        if not self.response_parser:
            return {"error": "响应解析器未初始化"}
        
        base_stats = self.response_parser.get_stats()
        
        if self.parsed_responses_history:
            # 计算额外统计信息
            confidence_scores = [entry['parsed_info'].confidence_score for entry in self.parsed_responses_history]
            base_stats.update({
                'total_analyzed_responses': len(self.parsed_responses_history),
                'average_confidence': sum(confidence_scores) / len(confidence_scores),
                'min_confidence': min(confidence_scores),
                'max_confidence': max(confidence_scores),
                'low_confidence_count': sum(1 for score in confidence_scores if score < self.confidence_threshold)
            })
        
        return base_stats
    
    def configure_response_parser(self, 
                                 parser_method: Union[str, ParserMethod] = None,
                                 parser_config: Dict[str, Any] = None,
                                 enable_response_analysis: bool = None,
                                 enable_execution_monitoring: bool = None):
        """
        重新配置响应解析器
        
        Args:
            parser_method: 新的解析器方法
            parser_config: 新的解析器配置
            enable_response_analysis: 是否启用响应分析
            enable_execution_monitoring: 是否启用执行监控
        """
        if enable_response_analysis is not None:
            self.enable_response_analysis = enable_response_analysis
        
        if enable_execution_monitoring is not None:
            self.enable_execution_monitoring = enable_execution_monitoring
        
        if parser_method is not None or parser_config is not None:
            # 重新初始化解析器
            self._init_response_parser(
                parser_method=parser_method or "rule",
                parser_config=parser_config or {},
                enable_response_analysis=self.enable_response_analysis,
                enable_execution_monitoring=self.enable_execution_monitoring
            )
            
            # 同步更新AI状态更新器的解析器
            if (hasattr(self, '_ai_updater') and self._ai_updater is not None and
                hasattr(self, 'response_parser') and self.response_parser is not None):
                self._ai_updater.response_parser = self.response_parser
                logger.info("AI状态更新器的响应解析器已同步更新")
        
        logger.info(f"响应解析器配置已更新")
    
    def clear_response_analysis_history(self):
        """清空响应分析历史"""
        self.parsed_responses_history = []
        logger.info("响应分析历史已清空")
    
    def get_natural_language_analysis_summary(self) -> str:
        """获取自然语言形式的分析摘要"""
        if not self.parsed_responses_history:
            return "智能体尚未执行任何任务，暂无分析数据。"
        
        total_responses = len(self.parsed_responses_history)
        confidence_scores = [entry['parsed_info'].confidence_score for entry in self.parsed_responses_history]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        # 分析最近的趋势
        if len(self.parsed_responses_history) >= 3:
            recent_confidences = confidence_scores[-3:]
            if recent_confidences[-1] > recent_confidences[0]:
                trend = "呈上升趋势"
            elif recent_confidences[-1] < recent_confidences[0]:
                trend = "呈下降趋势"
            else:
                trend = "保持稳定"
        else:
            trend = "数据不足"
        
        # 获取主要状态类型
        status_types = [entry['parsed_info'].extracted_entities.get('status_type', 'unknown') 
                       for entry in self.parsed_responses_history]
        if status_types:
            most_common_status = max(set(status_types), key=status_types.count)
            status_desc = {"success": "成功", "error": "错误", "progress": "进行中", "neutral": "中性"}.get(most_common_status, most_common_status)
        else:
            status_desc = "未知"
        
        summary = f"智能体已完成 {total_responses} 个任务的响应分析，"
        summary += f"平均解析置信度为 {avg_confidence:.1%}，置信度{trend}。"
        summary += f"主要任务状态类型为{status_desc}。"
        
        # 获取解析器性能
        if self.response_parser:
            parser_stats = self.response_parser.get_stats()
            success_rate = parser_stats.get('success_rate', 0)
            summary += f"解析器整体成功率为 {success_rate:.1%}。"
        
        return summary

