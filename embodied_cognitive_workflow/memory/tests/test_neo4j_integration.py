"""
Neo4j集成测试

测试Neo4j语义记忆与其他组件的集成
"""

import unittest
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

from ..memory_manager import MemoryManager, MemoryLayer
from ..interfaces import TriggerType, Concept, Episode
from ..semantic_memory_neo4j import Neo4jSemanticMemory
from ..neo4j_config import Neo4jConfig
from ..transformers import EpisodicToSemanticTransformer


class TestNeo4jIntegrationWithMemoryManager(unittest.TestCase):
    """测试Neo4j与记忆管理器的集成"""
    
    @classmethod
    def setUpClass(cls):
        """类级别设置"""
        # 检查Neo4j是否可用
        try:
            from neo4j import GraphDatabase
            test_config = Neo4jConfig(
                uri="bolt://localhost:7687",
                username="neo4j",
                password="graphiti123!",
                database="test_integration"
            )
            driver = GraphDatabase.driver(
                test_config.uri,
                auth=(test_config.username, test_config.password)
            )
            driver.verify_connectivity()
            driver.close()
            cls.neo4j_available = True
        except Exception as e:
            print(f"Neo4j not available: {e}")
            cls.neo4j_available = False
    
    def setUp(self):
        """测试前准备"""
        if not self.neo4j_available:
            self.skipTest("Neo4j not available")
        
        # 创建Neo4j语义记忆
        self.neo4j_config = Neo4jConfig(
            database="test_integration",
            create_indexes=True
        )
        self.semantic_memory = Neo4jSemanticMemory(self.neo4j_config)
        self.semantic_memory.clear()
        
        # 创建记忆管理器（使用Neo4j语义记忆）
        self.memory_manager = MemoryManager(
            semantic_memory=self.semantic_memory,
            auto_promote=True
        )
    
    def tearDown(self):
        """测试后清理"""
        if hasattr(self, 'semantic_memory'):
            self.semantic_memory.clear()
            self.semantic_memory.close()
    
    def test_automatic_promotion_to_neo4j(self):
        """测试从情景记忆自动提升到Neo4j语义记忆"""
        # 创建相似的情景记忆
        project_id = "test_project"
        
        # 模拟多次数据库连接失败
        for i in range(5):
            self.memory_manager.episodic.store_episode(
                event="Database connection timeout",
                context={
                    'error_type': 'timeout',
                    'database': 'production',
                    'retry_count': 3,
                    'resolution': 'increase timeout'
                },
                project_id=project_id,
                outcomes={'resolved': True}
            )
        
        # 手动触发模式分析
        patterns = self.memory_manager.analyze_memory_patterns(
            min_pattern_occurrences=3
        )
        
        # 验证模式被识别
        self.assertGreater(len(patterns['episodic_patterns']), 0)
        
        # 检查是否在Neo4j中创建了概念
        concepts = self.semantic_memory.find_patterns("error_handling", min_confidence=0.0)
        
        # 如果有自动提升，应该能找到相关概念
        if concepts:
            # 验证概念属性
            error_concepts = [c for c in concepts if 'timeout' in str(c.attributes).lower()]
            self.assertGreater(len(error_concepts), 0)
    
    def test_knowledge_graph_construction(self):
        """测试知识图谱构建"""
        # 添加编程语言知识体系
        root = Concept(
            id="prog_langs",
            name="Programming Languages",
            category="domain",
            attributes={'type': 'knowledge_domain'},
            confidence=1.0,
            domain="computer_science"
        )
        root_id = self.semantic_memory.add_concept(root)
        
        # 添加语言分类
        categories = [
            ("Static Typed", ["Java", "C++", "Rust", "Go"]),
            ("Dynamic Typed", ["Python", "JavaScript", "Ruby"]),
            ("Functional", ["Haskell", "Lisp", "Clojure"])
        ]
        
        category_ids = {}
        for category_name, languages in categories:
            # 创建分类概念
            category = Concept(
                id="",
                name=category_name,
                category="language_category",
                attributes={'description': f'{category_name} languages'},
                confidence=0.9
            )
            cat_id = self.semantic_memory.add_concept(category)
            category_ids[category_name] = cat_id
            
            # 连接到根节点
            self.semantic_memory.create_relationship(root_id, cat_id, "INCLUDES")
            
            # 添加具体语言
            for lang_name in languages:
                lang = Concept(
                    id="",
                    name=lang_name,
                    category="programming_language",
                    attributes={'paradigm': category_name.lower()},
                    confidence=0.85
                )
                lang_id = self.semantic_memory.add_concept(lang)
                self.semantic_memory.create_relationship(cat_id, lang_id, "CONTAINS")
        
        # 获取知识图谱
        graph = self.semantic_memory.get_knowledge_graph(root_id, depth=3)
        
        # 验证图谱结构
        self.assertGreater(len(graph['nodes']), 10)
        self.assertGreater(len(graph['edges']), 10)
        
        # 验证可以通过记忆管理器访问
        results = self.memory_manager.recall_with_context(
            "programming languages",
            layers=MemoryLayer.SEMANTIC
        )
        self.assertGreater(len(results['semantic']), 0)
    
    def test_cross_layer_memory_flow(self):
        """测试跨层记忆流动"""
        # 1. 工作记忆
        wm_id = self.memory_manager.process_information(
            "Learning about design patterns",
            trigger_type=TriggerType.STATE_CHANGE,
            metadata={'importance': 0.8, 'topic': 'software_design'}
        )
        
        # 2. 情景记忆
        episode_ids = []
        patterns = ["Singleton", "Factory", "Observer", "Strategy"]
        
        for pattern in patterns:
            ep_id = self.memory_manager.episodic.store_episode(
                event=f"Implemented {pattern} pattern",
                context={
                    'pattern_name': pattern,
                    'category': 'creational' if pattern in ['Singleton', 'Factory'] else 'behavioral',
                    'difficulty': 'medium',
                    'use_case': f'{pattern} pattern use case'
                },
                project_id="design_patterns_study"
            )
            episode_ids.append(ep_id)
        
        # 3. 手动提升到语义记忆
        transformer = EpisodicToSemanticTransformer(
            self.memory_manager.episodic,
            self.semantic_memory
        )
        
        # 从情景中提取概念
        for ep_id in episode_ids:
            episode = self.memory_manager.episodic.get(ep_id)
            if episode:
                # 转换为概念
                concept = Concept(
                    id="",
                    name=f"{episode.metadata['pattern_name']} Pattern",
                    category="design_pattern",
                    attributes=episode.metadata,
                    confidence=0.85,
                    domain="software_design"
                )
                self.semantic_memory.add_concept(concept)
        
        # 4. 验证各层都有相关记忆
        results = self.memory_manager.recall_with_context("pattern")
        
        # 验证各层结果
        self.assertGreater(len(results['working']), 0)
        self.assertGreater(len(results['episodic']), 0)
        self.assertGreater(len(results['semantic']), 0)
    
    def test_concept_similarity_and_merging(self):
        """测试概念相似度计算和合并"""
        # 创建相似概念
        concept1 = Concept(
            id="ml_1",
            name="Machine Learning",
            category="technology",
            attributes={
                'type': 'AI',
                'applications': ['prediction', 'classification'],
                'algorithms': ['neural networks', 'decision trees']
            },
            confidence=0.85,
            domain="artificial_intelligence"
        )
        
        concept2 = Concept(
            id="ml_2",
            name="ML",
            category="technology",
            attributes={
                'type': 'Artificial Intelligence',
                'applications': ['forecasting', 'pattern recognition'],
                'algorithms': ['deep learning', 'random forests']
            },
            confidence=0.80,
            domain="artificial_intelligence"
        )
        
        # 添加概念
        id1 = self.semantic_memory.add_concept(concept1)
        id2 = self.semantic_memory.add_concept(concept2)
        
        # 添加一些关系
        related = Concept(
            id="dl_1",
            name="Deep Learning",
            category="technology",
            attributes={'subset_of': 'Machine Learning'},
            confidence=0.9
        )
        related_id = self.semantic_memory.add_concept(related)
        
        self.semantic_memory.create_relationship(related_id, id1, "SUBSET_OF")
        self.semantic_memory.create_relationship(related_id, id2, "RELATED_TO")
        
        # 计算相似度
        similarity = self.semantic_memory.calculate_concept_similarity(id1, id2)
        self.assertGreater(similarity, 0.0)
        
        # 合并概念
        merged_id = self.semantic_memory.merge_concepts(id1, id2)
        self.assertIsNotNone(merged_id)
        
        # 验证合并后的概念
        merged = self.semantic_memory._get_concept(merged_id)
        self.assertIsNotNone(merged)
        self.assertIn("Machine Learning", merged.name)
        self.assertIn("ML", merged.name)
        
        # 验证关系被保留
        related_concepts = self.semantic_memory.find_related_concepts(merged_id)
        self.assertGreater(len(related_concepts), 0)
        
        # 验证原概念被删除
        self.assertFalse(self.semantic_memory.exists(id1))
        self.assertFalse(self.semantic_memory.exists(id2))
    
    def test_performance_with_large_dataset(self):
        """测试大数据集性能"""
        start_time = time.time()
        
        # 1. 批量创建概念
        concept_count = 500
        concept_ids = []
        
        for i in range(concept_count):
            concept = Concept(
                id="",
                name=f"Concept {i}",
                category=f"category_{i % 20}",  # 20个类别
                attributes={
                    'index': i,
                    'data': f"Description for concept {i}",
                    'tags': [f'tag_{j}' for j in range(i % 5 + 1)]
                },
                confidence=0.5 + (i % 50) / 100,
                domain=f"domain_{i % 10}"  # 10个领域
            )
            cid = self.semantic_memory.add_concept(concept)
            concept_ids.append(cid)
        
        insert_time = time.time() - start_time
        print(f"\n插入 {concept_count} 个概念耗时: {insert_time:.2f} 秒")
        
        # 2. 创建关系网络
        relationship_start = time.time()
        relationship_count = 0
        
        # 创建层次关系
        for i in range(0, len(concept_ids) - 1, 10):
            for j in range(1, min(10, len(concept_ids) - i)):
                self.semantic_memory.create_relationship(
                    concept_ids[i], 
                    concept_ids[i + j], 
                    "RELATED_TO"
                )
                relationship_count += 1
        
        relationship_time = time.time() - relationship_start
        print(f"创建 {relationship_count} 个关系耗时: {relationship_time:.2f} 秒")
        
        # 3. 测试搜索性能
        search_start = time.time()
        search_queries = ["Concept", "tag_2", "domain_5", "category_10"]
        total_results = 0
        
        for query in search_queries:
            results = self.semantic_memory.recall(query, limit=50)
            total_results += len(results)
        
        search_time = time.time() - search_start
        print(f"执行 {len(search_queries)} 次搜索耗时: {search_time:.2f} 秒")
        print(f"平均每次搜索: {search_time/len(search_queries)*1000:.2f} 毫秒")
        
        # 4. 测试图遍历性能
        graph_start = time.time()
        graph = self.semantic_memory.get_knowledge_graph(concept_ids[0], depth=2)
        graph_time = time.time() - graph_start
        
        print(f"图遍历（深度2）耗时: {graph_time:.2f} 秒")
        print(f"返回节点数: {len(graph['nodes'])}, 边数: {len(graph['edges'])}")
        
        # 5. 统计信息
        stats = self.semantic_memory.get_statistics()
        print(f"\n最终统计:")
        print(f"  总概念数: {stats['total_concepts']}")
        print(f"  总关系数: {stats['total_relationships']}")
        print(f"  平均置信度: {stats['avg_confidence']:.3f}")
        print(f"  类别数: {stats['categories_count']}")
        print(f"  领域数: {stats['domains_count']}")
        
        # 验证性能基准
        self.assertLess(insert_time, 30)  # 插入应在30秒内完成
        self.assertLess(search_time / len(search_queries), 0.5)  # 平均搜索小于0.5秒
    
    def test_memory_persistence(self):
        """测试记忆持久化"""
        # 添加测试数据
        test_concepts = []
        for i in range(10):
            concept = Concept(
                id=f"persist_test_{i}",
                name=f"Persistent Concept {i}",
                category="persistence_test",
                attributes={'test_id': i, 'persistent': True},
                confidence=0.9
            )
            self.semantic_memory.add_concept(concept)
            test_concepts.append(concept)
        
        # 关闭连接
        self.semantic_memory.close()
        
        # 重新创建连接
        new_memory = Neo4jSemanticMemory(self.neo4j_config)
        
        # 验证数据仍然存在
        for concept in test_concepts:
            self.assertTrue(new_memory.exists(concept.id))
            retrieved = new_memory._get_concept(concept.id)
            self.assertEqual(retrieved.name, concept.name)
            self.assertEqual(retrieved.attributes['test_id'], concept.attributes['test_id'])
        
        # 清理
        new_memory.clear()
        new_memory.close()


class TestNeo4jMigration(unittest.TestCase):
    """测试从内存到Neo4j的迁移"""
    
    @classmethod
    def setUpClass(cls):
        """检查Neo4j可用性"""
        try:
            from neo4j import GraphDatabase
            test_config = Neo4jConfig(
                uri="bolt://localhost:7687",
                username="neo4j",
                password="graphiti123!",
                database="test_migration"
            )
            driver = GraphDatabase.driver(
                test_config.uri,
                auth=(test_config.username, test_config.password)
            )
            driver.verify_connectivity()
            driver.close()
            cls.neo4j_available = True
        except Exception:
            cls.neo4j_available = False
    
    def setUp(self):
        """测试前准备"""
        if not self.neo4j_available:
            self.skipTest("Neo4j not available")
            
        # 创建内存版本的记忆管理器
        from ..semantic_memory import SemanticMemory
        self.in_memory_semantic = SemanticMemory()
        self.memory_manager_inmem = MemoryManager(
            semantic_memory=self.in_memory_semantic
        )
        
        # 创建Neo4j版本
        self.neo4j_config = Neo4jConfig(database="test_migration")
        self.neo4j_semantic = Neo4jSemanticMemory(self.neo4j_config)
        self.neo4j_semantic.clear()
        self.memory_manager_neo4j = MemoryManager(
            semantic_memory=self.neo4j_semantic
        )
    
    def tearDown(self):
        """测试后清理"""
        if hasattr(self, 'neo4j_semantic'):
            self.neo4j_semantic.clear()
            self.neo4j_semantic.close()
    
    def test_migrate_semantic_memory(self):
        """测试语义记忆迁移"""
        # 1. 在内存版本中创建数据
        concepts_data = [
            ("Algorithm", "computer_science", {'type': 'fundamental', 'complexity': 'varies'}),
            ("Data Structure", "computer_science", {'type': 'fundamental', 'examples': ['array', 'list']}),
            ("Design Pattern", "software_engineering", {'type': 'best_practice', 'gof': True}),
            ("Machine Learning", "artificial_intelligence", {'type': 'technology', 'applications': 'many'})
        ]
        
        in_memory_ids = {}
        for name, category, attrs in concepts_data:
            concept = Concept(
                id="",
                name=name,
                category=category,
                attributes=attrs,
                confidence=0.85,
                domain="technology"
            )
            cid = self.in_memory_semantic.add_concept(concept)
            in_memory_ids[name] = cid
        
        # 2. 获取内存中的所有概念
        all_concepts = []
        for concept_list in self.in_memory_semantic.category_index.values():
            all_concepts.extend(concept_list)
        
        # 3. 迁移到Neo4j
        neo4j_ids = {}
        for concept in all_concepts:
            # 创建新ID映射
            new_concept = Concept(
                id=f"migrated_{concept.id}",
                name=concept.name,
                category=concept.category,
                attributes=concept.attributes,
                relationships=concept.relationships,
                confidence=concept.confidence,
                examples=concept.examples,
                domain=concept.domain
            )
            new_id = self.neo4j_semantic.add_concept(new_concept)
            neo4j_ids[concept.name] = new_id
        
        # 4. 验证迁移成功
        self.assertEqual(len(neo4j_ids), len(in_memory_ids))
        
        # 5. 验证数据完整性
        for name in in_memory_ids:
            # 从Neo4j获取
            neo4j_concept = self.neo4j_semantic._get_concept(neo4j_ids[name])
            
            # 从内存获取原始概念
            in_mem_concept = None
            for concept_list in self.in_memory_semantic.category_index.values():
                for c in concept_list:
                    if c.name == name:
                        in_mem_concept = c
                        break
            
            # 比较属性
            self.assertEqual(neo4j_concept.name, in_mem_concept.name)
            self.assertEqual(neo4j_concept.category, in_mem_concept.category)
            self.assertEqual(neo4j_concept.confidence, in_mem_concept.confidence)
            self.assertEqual(neo4j_concept.domain, in_mem_concept.domain)
    
    def test_performance_comparison(self):
        """比较内存和Neo4j性能"""
        # 准备测试数据
        test_size = 100
        
        # 1. 测试插入性能
        print("\n性能比较测试:")
        
        # 内存版本插入
        in_memory_start = time.time()
        for i in range(test_size):
            concept = Concept(
                id="",
                name=f"InMemory Concept {i}",
                category="test",
                attributes={'index': i}
            )
            self.in_memory_semantic.add_concept(concept)
        in_memory_insert_time = time.time() - in_memory_start
        
        # Neo4j版本插入
        neo4j_start = time.time()
        for i in range(test_size):
            concept = Concept(
                id="",
                name=f"Neo4j Concept {i}",
                category="test",
                attributes={'index': i}
            )
            self.neo4j_semantic.add_concept(concept)
        neo4j_insert_time = time.time() - neo4j_start
        
        print(f"插入 {test_size} 个概念:")
        print(f"  内存版本: {in_memory_insert_time:.3f} 秒")
        print(f"  Neo4j版本: {neo4j_insert_time:.3f} 秒")
        print(f"  比率: {neo4j_insert_time/in_memory_insert_time:.2f}x")
        
        # 2. 测试搜索性能
        search_queries = ["Concept", "test", "50"]
        
        # 内存版本搜索
        in_memory_search_start = time.time()
        for query in search_queries:
            self.in_memory_semantic.recall(query)
        in_memory_search_time = time.time() - in_memory_search_start
        
        # Neo4j版本搜索
        neo4j_search_start = time.time()
        for query in search_queries:
            self.neo4j_semantic.recall(query)
        neo4j_search_time = time.time() - neo4j_search_start
        
        print(f"\n搜索性能 ({len(search_queries)} 次查询):")
        print(f"  内存版本: {in_memory_search_time*1000:.2f} 毫秒")
        print(f"  Neo4j版本: {neo4j_search_time*1000:.2f} 毫秒")
        
        # 注意：Neo4j在大规模数据和复杂查询时表现更好


if __name__ == '__main__':
    unittest.main()