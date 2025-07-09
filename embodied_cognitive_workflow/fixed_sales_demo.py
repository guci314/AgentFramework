#!/usr/bin/env python3
"""
修复后的销售数据分析演示
修复了execute_stream返回生成器的问题
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
    import pythonTask
    from embodied_cognitive_workflow import CognitiveAgent
    
    # 导入LLM实例
    llm_deepseek = pythonTask.llm_deepseek
    
    print("✅ 所有模块导入成功！")
    
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    exit(1)

def main():
    """主函数"""
    print("=== 实际任务演示：销售数据分析（修复后） ===")
    
    # 创建认知代理实例
    cognitive_agent = CognitiveAgent(
        llm=llm_deepseek,
        max_cycles=5,
        verbose=False,  # 减少日志输出
        enable_super_ego=True
    )
    
    # 销售数据分析任务
    sales_task = """
    # 销售数据分析任务
    
    /home/guci/aiProjects/AgentFrameWork/sales_data.csv是销售数据文件，请使用此文件进行数据分析。
    
    # 规则
    1. 不要生成图表
    2. 报告中必须包含每个地区，每个产品，每个销售人员的销售额
    3. 分析报告保存到sales_analysis_report.md
    """
    
    # 执行任务
    print(f"\n⚡ 开始执行销售数据分析任务...")
    start_time = time.time()
    
    try:
        # 修复：正确处理execute_stream返回的生成器
        print("🔄 开始流式执行...")
        result = None
        
        # 遍历生成器获取最终结果
        for chunk in cognitive_agent.execute_stream(sales_task):
            # 检查是否是最终的Result对象
            if hasattr(chunk, 'success'):
                result = chunk
                break
            else:
                # 如果是中间的流式输出，可以选择打印或忽略
                print(f"   📄 流式输出: {str(chunk)[:100]}...")
        
        duration = time.time() - start_time
        
        # 获取工作流状态
        status = cognitive_agent.get_workflow_status()
        
        print(f"\n📊 执行结果:")
        if result:
            print(f"   ✅ 成功: {result.success}")
            print(f"   ⏱️ 时间: {duration:.2f}秒")
            print(f"   🔄 循环: {status['当前循环次数']}轮")
            
            if result.return_value:
                result_str = str(result.return_value)
                if len(result_str) > 300:
                    print(f"   📋 结果: {result_str[:300]}...")
                else:
                    print(f"   📋 结果: {result_str}")
        else:
            print(f"   ⚠️ 未获取到有效结果")
            print(f"   ⏱️ 时间: {duration:.2f}秒")
        
        # 检查是否生成了报告文件
        report_file = '/home/guci/aiProjects/AgentFrameWork/sales_analysis_report.md'
        if os.path.exists(report_file):
            print(f"   📁 报告文件: 已生成 sales_analysis_report.md")
            
            # 显示报告文件的部分内容
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) > 500:
                    print(f"   📄 报告内容预览: {content[:500]}...")
                else:
                    print(f"   📄 报告内容: {content}")
        else:
            print(f"   📁 报告文件: 未找到")
            
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎉 修复后的具身认知工作流演示完成！")
    print(f"✨ 核心改进: 三分法→二分法, 启发式规则, 性能优化")
    print(f"🔧 修复要点: 正确处理execute_stream返回的生成器")

if __name__ == "__main__":
    main()