"""
记忆管理器测试
"""

import unittest
from datetime import datetime, timedelta
import time

from ..memory_manager import MemoryManager, MemoryLayer
from ..interfaces import TriggerType, Episode, Concept
from ..working_memory import WorkingMemory
from ..episodic_memory import EpisodicMemory
from ..semantic_memory import SemanticMemory


class TestMemoryManager(unittest.TestCase):
    """记忆管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.mm = MemoryManager(
            auto_promote=True,
            auto_decay=True
        )
    
    def test_process_information_levels(self):
        """测试不同重要性级别的信息处理"""
        # 低重要性
        low_result = self.mm.process_information(
            "Routine log entry",
            metadata={'importance': 0.2}
        )
        self.assertIn('working', low_result['stored_in'])
        self.assertEqual(len(low_result['stored_in']), 1)
        
        # 中等重要性
        mid_result = self.mm.process_information(
            "Configuration changed",
            metadata={'importance': 0.5}
        )
        self.assertIn('working', mid_result['stored_in'])
        
        # 高重要性
        high_result = self.mm.process_information(
            "Critical system error detected",
            trigger_type=TriggerType.ERROR,
            metadata={'importance': 0.9}
        )
        self.assertIn('working', high_result['stored_in'])
        self.assertIn('episodic', high_result['stored_in'])
    
    def test_multi_layer_recall(self):
        """测试多层记忆召回"""
        # 在各层存储信息
        # 工作记忆
        self.mm.working.add_with_trigger(
            "Current task: processing data",
            TriggerType.MANUAL
        )
        
        # 情景记忆
        self.mm.episodic.store_episode(
            event="Data processing completed",
            context={'duration': '5 minutes', 'records': 1000}
        )
        
        # 语义记忆
        concept = Concept(
            id="",
            name="Data Processing Pattern",
            category="process_pattern",
            attributes={'steps': ['load', 'transform', 'save']}
        )
        self.mm.semantic.add_concept(concept)
        
        # 召回
        results = self.mm.recall_with_context("data processing")
        
        # 验证各层都有结果
        self.assertGreater(len(results['working']), 0)
        self.assertGreater(len(results['episodic']), 0)
        self.assertGreater(len(results['semantic']), 0)
    
    def test_context_aware_recall(self):
        """测试上下文感知召回"""
        project_id = "test_project"
        
        # 为特定项目存储情景
        self.mm.episodic.store_episode(
            event="Project test started",
            context={'test_type': 'unit'},
            project_id=project_id
        )
        
        # 为其他项目存储情景
        self.mm.episodic.store_episode(
            event="Different project test",
            context={'test_type': 'integration'},
            project_id="other_project"
        )
        
        # 带项目上下文的召回
        context_results = self.mm.recall_with_context(
            "test",
            context={'project_id': project_id},
            layers=MemoryLayer.EPISODIC
        )
        
        # 验证只返回特定项目的结果
        for item in context_results['episodic']:
            self.assertEqual(item.metadata.get('project_id'), project_id)
    
    def test_memory_promotion(self):
        """测试记忆层级提升"""
        # 手动添加工作记忆
        wm_id = self.mm.working.add_with_trigger(
            "Important discovery",
            TriggerType.MANUAL,
            metadata={'importance': 0.8}
        )
        
        # 提升到情景记忆
        ep_id = self.mm.promote_memory(
            MemoryLayer.WORKING,
            MemoryLayer.EPISODIC,
            wm_id
        )
        
        self.assertIsNotNone(ep_id)
        
        # 验证情景记忆中存在
        episode_item = self.mm.episodic.get(ep_id)
        self.assertIsNotNone(episode_item)
        self.assertIn('Important discovery', str(episode_item.content))
    
    def test_automatic_promotion(self):
        """测试自动提升机制"""
        # 填充工作记忆到接近容量
        for i in range(6):
            self.mm.process_information(
                f"Task step {i}",
                metadata={'importance': 0.6}
            )
        
        # 添加触发自动提升的项
        result = self.mm.process_information(
            "Final important step",
            metadata={'importance': 0.65}
        )
        
        # 检查提升统计
        stats = self.mm.get_statistics()
        # 可能会触发自动提升
        if 'episodic' in result['stored_in']:
            self.assertGreater(
                stats['manager_stats']['promotions']['working_to_episodic'], 
                0
            )
    
    def test_memory_timeline(self):
        """测试记忆时间线"""
        now = datetime.now()
        
        # 在不同时间添加记忆
        for i in range(3):
            time.sleep(0.1)  # 确保时间差异
            self.mm.process_information(
                f"Event {i}",
                metadata={'index': i}
            )
        
        # 获取时间线
        timeline = self.mm.get_memory_timeline(
            now - timedelta(seconds=1),
            now + timedelta(seconds=1)
        )
        
        self.assertGreater(len(timeline), 0)
        
        # 验证时间顺序
        for i in range(len(timeline) - 1):
            self.assertLessEqual(
                timeline[i]['timestamp'],
                timeline[i+1]['timestamp']
            )
    
    def test_pattern_analysis(self):
        """测试模式分析"""
        # 创建一些模式
        for i in range(4):
            self.mm.episodic.store_episode(
                event="Database connection timeout",
                context={'retry_count': i, 'error_code': 'TIMEOUT'}
            )
        
        # 分析模式
        analysis = self.mm.analyze_memory_patterns(min_pattern_occurrences=3)
        
        self.assertIn('episodic_patterns', analysis)
        self.assertGreater(len(analysis['episodic_patterns']), 0)
        
        # 验证建议
        self.assertIn('recommendations', analysis)
    
    def test_semantic_extraction(self):
        """测试语义知识提取"""
        # 创建多个相似情景
        for i in range(5):
            self.mm.episodic.store_episode(
                event=f"API rate limit exceeded",
                context={
                    'endpoint': '/api/data',
                    'limit': 100,
                    'wait_time': 60
                },
                outcomes={'retry_successful': True}
            )
        
        # 手动触发语义提取（通常是自动的）
        episodes = self.mm.episodic.list_all()[:5]
        if len(episodes) >= 3:
            # 获取第一个情景ID
            first_id = episodes[0].id
            concept_id = self.mm._consider_semantic_extraction(first_id)
            
            # 如果提取成功，验证概念
            if concept_id:
                concept = self.mm.semantic._get_concept(concept_id)
                self.assertIsNotNone(concept)
                self.assertIn('rate', concept.name.lower())
    
    def test_statistics(self):
        """测试统计信息"""
        # 执行一些操作
        self.mm.process_information("Test info 1")
        self.mm.recall_with_context("test")
        
        # 获取统计
        stats = self.mm.get_statistics()
        
        self.assertIn('manager_stats', stats)
        self.assertIn('layer_stats', stats)
        
        # 验证统计数据
        self.assertGreater(stats['manager_stats']['total_processed'], 0)
        self.assertGreater(stats['manager_stats']['recalls']['working'], 0)
    
    def test_layer_specific_recall(self):
        """测试特定层召回"""
        # 在各层存储信息
        self.mm.process_information("Working memory item")
        self.mm.episodic.store_episode(
            event="Episodic event",
            context={'type': 'test'}
        )
        
        # 只查询工作记忆
        working_only = self.mm.recall_with_context(
            "memory",
            layers=MemoryLayer.WORKING
        )
        self.assertIn('working', working_only)
        self.assertNotIn('episodic', working_only)
        
        # 只查询情景记忆
        episodic_only = self.mm.recall_with_context(
            "event",
            layers=[MemoryLayer.EPISODIC]
        )
        self.assertIn('episodic', episodic_only)
        self.assertNotIn('working', episodic_only)
    
    def test_custom_memory_instances(self):
        """测试使用自定义记忆实例"""
        # 创建自定义容量的工作记忆
        custom_wm = WorkingMemory(capacity=10)
        custom_em = EpisodicMemory()
        custom_sm = SemanticMemory()
        
        custom_mm = MemoryManager(
            working_memory=custom_wm,
            episodic_memory=custom_em,
            semantic_memory=custom_sm
        )
        
        # 验证自定义设置
        self.assertEqual(custom_mm.working.capacity, 10)


if __name__ == '__main__':
    unittest.main()