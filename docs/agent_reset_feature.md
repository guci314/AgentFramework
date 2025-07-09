# AgentBase.reset() 方法文档

## 概述

`reset()` 方法是 `AgentBase` 类的新增功能，用于重置智能体的内存，同时智能地保留重要信息。

## 方法签名

```python
def reset(self) -> None
```

## 功能描述

该方法会清空智能体的对话历史，但会自动保留以下消息：

1. **系统消息** (`SystemMessage`) - 定义智能体身份和行为的初始消息
2. **受保护的消息** - 所有标记为 `protected=True` 的消息，包括：
   - 通过 `loadKnowledge()` 加载的知识
   - 手动设置 `protected=True` 的任何消息

## 使用场景

- **客服系统**: 在服务不同客户之间清除对话历史
- **多轮任务**: 在任务之间重置上下文，保留核心指令
- **隐私保护**: 定期清理敏感对话内容
- **内存优化**: 长时间运行时定期清理，避免内存溢出

## 代码示例

### 基础用法

```python
from agent_base import AgentBase
from langchain_openai import ChatOpenAI

# 创建智能体
agent = AgentBase(
    llm=ChatOpenAI(),
    system_message="你是一个助手"
)

# 进行一些对话
agent.chat_sync("你好")
agent.chat_sync("帮我写个邮件")

# 重置内存（保留系统消息）
agent.reset()
```

### 保留知识的高级用法

```python
# 创建智能体
agent = AgentBase(llm=llm, system_message="你是产品专家")

# 加载需要保留的知识（自动设置protected=True）
agent.loadKnowledge("""
产品信息：
- 名称：智能助手Pro
- 版本：2.0
- 特性：自然语言处理、多轮对话、知识管理
""")

# 对话
agent.chat_sync("产品有什么特性？")
agent.chat_sync("价格是多少？")

# 重置（保留系统消息和产品知识）
agent.reset()

# 新对话仍能访问产品知识
agent.chat_sync("介绍一下产品特性")
```

## 技术细节

### 内存管理

- 重置前会遍历所有消息，根据类型和保护状态决定保留
- 重置后会将 `memory_overloaded` 标志设为 `False`
- 保持消息的原始顺序

### 与现有功能的兼容性

- 完全兼容 `@reduce_memory_decorator` 装饰器
- 不影响继承类的功能
- 与 `loadKnowledge()` 方法完美配合

## 最佳实践

1. **定期重置**: 在长时间运行的应用中，定期调用 `reset()` 避免内存累积
2. **保护重要信息**: 使用 `loadKnowledge()` 加载需要持久保留的信息
3. **会话管理**: 在多用户场景中，每个用户会话结束后调用 `reset()`
4. **监控内存**: 配合 `calculate_memory_tokens()` 监控内存使用情况

## 注意事项

- `reset()` 是不可逆操作，清除的消息无法恢复
- 如果没有系统消息和受保护消息，`reset()` 后内存将完全清空
- 建议在 `reset()` 前后记录日志，便于调试和审计