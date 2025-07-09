# 开发建议命令

## 安装
```bash
# 安装主要依赖
pip install -r requirements.txt

# 安装 MCP 示例依赖（如需要）
cd mcp_examples
pip install -r requirements.txt
cd ..
```

## 测试命令
```bash
# 核心框架测试
python test_basic.py
python test_calculator.py
python test_compression.py
python test_jump_fix.py

# CognitiveWorkflow 测试
cd CognitiveWorkflow
python test_cognitive_workflow.py
python test_basic_functionality.py
python test_three_phase_planning.py
cd ..

# 综合测试套件
cd tests
python run_all_tests.py
python test_stress_boundary.py
cd ..

# 静态工作流测试
cd static_workflow/tests
python test_static_workflow.py
python test_workflow_examples.py
cd ../..

# 运行带覆盖率的测试
./run_tests.sh
# 或者
coverage run --source=enhancedAgent_v2 -m pytest tests/test_multi_step_agent_v2.py -v
coverage report -m
coverage html
```

## 运行示例
```bash
# CognitiveWorkflow 演示（推荐）
cd CognitiveWorkflow
python demo_cognitive_workflow.py
python hello_world.py
cd ..

# 遗留示例
python simple_calculator.py
python enhancedAgent_v2.py
python demo_agent_compression.py

# TaskMaster 集成
python examples/basic_task_master.py
python examples/observability_demo.py

# MCP 示例
cd mcp_examples
python simple_mcp_demo.py
python deepseek_mcp_example.py
cd ..
```

## Git 命令
```bash
git status
git add .
git commit -m "提交信息"
git push origin master
git log --oneline
```

## 系统工具（Linux）
```bash
ls -la          # 详细列出文件
cd directory    # 切换目录
pwd            # 打印当前目录
grep pattern   # 搜索模式
find . -name "*.py"  # 查找 Python 文件
ps aux         # 列出进程
top            # 监控系统资源
```

## 环境设置
```bash
# 复制示例环境文件
cp .env.example .env
# 编辑 .env 添加你的 API 密钥

# 设置内存限制环境变量
export AGENT_MAX_TOKENS=60000
```