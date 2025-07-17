"""
多Agent协作示例

演示如何使用具身认知工作流系统的多Agent功能。
创建专业的Agent并让认知系统智能选择合适的Agent执行任务。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embodied_cognitive_workflow import CognitiveAgent
from python_core import Agent, get_llm


def create_calculator_agent(llm):
    """创建计算器Agent"""
    calculator = Agent(
        llm=llm,
        system_message="""你是一个专业的计算器Agent，专门处理数学计算任务。
你可以：
1. 执行基础数学运算（加减乘除、幂运算、开方等）
2. 处理复杂的数学表达式
3. 解决数学问题和方程
4. 提供计算步骤说明

请使用Python代码执行所有计算任务。"""
    )
    calculator.name = "计算器"
    calculator.api_specification = "数学计算、表达式求值、方程求解、统计计算"
    return calculator


def create_data_analyst_agent(llm):
    """创建数据分析Agent"""
    analyst = Agent(
        llm=llm,
        system_message="""你是一个专业的数据分析Agent，专门处理数据分析任务。
你可以：
1. 分析数据集并生成统计报告
2. 创建数据可视化图表
3. 执行数据清洗和预处理
4. 进行趋势分析和预测

请使用pandas、numpy、matplotlib等库进行数据分析。"""
    )
    analyst.name = "数据分析师"
    analyst.api_specification = "数据分析、可视化、统计报告、趋势预测、数据清洗"
    
    # 加载数据分析相关模块
    analyst.loadPythonModules(['pandas', 'numpy', 'matplotlib.pyplot'])
    return analyst


def create_file_manager_agent(llm):
    """创建文件管理Agent"""
    file_manager = Agent(
        llm=llm,
        system_message="""你是一个专业的文件管理Agent，专门处理文件和目录操作。
你可以：
1. 创建、读取、写入和删除文件
2. 管理目录结构
3. 搜索和查找文件
4. 处理文件格式转换

请使用os、pathlib等模块进行文件操作。"""
    )
    file_manager.name = "文件管理员"
    file_manager.api_specification = "文件操作、目录管理、文件搜索、格式转换、文件信息查询"
    
    # 加载文件操作相关模块
    file_manager.loadPythonModules(['os', 'pathlib', 'shutil'])
    return file_manager


def create_web_scraper_agent(llm):
    """创建网络爬虫Agent"""
    scraper = Agent(
        llm=llm,
        system_message="""你是一个专业的网络爬虫Agent，专门处理网络数据采集任务。
你可以：
1. 抓取网页内容
2. 解析HTML和XML
3. 提取结构化数据
4. 处理API请求

请使用requests、beautifulsoup4等库进行网络数据采集。"""
    )
    scraper.name = "网络爬虫"
    scraper.api_specification = "网页抓取、HTML解析、API调用、数据提取、网络请求"
    
    # 加载网络相关模块
    scraper.loadPythonModules(['requests', 'json'])
    return scraper


def main():
    """主函数：演示多Agent协作"""
    
    # 设置代理
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"
    
    # 获取语言模型
    llm = get_llm("gemini")
    
    # 创建专业Agent列表
    agents = [
        create_calculator_agent(llm),
        create_data_analyst_agent(llm),
        create_file_manager_agent(llm),
        create_web_scraper_agent(llm)
    ]
    
    # 创建认知智能体，传入多个专业Agent
    cognitive_agent = CognitiveAgent(
        llm=llm,
        agents=agents,  # 传入多个专业Agent
        max_cycles=10,
        verbose=True,
        enable_meta_cognition=False,  # 暂时关闭元认知
        evaluation_mode="internal"
    )
    
    print("=== 多Agent协作示例 ===")
    print("\n可用的专业Agent：")
    for agent in agents:
        print(f"- {agent.name}: {agent.api_specification}")
    
    # 测试任务列表
    test_tasks = [
        "计算 (15 + 23) * 4 - 56 / 8 的结果",
        "创建一个名为test_data的目录，并在其中创建一个hello.txt文件，写入'Hello, Multi-Agent!'",
        "生成一个包含10个随机数的列表，计算平均值和标准差",
        "获取当前目录下所有Python文件的列表",
        "计算斐波那契数列的前20项"
    ]
    
    # 执行测试任务
    for i, task in enumerate(test_tasks, 1):
        print(f"\n\n{'='*60}")
        print(f"任务 {i}: {task}")
        print('='*60)
        
        try:
            # 执行任务
            result = cognitive_agent.execute_sync(task)
            
            if result.success:
                print(f"\n✅ 任务成功完成")
                print(f"结果：{result.return_value}")
            else:
                print(f"\n❌ 任务执行失败")
                print(f"错误：{result.stderr}")
                
        except Exception as e:
            print(f"\n❌ 发生异常：{e}")
        
        print(f"\n执行历史：")
        for j, history in enumerate(cognitive_agent.execution_history[-5:], 1):
            print(f"{j}. {history}")
    
    # 测试复杂的多步骤任务
    print(f"\n\n{'='*60}")
    print("复杂任务测试：数据分析工作流")
    print('='*60)
    
    complex_task = """
    1. 创建一个包含100个随机数的数据集（范围0-100）
    2. 计算这些数据的基本统计信息（平均值、中位数、标准差）
    3. 将结果保存到stats_report.txt文件中
    """
    
    result = cognitive_agent.execute_sync(complex_task)
    if result.success:
        print(f"\n✅ 复杂任务成功完成")
        print(f"结果：{result.return_value}")
    else:
        print(f"\n❌ 复杂任务执行失败")
        print(f"错误：{result.stderr}")


if __name__ == "__main__":
    main()