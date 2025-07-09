#!/usr/bin/env python3
"""
测试 CognitiveAgent 的 execute_stream 方法
验证流式执行是否正确调用四层架构的流式方法
"""

import os
import sys
from typing import Iterator

# 设置代理环境变量
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 添加父目录到系统路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    import pythonTask
    from embodied_cognitive_workflow import CognitiveAgent
    from agent_base import Result
    
    # 使用Gemini模型
    llm_gemini = pythonTask.llm_gemini_2_5_flash_google
    
    print("✅ 所有模块导入成功！")
    
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)

def test_execute_stream_basic():
    """测试基本的流式执行功能"""
    print("\n🧪 测试基本流式执行...")
    
    # 创建认知智能体
    agent = CognitiveAgent(
        llm=llm_gemini,
        max_cycles=5,
        verbose=True,
        enable_super_ego=False,  # 简化测试，关闭超我
        evaluation_mode="internal"
    )
    
    # 简单的计算任务
    task = "计算 2 + 3 的结果"
    
    print(f"📝 任务: {task}")
    print("🔄 开始流式执行...")
    
    chunks = []
    final_result = None
    
    try:
        for chunk in agent.execute_stream(task):
            if isinstance(chunk, Result):
                final_result = chunk
                print(f"✅ 最终结果: {chunk.success} - {chunk.return_value}")
                break
            else:
                chunks.append(chunk)
                print(f"📊 过程: {chunk}")
        
        print(f"\n📈 总共收到 {len(chunks)} 个过程片段")
        print(f"🎯 最终结果成功: {final_result.success if final_result else 'None'}")
        
        return final_result and final_result.success
        
    except Exception as e:
        print(f"❌ 流式执行失败: {e}")
        return False

def test_execute_stream_with_super_ego():
    """测试带超我监督的流式执行"""
    print("\n🧪 测试带超我监督的流式执行...")
    
    # 创建带超我监督的认知智能体
    agent = CognitiveAgent(
        llm=llm_gemini,
        max_cycles=5,
        verbose=True,
        enable_super_ego=True,  # 启用超我监督
        evaluation_mode="internal"
    )
    
    # 简单的任务
    task = "创建一个简单的Python函数返回Hello World"
    
    print(f"📝 任务: {task}")
    print("🔄 开始流式执行...")
    
    chunks = []
    final_result = None
    
    try:
        for chunk in agent.execute_stream(task):
            if isinstance(chunk, Result):
                final_result = chunk
                print(f"✅ 最终结果: {chunk.success} - {chunk.return_value}")
                break
            else:
                chunks.append(chunk)
                print(f"📊 过程: {chunk}")
        
        print(f"\n📈 总共收到 {len(chunks)} 个过程片段")
        print(f"🎯 最终结果成功: {final_result.success if final_result else 'None'}")
        
        return final_result and final_result.success
        
    except Exception as e:
        print(f"❌ 流式执行失败: {e}")
        return False

def test_execute_stream_vs_sync():
    """比较流式执行和同步执行的结果"""
    print("\n🧪 比较流式执行和同步执行...")
    
    # 创建认知智能体
    agent = CognitiveAgent(
        llm=llm_gemini,
        max_cycles=5,
        verbose=False,  # 关闭详细输出以便比较
        enable_super_ego=False,
        evaluation_mode="internal"
    )
    
    task = "计算 5 * 6 的结果"
    
    print(f"📝 任务: {task}")
    
    # 同步执行
    print("🔄 同步执行...")
    sync_result = agent.execute_sync(task)
    
    # 流式执行
    print("🔄 流式执行...")
    stream_result = None
    for chunk in agent.execute_stream(task):
        if isinstance(chunk, Result):
            stream_result = chunk
            break
    
    print(f"\n📊 同步结果: {sync_result.success} - {sync_result.return_value}")
    print(f"📊 流式结果: {stream_result.success if stream_result else 'None'} - {stream_result.return_value if stream_result else 'None'}")
    
    # 比较结果
    if sync_result.success and stream_result and stream_result.success:
        print("✅ 两种执行方式都成功")
        return True
    else:
        print("❌ 执行方式结果不一致")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试 CognitiveAgent.execute_stream 方法")
    print("=" * 60)
    
    # 运行测试
    test_results = []
    
    # 测试1：基本流式执行
    test_results.append(test_execute_stream_basic())
    
    # 测试2：带超我监督的流式执行
    test_results.append(test_execute_stream_with_super_ego())
    
    # 测试3：流式 vs 同步执行比较
    test_results.append(test_execute_stream_vs_sync())
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"✅ 基本流式执行: {'通过' if test_results[0] else '失败'}")
    print(f"✅ 超我监督流式执行: {'通过' if test_results[1] else '失败'}")
    print(f"✅ 流式vs同步对比: {'通过' if test_results[2] else '失败'}")
    
    success_count = sum(test_results)
    total_count = len(test_results)
    
    print(f"\n🎯 总体结果: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！execute_stream 方法已正确实现")
        return True
    else:
        print("❌ 部分测试失败，需要进一步调试")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)