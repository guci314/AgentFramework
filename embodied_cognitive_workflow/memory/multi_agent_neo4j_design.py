#!/usr/bin/env python
"""
多Agent共享Neo4j的设计方案
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from neo4j_config import Neo4jConfig
from semantic_memory_neo4j import Neo4jSemanticMemory


# ========== 方案1: 使用标签隔离 ==========
class LabelBasedMultiAgentMemory(Neo4jSemanticMemory):
    """基于标签的多Agent记忆隔离"""
    
    def __init__(self, config: Neo4jConfig, agent_id: str):
        super().__init__(config)
        self.agent_id = agent_id
        self.agent_label = f"Agent_{agent_id}"
    
    def add_concept(self, concept: 'Concept') -> str:
        """添加概念时加上Agent标签"""
        concept_id = super().add_concept(concept)
        
        # 为节点添加Agent标签
        with self.driver.session(database=self.config.database) as session:
            session.run(
                f"MATCH (c:Concept {{id: $id}}) "
                f"SET c:{self.agent_label}",
                id=concept_id
            )
        
        return concept_id
    
    def recall(self, query: str, limit: int = 10, **kwargs) -> List['MemoryItem']:
        """只召回属于当前Agent的记忆"""
        # 修改查询以只返回带有Agent标签的节点
        query_with_label = f"""
        MATCH (c:Concept:{self.agent_label})
        WHERE c.content CONTAINS $query
        RETURN c
        LIMIT $limit
        """
        # ... 执行查询


# ========== 方案2: 使用属性隔离 ==========
class PropertyBasedMultiAgentMemory(Neo4jSemanticMemory):
    """基于属性的多Agent记忆隔离"""
    
    def __init__(self, config: Neo4jConfig, agent_id: str):
        super().__init__(config)
        self.agent_id = agent_id
    
    def add_concept(self, concept: 'Concept') -> str:
        """添加概念时设置agent_id属性"""
        # 在metadata中添加agent_id
        concept.metadata['agent_id'] = self.agent_id
        return super().add_concept(concept)
    
    def recall(self, query: str, limit: int = 10, **kwargs) -> List['MemoryItem']:
        """只召回属于当前Agent的记忆"""
        # 添加agent_id过滤条件
        results = super().recall(query, limit, **kwargs)
        return [r for r in results if r.metadata.get('agent_id') == self.agent_id]


# ========== 方案3: 使用子图隔离 ==========
class SubgraphBasedMultiAgentMemory(Neo4jSemanticMemory):
    """基于子图的多Agent记忆隔离"""
    
    def __init__(self, config: Neo4jConfig, agent_id: str):
        super().__init__(config)
        self.agent_id = agent_id
        self._ensure_agent_root_node()
    
    def _ensure_agent_root_node(self):
        """确保Agent根节点存在"""
        with self.driver.session(database=self.config.database) as session:
            session.run(
                """
                MERGE (a:AgentRoot {id: $agent_id})
                SET a.created_at = coalesce(a.created_at, datetime())
                """,
                agent_id=self.agent_id
            )
    
    def add_concept(self, concept: 'Concept') -> str:
        """添加概念并连接到Agent根节点"""
        concept_id = super().add_concept(concept)
        
        # 将概念连接到Agent根节点
        with self.driver.session(database=self.config.database) as session:
            session.run(
                """
                MATCH (a:AgentRoot {id: $agent_id})
                MATCH (c:Concept {id: $concept_id})
                MERGE (a)-[:OWNS]->(c)
                """,
                agent_id=self.agent_id,
                concept_id=concept_id
            )
        
        return concept_id


# ========== 方案4: 使用数据库隔离 ==========
class DatabaseBasedMultiAgentMemory(Neo4jSemanticMemory):
    """基于数据库的多Agent记忆隔离（Neo4j 4.0+支持多数据库）"""
    
    def __init__(self, config: Neo4jConfig, agent_id: str):
        # 为每个Agent创建独立的数据库
        config.database = f"agent_{agent_id}"
        super().__init__(config)
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """确保Agent数据库存在"""
        with self.driver.session(database="system") as session:
            # 检查数据库是否存在
            result = session.run(
                "SHOW DATABASES WHERE name = $db_name",
                db_name=self.config.database
            )
            
            if not result.single():
                # 创建新数据库
                session.run(f"CREATE DATABASE {self.config.database}")


# ========== 方案5: 混合方案 - 推荐 ==========
@dataclass
class AgentMemoryConfig:
    """Agent记忆配置"""
    agent_id: str
    agent_type: str  # 'personal', 'shared', 'system'
    access_level: str  # 'private', 'team', 'public'
    team_id: Optional[str] = None


class HybridMultiAgentMemory(Neo4jSemanticMemory):
    """混合多Agent记忆系统 - 支持私有和共享记忆"""
    
    def __init__(self, config: Neo4jConfig, agent_config: AgentMemoryConfig):
        super().__init__(config)
        self.agent_config = agent_config
        self._ensure_agent_node()
    
    def _ensure_agent_node(self):
        """确保Agent节点存在"""
        with self.driver.session(database=self.config.database) as session:
            session.run(
                """
                MERGE (a:Agent {id: $agent_id})
                SET a.type = $agent_type,
                    a.access_level = $access_level,
                    a.team_id = $team_id,
                    a.created_at = coalesce(a.created_at, datetime())
                """,
                agent_id=self.agent_config.agent_id,
                agent_type=self.agent_config.agent_type,
                access_level=self.agent_config.access_level,
                team_id=self.agent_config.team_id
            )
    
    def add_concept(self, concept: 'Concept', 
                   visibility: str = 'private') -> str:
        """添加概念并设置可见性"""
        concept_id = super().add_concept(concept)
        
        with self.driver.session(database=self.config.database) as session:
            # 创建所有权关系
            session.run(
                """
                MATCH (a:Agent {id: $agent_id})
                MATCH (c:Concept {id: $concept_id})
                MERGE (a)-[r:OWNS]->(c)
                SET r.visibility = $visibility,
                    r.created_at = datetime()
                """,
                agent_id=self.agent_config.agent_id,
                concept_id=concept_id,
                visibility=visibility
            )
            
            # 如果是团队共享，创建团队访问关系
            if visibility == 'team' and self.agent_config.team_id:
                session.run(
                    """
                    MATCH (t:Team {id: $team_id})
                    MATCH (c:Concept {id: $concept_id})
                    MERGE (t)-[:CAN_ACCESS]->(c)
                    """,
                    team_id=self.agent_config.team_id,
                    concept_id=concept_id
                )
        
        return concept_id
    
    def recall(self, query: str, limit: int = 10, 
              include_shared: bool = True, **kwargs) -> List['MemoryItem']:
        """召回记忆，可选择是否包含共享记忆"""
        
        if include_shared and self.agent_config.team_id:
            # 包含私有和团队共享的记忆
            cypher = """
            MATCH (c:Concept)
            WHERE (
                EXISTS((a:Agent {id: $agent_id})-[:OWNS]->(c))
                OR EXISTS((t:Team {id: $team_id})-[:CAN_ACCESS]->(c))
            )
            AND c.content CONTAINS $query
            RETURN c
            ORDER BY c.importance DESC
            LIMIT $limit
            """
            params = {
                'agent_id': self.agent_config.agent_id,
                'team_id': self.agent_config.team_id,
                'query': query,
                'limit': limit
            }
        else:
            # 只返回私有记忆
            cypher = """
            MATCH (a:Agent {id: $agent_id})-[:OWNS]->(c:Concept)
            WHERE c.content CONTAINS $query
            RETURN c
            ORDER BY c.importance DESC
            LIMIT $limit
            """
            params = {
                'agent_id': self.agent_config.agent_id,
                'query': query,
                'limit': limit
            }
        
        # 执行查询并返回结果
        # ...


# ========== 使用示例 ==========
def demo_multi_agent_setup():
    """演示多Agent设置"""
    
    # Neo4j配置（所有Agent共享）
    neo4j_config = Neo4jConfig(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="graphiti123!"
    )
    
    # 创建不同的Agent记忆系统
    agents = []
    
    # Agent 1: 研发团队成员
    dev_agent = HybridMultiAgentMemory(
        config=neo4j_config,
        agent_config=AgentMemoryConfig(
            agent_id="dev_agent_001",
            agent_type="personal",
            access_level="team",
            team_id="dev_team"
        )
    )
    agents.append(dev_agent)
    
    # Agent 2: 数据分析师
    analyst_agent = HybridMultiAgentMemory(
        config=neo4j_config,
        agent_config=AgentMemoryConfig(
            agent_id="analyst_agent_001",
            agent_type="personal", 
            access_level="team",
            team_id="data_team"
        )
    )
    agents.append(analyst_agent)
    
    # Agent 3: 系统管理员（可访问所有）
    admin_agent = HybridMultiAgentMemory(
        config=neo4j_config,
        agent_config=AgentMemoryConfig(
            agent_id="admin_agent_001",
            agent_type="system",
            access_level="public"
        )
    )
    agents.append(admin_agent)
    
    return agents


# ========== 最佳实践建议 ==========
"""
1. 小规模（<10 Agents）:
   - 使用属性隔离或标签隔离
   - 单个Neo4j数据库足够

2. 中等规模（10-100 Agents）:
   - 使用子图隔离
   - 考虑添加索引优化查询

3. 大规模（>100 Agents）:
   - 考虑数据库隔离（如果Neo4j版本支持）
   - 或使用分片策略

4. 混合场景（推荐）:
   - 私有记忆 + 共享记忆
   - 基于角色的访问控制
   - 支持团队协作

5. 性能优化:
   - 为agent_id创建索引
   - 使用连接池
   - 批量操作
   - 定期清理过期数据
"""


if __name__ == "__main__":
    print("多Agent Neo4j设计方案演示")
    agents = demo_multi_agent_setup()
    print(f"创建了 {len(agents)} 个Agent记忆系统")