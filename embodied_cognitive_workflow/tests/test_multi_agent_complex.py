"""
复杂任务的多Agent测试

使用更复杂的任务来确保进入认知循环模式，测试多Agent选择功能。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embodied_cognitive_workflow import CognitiveAgent
from python_core import Agent
from llm_lazy import get_model


def main():
    """测试多Agent选择 - 复杂任务"""
    
    # 设置代理
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"
    
    # 获取语言模型
    llm = get_model('gemini_2_5_flash')
    
    # 创建专业Agent
    
    # 1. 数学分析Agent
    math_agent = Agent(llm=llm)
    math_agent.name = "数学分析师"
    math_agent.api_specification = "专精复杂数学分析、统计计算、数据分析、可视化图表"
    
    # 2. 文件处理Agent  
    file_agent = Agent(llm=llm)
    file_agent.name = "数据管理员"
    file_agent.api_specification = "专精文件读写、数据存储、CSV处理、JSON操作"
    
    # 3. 算法专家Agent
    algo_agent = Agent(llm=llm)
    algo_agent.name = "算法工程师"
    algo_agent.api_specification = "专精算法设计、数据结构、性能优化、复杂度分析"
    
    # 创建认知智能体
    cognitive_agent = CognitiveAgent(
        llm=llm,
        agents=[math_agent, file_agent, algo_agent],
        max_cycles=10,
        verbose=True,
        enable_meta_cognition=False,
        evaluation_mode="internal"
    )
    
    print("=== 测试多Agent协作处理复杂任务 ===\n")
    print("可用的专业Agent：")
    for agent in [math_agent, file_agent, algo_agent]:
        print(f"- {agent.name}: {agent.api_specification}")
    print()
    
    # 复杂任务：需要多步骤和多Agent协作
    complex_task = """
    请完成以下数据分析任务：
    1. 生成一个包含100个随机数的数据集（范围1-1000）
    2. 计算这些数据的统计信息（平均值、中位数、标准差、最大值、最小值）
    3. 找出所有大于平均值的数字
    4. 将结果保存到 analysis_report.json 文件中
    5. 再创建一个summary.txt文件，用人类可读的格式总结分析结果
    """
    
    print("执行复杂任务：")
    print("-" * 60)
    print(complex_task)
    print("-" * 60)
    
    result = cognitive_agent.execute_sync(complex_task)
    
    if result.success:
        print(f"\n✅ 任务成功完成")
        print(f"结果：{result.return_value}")
    else:
        print(f"\n❌ 任务执行失败")
        print(f"错误：{result.stderr}")
    
    # 显示执行历史，查看Agent选择情况
    print("\n执行历史：")
    print("=" * 60)
    for i, history in enumerate(cognitive_agent.execution_history[-20:], 1):
        if "执行者" in history or "选择" in history or "Agent" in history:
            print(f"{i}. {history}")
    
    # 检查生成的文件
    print("\n检查生成的文件：")
    for filename in ["analysis_report.json", "summary.txt"]:
        if os.path.exists(filename):
            print(f"\n📄 {filename} 内容：")
            with open(filename, "r") as f:
                content = f.read()
                if len(content) > 200:
                    print(content[:200] + "...")
                else:
                    print(content)
            # 清理文件
            os.remove(filename)
            print(f"已清理 {filename}")
        else:
            print(f"❌ {filename} 未找到")


if __name__ == "__main__":
    main()