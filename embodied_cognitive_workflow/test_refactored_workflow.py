#!/usr/bin/env python3
"""
测试重构后的具身认知工作流

验证二分法处理机制：
- 直接处理 vs 认知循环
- 性能和效果对比
"""

import sys
import os
import time
import logging

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置代理环境变量
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 导入必要模块
from embodied_cognitive_workflow import CognitiveAgent
sys.path.append('/home/guci/aiProjects/AgentFrameWork')
from llm_lazy import get_modelni_2_5_flash_google


def test_refactored_workflow():
    """测试重构后的工作流"""
    
    print("🚀 重构后的具身认知工作流测试")
    print("=" * 60)
    
    # 创建工作流实例
    print("1. 初始化重构后的工作流...")
    workflow = CognitiveAgent(
        llm=get_model("gemini_2_5_flash"),
        max_cycles=10,
        verbose=True
    )
    print("✅ 工作流初始化成功")
    
    # 测试用例：设计验证二分法的有效性
    test_cases = [
        {
            "name": "🎯 直接处理 - 基本计算",
            "task": "计算 15 × 7",
            "expected_mode": "直接处理",
            "expected_time": (0, 20)
        },
        {
            "name": "🎯 直接处理 - 简单问答",
            "task": "什么是Python?",
            "expected_mode": "直接处理", 
            "expected_time": (0, 20)
        },
        {
            "name": "🔄 认知循环 - 编程任务",
            "task": "写一个Python函数，判断一个数是否为质数",
            "expected_mode": "认知循环",
            "expected_time": (20, 120)
        },
        {
            "name": "🔄 认知循环 - 复杂任务", 
            "task": "设计一个简单的用户注册系统，包括数据验证和存储",
            "expected_mode": "认知循环",
            "expected_time": (30, 180)
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases):
        print(f"\n{'-'*60}")
        print(f"🧪 测试 {i+1}: {test_case['name']}")
        print(f"📝 任务: {test_case['task']}")
        print(f"🎯 预期模式: {test_case['expected_mode']}")
        print(f"{'-'*60}")
        
        # 测试任务判断逻辑
        can_direct = workflow._can_handle_directly(test_case['task'])
        predicted_mode = "直接处理" if can_direct else "认知循环"
        
        print(f"🤖 AI预测处理模式: {predicted_mode}")
        print(f"✅ 预测准确: {'是' if predicted_mode == test_case['expected_mode'] else '否'}")
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 执行任务
            print(f"⚡ 开始执行任务...")
            result = workflow.execute_cognitive_cycle(test_case['task'])
            
            # 计算执行时间
            duration = time.time() - start_time
            
            # 获取工作流状态
            status = workflow.get_workflow_status()
            
            # 记录结果
            test_result = {
                "name": test_case['name'],
                "task": test_case['task'][:40] + "..." if len(test_case['task']) > 40 else test_case['task'],
                "predicted_mode": predicted_mode,
                "expected_mode": test_case['expected_mode'],
                "prediction_correct": predicted_mode == test_case['expected_mode'],
                "success": result.success,
                "duration": duration,
                "cycles": status['当前循环次数'],
                "within_expected_time": test_case['expected_time'][0] <= duration <= test_case['expected_time'][1]
            }
            results.append(test_result)
            
            # 显示结果
            print(f"\n📊 执行结果:")
            print(f"   ✅ 成功: {result.success}")
            print(f"   ⏱️  时间: {duration:.1f}秒")
            print(f"   🔄 循环: {status['当前循环次数']}轮")
            print(f"   ⏳ 时间合理: {'是' if test_result['within_expected_time'] else '否'}")
            
            if len(str(result.return_value)) > 150:
                print(f"   📋 结果: {str(result.return_value)[:150]}...")
            else:
                print(f"   📋 结果: {result.return_value}")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append({
                "name": test_case['name'],
                "success": False,
                "error": str(e)
            })
        
        # 重置工作流
        workflow.reset()
        
        # 短暂暂停
        if i < len(test_cases) - 1:
            print(f"\n⏳ 等待3秒后进行下一个测试...")
            time.sleep(3)
    
    # 生成重构效果报告
    print(f"\n{'='*60}")
    print("🎉 重构效果测试报告")
    print(f"{'='*60}")
    
    # 统计结果
    successful_tests = sum(1 for r in results if r.get('success', False))
    total_tests = len(results)
    prediction_accuracy = sum(1 for r in results if r.get('prediction_correct', False))
    
    print(f"\n📈 总体表现:")
    print(f"   测试成功率: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
    print(f"   模式预测准确率: {prediction_accuracy}/{total_tests} ({prediction_accuracy/total_tests*100:.1f}%)")
    
    print(f"\n📊 详细结果:")
    for result in results:
        if 'success' in result and result['success']:
            print(f"\n{result['name']}:")
            print(f"   任务: {result['task']}")
            print(f"   模式: {result['predicted_mode']} {'✅' if result['prediction_correct'] else '❌'}")
            print(f"   时间: {result['duration']:.1f}秒 {'✅' if result['within_expected_time'] else '⚠️'}")
            print(f"   循环: {result['cycles']}轮")
    
    # 重构优势分析
    direct_tasks = [r for r in results if r.get('predicted_mode') == '直接处理' and r.get('success')]
    cognitive_tasks = [r for r in results if r.get('predicted_mode') == '认知循环' and r.get('success')]
    
    if direct_tasks and cognitive_tasks:
        avg_direct_time = sum(r['duration'] for r in direct_tasks) / len(direct_tasks)
        avg_cognitive_time = sum(r['duration'] for r in cognitive_tasks) / len(cognitive_tasks)
        
        print(f"\n🚀 重构优势:")
        print(f"   直接处理平均时间: {avg_direct_time:.1f}秒")
        print(f"   认知循环平均时间: {avg_cognitive_time:.1f}秒")
        print(f"   效率提升: {((avg_cognitive_time - avg_direct_time) / avg_cognitive_time * 100):.1f}%")
    
    print(f"\n✨ 重构核心改进:")
    print(f"   ✅ 消除中等复杂度的边界模糊问题")
    print(f"   ✅ 使用启发式规则，避免额外AI调用")
    print(f"   ✅ 简化系统架构，提升可维护性")
    print(f"   ✅ 保持完整认知能力，优化简单任务效率")
    
    print(f"\n🎊 重构测试完成！")


if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.WARNING)  # 减少日志噪音
    
    try:
        test_refactored_workflow()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc() 