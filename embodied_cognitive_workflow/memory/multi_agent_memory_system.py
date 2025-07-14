#!/usr/bin/env python
"""
统一的多Agent记忆系统

整合了MultiAgentMemory和MultiTenantMemorySystem的功能
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

from neo4j import Driver
from neo4j_config import Neo4jConfig
from semantic_memory_neo4j import Neo4jSemanticMemory
from interfaces import Concept, MemoryItem


class AccessLevel(Enum):
    """访问级别"""
    PRIVATE = "private"      # 仅自己可见
    TEAM = "team"           # 团队可见
    ORGANIZATION = "org"    # 组织可见
    PUBLIC = "public"       # 所有人可见


class AgentType(Enum):
    """Agent类型"""
    PERSONAL = "personal"    # 个人Agent
    TEAM = "team"           # 团队Agent
    SYSTEM = "system"       # 系统Agent
    SERVICE = "service"     # 服务Agent


@dataclass
class AgentProfile:
    """Agent配置文件"""
    agent_id: str
    agent_type: AgentType = AgentType.PERSONAL
    team_ids: Set[str] = field(default_factory=set)
    organization_id: Optional[str] = None
    permissions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class MultiAgentMemorySystem:
    """
    统一的多Agent记忆系统
    
    功能：
    1. Agent管理（注册、认证、权限）
    2. 记忆存储（私有、共享、公共）
    3. 访问控制（基于角色和级别）
    4. 查询路由（智能选择数据源）
    5. 系统管理（监控、清理、备份）
    """
    
    def __init__(self, neo4j_config: Neo4jConfig):
        self.config = neo4j_config
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self._agents_cache: Dict[str, AgentProfile] = {}
        self._init_connection()
        self._init_database_schema()
    
    def _init_connection(self):
        """初始化数据库连接"""
        from neo4j import GraphDatabase
        
        self.driver = GraphDatabase.driver(
            self.config.uri,
            auth=(self.config.username, self.config.password),
            max_connection_lifetime=self.config.max_connection_lifetime,
            max_connection_pool_size=self.config.max_connection_pool_size
        )
        
        # 验证连接
        self.driver.verify_connectivity()
    
    def _init_database_schema(self):
        """初始化数据库模式"""
        with self.driver.session(database=self.config.database) as session:
            # 创建约束和索引
            queries = [
                # Agent唯一性约束
                """
                CREATE CONSTRAINT agent_id_unique IF NOT EXISTS
                FOR (a:Agent) REQUIRE a.id IS UNIQUE
                """,
                
                # Team唯一性约束  
                """
                CREATE CONSTRAINT team_id_unique IF NOT EXISTS
                FOR (t:Team) REQUIRE t.id IS UNIQUE
                """,
                
                # 概念索引
                """
                CREATE INDEX concept_agent_index IF NOT EXISTS
                FOR (c:Concept) ON (c.agent_id)
                """,
                
                # 访问级别索引
                """
                CREATE INDEX concept_access_index IF NOT EXISTS
                FOR (c:Concept) ON (c.access_level)
                """,
                
                # 复合索引
                """
                CREATE INDEX concept_composite_index IF NOT EXISTS
                FOR (c:Concept) ON (c.agent_id, c.access_level, c.created_at)
                """
            ]
            
            for query in queries:
                try:
                    session.run(query)
                except Exception as e:
                    self.logger.debug(f"索引可能已存在: {e}")
    
    # ========== Agent管理 ==========
    
    def register_agent(self, profile: AgentProfile) -> bool:
        """注册新Agent"""
        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                """
                CREATE (a:Agent {
                    id: $agent_id,
                    type: $agent_type,
                    organization_id: $org_id,
                    created_at: datetime(),
                    metadata: $metadata
                })
                RETURN a
                """,
                agent_id=profile.agent_id,
                agent_type=profile.agent_type.value,
                org_id=profile.organization_id,
                metadata=profile.metadata
            )
            
            # 创建团队关系
            for team_id in profile.team_ids:
                session.run(
                    """
                    MATCH (a:Agent {id: $agent_id})
                    MERGE (t:Team {id: $team_id})
                    MERGE (a)-[:MEMBER_OF]->(t)
                    """,
                    agent_id=profile.agent_id,
                    team_id=team_id
                )
            
            # 缓存Agent信息
            self._agents_cache[profile.agent_id] = profile
            
            return result.single() is not None
    
    def get_agent_profile(self, agent_id: str) -> Optional[AgentProfile]:
        """获取Agent配置"""
        # 先检查缓存
        if agent_id in self._agents_cache:
            return self._agents_cache[agent_id]
        
        # 从数据库加载
        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                """
                MATCH (a:Agent {id: $agent_id})
                OPTIONAL MATCH (a)-[:MEMBER_OF]->(t:Team)
                RETURN a, collect(t.id) as team_ids
                """,
                agent_id=agent_id
            )
            
            record = result.single()
            if record:
                agent_node = record["a"]
                profile = AgentProfile(
                    agent_id=agent_node["id"],
                    agent_type=AgentType(agent_node["type"]),
                    team_ids=set(record["team_ids"]),
                    organization_id=agent_node.get("organization_id"),
                    metadata=agent_node.get("metadata", {})
                )
                self._agents_cache[agent_id] = profile
                return profile
        
        return None
    
    # ========== 记忆存储 ==========
    
    def store_memory(self, 
                    agent_id: str,
                    concept: Concept,
                    access_level: AccessLevel = AccessLevel.PRIVATE) -> Optional[str]:
        """存储记忆"""
        # 验证Agent
        profile = self.get_agent_profile(agent_id)
        if not profile:
            raise ValueError(f"Agent {agent_id} not registered")
        
        # 添加元数据
        concept.metadata.update({
            'agent_id': agent_id,
            'access_level': access_level.value,
            'team_ids': list(profile.team_ids) if access_level == AccessLevel.TEAM else [],
            'org_id': profile.organization_id if access_level == AccessLevel.ORGANIZATION else None,
            'stored_at': datetime.now().isoformat()
        })
        
        # 存储概念
        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                """
                CREATE (c:Concept {
                    id: $id,
                    name: $name,
                    category: $category,
                    agent_id: $agent_id,
                    access_level: $access_level,
                    content: $content,
                    metadata: $metadata,
                    created_at: datetime()
                })
                RETURN c.id as concept_id
                """,
                id=concept.id,
                name=concept.name,
                category=concept.category,
                agent_id=agent_id,
                access_level=access_level.value,
                content=concept.attributes,
                metadata=concept.metadata
            )
            
            record = result.single()
            if record:
                concept_id = record["concept_id"]
                
                # 创建所有权关系
                session.run(
                    """
                    MATCH (a:Agent {id: $agent_id})
                    MATCH (c:Concept {id: $concept_id})
                    CREATE (a)-[:OWNS]->(c)
                    """,
                    agent_id=agent_id,
                    concept_id=concept_id
                )
                
                # 如果是团队或组织级别，创建访问关系
                if access_level == AccessLevel.TEAM:
                    for team_id in profile.team_ids:
                        session.run(
                            """
                            MATCH (t:Team {id: $team_id})
                            MATCH (c:Concept {id: $concept_id})
                            CREATE (t)-[:CAN_ACCESS]->(c)
                            """,
                            team_id=team_id,
                            concept_id=concept_id
                        )
                
                return concept_id
        
        return None
    
    # ========== 记忆召回 ==========
    
    def recall_memories(self,
                       agent_id: str,
                       query: str,
                       include_shared: bool = True,
                       limit: int = 10) -> List[MemoryItem]:
        """召回记忆"""
        profile = self.get_agent_profile(agent_id)
        if not profile:
            raise ValueError(f"Agent {agent_id} not registered")
        
        # 构建访问条件
        access_conditions = self._build_access_conditions(profile, include_shared)
        
        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                f"""
                MATCH (c:Concept)
                WHERE ({access_conditions})
                AND (c.name CONTAINS $query OR c.content CONTAINS $query)
                RETURN c
                ORDER BY c.created_at DESC
                LIMIT $limit
                """,
                agent_id=agent_id,
                team_ids=list(profile.team_ids),
                org_id=profile.organization_id,
                query=query,
                limit=limit
            )
            
            memories = []
            for record in result:
                node = record["c"]
                memory = MemoryItem(
                    id=node["id"],
                    content=node.get("content", {}),
                    metadata=node.get("metadata", {}),
                    timestamp=node.get("created_at", datetime.now())
                )
                memories.append(memory)
            
            return memories
    
    def _build_access_conditions(self, profile: AgentProfile, include_shared: bool) -> str:
        """构建访问条件查询"""
        conditions = [
            # 自己的私有记忆
            f"(c.agent_id = $agent_id AND c.access_level = '{AccessLevel.PRIVATE.value}')"
        ]
        
        if include_shared:
            # 公共记忆
            conditions.append(f"c.access_level = '{AccessLevel.PUBLIC.value}'")
            
            # 团队记忆
            if profile.team_ids:
                conditions.append(
                    f"(c.access_level = '{AccessLevel.TEAM.value}' "
                    f"AND any(team_id IN $team_ids WHERE team_id IN c.metadata.team_ids))"
                )
            
            # 组织记忆
            if profile.organization_id:
                conditions.append(
                    f"(c.access_level = '{AccessLevel.ORGANIZATION.value}' "
                    f"AND c.metadata.org_id = $org_id)"
                )
        
        return " OR ".join(conditions)
    
    # ========== 团队协作 ==========
    
    def share_memory(self,
                    agent_id: str,
                    concept_id: str,
                    new_access_level: AccessLevel) -> bool:
        """共享记忆（修改访问级别）"""
        profile = self.get_agent_profile(agent_id)
        if not profile:
            return False
        
        with self.driver.session(database=self.config.database) as session:
            # 验证所有权
            ownership = session.run(
                """
                MATCH (a:Agent {id: $agent_id})-[:OWNS]->(c:Concept {id: $concept_id})
                RETURN c
                """,
                agent_id=agent_id,
                concept_id=concept_id
            ).single()
            
            if not ownership:
                return False
            
            # 更新访问级别
            session.run(
                """
                MATCH (c:Concept {id: $concept_id})
                SET c.access_level = $new_level,
                    c.metadata.team_ids = $team_ids,
                    c.metadata.org_id = $org_id
                """,
                concept_id=concept_id,
                new_level=new_access_level.value,
                team_ids=list(profile.team_ids) if new_access_level == AccessLevel.TEAM else [],
                org_id=profile.organization_id if new_access_level == AccessLevel.ORGANIZATION else None
            )
            
            return True
    
    # ========== 系统管理 ==========
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                """
                MATCH (a:Agent)
                WITH count(a) as total_agents
                MATCH (t:Team)
                WITH total_agents, count(t) as total_teams
                MATCH (c:Concept)
                WITH total_agents, total_teams, 
                     count(c) as total_concepts,
                     count(CASE WHEN c.access_level = 'private' THEN 1 END) as private_concepts,
                     count(CASE WHEN c.access_level = 'team' THEN 1 END) as team_concepts,
                     count(CASE WHEN c.access_level = 'public' THEN 1 END) as public_concepts
                RETURN {
                    agents: total_agents,
                    teams: total_teams,
                    concepts: {
                        total: total_concepts,
                        private: private_concepts,
                        team: team_concepts,
                        public: public_concepts
                    }
                } as stats
                """
            )
            
            return result.single()["stats"]
    
    def cleanup_old_memories(self, days: int = 90) -> int:
        """清理旧记忆"""
        with self.driver.session(database=self.config.database) as session:
            result = session.run(
                """
                MATCH (c:Concept)
                WHERE c.created_at < datetime() - duration({days: $days})
                AND c.access_level = 'private'
                AND NOT EXISTS((c)<-[:REFERS_TO]-())
                DETACH DELETE c
                RETURN count(c) as deleted_count
                """,
                days=days
            )
            
            return result.single()["deleted_count"]
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()


# ========== 便捷接口 ==========

class AgentMemory:
    """单个Agent的记忆接口"""
    
    def __init__(self, system: MultiAgentMemorySystem, agent_id: str):
        self.system = system
        self.agent_id = agent_id
        self.profile = system.get_agent_profile(agent_id)
        
        if not self.profile:
            raise ValueError(f"Agent {agent_id} not found")
    
    def store(self, concept: Concept, access_level: AccessLevel = AccessLevel.PRIVATE) -> str:
        """存储概念"""
        return self.system.store_memory(self.agent_id, concept, access_level)
    
    def recall(self, query: str, include_shared: bool = True, limit: int = 10) -> List[MemoryItem]:
        """召回记忆"""
        return self.system.recall_memories(self.agent_id, query, include_shared, limit)
    
    def share(self, concept_id: str, access_level: AccessLevel) -> bool:
        """共享记忆"""
        return self.system.share_memory(self.agent_id, concept_id, access_level)


# ========== 使用示例 ==========

def example_usage():
    """使用示例"""
    # 创建系统
    config = Neo4jConfig(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="graphiti123!",
        database="agents"  # 使用专门的agents数据库
    )
    
    system = MultiAgentMemorySystem(config)
    
    # 注册Agent
    dev_agent = AgentProfile(
        agent_id="dev_001",
        agent_type=AgentType.PERSONAL,
        team_ids={"backend_team", "ai_team"},
        organization_id="tech_corp"
    )
    system.register_agent(dev_agent)
    
    # 创建Agent记忆接口
    memory = AgentMemory(system, "dev_001")
    
    # 存储私有概念
    private_concept = Concept(
        id="concept_001",
        name="项目密码",
        category="security",
        attributes={"password": "secret123"}
    )
    memory.store(private_concept, AccessLevel.PRIVATE)
    
    # 存储团队共享概念
    team_concept = Concept(
        id="concept_002",
        name="API设计规范",
        category="documentation",
        attributes={"version": "2.0", "rules": ["RESTful", "JWT"]}
    )
    memory.store(team_concept, AccessLevel.TEAM)
    
    # 召回记忆
    results = memory.recall("API", include_shared=True)
    for item in results:
        print(f"Found: {item.content}")
    
    # 获取系统统计
    stats = system.get_system_statistics()
    print(f"系统统计: {stats}")
    
    # 清理
    system.close()


if __name__ == "__main__":
    example_usage()