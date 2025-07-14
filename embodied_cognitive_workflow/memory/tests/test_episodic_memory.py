"""
情景记忆测试
"""

import unittest
from datetime import datetime, timedelta

from ..episodic_memory import EpisodicMemory
from ..interfaces import Episode


class TestEpisodicMemory(unittest.TestCase):
    """情景记忆测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.em = EpisodicMemory()
        self.project_id = "test_project"
    
    def test_store_episode(self):
        """测试存储情景"""
        # 存储情景
        episode_id = self.em.store_episode(
            event="User login successful",
            context={
                'user_id': 'user123',
                'ip_address': '192.168.1.1',
                'browser': 'Chrome'
            },
            project_id=self.project_id,
            participants=['user123', 'auth_service'],
            outcomes={'status': 'success', 'session_created': True}
        )
        
        self.assertIsNotNone(episode_id)
        
        # 验证存储
        item = self.em.get(episode_id)
        self.assertIsNotNone(item)
        self.assertEqual(item.content['event'], "User login successful")
    
    def test_query_timeline(self):
        """测试时间线查询"""
        now = datetime.now()
        
        # 存储多个情景
        for i in range(5):
            self.em.store_episode(
                event=f"Event {i}",
                context={'index': i},
                timestamp=now + timedelta(minutes=i),
                project_id=self.project_id
            )
        
        # 查询时间范围
        start = now - timedelta(minutes=1)
        end = now + timedelta(minutes=3)
        
        episodes = self.em.query_timeline(start, end)
        self.assertEqual(len(episodes), 4)  # 应该包含 0, 1, 2, 3
        
        # 验证时间顺序
        for i in range(len(episodes) - 1):
            self.assertLessEqual(episodes[i].timestamp, episodes[i+1].timestamp)
    
    def test_project_context(self):
        """测试项目上下文"""
        # 为项目存储多个情景
        episode_ids = []
        for i in range(3):
            eid = self.em.store_episode(
                event=f"Project event {i}",
                context={'phase': i},
                project_id=self.project_id,
                participants=['dev1', 'dev2'] if i == 0 else ['dev2', 'dev3']
            )
            episode_ids.append(eid)
        
        # 获取项目上下文
        context = self.em.get_project_context(self.project_id)
        
        self.assertEqual(context['project_id'], self.project_id)
        self.assertEqual(context['episodes_count'], 3)
        self.assertIn('dev1', context['participants'])
        self.assertIn('dev2', context['participants'])
        self.assertIn('dev3', context['participants'])
        self.assertEqual(len(context['timeline']), 3)
    
    def test_link_episodes(self):
        """测试情景关联"""
        # 创建两个情景
        ep1_id = self.em.store_episode(
            event="Task started",
            context={'task_id': 'task001'}
        )
        
        ep2_id = self.em.store_episode(
            event="Task completed",
            context={'task_id': 'task001', 'duration': '2 hours'}
        )
        
        # 建立关联
        success = self.em.link_episodes(ep1_id, ep2_id, "followed_by")
        self.assertTrue(success)
        
        # 获取相关情景
        related = self.em.get_related_episodes(ep1_id, "followed_by")
        self.assertEqual(len(related), 1)
        self.assertEqual(related[0].id, ep2_id)
        
        # 反向关系
        reverse_related = self.em.get_related_episodes(ep2_id, "reverse_followed_by")
        self.assertEqual(len(reverse_related), 1)
        self.assertEqual(reverse_related[0].id, ep1_id)
    
    def test_find_similar_episodes(self):
        """测试查找相似情景"""
        # 创建相似的情景
        base_id = self.em.store_episode(
            event="Database connection error",
            context={'error_code': 'DB001', 'retry_count': 3}
        )
        
        similar_ids = []
        for i in range(3):
            sid = self.em.store_episode(
                event="Database connection failed",
                context={'error_code': 'DB001', 'retry_count': i}
            )
            similar_ids.append(sid)
        
        # 查找相似情景
        similar = self.em.find_similar_episodes(base_id, limit=2)
        self.assertEqual(len(similar), 2)
        
        # 验证返回的是相似的情景
        for episode in similar:
            self.assertIn('database', episode.event.lower())
    
    def test_analyze_patterns(self):
        """测试模式分析"""
        # 创建重复模式
        for i in range(5):
            self.em.store_episode(
                event="API request timeout",
                context={'endpoint': '/api/data', 'timeout': 30},
                project_id=self.project_id
            )
        
        for i in range(3):
            self.em.store_episode(
                event="Cache miss occurred",
                context={'cache_key': 'user_data', 'miss_rate': 0.3},
                project_id=self.project_id
            )
        
        # 分析模式
        patterns = self.em.analyze_patterns(
            project_id=self.project_id,
            min_occurrences=3
        )
        
        self.assertGreater(len(patterns), 0)
        
        # 验证模式
        timeout_pattern = next(
            (p for p in patterns if 'timeout' in p['pattern'].lower()),
            None
        )
        self.assertIsNotNone(timeout_pattern)
        self.assertEqual(timeout_pattern['occurrences'], 5)
    
    def test_empty_timeline(self):
        """测试空时间线查询"""
        now = datetime.now()
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)
        
        episodes = self.em.query_timeline(start, end)
        self.assertEqual(len(episodes), 0)
    
    def test_project_filtering(self):
        """测试项目过滤"""
        # 为不同项目存储情景
        proj1_id = self.em.store_episode(
            event="Project 1 event",
            context={},
            project_id="project1"
        )
        
        proj2_id = self.em.store_episode(
            event="Project 2 event",
            context={},
            project_id="project2"
        )
        
        # 查询特定项目
        now = datetime.now()
        episodes = self.em.query_timeline(
            now - timedelta(hours=1),
            now + timedelta(hours=1),
            project_id="project1"
        )
        
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0].project_id, "project1")
    
    def test_complex_relationships(self):
        """测试复杂关系网络"""
        # 创建情景网络
        root_id = self.em.store_episode(
            event="System initialization",
            context={'version': '1.0'}
        )
        
        child_ids = []
        for i in range(3):
            child_id = self.em.store_episode(
                event=f"Subsystem {i} started",
                context={'subsystem_id': i}
            )
            child_ids.append(child_id)
            self.em.link_episodes(root_id, child_id, "triggers")
        
        # 验证关系
        triggered = self.em.get_related_episodes(root_id, "triggers")
        self.assertEqual(len(triggered), 3)
        
        # 获取所有相关情景
        all_related = self.em.get_related_episodes(root_id)
        self.assertEqual(len(all_related), 3)


if __name__ == '__main__':
    unittest.main()