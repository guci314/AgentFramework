"""
记忆转换器

实现不同记忆层之间的转换机制
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict

from .interfaces import MemoryItem, Episode, Concept, MemoryType
from .utils import extract_keywords, calculate_similarity


class IMemoryTransformer(ABC):
    """记忆转换器接口"""
    
    @abstractmethod
    def transform(self, source_data: Any) -> Any:
        """
        转换记忆数据
        
        Args:
            source_data: 源数据
            
        Returns:
            转换后的数据
        """
        pass
    
    @abstractmethod
    def can_transform(self, source_data: Any) -> bool:
        """
        检查是否可以转换
        
        Args:
            source_data: 源数据
            
        Returns:
            是否可以转换
        """
        pass


class WorkingToEpisodicTransformer(IMemoryTransformer):
    """工作记忆到情景记忆的转换器"""
    
    def transform(self, source_data: Any) -> Dict[str, Any]:
        """
        将工作记忆数据转换为情景记忆格式
        
        Args:
            source_data: 工作记忆的consolidate()输出或MemoryItem列表
            
        Returns:
            适合存储为Episode的数据
        """
        if isinstance(source_data, dict) and 'events' in source_data:
            # 处理consolidate()的输出
            return self._transform_consolidated(source_data)
        elif isinstance(source_data, list):
            # 处理MemoryItem列表
            return self._transform_items(source_data)
        else:
            raise ValueError("Unsupported source data type")
    
    def can_transform(self, source_data: Any) -> bool:
        """检查是否可以转换"""
        if isinstance(source_data, dict):
            return 'events' in source_data and 'start_time' in source_data
        elif isinstance(source_data, list):
            return all(isinstance(item, MemoryItem) for item in source_data)
        return False
    
    def _transform_consolidated(self, consolidated: Dict[str, Any]) -> Dict[str, Any]:
        """转换整合后的数据"""
        # 生成事件描述
        event_description = self._generate_event_description(consolidated)
        
        # 构建上下文
        context = {
            'duration': consolidated.get('duration', 0),
            'events_count': consolidated.get('items_count', 0),
            'time_range': {
                'start': consolidated.get('start_time'),
                'end': consolidated.get('end_time')
            },
            'summary': consolidated.get('summary', {})
        }
        
        # 提取关键事件
        key_events = []
        for event in consolidated.get('events', []):
            if event['importance'] > 0.6:
                key_events.append({
                    'content': event['content'],
                    'trigger_type': event['trigger_type']
                })
        
        if key_events:
            context['key_events'] = key_events
        
        # 分析结果
        outcomes = self._analyze_outcomes(consolidated)
        
        return {
            'event': event_description,
            'context': context,
            'outcomes': outcomes,
            'timestamp': consolidated.get('end_time', datetime.now())
        }
    
    def _transform_items(self, items: List[MemoryItem]) -> Dict[str, Any]:
        """转换记忆项列表"""
        if not items:
            return {}
        
        # 按时间排序
        items.sort(key=lambda x: x.timestamp)
        
        # 构建事件序列
        events = []
        for item in items:
            events.append({
                'timestamp': item.timestamp,
                'content': item.content,
                'importance': item.importance,
                'trigger_type': item.metadata.get('trigger_type', 'unknown')
            })
        
        # 创建整合数据
        consolidated = {
            'start_time': items[0].timestamp,
            'end_time': items[-1].timestamp,
            'duration': (items[-1].timestamp - items[0].timestamp).total_seconds(),
            'items_count': len(items),
            'events': events
        }
        
        # 使用整合方法转换
        return self._transform_consolidated(consolidated)
    
    def _generate_event_description(self, consolidated: Dict[str, Any]) -> str:
        """生成事件描述"""
        events = consolidated.get('events', [])
        if not events:
            return "Empty working memory session"
        
        # 统计触发类型
        trigger_counts = defaultdict(int)
        for event in events:
            trigger_counts[event.get('trigger_type', 'unknown')] += 1
        
        # 找出主要触发类型
        main_trigger = max(trigger_counts.items(), key=lambda x: x[1])[0]
        
        # 生成描述
        duration = consolidated.get('duration', 0)
        duration_str = f"{duration:.1f}s" if duration < 60 else f"{duration/60:.1f}min"
        
        description = f"Working memory session ({duration_str})"
        
        if main_trigger != 'unknown':
            description += f" - mainly {main_trigger} events"
        
        summary = consolidated.get('summary', {})
        if summary.get('total_errors', 0) > 0:
            description += f" with {summary['total_errors']} errors"
        
        return description
    
    def _analyze_outcomes(self, consolidated: Dict[str, Any]) -> Dict[str, Any]:
        """分析结果"""
        outcomes = {}
        
        summary = consolidated.get('summary', {})
        events = consolidated.get('events', [])
        
        # 分析错误
        if summary.get('total_errors', 0) > 0:
            error_events = [e for e in events if e.get('trigger_type') == 'error']
            outcomes['errors'] = [e['content'] for e in error_events]
        
        # 分析决策
        if summary.get('total_decisions', 0) > 0:
            decision_events = [e for e in events if e.get('trigger_type') == 'decision']
            outcomes['decisions'] = [e['content'] for e in decision_events]
        
        # 总体评估
        avg_importance = summary.get('avg_importance', 0.5)
        if avg_importance > 0.7:
            outcomes['significance'] = 'high'
        elif avg_importance > 0.4:
            outcomes['significance'] = 'medium'
        else:
            outcomes['significance'] = 'low'
        
        return outcomes


class EpisodicToSemanticTransformer(IMemoryTransformer):
    """情景记忆到语义记忆的转换器"""
    
    def __init__(self, min_examples: int = 3, min_confidence: float = 0.6):
        """
        初始化转换器
        
        Args:
            min_examples: 提取模式所需的最小示例数
            min_confidence: 最小置信度阈值
        """
        self.min_examples = min_examples
        self.min_confidence = min_confidence
    
    def transform(self, source_data: List[Episode]) -> Optional[Concept]:
        """
        从情景集合中提取概念
        
        Args:
            source_data: Episode列表
            
        Returns:
            提取的概念或None
        """
        if not self.can_transform(source_data):
            return None
        
        # 分析情景模式
        pattern = self._analyze_episodes(source_data)
        if not pattern:
            return None
        
        # 创建概念
        concept = Concept(
            id="",  # 将由SemanticMemory分配
            name=pattern['name'],
            category=pattern['category'],
            attributes=pattern['attributes'],
            confidence=pattern['confidence'],
            examples=pattern['examples'],
            domain=pattern.get('domain')
        )
        
        return concept
    
    def can_transform(self, source_data: Any) -> bool:
        """检查是否可以转换"""
        if not isinstance(source_data, list):
            return False
        
        if len(source_data) < self.min_examples:
            return False
        
        return all(isinstance(item, Episode) for item in source_data)
    
    def extract_pattern(self, episodes: List[Episode]) -> Optional[Dict[str, Any]]:
        """
        提取情景中的模式（公共方法，供MemoryManager使用）
        
        Args:
            episodes: 情景列表
            
        Returns:
            模式字典或None
        """
        return self._analyze_episodes(episodes)
    
    def _analyze_episodes(self, episodes: List[Episode]) -> Optional[Dict[str, Any]]:
        """分析情景集合，提取共同模式"""
        if len(episodes) < self.min_examples:
            return None
        
        # 提取共同特征
        common_context_keys = self._find_common_keys(episodes)
        common_attributes = self._extract_common_attributes(episodes, common_context_keys)
        
        # 计算相似度和置信度
        similarity_score = self._calculate_episode_similarity(episodes)
        confidence = min(1.0, similarity_score * (len(episodes) / 10))
        
        if confidence < self.min_confidence:
            return None
        
        # 确定类别和名称
        category = self._determine_category(episodes)
        name = self._generate_pattern_name(episodes, category)
        
        # 准备示例
        examples = []
        for episode in episodes[:5]:  # 最多保留5个示例
            examples.append({
                'event': episode.event,
                'context': episode.context,
                'outcomes': episode.outcomes
            })
        
        return {
            'name': name,
            'category': category,
            'attributes': common_attributes,
            'confidence': confidence,
            'examples': examples,
            'domain': self._determine_domain(episodes)
        }
    
    def _find_common_keys(self, episodes: List[Episode]) -> Set[str]:
        """找出所有情景中的共同键"""
        if not episodes:
            return set()
        
        # 初始化为第一个情景的键
        common_keys = set(episodes[0].context.keys())
        
        # 与其他情景的键取交集
        for episode in episodes[1:]:
            common_keys &= set(episode.context.keys())
        
        return common_keys
    
    def _extract_common_attributes(self, episodes: List[Episode], 
                                  common_keys: Set[str]) -> Dict[str, Any]:
        """提取共同属性"""
        attributes = {}
        
        for key in common_keys:
            values = [ep.context[key] for ep in episodes]
            
            # 如果所有值都相同
            if len(set(str(v) for v in values)) == 1:
                attributes[key] = values[0]
            else:
                # 记录值的变化模式
                unique_values = list(set(str(v) for v in values))[:3]
                attributes[key] = {
                    'type': 'variable',
                    'examples': unique_values
                }
        
        # 分析事件模式
        event_keywords = defaultdict(int)
        for episode in episodes:
            for keyword in extract_keywords(episode.event):
                event_keywords[keyword] += 1
        
        # 找出频繁关键词
        frequent_keywords = [k for k, count in event_keywords.items() 
                           if count >= len(episodes) * 0.5]
        
        if frequent_keywords:
            attributes['event_keywords'] = frequent_keywords
        
        return attributes
    
    def _calculate_episode_similarity(self, episodes: List[Episode]) -> float:
        """计算情景集合的相似度"""
        if len(episodes) < 2:
            return 1.0
        
        total_similarity = 0.0
        comparisons = 0
        
        # 比较每对情景
        for i in range(len(episodes)):
            for j in range(i + 1, len(episodes)):
                # 事件相似度
                event_sim = calculate_similarity(episodes[i].event, episodes[j].event)
                
                # 上下文相似度
                context_sim = self._calculate_context_similarity(
                    episodes[i].context, episodes[j].context
                )
                
                total_similarity += (event_sim + context_sim) / 2
                comparisons += 1
        
        return total_similarity / comparisons if comparisons > 0 else 0.0
    
    def _calculate_context_similarity(self, context1: Dict[str, Any], 
                                    context2: Dict[str, Any]) -> float:
        """计算上下文相似度"""
        all_keys = set(context1.keys()) | set(context2.keys())
        if not all_keys:
            return 0.0
        
        common_keys = set(context1.keys()) & set(context2.keys())
        
        # 键重叠度
        key_overlap = len(common_keys) / len(all_keys)
        
        # 值相似度
        value_similarity = 0.0
        for key in common_keys:
            if context1[key] == context2[key]:
                value_similarity += 1.0
            else:
                # 简单的字符串相似度
                str_sim = calculate_similarity(str(context1[key]), str(context2[key]))
                value_similarity += str_sim
        
        value_score = value_similarity / len(common_keys) if common_keys else 0
        
        return (key_overlap + value_score) / 2
    
    def _determine_category(self, episodes: List[Episode]) -> str:
        """确定模式类别"""
        # 基于事件类型统计
        event_types = defaultdict(int)
        
        for episode in episodes:
            # 简单的事件类型推断
            event_lower = episode.event.lower()
            if any(word in event_lower for word in ['error', 'fail', 'exception']):
                event_types['error_pattern'] += 1
            elif any(word in event_lower for word in ['success', 'complete', 'finish']):
                event_types['success_pattern'] += 1
            elif any(word in event_lower for word in ['decide', 'choose', 'select']):
                event_types['decision_pattern'] += 1
            elif any(word in event_lower for word in ['process', 'execute', 'perform']):
                event_types['process_pattern'] += 1
            else:
                event_types['general_pattern'] += 1
        
        # 返回最频繁的类型
        return max(event_types.items(), key=lambda x: x[1])[0]
    
    def _generate_pattern_name(self, episodes: List[Episode], category: str) -> str:
        """生成模式名称"""
        # 提取关键词
        all_keywords = set()
        for episode in episodes[:3]:  # 使用前3个情景
            keywords = extract_keywords(episode.event)
            all_keywords.update(keywords)
        
        # 选择最具代表性的关键词
        keyword_str = "_".join(list(all_keywords)[:3])
        
        if keyword_str:
            return f"{category}_{keyword_str}"
        else:
            return f"{category}_{len(episodes)}_instances"
    
    def _determine_domain(self, episodes: List[Episode]) -> Optional[str]:
        """确定领域"""
        # 如果所有情景都属于同一项目
        project_ids = set(ep.project_id for ep in episodes if ep.project_id)
        if len(project_ids) == 1:
            return f"project_{list(project_ids)[0]}"
        
        # 基于参与者推断
        all_participants = set()
        for episode in episodes:
            all_participants.update(episode.participants)
        
        if all_participants:
            return f"domain_{list(all_participants)[0]}"
        
        return None


class SemanticToEpisodicTransformer(IMemoryTransformer):
    """语义记忆到情景记忆的转换器"""
    
    def transform(self, source_data: tuple) -> Dict[str, Any]:
        """
        将语义概念实例化为情景
        
        Args:
            source_data: (Concept, context) 元组
            
        Returns:
            适合存储为Episode的数据
        """
        concept, context = source_data
        
        # 生成事件描述
        event = f"Applying concept '{concept.name}' in practice"
        
        # 构建情景上下文
        episode_context = {
            'concept_id': concept.id,
            'concept_name': concept.name,
            'concept_category': concept.category,
            'application_context': context,
            'concept_attributes': concept.attributes
        }
        
        # 如果有示例，选择最相关的
        if concept.examples:
            # 简单选择第一个示例
            episode_context['reference_example'] = concept.examples[0]
        
        return {
            'event': event,
            'context': episode_context,
            'outcomes': {
                'concept_applied': True,
                'confidence': concept.confidence
            }
        }
    
    def can_transform(self, source_data: Any) -> bool:
        """检查是否可以转换"""
        if not isinstance(source_data, tuple) or len(source_data) != 2:
            return False
        
        concept, context = source_data
        return isinstance(concept, Concept) and isinstance(context, dict)


class EpisodicToWorkingTransformer(IMemoryTransformer):
    """情景记忆到工作记忆的转换器"""
    
    def transform(self, source_data: Episode) -> List[Dict[str, Any]]:
        """
        将情景分解为工作记忆项
        
        Args:
            source_data: Episode对象
            
        Returns:
            适合加载到工作记忆的数据列表
        """
        working_items = []
        
        # 主事件
        working_items.append({
            'content': {
                'type': 'recalled_event',
                'event': source_data.event,
                'episode_id': source_data.id,
                'timestamp': source_data.timestamp
            },
            'importance': 0.7,
            'metadata': {
                'source': 'episodic_recall',
                'episode_id': source_data.id
            }
        })
        
        # 关键上下文
        for key, value in source_data.context.items():
            if key in ['key_events', 'critical_decisions', 'important_outcomes']:
                working_items.append({
                    'content': {
                        'type': f'recalled_{key}',
                        'data': value
                    },
                    'importance': 0.6,
                    'metadata': {
                        'source': 'episodic_recall',
                        'episode_id': source_data.id,
                        'context_key': key
                    }
                })
        
        # 结果
        if source_data.outcomes:
            working_items.append({
                'content': {
                    'type': 'recalled_outcomes',
                    'outcomes': source_data.outcomes
                },
                'importance': 0.8,
                'metadata': {
                    'source': 'episodic_recall',
                    'episode_id': source_data.id
                }
            })
        
        return working_items
    
    def can_transform(self, source_data: Any) -> bool:
        """检查是否可以转换"""
        return isinstance(source_data, Episode)