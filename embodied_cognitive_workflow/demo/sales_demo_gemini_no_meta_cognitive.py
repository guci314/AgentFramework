#!/usr/bin/env python3
"""
使用Gemini 2.5 Flash的销售数据分析演示 - 禁用元认知
测试禁用元认知在快速模型上的表现
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
    
    # 使用正确的Gemini模型
    llm_gemini = \1("gemini_2_5_flash")
    
    print("✅ 所有模块导入成功！")
    print("🚀 使用Gemini 2.5 Flash Google模型")
    
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    exit(1)

def main():
    """主函数"""
    print("=== 销售数据分析演示（Gemini 2.5 Flash + 禁用元认知） ===")
    
    # 确保报告文件不存在
    report_file = '/home/guci/aiProjects/AgentFrameWork/sales_analysis_report_gemini_no_superego.md'
    if os.path.exists(report_file):
        os.remove(report_file)
        print("🗑️ 已删除旧报告文件")
    
    # 创建认知代理实例 - 使用Gemini，禁用元认知
    cognitive_agent = CognitiveAgent(
        llm=llm_gemini,
        max_cycles=5,
        verbose=True,
        enable_meta_cognition=False  # 禁用元认知
    )
    
    print(f"📋 配置信息:")
    print(f"   🤖 LLM: Gemini 2.5 Flash Google")
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
    3. 分析报告保存到sales_analysis_report_gemini_no_superego.md
    """
    
    # 执行任务
    print(f"\n⚡ 开始执行销售数据分析任务（Gemini 2.5 Flash + 禁用元认知）...")
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
        
        print(f"\n📊 执行结果（Gemini 2.5 Flash + 禁用元认知）:")
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
        if os.path.exists(report_file):
            print(f"   📁 报告文件: ✅ 已生成 sales_analysis_report_gemini_no_superego.md")
            
            # 显示报告文件信息
            file_size = os.path.getsize(report_file)
            print(f"   📏 文件大小: {file_size} 字节")
            
            # 显示报告文件的部分内容
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                print(f"   📄 报告行数: {len(lines)}")
                
                # 显示前几行内容
                preview_lines = lines[:10]
                print(f"   📄 报告预览:")
                for i, line in enumerate(preview_lines, 1):
                    if line.strip():
                        print(f"      {i}: {line}")
        else:
            print(f"   📁 报告文件: ❌ 未生成")
        
        # 性能分析
        print(f"\n🚀 Gemini 2.5 Flash性能分析（禁用元认知）:")
        print(f"   🤖 模型: Gemini 2.5 Flash Google")
        print(f"   ⚡ 速度优势: 更快的响应时间")
        print(f"   🧠 元认知监督: 禁用")
        print(f"   ⏱️ 总执行时间: {duration:.2f}秒")
        print(f"   🔄 认知循环: {status['当前循环次数']}轮")
        
        # 验证元认知状态
        meta_cognition_state = cognitive_agent.get_meta_cognition_state()
        print(f"\n🧠 元认知状态:")
        print(f"   启用: {meta_cognition_state.get('enabled', 'Unknown')}")
        print(f"   监控: {meta_cognition_state.get('monitoring', 'Unknown')}")
        
        # 成功标志
        if result and result.success and os.path.exists(report_file):
            print(f"\n🎉 任务完成成功！")
            print(f"   ✅ 认知循环正常结束")
            print(f"   ✅ 报告文件生成完成")
            print(f"   ✅ 禁用元认知情况下完成任务")
            print(f"   ✅ Gemini 2.5 Flash性能表现优秀")
        else:
            print(f"\n⚠️ 任务可能未完全完成")
            
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎊 Gemini 2.5 Flash销售数据分析演示完成（禁用元认知）！")
    print(f"🔧 测试目的: 验证在快速模型上禁用元认知的表现")

if __name__ == "__main__":
    main()