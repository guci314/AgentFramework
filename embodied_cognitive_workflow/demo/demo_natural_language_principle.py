#!/usr/bin/env python3
"""
展示整个架构的自然语言优先原则：指令是自然语言，状态是自然语言
"""

import sys
import os
# 确保使用项目本地的模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from embodied_cognitive_workflow import CognitiveAgent, WorkflowContext
from python_core import *
from llm_lazy import get_model

print("🌟 具身认知工作流架构 - 自然语言优先原则演示")
print("=" * 70)

print("\n📋 核心设计原则:")
print("✅ 指令是自然语言 - 用户命令、任务描述都使用自然语言")
print("✅ 状态是自然语言 - 所有认知状态、评估、上下文都是自然语言描述")
print("✅ 无硬编码枚举 - 避免刚性状态枚举，使用灵活的自然语言描述")
print("✅ 人类可读透明 - 认知过程的每个方面都可被人类理解和审查")
print("✅ AI模型友好 - 自然语言状态天然兼容大语言模型")

print("\n" + "=" * 70)
print("🧠 四层认知架构的自然语言交互演示")

# 创建认知智能体
agent = CognitiveAgent(
    llm=\1("gemini_2_5_flash"),
    max_cycles=3,
    verbose=False,
    enable_meta_cognition=False,
    evaluation_mode="external"
)

print("\n1️⃣ 指令层 - 自然语言指令:")
instruction = "创建一个简单的Python函数，用于计算两个数字的平均值"
print(f"   用户指令: '{instruction}'")
print("   📝 注意: 完全是自然语言，没有任何代码或结构化命令")

print("\n2️⃣ 状态层 - 自然语言状态管理:")
# 模拟认知状态 (实际会由各层智能体生成)
context = WorkflowContext(instruction)

# 模拟自我智能体的自然语言状态分析
ego_state = """
1. **当前状态**: 接收到计算平均值函数的开发任务
2. **已完成**: 理解了用户需求 - 需要一个计算两数平均值的Python函数
3. **待完成**: 设计函数结构、实现计算逻辑、添加参数验证
4. **潜在问题**: 需要考虑除零错误、参数类型验证、返回值格式
"""
context.update_current_state(ego_state.strip())
print("   自我状态分析 (自然语言):")
print(f"   {context.current_state[:100]}...")

# 模拟本我智能体的自然语言评估
id_evaluation = "函数需求明确，实现相对简单，核心是算术平均值计算，需要基本的错误处理"
context.update_id_evaluation(id_evaluation)
print(f"\n   本我价值评估 (自然语言): '{context.id_evaluation}'")

print("\n3️⃣ 上下文层 - 完整的自然语言上下文:")
full_context = context.get_current_context()
print("   自然语言格式的完整认知上下文:")
print("-" * 50)
print(full_context)
print("-" * 50)

print("\n4️⃣ 控制层 - 自然语言驱动的工作流控制:")
print(f"   当前目标达成状态: {context.goal_achieved}")
print("   📊 工作流继续判断基于: goal_achieved 布尔变量")
print("   📊 状态更新通过: context.update_goal_status(True/False)")

# 模拟目标达成
context.update_goal_status(True)
print(f"   设置目标达成后: {context.goal_achieved}")
print("   🎯 这将导致认知循环终止")

print("\n" + "=" * 70)
print("🎯 自然语言优先原则的核心价值:")

print("\n📈 技术优势:")
print("  • 认知透明性: 所有智能体思维过程都是人类可读的")
print("  • 动态灵活性: 状态可以演化和适应，无需代码修改")
print("  • 跨智能体通信: 不同智能体类型可以理解彼此的状态")
print("  • 调试简单性: 所有状态和决策都是纯语言形式")
print("  • 可扩展性: 可以添加新的认知模式而无需结构变更")

print("\n🔧 实现原则:")
print("  • 避免硬编码枚举: 不使用 PENDING/RUNNING/COMPLETED 等状态码")
print("  • 自然语言描述: 使用 '正在分析用户需求' 而非 status=ANALYZING")
print("  • 结构化解析: 使用JSON格式解析自然语言评估结果")
print("  • 上下文整合: 将所有状态信息整合为完整的自然语言描述")

print("\n💡 与传统架构的对比:")
print("  传统: user_command = 'CREATE_FUNCTION', status = ENUM_PROCESSING")
print("  本架构: instruction = '创建一个计算平均值的函数', state = '正在分析函数需求...'")
print()
print("  传统: if status == COMPLETED: workflow.stop()")
print("  本架构: if goal_achieved: # 基于自然语言评估的布尔结果")

print("\n🌟 这种设计使得整个认知架构:")
print("  ✅ 完全透明和可解释")
print("  ✅ 天然适配大语言模型")
print("  ✅ 支持复杂的动态认知模式") 
print("  ✅ 便于人类理解和调试")
print("  ✅ 具备无限的扩展可能性")

print(f"\n🎉 具身认知工作流 - 引领AI认知架构的自然语言革命！")