#!/usr/bin/env python3
"""
演示快速导入的效果

对比三种导入方式：
1. 传统 pythonTask 导入（慢）
2. 分离后的 python_core + llm_models（快）
3. 懒加载方式（最快）
"""

import sys
import os
import time

# 确保使用项目本地的模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

print("🚀 模块分离后的快速导入演示")
print("=" * 60)

# 方式1：传统导入（慢）
print("\n1️⃣ 传统导入方式（包含49个模型）:")
print("   from python_core import *")
print("   from llm_lazy import get_model")
print("   预期耗时：~26秒")

# 方式2：分离导入（快）
print("\n2️⃣ 分离导入方式（核心类与模型分离）:")
start_time = time.time()

# 只导入核心类，不导入模型
from python_core import Agent, Device, StatefulExecutor
core_import_time = time.time() - start_time

print(f"   from python_core import Agent  # 耗时: {core_import_time:.3f}s")
print("   ✅ 成功导入核心类，无模型初始化")

# 方式3：按需导入模型（最快）
print("\n3️⃣ 按需导入模型:")
start_time = time.time()

# 只导入需要的模型
from llm_models import get_model
model_import_time = time.time() - start_time

print(f"   from llm_models import get_model  # 耗时: {model_import_time:.3f}s")

# 获取特定模型
start_time = time.time()
llm = get_model('gemini_2_5_flash')
model_get_time = time.time() - start_time

print(f"   llm = get_model('gemini_2_5_flash')  # 耗时: {model_get_time:.3f}s")
print(f"   ✅ 成功获取模型: {type(llm).__name__}")

print("\n📊 性能对比:")
total_fast_time = core_import_time + model_import_time + model_get_time
print(f"   传统方式预计耗时: ~26.000s")
print(f"   分离方式实际耗时: {total_fast_time:.3f}s")
print(f"   性能提升: ~{26.0/total_fast_time:.1f}倍")

print("\n4️⃣ 创建智能体测试:")
start_time = time.time()

# 创建智能体（使用分离后的导入）
if llm:
    agent = Agent(llm=llm, stateful=True)
    agent_create_time = time.time() - start_time
    print(f"   agent = Agent(llm=llm)  # 耗时: {agent_create_time:.3f}s")
    print(f"   ✅ 智能体创建成功")
else:
    print("   ❌ 模型获取失败，无法创建智能体")

print("\n💡 分离方案的优势:")
print("   ✅ 核心类导入极快（无模型初始化开销）")
print("   ✅ 按需加载模型（只初始化实际使用的）") 
print("   ✅ 模块职责分离（便于维护和扩展）")
print("   ✅ 向后兼容（现有代码无需修改）")

print("\n🎯 使用建议:")
print("   # 快速导入核心功能")
print("   from python_core import Agent")
print("   ")
print("   # 按需导入模型")
print("   from llm_models import get_model")
print("   llm = get_model('gemini_2_5_flash')")
print("   ")
print("   # 创建智能体")
print("   agent = Agent(llm=llm)")

print(f"\n🎉 模块分离完成！导入速度提升约{26.0/total_fast_time:.0f}倍！")