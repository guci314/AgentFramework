# 多Agent记忆系统架构设计

## 概述

在多Agent系统中，不需要为每个Agent创建独立的Neo4j数据库。相反，我们可以通过合理的架构设计，让多个Agent共享同一个Neo4j实例，同时保证数据隔离和访问控制。

## 设计方案对比

### 1. 标签隔离方案
```cypher
// 每个Agent的节点都有专属标签
(:Concept:Agent_001)  // Agent 001的概念
(:Concept:Agent_002)  // Agent 002的概念
```

**优点**：
- 实现简单
- 查询性能好（标签索引）
- 易于管理

**缺点**：
- 标签数量有限制
- 不够灵活

### 2. 属性隔离方案
```cypher
// 使用属性标识Agent
(:Concept {agent_id: "agent_001"})
(:Concept {agent_id: "agent_002"})
```

**优点**：
- 灵活性高
- 支持复杂查询
- 易于实现权限控制

**缺点**：
- 需要为agent_id建索引
- 每次查询都需要过滤

### 3. 子图隔离方案
```cypher
// 每个Agent有自己的根节点
(:AgentRoot {id: "agent_001"})-[:OWNS]->(:Concept)
(:AgentRoot {id: "agent_002"})-[:OWNS]->(:Concept)
```

**优点**：
- 清晰的所有权关系
- 支持复杂的权限模型
- 便于实现共享机制

**缺点**：
- 查询路径较长
- 需要维护关系

### 4. 混合方案（推荐）

结合多种隔离机制，支持私有和共享记忆：

```cypher
// Agent节点
(:Agent {id: "agent_001", type: "personal", team_id: "dev_team"})

// 私有概念
(:Agent)-[:OWNS {visibility: "private"}]->(:Concept)

// 团队共享概念
(:Team {id: "dev_team"})-[:CAN_ACCESS]->(:Concept)

// 公共概念
(:Concept {visibility: "public"})
```

## 推荐架构

### 1. 数据模型

```python
# Agent配置
@dataclass
class AgentMemoryConfig:
    agent_id: str           # 唯一标识
    agent_type: str         # personal/shared/system
    access_level: str       # private/team/public
    team_id: Optional[str]  # 所属团队
```

### 2. 访问控制

```python
class MultiAgentMemoryAccess:
    def can_read(self, agent_id: str, concept_id: str) -> bool:
        """检查Agent是否可以读取概念"""
        # 1. 检查是否是所有者
        # 2. 检查团队访问权限
        # 3. 检查公共访问权限
        
    def can_write(self, agent_id: str, concept_id: str) -> bool:
        """检查Agent是否可以修改概念"""
        # 通常只有所有者可以修改
```

### 3. 查询优化

```cypher
// 创建索引
CREATE INDEX agent_id_index FOR (n:Concept) ON (n.agent_id);
CREATE INDEX team_id_index FOR (n:Concept) ON (n.team_id);

// 复合查询示例
MATCH (c:Concept)
WHERE c.agent_id = $agent_id 
   OR c.team_id = $team_id
   OR c.visibility = 'public'
RETURN c
```

## 实施建议

### 小规模部署（<10 Agents）
- 使用单个Neo4j数据库
- 属性隔离即可
- 简单的访问控制

### 中等规模部署（10-100 Agents）
- 使用子图隔离
- 实现基于角色的访问控制
- 添加缓存层

### 大规模部署（>100 Agents）
- 考虑Neo4j集群
- 实现分片策略
- 使用专门的权限服务

## 性能考虑

1. **索引策略**
   - 为agent_id创建索引
   - 为常用查询创建复合索引
   
2. **查询优化**
   - 使用参数化查询
   - 避免全图扫描
   - 合理使用LIMIT

3. **数据清理**
   - 定期归档旧数据
   - 实现数据生命周期管理
   - 监控数据库大小

## 示例代码

```python
# 创建多Agent记忆系统
from embodied_cognitive_workflow.memory import Neo4jConfig

# 共享的Neo4j配置
config = Neo4jConfig(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="graphiti123!"
)

# 为不同Agent创建记忆系统
agents = {}
for agent_id in ["agent_001", "agent_002", "agent_003"]:
    agents[agent_id] = HybridMultiAgentMemory(
        config=config,
        agent_config=AgentMemoryConfig(
            agent_id=agent_id,
            agent_type="personal",
            access_level="team",
            team_id="research_team"
        )
    )

# Agent 001 存储私有概念
agents["agent_001"].add_concept(concept1, visibility="private")

# Agent 002 存储团队共享概念
agents["agent_002"].add_concept(concept2, visibility="team")

# Agent 003 查询时可以看到团队共享的概念
results = agents["agent_003"].recall("机器学习", include_shared=True)
```

## 总结

多Agent系统不需要每个Agent都创建独立的Neo4j数据库。通过合理的架构设计，可以实现：

1. **资源共享**：所有Agent共享一个Neo4j实例
2. **数据隔离**：通过标签、属性或子图实现隔离
3. **灵活访问**：支持私有、团队共享和公共记忆
4. **高效查询**：通过索引和优化保证性能
5. **易于扩展**：支持从小规模到大规模的平滑扩展

这种设计既节省资源，又保证了系统的灵活性和可扩展性。