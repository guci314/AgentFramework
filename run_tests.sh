#!/bin/bash

# 清理之前的覆盖率数据
echo "🧹 清理之前的覆盖率数据..."
coverage erase

# 使用coverage运行测试
echo "🧪 运行测试并收集覆盖率数据..."
coverage run --source=enhancedAgent_v2 -m pytest tests/test_multi_step_agent_v2.py -v

# 检查测试是否成功
if [ $? -eq 0 ]; then
    echo "✅ 测试通过！"
    
    # 生成控制台报告
    echo "📊 生成控制台覆盖率报告..."
    coverage report -m
    
    # 生成HTML报告
    echo "📄 生成HTML覆盖率报告..."
    coverage html
    
    echo "🎉 覆盖率报告生成完成！"
    echo "📂 HTML报告位置: htmlcov/index.html"
    echo "🌐 打开HTML报告: file://$(pwd)/htmlcov/index.html"
else
    echo "❌ 测试失败，请检查测试代码"
    exit 1
fi 