"""
使用llm_lazy.py的多Agent测试

测试多Agent选择功能，使用懒加载模型。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embodied_cognitive_workflow import CognitiveAgent
from python_core import Agent
from llm_lazy import get_model


def main():
    """测试多Agent选择"""
    
    # 设置代理
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"
    
    # 获取语言模型
    llm = get_model('gemini_2_5_flash')
    
    # 创建专业Agent
    
    # 1. 数学计算Agent
    math_agent = Agent(llm=llm)
    math_agent.name = "数学专家"
    math_agent.api_specification = "专精数学计算、公式推导、数值分析"
    
    # 2. 文件处理Agent  
    file_agent = Agent(llm=llm)
    file_agent.name = "文件助手"
    file_agent.api_specification = "专精文件读写、目录管理、文件搜索"
    
    # 3. 通用助手Agent
    general_agent = Agent(llm=llm)
    general_agent.name = "通用助手"
    general_agent.api_specification = "处理各种通用任务、代码编写、问题解答"
    
    # 创建认知智能体
    cognitive_agent = CognitiveAgent(
        llm=llm,
        agents=[math_agent, file_agent, general_agent],
        max_cycles=5,
        verbose=True,
        enable_meta_cognition=False
    )
    
    print("=== 测试多Agent选择功能 ===\n")
    print("可用的专业Agent：")
    for agent in [math_agent, file_agent, general_agent]:
        print(f"- {agent.name}: {agent.api_specification}")
    print()
    
    # 测试1：数学计算任务（应该选择数学专家）
    print("测试1：数学计算任务")
    print("-" * 40)
    result = cognitive_agent.execute_sync("计算 25 * 36 + 78 - 14 的结果")
    if result.success:
        print(f"✅ 结果：{result.return_value}")
    else:
        print(f"❌ 错误：{result.stderr}")
    
    # 检查执行历史
    print("\n执行历史片段：")
    for history in cognitive_agent.execution_history[-5:]:
        print(f"  {history}")
    
    print("\n" + "="*60 + "\n")
    
    # 测试2：文件操作任务（应该选择文件助手）
    print("测试2：文件操作任务")
    print("-" * 40)
    result = cognitive_agent.execute_sync("创建一个test_multi_agent.txt文件，写入'Multi-Agent System Works!'")
    if result.success:
        print(f"✅ 结果：{result.return_value}")
    else:
        print(f"❌ 错误：{result.stderr}")
    
    # 检查文件是否创建成功
    if os.path.exists("test_multi_agent.txt"):
        with open("test_multi_agent.txt", "r") as f:
            content = f.read()
        print(f"文件内容：{content}")
        # 清理文件
        os.remove("test_multi_agent.txt")
        print("已清理测试文件")


if __name__ == "__main__":
    main()