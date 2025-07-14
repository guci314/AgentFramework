"""
记忆管理系统演示

展示如何使用三层记忆架构
"""

from datetime import datetime, timedelta
import time

from memory_manager import MemoryManager, MemoryLayer
from interfaces import TriggerType, Concept, Episode
from working_memory import WorkingMemory
from episodic_memory import EpisodicMemory
from semantic_memory import SemanticMemory


def demo_basic_usage():
    """基础使用演示"""
    print("=== 记忆管理系统基础演示 ===\n")
    
    # 创建记忆管理器
    mm = MemoryManager()
    
    # 1. 处理不同重要性的信息
    print("1. 处理不同重要性的信息:")
    
    # 低重要性
    result1 = mm.process_information(
        "Starting routine check",
        metadata={'importance': 0.2}
    )
    print(f"   低重要性信息存储在: {result1['stored_in']}")
    
    # 中等重要性
    result2 = mm.process_information(
        "Configuration updated successfully",
        metadata={'importance': 0.5}
    )
    print(f"   中等重要性信息存储在: {result2['stored_in']}")
    
    # 高重要性
    result3 = mm.process_information(
        "Critical security vulnerability detected",
        trigger_type=TriggerType.ERROR,
        metadata={'importance': 0.9, 'severity': 'critical'}
    )
    print(f"   高重要性信息存储在: {result3['stored_in']}")
    
    # 2. 多层召回
    print("\n2. 多层记忆召回:")
    results = mm.recall_with_context("security", limit=5)
    
    for layer, items in results.items():
        if items:
            print(f"   {layer}层找到 {len(items)} 条记忆")
            for item in items[:2]:  # 只显示前2条
                print(f"     - {str(item.content)[:50]}...")
    
    # 3. 获取统计信息
    print("\n3. 记忆系统统计:")
    stats = mm.get_statistics()
    print(f"   总处理信息: {stats['manager_stats']['total_processed']}")
    print(f"   工作记忆项: {stats['layer_stats']['working']['total_items']}")
    print(f"   情景记忆项: {stats['layer_stats']['episodic']['total_episodes']}")
    print(f"   语义概念数: {stats['layer_stats']['semantic']['total_concepts']}")


def demo_working_memory():
    """工作记忆演示"""
    print("\n=== 工作记忆演示 ===\n")
    
    wm = WorkingMemory(capacity=5, decay_threshold=timedelta(seconds=2))
    
    # 1. 触发器驱动的记录
    print("1. 触发器驱动的记录:")
    
    # 错误触发
    error_id = wm.add_with_trigger(
        "Database connection failed",
        TriggerType.ERROR
    )
    print(f"   错误信息已记录: {error_id}")
    
    # 决策触发
    decision_id = wm.add_with_trigger(
        "Decided to use caching strategy",
        TriggerType.DECISION
    )
    print(f"   决策信息已记录: {decision_id}")
    
    # 2. 容量管理
    print("\n2. 容量管理演示:")
    for i in range(6):
        wm.add_with_trigger(f"Task {i}", TriggerType.MANUAL)
    
    print(f"   添加6个项后，当前容量: {wm.size()}/{wm.capacity}")
    
    # 3. 时间衰减
    print("\n3. 时间衰减演示:")
    print("   等待2秒...")
    time.sleep(2.5)
    
    decayed = wm.decay()
    print(f"   衰减了 {decayed} 个过期项")
    print(f"   当前容量: {wm.size()}/{wm.capacity}")
    
    # 4. 记忆整合
    print("\n4. 记忆整合:")
    consolidated = wm.consolidate()
    if consolidated.get('events'):
        print(f"   整合了 {len(consolidated['events'])} 个事件")
        print(f"   总持续时间: {consolidated['duration']:.1f} 秒")


def demo_episodic_memory():
    """情景记忆演示"""
    print("\n=== 情景记忆演示 ===\n")
    
    em = EpisodicMemory()
    project_id = "demo_project"
    
    # 1. 存储项目相关情景
    print("1. 存储项目情景:")
    
    episode_ids = []
    events = [
        ("Project kickoff meeting", {'attendees': 5, 'duration': '2 hours'}),
        ("Requirements analysis completed", {'requirements': 25, 'priority': 'high'}),
        ("Development phase started", {'team_size': 3, 'sprint': 1}),
        ("First milestone achieved", {'features': 10, 'bugs_fixed': 5})
    ]
    
    for event, context in events:
        eid = em.store_episode(
            event=event,
            context=context,
            project_id=project_id,
            participants=['dev_team', 'pm']
        )
        episode_ids.append(eid)
        print(f"   存储情景: {event}")
    
    # 2. 建立情景关系
    print("\n2. 建立情景关系:")
    for i in range(len(episode_ids) - 1):
        em.link_episodes(episode_ids[i], episode_ids[i+1], "followed_by")
    print("   已建立时序关系")
    
    # 3. 获取项目上下文
    print("\n3. 项目上下文:")
    context = em.get_project_context(project_id)
    print(f"   项目情景数: {context['episodes_count']}")
    print(f"   参与者: {', '.join(context['participants'])}")
    print(f"   时间跨度: {context['duration']:.1f} 秒")
    
    # 4. 分析模式
    print("\n4. 模式分析:")
    # 添加重复模式
    for i in range(3):
        em.store_episode(
            event="Code review session",
            context={'review_type': 'peer', 'issues_found': i},
            project_id=project_id
        )
    
    patterns = em.analyze_patterns(project_id=project_id, min_occurrences=3)
    if patterns:
        print(f"   发现 {len(patterns)} 个模式")
        for pattern in patterns[:2]:
            print(f"   - {pattern['type']}: {pattern['pattern']} (出现{pattern['occurrences']}次)")


def demo_semantic_memory():
    """语义记忆演示"""
    print("\n=== 语义记忆演示 ===\n")
    
    sm = SemanticMemory()
    
    # 1. 添加概念
    print("1. 添加设计模式概念:")
    
    patterns = [
        Concept(
            id="",
            name="Singleton Pattern",
            category="design_pattern",
            attributes={
                'intent': 'Ensure a class has only one instance',
                'applicability': 'When exactly one instance is needed',
                'structure': 'Private constructor, static instance'
            },
            confidence=0.9,
            domain="software_design"
        ),
        Concept(
            id="",
            name="Observer Pattern",
            category="design_pattern",
            attributes={
                'intent': 'Define one-to-many dependency between objects',
                'applicability': 'When change in one object requires change in dependents',
                'structure': 'Subject-Observer interface'
            },
            confidence=0.85,
            domain="software_design"
        )
    ]
    
    concept_ids = []
    for concept in patterns:
        cid = sm.add_concept(concept)
        concept_ids.append(cid)
        print(f"   添加概念: {concept.name}")
    
    # 2. 查找模式
    print("\n2. 查找领域模式:")
    found = sm.find_patterns("software_design", min_confidence=0.8)
    print(f"   找到 {len(found)} 个高置信度模式")
    
    # 3. 构建知识图谱
    print("\n3. 知识图谱:")
    # 添加关系
    root = Concept(
        id="",
        name="Design Patterns",
        category="knowledge_domain",
        attributes={'description': 'Reusable solutions to common problems'},
        relationships={'includes': concept_ids}
    )
    root_id = sm.add_concept(root)
    
    graph = sm.get_knowledge_graph(root_id, depth=2)
    print(f"   节点数: {len(graph['nodes'])}")
    print(f"   边数: {len(graph['edges'])}")


def demo_memory_transformation():
    """记忆转换演示"""
    print("\n=== 记忆转换演示 ===\n")
    
    mm = MemoryManager()
    
    # 1. 模拟工作流程
    print("1. 模拟开发工作流程:")
    
    # 工作记忆阶段
    for i in range(5):
        mm.process_information(
            f"Implementing feature {i}",
            trigger_type=TriggerType.STATE_CHANGE,
            metadata={'importance': 0.6, 'feature_id': f'F{i}'}
        )
    
    # 遇到错误
    mm.process_information(
        "Null pointer exception in module X",
        trigger_type=TriggerType.ERROR,
        metadata={'importance': 0.8, 'error_type': 'runtime'}
    )
    
    # 做出决策
    mm.process_information(
        "Decided to refactor module X",
        trigger_type=TriggerType.DECISION,
        metadata={'importance': 0.7, 'decision_type': 'technical'}
    )
    
    print("   工作记忆已记录开发过程")
    
    # 2. 自动提升演示
    print("\n2. 记忆层级提升:")
    
    # 填充更多工作记忆触发自动提升
    for i in range(3):
        result = mm.process_information(
            f"Refactoring step {i}",
            metadata={'importance': 0.65}
        )
        if 'episodic' in result['stored_in']:
            print("   工作记忆自动提升到情景记忆!")
            break
    
    # 3. 创建相似情景以提取语义知识
    print("\n3. 语义知识提取:")
    
    # 创建多个相似的错误处理情景
    for i in range(4):
        mm.episodic.store_episode(
            event="Handled database timeout error",
            context={
                'error_type': 'timeout',
                'retry_count': 3,
                'backoff_strategy': 'exponential',
                'success': True
            },
            outcomes={'resolved': True, 'time_to_resolve': f'{i+1} minutes'}
        )
    
    # 分析模式
    patterns = mm.analyze_memory_patterns(min_pattern_occurrences=3)
    if patterns['episodic_patterns']:
        print(f"   发现 {len(patterns['episodic_patterns'])} 个情景模式")
        print("   可能已自动提取为语义知识")
    
    # 4. 查看最终统计
    print("\n4. 最终记忆系统状态:")
    final_stats = mm.get_statistics()
    print(f"   总处理: {final_stats['manager_stats']['total_processed']}")
    print(f"   提升次数: {final_stats['manager_stats']['promotions']}")
    print(f"   各层记忆数量: ")
    for layer, stats in final_stats['layer_stats'].items():
        if layer == 'working':
            print(f"     {layer}: {stats['total_items']} 项")
        elif layer == 'episodic':
            print(f"     {layer}: {stats['total_episodes']} 情景")
        elif layer == 'semantic':
            print(f"     {layer}: {stats['total_concepts']} 概念")


def main():
    """主函数"""
    print("记忆管理系统完整演示\n")
    print("这个演示展示了基于人类认知的三层记忆架构：")
    print("- 工作记忆：短期临时存储，容量有限")
    print("- 情景记忆：项目和任务相关的经验")
    print("- 语义记忆：抽象的知识和模式")
    print("\n" + "="*50 + "\n")
    
    # 运行各个演示
    demo_basic_usage()
    demo_working_memory()
    demo_episodic_memory()
    demo_semantic_memory()
    demo_memory_transformation()
    
    print("\n" + "="*50)
    print("\n演示完成！")
    print("\n关键特性总结：")
    print("1. 三层记忆架构模拟人类认知")
    print("2. 自动记忆层级提升和转化")
    print("3. 基于触发器的智能记录")
    print("4. 时间衰减和容量管理")
    print("5. 模式识别和知识提取")
    print("6. 项目上下文和关系管理")
    print("7. 灵活的查询和召回机制")


if __name__ == "__main__":
    main()