#!/usr/bin/env python3
"""
测试修复后的认知工作流
"""

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from embodied_cognitive_workflow import CognitiveAgent
from cognitive_debugger import CognitiveDebugger, StepType
from llm_lazy import get_model

print("✅ 所有导入成功!")

# 获取语言模型
llm = get_model('deepseek_chat')
print("✅ 成功加载模型: deepseek_chat")

# 创建认知智能体
agent = CognitiveAgent(
    llm=llm,
    max_cycles=3,
    verbose=True,  # 开启详细输出
    enable_meta_cognition=False,
    evaluation_mode="internal"
)
print("✅ 成功创建认知智能体")

# 测试一个需要多步骤的任务
task = "请帮我创建一个简单的hello.py文件，内容是打印'Hello, World!'"
print(f"\n🎯 测试任务: {task}")

# 直接执行任务
print("\n🚀 开始执行任务...")
result = agent.execute_sync(task)

print(f"\n📊 执行结果:")
print(f"  - 成功: {result.success}")
print(f"  - 代码: {result.code}")
print(f"  - 输出: {result.stdout}")
print(f"  - 错误: {result.stderr}")
print(f"  - 返回值: {result.return_value}")

print("\n✅ 测试完成!")