"""
记忆管理器

协调三层记忆系统的核心管理器
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .interfaces import (
    IWorkingMemory, IEpisodicMemory, ISemanticMemory,
    MemoryItem, Episode, Concept, TriggerType, MemoryLayer
)
from .working_memory import WorkingMemory
from .episodic_memory import EpisodicMemory
from .semantic_memory import SemanticMemory
from .transformers import (
    WorkingToEpisodicTransformer,
    EpisodicToSemanticTransformer,
    SemanticToEpisodicTransformer,
    EpisodicToWorkingTransformer
)
from .utils import calculate_importance


class MemoryManager:
    """记忆管理器 - 协调三层记忆"""
    
    def __init__(self, 
                 working_memory: Optional[IWorkingMemory] = None,
                 episodic_memory: Optional[IEpisodicMemory] = None,
                 semantic_memory: Optional[ISemanticMemory] = None,
                 auto_promote: bool = True,
                 auto_decay: bool = True):
        """
        初始化记忆管理器
        
        Args:
            working_memory: 工作记忆实例
            episodic_memory: 情景记忆实例
            semantic_memory: 语义记忆实例
            auto_promote: 是否自动提升记忆层级
            auto_decay: 是否自动执行衰减
        """
        self.working = working_memory or WorkingMemory()
        self.episodic = episodic_memory or EpisodicMemory()
        self.semantic = semantic_memory or SemanticMemory()
        
        self.auto_promote = auto_promote
        self.auto_decay = auto_decay
        
        # 初始化转换器
        self._transformers = {
            'working_to_episodic': WorkingToEpisodicTransformer(),
            'episodic_to_semantic': EpisodicToSemanticTransformer(),
            'semantic_to_episodic': SemanticToEpisodicTransformer(),
            'episodic_to_working': EpisodicToWorkingTransformer()
        }
        
        # 统计信息
        self._stats = {
            'total_processed': 0,
            'promotions': {'working_to_episodic': 0, 'episodic_to_semantic': 0},
            'recalls': {'working': 0, 'episodic': 0, 'semantic': 0},
            'decays': 0
        }
    
    def process_information(self, 
                          info: Any, 
                          source: str = 'external',
                          trigger_type: TriggerType = TriggerType.MANUAL,
                          metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        处理新信息，决定存储层级
        
        Args:
            info: 信息内容
            source: 信息来源
            trigger_type: 触发类型
            metadata: 元数据
            
        Returns:
            处理结果
        """
        self._stats['total_processed'] += 1
        
        # 计算重要性
        importance = calculate_importance(info, metadata or {})
        
        # 决定存储策略
        result = {
            'stored_in': [],
            'ids': {},
            'importance': importance
        }
        
        # 根据重要性决定存储层级
        if importance < 0.3:
            # 低重要性 - 仅工作记忆
            memory_id = self.working.add_with_trigger(
                info, trigger_type, metadata=metadata
            )
            if memory_id:
                result['stored_in'].append(MemoryLayer.WORKING.value)
                result['ids']['working'] = memory_id
        
        elif importance < 0.7:
            # 中等重要性 - 工作记忆 + 可能提升到情景记忆
            memory_id = self.working.add_with_trigger(
                info, trigger_type, metadata=metadata
            )
            if memory_id:
                result['stored_in'].append(MemoryLayer.WORKING.value)
                result['ids']['working'] = memory_id
                
                # 考虑提升到情景记忆
                if self.auto_promote and self._should_promote_to_episodic():
                    episode_id = self._promote_working_to_episodic()
                    if episode_id:
                        result['stored_in'].append(MemoryLayer.EPISODIC.value)
                        result['ids']['episodic'] = episode_id
                        self._stats['promotions']['working_to_episodic'] += 1
        
        else:
            # 高重要性 - 全部三层
            memory_id = self.working.add_with_trigger(
                info, trigger_type, metadata=metadata
            )
            if memory_id:
                result['stored_in'].append(MemoryLayer.WORKING.value)
                result['ids']['working'] = memory_id
                
                # 立即提升到情景记忆
                episode_data = {
                    'event': f"Important {trigger_type.value}: {str(info)[:100]}",
                    'context': {
                        'content': info,
                        'trigger_type': trigger_type.value,
                        'source': source,
                        'importance': importance
                    },
                    'metadata': metadata
                }
                episode_id = self.episodic.store_episode(**episode_data)
                result['stored_in'].append(MemoryLayer.EPISODIC.value)
                result['ids']['episodic'] = episode_id
                
                # 考虑是否提取语义知识
                if self.auto_promote:
                    self._consider_semantic_extraction(episode_id)
        
        # 执行自动衰减
        if self.auto_decay and self._stats['total_processed'] % 10 == 0:
            decayed = self.working.decay()
            self._stats['decays'] += decayed
        
        return result
    
    def recall_with_context(self, 
                          query: str, 
                          context: Dict[str, Any] = None,
                          layers: Union[MemoryLayer, List[MemoryLayer]] = MemoryLayer.ALL,
                          limit: int = 10) -> Dict[str, List[MemoryItem]]:
        """
        基于上下文的多层记忆召回
        
        Args:
            query: 查询字符串
            context: 上下文信息
            layers: 要查询的记忆层
            limit: 每层的结果限制
            
        Returns:
            各层的查询结果
        """
        # 处理层级参数
        if isinstance(layers, MemoryLayer):
            if layers == MemoryLayer.ALL:
                query_layers = [MemoryLayer.WORKING, MemoryLayer.EPISODIC, MemoryLayer.SEMANTIC]
            else:
                query_layers = [layers]
        else:
            query_layers = layers
        
        results = {}
        
        # 查询各层
        if MemoryLayer.WORKING in query_layers:
            results['working'] = self.working.recall(query, limit=limit)
            self._stats['recalls']['working'] += 1
        
        if MemoryLayer.EPISODIC in query_layers:
            if context and 'project_id' in context:
                # 先获取项目上下文
                project_context = self.episodic.get_project_context(context['project_id'])
                # 在项目范围内搜索
                all_episodes = self.episodic.recall(query, limit=limit * 2)
                results['episodic'] = [
                    item for item in all_episodes 
                    if item.metadata.get('project_id') == context['project_id']
                ][:limit]
            else:
                results['episodic'] = self.episodic.recall(query, limit=limit)
            self._stats['recalls']['episodic'] += 1
        
        if MemoryLayer.SEMANTIC in query_layers:
            results['semantic'] = self.semantic.recall(query, limit=limit)
            self._stats['recalls']['semantic'] += 1
        
        # 整合结果
        return self._integrate_recall_results(results, context)
    
    def promote_memory(self, 
                      source_layer: MemoryLayer, 
                      target_layer: MemoryLayer,
                      memory_id: str) -> Optional[str]:
        """
        手动提升记忆到更高层级
        
        Args:
            source_layer: 源层级
            target_layer: 目标层级
            memory_id: 记忆ID
            
        Returns:
            新记忆ID或None
        """
        if source_layer == MemoryLayer.WORKING and target_layer == MemoryLayer.EPISODIC:
            # 获取工作记忆项
            item = self.working.get(memory_id)
            if item:
                # 转换为情景
                episode_data = {
                    'event': f"Promoted from working memory: {str(item.content)[:100]}",
                    'context': {
                        'content': item.content,
                        'original_id': memory_id,
                        'importance': item.importance,
                        'metadata': item.metadata
                    }
                }
                return self.episodic.store_episode(**episode_data)
        
        elif source_layer == MemoryLayer.EPISODIC and target_layer == MemoryLayer.SEMANTIC:
            # 获取情景
            episode = self.episodic.get(memory_id)
            if episode:
                # 查找相似情景
                similar_episodes = self._find_similar_episodes(memory_id)
                if len(similar_episodes) >= 2:
                    # 提取概念
                    transformer = self._transformers['episodic_to_semantic']
                    concept = transformer.transform(similar_episodes)
                    if concept:
                        return self.semantic.add_concept(concept)
        
        return None
    
    def get_memory_timeline(self, 
                          start: datetime, 
                          end: datetime,
                          project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取时间范围内的记忆时间线
        
        Args:
            start: 开始时间
            end: 结束时间
            project_id: 项目ID（可选）
            
        Returns:
            时间线事件列表
        """
        timeline = []
        
        # 获取工作记忆（如果在时间范围内）
        working_items = self.working.list_all()
        for item in working_items:
            if start <= item.timestamp <= end:
                timeline.append({
                    'timestamp': item.timestamp,
                    'layer': 'working',
                    'type': item.metadata.get('trigger_type', 'unknown'),
                    'content': str(item.content)[:100],
                    'importance': item.importance
                })
        
        # 获取情景记忆
        episodes = self.episodic.query_timeline(start, end, project_id)
        for episode in episodes:
            timeline.append({
                'timestamp': episode.timestamp,
                'layer': 'episodic',
                'type': 'episode',
                'content': episode.event,
                'importance': 0.7,  # 默认重要性
                'episode_id': episode.id
            })
        
        # 按时间排序
        timeline.sort(key=lambda x: x['timestamp'])
        
        return timeline
    
    def analyze_memory_patterns(self, 
                              time_window: Optional[tuple] = None,
                              min_pattern_occurrences: int = 3) -> Dict[str, Any]:
        """
        分析记忆中的模式
        
        Args:
            time_window: (start, end) 时间窗口
            min_pattern_occurrences: 最小模式出现次数
            
        Returns:
            模式分析结果
        """
        analysis = {
            'episodic_patterns': [],
            'semantic_concepts': [],
            'working_memory_stats': {},
            'recommendations': []
        }
        
        # 分析情景模式
        episodic_patterns = self.episodic.analyze_patterns(
            min_occurrences=min_pattern_occurrences
        )
        analysis['episodic_patterns'] = episodic_patterns
        
        # 获取高置信度概念
        all_concepts = []
        for item in self.semantic.list_all():
            concept = self.semantic._get_concept(item.id)
            if concept and concept.confidence > 0.7:
                all_concepts.append({
                    'id': concept.id,
                    'name': concept.name,
                    'category': concept.category,
                    'confidence': concept.confidence,
                    'examples_count': len(concept.examples)
                })
        analysis['semantic_concepts'] = all_concepts
        
        # 工作记忆统计
        wm_stats = self.working.get_statistics()
        analysis['working_memory_stats'] = wm_stats
        
        # 生成建议
        if len(episodic_patterns) > 5:
            analysis['recommendations'].append(
                "High pattern density detected. Consider extracting semantic concepts."
            )
        
        if wm_stats.get('avg_access_count', 0) < 2:
            analysis['recommendations'].append(
                "Low working memory utilization. Consider adjusting decay threshold."
            )
        
        return analysis
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取记忆管理统计信息"""
        return {
            'manager_stats': self._stats.copy(),
            'layer_stats': {
                'working': self.working.get_statistics(),
                'episodic': {
                    'total_episodes': self.episodic.size(),
                    'projects': len(self.episodic._project_index),
                    'relationships': sum(
                        len(rels) for rels in self.episodic._relationships.values()
                    )
                },
                'semantic': {
                    'total_concepts': self.semantic.size(),
                    'categories': len(self.semantic._category_index),
                    'domains': len(self.semantic._domain_index)
                }
            }
        }
    
    def _should_promote_to_episodic(self) -> bool:
        """判断是否应该提升到情景记忆"""
        # 基于工作记忆的活跃程度
        active_memories = self.working.get_active_memories()
        if len(active_memories) >= self.working.capacity * 0.8:
            return True
        
        # 基于重要事件累积
        high_importance_count = sum(
            1 for mem in active_memories if mem.importance > 0.6
        )
        
        return high_importance_count >= 3
    
    def _promote_working_to_episodic(self) -> Optional[str]:
        """将工作记忆提升到情景记忆"""
        # 整合工作记忆
        consolidated = self.working.consolidate()
        if not consolidated or not consolidated.get('events'):
            return None
        
        # 使用转换器
        transformer = self._transformers['working_to_episodic']
        episode_data = transformer.transform(consolidated)
        
        # 存储为情景
        return self.episodic.store_episode(**episode_data)
    
    def _consider_semantic_extraction(self, episode_id: str) -> Optional[str]:
        """考虑是否提取语义知识"""
        # 查找相似情景
        similar_episodes = self._find_similar_episodes(episode_id)
        
        if len(similar_episodes) >= 3:
            # 使用转换器提取模式
            transformer = self._transformers['episodic_to_semantic']
            concept = transformer.transform(similar_episodes)
            
            if concept:
                concept_id = self.semantic.add_concept(concept)
                self._stats['promotions']['episodic_to_semantic'] += 1
                return concept_id
        
        return None
    
    def _find_similar_episodes(self, episode_id: str) -> List[Episode]:
        """查找相似的情景"""
        target_item = self.episodic.get(episode_id)
        if not target_item:
            return []
        
        # 使用情景记忆的相似性搜索
        similar_items = self.episodic.recall(
            target_item.content.get('event', ''), 
            limit=10
        )
        
        episodes = []
        for item in similar_items:
            if item.id != episode_id:
                # 尝试转换为Episode对象
                episode = self.episodic._get_episode(item.id)
                if episode:
                    episodes.append(episode)
        
        return episodes[:5]  # 最多返回5个
    
    def _integrate_recall_results(self, 
                                results: Dict[str, List[MemoryItem]], 
                                context: Dict[str, Any] = None) -> Dict[str, List[MemoryItem]]:
        """整合多层召回结果"""
        # 计算综合相关性分数
        all_items = []
        
        for layer, items in results.items():
            for item in items:
                # 根据层级调整权重
                layer_weight = {
                    'working': 1.2,    # 工作记忆更相关
                    'episodic': 1.0,   # 情景记忆标准权重
                    'semantic': 0.8    # 语义记忆稍低权重
                }.get(layer, 1.0)
                
                # 综合评分
                score = item.importance * layer_weight
                
                # 如果有上下文匹配，提高分数
                if context:
                    if context.get('project_id') and \
                       item.metadata.get('project_id') == context['project_id']:
                        score *= 1.5
                
                all_items.append((score, layer, item))
        
        # 按分数排序
        all_items.sort(key=lambda x: x[0], reverse=True)
        
        # 重组结果
        integrated = {'working': [], 'episodic': [], 'semantic': []}
        for score, layer, item in all_items:
            integrated[layer].append(item)
        
        return integrated