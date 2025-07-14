# Neo4j Database 概念详解

## Neo4j 版本差异

### Neo4j 3.x（社区版）
- **只支持单个数据库**
- 所有数据都存储在默认的图数据库中
- 没有 database 的概念

### Neo4j 4.x+（重要更新）
- **支持多数据库**
- 默认数据库名称：`neo4j`
- 系统数据库：`system`（存储用户、角色、权限等）

## 多数据库功能

### 1. 默认配置
```python
neo4j_config = Neo4jConfig(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="graphiti123!",
    database="neo4j"  # 默认数据库
)
```

### 2. 创建新数据库（需要管理员权限）
```cypher
// 在 system 数据库中执行
:use system
CREATE DATABASE myapp;
CREATE DATABASE agent_001;
CREATE DATABASE test_env;
```

### 3. 查看所有数据库
```cypher
:use system
SHOW DATABASES;
```

输出示例：
```
╒═══════════╤═════════╤═══════════╤═══════════════╤═══════════╕
│name       │aliases  │access     │address        │role       │
╞═══════════╪═════════╪═══════════╪═══════════════╪═══════════╡
│"neo4j"    │[]       │"read-write"│"localhost:7687"│"primary"  │
├───────────┼─────────┼───────────┼───────────────┼───────────┤
│"system"   │[]       │"read-write"│"localhost:7687"│"primary"  │
├───────────┼─────────┼───────────┼───────────────┼───────────┤
│"myapp"    │[]       │"read-write"│"localhost:7687"│"primary"  │
└───────────┴─────────┴───────────┴───────────────┴───────────┘
```

### 4. 切换数据库
```cypher
// 在 Neo4j Browser 中
:use myapp

// 在 Python 中
session = driver.session(database="myapp")
```

## 多Agent系统中的数据库策略

### 策略1：共享数据库（推荐）
```python
# 所有Agent使用同一个数据库，通过属性或标签隔离
config = Neo4jConfig(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="graphiti123!",
    database="agents"  # 共享数据库
)

# Agent数据通过属性隔离
CREATE (n:Concept {agent_id: "agent_001", ...})
CREATE (n:Concept {agent_id: "agent_002", ...})
```

### 策略2：按团队/项目分库
```python
# 开发团队数据库
dev_config = Neo4jConfig(database="dev_team")

# 数据分析团队数据库
data_config = Neo4jConfig(database="data_team")

# 测试环境数据库
test_config = Neo4jConfig(database="test_env")
```

### 策略3：按Agent分库（不推荐，除非特殊需求）
```python
# 每个Agent独立数据库
agent1_config = Neo4jConfig(database="agent_001")
agent2_config = Neo4jConfig(database="agent_002")
# 问题：数据库数量过多，难以管理
```

## 实践示例

### 创建多租户记忆系统
```python
class MultiTenantMemorySystem:
    def __init__(self, base_config: Neo4jConfig):
        self.base_config = base_config
        self.ensure_databases()
    
    def ensure_databases(self):
        """确保必要的数据库存在"""
        with self.get_driver().session(database="system") as session:
            # 创建共享数据库
            databases = [
                "agents_shared",     # 共享知识库
                "agents_private",    # 私有数据
                "agents_archive"     # 归档数据
            ]
            
            for db_name in databases:
                try:
                    session.run(f"CREATE DATABASE {db_name}")
                    print(f"创建数据库: {db_name}")
                except:
                    print(f"数据库已存在: {db_name}")
    
    def get_memory_for_agent(self, agent_id: str, db_type: str = "shared"):
        """为Agent获取相应的记忆系统"""
        config = Neo4jConfig(
            uri=self.base_config.uri,
            username=self.base_config.username,
            password=self.base_config.password,
            database=f"agents_{db_type}"
        )
        
        return MultiAgentMemory(config, agent_id)
```

### 使用示例
```python
# 初始化系统
base_config = Neo4jConfig(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="graphiti123!"
)

system = MultiTenantMemorySystem(base_config)

# Agent 1 使用共享数据库
agent1_shared = system.get_memory_for_agent("agent_001", "shared")

# Agent 1 使用私有数据库
agent1_private = system.get_memory_for_agent("agent_001", "private")

# 存储共享知识
agent1_shared.add_concept(concept1, visibility="team")

# 存储私有知识
agent1_private.add_concept(concept2, visibility="private")
```

## 版本检查

```python
def check_neo4j_version(driver):
    """检查Neo4j版本和多数据库支持"""
    with driver.session(database="system") as session:
        result = session.run("CALL dbms.components()")
        for record in result:
            if record["name"] == "Neo4j Kernel":
                version = record["versions"][0]
                major_version = int(version.split(".")[0])
                
                if major_version >= 4:
                    print(f"Neo4j {version} - 支持多数据库")
                else:
                    print(f"Neo4j {version} - 不支持多数据库")
                
                return major_version >= 4
    return False
```

## 最佳实践

1. **社区版 vs 企业版**
   - 社区版：从4.0开始支持多数据库
   - 企业版：更多高级功能（集群、备份等）

2. **数据库命名规范**
   - 使用小写字母和下划线
   - 避免特殊字符
   - 有意义的名称：`agents_prod`, `agents_dev`

3. **权限管理**
   ```cypher
   // 创建角色
   CREATE ROLE agent_reader;
   
   // 授予权限
   GRANT MATCH {*} ON DATABASE agents TO agent_reader;
   ```

4. **备份策略**
   - 定期备份重要数据库
   - 使用 `neo4j-admin dump` 命令
   
## 总结

- Neo4j 4.x+ 支持多数据库
- 默认数据库名为 `neo4j`
- 可以通过 `database` 参数指定使用哪个数据库
- 多Agent系统推荐使用共享数据库 + 数据隔离策略
- 只在特殊情况下（如严格的数据隔离需求）才为每个Agent创建独立数据库