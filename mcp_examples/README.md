# MCP (Model Context Protocol) 示例集合

这个目录包含了完整的 MCP 使用示例，展示如何让语言模型与 MCP 服务器进行交互。

## 📁 文件说明

### 1. `simple_mcp_demo.py` - 简化版演示 ⭐ **推荐入门**
**最适合初学者理解概念**

- 🎯 **功能**: 模拟 MCP 的完整交互流程
- 🔧 **特点**: 不需要真实的 MCP 服务器或语言模型 API
- 💡 **用途**: 理解 语言模型 ↔ MCP 的交互机制

```bash
# 运行简化演示
python3 simple_mcp_demo.py
```

**演示内容**:
- 模拟语言模型的推理过程
- 展示工具选择和调用
- 显示完整的交互流程

### 2. `server.py` - 基础 MCP 服务器
**简单的 MCP 服务器实现**

- 🧮 **功能**: 基础计算器功能（加、减、乘）
- 📝 **特点**: 代码简洁，易于理解
- 🔧 **用途**: 学习 MCP 服务器的基本结构

```bash
# 启动基础服务器
python3 server.py
```

### 3. `enhanced_server.py` - 完整功能的 MCP 服务器
**生产级别的 MCP 服务器示例**

- 🛠️ **工具**: 计算器、数据管理、时间获取、文本处理
- 📁 **资源**: 数据存储、对话历史、服务器配置
- 📝 **提示**: 数据分析、问题解决模板
- 🔄 **状态**: 支持持久化数据和历史记录

```bash
# 启动增强版服务器
python3 enhanced_server.py
```

### 4. `client.py` - MCP 客户端示例
**展示如何连接和使用 MCP 服务器**

- 🔗 **连接**: 演示客户端-服务器通信
- 🧪 **测试**: 测试各种工具调用
- 📊 **监控**: 显示连接状态和响应

```bash
# 连接到服务器并测试
python3 client.py
```

### 5. `llm_mcp_example.py` - 语言模型集成示例
**展示真实的语言模型如何调用 MCP**

- 🤖 **支持**: Claude (Anthropic) 和 GPT (OpenAI)
- 🔗 **集成**: 完整的客户端-服务器通信
- 📋 **功能**: 工具调用、资源访问、提示模板使用

```bash
# 运行集成演示（需要 API 密钥）
python3 llm_mcp_example.py
```

### 6. `requirements.txt` - 依赖管理
**项目所需的 Python 包**

```bash
# 安装依赖
pip install -r requirements.txt
```

## 🚀 快速开始

### 方案 1: 理解概念（推荐入门）
```bash
cd mcp_examples
python3 simple_mcp_demo.py
```

选择选项 1 或 3，观看完整的交互演示。

### 方案 2: 真实服务器测试
```bash
# 终端 1: 启动 MCP 服务器
python3 enhanced_server.py

# 终端 2: 测试客户端连接
# 可以使用 MCP Inspector 或自定义客户端
```

### 方案 3: 语言模型集成（需要 API 密钥）
1. 在 `llm_mcp_example.py` 中设置你的 API 密钥
2. 运行集成演示

## 🔧 MCP 的四大组件

### 1. **Tools (工具)** - 标准化的 Function Call
```python
# 示例：计算器工具
{
    "name": "calculator",
    "description": "执行基本数学运算",
    "inputSchema": {
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["add", "subtract"]},
            "a": {"type": "number"},
            "b": {"type": "number"}
        }
    }
}
```

### 2. **Resources (资源)** - 数据和文件访问
```python
# 示例：数据存储资源
{
    "uri": "data://store",
    "name": "数据存储",
    "description": "当前数据存储的内容",
    "mimeType": "application/json"
}
```

### 3. **Prompts (提示)** - 模板化提示管理
```python
# 示例：数据分析提示
{
    "name": "data_analysis",
    "description": "数据分析助手",
    "arguments": [
        {"name": "data_description", "required": True}
    ]
}
```

### 4. **Sampling (采样)** - 生成控制参数
- 控制 AI 生成内容的参数
- 温度、最大长度等设置

## 📚 核心概念对比

| 特性 | 传统 Function Call | MCP |
|------|-------------------|-----|
| **标准化** | ❌ 各厂商不同 | ✅ 统一协议 |
| **架构** | 直接调用 | 客户端-服务器 |
| **功能** | 仅工具调用 | 工具+资源+提示+采样 |
| **状态** | 无状态 | 持久连接 |
| **互操作** | 厂商锁定 | 跨平台兼容 |

## 🎯 交互流程

```
用户请求 → AI模型分析 → 选择MCP工具 → MCP服务器执行 → 返回结果 → AI模型响应
```

### 详细步骤：
1. **用户发送请求**：例如 "帮我计算 15 + 27"
2. **AI模型分析**：理解需求，选择合适的工具
3. **调用MCP工具**：发送 `calculator` 工具调用请求
4. **MCP服务器执行**：处理计算逻辑
5. **返回结果**：服务器返回 "计算结果: 15 + 27 = 42"
6. **AI模型响应**：整合结果给用户最终回复

## 🛠️ 安装依赖

```bash
# 基础依赖
pip install mcp

# 如果要运行语言模型集成示例
pip install anthropic openai

# 可选：MCP Inspector（用于调试）
npm install -g @modelcontextprotocol/inspector
```

## 🔍 调试和测试

### 使用 MCP Inspector
```bash
# 启动服务器
python3 enhanced_server.py

# 在另一个终端启动 Inspector
mcp-inspector python3 enhanced_server.py
```

### 手动测试工具调用
可以通过 MCP Inspector 或自定义客户端测试所有工具功能。

## 💡 最佳实践

1. **开发顺序**：
   - 先看 `simple_mcp_demo.py` 理解概念
   - 再运行 `enhanced_server.py` 体验真实服务器
   - 最后集成到语言模型中

2. **错误处理**：
   - 所有工具都包含完整的错误处理
   - 提供清晰的错误信息和使用提示

3. **扩展性**：
   - 代码结构清晰，易于添加新工具
   - 资源和提示模板支持动态配置

## 📄 相关资源

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [MCP GitHub 仓库](https://github.com/modelcontextprotocol)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [OpenAI API](https://openai.com/api/)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这些示例！

---

**总结**: MCP 是**标准化的增强版 Function Call**，它不仅统一了工具调用格式，还扩展了功能范围，支持资源访问、提示模板和持久连接。这些示例从简单到复杂，帮助你全面理解和使用 MCP。 