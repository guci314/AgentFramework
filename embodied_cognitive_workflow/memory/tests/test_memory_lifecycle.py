"""
记忆生命周期管理测试
"""

import unittest
import tempfile
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path

from ..interfaces import MemoryLayer, Concept, TriggerType
from ..memory_manager import MemoryManager
from ..working_memory import WorkingMemory
from ..episodic_memory import EpisodicMemory
from ..semantic_memory import SemanticMemory
from ..memory_lifecycle import (
    MemoryLifecycleManager, LifecyclePolicy, LifecycleStage, LifecycleMetadata
)


class TestMemoryLifecycle(unittest.TestCase):
    """记忆生命周期测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.archive_path = Path(self.temp_dir) / "test_archive"
        
        # 创建记忆管理器
        self.memory_manager = MemoryManager(
            working_memory=WorkingMemory(),
            episodic_memory=EpisodicMemory(),
            semantic_memory=SemanticMemory()
        )
        
        # 创建生命周期策略（使用短时间以便测试）
        self.policy = LifecyclePolicy(
            active_duration=timedelta(seconds=1),
            archive_after=timedelta(seconds=2),
            compress_after=timedelta(seconds=3),
            forget_after=timedelta(seconds=4),
            min_access_for_active=2,
            min_importance_for_archive=0.3,
            archive_path=self.archive_path
        )
        
        # 创建生命周期管理器
        self.lifecycle_manager = MemoryLifecycleManager(
            self.memory_manager, 
            self.policy
        )
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_track_memory(self):
        """测试记忆跟踪"""
        # 创建记忆
        result = self.memory_manager.process_information(
            info="Test memory",
            source="test"
        )
        memory_id = result['ids']['working']
        
        # 跟踪记忆
        metadata = self.lifecycle_manager.track_memory(memory_id, MemoryLayer.WORKING)
        
        # 验证元数据
        self.assertEqual(metadata.stage, LifecycleStage.CREATED)
        self.assertEqual(metadata.access_count, 1)
        self.assertIsNotNone(metadata.created_at)
        self.assertEqual(len(metadata.stage_transitions), 1)
    
    def test_update_access(self):
        """测试访问更新"""
        # 创建并跟踪记忆
        result = self.memory_manager.process_information(
            info="Frequently accessed memory",
            source="test"
        )
        memory_id = result['ids']['working']
        self.lifecycle_manager.track_memory(memory_id, MemoryLayer.WORKING)
        
        # 更新访问
        for _ in range(3):
            success = self.lifecycle_manager.update_access(memory_id)
            self.assertTrue(success)
        
        # 验证状态转换
        metadata = self.lifecycle_manager.lifecycle_metadata[memory_id]
        self.assertEqual(metadata.access_count, 4)  # 初始1次 + 3次更新
        self.assertEqual(metadata.stage, LifecycleStage.ACTIVE)
    
    def test_lifecycle_transitions(self):
        """测试生命周期转换"""
        # 创建记忆
        result = self.memory_manager.process_information(
            info="Lifecycle test memory",
            source="test",
            metadata={"importance": 0.5}
        )
        memory_id = result['ids']['working']
        self.lifecycle_manager.track_memory(memory_id, MemoryLayer.WORKING)
        
        # 1. 转换到活跃
        self.lifecycle_manager.update_access(memory_id)
        self.lifecycle_manager.update_access(memory_id)
        
        transitions = self.lifecycle_manager.process_lifecycle()
        self.assertIn(memory_id, transitions['to_active'])
        
        # 2. 等待并转换到归档
        time.sleep(2.5)
        transitions = self.lifecycle_manager.process_lifecycle()
        self.assertIn(memory_id, transitions['to_archived'])
        
        # 验证归档文件
        archive_file = self.archive_path / "working" / f"{memory_id}.json"
        self.assertTrue(archive_file.exists())
        
        # 3. 等待并转换到压缩
        time.sleep(1.5)
        transitions = self.lifecycle_manager.process_lifecycle()
        self.assertIn(memory_id, transitions['to_compressed'])
        
        # 验证压缩文件
        compressed_file = self.archive_path / "working" / f"{memory_id}.json.gz"
        self.assertTrue(compressed_file.exists())
        self.assertFalse(archive_file.exists())  # 原文件应被删除
        
        # 4. 等待并转换到遗忘
        time.sleep(1.5)
        transitions = self.lifecycle_manager.process_lifecycle()
        self.assertIn(memory_id, transitions['to_forgotten'])
        
        # 验证记忆已被遗忘
        self.assertNotIn(memory_id, self.lifecycle_manager.lifecycle_metadata)
        self.assertFalse(compressed_file.exists())
    
    def test_archive_memory(self):
        """测试记忆归档"""
        # 创建不同重要性的记忆
        # 重要记忆
        important_result = self.memory_manager.process_information(
            info="Important memory",
            source="test",
            metadata={"importance": 0.8}
        )
        important_id = important_result['ids']['working']
        self.lifecycle_manager.track_memory(important_id, MemoryLayer.WORKING)
        
        # 不重要记忆
        unimportant_result = self.memory_manager.process_information(
            info="Unimportant memory",
            source="test",
            metadata={"importance": 0.1}
        )
        unimportant_id = unimportant_result['ids']['working']
        self.lifecycle_manager.track_memory(unimportant_id, MemoryLayer.WORKING)
        
        # 归档
        success1 = self.lifecycle_manager._archive_memory(important_id)
        success2 = self.lifecycle_manager._archive_memory(unimportant_id)
        
        self.assertTrue(success1)
        self.assertTrue(success2)
        
        # 验证重要记忆被归档
        important_metadata = self.lifecycle_manager.lifecycle_metadata.get(important_id)
        self.assertIsNotNone(important_metadata)
        self.assertEqual(important_metadata.stage, LifecycleStage.ARCHIVED)
        self.assertIsNotNone(important_metadata.archive_path)
        
        # 验证不重要记忆被遗忘
        unimportant_metadata = self.lifecycle_manager.lifecycle_metadata.get(unimportant_id)
        self.assertIsNone(unimportant_metadata)
    
    def test_restore_memory(self):
        """测试记忆恢复"""
        # 创建并归档记忆
        result = self.memory_manager.process_information(
            info="Memory to restore",
            source="test",
            metadata={"importance": 0.7}
        )
        memory_id = result['ids']['working']
        self.lifecycle_manager.track_memory(memory_id, MemoryLayer.WORKING)
        
        # 归档
        self.lifecycle_manager._archive_memory(memory_id)
        
        # 验证记忆已从活跃存储删除
        self.assertIsNone(self.memory_manager.working.get(memory_id))
        
        # 恢复记忆
        restored = self.lifecycle_manager.restore_memory(memory_id)
        
        # 验证恢复成功
        self.assertIsNotNone(restored)
        self.assertEqual(restored.id, memory_id)
        self.assertEqual(restored.content, "Memory to restore")
        
        # 验证记忆已恢复到活跃存储
        active_memory = self.memory_manager.working.get(memory_id)
        self.assertIsNotNone(active_memory)
        
        # 验证生命周期状态
        metadata = self.lifecycle_manager.lifecycle_metadata[memory_id]
        self.assertEqual(metadata.stage, LifecycleStage.ACTIVE)
        self.assertIsNone(metadata.archive_path)
    
    def test_compression(self):
        """测试压缩功能"""
        # 创建记忆
        result = self.memory_manager.process_information(
            info="Memory to compress " * 100,  # 创建较大内容以测试压缩
            source="test",
            metadata={"importance": 0.6}
        )
        memory_id = result['ids']['working']
        self.lifecycle_manager.track_memory(memory_id, MemoryLayer.WORKING)
        
        # 归档
        self.lifecycle_manager._archive_memory(memory_id)
        
        # 获取原始文件大小
        metadata = self.lifecycle_manager.lifecycle_metadata[memory_id]
        original_file = Path(metadata.archive_path)
        original_size = original_file.stat().st_size
        
        # 压缩
        success = self.lifecycle_manager._compress_memory(memory_id)
        self.assertTrue(success)
        
        # 验证压缩
        self.assertTrue(metadata.compressed)
        self.assertIsNotNone(metadata.compression_ratio)
        self.assertGreater(metadata.compression_ratio, 0)
        
        # 验证压缩文件
        compressed_file = Path(metadata.archive_path)
        self.assertTrue(compressed_file.suffix == '.gz')
        self.assertTrue(compressed_file.exists())
        self.assertLess(compressed_file.stat().st_size, original_size)
    
    def test_lifecycle_stats(self):
        """测试统计功能"""
        # 创建多个记忆并设置不同状态
        memory_ids = []
        
        for i in range(5):
            result = self.memory_manager.process_information(
                info=f"Test memory {i}",
                source="test"
            )
            memory_id = result['ids']['working']
            self.lifecycle_manager.track_memory(memory_id, MemoryLayer.WORKING)
            memory_ids.append(memory_id)
        
        # 设置不同状态
        # 保持一个在CREATED
        # 转换一个到ACTIVE
        self.lifecycle_manager.update_access(memory_ids[1])
        self.lifecycle_manager.update_access(memory_ids[1])
        
        # 归档一个
        self.lifecycle_manager._archive_memory(memory_ids[2])
        
        # 获取统计
        stats = self.lifecycle_manager.get_lifecycle_stats()
        
        # 验证统计
        self.assertEqual(stats['total_tracked'], 4)  # 5-1(归档时可能被遗忘)
        self.assertGreater(stats['average_access_count'], 1)
        self.assertIn('by_stage', stats)
        self.assertIn('compression_stats', stats)
    
    def test_cleanup_forgotten(self):
        """测试清理遗忘的归档"""
        # 创建一个归档文件（模拟遗忘的记忆）
        forgotten_file = self.archive_path / "working" / "forgotten_memory.json"
        forgotten_file.parent.mkdir(parents=True, exist_ok=True)
        forgotten_file.write_text('{"test": "data"}')
        
        # 修改文件时间为很久以前
        import os
        old_time = time.time() - (40 * 24 * 60 * 60)  # 40天前
        os.utime(forgotten_file, (old_time, old_time))
        
        # 执行清理
        cleaned = self.lifecycle_manager.cleanup_forgotten(days=30)
        
        # 验证清理
        self.assertEqual(cleaned, 1)
        self.assertFalse(forgotten_file.exists())
    
    def test_multiple_layers(self):
        """测试跨层记忆生命周期"""
        # 创建不同层的记忆
        # 工作记忆
        wm_result = self.memory_manager.process_information(
            info="Working memory item",
            source="test"
        )
        wm_id = wm_result['ids']['working']
        self.lifecycle_manager.track_memory(wm_id, MemoryLayer.WORKING)
        
        # 情景记忆
        ep_id = self.memory_manager.episodic.store_episode(
            event="Test episode",
            context={"test": True},
            project_id="test_project"
        )
        self.lifecycle_manager.track_memory(ep_id, MemoryLayer.EPISODIC)
        
        # 语义记忆
        concept = Concept(
            id="",
            name="Test Concept",
            category="test",
            attributes={},
            confidence=0.8
        )
        sm_id = self.memory_manager.semantic.add_concept(concept)
        self.lifecycle_manager.track_memory(sm_id, MemoryLayer.SEMANTIC)
        
        # 验证所有记忆都被跟踪
        self.assertEqual(len(self.lifecycle_manager.lifecycle_metadata), 3)
        
        # 归档所有记忆
        for memory_id in [wm_id, ep_id, sm_id]:
            self.lifecycle_manager._archive_memory(memory_id)
        
        # 验证归档文件在正确的子目录
        self.assertTrue((self.archive_path / "working" / f"{wm_id}.json").exists())
        self.assertTrue((self.archive_path / "episodic" / f"{ep_id}.json").exists())
        self.assertTrue((self.archive_path / "semantic" / f"{sm_id}.json").exists())


if __name__ == '__main__':
    unittest.main()