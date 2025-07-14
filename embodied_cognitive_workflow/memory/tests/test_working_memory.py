"""
工作记忆测试
"""

import unittest
from datetime import datetime, timedelta
import time

from ..working_memory import WorkingMemory
from ..interfaces import TriggerType, MemoryItem


class TestWorkingMemory(unittest.TestCase):
    """工作记忆测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.wm = WorkingMemory(capacity=5, decay_threshold=timedelta(seconds=1))
    
    def test_capacity_limit(self):
        """测试容量限制"""
        # 添加超过容量的项
        for i in range(8):
            self.wm.add_with_trigger(
                f"Item {i}", 
                TriggerType.MANUAL,
                metadata={'index': i}
            )
        
        # 检查容量
        self.assertLessEqual(self.wm.size(), self.wm.capacity)
    
    def test_trigger_filtering(self):
        """测试触发器过滤"""
        # 添加错误信息
        error_id = self.wm.add_with_trigger(
            "System error occurred",
            TriggerType.ERROR
        )
        self.assertIsNotNone(error_id)
        
        # 添加普通信息（不应该被ERROR触发器记录）
        normal_id = self.wm.add_with_trigger(
            "Normal operation",
            TriggerType.ERROR
        )
        self.assertIsNone(normal_id)
        
        # 添加决策信息
        decision_id = self.wm.add_with_trigger(
            "Decided to use approach A",
            TriggerType.DECISION
        )
        self.assertIsNotNone(decision_id)
    
    def test_time_decay(self):
        """测试时间衰减"""
        # 添加一些项
        old_ids = []
        for i in range(3):
            mid = self.wm.add_with_trigger(
                f"Old item {i}",
                TriggerType.MANUAL,
                metadata={'age': 'old'}
            )
            old_ids.append(mid)
        
        # 等待超过衰减阈值
        time.sleep(1.5)
        
        # 添加新项
        new_id = self.wm.add_with_trigger(
            "New item",
            TriggerType.MANUAL,
            metadata={'age': 'new'}
        )
        
        # 执行衰减
        decayed_count = self.wm.decay()
        
        # 检查旧项被清理
        self.assertGreater(decayed_count, 0)
        
        # 检查新项还在
        self.assertIsNotNone(self.wm.get(new_id))
    
    def test_attention_weights(self):
        """测试注意力权重"""
        # 添加项
        item_id = self.wm.add_with_trigger(
            "Important item",
            TriggerType.MANUAL,
            metadata={'importance': 0.8}
        )
        
        # 获取初始权重
        weights = self.wm.get_attention_weights()
        self.assertIn(item_id, weights)
        
        # 更新权重
        success = self.wm.update_attention(item_id, 0.2)
        self.assertTrue(success)
        
        # 检查更新后的权重
        new_weights = self.wm.get_attention_weights()
        self.assertAlmostEqual(new_weights[item_id], 1.0)  # 0.8 + 0.2
    
    def test_eviction_strategy(self):
        """测试驱逐策略"""
        # 填满容量
        for i in range(self.wm.capacity):
            self.wm.add_with_trigger(
                f"Item {i}",
                TriggerType.MANUAL,
                metadata={'importance': 0.5}
            )
        
        # 添加高重要性项
        important_id = self.wm.add_with_trigger(
            "Very important item",
            TriggerType.MANUAL,
            metadata={'importance': 0.9}
        )
        
        # 确保高重要性项被保留
        self.assertIsNotNone(self.wm.get(important_id))
        self.assertEqual(self.wm.size(), self.wm.capacity)
    
    def test_consolidate(self):
        """测试记忆整合"""
        # 添加多种类型的事件
        self.wm.add_with_trigger("Error in module A", TriggerType.ERROR)
        self.wm.add_with_trigger("Decided to retry", TriggerType.DECISION)
        self.wm.add_with_trigger("State changed to active", TriggerType.STATE_CHANGE)
        
        # 整合记忆
        consolidated = self.wm.consolidate()
        
        # 验证整合结果
        self.assertIn('events', consolidated)
        self.assertIn('summary', consolidated)
        self.assertEqual(len(consolidated['events']), 3)
        self.assertEqual(consolidated['summary']['total_errors'], 1)
        self.assertEqual(consolidated['summary']['total_decisions'], 1)
    
    def test_active_memories(self):
        """测试活跃记忆队列"""
        # 添加项
        ids = []
        for i in range(3):
            mid = self.wm.add_with_trigger(
                f"Item {i}",
                TriggerType.MANUAL
            )
            ids.append(mid)
        
        # 获取活跃记忆
        active = self.wm.get_active_memories()
        self.assertEqual(len(active), 3)
        
        # 访问中间的项
        self.wm.get(ids[1])
        
        # 再次获取活跃记忆，确保顺序更新
        active_after = self.wm.get_active_memories()
        self.assertEqual(active_after[-1].id, ids[1])
    
    def test_set_capacity(self):
        """测试动态设置容量"""
        # 添加5个项
        for i in range(5):
            self.wm.add_with_trigger(f"Item {i}", TriggerType.MANUAL)
        
        self.assertEqual(self.wm.size(), 5)
        
        # 减少容量
        self.wm.set_capacity(3)
        self.assertEqual(self.wm.capacity, 3)
        self.assertLessEqual(self.wm.size(), 3)
        
        # 增加容量
        self.wm.set_capacity(7)
        self.assertEqual(self.wm.capacity, 7)
        
        # 添加更多项
        for i in range(5, 8):
            self.wm.add_with_trigger(f"Item {i}", TriggerType.MANUAL)
        
        self.assertLessEqual(self.wm.size(), 7)
    
    def test_milestone_trigger(self):
        """测试里程碑触发器"""
        # 添加里程碑
        milestone_id = self.wm.add_with_trigger(
            "Project phase 1 completed",
            TriggerType.MILESTONE,
            metadata={'milestone': True, 'phase': 1}
        )
        
        self.assertIsNotNone(milestone_id)
        
        # 验证元数据
        item = self.wm.get(milestone_id)
        self.assertEqual(item.metadata['trigger_type'], TriggerType.MILESTONE.value)
        self.assertTrue(item.metadata['milestone'])


if __name__ == '__main__':
    unittest.main()