#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证所有组件功能的脚本
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_device():
    """测试Device组件"""
    print("📦 测试Device组件...")
    try:
        # 设置临时API密钥以避免导入错误
        if not os.getenv('DEEPSEEK_API_KEY'):
            os.environ['DEEPSEEK_API_KEY'] = 'fake_key_for_testing'
        
        from pythonTask import Device
        device = Device()
        
        # 测试简单执行
        result = device.execute_code('print("Device测试成功")')
        assert result.success, "Device执行失败"
        assert "Device测试成功" in result.stdout, "Device输出不正确"
        
        print("   ✅ Device基础功能正常")
        return True
    except Exception as e:
        print(f"   ❌ Device测试失败: {e}")
        return False

def test_stateful_executor():
    """测试StatefulExecutor组件"""
    print("📦 测试StatefulExecutor组件...")
    try:
        from pythonTask import StatefulExecutor
        executor = StatefulExecutor()
        
        # 测试变量持久化
        result1 = executor.execute_code('x = 42\nprint(f"设置x = {x}")')
        assert result1.success, "StatefulExecutor第一次执行失败"
        
        result2 = executor.execute_code('print(f"获取x = {x}")')
        assert result2.success, "StatefulExecutor第二次执行失败"
        assert "获取x = 42" in result2.stdout, "变量持久化失败"
        
        print("   ✅ StatefulExecutor状态管理正常")
        return True
    except Exception as e:
        print(f"   ❌ StatefulExecutor测试失败: {e}")
        return False

def test_thinker():
    """测试Thinker组件（需要API密钥）"""
    print("📦 测试Thinker组件...")
    
    if not os.getenv('DEEPSEEK_API_KEY') or os.getenv('DEEPSEEK_API_KEY') == 'fake_key_for_testing':
        print("   ⚠️  跳过Thinker测试（缺少真实API密钥）")
        return True
    
    try:
        from pythonTask import Thinker, StatefulExecutor, llm_deepseek
        
        device = StatefulExecutor()
        thinker = Thinker(llm=llm_deepseek, device=device, max_retries=1)
        
        # 测试简单代码生成
        result = thinker.execute_sync("计算2+3的结果并打印")
        assert result.success, "Thinker代码生成失败"
        assert "5" in result.stdout, "Thinker计算结果不正确"
        
        print("   ✅ Thinker代码生成正常")
        return True
    except Exception as e:
        print(f"   ❌ Thinker测试失败: {e}")
        return False

def test_evaluator():
    """测试Evaluator组件（需要API密钥）"""
    print("📦 测试Evaluator组件...")
    
    if not os.getenv('DEEPSEEK_API_KEY') or os.getenv('DEEPSEEK_API_KEY') == 'fake_key_for_testing':
        print("   ⚠️  跳过Evaluator测试（缺少真实API密钥）")
        return True
    
    try:
        from pythonTask import Evaluator, llm_deepseek
        from agent_base import Result
        from mda.prompts import default_evaluate_message
        
        evaluator = Evaluator(llm=llm_deepseek, systemMessage=default_evaluate_message)
        
        # 测试成功案例评估
        success_result = Result(
            success=True,
            code='print("Hello, World!")',
            stdout="Hello, World!\n",
            stderr=None,
            return_value=None
        )
        
        is_complete, reason = evaluator.evaluate("打印Hello World", success_result)
        assert isinstance(is_complete, bool), "Evaluator返回类型错误"
        assert isinstance(reason, str), "Evaluator原因类型错误"
        
        print("   ✅ Evaluator评估功能正常")
        return True
    except Exception as e:
        print(f"   ❌ Evaluator测试失败: {e}")
        return False

def test_agent():
    """测试Agent组件（需要API密钥）"""
    print("📦 测试Agent组件...")
    
    if not os.getenv('DEEPSEEK_API_KEY') or os.getenv('DEEPSEEK_API_KEY') == 'fake_key_for_testing':
        print("   ⚠️  跳过Agent测试（缺少真实API密钥）")
        return True
    
    try:
        from pythonTask import Agent, llm_deepseek
        
        agent = Agent(llm=llm_deepseek, stateful=True, max_retries=1, skip_evaluation=True)
        
        # 测试简单任务执行
        result = agent.execute_sync("计算1+1的结果")
        assert result.success, "Agent任务执行失败"
        assert "2" in result.stdout, "Agent计算结果不正确"
        
        print("   ✅ Agent集成功能正常")
        return True
    except Exception as e:
        print(f"   ❌ Agent测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 快速验证pythonTask.py组件功能")
    print("="*50)
    
    # 检查API密钥
    has_api_key = bool(os.getenv('DEEPSEEK_API_KEY')) and os.getenv('DEEPSEEK_API_KEY') != 'fake_key_for_testing'
    
    if has_api_key:
        print("📡 检测到DEEPSEEK_API_KEY，将测试所有组件")
    else:
        print("⚠️  未检测到DEEPSEEK_API_KEY，将跳过API相关测试")
    
    print()
    
    # 运行测试
    tests = [
        test_device,
        test_stateful_executor,
        test_thinker,
        test_evaluator,
        test_agent
    ]
    
    results = []
    for test_func in tests:
        success = test_func()
        results.append(success)
        print()
    
    # 统计结果
    passed = sum(results)
    total = len(results)
    
    print("="*50)
    print(f"📊 验证结果: {passed}/{total} 组件通过")
    
    if passed == total:
        print("🎉 所有组件验证通过！")
    else:
        print("❌ 部分组件验证失败")
    
    if not has_api_key:
        print("\n💡 提示: 设置DEEPSEEK_API_KEY环境变量可验证完整功能")

if __name__ == '__main__':
    main()