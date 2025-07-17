#!/usr/bin/env python
"""
测试记忆生命周期管理
"""

import sys
sys.path.insert(0, '.')

import unittest
import tempfile
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path

from embodied_cognitive_workflow.memory import (
    MemoryManager, WorkingMemory, EpisodicMemory, SemanticMemory,
    MemoryLifecycleManager, LifecyclePolicy, LifecycleStage,
    TriggerType, MemoryLayer, Concept
)


class TestLifecycleBasic(unittest.TestCase):
    """基础生命周期测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.archive_path = Path(self.temp_dir) / "test_archive"
        
        # 创建记忆管理器
        self.memory_manager = MemoryManager(
            working_memory=WorkingMemory(),
            episodic_memory=EpisodicMemory(),
            semantic_memory=SemanticMemory()
        )
        
        # 创建快速策略
        self.policy = LifecyclePolicy(
            active_duration=timedelta(seconds=0.5),
            archive_after=timedelta(seconds=1),
            compress_after=timedelta(seconds=1.5),
            forget_after=timedelta(seconds=2),
            min_access_for_active=2,
            archive_path=self.archive_path
        )
        
        self.lifecycle = MemoryLifecycleManager(self.memory_manager, self.policy)
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_basic_lifecycle(self):
        """测试基本生命周期流程"""
        print("\n测试基本生命周期流程")
        
        # 创建记忆
        result = self.memory_manager.process_information(
            info="Test memory for lifecycle",
            source="test",
            metadata={"importance": 0.5}
        )
        
        memory_id = result['ids'].get('working')
        self.assertIsNotNone(memory_id, "应该创建工作记忆")
        
        # 跟踪记忆
        metadata = self.lifecycle.track_memory(memory_id, MemoryLayer.WORKING)
        self.assertEqual(metadata.stage, LifecycleStage.CREATED)
        print(f"✓ 记忆创建: {memory_id}")
        
        # 多次访问使其活跃
        for _ in range(2):
            self.lifecycle.update_access(memory_id)
        
        # 检查当前状态
        current_metadata = self.lifecycle.lifecycle_metadata[memory_id]
        print(f"  当前状态: {current_metadata.stage.value}, 访问次数: {current_metadata.access_count}")
        
        # 处理生命周期
        transitions = self.lifecycle.process_lifecycle()
        print(f"  转换结果: {transitions}")
        
        # 状态可能已经在update_access中转换了
        if current_metadata.stage == LifecycleStage.ACTIVE:
            print(f"✓ 记忆已激活: {memory_id}")
        else:
            self.assertIn(memory_id, transitions['to_active'])
        print(f"✓ 记忆激活: {memory_id}")
        
        # 等待并归档
        time.sleep(1.1)
        transitions = self.lifecycle.process_lifecycle()
        self.assertIn(memory_id, transitions['to_archived'])
        print(f"✓ 记忆归档: {memory_id}")
        
        # 验证归档文件
        archive_file = self.archive_path / "working" / f"{memory_id}.json"
        self.assertTrue(archive_file.exists())
        print(f"✓ 归档文件存在: {archive_file.name}")
        
        # 恢复记忆
        restored = self.lifecycle.restore_memory(memory_id)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.id, memory_id)
        print(f"✓ 记忆恢复成功")
        
        # 获取统计
        stats = self.lifecycle.get_lifecycle_stats()
        print(f"\n生命周期统计:")
        print(f"  总记忆数: {stats['total_tracked']}")
        print(f"  各阶段: {stats['by_stage']}")
        
        return True


if __name__ == "__main__":
    # 运行测试
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLifecycleBasic)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 显示结果
    print(f"\n测试结果: {'通过' if result.wasSuccessful() else '失败'}")
    print(f"运行: {result.testsRun}, 失败: {len(result.failures)}, 错误: {len(result.errors)}")