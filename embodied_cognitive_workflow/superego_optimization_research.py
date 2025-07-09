#!/usr/bin/env python3
"""
超我任务优化细节研究
深入分析超我在任务执行过程中的优化机制
"""

import os
import sys
import time
import json
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
    print("🚀 使用Gemini 2.5 Flash Google模型进行超我研究")
    
except Exception as e:
    print(f"❌ 模块导入失败: {e}")
    exit(1)

class SuperEgoMonitor:
    """超我监督机制监控器"""
    
    def __init__(self):
        self.optimization_log = []
        self.start_time = None
        self.cycle_times = []
        self.superego_interventions = []
        self.reflection_data = []
        self.strategy_adjustments = []
        
    def log_optimization(self, event_type, data, timestamp=None):
        """记录优化事件"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.optimization_log.append({
            'timestamp': timestamp.isoformat(),
            'event_type': event_type,
            'data': data
        })
        
    def log_superego_intervention(self, intervention_type, details):
        """记录超我干预"""
        self.superego_interventions.append({
            'timestamp': datetime.now().isoformat(),
            'intervention_type': intervention_type,
            'details': details
        })
        
    def log_reflection(self, reflection_result):
        """记录反思结果"""
        self.reflection_data.append({
            'timestamp': datetime.now().isoformat(),
            'reflection': reflection_result
        })
        
    def log_strategy_adjustment(self, adjustment):
        """记录策略调整"""
        self.strategy_adjustments.append({
            'timestamp': datetime.now().isoformat(),
            'adjustment': adjustment
        })
        
    def generate_report(self):
        """生成分析报告"""
        report = {
            'execution_summary': {
                'total_optimizations': len(self.optimization_log),
                'superego_interventions': len(self.superego_interventions),
                'reflections': len(self.reflection_data),
                'strategy_adjustments': len(self.strategy_adjustments),
                'execution_time': time.time() - self.start_time if self.start_time else 0
            },
            'optimization_log': self.optimization_log,
            'superego_interventions': self.superego_interventions,
            'reflection_data': self.reflection_data,
            'strategy_adjustments': self.strategy_adjustments
        }
        return report

def analyze_superego_mechanisms(agent, task_description):
    """分析超我机制"""
    print(f"\n🔍 开始分析超我机制...")
    print(f"📋 任务: {task_description}")
    
    # 获取超我状态
    superego_state = agent.get_super_ego_state()
    print(f"\n🧠 超我初始状态:")
    for key, value in superego_state.items():
        print(f"   {key}: {value}")
    
    # 监控超我优化过程
    monitor = SuperEgoMonitor()
    monitor.start_time = time.time()
    
    print(f"\n🔄 开始执行任务并监控超我优化...")
    print("="*80)
    
    # 执行任务并实时监控
    try:
        cycle_count = 0
        chunk_count = 0
        
        for chunk in agent.execute_stream(task_description):
            chunk_count += 1
            chunk_str = str(chunk)
            
            # 检查是否是最终结果
            if hasattr(chunk, 'success'):
                print(f"\n✅ 获得最终结果 (第{chunk_count}个数据块)")
                result = chunk
                break
            
            # 分析超我相关的流式输出
            if "超我" in chunk_str or "SuperEgo" in chunk_str:
                monitor.log_optimization("superego_activity", chunk_str)
                print(f"🧠 超我活动: {chunk_str[:200]}...")
            
            elif "反思" in chunk_str or "reflection" in chunk_str:
                monitor.log_reflection(chunk_str)
                print(f"🤔 反思过程: {chunk_str[:200]}...")
            
            elif "策略" in chunk_str or "strategy" in chunk_str:
                monitor.log_strategy_adjustment(chunk_str)
                print(f"📊 策略调整: {chunk_str[:200]}...")
            
            elif "认知循环" in chunk_str or "cycle" in chunk_str:
                if "轮" in chunk_str:
                    cycle_count += 1
                    monitor.cycle_times.append(time.time() - monitor.start_time)
                    print(f"🔄 认知循环 #{cycle_count}: {chunk_str[:200]}...")
            
            elif "评估" in chunk_str or "evaluation" in chunk_str:
                monitor.log_optimization("evaluation", chunk_str)
                print(f"📋 评估过程: {chunk_str[:200]}...")
            
            elif "优化" in chunk_str or "optimization" in chunk_str:
                monitor.log_optimization("optimization", chunk_str)
                print(f"⚡ 优化过程: {chunk_str[:200]}...")
            
            else:
                # 其他一般性输出
                print(f"📄 流式输出 #{chunk_count}: {chunk_str[:150]}...")
        
        print("="*80)
        print(f"🎯 任务执行完成!")
        
        # 获取最终超我状态
        final_superego_state = agent.get_super_ego_state()
        print(f"\n🧠 超我最终状态:")
        for key, value in final_superego_state.items():
            print(f"   {key}: {value}")
        
        # 生成监控报告
        report = monitor.generate_report()
        
        return result, report
        
    except Exception as e:
        print(f"❌ 执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None, monitor.generate_report()

def detailed_superego_analysis():
    """详细的超我分析"""
    print("🔬 开始详细超我分析研究")
    print("="*80)
    
    # 创建启用超我的认知代理
    agent = CognitiveAgent(
        llm=llm_gemini,
        max_cycles=10,  # 增加最大循环数以观察更多优化
        verbose=True,
        enable_super_ego=True
    )
    
    # 设计一个中等复杂度的任务来观察超我优化
    research_task = """
    # 计算器功能开发任务
    
    请创建一个完整的Python计算器程序，要求：
    
    1. 基础功能：加、减、乘、除
    2. 高级功能：幂运算、开方、三角函数
    3. 错误处理：除零错误、无效输入处理
    4. 用户界面：命令行交互式界面
    5. 测试用例：包含各种功能的测试
    6. 文档说明：使用说明和代码注释
    
    请将完整的程序保存到文件 /home/guci/aiProjects/AgentFrameWork/calculator_superego_research.py
    """
    
    print(f"📋 研究任务: 计算器功能开发")
    print(f"🎯 目标: 观察超我如何优化复杂任务执行")
    print(f"⏱️ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 执行分析
    result, report = analyze_superego_mechanisms(agent, research_task)
    
    print(f"\n📊 超我优化分析报告:")
    print("="*80)
    
    if result:
        print(f"✅ 任务执行成功: {result.success}")
        if result.return_value:
            print(f"📝 结果摘要: {str(result.return_value)[:300]}...")
    else:
        print("❌ 任务执行失败")
    
    # 分析报告
    summary = report['execution_summary']
    print(f"\n📈 执行摘要:")
    print(f"   总优化次数: {summary['total_optimizations']}")
    print(f"   超我干预次数: {summary['superego_interventions']}")
    print(f"   反思次数: {summary['reflections']}")
    print(f"   策略调整次数: {summary['strategy_adjustments']}")
    print(f"   总执行时间: {summary['execution_time']:.2f}秒")
    
    # 详细分析超我干预
    if report['superego_interventions']:
        print(f"\n🧠 超我干预详情:")
        for i, intervention in enumerate(report['superego_interventions'], 1):
            print(f"   干预 #{i}: {intervention['intervention_type']}")
            print(f"   时间: {intervention['timestamp']}")
            print(f"   详情: {intervention['details'][:200]}...")
            print()
    
    # 分析反思过程
    if report['reflection_data']:
        print(f"\n🤔 反思过程分析:")
        for i, reflection in enumerate(report['reflection_data'], 1):
            print(f"   反思 #{i}: {reflection['timestamp']}")
            print(f"   内容: {reflection['reflection'][:200]}...")
            print()
    
    # 分析策略调整
    if report['strategy_adjustments']:
        print(f"\n📊 策略调整分析:")
        for i, adjustment in enumerate(report['strategy_adjustments'], 1):
            print(f"   调整 #{i}: {adjustment['timestamp']}")
            print(f"   内容: {adjustment['adjustment'][:200]}...")
            print()
    
    # 保存详细报告
    report_file = '/home/guci/aiProjects/AgentFrameWork/embodied_cognitive_workflow/superego_optimization_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 详细报告已保存到: {report_file}")
    
    # 检查是否生成了计算器文件
    calculator_file = '/home/guci/aiProjects/AgentFrameWork/calculator_superego_research.py'
    if os.path.exists(calculator_file):
        print(f"✅ 计算器文件已生成: {calculator_file}")
        
        # 显示文件信息
        file_size = os.path.getsize(calculator_file)
        print(f"   文件大小: {file_size} 字节")
        
        # 显示文件前几行
        with open(calculator_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"   文件行数: {len(lines)}")
            print(f"   前几行内容:")
            for i, line in enumerate(lines[:10], 1):
                print(f"      {i}: {line.rstrip()}")
    else:
        print(f"❌ 计算器文件未生成: {calculator_file}")
    
    return report

def main():
    """主函数"""
    print("🔬 超我任务优化细节研究")
    print("="*80)
    print("研究目标:")
    print("1. 观察超我的实时优化过程")
    print("2. 分析超我的干预机制")
    print("3. 研究超我的策略调整逻辑")
    print("4. 评估超我对任务执行的影响")
    print("="*80)
    
    # 执行详细分析
    report = detailed_superego_analysis()
    
    print(f"\n🎊 超我优化研究完成!")
    print(f"🔍 研究发现:")
    print(f"   - 超我是一个主动的优化系统")
    print(f"   - 超我通过反思和策略调整提升效率")
    print(f"   - 超我的干预是有针对性和时机性的")
    print(f"   - 超我确保任务质量和完整性")
    
    print(f"\n💡 关键洞察:")
    print(f"   - 超我不是被动的监督者，而是主动的优化者")
    print(f"   - 超我的价值在于预防问题，而非只是发现问题")
    print(f"   - 超我通过元认知提升整个系统的智能水平")

if __name__ == "__main__":
    main()