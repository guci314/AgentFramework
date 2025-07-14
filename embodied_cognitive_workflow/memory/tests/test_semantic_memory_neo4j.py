"""
Neo4j语义记忆测试

包括单元测试、集成测试和性能测试
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
import time

from ..semantic_memory_neo4j import Neo4jSemanticMemory
from ..neo4j_config import Neo4jConfig, default_config
from ..interfaces import Concept, MemoryItem
from ..utils import generate_memory_id


class TestNeo4jSemanticMemoryUnit(unittest.TestCase):
    """Neo4j语义记忆单元测试（使用Mock）"""
    
    @patch('memory.semantic_memory_neo4j.GraphDatabase')
    def setUp(self, mock_graph_db):
        """测试前准备"""
        # 设置mock driver
        self.mock_driver = Mock()
        self.mock_session = Mock()
        self.mock_tx = Mock()
        
        mock_graph_db.driver.return_value = self.mock_driver
        self.mock_driver.verify_connectivity.return_value = None
        self.mock_driver.session.return_value.__enter__ = Mock(return_value=self.mock_session)
        self.mock_driver.session.return_value.__exit__ = Mock(return_value=None)
        
        # 创建测试实例
        self.config = Neo4jConfig(create_indexes=False)
        self.memory = Neo4jSemanticMemory(self.config)
    
    def test_add_concept(self):
        """测试添加概念"""
        # 准备测试数据
        concept = Concept(
            id="test_concept_1",
            name="Test Concept",
            category="test",
            attributes={"key": "value"},
            confidence=0.8,
            domain="testing"
        )
        
        # Mock查询结果
        self.mock_session.run.return_value = Mock()
        
        # 执行测试
        result_id = self.memory.add_concept(concept)
        
        # 验证
        self.assertEqual(result_id, "test_concept_1")
        self.mock_session.run.assert_called()
        
        # 验证SQL参数
        call_args = self.mock_session.run.call_args[1]
        self.assertEqual(call_args['id'], concept.id)
        self.assertEqual(call_args['name'], concept.name)
        self.assertEqual(call_args['category'], concept.category)
        self.assertEqual(call_args['confidence'], concept.confidence)
    
    def test_get_concept(self):
        """测试获取概念"""
        # Mock查询结果
        mock_record = Mock()
        mock_record.__getitem__.return_value = {
            'id': 'test_id',
            'name': 'Test Concept',
            'category': 'test',
            'attributes': '{"key": "value"}',
            'confidence': 0.8,
            'domain': 'testing'
        }
        
        mock_result = Mock()
        mock_result.single.return_value = mock_record
        self.mock_session.run.return_value = mock_result
        
        # 执行测试
        concept = self.memory._get_concept('test_id')
        
        # 验证
        self.assertIsNotNone(concept)
        self.assertEqual(concept.id, 'test_id')
        self.assertEqual(concept.name, 'Test Concept')
        self.assertEqual(concept.category, 'test')
    
    def test_calculate_similarity(self):
        """测试相似度计算"""
        # Mock Jaccard相似度结果
        mock_record = {'jaccard_similarity': 0.75}
        mock_result = Mock()
        mock_result.single.return_value = mock_record
        self.mock_session.run.return_value = mock_result
        
        # 执行测试
        similarity = self.memory.calculate_concept_similarity('concept1', 'concept2')
        
        # 验证
        self.assertEqual(similarity, 0.75)
    
    def test_find_patterns(self):
        """测试模式查找"""
        # Mock查询结果
        mock_records = [
            {'c': {
                'id': 'pattern1',
                'name': 'Pattern 1',
                'category': 'pattern',
                'attributes': '{}',
                'confidence': 0.9,
                'domain': 'test'
            }},
            {'c': {
                'id': 'pattern2',
                'name': 'Pattern 2',
                'category': 'pattern',
                'attributes': '{}',
                'confidence': 0.85,
                'domain': 'test'
            }}
        ]
        
        self.mock_session.run.return_value = mock_records
        
        # 执行测试
        patterns = self.memory.find_patterns('test', min_confidence=0.8)
        
        # 验证
        self.assertEqual(len(patterns), 2)
        self.assertEqual(patterns[0].name, 'Pattern 1')
        self.assertEqual(patterns[1].name, 'Pattern 2')
    
    def test_merge_concepts(self):
        """测试概念合并"""
        # Mock获取概念
        concept1 = Concept(
            id='concept1',
            name='Concept A',
            category='test',
            attributes={'a': 1},
            confidence=0.7
        )
        concept2 = Concept(
            id='concept2',
            name='Concept B',
            category='test',
            attributes={'b': 2},
            confidence=0.8
        )
        
        with patch.object(self.memory, '_get_concept') as mock_get:
            mock_get.side_effect = [concept1, concept2]
            
            # Mock添加概念
            with patch.object(self.memory, 'add_concept') as mock_add:
                mock_add.return_value = 'merged_id'
                
                # 执行测试
                result = self.memory.merge_concepts('concept1', 'concept2')
                
                # 验证
                self.assertEqual(result, 'merged_id')
                mock_add.assert_called_once()
                
                # 验证合并的概念
                merged_concept = mock_add.call_args[0][0]
                self.assertIn('Concept A', merged_concept.name)
                self.assertIn('Concept B', merged_concept.name)
                self.assertEqual(merged_concept.confidence, 0.8)  # max
    
    def test_get_knowledge_graph(self):
        """测试知识图谱构建"""
        # Mock路径查询结果
        mock_path = Mock()
        mock_path.nodes = [
            {'id': 'root', 'name': 'Root', 'category': 'root', 'confidence': 1.0, 'attributes': '{}'},
            {'id': 'child1', 'name': 'Child 1', 'category': 'child', 'confidence': 0.9, 'attributes': '{}'},
            {'id': 'child2', 'name': 'Child 2', 'category': 'child', 'confidence': 0.8, 'attributes': '{}'}
        ]
        
        mock_rel1 = Mock()
        mock_rel1.start_node = {'id': 'root'}
        mock_rel1.end_node = {'id': 'child1'}
        mock_rel1.type = 'INCLUDES'
        mock_rel1.__iter__ = Mock(return_value=iter([]))
        
        mock_rel2 = Mock()
        mock_rel2.start_node = {'id': 'root'}
        mock_rel2.end_node = {'id': 'child2'}
        mock_rel2.type = 'INCLUDES'
        mock_rel2.__iter__ = Mock(return_value=iter([]))
        
        mock_path.relationships = [mock_rel1, mock_rel2]
        
        self.mock_session.run.return_value = [{'path': mock_path}]
        
        # 执行测试
        graph = self.memory.get_knowledge_graph('root', depth=1)
        
        # 验证
        self.assertEqual(len(graph['nodes']), 3)
        self.assertEqual(len(graph['edges']), 2)
        self.assertEqual(graph['root'], 'root')
    
    def test_error_handling(self):
        """测试错误处理"""
        # Mock连接错误
        with patch('memory.semantic_memory_neo4j.GraphDatabase') as mock_graph_db:
            mock_graph_db.driver.side_effect = Exception("Connection failed")
            
            # 验证抛出异常
            with self.assertRaises(Exception):
                Neo4jSemanticMemory(self.config)


class TestNeo4jSemanticMemoryIntegration(unittest.TestCase):
    """Neo4j语义记忆集成测试（需要真实Neo4j实例）"""
    
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
                database="test"  # 使用测试数据库
            )
            driver = GraphDatabase.driver(
                test_config.uri,
                auth=(test_config.username, test_config.password)
            )
            driver.verify_connectivity()
            driver.close()
            cls.neo4j_available = True
        except Exception as e:
            print(f"Neo4j not available for integration tests: {e}")
            cls.neo4j_available = False
    
    def setUp(self):
        """测试前准备"""
        if not self.neo4j_available:
            self.skipTest("Neo4j not available")
        
        # 使用测试数据库
        self.config = Neo4jConfig(
            database="test",
            create_indexes=True
        )
        self.memory = Neo4jSemanticMemory(self.config)
        
        # 清空测试数据
        self.memory.clear()
    
    def tearDown(self):
        """测试后清理"""
        if hasattr(self, 'memory'):
            self.memory.clear()
            self.memory.close()
    
    def test_full_lifecycle(self):
        """测试完整生命周期"""
        # 1. 添加概念
        concept1 = Concept(
            id="",
            name="Machine Learning",
            category="technology",
            attributes={
                'type': 'AI',
                'applications': ['classification', 'regression', 'clustering']
            },
            confidence=0.95,
            domain="artificial_intelligence"
        )
        
        id1 = self.memory.add_concept(concept1)
        self.assertIsNotNone(id1)
        
        # 2. 验证存在
        self.assertTrue(self.memory.exists(id1))
        
        # 3. 获取概念
        retrieved = self.memory.get(id1)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content['name'], 'Machine Learning')
        
        # 4. 更新概念
        updated = self.memory.update(
            id1,
            concept1.name,
            {'confidence': 0.98, 'verified': True}
        )
        self.assertTrue(updated)
        
        # 5. 添加相关概念
        concept2 = Concept(
            id="",
            name="Deep Learning",
            category="technology",
            attributes={'type': 'AI', 'subset_of': 'Machine Learning'},
            confidence=0.9,
            domain="artificial_intelligence"
        )
        id2 = self.memory.add_concept(concept2)
        
        # 6. 创建关系
        self.memory.create_relationship(id2, id1, "SUBSET_OF")
        
        # 7. 查找相关概念
        related = self.memory.find_related_concepts(id1)
        self.assertEqual(len(related), 1)
        self.assertEqual(related[0][0], "SUBSET_OF")
        
        # 8. 搜索
        results = self.memory.recall("learning", limit=10)
        self.assertGreaterEqual(len(results), 2)
        
        # 9. 删除
        deleted = self.memory.forget(id2)
        self.assertTrue(deleted)
        self.assertFalse(self.memory.exists(id2))
    
    def test_knowledge_graph_building(self):
        """测试知识图谱构建"""
        # 创建层次结构
        root = Concept(
            id="root",
            name="Programming Languages",
            category="domain",
            attributes={'description': 'Study of programming languages'}
        )
        root_id = self.memory.add_concept(root)
        
        # 添加子概念
        languages = [
            ("Python", "dynamic", {'paradigm': 'multi-paradigm'}),
            ("Java", "static", {'paradigm': 'object-oriented'}),
            ("Haskell", "static", {'paradigm': 'functional'})
        ]
        
        for name, typing, attrs in languages:
            concept = Concept(
                id="",
                name=name,
                category="language",
                attributes={**attrs, 'typing': typing}
            )
            lang_id = self.memory.add_concept(concept)
            self.memory.create_relationship(root_id, lang_id, "INCLUDES")
        
        # 获取知识图谱
        graph = self.memory.get_knowledge_graph(root_id, depth=2)
        
        # 验证结构
        self.assertEqual(len(graph['nodes']), 4)  # root + 3 languages
        self.assertEqual(len(graph['edges']), 3)  # 3 INCLUDES关系
        self.assertEqual(graph['root'], root_id)
    
    def test_pattern_finding(self):
        """测试模式查找"""
        # 添加多个设计模式概念
        patterns = [
            ("Singleton", 0.9),
            ("Factory", 0.85),
            ("Observer", 0.88),
            ("Strategy", 0.82)
        ]
        
        for name, confidence in patterns:
            concept = Concept(
                id="",
                name=f"{name} Pattern",
                category="design_pattern",
                attributes={'type': 'creational' if 'Factory' in name or 'Singleton' in name else 'behavioral'},
                confidence=confidence,
                domain="software_design"
            )
            self.memory.add_concept(concept)
        
        # 查找高置信度模式
        found = self.memory.find_patterns("software_design", min_confidence=0.85)
        
        # 验证结果
        self.assertGreaterEqual(len(found), 3)
        for pattern in found:
            self.assertGreaterEqual(pattern.confidence, 0.85)
    
    def test_statistics(self):
        """测试统计功能"""
        # 添加测试数据
        categories = ['algorithm', 'data_structure', 'pattern']
        domains = ['computer_science', 'software_engineering']
        
        for i in range(10):
            concept = Concept(
                id="",
                name=f"Concept {i}",
                category=categories[i % len(categories)],
                attributes={'index': i},
                confidence=0.5 + (i * 0.05),
                domain=domains[i % len(domains)]
            )
            self.memory.add_concept(concept)
        
        # 获取统计信息
        stats = self.memory.get_statistics()
        
        # 验证统计数据
        self.assertEqual(stats['total_concepts'], 10)
        self.assertGreater(stats['avg_confidence'], 0.5)
        self.assertEqual(stats['categories_count'], len(categories))
        self.assertEqual(stats['domains_count'], len(domains))
        self.assertIn('algorithm', stats['categories'])
        self.assertIn('computer_science', stats['domains'])


class TestNeo4jSemanticMemoryPerformance(unittest.TestCase):
    """Neo4j语义记忆性能测试"""
    
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
                database="test_performance"
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
        
        self.config = Neo4jConfig(
            database="test_performance",
            create_indexes=True
        )
        self.memory = Neo4jSemanticMemory(self.config)
        self.memory.clear()
    
    def tearDown(self):
        """测试后清理"""
        if hasattr(self, 'memory'):
            self.memory.clear()
            self.memory.close()
    
    def test_bulk_insert_performance(self):
        """测试批量插入性能"""
        concept_count = 1000
        
        start_time = time.time()
        
        # 批量插入概念
        for i in range(concept_count):
            concept = Concept(
                id="",
                name=f"Concept {i}",
                category=f"category_{i % 10}",
                attributes={
                    'index': i,
                    'data': f"Some data for concept {i}",
                    'tags': [f'tag_{j}' for j in range(i % 5)]
                },
                confidence=0.5 + (i % 50) / 100,
                domain=f"domain_{i % 5}"
            )
            self.memory.add_concept(concept)
        
        insert_time = time.time() - start_time
        
        # 验证和报告
        self.assertEqual(self.memory.size(), concept_count)
        print(f"\n批量插入 {concept_count} 个概念耗时: {insert_time:.2f} 秒")
        print(f"平均每个概念: {insert_time/concept_count*1000:.2f} 毫秒")
        
        # 性能基准（应该在合理范围内）
        self.assertLess(insert_time, 60)  # 1000个概念应该在60秒内完成
    
    def test_search_performance(self):
        """测试搜索性能"""
        # 准备测试数据
        for i in range(500):
            concept = Concept(
                id="",
                name=f"Search Test Concept {i}",
                category="search_test",
                attributes={'keywords': ['search', 'test', 'performance', f'keyword_{i}']},
                confidence=0.8
            )
            self.memory.add_concept(concept)
        
        # 测试搜索性能
        search_queries = ['search', 'test', 'concept', 'performance', 'keyword_100']
        total_time = 0
        total_results = 0
        
        for query in search_queries:
            start_time = time.time()
            results = self.memory.recall(query, limit=50)
            search_time = time.time() - start_time
            total_time += search_time
            total_results += len(results)
            
            print(f"\n搜索 '{query}': {len(results)} 结果，耗时 {search_time*1000:.2f} 毫秒")
        
        avg_time = total_time / len(search_queries)
        print(f"\n平均搜索时间: {avg_time*1000:.2f} 毫秒")
        
        # 性能基准
        self.assertLess(avg_time, 1.0)  # 平均搜索应该在1秒内
    
    def test_graph_traversal_performance(self):
        """测试图遍历性能"""
        # 创建深层次结构
        root_id = self.memory.add_concept(Concept(
            id="root",
            name="Root Concept",
            category="root"
        ))
        
        # 创建树形结构（深度3，每层10个节点）
        current_layer = [root_id]
        
        for depth in range(3):
            next_layer = []
            for parent_id in current_layer:
                for i in range(10):
                    child = Concept(
                        id="",
                        name=f"Level {depth+1} Node {i}",
                        category=f"level_{depth+1}"
                    )
                    child_id = self.memory.add_concept(child)
                    self.memory.create_relationship(parent_id, child_id, "CONTAINS")
                    next_layer.append(child_id)
            current_layer = next_layer
        
        # 测试图遍历性能
        start_time = time.time()
        graph = self.memory.get_knowledge_graph(root_id, depth=3)
        traversal_time = time.time() - start_time
        
        print(f"\n图遍历（深度3）: {len(graph['nodes'])} 节点，{len(graph['edges'])} 边")
        print(f"耗时: {traversal_time*1000:.2f} 毫秒")
        
        # 验证结果
        self.assertEqual(len(graph['nodes']), 1111)  # 1 + 10 + 100 + 1000
        self.assertLess(traversal_time, 5.0)  # 应该在5秒内完成
    
    def test_concurrent_operations(self):
        """测试并发操作性能"""
        import threading
        import queue
        
        results = queue.Queue()
        thread_count = 5
        operations_per_thread = 100
        
        def worker(thread_id):
            """工作线程"""
            local_results = []
            
            for i in range(operations_per_thread):
                try:
                    # 混合操作
                    if i % 3 == 0:
                        # 添加
                        concept = Concept(
                            id="",
                            name=f"Thread {thread_id} Concept {i}",
                            category="concurrent_test"
                        )
                        self.memory.add_concept(concept)
                    elif i % 3 == 1:
                        # 搜索
                        self.memory.recall(f"Thread {thread_id}", limit=10)
                    else:
                        # 获取统计
                        self.memory.get_statistics()
                    
                    local_results.append(True)
                except Exception as e:
                    local_results.append(False)
                    print(f"Thread {thread_id} operation {i} failed: {e}")
            
            results.put(local_results)
        
        # 启动线程
        threads = []
        start_time = time.time()
        
        for i in range(thread_count):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        # 等待完成
        for t in threads:
            t.join()
        
        concurrent_time = time.time() - start_time
        
        # 收集结果
        total_success = 0
        while not results.empty():
            thread_results = results.get()
            total_success += sum(thread_results)
        
        print(f"\n并发测试: {thread_count} 线程，每线程 {operations_per_thread} 操作")
        print(f"总耗时: {concurrent_time:.2f} 秒")
        print(f"成功率: {total_success}/{thread_count * operations_per_thread}")
        
        # 验证
        self.assertGreater(total_success, thread_count * operations_per_thread * 0.95)  # 95%成功率


def run_performance_tests():
    """运行性能测试并生成报告"""
    print("\n" + "="*50)
    print("Neo4j 语义记忆性能测试报告")
    print("="*50)
    
    # 运行性能测试
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNeo4jSemanticMemoryPerformance)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 生成报告
    print("\n" + "="*50)
    print("测试总结:")
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("="*50)


if __name__ == '__main__':
    # 运行所有测试
    unittest.main()
    
    # 如果只想运行性能测试，取消下面的注释
    # run_performance_tests()