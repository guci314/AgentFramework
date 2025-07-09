#!/usr/bin/env python3
"""
测试流式输出修复效果
"""

import os
import sys

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
    
    print("✅ 模块导入成功！")
    
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)

def test_stream_output_clean():
    """测试流式输出是否干净（无重复前缀）"""
    print("\n🧪 测试流式输出清洁度...")
    
    # 创建认知智能体
    agent = CognitiveAgent(
        llm=llm_gemini,
        max_cycles=3,
        verbose=False,  # 关闭详细输出以便观察流式输出
        enable_super_ego=False,
        evaluation_mode="external"  # 使用外观评估来触发身体观察
    )
    
    # 简单的环境变量检查任务
    task = "检查是否能读取环境变量$HOME"
    
    print(f"📝 任务: {task}")
    print("🔄 开始流式执行...")
    
    chunks = []
    final_result = None
    
    try:
        for chunk in agent.execute_stream(task):
            if isinstance(chunk, Result):
                final_result = chunk
                print(f"✅ 最终结果: {chunk.success}")
                break
            else:
                chunks.append(str(chunk))
                print(f"📊 过程: {chunk}")
        
        # 检查是否有重复的前缀问题
        print(f"\n🔍 输出质量检查:")
        print(f"📈 总共收到 {len(chunks)} 个过程片段")
        
        # 检查是否有问题的输出
        problem_chunks = []
        for i, chunk in enumerate(chunks):
            # 检查是否有重复的前缀
            if chunk.count('[身体观察]') > 1 or chunk.count('[身体执行]') > 1:
                problem_chunks.append((i, chunk))
        
        if problem_chunks:
            print(f"❌ 发现 {len(problem_chunks)} 个有问题的片段:")
            for i, chunk in problem_chunks[:3]:  # 只显示前3个
                print(f"   #{i}: {chunk[:100]}...")
        else:
            print("✅ 所有流式输出都是干净的，无重复前缀")
        
        return len(problem_chunks) == 0
        
    except Exception as e:
        print(f"❌ 流式执行失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 测试流式输出修复效果")
    print("=" * 50)
    
    success = test_stream_output_clean()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 流式输出修复成功！输出干净无重复前缀")
    else:
        print("❌ 仍存在流式输出问题，需要进一步修复")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)