"""
情景记忆实现

实现了项目中心的组织、时序存储和上下文管理
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict

from .interfaces import IEpisodicMemory, Episode, MemoryItem
from .base_memory import BaseMemory, InMemoryStorage
from .utils import generate_memory_id, merge_metadata


class EpisodicMemory(BaseMemory, IEpisodicMemory):
    """情景记忆实现"""
    
    def __init__(self, storage: Optional[InMemoryStorage] = None):
        """
        初始化情景记忆
        
        Args:
            storage: 存储策略，默认使用内存存储
        """
        super().__init__(storage or InMemoryStorage())
        
        # 项目索引：项目ID -> 情景ID列表
        self._project_index: Dict[str, List[str]] = defaultdict(list)
        
        # 时间索引：用于快速时间范围查询
        self._timeline: List[tuple[datetime, str]] = []  # (timestamp, episode_id)
        
        # 关系索引：情景ID -> {关系类型 -> [相关情景ID]}
        self._relationships: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        
        # 情景对象缓存
        self._episode_cache: Dict[str, Episode] = {}
    
    def store_episode(self, event: str, context: Dict[str, Any], **kwargs) -> str:
        """存储情景事件"""
        # 创建情景对象
        episode = Episode(
            id=generate_memory_id("ep"),
            event=event,
            context=context,
            timestamp=kwargs.get('timestamp', datetime.now()),
            project_id=kwargs.get('project_id'),
            participants=kwargs.get('participants', []),
            outcomes=kwargs.get('outcomes', {}),
            related_episodes=kwargs.get('related_episodes', [])
        )
        
        # 转换为记忆项并存储
        memory_item = episode.to_memory_item()
        self.storage.put(episode.id, memory_item)
        
        # 更新缓存
        self._episode_cache[episode.id] = episode
        
        # 更新索引
        self._update_indices(episode)
        
        return episode.id
    
    def query_timeline(self, start: datetime, end: datetime, project_id: Optional[str] = None) -> List[Episode]:
        """按时间线查询"""
        episodes = []
        
        # 二分查找起始位置
        start_idx = self._binary_search_timeline(start)
        
        # 从起始位置开始收集符合条件的情景
        for i in range(start_idx, len(self._timeline)):
            timestamp, episode_id = self._timeline[i]
            
            # 如果超过结束时间，停止
            if timestamp > end:
                break
            
            episode = self._get_episode(episode_id)
            if episode:
                # 如果指定了项目ID，进行过滤
                if project_id is None or episode.project_id == project_id:
                    episodes.append(episode)
        
        return episodes
    
    def get_project_context(self, project_id: str) -> Dict[str, Any]:
        """获取项目上下文"""
        # 获取项目的所有情景
        episode_ids = self._project_index.get(project_id, [])
        episodes = [self._get_episode(eid) for eid in episode_ids if self._get_episode(eid)]
        
        if not episodes:
            return {
                'project_id': project_id,
                'episodes_count': 0,
                'timeline': [],
                'participants': set(),
                'key_events': []
            }
        
        # 按时间排序
        episodes.sort(key=lambda e: e.timestamp)
        
        # 提取参与者
        all_participants = set()
        for episode in episodes:
            all_participants.update(episode.participants)
        
        # 识别关键事件（基于关联数量和结果影响）
        key_events = []
        for episode in episodes:
            importance_score = len(episode.related_episodes) * 0.3
            if episode.outcomes:
                importance_score += len(episode.outcomes) * 0.2
            
            if importance_score > 0.5:
                key_events.append({
                    'episode_id': episode.id,
                    'event': episode.event,
                    'timestamp': episode.timestamp,
                    'importance': importance_score
                })
        
        # 构建时间线
        timeline = []
        for episode in episodes:
            timeline.append({
                'timestamp': episode.timestamp,
                'event': episode.event,
                'episode_id': episode.id
            })
        
        return {
            'project_id': project_id,
            'episodes_count': len(episodes),
            'start_time': episodes[0].timestamp,
            'end_time': episodes[-1].timestamp,
            'duration': (episodes[-1].timestamp - episodes[0].timestamp).total_seconds(),
            'timeline': timeline,
            'participants': list(all_participants),
            'key_events': sorted(key_events, key=lambda x: x['importance'], reverse=True)[:10]
        }
    
    def link_episodes(self, episode_id1: str, episode_id2: str, relationship: str) -> bool:
        """关联两个情景"""
        # 检查情景是否存在
        ep1 = self._get_episode(episode_id1)
        ep2 = self._get_episode(episode_id2)
        
        if not ep1 or not ep2:
            return False
        
        # 建立双向关系
        self._relationships[episode_id1][relationship].append(episode_id2)
        self._relationships[episode_id2][f"reverse_{relationship}"].append(episode_id1)
        
        # 更新情景的关联列表
        if episode_id2 not in ep1.related_episodes:
            ep1.related_episodes.append(episode_id2)
        if episode_id1 not in ep2.related_episodes:
            ep2.related_episodes.append(episode_id1)
        
        # 更新存储
        self._update_episode_storage(ep1)
        self._update_episode_storage(ep2)
        
        return True
    
    def get_related_episodes(self, episode_id: str, relationship: Optional[str] = None) -> List[Episode]:
        """获取相关情景"""
        related_episodes = []
        
        if relationship:
            # 获取特定关系的情景
            related_ids = self._relationships.get(episode_id, {}).get(relationship, [])
        else:
            # 获取所有相关情景
            related_ids = []
            for rel_episodes in self._relationships.get(episode_id, {}).values():
                related_ids.extend(rel_episodes)
        
        # 去重并获取情景对象
        for eid in set(related_ids):
            episode = self._get_episode(eid)
            if episode:
                related_episodes.append(episode)
        
        return related_episodes
    
    def find_similar_episodes(self, episode_id: str, limit: int = 5) -> List[Episode]:
        """查找相似的情景"""
        target_episode = self._get_episode(episode_id)
        if not target_episode:
            return []
        
        # 基于事件内容查找相似情景
        similar_items = self.recall(target_episode.event, limit=limit * 2)
        
        similar_episodes = []
        for item in similar_items:
            if item.id != episode_id:
                episode = self._get_episode(item.id)
                if episode:
                    similar_episodes.append(episode)
        
        return similar_episodes[:limit]
    
    def analyze_patterns(self, project_id: Optional[str] = None, min_occurrences: int = 3) -> List[Dict[str, Any]]:
        """分析情景中的模式"""
        # 获取要分析的情景
        if project_id:
            episode_ids = self._project_index.get(project_id, [])
            episodes = [self._get_episode(eid) for eid in episode_ids if self._get_episode(eid)]
        else:
            episodes = [self._get_episode(item.id) for item in self.list_all() 
                       if self._get_episode(item.id)]
        
        # 统计事件模式
        event_patterns = defaultdict(list)
        context_patterns = defaultdict(list)
        
        for episode in episodes:
            # 简化事件描述以识别模式
            event_key = self._normalize_event(episode.event)
            event_patterns[event_key].append(episode)
            
            # 提取上下文模式
            for key, value in episode.context.items():
                if isinstance(value, str):
                    context_patterns[(key, value)].append(episode)
        
        # 筛选频繁模式
        patterns = []
        
        # 事件模式
        for event_key, episodes in event_patterns.items():
            if len(episodes) >= min_occurrences:
                patterns.append({
                    'type': 'event_pattern',
                    'pattern': event_key,
                    'occurrences': len(episodes),
                    'episodes': [e.id for e in episodes],
                    'timespan': {
                        'start': min(e.timestamp for e in episodes),
                        'end': max(e.timestamp for e in episodes)
                    }
                })
        
        # 上下文模式
        for (key, value), episodes in context_patterns.items():
            if len(episodes) >= min_occurrences:
                patterns.append({
                    'type': 'context_pattern',
                    'pattern': f"{key}={value}",
                    'occurrences': len(episodes),
                    'episodes': [e.id for e in episodes]
                })
        
        return sorted(patterns, key=lambda x: x['occurrences'], reverse=True)
    
    def _get_episode(self, episode_id: str) -> Optional[Episode]:
        """获取情景对象"""
        # 先检查缓存
        if episode_id in self._episode_cache:
            return self._episode_cache[episode_id]
        
        # 从存储获取
        item = self.get(episode_id)
        if item and item.metadata.get('type') == 'episode':
            # 重建情景对象
            episode = Episode(
                id=item.id,
                event=item.content.get('event', ''),
                context=item.content.get('context', {}),
                timestamp=item.timestamp,
                project_id=item.metadata.get('project_id'),
                participants=item.metadata.get('participants', []),
                outcomes=item.content.get('outcomes', {}),
                related_episodes=item.metadata.get('related_episodes', [])
            )
            
            # 更新缓存
            self._episode_cache[episode_id] = episode
            return episode
        
        return None
    
    def _update_indices(self, episode: Episode) -> None:
        """更新各种索引"""
        # 更新项目索引
        if episode.project_id:
            self._project_index[episode.project_id].append(episode.id)
        
        # 更新时间索引（保持排序）
        import bisect
        bisect.insort(self._timeline, (episode.timestamp, episode.id))
    
    def _update_episode_storage(self, episode: Episode) -> None:
        """更新情景的存储"""
        memory_item = episode.to_memory_item()
        self.storage.put(episode.id, memory_item)
    
    def _binary_search_timeline(self, target_time: datetime) -> int:
        """二分查找时间线中的位置"""
        left, right = 0, len(self._timeline)
        
        while left < right:
            mid = (left + right) // 2
            if self._timeline[mid][0] < target_time:
                left = mid + 1
            else:
                right = mid
        
        return left
    
    def _normalize_event(self, event: str) -> str:
        """规范化事件描述以识别模式"""
        # 简单的规范化：转小写，移除数字和特殊字符
        import re
        normalized = event.lower()
        normalized = re.sub(r'\d+', 'N', normalized)  # 数字替换为N
        normalized = re.sub(r'[^\w\s]', '', normalized)  # 移除特殊字符
        normalized = ' '.join(normalized.split())  # 规范化空白
        return normalized