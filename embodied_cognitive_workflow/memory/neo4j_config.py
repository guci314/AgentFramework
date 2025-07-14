"""
Neo4j配置管理

提供Neo4j连接配置和管理
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Neo4jConfig:
    """Neo4j连接配置"""
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = "graphiti123!"
    database: str = "neo4j"  # 默认数据库
    
    # 连接池配置
    max_connection_lifetime: int = 3600  # 秒
    max_connection_pool_size: int = 50
    connection_acquisition_timeout: int = 60  # 秒
    
    # 查询超时配置
    query_timeout: int = 30  # 秒
    
    # 索引配置
    create_indexes: bool = True
    
    @classmethod
    def from_env(cls) -> 'Neo4jConfig':
        """从环境变量加载配置"""
        return cls(
            uri=os.getenv("NEO4J_URI", cls.uri),
            username=os.getenv("NEO4J_USERNAME", cls.username),
            password=os.getenv("NEO4J_PASSWORD", cls.password),
            database=os.getenv("NEO4J_DATABASE", cls.database),
            max_connection_lifetime=int(os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", cls.max_connection_lifetime)),
            max_connection_pool_size=int(os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", cls.max_connection_pool_size)),
            connection_acquisition_timeout=int(os.getenv("NEO4J_CONNECTION_ACQUISITION_TIMEOUT", cls.connection_acquisition_timeout)),
            query_timeout=int(os.getenv("NEO4J_QUERY_TIMEOUT", cls.query_timeout)),
            create_indexes=os.getenv("NEO4J_CREATE_INDEXES", "true").lower() == "true"
        )


# 默认配置实例
default_config = Neo4jConfig()


# Cypher查询模板
class CypherQueries:
    """常用Cypher查询模板"""
    
    # 创建概念节点
    CREATE_CONCEPT = """
    CREATE (c:Concept {
        id: $id,
        name: $name,
        category: $category,
        confidence: $confidence,
        domain: $domain,
        attributes: $attributes,
        created_at: datetime(),
        updated_at: datetime()
    })
    RETURN c
    """
    
    # 更新概念
    UPDATE_CONCEPT = """
    MATCH (c:Concept {id: $id})
    SET c.name = $name,
        c.category = $category,
        c.confidence = $confidence,
        c.domain = $domain,
        c.attributes = $attributes,
        c.updated_at = datetime()
    RETURN c
    """
    
    # 获取概念
    GET_CONCEPT = """
    MATCH (c:Concept {id: $id})
    RETURN c
    """
    
    # 删除概念
    DELETE_CONCEPT = """
    MATCH (c:Concept {id: $id})
    DETACH DELETE c
    RETURN count(c) as deleted_count
    """
    
    # 创建关系
    CREATE_RELATIONSHIP = """
    MATCH (c1:Concept {id: $concept_id1}), (c2:Concept {id: $concept_id2})
    CREATE (c1)-[r:%s {
        created_at: datetime()
    }]->(c2)
    RETURN r
    """
    
    # 查找概念按类别
    FIND_BY_CATEGORY = """
    MATCH (c:Concept {category: $category})
    RETURN c
    ORDER BY c.confidence DESC
    """
    
    # 查找概念按领域和置信度
    FIND_BY_DOMAIN = """
    MATCH (c:Concept)
    WHERE c.domain = $domain AND c.confidence >= $min_confidence
    RETURN c
    ORDER BY c.confidence DESC
    """
    
    # 获取知识图谱
    GET_KNOWLEDGE_GRAPH = """
    MATCH path = (c:Concept {id: $root_id})-[*0..%d]-(related)
    RETURN path
    """
    
    # 查找相关概念
    FIND_RELATED = """
    MATCH (c:Concept {id: $concept_id})-[r:%s]-(related:Concept)
    RETURN related, r
    """
    
    # 查找所有相关概念
    FIND_ALL_RELATED = """
    MATCH (c:Concept {id: $concept_id})-[r]-(related:Concept)
    RETURN related, type(r) as relationship_type, properties(r) as relationship_properties
    """
    
    # 合并概念 - 转移关系
    MERGE_CONCEPTS_TRANSFER_RELATIONSHIPS = """
    MATCH (old:Concept {id: $old_id})-[r]-(other:Concept)
    WHERE other.id <> $new_id
    WITH old, r, other, type(r) as rel_type, properties(r) as rel_props
    MATCH (new:Concept {id: $new_id})
    CALL apoc.create.relationship(
        CASE WHEN startNode(r) = old THEN new ELSE other END,
        rel_type,
        rel_props,
        CASE WHEN endNode(r) = old THEN new ELSE other END
    ) YIELD rel
    DELETE r
    RETURN count(rel) as transferred_count
    """
    
    # 计算概念相似度（基于共同邻居）
    CALCULATE_SIMILARITY = """
    MATCH (c1:Concept {id: $concept_id1})-[]-(neighbor:Concept)-[]-(c2:Concept {id: $concept_id2})
    WITH c1, c2, count(distinct neighbor) as common_neighbors
    MATCH (c1)-[]-(n1:Concept)
    WITH c1, c2, common_neighbors, count(distinct n1) as c1_neighbors
    MATCH (c2)-[]-(n2:Concept)
    WITH c1, c2, common_neighbors, c1_neighbors, count(distinct n2) as c2_neighbors
    RETURN c1.id as id1, c2.id as id2,
           common_neighbors,
           c1_neighbors,
           c2_neighbors,
           toFloat(common_neighbors) / (c1_neighbors + c2_neighbors - common_neighbors) as jaccard_similarity
    """
    
    # 全文搜索（需要全文索引）
    FULLTEXT_SEARCH = """
    CALL db.index.fulltext.queryNodes('concept_search', $query)
    YIELD node, score
    RETURN node as c, score
    ORDER BY score DESC
    LIMIT $limit
    """
    
    # 获取统计信息
    GET_STATISTICS = """
    MATCH (c:Concept)
    WITH count(c) as total_concepts,
         avg(c.confidence) as avg_confidence
    MATCH ()-[r]->()
    WITH total_concepts, avg_confidence, count(r) as total_relationships
    MATCH (c:Concept)
    WITH total_concepts, avg_confidence, total_relationships,
         collect(distinct c.category) as categories,
         collect(distinct c.domain) as domains
    RETURN {
        total_concepts: total_concepts,
        total_relationships: total_relationships,
        avg_confidence: avg_confidence,
        categories_count: size(categories),
        domains_count: size(domains),
        categories: categories,
        domains: domains
    } as stats
    """


# 索引创建语句
class IndexQueries:
    """索引创建查询"""
    
    # 创建唯一性约束（自动创建索引）
    CREATE_CONCEPT_ID_CONSTRAINT = """
    CREATE CONSTRAINT concept_id_unique IF NOT EXISTS
    FOR (c:Concept)
    REQUIRE c.id IS UNIQUE
    """
    
    # 创建索引
    CREATE_CATEGORY_INDEX = """
    CREATE INDEX concept_category_index IF NOT EXISTS
    FOR (c:Concept)
    ON (c.category)
    """
    
    CREATE_DOMAIN_INDEX = """
    CREATE INDEX concept_domain_index IF NOT EXISTS
    FOR (c:Concept)
    ON (c.domain)
    """
    
    CREATE_CONFIDENCE_INDEX = """
    CREATE INDEX concept_confidence_index IF NOT EXISTS
    FOR (c:Concept)
    ON (c.confidence)
    """
    
    # 创建全文索引
    CREATE_FULLTEXT_INDEX = """
    CREATE FULLTEXT INDEX concept_search IF NOT EXISTS
    FOR (c:Concept)
    ON EACH [c.name, c.attributes]
    """
    
    # 获取所有索引
    LIST_INDEXES = """
    SHOW INDEXES
    """