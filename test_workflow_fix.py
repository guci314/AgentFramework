#!/usr/bin/env python3
"""
测试工作流修复效果
=================

验证方案1修复后的工作流生成是否符合要求。
"""

import os
import sys
import json
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from static_workflow.MultiStepAgent_v3 import MultiStepAgent_v3, RegisteredAgent
from pythonTask import Agent
from langchain_openai import ChatOpenAI

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_workflow_generation():
    """测试工作流生成功能"""
    
    print("🧪 测试工作流生成修复效果")
    print("=" * 60)
    
    # 检查API密钥（使用模拟评估器，所以只需要主LLM的密钥）
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("❌ 错误: 请设置DEEPSEEK_API_KEY环境变量")
        return False
    
    try:
        # 创建LLM实例
        print("🔧 初始化DeepSeek语言模型...")
        llm = ChatOpenAI(
            temperature=0,
            model="deepseek-chat",
            base_url="https://api.deepseek.com", 
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            max_tokens=8192
        )
        
        # 创建智能体
        print("🤖 创建智能体...")
        coder_agent = Agent(llm=llm, stateful=True)
        coder_agent.api_specification = "专业编程智能体，擅长Python编程"
        
        tester_agent = Agent(llm=llm, stateful=True)
        tester_agent.api_specification = "专业测试智能体，擅长编写单元测试"
        
        # 创建MultiStepAgent_v3（使用模拟评估器）
        print("🏗️  构建MultiStepAgent_v3...")
        agent_v3 = MultiStepAgent_v3(
            llm=llm,
            registered_agents=[
                RegisteredAgent("coder", coder_agent, "专业编程智能体"),
                RegisteredAgent("tester", tester_agent, "专业测试智能体")
            ],
            use_mock_evaluator=True  # 使用模拟评估器，不需要DeepSeek API
        )
        
        # 测试工作流生成（不实际执行，只生成规划）
        print("📋 生成工作流规划...")
        test_instruction = """
        实现一个计算器类Calculator，保存到文件calculator.py中。
        编写测试用例，保存到文件test_calculator.py中。
        运行测试用例。
        如果测试用例失败，则修复代码，并重新运行测试用例。
        如果测试用例成功，则结束。
        """
        
        # 调用内部方法生成工作流规划
        workflow_definition = agent_v3._generate_workflow_plan(test_instruction)
        
        print("✅ 工作流生成成功！")
        print(f"📊 生成的工作流包含 {len(workflow_definition.steps)} 个步骤")
        
        # 分析生成的工作流
        print("\n" + "=" * 60)
        print("📋 工作流分析")
        print("=" * 60)
        
        test_step = None
        fix_step = None
        
        for step in workflow_definition.steps:
            print(f"\n步骤 {step.id}: {step.name}")
            print(f"  智能体: {step.agent_name}")
            print(f"  类型: {step.instruction_type}")
            
            if step.control_flow:
                cf = step.control_flow
                print(f"  控制流: {cf.type.value}")
                
                # 查找测试步骤（应该使用AI评估）
                if ("test" in step.name.lower() or "run" in step.instruction.lower()) and cf.type.value == "conditional":
                    test_step = step
                    if getattr(cf, 'ai_evaluate_test_result', False):
                        print(f"    ✅ 使用AI评估: {cf.ai_evaluate_test_result}")
                        print(f"    置信度阈值: {getattr(cf, 'ai_confidence_threshold', 'N/A')}")
                        print(f"    回退条件: {getattr(cf, 'ai_fallback_condition', 'N/A')}")
                    else:
                        print(f"    ⚠️  使用传统条件: {getattr(cf, 'condition', 'N/A')}")
                
                # 查找修复步骤（应该使用简单循环）
                elif ("fix" in step.name.lower() or "repair" in step.instruction.lower()) and cf.type.value == "loop":
                    fix_step = step
                    print(f"    循环目标: {cf.loop_target}")
                    print(f"    最大迭代: {cf.max_iterations}")
                    print(f"    循环条件: {cf.loop_condition}")
                    print(f"    退出路径: {getattr(cf, 'exit_on_max', 'N/A')}")
                    
                    # 检查是否符合方案1要求
                    if cf.loop_condition is None and cf.max_iterations and getattr(cf, 'exit_on_max', None):
                        print(f"    ✅ 符合方案1要求")
                    else:
                        print(f"    ❌ 不符合方案1要求")
        
        # 验证修复效果
        print("\n" + "=" * 60)
        print("🔍 修复效果验证")
        print("=" * 60)
        
        success_count = 0
        total_checks = 0
        
        # 检查1：测试步骤应该使用AI评估
        total_checks += 1
        if test_step and getattr(test_step.control_flow, 'ai_evaluate_test_result', False):
            print("✅ 测试步骤正确使用AI评估")
            success_count += 1
        else:
            print("❌ 测试步骤未使用AI评估")
        
        # 检查2：修复步骤应该使用简单循环
        total_checks += 1
        if fix_step:
            cf = fix_step.control_flow
            if (cf.loop_condition is None and 
                cf.max_iterations and 
                getattr(cf, 'exit_on_max', None)):
                print("✅ 修复步骤正确使用简单循环机制")
                success_count += 1
            else:
                print("❌ 修复步骤循环配置不正确")
                print(f"   循环条件: {cf.loop_condition} (应为None)")
                print(f"   最大迭代: {cf.max_iterations} (应设置)")
                print(f"   退出路径: {getattr(cf, 'exit_on_max', None)} (应设置)")
        else:
            print("❌ 未找到修复步骤")
        
        # 检查3：工作流验证
        total_checks += 1
        errors = workflow_definition.validate()
        if not errors:
            print("✅ 工作流定义验证通过")
            success_count += 1
        else:
            print("❌ 工作流定义验证失败:")
            for error in errors:
                print(f"   - {error}")
        
        print(f"\n🏆 验证结果: {success_count}/{total_checks} 项检查通过")
        
        return success_count == total_checks
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    success = test_workflow_generation()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过！方案1修复效果良好。")
    else:
        print("⚠️  部分测试失败，需要进一步检查。")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)