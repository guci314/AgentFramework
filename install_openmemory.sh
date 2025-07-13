#!/bin/bash

# OpenMemory MCP 安装脚本

echo "正在设置OpenMemory MCP..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误：需要安装Docker"
    echo "请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 创建OpenMemory目录
mkdir -p ~/openmemory
cd ~/openmemory

# 克隆仓库
if [ ! -d "mem0" ]; then
    echo "克隆Mem0仓库..."
    git clone https://github.com/mem0ai/mem0.git
fi

cd mem0

# 创建环境变量文件
echo "配置环境变量..."
cat > backend/.env << 'EOF'
OPENAI_API_KEY=your_openai_api_key_here
EOF

echo "请编辑 ~/openmemory/mem0/backend/.env 文件，添加你的OpenAI API密钥"

# 构建和启动服务
echo "构建Docker镜像..."
make build

echo "启动OpenMemory服务..."
make up

echo "OpenMemory MCP 安装完成！"
echo ""
echo "下一步："
echo "1. 编辑 ~/openmemory/mem0/backend/.env 添加你的OpenAI API密钥"
echo "2. 重启服务: cd ~/openmemory/mem0 && make down && make up"
echo "3. 访问管理界面: http://localhost:3000"
echo "4. 配置Claude Code MCP:"
echo ""
echo '{
  "mcpServers": {
    "openmemory": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sse", 
        "http://localhost:8765/mcp/claude/sse/your-username"
      ]
    }
  }
}'