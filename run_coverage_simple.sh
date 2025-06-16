#!/bin/bash

echo "🎯 简化的代码覆盖率测试"
echo "========================"

# 清理所有Python缓存和之前的覆盖率数据
echo "🧹 清理缓存和覆盖率数据..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
coverage erase

# 运行简单的导入测试来收集覆盖率
echo "🧪 运行覆盖率收集..."
coverage run --source=. --include="enhancedAgent_v2.py" -m pytest tests/test_multi_step_agent_v2.py::TestMultiStepAgentV2::test_import_and_initialization -v

# 检查结果
if [ $? -eq 0 ]; then
    echo "✅ 测试执行成功"
    
    echo ""
    echo "📊 覆盖率报告："
    coverage report --include="enhancedAgent_v2.py"
    
    echo ""
    echo "📄 生成HTML报告..."
    coverage html --include="enhancedAgent_v2.py"
    
    if [ -f "htmlcov/index.html" ]; then
        echo "✅ HTML报告生成成功: htmlcov/index.html"
    else
        echo "❌ HTML报告生成失败"
    fi
else
    echo "❌ 测试执行失败"
    exit 1
fi 