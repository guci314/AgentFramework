#!/bin/bash

echo "🎯 MultiStepAgent_v2 代码覆盖率测试"
echo "======================================"

# 清理之前的覆盖率数据
echo "🧹 清理之前的覆盖率数据..."
coverage erase

# 运行测试（只针对enhancedAgent_v2.py）
echo "🧪 运行测试并收集覆盖率数据..."
coverage run --source=enhancedAgent_v2 -m pytest tests/test_multi_step_agent_v2.py::TestMultiStepAgentV2::test_import_and_initialization tests/test_multi_step_agent_v2.py::TestMultiStepAgentV2::test_register_agent_success tests/test_multi_step_agent_v2.py::TestMultiStepAgentV2::test_execute_single_step_with_missing_agent tests/test_multi_step_agent_v2.py::TestMultiStepAgentV2::test_select_next_executable_step_single_pending_step tests/test_multi_step_agent_v2.py::TestMultiStepAgentV2::test_execute_multi_step_simple_echo_task -v

# 检查测试是否成功
if [ $? -eq 0 ]; then
    echo "✅ 测试通过！"
    
    echo ""
    echo "📊 enhancedAgent_v2.py 覆盖率报告："
    echo "========================================"
    # 生成针对特定文件的覆盖率报告
    coverage report -m --include="enhancedAgent_v2.py"
    
    echo ""
    echo "📄 生成HTML覆盖率报告..."
    coverage html --include="enhancedAgent_v2.py"
    
    echo ""
    echo "🎉 覆盖率分析完成！"
    echo "📂 HTML报告位置: htmlcov/index.html"
    echo "📊 enhancedAgent_v2.py 专项报告: htmlcov/enhancedAgent_v2_py.html"
    
    # 显示覆盖率统计
    echo ""
    echo "📈 关键统计信息："
    coverage report --include="enhancedAgent_v2.py" | grep enhancedAgent_v2.py
    
else
    echo "❌ 测试失败，请检查测试代码"
    exit 1
fi 