# Mem0 MCP 集成完整指南

## 方案选择

基于研究，我们有以下几种方案来集成Mem0和Claude Code：

### 方案一：OpenMemory MCP (官方推荐)

#### 1. Docker方式（推荐生产环境）

```bash
# 克隆官方仓库
git clone https://github.com/mem0ai/mem0.git
cd mem0

# 配置环境变量
cat > backend/.env << 'EOF'
OPENAI_API_KEY=your_openai_api_key
EOF

# 启动服务
make build
make up
make ui
```

#### 2. Claude Code配置

```json
{
  "mcpServers": {
    "openmemory": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sse",
        "http://localhost:8765/mcp/claude/sse/your-username"
      ],
      "transport": "sse"
    }
  }
}
```

### 方案二：第三方MCP-Mem0服务器

#### 1. 安装

```bash
git clone https://github.com/coleam00/mcp-mem0.git
cd mcp-mem0
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 2. Claude Code配置

```json
{
  "mcpServers": {
    "mem0": {
      "command": "/path/to/mcp-mem0/.venv/bin/python",
      "args": ["/path/to/mcp-mem0/src/main.py"],
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key",
        "LLM_CHOICE": "gpt-4o-mini"
      }
    }
  }
}
```

### 方案三：简化记忆服务器（已配置）

当前我们已经配置的方案：

```json
{
  "mcpServers": {
    "mcp-openmemory": {
      "command": "npx",
      "args": ["@peakmojo/mcp-openmemory@latest"],
      "env": {
        "MEMORY_DB_PATH": "/home/guci/aiProjects/AgentFrameWork/claude-memory.sqlite"
      }
    }
  }
}
```

## 当前问题诊断

您遇到的问题可能是：

1. **包安装问题**：需要确保npm包正确安装
2. **权限问题**：数据库路径权限
3. **配置问题**：MCP服务器配置格式

## 解决步骤

### 1. 验证包安装

```bash
npm list @peakmojo/mcp-openmemory
```

### 2. 测试MCP服务器

```bash
# 手动测试MCP服务器
MEMORY_DB_PATH=/home/guci/aiProjects/AgentFrameWork/claude-memory.sqlite npx @peakmojo/mcp-openmemory@latest
```

### 3. 检查数据库文件权限

```bash
touch /home/guci/aiProjects/AgentFrameWork/claude-memory.sqlite
chmod 666 /home/guci/aiProjects/AgentFrameWork/claude-memory.sqlite
```

## 推荐方案

我建议使用**方案一（OpenMemory MCP）**，因为：

1. 官方支持
2. 功能完整
3. 支持Web界面管理
4. 跨工具记忆共享

## 下一步

1. 选择合适的方案
2. 按照指南配置
3. 重启Claude Code
4. 测试记忆功能