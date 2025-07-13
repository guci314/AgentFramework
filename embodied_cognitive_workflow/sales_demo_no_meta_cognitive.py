#!/usr/bin/env python3
"""
禁用元认知的销售数据分析演示
测试禁用元认知后的性能表现
"""

import os
import sys
import time

# 设置代理环境变量
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 添加父目录到系统路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 导入必要的模块
try:
    from python_core import *
from llm_lazy import get_model
    from embodied_cognitive_workflow import CognitiveAgent
    
    # 导入LLM实例
    get_model("deepseek_chat") = \1("deepseek_chat")
    
    print("✅ 所有模块导入成功！")
    
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    exit(1)

def main():
    """主函数"""
    print("=== 销售数据分析演示（禁用元认知） ===")
    
    # 创建认知代理实例 - 禁用元认知
    cognitive_agent = CognitiveAgent(
        llm=get_model("deepseek_chat"),
        max_cycles=5,
        verbose=True,  # 启用详细输出观察差异
        enable_meta_cognition=False  # 🔑 关键：禁用元认知
    )
    
    print(f"📋 配置信息:")
    print(f"   🤖 LLM: DeepSeek")
    print(f"   🔄 最大循环: 5")
    print(f"   📢 详细模式: 启用")
    print(f"   🧠 元认知监督: 禁用")
    
    # 销售数据分析任务
    sales_task = """
    # 销售数据分析任务
    
    /home/guci/aiProjects/AgentFrameWork/sales_data.csv是销售数据文件，请使用此文件进行数据分析。
    
    # 规则
    1. 不要生成图表
    2. 报告中必须包含每个地区，每个产品，每个销售人员的销售额
    3. 分析报告保存到sales_analysis_report_no_superego.md
    """
    
    # 执行任务
    print(f"\n⚡ 开始执行销售数据分析任务（禁用元认知）...")
    start_time = time.time()
    
    try:
        # 正确处理execute_stream返回的生成器
        print("🔄 开始流式执行...")
        result = None
        chunk_count = 0
        
        # 遍历生成器获取最终结果
        for chunk in cognitive_agent.execute_stream(sales_task):
            chunk_count += 1
            
            # 检查是否是最终的Result对象
            if hasattr(chunk, 'success'):
                result = chunk
                print(f"   ✅ 获得最终结果 (总共 {chunk_count} 个数据块)")
                break
            else:
                # 显示流式输出
                chunk_str = str(chunk)
                if len(chunk_str) > 150:
                    print(f"   📄 流式输出 #{chunk_count}: {chunk_str[:150]}...")
                else:
                    print(f"   📄 流式输出 #{chunk_count}: {chunk_str}")
        
        duration = time.time() - start_time
        
        # 获取工作流状态
        status = cognitive_agent.get_workflow_status()
        
        print(f"\n📊 执行结果（禁用元认知）:")
        if result:
            print(f"   ✅ 成功: {result.success}")
            print(f"   ⏱️ 时间: {duration:.2f}秒")
            print(f"   🔄 循环: {status['当前循环次数']}轮")
            print(f"   📦 数据块: {chunk_count}个")
            
            if result.return_value:
                result_str = str(result.return_value)
                if len(result_str) > 300:
                    print(f"   📋 结果: {result_str[:300]}...")
                else:
                    print(f"   📋 结果: {result_str}")
        else:
            print(f"   ⚠️ 未获取到有效结果")
            print(f"   ⏱️ 时间: {duration:.2f}秒")
            print(f"   📦 数据块: {chunk_count}个")
        
        # 检查是否生成了报告文件
        report_file = '/home/guci/aiProjects/AgentFrameWork/sales_analysis_report_no_superego.md'
        if os.path.exists(report_file):
            print(f"   📁 报告文件: 已生成 sales_analysis_report_no_superego.md")
            
            # 显示报告文件大小
            file_size = os.path.getsize(report_file)
            print(f"   📏 文件大小: {file_size} 字节")
            
            # 显示报告文件的部分内容
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                print(f"   📄 报告行数: {len(lines)}")
                
                if len(content) > 500:
                    print(f"   📄 报告内容预览: {content[:500]}...")
                else:
                    print(f"   📄 报告内容: {content}")
        else:
            print(f"   📁 报告文件: 未找到")
        
        # 对比分析
        print(f"\n🔍 禁用元认知的影响分析:")
        print(f"   🧠 元认知监督: 已禁用")
        print(f"   🎯 执行模式: 自我-本我双层架构")
        print(f"   ⚡ 性能影响: 减少元认知开销")
        print(f"   🔄 循环次数: {status['当前循环次数']}轮")
        print(f"   ⏱️ 执行时间: {duration:.2f}秒")
        
        # 验证元认知状态
        meta_cognition_state = cognitive_agent.get_meta_cognition_state()
        print(f"\n🧠 元认知状态验证:")
        print(f"   启用状态: {meta_cognition_state.get('enabled', 'Unknown')}")
        print(f"   监控状态: {meta_cognition_state.get('monitoring', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎉 禁用元认知的具身认知工作流演示完成！")
    print(f"🔧 测试目的: 验证禁用元认知后的性能和功能表现")
    print(f"📊 对比要点: 执行时间、循环次数、结果质量")

if __name__ == "__main__":
    main()