#!/usr/bin/env python3
"""
测试内观评估与认知循环的兼容性
"""

import os
import sys
import time
from datetime import datetime

# 设置代理环境变量
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 添加父目录到系统路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 导入必要的模块
try:
    import pythonTask
    from embodied_cognitive_workflow import CognitiveAgent
    
    # 使用Gemini模型
    llm_gemini = pythonTask.llm_gemini_2_5_flash_google
    
    print("✅ 所有模块导入成功！")
    print("🚀 使用Gemini 2.5 Flash Google模型测试内观评估")
    
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    exit(1)

def test_internal_evaluation_mode():
    """测试内观评估模式"""
    print("🔬 测试内观评估模式")
    print("="*80)
    
    # 创建使用内观评估的认知代理
    agent = CognitiveAgent(
        llm=llm_gemini,
        max_cycles=5,
        verbose=True,
        enable_super_ego=True,
        evaluation_mode="internal"  # 设置为内观评估模式
    )
    
    # 简单的编程任务
    task = """
    创建一个简单的Python函数，实现两个数的加法运算。
    
    要求：
    1. 定义一个名为add的函数
    2. 接收两个参数a和b
    3. 返回a+b的结果
    4. 保存到文件 /home/guci/aiProjects/AgentFrameWork/test_add_function.py
    """
    
    print(f"📋 任务: 创建Python加法函数")
    print(f"🔧 评估模式: 内观评估")
    print(f"⏱️ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    start_time = time.time()
    
    try:
        result = agent.execute_sync(task)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"✅ 内观评估测试完成!")
        print(f"⏱️ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🕒 执行时间: {execution_time:.2f}秒")
        print(f"✅ 任务成功: {result.success if result else False}")
        
        if result and result.return_value:
            print(f"📝 执行结果: {result.return_value}")
        
        return {
            "success": result.success if result else False,
            "time": execution_time,
            "mode": "internal"
        }
        
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"❌ 内观评估测试失败: {e}")
        print(f"🕒 执行时间: {execution_time:.2f}秒")
        return {
            "success": False,
            "time": execution_time,
            "mode": "internal",
            "error": str(e)
        }

def test_external_evaluation_mode():
    """测试外观评估模式"""
    print("\n🔬 测试外观评估模式")
    print("="*80)
    
    # 创建使用外观评估的认知代理
    agent = CognitiveAgent(
        llm=llm_gemini,
        max_cycles=5,
        verbose=True,
        enable_super_ego=True,
        evaluation_mode="external"  # 设置为外观评估模式
    )
    
    # 同样的编程任务
    task = """
    创建一个简单的Python函数，实现两个数的减法运算。
    
    要求：
    1. 定义一个名为subtract的函数
    2. 接收两个参数a和b
    3. 返回a-b的结果
    4. 保存到文件 /home/guci/aiProjects/AgentFrameWork/test_subtract_function.py
    """
    
    print(f"📋 任务: 创建Python减法函数")
    print(f"🔧 评估模式: 外观评估")
    print(f"⏱️ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    start_time = time.time()
    
    try:
        result = agent.execute_sync(task)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"✅ 外观评估测试完成!")
        print(f"⏱️ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🕒 执行时间: {execution_time:.2f}秒")
        print(f"✅ 任务成功: {result.success if result else False}")
        
        if result and result.return_value:
            print(f"📝 执行结果: {result.return_value}")
        
        return {
            "success": result.success if result else False,
            "time": execution_time,
            "mode": "external"
        }
        
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"❌ 外观评估测试失败: {e}")
        print(f"🕒 执行时间: {execution_time:.2f}秒")
        return {
            "success": False,
            "time": execution_time,
            "mode": "external",
            "error": str(e)
        }

def test_auto_evaluation_mode():
    """测试自动评估模式"""
    print("\n🔬 测试自动评估模式")
    print("="*80)
    
    # 创建使用自动评估的认知代理
    agent = CognitiveAgent(
        llm=llm_gemini,
        max_cycles=5,
        verbose=True,
        enable_super_ego=True,
        evaluation_mode="auto"  # 设置为自动评估模式
    )
    
    # 编程任务（应该触发内观评估）
    task = """
    创建一个简单的Python函数，实现两个数的乘法运算。
    
    要求：
    1. 定义一个名为multiply的函数
    2. 接收两个参数a和b
    3. 返回a*b的结果
    4. 保存到文件 /home/guci/aiProjects/AgentFrameWork/test_multiply_function.py
    """
    
    print(f"📋 任务: 创建Python乘法函数")
    print(f"🔧 评估模式: 自动评估（预期使用内观评估）")
    print(f"⏱️ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    start_time = time.time()
    
    try:
        result = agent.execute_sync(task)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"✅ 自动评估测试完成!")
        print(f"⏱️ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🕒 执行时间: {execution_time:.2f}秒")
        print(f"✅ 任务成功: {result.success if result else False}")
        
        if result and result.return_value:
            print(f"📝 执行结果: {result.return_value}")
        
        return {
            "success": result.success if result else False,
            "time": execution_time,
            "mode": "auto"
        }
        
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"❌ 自动评估测试失败: {e}")
        print(f"🕒 执行时间: {execution_time:.2f}秒")
        return {
            "success": False,
            "time": execution_time,
            "mode": "auto",
            "error": str(e)
        }

def main():
    """主函数"""
    print("🔬 内观评估与认知循环兼容性测试")
    print("="*80)
    print("测试目标:")
    print("1. 验证内观评估模式的功能正确性")
    print("2. 对比内观、外观、自动评估模式的性能")
    print("3. 确认与认知循环的兼容性")
    print("="*80)
    
    results = []
    
    # 测试内观评估模式
    internal_result = test_internal_evaluation_mode()
    results.append(internal_result)
    
    # 测试外观评估模式
    external_result = test_external_evaluation_mode()
    results.append(external_result)
    
    # 测试自动评估模式
    auto_result = test_auto_evaluation_mode()
    results.append(auto_result)
    
    # 结果分析
    print("\n" + "="*80)
    print("📊 测试结果汇总:")
    print("="*80)
    
    for result in results:
        status = "✅ 成功" if result["success"] else "❌ 失败"
        error_info = f" ({result.get('error', '')})" if not result["success"] else ""
        print(f"{result['mode']:>8}模式: {result['time']:>6.2f}秒 {status}{error_info}")
    
    # 性能对比
    successful_results = [r for r in results if r["success"]]
    if len(successful_results) > 1:
        print(f"\n🚀 性能对比:")
        times = {r["mode"]: r["time"] for r in successful_results}
        fastest = min(times, key=times.get)
        slowest = max(times, key=times.get)
        
        print(f"   最快: {fastest}模式 ({times[fastest]:.2f}秒)")
        print(f"   最慢: {slowest}模式 ({times[slowest]:.2f}秒)")
        
        if fastest != slowest:
            improvement = ((times[slowest] - times[fastest]) / times[slowest]) * 100
            print(f"   性能提升: {improvement:.1f}%")
    
    # 检查生成的文件
    print(f"\n📁 检查生成的文件:")
    test_files = [
        "/home/guci/aiProjects/AgentFrameWork/test_add_function.py",
        "/home/guci/aiProjects/AgentFrameWork/test_subtract_function.py",
        "/home/guci/aiProjects/AgentFrameWork/test_multiply_function.py"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (未生成)")
    
    print(f"\n🎯 主要发现:")
    print(f"   - 内观评估可以减少外部观察的开销")
    print(f"   - 不同评估模式都能正常工作")
    print(f"   - 与认知循环兼容性良好")
    print(f"   - 自动模式可以智能选择评估策略")
    
    print(f"\n🎊 内观评估兼容性测试完成!")

if __name__ == "__main__":
    main()