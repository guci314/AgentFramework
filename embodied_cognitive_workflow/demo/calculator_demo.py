"""
具身认知工作流 Calculator 演示

这个演示展示了如何使用具身认知工作流系统生成一个Calculator类和单元测试。
验证了增量式规划的认知循环和自我-本我-身体三层架构的协作。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embodied_cognitive_workflow import CognitiveAgent
from langchain_openai import ChatOpenAI
import os
from llm_lazy import get_model

def 运行Calculator演示():
    """
    运行Calculator类生成演示
    """
    print("=== 具身认知工作流 Calculator 演示 ===\n")
    
    # 初始化语言模型
    # 注意：需要设置环境变量 DEEPSEEK_API_KEY
    try:
        llm = get_model("gemini_2_5_flash")
        print("✓ DeepSeek语言模型初始化成功")
    except Exception as e:
        print(f"❌ 语言模型初始化失败：{e}")
        print("请确保已设置 DEEPSEEK_API_KEY 环境变量")
        return
    
    # 创建具身认知工作流
    try:
        工作流 = CognitiveAgent(
            llm=llm,
            max_cycles=30,
            verbose=True
        )
        工作流.loadKnowledge('unittest的测试结果在标准错误流中而不是标准输出流中')
        print("✓ 具身认知工作流初始化成功")
    except Exception as e:
        print(f"❌ 工作流初始化失败：{e}")
        return
    
    # 定义任务：生成Calculator类和单元测试
    任务描述 = """
请开发一个完整的Calculator类和对应的单元测试。请创建两个文件：calculator.py（Calculator类）和 test_calculator.py（单元测试）要求如下：

1. Calculator类功能：
   - 基本四则运算：加法、减法、乘法、除法
   - 错误处理：除零检查

2. 单元测试要求：
   - 测试所有基本功能
   - 测试边界条件和错误情况
   - 使用unittest框架

3. 验证要求：
   - 代码能够正常运行
   - 所有测试能够通过
   - 功能完整可用

请使用python3运行
"""
    
    print(f"\n📋 任务描述：\n{任务描述}\n")
    print("🚀 开始执行具身认知工作流...\n")
    
    # 执行工作流
    try:
        结果 = 工作流.execute_cognitive_cycle(任务描述)
        
        print("\n" + "="*60)
        print("🎯 工作流执行完成")
        print("="*60)
        
        if 结果.success:
            print("✅ 执行状态：成功")
            print(f"\n📊 最终结果：\n{结果.return_value}")
            
            # 获取工作流状态信息
            状态信息 = 工作流.get_workflow_status()
            print(f"\n📈 工作流统计：")
            print(f"   循环次数：{状态信息['当前循环次数']}/{状态信息['最大循环次数']}")
            print(f"   最终状态：{状态信息['状态']}")
            print(f"   目标描述：{状态信息['目标描述']}")
            
        else:
            print("❌ 执行状态：失败")
            print(f"\n❗ 失败原因：\n{结果.return_value}")
            
    except Exception as e:
        print(f"\n💥 工作流执行异常：{e}")
        import traceback
        traceback.print_exc()


def 测试具身认知组件():
    """
    单独测试具身认知工作流的各个组件
    """
    print("\n=== 组件单元测试 ===\n")
    
    try:
        llm = ChatOpenAI(
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            temperature=0.1
        )
        
        # 测试自我智能体
        print("🧠 测试自我智能体...")
        from ego_agent import EgoAgent
        自我 = EgoAgent(llm)
        
        测试状态 = "当前需要创建一个Calculator类，已经了解了基本需求"
        状态分析 = 自我.analyze_current_state(测试状态)
        print(f"   状态分析：{状态分析[:100]}...")
        
        决策 = 自我.decide_next_action(状态分析)
        print(f"   决策结果：{决策}")
        
        # 测试本我智能体
        print("\n💖 测试本我智能体...")
        from id_agent import IdAgent
        本我 = IdAgent(llm)
        
        测试指令 = "创建一个功能完整的Calculator类"
        价值系统 = 本我.initialize_value_system(测试指令)
        print(f"   价值系统：{价值系统[:100]}...")
        
        print("\n✅ 组件测试完成")
        
    except Exception as e:
        print(f"❌ 组件测试失败：{e}")


def main():
    """主函数"""
    print("具身认知工作流 Calculator 演示程序")
    print("====================================")
    
    # 检查环境变量
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("⚠️  请设置 DEEPSEEK_API_KEY 环境变量")
        print("   例如：export DEEPSEEK_API_KEY='your-api-key'")
        print("\n🔧 如果只是测试导入功能，可以运行组件测试（不需要API密钥）")
        print("   python3 -c \"from embodied_cognitive_workflow import *; print('所有组件导入成功!')\"")
        return
    
    运行Calculator演示()


if __name__ == "__main__":
    main()