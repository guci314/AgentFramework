"""
语义记忆测试
"""

import unittest

from ..semantic_memory import SemanticMemory
from ..interfaces import Concept


class TestSemanticMemory(unittest.TestCase):
    """语义记忆测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.sm = SemanticMemory()
    
    def test_add_concept(self):
        """测试添加概念"""
        # 创建概念
        concept = Concept(
            id="",
            name="MVC Pattern",
            category="architecture_pattern",
            attributes={
                'components': ['Model', 'View', 'Controller'],
                'purpose': 'Separation of concerns',
                'use_cases': 'Web applications'
            },
            confidence=0.9,
            domain="software_architecture"
        )
        
        # 添加概念
        concept_id = self.sm.add_concept(concept)
        self.assertIsNotNone(concept_id)
        
        # 验证存储
        retrieved = self.sm._get_concept(concept_id)
        self.assertEqual(retrieved.name, "MVC Pattern")
        self.assertEqual(retrieved.confidence, 0.9)
    
    def test_find_patterns(self):
        """测试查找领域模式"""
        domain = "software_patterns"
        
        # 添加多个模式
        patterns = [
            ("Singleton", 0.8),
            ("Factory", 0.9),
            ("Observer", 0.7),
            ("Low Quality Pattern", 0.3)
        ]
        
        for name, confidence in patterns:
            concept = Concept(
                id="",
                name=name,
                category="design_pattern",
                attributes={'type': 'GoF'},
                confidence=confidence,
                domain=domain
            )
            self.sm.add_concept(concept)
        
        # 查找高置信度模式
        found_patterns = self.sm.find_patterns(domain, min_confidence=0.6)
        self.assertEqual(len(found_patterns), 3)
        
        # 验证按置信度排序
        confidences = [p.confidence for p in found_patterns]
        self.assertEqual(confidences, sorted(confidences, reverse=True))
    
    def test_knowledge_graph(self):
        """测试知识图谱构建"""
        # 创建概念网络
        root_concept = Concept(
            id="root",
            name="Programming",
            category="domain",
            attributes={'scope': 'general'}
        )
        root_id = self.sm.add_concept(root_concept)
        
        # 添加子概念
        sub_concepts = []
        for lang in ["Python", "Java", "JavaScript"]:
            sub = Concept(
                id="",
                name=lang,
                category="language",
                attributes={'type': 'programming_language'},
                relationships={'parent': [root_id]}
            )
            sub_id = self.sm.add_concept(sub)
            sub_concepts.append(sub_id)
            
            # 更新根概念的关系
            root_concept.relationships['children'] = sub_concepts
            self.sm._update_concept_storage(root_concept)
        
        # 构建知识图谱
        graph = self.sm.get_knowledge_graph(root_id, depth=2)
        
        self.assertEqual(len(graph['nodes']), 4)  # 1 root + 3 children
        self.assertGreater(len(graph['edges']), 0)
        self.assertEqual(graph['root'], root_id)
    
    def test_update_confidence(self):
        """测试更新概念置信度"""
        # 添加概念
        concept = Concept(
            id="",
            name="Test Pattern",
            category="pattern",
            attributes={},
            confidence=0.5
        )
        concept_id = self.sm.add_concept(concept)
        
        # 增加置信度
        success = self.sm.update_concept_confidence(concept_id, 0.3)
        self.assertTrue(success)
        
        # 验证更新
        updated = self.sm._get_concept(concept_id)
        self.assertAlmostEqual(updated.confidence, 0.8)
        
        # 测试边界条件
        self.sm.update_concept_confidence(concept_id, 0.5)
        updated = self.sm._get_concept(concept_id)
        self.assertAlmostEqual(updated.confidence, 1.0)
    
    def test_merge_concepts(self):
        """测试合并概念"""
        # 创建两个相似概念
        concept1 = Concept(
            id="",
            name="REST API",
            category="api_pattern",
            attributes={
                'methods': ['GET', 'POST', 'PUT', 'DELETE'],
                'stateless': True
            },
            confidence=0.8,
            examples=[{'endpoint': '/users', 'method': 'GET'}]
        )
        
        concept2 = Concept(
            id="",
            name="RESTful Service",
            category="api_pattern",
            attributes={
                'methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
                'stateless': True,
                'hypermedia': True
            },
            confidence=0.9,
            examples=[{'endpoint': '/products', 'method': 'POST'}]
        )
        
        id1 = self.sm.add_concept(concept1)
        id2 = self.sm.add_concept(concept2)
        
        # 合并概念
        merged_id = self.sm.merge_concepts(id1, id2)
        self.assertIsNotNone(merged_id)
        
        # 验证合并结果
        merged = self.sm._get_concept(merged_id)
        self.assertIn("REST", merged.name)
        self.assertEqual(merged.confidence, 0.9)  # 取最大值
        self.assertEqual(len(merged.examples), 2)  # 合并示例
        self.assertIn('PATCH', merged.attributes['methods'])  # 合并属性
        
        # 验证原概念被删除
        self.assertIsNone(self.sm.get(id1))
        self.assertIsNone(self.sm.get(id2))
    
    def test_get_concepts_by_category(self):
        """测试按类别获取概念"""
        # 添加不同类别的概念
        categories = {
            'design_pattern': ['Singleton', 'Factory', 'Observer'],
            'architecture': ['MVC', 'MVP', 'MVVM'],
            'algorithm': ['QuickSort', 'MergeSort']
        }
        
        for category, names in categories.items():
            for name in names:
                concept = Concept(
                    id="",
                    name=name,
                    category=category,
                    attributes={'type': category}
                )
                self.sm.add_concept(concept)
        
        # 获取特定类别
        design_patterns = self.sm.get_concepts_by_category('design_pattern')
        self.assertEqual(len(design_patterns), 3)
        
        algorithms = self.sm.get_concepts_by_category('algorithm')
        self.assertEqual(len(algorithms), 2)
    
    def test_extract_concept_from_examples(self):
        """测试从示例中提取概念"""
        # 准备示例
        examples = [
            {
                'status_code': 404,
                'error': 'Not Found',
                'resource': '/users/123'
            },
            {
                'status_code': 404,
                'error': 'Not Found',
                'resource': '/products/456'
            },
            {
                'status_code': 404,
                'error': 'Not Found',
                'resource': '/orders/789'
            }
        ]
        
        # 提取概念
        concept = self.sm.extract_concept_from_examples(
            examples,
            category='error_pattern',
            domain='http_errors'
        )
        
        self.assertIsNotNone(concept)
        self.assertEqual(concept.attributes['status_code'], 404)
        self.assertEqual(concept.attributes['error'], 'Not Found')
        self.assertIn('varies', concept.attributes['resource'])
    
    def test_calculate_similarity(self):
        """测试概念相似度计算"""
        # 创建相似概念
        concept1 = Concept(
            id="",
            name="Binary Search",
            category="algorithm",
            attributes={
                'complexity': 'O(log n)',
                'type': 'search',
                'requires': 'sorted array'
            },
            domain="algorithms"
        )
        
        concept2 = Concept(
            id="",
            name="Binary Search Tree",
            category="algorithm",
            attributes={
                'complexity': 'O(log n)',
                'type': 'search',
                'structure': 'tree'
            },
            domain="algorithms"
        )
        
        id1 = self.sm.add_concept(concept1)
        id2 = self.sm.add_concept(concept2)
        
        # 计算相似度
        similarity = self.sm.calculate_concept_similarity(id1, id2)
        
        # 应该有较高相似度（相同类别、领域、部分属性）
        self.assertGreater(similarity, 0.5)
        self.assertLess(similarity, 1.0)
    
    def test_find_related_concepts(self):
        """测试查找相关概念"""
        # 创建概念网络
        main_concept = Concept(
            id="main",
            name="Web Framework",
            category="framework",
            attributes={'type': 'web'}
        )
        main_id = self.sm.add_concept(main_concept)
        
        # 添加相关概念
        related_names = ["Django", "Flask", "FastAPI"]
        for name in related_names:
            related = Concept(
                id="",
                name=name,
                category="framework",
                attributes={'language': 'Python'},
                relationships={'implements': [main_id]}
            )
            related_id = self.sm.add_concept(related)
            
            # 建立反向关系
            if 'implementations' not in main_concept.relationships:
                main_concept.relationships['implementations'] = []
            main_concept.relationships['implementations'].append(related_id)
        
        self.sm._update_concept_storage(main_concept)
        
        # 查找相关概念
        implementations = self.sm.find_related_concepts(
            main_id, 
            relationship_type='implementations'
        )
        
        self.assertEqual(len(implementations), 3)
        
        # 查找所有相关
        all_related = self.sm.find_related_concepts(main_id)
        self.assertEqual(len(all_related), 3)


if __name__ == '__main__':
    unittest.main()