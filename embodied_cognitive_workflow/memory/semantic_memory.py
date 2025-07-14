"""
语义记忆实现

实现了概念知识存储、模式识别和知识图谱构建
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict
import json

from .interfaces import ISemanticMemory, Concept, MemoryItem
from .base_memory import BaseMemory, InMemoryStorage
from .utils import calculate_similarity, generate_memory_id


class SemanticMemory(BaseMemory, ISemanticMemory):
    """语义记忆实现"""
    
    def __init__(self, storage: Optional[InMemoryStorage] = None):
        """
        初始化语义记忆
        
        Args:
            storage: 存储策略，默认使用内存存储
        """
        super().__init__(storage or InMemoryStorage())
        
        # 类别索引：类别 -> 概念ID列表
        self._category_index: Dict[str, List[str]] = defaultdict(list)
        
        # 领域索引：领域 -> 概念ID列表
        self._domain_index: Dict[str, List[str]] = defaultdict(list)
        
        # 关系索引：用于快速查找关系
        self._relationship_index: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        
        # 概念对象缓存
        self._concept_cache: Dict[str, Concept] = {}
    
    def add_concept(self, concept: Concept) -> str:
        """添加概念知识"""
        # 如果没有ID，生成一个
        if not concept.id:
            concept.id = generate_memory_id("concept")
        
        # 转换为记忆项并存储
        memory_item = concept.to_memory_item()
        self.storage.put(concept.id, memory_item)
        
        # 更新缓存
        self._concept_cache[concept.id] = concept
        
        # 更新索引
        self._update_indices(concept)
        
        return concept.id
    
    def find_patterns(self, domain: str, min_confidence: float = 0.5) -> List[Concept]:
        """查找领域模式"""
        # 获取领域内的所有概念
        concept_ids = self._domain_index.get(domain, [])
        concepts = []
        
        for cid in concept_ids:
            concept = self._get_concept(cid)
            if concept and concept.confidence >= min_confidence:
                concepts.append(concept)
        
        # 按置信度排序
        concepts.sort(key=lambda c: c.confidence, reverse=True)
        
        return concepts
    
    def get_knowledge_graph(self, root_concept: str, depth: int = 2) -> Dict[str, Any]:
        """获取知识图谱"""
        visited = set()
        graph = {
            'nodes': [],
            'edges': [],
            'root': root_concept
        }
        
        # 深度优先遍历构建图谱
        self._build_knowledge_graph(root_concept, depth, visited, graph)
        
        return graph
    
    def update_concept_confidence(self, concept_id: str, confidence_delta: float) -> bool:
        """更新概念置信度"""
        concept = self._get_concept(concept_id)
        if not concept:
            return False
        
        # 更新置信度
        concept.confidence = max(0.0, min(1.0, concept.confidence + confidence_delta))
        
        # 更新存储
        self._update_concept_storage(concept)
        
        return True
    
    def merge_concepts(self, concept_id1: str, concept_id2: str) -> Optional[str]:
        """合并两个相似概念"""
        concept1 = self._get_concept(concept_id1)
        concept2 = self._get_concept(concept_id2)
        
        if not concept1 or not concept2:
            return None
        
        # 创建合并后的概念
        merged_concept = Concept(
            id=generate_memory_id("merged"),
            name=f"{concept1.name} / {concept2.name}",
            category=concept1.category,  # 使用第一个概念的类别
            attributes=self._merge_attributes(concept1.attributes, concept2.attributes),
            relationships=self._merge_relationships(concept1.relationships, concept2.relationships),
            confidence=max(concept1.confidence, concept2.confidence),
            examples=concept1.examples + concept2.examples,
            domain=concept1.domain or concept2.domain
        )
        
        # 添加合并后的概念
        merged_id = self.add_concept(merged_concept)
        
        # 更新所有指向原概念的关系
        self._redirect_relationships(concept_id1, merged_id)
        self._redirect_relationships(concept_id2, merged_id)
        
        # 删除原概念
        self.forget(concept_id1)
        self.forget(concept_id2)
        
        return merged_id
    
    def get_concepts_by_category(self, category: str) -> List[Concept]:
        """按类别获取概念"""
        concept_ids = self._category_index.get(category, [])
        concepts = []
        
        for cid in concept_ids:
            concept = self._get_concept(cid)
            if concept:
                concepts.append(concept)
        
        return concepts
    
    def find_related_concepts(self, concept_id: str, relationship_type: Optional[str] = None) -> List[Tuple[str, Concept]]:
        """查找相关概念"""
        concept = self._get_concept(concept_id)
        if not concept:
            return []
        
        related = []
        
        if relationship_type:
            # 获取特定类型的关系
            related_ids = concept.relationships.get(relationship_type, [])
            for rid in related_ids:
                related_concept = self._get_concept(rid)
                if related_concept:
                    related.append((relationship_type, related_concept))
        else:
            # 获取所有关系
            for rel_type, related_ids in concept.relationships.items():
                for rid in related_ids:
                    related_concept = self._get_concept(rid)
                    if related_concept:
                        related.append((rel_type, related_concept))
        
        return related
    
    def extract_concept_from_examples(self, examples: List[Dict[str, Any]], 
                                    category: str, domain: Optional[str] = None) -> Optional[Concept]:
        """从示例中提取概念"""
        if len(examples) < 3:
            return None
        
        # 提取共同属性
        common_attributes = {}
        all_keys = set()
        
        # 收集所有键
        for example in examples:
            if isinstance(example, dict):
                all_keys.update(example.keys())
        
        # 查找共同属性
        for key in all_keys:
            values = []
            for example in examples:
                if isinstance(example, dict) and key in example:
                    values.append(example[key])
            
            # 如果大多数示例都有这个属性
            if len(values) >= len(examples) * 0.7:
                # 如果值都相同，作为固定属性
                if len(set(str(v) for v in values)) == 1:
                    common_attributes[key] = values[0]
                else:
                    # 否则记录为可变属性
                    common_attributes[key] = f"varies: {', '.join(set(str(v) for v in values[:3]))}"
        
        # 生成概念名称
        concept_name = f"{category}_pattern_{len(self._category_index[category])}"
        
        # 创建概念
        concept = Concept(
            id=generate_memory_id("extracted"),
            name=concept_name,
            category=category,
            attributes=common_attributes,
            confidence=len(examples) / 10.0,  # 基于示例数量的初始置信度
            examples=examples[:5],  # 保留最多5个示例
            domain=domain
        )
        
        return concept
    
    def calculate_concept_similarity(self, concept_id1: str, concept_id2: str) -> float:
        """计算两个概念的相似度"""
        concept1 = self._get_concept(concept_id1)
        concept2 = self._get_concept(concept_id2)
        
        if not concept1 or not concept2:
            return 0.0
        
        similarity_score = 0.0
        
        # 类别相似度
        if concept1.category == concept2.category:
            similarity_score += 0.3
        
        # 领域相似度
        if concept1.domain == concept2.domain and concept1.domain is not None:
            similarity_score += 0.2
        
        # 属性相似度
        attr_similarity = self._calculate_attribute_similarity(
            concept1.attributes, concept2.attributes
        )
        similarity_score += attr_similarity * 0.3
        
        # 关系相似度
        rel_similarity = self._calculate_relationship_similarity(
            concept1.relationships, concept2.relationships
        )
        similarity_score += rel_similarity * 0.2
        
        return min(1.0, similarity_score)
    
    def _get_concept(self, concept_id: str) -> Optional[Concept]:
        """获取概念对象"""
        # 先检查缓存
        if concept_id in self._concept_cache:
            return self._concept_cache[concept_id]
        
        # 从存储获取
        item = self.get(concept_id)
        if item and item.metadata.get('type') == 'concept':
            # 重建概念对象
            concept = Concept(
                id=item.id,
                name=item.content.get('name', ''),
                category=item.metadata.get('category', ''),
                attributes=item.content.get('attributes', {}),
                relationships=item.metadata.get('relationships', {}),
                confidence=item.metadata.get('confidence', 0.5),
                examples=item.content.get('examples', []),
                domain=item.metadata.get('domain')
            )
            
            # 更新缓存
            self._concept_cache[concept_id] = concept
            return concept
        
        return None
    
    def _update_indices(self, concept: Concept) -> None:
        """更新各种索引"""
        # 更新类别索引
        self._category_index[concept.category].append(concept.id)
        
        # 更新领域索引
        if concept.domain:
            self._domain_index[concept.domain].append(concept.id)
        
        # 更新关系索引
        for rel_type, related_ids in concept.relationships.items():
            for related_id in related_ids:
                self._relationship_index[concept.id][rel_type].add(related_id)
    
    def _update_concept_storage(self, concept: Concept) -> None:
        """更新概念的存储"""
        memory_item = concept.to_memory_item()
        self.storage.put(concept.id, memory_item)
    
    def _build_knowledge_graph(self, concept_id: str, depth: int, 
                             visited: Set[str], graph: Dict[str, Any]) -> None:
        """递归构建知识图谱"""
        if depth <= 0 or concept_id in visited:
            return
        
        visited.add(concept_id)
        
        concept = self._get_concept(concept_id)
        if not concept:
            return
        
        # 添加节点
        graph['nodes'].append({
            'id': concept.id,
            'name': concept.name,
            'category': concept.category,
            'confidence': concept.confidence,
            'attributes': concept.attributes
        })
        
        # 添加边并递归
        for rel_type, related_ids in concept.relationships.items():
            for related_id in related_ids:
                # 添加边
                graph['edges'].append({
                    'source': concept.id,
                    'target': related_id,
                    'type': rel_type
                })
                
                # 递归构建
                self._build_knowledge_graph(related_id, depth - 1, visited, graph)
    
    def _merge_attributes(self, attrs1: Dict[str, Any], attrs2: Dict[str, Any]) -> Dict[str, Any]:
        """合并两个属性字典"""
        merged = attrs1.copy()
        
        for key, value in attrs2.items():
            if key not in merged:
                merged[key] = value
            elif merged[key] != value:
                # 如果值不同，创建一个列表
                if not isinstance(merged[key], list):
                    merged[key] = [merged[key]]
                if value not in merged[key]:
                    merged[key].append(value)
        
        return merged
    
    def _merge_relationships(self, rels1: Dict[str, List[str]], 
                           rels2: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """合并两个关系字典"""
        merged = defaultdict(list)
        
        # 合并第一个字典
        for rel_type, related_ids in rels1.items():
            merged[rel_type].extend(related_ids)
        
        # 合并第二个字典
        for rel_type, related_ids in rels2.items():
            for rid in related_ids:
                if rid not in merged[rel_type]:
                    merged[rel_type].append(rid)
        
        return dict(merged)
    
    def _redirect_relationships(self, old_id: str, new_id: str) -> None:
        """重定向所有指向旧概念的关系到新概念"""
        # 遍历所有概念，更新它们的关系
        for item in self.list_all():
            concept = self._get_concept(item.id)
            if concept:
                updated = False
                for rel_type, related_ids in concept.relationships.items():
                    if old_id in related_ids:
                        # 替换旧ID为新ID
                        idx = related_ids.index(old_id)
                        related_ids[idx] = new_id
                        updated = True
                
                if updated:
                    self._update_concept_storage(concept)
    
    def _calculate_attribute_similarity(self, attrs1: Dict[str, Any], 
                                      attrs2: Dict[str, Any]) -> float:
        """计算属性相似度"""
        if not attrs1 and not attrs2:
            return 1.0
        if not attrs1 or not attrs2:
            return 0.0
        
        all_keys = set(attrs1.keys()) | set(attrs2.keys())
        if not all_keys:
            return 0.0
        
        common_keys = set(attrs1.keys()) & set(attrs2.keys())
        
        # 计算共同属性的值相似度
        value_similarity = 0.0
        for key in common_keys:
            if attrs1[key] == attrs2[key]:
                value_similarity += 1.0
            else:
                # 简单的字符串相似度
                str_sim = calculate_similarity(str(attrs1[key]), str(attrs2[key]))
                value_similarity += str_sim
        
        # 综合考虑键的重叠和值的相似度
        key_overlap = len(common_keys) / len(all_keys)
        value_score = value_similarity / len(common_keys) if common_keys else 0
        
        return (key_overlap + value_score) / 2
    
    def _calculate_relationship_similarity(self, rels1: Dict[str, List[str]], 
                                         rels2: Dict[str, List[str]]) -> float:
        """计算关系相似度"""
        if not rels1 and not rels2:
            return 1.0
        if not rels1 or not rels2:
            return 0.0
        
        all_types = set(rels1.keys()) | set(rels2.keys())
        common_types = set(rels1.keys()) & set(rels2.keys())
        
        if not all_types:
            return 0.0
        
        # 计算关系类型的重叠
        type_overlap = len(common_types) / len(all_types)
        
        return type_overlap