#!/usr/bin/env python3
"""
展示WorkflowContext的中文文档字符串和自然语言状态特性
"""

import sys
import os
# 确保使用项目本地的模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from embodied_cognitive_workflow import WorkflowContext

print("📚 WorkflowContext 中文文档字符串展示")
print("=" * 60)

# 显示类的帮助信息
print("\n🔍 查看WorkflowContext的完整文档:")
help(WorkflowContext)

print("\n" + "=" * 60)
print("🧠 WorkflowContext 自然语言状态演示")

# 创建工作流上下文
context = WorkflowContext("开发一个Python计算器程序")

print(f"\n1️⃣ 初始化状态:")
print(f"   用户指令: {context.instruction}")
print(f"   目标达成: {context.goal_achieved}")
print(f"   当前状态: '{context.current_state}' (空字符串)")

print(f"\n2️⃣ 自我智能体分析当前状态 (自然语言):")
ego_analysis = """
1. **当前处于什么状态**: 刚接收到用户指令，需要开发一个Python计算器程序
2. **已经完成了什么**: 理解了用户需求，准备开始分析如何实现
3. **还需要做什么**: 设计计算器的功能模块，编写代码，测试功能
4. **可能遇到的问题**: 需要确定计算器的具体功能范围和用户界面形式
"""
context.update_current_state(ego_analysis.strip())
print(f"   current_state已更新为自然语言描述:")
print(f"   '{context.current_state[:50]}...'")

print(f"\n3️⃣ 添加循环历史记录:")
context.add_cycle_result(1, "分析需求：基本四则运算功能")
context.add_cycle_result(2, "设计架构：命令行交互式计算器")
print(f"   历史记录数量: {len(context.history)}")

print(f"\n4️⃣ 本我智能体评估 (自然语言):")
id_evaluation = "计算器的基本架构已设计完成，核心功能需求明确，可以开始编码实现"
context.update_id_evaluation(id_evaluation)
print(f"   id_evaluation: '{context.id_evaluation}'")

print(f"\n5️⃣ 目标达成控制:")
print(f"   当前goal_achieved: {context.goal_achieved}")
context.update_goal_status(True)  # 模拟任务完成
print(f"   设置goal_achieved为True后: {context.goal_achieved}")
print(f"   📍 这将导致认知循环终止!")

print(f"\n6️⃣ 完整的自然语言上下文:")
print(f"   get_current_context()返回的完整上下文:")
print("-" * 40)
print(context.get_current_context())
print("-" * 40)

print(f"\n🎯 核心特性总结:")
print(f"✅ 所有状态都是自然语言: current_state、id_evaluation都是文本描述")
print(f"✅ 工作流控制变量: goal_achieved决定是否继续认知循环")  
print(f"✅ 状态透明性: 通过get_current_context()获得完整的可读状态")
print(f"✅ 动态更新: 支持实时更新各种认知状态")
print(f"✅ 历史追踪: 维护完整的认知循环执行历史")

print(f"\n💡 设计理念:")
print(f"- 自然语言优先: 避免硬编码枚举，使用灵活的文本描述")
print(f"- 认知透明性: 所有状态都可被人类理解和审查")  
print(f"- 智能体友好: 便于AI模型理解和处理状态信息")
print(f"- 精确控制: 通过goal_achieved变量精确控制工作流生命周期")