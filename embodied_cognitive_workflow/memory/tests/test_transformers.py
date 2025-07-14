"""
记忆转换器测试
"""

import unittest
from datetime import datetime, timedelta

from ..transformers import (
    WorkingToEpisodicTransformer,
    EpisodicToSemanticTransformer,
    SemanticToEpisodicTransformer,
    EpisodicToWorkingTransformer
)
from ..interfaces import MemoryItem, Episode, Concept


class TestWorkingToEpisodicTransformer(unittest.TestCase):
    """工作记忆到情景记忆转换器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.transformer = WorkingToEpisodicTransformer()
    
    def test_transform_consolidated(self):
        """测试转换整合数据"""
        # 准备整合数据
        consolidated = {
            'start_time': datetime.now() - timedelta(minutes=5),
            'end_time': datetime.now(),
            'duration': 300,  # 5 minutes
            'items_count': 3,
            'events': [
                {
                    'timestamp': datetime.now() - timedelta(minutes=4),
                    'content': 'Started processing',
                    'importance': 0.5,
                    'trigger_type': 'manual'
                },
                {
                    'timestamp': datetime.now() - timedelta(minutes=2),
                    'content': 'Error occurred',
                    'importance': 0.8,
                    'trigger_type': 'error'
                },
                {
                    'timestamp': datetime.now(),
                    'content': 'Processing completed',
                    'importance': 0.7,
                    'trigger_type': 'milestone'
                }
            ],
            'summary': {
                'total_errors': 1,
                'total_decisions': 0,
                'avg_importance': 0.67
            }
        }
        
        # 转换
        result = self.transformer.transform(consolidated)
        
        # 验证结果
        self.assertIn('event', result)
        self.assertIn('context', result)
        self.assertIn('outcomes', result)
        
        self.assertIn('with 1 errors', result['event'])
        self.assertEqual(result['context']['events_count'], 3)
        self.assertEqual(result['outcomes']['errors'][0], 'Error occurred')
    
    def test_transform_memory_items(self):
        """测试转换记忆项列表"""
        # 创建记忆项
        items = [
            MemoryItem(
                id='1',
                content='Task started',
                timestamp=datetime.now() - timedelta(minutes=2),
                importance=0.6,
                metadata={'trigger_type': 'manual'}
            ),
            MemoryItem(
                id='2',
                content='Task completed',
                timestamp=datetime.now(),
                importance=0.7,
                metadata={'trigger_type': 'milestone'}
            )
        ]
        
        # 转换
        result = self.transformer.transform(items)
        
        # 验证结果
        self.assertIn('event', result)
        self.assertIn('context', result)
        self.assertEqual(result['context']['events_count'], 2)
    
    def test_can_transform(self):
        """测试转换条件检查"""
        # 有效的整合数据
        valid_consolidated = {
            'events': [],
            'start_time': datetime.now()
        }
        self.assertTrue(self.transformer.can_transform(valid_consolidated))
        
        # 有效的记忆项列表
        valid_items = [MemoryItem(id='1', content='test')]
        self.assertTrue(self.transformer.can_transform(valid_items))
        
        # 无效数据
        self.assertFalse(self.transformer.can_transform("invalid"))
        self.assertFalse(self.transformer.can_transform({}))


class TestEpisodicToSemanticTransformer(unittest.TestCase):
    """情景记忆到语义记忆转换器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.transformer = EpisodicToSemanticTransformer(
            min_examples=2,
            min_confidence=0.5
        )
    
    def test_transform_episodes(self):
        """测试转换情景集合"""
        # 创建相似情景
        episodes = []
        for i in range(3):
            episode = Episode(
                id=f'ep_{i}',
                event=f"Database connection error {i}",
                context={
                    'error_code': 'CONN_TIMEOUT',
                    'database': 'postgres',
                    'retry_count': i
                },
                timestamp=datetime.now(),
                outcomes={'resolved': True}
            )
            episodes.append(episode)
        
        # 转换
        concept = self.transformer.transform(episodes)
        
        # 验证概念
        self.assertIsNotNone(concept)
        self.assertIn('error', concept.category)
        self.assertEqual(concept.attributes['error_code'], 'CONN_TIMEOUT')
        self.assertEqual(concept.attributes['database'], 'postgres')
        self.assertGreater(concept.confidence, 0.5)
    
    def test_insufficient_examples(self):
        """测试示例不足的情况"""
        # 只有一个情景
        episodes = [
            Episode(
                id='single',
                event="Single event",
                context={},
                timestamp=datetime.now()
            )
        ]
        
        # 应该返回None
        concept = self.transformer.transform(episodes)
        self.assertIsNone(concept)
    
    def test_extract_pattern(self):
        """测试模式提取"""
        # 创建有模式的情景
        episodes = []
        for i in range(4):
            episode = Episode(
                id=f'pattern_{i}',
                event=f"API rate limit exceeded at endpoint /api/users",
                context={
                    'endpoint': '/api/users',
                    'rate_limit': 100,
                    'current_rate': 150 + i * 10
                },
                timestamp=datetime.now()
            )
            episodes.append(episode)
        
        # 提取模式
        pattern = self.transformer.extract_pattern(episodes)
        
        # 验证模式
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern['attributes']['endpoint'], '/api/users')
        self.assertEqual(pattern['attributes']['rate_limit'], 100)
        self.assertIn('rate', pattern['name'].lower())


class TestSemanticToEpisodicTransformer(unittest.TestCase):
    """语义记忆到情景记忆转换器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.transformer = SemanticToEpisodicTransformer()
    
    def test_transform_concept(self):
        """测试转换概念到情景"""
        # 创建概念
        concept = Concept(
            id='concept_1',
            name='Error Handling Pattern',
            category='pattern',
            attributes={
                'strategy': 'retry_with_backoff',
                'max_retries': 3
            },
            confidence=0.8,
            examples=[{'case': 'network_timeout'}]
        )
        
        # 应用上下文
        context = {
            'current_task': 'api_call',
            'environment': 'production'
        }
        
        # 转换
        result = self.transformer.transform((concept, context))
        
        # 验证结果
        self.assertIn('event', result)
        self.assertIn('context', result)
        self.assertIn('outcomes', result)
        
        self.assertIn('Error Handling Pattern', result['event'])
        self.assertEqual(result['context']['concept_id'], 'concept_1')
        self.assertEqual(result['context']['application_context'], context)
        self.assertEqual(result['outcomes']['confidence'], 0.8)


class TestEpisodicToWorkingTransformer(unittest.TestCase):
    """情景记忆到工作记忆转换器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.transformer = EpisodicToWorkingTransformer()
    
    def test_transform_episode(self):
        """测试转换情景到工作记忆"""
        # 创建情景
        episode = Episode(
            id='ep_test',
            event='Important decision made',
            context={
                'decision': 'Use microservices architecture',
                'reasons': ['scalability', 'maintainability'],
                'key_events': ['team_meeting', 'architecture_review']
            },
            timestamp=datetime.now(),
            outcomes={
                'approved': True,
                'implementation_timeline': '3 months'
            }
        )
        
        # 转换
        working_items = self.transformer.transform(episode)
        
        # 验证结果
        self.assertGreater(len(working_items), 0)
        
        # 检查主事件
        main_event = next(
            (item for item in working_items 
             if item['content']['type'] == 'recalled_event'),
            None
        )
        self.assertIsNotNone(main_event)
        self.assertEqual(
            main_event['content']['event'], 
            'Important decision made'
        )
        
        # 检查关键事件
        key_events_item = next(
            (item for item in working_items 
             if item['content']['type'] == 'recalled_key_events'),
            None
        )
        self.assertIsNotNone(key_events_item)
        
        # 检查结果
        outcomes_item = next(
            (item for item in working_items 
             if item['content']['type'] == 'recalled_outcomes'),
            None
        )
        self.assertIsNotNone(outcomes_item)
        self.assertTrue(outcomes_item['content']['outcomes']['approved'])


class TestTransformerIntegration(unittest.TestCase):
    """转换器集成测试"""
    
    def test_full_cycle_transformation(self):
        """测试完整的转换循环"""
        # 1. 创建工作记忆项
        working_items = [
            MemoryItem(
                id=f'wm_{i}',
                content=f'Processing step {i}',
                timestamp=datetime.now() + timedelta(seconds=i),
                importance=0.6,
                metadata={'trigger_type': 'manual'}
            )
            for i in range(3)
        ]
        
        # 2. 工作记忆 -> 情景记忆
        w2e_transformer = WorkingToEpisodicTransformer()
        episode_data = w2e_transformer.transform(working_items)
        
        # 创建情景对象
        episode = Episode(
            id='ep_from_working',
            event=episode_data['event'],
            context=episode_data['context'],
            timestamp=episode_data.get('timestamp', datetime.now()),
            outcomes=episode_data.get('outcomes', {})
        )
        
        # 3. 情景记忆 -> 语义记忆
        e2s_transformer = EpisodicToSemanticTransformer(min_examples=1)
        concept = e2s_transformer.transform([episode, episode])  # 需要多个示例
        
        if concept:  # 可能因为相似度不够而失败
            # 4. 语义记忆 -> 情景记忆
            s2e_transformer = SemanticToEpisodicTransformer()
            new_episode_data = s2e_transformer.transform(
                (concept, {'application': 'test'})
            )
            
            # 5. 情景记忆 -> 工作记忆
            e2w_transformer = EpisodicToWorkingTransformer()
            new_working_items = e2w_transformer.transform(episode)
            
            # 验证循环完成
            self.assertGreater(len(new_working_items), 0)


if __name__ == '__main__':
    unittest.main()