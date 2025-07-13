#!/usr/bin/env python3
"""
修复后的aider使用示例 - 正确处理错误情况
"""
import sys
import os

# 添加父目录到Python路径以导入Agent框架
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Agent
from llm_lazy import get_model
from aider_knowledge import aider_knowledge

# 更新的知识库，专门处理错误情况
error_handling_knowledge = """
## 处理aider shell命令错误

当aider尝试执行shell命令时可能会遇到交互式提示错误。解决方案：

1. **使用subprocess直接调用aider命令行**（推荐用于简单任务）
```python
import subprocess
import os

# 确保在正确的目录
os.chdir(target_directory)

# 构建aider命令
cmd = [
    "aider",
    "--model", "deepseek/deepseek-chat",
    "--yes",  # 自动确认
    "--no-git",  # 禁用git
    "--message", "创建Calculator类，只包含文件操作，不执行代码",
    "calculator.py"
]

# 执行命令
result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
```

2. **捕获并处理错误**
```python
try:
    # aider操作
    pass
except KeyboardInterrupt:
    print("检测到交互式提示，请使用命令行参数避免")
except Exception as e:
    print(f"错误: {e}")
```

3. **最佳实践**
- 始终使用 --yes 参数
- 对新文件使用 --no-git 避免git操作
- 指令明确说明"只创建/修改文件，不执行代码"
"""

# 创建标准Agent
llm = get_model('deepseek_chat')
agent = Agent(llm=llm, stateful=True)

# 注入原始知识和错误处理知识
agent.loadKnowledge(aider_knowledge + "\n\n" + error_handling_knowledge)

if __name__ == "__main__":
    # 修正后的指令
    instruction = """
    请使用subprocess调用aider命令行工具创建calculator2.py文件。
    使用以下参数：
    - --model deepseek/deepseek-chat
    - --yes (自动确认)
    - --no-git (避免git操作)
    - --message "创建Calculator类，包含add和multiply方法"
    
    注意：使用subprocess.run()执行命令，设置合理的超时时间。
    """
    
    print("开始执行修正后的任务...")
    result = agent.execute_sync(instruction)
    
    if result.success:
        print("✅ 任务成功完成")
        print(f"输出: {result.stdout}")
    else:
        print("❌ 任务失败")
        print(f"错误: {result.stderr}")