"""
MultiStepAgent_v3 静态工作流演示
===============================

演示如何使用MultiStepAgent_v3执行静态工作流。
"""

import os
import sys
from pathlib import Path
from langchain_openai import ChatOpenAI

# 导入必要的模块
from pythonTask import Agent
from static_workflow.MultiStepAgent_v3 import MultiStepAgent_v3

from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

def main():
    """主演示函数"""
    
    print("=" * 60)
    print("MultiStepAgent_v3 静态工作流演示")
    print("=" * 60)
    
    # 检查API密钥
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("❌ 错误: 请设置 DEEPSEEK_API_KEY 环境变量")
        print("   export DEEPSEEK_API_KEY='your_api_key_here'")
        return
    
    # 配置DeepSeek模型
    llm_deepseek = ChatOpenAI(
        temperature=0,
        model="deepseek-chat",  
        base_url="https://api.deepseek.com",
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        max_tokens=8192
    )
    
    print("✅ DeepSeek模型配置完成")
    
    try:
        # 初始化MultiStepAgent_v3
        print("\n🚀 初始化MultiStepAgent_v3...")
        agent_v3 = MultiStepAgent_v3(llm=llm_deepseek)
        
        # 创建智能体团队
        print("👥 创建智能体团队...")
        setup_agent_team(agent_v3, llm_deepseek)
        
        # 演示工作流列表
        print("\n📋 可用工作流:")
        available_workflows = agent_v3.list_available_workflows()
        for i, workflow in enumerate(available_workflows, 1):
            print(f"   {i}. {workflow}")
        
        if not available_workflows:
            print("   没有找到可用的工作流配置文件")
            return
        
        # 演示工作流信息
        print("\n📄 工作流详细信息:")
        for workflow_file in available_workflows:
            if workflow_file.endswith('.json'):
                try:
                    info = agent_v3.get_workflow_info(workflow_file)
                    print(f"\n   📋 {workflow_file}:")
                    print(f"      名称: {info['name']}")
                    print(f"      版本: {info['version']}")
                    print(f"      描述: {info['description']}")
                    print(f"      步骤数: {info['total_steps']}")
                    print(f"      所需智能体: {', '.join(info['required_agents'])}")
                except Exception as e:
                    print(f"      ❌ 获取信息失败: {e}")
        
        # 演示简单工作流执行
        print(f"\n{'='*60}")
        print("执行简单演示工作流")
        print("="*60)
        
        demo_workflow = create_demo_workflow()
        
        print("🔄 开始执行演示工作流...")
        result = agent_v3.execute_workflow(demo_workflow)
        
        # 显示执行结果
        display_execution_result(result)
        
        # 如果有计算器工作流，演示执行
        if "calculator_workflow.json" in available_workflows:
            print(f"\n{'='*60}")
            print("执行计算器工作流演示")
            print("="*60)
            
            try:
                print("🔄 开始执行计算器工作流...")
                calc_result = agent_v3.execute_workflow_from_file("calculator_workflow.json")
                display_execution_result(calc_result)
                
            except Exception as e:
                print(f"❌ 计算器工作流执行失败: {e}")
        
        print(f"\n{'='*60}")
        print("演示完成!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断演示")
    except Exception as e:
        print(f"\n❌ 演示执行失败: {e}")
        import traceback
        traceback.print_exc()


def setup_agent_team(agent_v3, llm):
    """设置智能体团队"""
    
    # 代码开发者
    coder = Agent(
        llm=llm,
        stateful=True,
        thinker_system_message="你是一个专业的Python开发者，擅长编写高质量的代码。"
    )
    
    # 测试工程师
    tester = Agent(
        llm=llm,
        stateful=True,
        thinker_system_message="你是一个专业的软件测试工程师，擅长编写和执行测试用例。"
    )
    
    # 数据分析师
    analyst = Agent(
        llm=llm,
        stateful=True,
        thinker_system_message="你是一个专业的数据分析师，擅长分析和解释数据。"
    )
    
    # 注册智能体
    agent_v3.register_agent("coder", coder, "Python开发专家")
    agent_v3.register_agent("tester", tester, "软件测试专家")
    agent_v3.register_agent("analyst", analyst, "数据分析专家")
    
    print(f"   ✅ 已注册 {len(agent_v3.registered_agents)} 个智能体")


def create_demo_workflow():
    """创建演示工作流"""
    
    demo_workflow_dict = {
        "workflow_metadata": {
            "name": "hello_static_workflow",
            "version": "1.0",
            "description": "静态工作流Hello World演示",
            "author": "MultiStepAgent_v3 Demo"
        },
        "global_variables": {
            "greeting": "Hello, Static Workflow!",
            "language": "Python"
        },
        "steps": [
            {
                "id": "create_greeting",
                "name": "创建问候程序",
                "agent_name": "coder",
                "instruction": "创建一个简单的Python程序，打印问候语 '${greeting}'。程序应该包含一个main函数。",
                "instruction_type": "execution",
                "expected_output": "Python问候程序",
                "timeout": 60,
                "control_flow": {
                    "type": "sequential",
                    "success_next": "test_greeting",
                    "failure_next": "error_handling"
                }
            },
            {
                "id": "test_greeting",
                "name": "测试问候程序",
                "agent_name": "tester",
                "instruction": "运行刚刚创建的Python问候程序，验证输出是否正确包含 '${greeting}'。",
                "instruction_type": "execution",
                "expected_output": "测试结果",
                "timeout": 30,
                "control_flow": {
                    "type": "conditional",
                    "condition": "last_result.success == true",
                    "success_next": "analyze_result",
                    "failure_next": "fix_program"
                }
            },
            {
                "id": "fix_program",
                "name": "修复程序",
                "agent_name": "coder",
                "instruction": "根据测试结果修复程序中的问题，确保能够正确输出问候语。",
                "instruction_type": "execution",
                "expected_output": "修复后的程序",
                "timeout": 60,
                "control_flow": {
                    "type": "loop",
                    "loop_condition": "retry_count < 2",
                    "loop_target": "test_greeting",
                    "max_iterations": 2,
                    "exit_on_max": "error_handling"
                }
            },
            {
                "id": "analyze_result",
                "name": "分析结果",
                "agent_name": "analyst",
                "instruction": "分析程序执行结果，生成简要的成功报告，包括程序功能和执行状态。",
                "instruction_type": "information",
                "expected_output": "成功分析报告",
                "control_flow": {
                    "type": "terminal"
                }
            },
            {
                "id": "error_handling",
                "name": "错误处理",
                "agent_name": "analyst",
                "instruction": "处理执行过程中的错误，生成错误报告和建议。",
                "instruction_type": "information",
                "expected_output": "错误报告",
                "control_flow": {
                    "type": "terminal"
                }
            }
        ],
        "control_rules": [
            {
                "trigger": "execution_time > 180",
                "action": "jump_to",
                "target": "error_handling",
                "priority": 1
            }
        ],
        "error_handling": {
            "default_strategy": "continue_with_logging",
            "escalation_rules": [
                {
                    "condition": "consecutive_failures > 3",
                    "action": "terminate_workflow"
                }
            ]
        }
    }
    
    # 转换为WorkflowDefinition对象
    from static_workflow.workflow_definitions import WorkflowLoader
    loader = WorkflowLoader()
    return loader.load_from_dict(demo_workflow_dict)


def display_execution_result(result):
    """显示工作流执行结果"""
    
    print(f"\n📊 执行结果总览:")
    print(f"   {'状态:':<12} {'✅ 成功' if result.success else '❌ 失败'}")
    print(f"   {'工作流:':<12} {result.workflow_name}")
    print(f"   {'总步骤:':<12} {result.total_steps}")
    print(f"   {'完成步骤:':<12} {result.completed_steps}")
    print(f"   {'失败步骤:':<12} {result.failed_steps}")
    print(f"   {'跳过步骤:':<12} {result.skipped_steps}")
    print(f"   {'执行时间:':<12} {result.execution_time:.2f}秒")
    
    if not result.success and result.error_message:
        print(f"   {'错误信息:':<12} {result.error_message}")
    
    print(f"\n📝 步骤详情:")
    for step_id, step_info in result.step_results.items():
        status_icon = {
            'completed': '✅',
            'failed': '❌', 
            'skipped': '⏭️',
            'pending': '⏸️',
            'running': '🔄'
        }.get(step_info['status'], '❓')
        
        print(f"   {status_icon} {step_info['name']} ({step_id})")
        
        if step_info['error_message']:
            print(f"      ❌ 错误: {step_info['error_message']}")
        
        if step_info['retry_count'] > 0:
            print(f"      🔄 重试次数: {step_info['retry_count']}")
        
        # 显示输出预览
        if step_info.get('result') and hasattr(step_info['result'], 'stdout'):
            stdout = step_info['result'].stdout
            if stdout and len(stdout.strip()) > 0:
                preview = stdout[:100] + "..." if len(stdout) > 100 else stdout
                print(f"      📄 输出预览: {preview.strip()}")


if __name__ == "__main__":
    main()