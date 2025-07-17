"""
简单的多Agent测试

直接使用langchain创建LLM，测试多Agent选择功能。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embodied_cognitive_workflow import CognitiveAgent
from python_core import Agent
from langchain_google_genai import ChatGoogleGenerativeAI


def main():
    """测试多Agent选择"""
    
    # 设置代理
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"
    
    # 创建语言模型
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0.1,
        max_output_tokens=2000,
    )
    
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
    
    # 测试1：数学计算任务（应该选择数学专家）
    print("测试1：数学计算任务")
    print("-" * 40)
    result = cognitive_agent.execute_sync("计算 25 * 36 + 78 - 14")
    print(f"结果：{result.return_value if result.success else result.stderr}\n")
    
    # 打印执行历史查看是否选择了正确的Agent
    if cognitive_agent.execution_history:
        print("执行历史片段：")
        for history in cognitive_agent.execution_history[-3:]:
            print(f"  {history}")


if __name__ == "__main__":
    main()