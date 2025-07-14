#!/usr/bin/env python
"""
记忆生命周期管理演示

展示记忆从创建到遗忘的完整流程
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from embodied_cognitive_workflow.memory import (
    MemoryManager, WorkingMemory, EpisodicMemory, SemanticMemory,
    TriggerType, MemoryLayer
)
from embodied_cognitive_workflow.memory.memory_lifecycle import (
    MemoryLifecycleManager, LifecyclePolicy, LifecycleStage
)


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'=' * 60}")
    print(f"{title:^60}")
    print('=' * 60)


def demonstrate_lifecycle():
    """演示记忆生命周期管理"""
    
    # 1. 创建记忆管理器
    print_section("1. 初始化记忆系统")
    
    memory_manager = MemoryManager(
        working_memory=WorkingMemory(),
        episodic_memory=EpisodicMemory(),
        semantic_memory=SemanticMemory()
    )
    
    # 创建生命周期策略（使用较短的时间以便演示）
    policy = LifecyclePolicy(
        active_duration=timedelta(seconds=5),
        archive_after=timedelta(seconds=10),
        compress_after=timedelta(seconds=15),
        forget_after=timedelta(seconds=20),
        min_access_for_active=2,
        min_importance_for_archive=0.3,
        archive_path=Path("./demo_archive")
    )
    
    lifecycle_manager = MemoryLifecycleManager(memory_manager, policy)
    print("✓ 记忆系统初始化完成")
    print(f"✓ 归档路径: {policy.archive_path}")
    
    # 2. 创建一些记忆
    print_section("2. 创建测试记忆")
    
    # 工作记忆
    wm_result = memory_manager.process_information(
        info="重要会议: 明天下午3点与客户讨论新项目",
        source="calendar",
        trigger_type=TriggerType.STATE_CHANGE,
        metadata={"importance": 0.5}  # 降低重要性以确保存储到工作记忆
    )
    wm_id = wm_result['ids'].get('working')
    if not wm_id:
        # 如果没有存储到工作记忆，可能直接存储到了情景记忆
        wm_id = wm_result['ids'].get('episodic')
        if wm_id:
            print(f"  注意: 记忆直接存储到情景记忆: {wm_id}")
    lifecycle_manager.track_memory(wm_id, MemoryLayer.WORKING)
    print(f"✓ 创建工作记忆: {wm_id}")
    
    # 情景记忆
    ep_id = memory_manager.episodic.store_episode(
        event="完成了用户认证模块的开发",
        context={"module": "auth", "duration": "3 days"},
        project_id="web_app"
    )
    lifecycle_manager.track_memory(ep_id, MemoryLayer.EPISODIC)
    print(f"✓ 创建情景记忆: {ep_id}")
    
    # 语义记忆
    from embodied_cognitive_workflow.memory.interfaces import Concept
    concept = Concept(
        id="",
        name="单例模式",
        category="design_pattern",
        attributes={"type": "creational", "usage": "ensure single instance"},
        confidence=0.9
    )
    sm_id = memory_manager.semantic.add_concept(concept)
    lifecycle_manager.track_memory(sm_id, MemoryLayer.SEMANTIC)
    print(f"✓ 创建语义记忆: {sm_id}")
    
    # 3. 模拟记忆访问
    print_section("3. 模拟记忆访问")
    
    # 访问记忆多次，使其变为活跃
    for i in range(3):
        # 尝试从工作记忆或情景记忆访问
        if memory_manager.working.exists(wm_id):
            memory_manager.working.get(wm_id)
        elif memory_manager.episodic.exists(wm_id):
            memory_manager.episodic.get(wm_id)
        lifecycle_manager.update_access(wm_id)
        print(f"  访问记忆 {i+1} 次")
        time.sleep(1)
    
    # 4. 处理生命周期（活跃阶段）
    print_section("4. 生命周期处理 - 活跃阶段")
    
    transitions = lifecycle_manager.process_lifecycle()
    print(f"✓ 转换到活跃: {transitions['to_active']}")
    
    # 显示当前状态
    stats = lifecycle_manager.get_lifecycle_stats()
    print(f"\n当前统计:")
    for stage, count in stats['by_stage'].items():
        if count > 0:
            print(f"  {stage}: {count}")
    
    # 5. 等待并处理归档
    print_section("5. 生命周期处理 - 归档阶段")
    print("等待记忆老化...")
    time.sleep(11)  # 等待超过归档阈值
    
    transitions = lifecycle_manager.process_lifecycle()
    print(f"✓ 转换到归档: {transitions['to_archived']}")
    
    # 检查归档文件
    archive_files = list(policy.archive_path.rglob("*.json"))
    print(f"✓ 归档文件数: {len(archive_files)}")
    for f in archive_files:
        print(f"  - {f.name}")
    
    # 6. 恢复归档的记忆
    print_section("6. 恢复归档记忆")
    
    # 尝试从原始存储获取（应该失败）
    original = None
    if memory_manager.working.exists(wm_id):
        original = memory_manager.working.get(wm_id)
    elif memory_manager.episodic.exists(wm_id):
        original = memory_manager.episodic.get(wm_id)
    print(f"原始存储中的记忆: {'不存在' if original is None else '存在'}")
    
    # 从归档恢复
    restored = lifecycle_manager.restore_memory(wm_id)
    if restored:
        print(f"✓ 成功恢复记忆: {restored.id}")
        print(f"  内容: {restored.content}")
        print(f"  访问次数: {restored.access_count}")
    
    # 7. 压缩阶段
    print_section("7. 生命周期处理 - 压缩阶段")
    
    # 重新归档以测试压缩
    lifecycle_manager._archive_memory(wm_id)
    print("等待压缩...")
    time.sleep(6)  # 等待超过压缩阈值
    
    transitions = lifecycle_manager.process_lifecycle()
    print(f"✓ 转换到压缩: {transitions['to_compressed']}")
    
    # 检查压缩文件
    compressed_files = list(policy.archive_path.rglob("*.gz"))
    print(f"✓ 压缩文件数: {len(compressed_files)}")
    
    # 显示压缩统计
    stats = lifecycle_manager.get_lifecycle_stats()
    comp_stats = stats['compression_stats']
    if comp_stats['total_compressed'] > 0:
        print(f"✓ 平均压缩率: {comp_stats['average_compression_ratio']:.2%}")
    
    # 8. 遗忘阶段
    print_section("8. 生命周期处理 - 遗忘阶段")
    
    print("等待遗忘...")
    time.sleep(6)  # 等待超过遗忘阈值
    
    transitions = lifecycle_manager.process_lifecycle()
    print(f"✓ 转换到遗忘: {transitions['to_forgotten']}")
    
    # 9. 最终统计
    print_section("9. 最终统计")
    
    final_stats = lifecycle_manager.get_lifecycle_stats()
    print(f"追踪的记忆总数: {final_stats['total_tracked']}")
    print(f"平均年龄: {final_stats['average_age']}")
    print(f"平均访问次数: {final_stats['average_access_count']:.1f}")
    
    print("\n各阶段分布:")
    for stage, count in final_stats['by_stage'].items():
        print(f"  {stage}: {count}")
    
    # 10. 清理演示文件
    print_section("10. 清理")
    
    cleaned = lifecycle_manager.cleanup_forgotten(days=0)
    print(f"✓ 清理了 {cleaned} 个遗忘的归档文件")
    
    # 删除演示目录
    import shutil
    if policy.archive_path.exists():
        shutil.rmtree(policy.archive_path)
        print(f"✓ 删除演示归档目录: {policy.archive_path}")


def demonstrate_batch_lifecycle():
    """演示批量记忆的生命周期管理"""
    
    print_section("批量记忆生命周期演示")
    
    # 创建记忆系统
    memory_manager = MemoryManager()
    
    # 使用更实际的策略
    policy = LifecyclePolicy(
        active_duration=timedelta(hours=1),
        archive_after=timedelta(days=7),
        compress_after=timedelta(days=30),
        forget_after=timedelta(days=90),
        archive_path=Path("./production_archive")
    )
    
    lifecycle_manager = MemoryLifecycleManager(memory_manager, policy)
    
    # 批量创建记忆
    print("\n创建100个测试记忆...")
    memory_ids = []
    
    for i in range(100):
        info = f"Test memory item {i}"
        result = memory_manager.process_information(
            info=info,
            source="batch_test",
            metadata={"batch_id": i // 10, "importance": i / 100}
        )
        
        # 跟踪所有创建的记忆
        for layer_name, memory_id in result['ids'].items():
            if memory_id:
                layer = MemoryLayer(layer_name)
                lifecycle_manager.track_memory(memory_id, layer)
                memory_ids.append((memory_id, layer))
    
    print(f"✓ 创建了 {len(memory_ids)} 个记忆")
    
    # 模拟不同的访问模式
    print("\n模拟访问模式...")
    import random
    
    # 20%的记忆被频繁访问
    frequently_accessed = random.sample(memory_ids[:20], 5)
    for memory_id, layer in frequently_accessed:
        for _ in range(5):
            lifecycle_manager.update_access(memory_id)
    
    # 处理生命周期
    print("\n处理生命周期...")
    transitions = lifecycle_manager.process_lifecycle()
    
    print(f"✓ 活跃记忆: {transitions['to_active']}")
    
    # 显示统计
    stats = lifecycle_manager.get_lifecycle_stats()
    print(f"\n生命周期统计:")
    print(f"  总记忆数: {stats['total_tracked']}")
    print(f"  平均访问: {stats['average_access_count']:.2f}")
    
    # 清理
    if policy.archive_path.exists():
        shutil.rmtree(policy.archive_path)
        print(f"\n✓ 清理完成")


if __name__ == "__main__":
    print("记忆生命周期管理演示")
    print("=" * 60)
    
    # 运行主要演示
    demonstrate_lifecycle()
    
    # 可选：运行批量演示
    # print("\n\n")
    # demonstrate_batch_lifecycle()