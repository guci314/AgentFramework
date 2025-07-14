"""
Neo4j语义记忆实现

使用Neo4j图数据库作为语义记忆的持久化存储
"""

import json
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from neo4j import GraphDatabase, Transaction
from neo4j.exceptions import Neo4jError
import logging

from .interfaces import ISemanticMemory, Concept, MemoryItem
from .semantic_memory import SemanticMemory
from .neo4j_config import Neo4jConfig, CypherQueries, IndexQueries, default_config
from .utils import generate_memory_id, calculate_similarity


logger = logging.getLogger(__name__)


class Neo4jSemanticMemory(ISemanticMemory):
    """Neo4j实现的语义记忆"""
    
    def __init__(self, config: Optional[Neo4jConfig] = None):
        """
        初始化Neo4j语义记忆
        
        Args:
            config: Neo4j配置，默认使用default_config
        """
        self.config = config or default_config
        self.driver = None
        self._connect()
        
        # 创建索引
        if self.config.create_indexes:
            self._create_indexes()
    
    def _connect(self):
        """建立Neo4j连接"""
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password),
                max_connection_lifetime=self.config.max_connection_lifetime,
                max_connection_pool_size=self.config.max_connection_pool_size,
                connection_acquisition_timeout=self.config.connection_acquisition_timeout
            )
            # 验证连接
            self.driver.verify_connectivity()
            logger.info(f"Successfully connected to Neo4j at {self.config.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def _create_indexes(self):
        """创建必要的索引"""
        with self.driver.session(database=self.config.database) as session:
            try:
                # 创建约束和索引
                session.run(IndexQueries.CREATE_CONCEPT_ID_CONSTRAINT)
                session.run(IndexQueries.CREATE_CATEGORY_INDEX)
                session.run(IndexQueries.CREATE_DOMAIN_INDEX)
                session.run(IndexQueries.CREATE_CONFIDENCE_INDEX)
                session.run(IndexQueries.CREATE_FULLTEXT_INDEX)
                logger.info("Neo4j indexes created successfully")
            except Neo4jError as e:
                logger.warning(f"Error creating indexes (may already exist): {e}")
    
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def __del__(self):
        """析构函数，确保连接关闭"""
        self.close()
    
    # 实现IMemory接口方法
    
    def store(self, key: str, content: Any, metadata: Dict[str, Any] = None) -> str:
        """存储记忆项（将被add_concept覆盖）"""
        # 创建概念对象
        concept = Concept(
            id=key or generate_memory_id("concept"),
            name=str(content)[:100],  # 使用内容的前100个字符作为名称
            category=metadata.get('category', 'general'),
            attributes={'content': content, **metadata} if metadata else {'content': content},
            confidence=metadata.get('confidence', 0.5) if metadata else 0.5,
            domain=metadata.get('domain')
        )
        return self.add_concept(concept)
    
    def recall(self, query: str, limit: int = 10, **kwargs) -> List[MemoryItem]:
        """检索记忆"""
        with self.driver.session(database=self.config.database) as session:
            try:
                # 使用全文搜索
                # 直接使用查询字符串，避免参数名冲突
                query_text = CypherQueries.FULLTEXT_SEARCH
                result = session.run(query_text, {"query": query, "limit": limit})
                
                memory_items = []
                for record in result:
                    concept_node = record['c']
                    concept = self._node_to_concept(concept_node)
                    memory_items.append(concept.to_memory_item())
                
                return memory_items
            except Neo4jError:
                # 如果全文搜索失败，回退到基于属性的搜索
                logger.warning("Fulltext search failed, falling back to property search")
                return self._recall_by_property(query, limit)
    
    def _recall_by_property(self, query: str, limit: int) -> List[MemoryItem]:
        """基于属性的备用搜索"""
        with self.driver.session(database=self.config.database) as session:
            # 搜索名称包含查询词的概念
            result = session.run("""
                MATCH (c:Concept)
                WHERE toLower(c.name) CONTAINS toLower($query)
                   OR toLower(c.attributes) CONTAINS toLower($query)
                RETURN c
                ORDER BY c.confidence DESC
                LIMIT $limit
            """, query=query, limit=limit)
            
            memory_items = []
            for record in result:
                concept = self._node_to_concept(record['c'])
                memory_items.append(concept.to_memory_item())
            
            return memory_items
    
    def forget(self, key: str) -> bool:
        """删除记忆"""
        with self.driver.session(database=self.config.database) as session:
            result = session.run(CypherQueries.DELETE_CONCEPT, id=key)
            deleted_count = result.single()['deleted_count']
            return deleted_count > 0
    
    def update(self, key: str, content: Any, metadata: Dict[str, Any] = None) -> bool:
        """更新记忆"""
        concept = self._get_concept(key)
        if not concept:
            return False
        
        # 更新概念属性
        concept.attributes.update({'content': content})
        if metadata:
            concept.attributes.update(metadata)
            if 'confidence' in metadata:
                concept.confidence = metadata['confidence']
            if 'domain' in metadata:
                concept.domain = metadata['domain']
        
        # 保存更新
        return self._update_concept(concept)
    
    def exists(self, key: str) -> bool:
        """检查记忆是否存在"""
        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                "MATCH (c:Concept {id: $id}) RETURN count(c) as count",
                id=key
            )
            return result.single()['count'] > 0
    
    def get(self, key: str) -> Optional[MemoryItem]:
        """获取单个记忆项"""
        concept = self._get_concept(key)
        return concept.to_memory_item() if concept else None
    
    def list_all(self, limit: int = 100, offset: int = 0) -> List[MemoryItem]:
        """列出所有记忆项"""
        with self.driver.session(database=self.config.database) as session:
            result = session.run("""
                MATCH (c:Concept)
                RETURN c
                ORDER BY c.created_at DESC
                SKIP $offset
                LIMIT $limit
            """, offset=offset, limit=limit)
            
            memory_items = []
            for record in result:
                concept = self._node_to_concept(record['c'])
                memory_items.append(concept.to_memory_item())
            
            return memory_items
    
    def clear(self) -> int:
        """清空所有记忆"""
        with self.driver.session(database=self.config.database) as session:
            # 先获取总数
            count_result = session.run("MATCH (c:Concept) RETURN count(c) as total")
            total = count_result.single()['total']
            
            # 然后删除所有节点
            session.run("MATCH (c:Concept) DETACH DELETE c")
            return total
    
    def size(self) -> int:
        """获取记忆项数量"""
        with self.driver.session(database=self.config.database) as session:
            result = session.run("MATCH (c:Concept) RETURN count(c) as count")
            return result.single()['count']
    
    # 实现ISemanticMemory接口方法
    
    def add_concept(self, concept: Concept) -> str:
        """添加概念知识"""
        if not concept.id:
            concept.id = generate_memory_id("concept")
        
        with self.driver.session(database=self.config.database) as session:
            # 创建节点
            result = session.run(
                CypherQueries.CREATE_CONCEPT,
                id=concept.id,
                name=concept.name,
                category=concept.category,
                confidence=concept.confidence,
                domain=concept.domain or "",
                attributes=json.dumps(concept.attributes)
            )
            
            # 创建关系
            if concept.relationships:
                self._create_relationships(session, concept.id, concept.relationships)
            
            logger.info(f"Created concept: {concept.id}")
            return concept.id
    
    def find_patterns(self, domain: str, min_confidence: float = 0.5) -> List[Concept]:
        """查找领域模式"""
        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                CypherQueries.FIND_BY_DOMAIN,
                domain=domain,
                min_confidence=min_confidence
            )
            
            concepts = []
            for record in result:
                concept = self._node_to_concept(record['c'])
                concepts.append(concept)
            
            return concepts
    
    def get_knowledge_graph(self, root_concept: str, depth: int = 2) -> Dict[str, Any]:
        """获取知识图谱"""
        with self.driver.session(database=self.config.database) as session:
            query = CypherQueries.GET_KNOWLEDGE_GRAPH % depth
            result = session.run(query, root_id=root_concept)
            
            # 构建图谱数据结构
            nodes = {}
            edges = []
            
            for record in result:
                path = record['path']
                
                # 提取节点
                for node in path.nodes:
                    if node['id'] not in nodes:
                        nodes[node['id']] = {
                            'id': node['id'],
                            'name': node['name'],
                            'category': node['category'],
                            'confidence': node['confidence'],
                            'attributes': json.loads(node['attributes']) if isinstance(node['attributes'], str) else node['attributes']
                        }
                
                # 提取边
                for rel in path.relationships:
                    edge = {
                        'source': rel.start_node['id'],
                        'target': rel.end_node['id'],
                        'type': rel.type,
                        'properties': dict(rel)
                    }
                    # 避免重复边
                    if edge not in edges:
                        edges.append(edge)
            
            return {
                'nodes': list(nodes.values()),
                'edges': edges,
                'root': root_concept
            }
    
    def update_concept_confidence(self, concept_id: str, confidence_delta: float) -> bool:
        """更新概念置信度"""
        with self.driver.session(database=self.config.database) as session:
            result = session.run("""
                MATCH (c:Concept {id: $id})
                SET c.confidence = CASE
                    WHEN c.confidence + $delta > 1.0 THEN 1.0
                    WHEN c.confidence + $delta < 0.0 THEN 0.0
                    ELSE c.confidence + $delta
                END,
                c.updated_at = datetime()
                RETURN c
            """, id=concept_id, delta=confidence_delta)
            
            return result.single() is not None
    
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
            category=concept1.category,
            attributes=self._merge_attributes(concept1.attributes, concept2.attributes),
            confidence=max(concept1.confidence, concept2.confidence),
            examples=concept1.examples + concept2.examples,
            domain=concept1.domain or concept2.domain
        )
        
        # 添加合并后的概念
        merged_id = self.add_concept(merged_concept)
        
        with self.driver.session(database=self.config.database) as session:
            # 转移所有关系到新概念
            for old_id in [concept_id1, concept_id2]:
                # 获取所有关系
                rels = session.run("""
                    MATCH (old:Concept {id: $old_id})-[r]-(other:Concept)
                    WHERE other.id <> $new_id
                    RETURN type(r) as rel_type, 
                           properties(r) as props,
                           other.id as other_id,
                           startNode(r).id = $old_id as is_outgoing
                """, old_id=old_id, new_id=merged_id)
                
                # 创建新关系
                for record in rels:
                    if record['is_outgoing']:
                        session.run(f"""
                            MATCH (new:Concept {{id: $new_id}}), (other:Concept {{id: $other_id}})
                            CREATE (new)-[:{record['rel_type']}]->(other)
                        """, new_id=merged_id, other_id=record['other_id'])
                    else:
                        session.run(f"""
                            MATCH (new:Concept {{id: $new_id}}), (other:Concept {{id: $other_id}})
                            CREATE (other)-[:{record['rel_type']}]->(new)
                        """, new_id=merged_id, other_id=record['other_id'])
            
            # 删除原概念
            session.run("MATCH (c:Concept) WHERE c.id IN $ids DETACH DELETE c",
                       ids=[concept_id1, concept_id2])
        
        logger.info(f"Merged concepts {concept_id1} and {concept_id2} into {merged_id}")
        return merged_id
    
    def get_concepts_by_category(self, category: str) -> List[Concept]:
        """按类别获取概念"""
        with self.driver.session(database=self.config.database) as session:
            result = session.run(CypherQueries.FIND_BY_CATEGORY, category=category)
            
            concepts = []
            for record in result:
                concept = self._node_to_concept(record['c'])
                concepts.append(concept)
            
            return concepts
    
    # Neo4j特有方法
    
    def find_related_concepts(self, concept_id: str, relationship_type: Optional[str] = None) -> List[Tuple[str, Concept]]:
        """查找相关概念"""
        with self.driver.session(database=self.config.database) as session:
            if relationship_type:
                query = CypherQueries.FIND_RELATED % relationship_type
                result = session.run(query, concept_id=concept_id)
            else:
                result = session.run(
                    CypherQueries.FIND_ALL_RELATED,
                    concept_id=concept_id
                )
            
            related = []
            for record in result:
                concept = self._node_to_concept(record['related'])
                rel_type = record.get('relationship_type', relationship_type)
                related.append((rel_type, concept))
            
            return related
    
    def calculate_concept_similarity(self, concept_id1: str, concept_id2: str) -> float:
        """计算两个概念的相似度（基于图结构）"""
        with self.driver.session(database=self.config.database) as session:
            # 使用Jaccard相似度（基于共同邻居）
            result = session.run(
                CypherQueries.CALCULATE_SIMILARITY,
                concept_id1=concept_id1,
                concept_id2=concept_id2
            )
            
            record = result.single()
            if record and record['jaccard_similarity'] is not None:
                return float(record['jaccard_similarity'])
            
            # 如果没有共同邻居，使用属性相似度
            concept1 = self._get_concept(concept_id1)
            concept2 = self._get_concept(concept_id2)
            
            if concept1 and concept2:
                # 简单的文本相似度
                text1 = f"{concept1.name} {json.dumps(concept1.attributes)}"
                text2 = f"{concept2.name} {json.dumps(concept2.attributes)}"
                return calculate_similarity(text1, text2)
            
            return 0.0
    
    def create_relationship(self, concept_id1: str, concept_id2: str, 
                          relationship_type: str, properties: Dict[str, Any] = None) -> bool:
        """创建概念间的关系"""
        with self.driver.session(database=self.config.database) as session:
            try:
                # 如果有自定义属性，需要特殊处理
                if properties:
                    # 构建带属性的查询
                    props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
                    query = f"""
                    MATCH (c1:Concept {{id: $concept_id1}}), (c2:Concept {{id: $concept_id2}})
                    CREATE (c1)-[r:{relationship_type} {{
                        created_at: datetime(),
                        {props_str}
                    }}]->(c2)
                    RETURN r
                    """
                    params = {"concept_id1": concept_id1, "concept_id2": concept_id2}
                    params.update(properties)
                    session.run(query, params)
                else:
                    # 使用默认查询
                    query = CypherQueries.CREATE_RELATIONSHIP % relationship_type
                    session.run(
                        query,
                        concept_id1=concept_id1,
                        concept_id2=concept_id2
                    )
                return True
            except Neo4jError as e:
                logger.error(f"Failed to create relationship: {e}")
                return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.driver.session(database=self.config.database) as session:
            result = session.run(CypherQueries.GET_STATISTICS)
            record = result.single()
            
            if not record:
                return {
                    'total_concepts': 0,
                    'total_relationships': 0,
                    'avg_confidence': 0.0,
                    'categories_count': 0,
                    'domains_count': 0,
                    'categories': [],
                    'domains': []
                }
            
            stats = record['stats']
            
            # 转换Neo4j类型为Python类型
            return {
                'total_concepts': int(stats['total_concepts']) if stats['total_concepts'] else 0,
                'total_relationships': int(stats['total_relationships']) if stats['total_relationships'] else 0,
                'avg_confidence': float(stats['avg_confidence']) if stats['avg_confidence'] else 0.0,
                'categories_count': int(stats['categories_count']) if stats['categories_count'] else 0,
                'domains_count': int(stats['domains_count']) if stats['domains_count'] else 0,
                'categories': list(stats['categories']) if stats['categories'] else [],
                'domains': list(stats['domains']) if stats['domains'] else []
            }
    
    # 辅助方法
    
    def _get_concept(self, concept_id: str) -> Optional[Concept]:
        """获取概念对象"""
        with self.driver.session(database=self.config.database) as session:
            result = session.run(CypherQueries.GET_CONCEPT, id=concept_id)
            record = result.single()
            
            if record:
                concept_node = record['c']
                # 获取关系
                relationships = self._get_concept_relationships(session, concept_id)
                return self._node_to_concept(concept_node, relationships)
            
            return None
    
    def _node_to_concept(self, node: Dict[str, Any], relationships: Dict[str, List[str]] = None) -> Concept:
        """将Neo4j节点转换为Concept对象"""
        attributes = node.get('attributes', '{}')
        if isinstance(attributes, str):
            attributes = json.loads(attributes)
        
        return Concept(
            id=node['id'],
            name=node['name'],
            category=node['category'],
            attributes=attributes,
            relationships=relationships or {},
            confidence=float(node['confidence']),
            examples=[],  # 示例可以从属性中提取
            domain=node.get('domain') if node.get('domain') else None
        )
    
    def _update_concept(self, concept: Concept) -> bool:
        """更新概念"""
        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                CypherQueries.UPDATE_CONCEPT,
                id=concept.id,
                name=concept.name,
                category=concept.category,
                confidence=concept.confidence,
                domain=concept.domain or "",
                attributes=json.dumps(concept.attributes)
            )
            
            return result.single() is not None
    
    def _create_relationships(self, session: Any, concept_id: str, relationships: Dict[str, List[str]]):
        """创建概念的所有关系"""
        for rel_type, target_ids in relationships.items():
            for target_id in target_ids:
                try:
                    query = f"""
                    MATCH (c1:Concept {{id: $concept_id}}), (c2:Concept {{id: $target_id}})
                    CREATE (c1)-[:{rel_type}]->(c2)
                    """
                    session.run(query, concept_id=concept_id, target_id=target_id)
                except Neo4jError as e:
                    logger.warning(f"Failed to create relationship {rel_type} to {target_id}: {e}")
    
    def _get_concept_relationships(self, session: Any, concept_id: str) -> Dict[str, List[str]]:
        """获取概念的所有关系"""
        result = session.run("""
            MATCH (c:Concept {id: $concept_id})-[r]->(target:Concept)
            RETURN type(r) as rel_type, collect(target.id) as target_ids
        """, concept_id=concept_id)
        
        relationships = {}
        for record in result:
            relationships[record['rel_type']] = list(record['target_ids'])
        
        return relationships
    
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