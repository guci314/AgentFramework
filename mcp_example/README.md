# MCP 计算器示例

这是一个简单的 Model Context Protocol (MCP) 示例，展示如何创建和使用计算工具，**无需语言模型**。

## 🎯 功能特性

- ✅ **纯计算工具**: 加法、减法、乘法
- ✅ **MCP 协议**: 标准的 MCP 服务器/客户端通信
- ✅ **无 LLM 依赖**: 不需要 API 密钥或语言模型
- ✅ **错误处理**: 完整的参数验证和异常处理
- ✅ **交互式体验**: 支持命令行交互
- ✅ **快速测试**: 一键验证所有功能

## 📦 安装

1. **安装依赖**:
```bash
pip install -r requirements.txt
```

2. **验证安装**:
```bash
python run_example.py
```

## 🚀 快速开始

### 方式1: 一键测试 (推荐)
```bash
cd mcp_example
python run_example.py
```

### 方式2: 简单测试
```bash
python simple_test.py
```

### 方式3: 分别启动
1. **启动服务器** (终端1):
```bash
python server.py
```

2. **启动客户端** (终端2):
```bash  
python client.py
```

### 方式4: Inspector CLI 测试
```bash
# 安装 Inspector (需要 Node.js)
npm install -g @modelcontextprotocol/inspector

# 运行测试
python test_with_inspector.py

# 或查看手动使用说明
python test_with_inspector.py --manual
```

## 📁 文件结构

```
mcp_example/
├── README.md               # 本文档
├── requirements.txt        # 依赖列表
├── server.py              # MCP 服务器实现
├── client.py              # MCP 客户端实现 (交互式)
├── run_example.py         # 一键测试脚本
├── simple_test.py         # 简单测试 (非交互)
└── test_with_inspector.py # Inspector CLI 测试
```

## 🛠️ 工具说明

### 可用工具

| 工具名 | 描述 | 参数 | 示例 |
|--------|------|------|------|
| `add` | 两数相加 | `a`, `b` (数字) | `5 + 3 = 8` |
| `subtract` | 两数相减 | `a`, `b` (数字) | `10 - 4 = 6` |
| `multiply` | 两数相乘 | `a`, `b` (数字) | `6 × 7 = 42` |

### API 调用示例

```python
# 调用加法工具
result = await session.call_tool("add", {"a": 5, "b": 3})
# 返回: "计算结果: 5.0 + 3.0 = 8.0"

# 调用减法工具  
result = await session.call_tool("subtract", {"a": 10, "b": 4})
# 返回: "计算结果: 10.0 - 4.0 = 6.0"
```

## 🔧 代码架构

### 服务器端 (server.py)
```python
# 定义工具
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [Tool(name="add", description="将两个数字相加", ...)]

# 处理调用
@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    if name == "add":
        return [TextContent(text=f"结果: {a + b}")]
```

### 客户端 (client.py) 
```python
# 连接服务器
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("add", {"a": 5, "b": 3})
```

## 🧪 测试用例

运行 `python run_example.py` 会自动执行以下测试:

1. **基本运算**:
   - 加法: `10 + 20 = 30`
   - 减法: `100 - 30 = 70`
   - 乘法: `6 × 9 = 54`

2. **特殊情况**:
   - 小数运算: `3.14 + 2.86 = 6.0`
   - 负数运算: `(-5) - (-3) = -2`

3. **错误处理**:
   - 无效工具名
   - 参数类型错误
   - 缺少必需参数

## 🛠️ 扩展开发

### 添加新工具

1. **在 server.py 中添加工具定义**:
```python
Tool(
    name="divide",
    description="两数相除",
    inputSchema={
        "type": "object",
        "properties": {
            "a": {"type": "number", "description": "被除数"},
            "b": {"type": "number", "description": "除数"}
        },
        "required": ["a", "b"]
    }
)
```

2. **在 call_tool() 中添加处理逻辑**:
```python
elif name == "divide":
    a = float(arguments.get("a", 0))
    b = float(arguments.get("b", 1))
    if b == 0:
        return [TextContent(text="错误: 除数不能为零")]
    result = a / b
    return [TextContent(text=f"计算结果: {a} ÷ {b} = {result}")]
```

### 添加更多功能

- **科学计算**: 开方、指数、三角函数
- **数据处理**: 统计、排序、筛选
- **文件操作**: 读取、写入、转换
- **网络请求**: API 调用、数据获取

## 🐛 故障排除

### 常见问题

1. **ImportError: No module named 'mcp'**
   ```bash
   pip install mcp
   ```

2. **服务器启动失败**
   - 检查 Python 版本 (需要 3.8+)
   - 确保 server.py 文件存在
   - 查看错误日志

3. **客户端连接失败**
   - 确保服务器正在运行
   - 检查端口是否被占用
   - 验证 stdio 通信

4. **工具调用失败**
   - 检查参数格式和类型
   - 验证工具名称拼写
   - 查看服务器日志

### 调试技巧

- 在 server.py 中添加 `print()` 语句调试
- 使用 `try-except` 捕获详细错误信息
- 检查 MCP 协议消息格式

## 📚 进一步学习

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP 示例集合](https://github.com/modelcontextprotocol/servers)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个示例!

## 📄 许可证

MIT License