#!/bin/bash

echo "=== MCP配置诊断工具 ==="

# 检查配置文件
echo "1. 检查MCP配置文件..."
if [ -f ".claude/mcp.json" ]; then
    echo "✓ MCP配置文件存在"
    echo "配置内容:"
    cat .claude/mcp.json
else
    echo "✗ MCP配置文件不存在"
fi

echo ""

# 检查数据库文件
echo "2. 检查数据库文件..."
if [ -f "claude-memory.sqlite" ]; then
    echo "✓ 数据库文件存在"
    ls -la claude-memory.sqlite
else
    echo "✗ 数据库文件不存在"
fi

echo ""

# 检查npm包
echo "3. 检查npm包..."
if npm list @peakmojo/mcp-openmemory &>/dev/null; then
    echo "✓ npm包已安装"
    npm list @peakmojo/mcp-openmemory
else
    echo "✗ npm包未安装"
    echo "正在安装..."
    npm install @peakmojo/mcp-openmemory
fi

echo ""

# 测试MCP服务器
echo "4. 测试MCP服务器启动..."
echo "运行5秒测试..."
timeout 5s env MEMORY_DB_PATH="$(pwd)/claude-memory.sqlite" npx @peakmojo/mcp-openmemory@latest &
SERVER_PID=$!
sleep 2

if ps -p $SERVER_PID > /dev/null; then
    echo "✓ MCP服务器可以正常启动"
    kill $SERVER_PID 2>/dev/null
else
    echo "✗ MCP服务器启动失败"
fi

echo ""
echo "=== 诊断完成 ==="
echo ""
echo "如果所有检查都通过，请重新启动Claude Code:"
echo "1. 退出当前Claude Code会话"
echo "2. 重新运行: claude"