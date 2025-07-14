# Neo4j语义记忆集成指南

## 概述

本项目实现了基于Neo4j图数据库的语义记忆持久化存储，提供了完整的ISemanticMemory接口实现，支持概念存储、知识图谱构建、模式识别等高级功能。

## 快速开始

### 1. 环境准备

确保已安装并运行Neo4j：

```bash
# Docker方式启动Neo4j
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/graphiti123! \
  neo4j:latest
```

### 2. 基本使用

```python
from semantic_memory_neo4j import Neo4jSemanticMemory
from neo4j_config import Neo4jConfig
from interfaces import Concept

# 创建配置
config = Neo4jConfig(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="graphiti123!"
)

# 创建Neo4j语义记忆
memory = Neo4jSemanticMemory(config)

# 添加概念
concept = Concept(
    name="Machine Learning",
    category="technology",
    attributes={'type': 'AI', 'applications': ['prediction']},
    confidence=0.9,
    domain="artificial_intelligence"
)
concept_id = memory.add_concept(concept)

# 搜索概念
results = memory.recall("learning", limit=10)

# 构建知识图谱
graph = memory.get_knowledge_graph(concept_id, depth=2)
```

### 3. 与记忆管理器集成

```python
from memory_manager import MemoryManager
from semantic_memory_neo4j import Neo4jSemanticMemory

# 使用Neo4j作为语义记忆存储
neo4j_semantic = Neo4jSemanticMemory()
mm = MemoryManager(semantic_memory=neo4j_semantic)

# 正常使用记忆管理器
mm.process_information("重要发现", metadata={'importance': 0.9})
```

## 核心功能

### 1. 概念管理

- **添加概念**：`add_concept(concept)`
- **获取概念**：`get(concept_id)`
- **更新概念**：`update(concept_id, content, metadata)`
- **删除概念**：`forget(concept_id)`
- **搜索概念**：`recall(query, limit)`

### 2. 知识图谱

- **构建图谱**：`get_knowledge_graph(root_id, depth)`
- **创建关系**：`create_relationship(id1, id2, type)`
- **查找相关**：`find_related_concepts(concept_id)`

### 3. 模式识别

- **查找模式**：`find_patterns(domain, min_confidence)`
- **概念相似度**：`calculate_concept_similarity(id1, id2)`
- **概念合并**：`merge_concepts(id1, id2)`

### 4. 高级功能

- **批量操作**：支持批量插入和查询
- **全文搜索**：基于Neo4j全文索引
- **统计分析**：`get_statistics()`

## 性能优化

### 1. 索引配置

系统自动创建以下索引：
- 概念ID唯一性约束
- 类别索引
- 领域索引
- 置信度索引
- 全文搜索索引

### 2. 连接池配置

```python
config = Neo4jConfig(
    max_connection_pool_size=50,
    connection_acquisition_timeout=60,
    query_timeout=30
)
```

### 3. 批量操作

对于大量数据插入，建议使用批量操作：

```python
# 批量插入示例
concepts = [...]  # 大量概念
with memory.driver.session() as session:
    with session.begin_transaction() as tx:
        for concept in concepts:
            # 使用事务批量插入
            tx.run(CREATE_CONCEPT_QUERY, **concept_params)
        tx.commit()
```

## 测试

### 运行单元测试

```bash
# 运行所有测试
python -m pytest tests/test_semantic_memory_neo4j.py -v

# 只运行单元测试（不需要Neo4j）
python -m pytest tests/test_semantic_memory_neo4j.py::TestNeo4jSemanticMemoryUnit -v

# 运行集成测试（需要Neo4j）
python -m pytest tests/test_semantic_memory_neo4j.py::TestNeo4jSemanticMemoryIntegration -v
```

### 运行性能测试

```bash
# 运行性能基准测试
python tests/benchmark_neo4j.py

# 运行特定测试
python -m pytest tests/test_semantic_memory_neo4j.py::TestNeo4jSemanticMemoryPerformance::test_bulk_insert_performance -v
```

### 运行集成测试

```bash
# 测试与记忆管理器的集成
python -m pytest tests/test_neo4j_integration.py -v
```

## 演示程序

### 基础演示

```bash
# 运行完整演示
python demo_neo4j_memory.py

# 运行记忆系统演示（包含Neo4j）
python demo_memory_system.py
```

### 功能展示

1. **基础功能**：概念CRUD、搜索、关系管理
2. **知识图谱**：多层次知识结构构建
3. **记忆管理器集成**：三层记忆架构与Neo4j
4. **数据迁移**：从内存迁移到Neo4j

## 架构设计

### 类图

```
ISemanticMemory (接口)
    ↑
    |
Neo4jSemanticMemory
    |
    ├── Neo4jConfig (配置)
    ├── GraphDatabase.driver (连接)
    └── CypherQueries (查询模板)
```

### 数据模型

```cypher
// 概念节点
(:Concept {
    id: String,
    name: String,
    category: String,
    attributes: String (JSON),
    confidence: Float,
    domain: String,
    created_at: DateTime,
    updated_at: DateTime
})

// 关系类型
-[:INCLUDES]->
-[:CONTAINS]->
-[:RELATED_TO]->
-[:SUBSET_OF]->
// ... 自定义关系
```

## 配置选项

### Neo4jConfig参数

| 参数 | 默认值 | 说明 |
|-----|--------|------|
| uri | bolt://localhost:7687 | Neo4j连接URI |
| username | neo4j | 用户名 |
| password | graphiti123! | 密码 |
| database | neo4j | 数据库名 |
| max_connection_pool_size | 50 | 最大连接池大小 |
| connection_acquisition_timeout | 60 | 连接获取超时(秒) |
| query_timeout | 30 | 查询超时(秒) |
| create_indexes | True | 是否自动创建索引 |

### 环境变量

支持通过环境变量配置：

```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=your_password
export NEO4J_DATABASE=your_database
```

## 最佳实践

### 1. 概念设计

```python
# 良好的概念设计
concept = Concept(
    name="明确的概念名称",
    category="合理的分类",
    attributes={
        'description': '详细描述',
        'tags': ['标签1', '标签2'],
        'metadata': {...}
    },
    confidence=0.85,  # 合理的置信度
    domain="明确的领域"
)
```

### 2. 关系管理

```python
# 创建有意义的关系
memory.create_relationship(
    parent_id, 
    child_id, 
    "IS_PART_OF",  # 使用清晰的关系类型
    properties={'weight': 0.8}
)
```

### 3. 查询优化

```python
# 使用参数化查询
results = memory.recall(query, limit=50)  # 限制结果数量

# 使用索引字段
concepts = memory.get_concepts_by_category("technology")  # 利用索引
```

### 4. 错误处理

```python
try:
    memory = Neo4jSemanticMemory(config)
except Exception as e:
    logger.error(f"Failed to connect to Neo4j: {e}")
    # 使用备用存储或重试
```

## 故障排除

### 常见问题

1. **连接失败**
   - 检查Neo4j是否运行：`docker ps`
   - 验证连接参数是否正确
   - 检查防火墙设置

2. **性能问题**
   - 确保索引已创建
   - 调整连接池大小
   - 使用批量操作

3. **内存问题**
   - 限制查询结果大小
   - 使用分页查询
   - 定期清理过期数据

### 日志配置

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('memory.semantic_memory_neo4j')
```

## 扩展开发

### 自定义查询

```python
# 添加自定义Cypher查询
class CustomQueries(CypherQueries):
    CUSTOM_PATTERN = """
    MATCH (c:Concept)-[:CUSTOM_REL*1..3]->(related)
    WHERE c.id = $concept_id
    RETURN related
    """
```

### 自定义关系类型

```python
# 定义领域特定的关系
DOMAIN_RELATIONSHIPS = {
    'PREREQUISITE_OF': '前置条件',
    'CONFLICTS_WITH': '冲突关系',
    'ENHANCES': '增强关系'
}
```

## 性能指标

基于性能测试结果：

| 操作 | 平均耗时 | 吞吐量 |
|------|---------|---------|
| 单个插入 | ~20ms | 50 ops/s |
| 批量插入(1000) | <30s | 33 concepts/s |
| 简单搜索 | <100ms | >10 queries/s |
| 图遍历(深度2) | <500ms | - |
| 相似度计算 | <50ms | - |

## 未来计划

1. **向量搜索集成**：结合向量数据库实现语义搜索
2. **分布式支持**：Neo4j集群配置
3. **缓存层**：Redis缓存热点数据
4. **可视化工具**：知识图谱可视化界面

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork项目
2. 创建功能分支
3. 编写测试
4. 提交PR

## 许可证

[项目许可证]