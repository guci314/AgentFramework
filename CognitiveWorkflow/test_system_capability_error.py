# -*- coding: utf-8 -*-
"""
测试system能力错误的重现

这个测试专门用来重现"未找到智能体能力: system"错误
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent))

from pythonTask import Agent, llm_deepseek
from cognitive_workflow_rule_base import create_production_rule_system

def test_system_capability_error():
    """测试重现system能力错误"""
    
    print("🧪 测试重现'未找到智能体能力: system'错误")
    print("="*50)
    
    # 1. 创建一个智能体（不包含system能力）
    print("1. 创建测试智能体...")
    test_agent = Agent(llm=llm_deepseek)
    test_agent.api_specification = "测试智能体，用于重现错误"
    
    agents = {"test_agent": test_agent}
    print(f"   创建了 {len(agents)} 个智能体")
    
    # 2. 创建工作流系统
    print("\n2. 创建工作流系统...")
    workflow_engine = create_production_rule_system(
        llm=llm_deepseek,
        agents=agents,
        enable_auto_recovery=True  # 启用自动恢复，这会触发错误恢复规则
    )
    print("   ✅ 工作流系统创建成功")
    
    # 3. 执行一个可能失败的目标，来触发错误恢复机制
    print("\n3. 执行可能触发错误的目标...")
    
    # 创建一个故意会失败的目标，以触发错误恢复规则生成
    error_prone_goal = """
    执行一个复杂且可能失败的任务：
    1. 连接到一个不存在的数据库 postgresql://fake:fake@nonexistent:5432/fake
    2. 读取一个不存在的文件 /nonexistent/file.txt  
    3. 调用一个不存在的API接口
    4. 当出现错误时自动恢复
    """
    
    try:
        result = workflow_engine.execute_goal(error_prone_goal)
        print(f"   执行结果: {'成功' if result.is_successful else '失败'}")
        print(f"   最终消息: {result.final_message}")
        
    except ValueError as e:
        if "未找到智能体能力: system" in str(e):
            print(f"   ✅ 成功重现错误: {e}")
            return True
        else:
            print(f"   ❌ 不同的ValueError: {e}")
            return False
    except Exception as e:
        print(f"   ❌ 其他异常: {e}")
        return False
        
    print("   ❌ 未能重现预期的错误")
    return False

def test_direct_rule_generation():
    """直接测试规则生成服务以触发错误"""
    
    print("\n\n🧪 直接测试规则生成服务")
    print("="*40)
    
    from cognitive_workflow_rule_base.services.rule_generation_service import RuleGenerationService
    from cognitive_workflow_rule_base.services.language_model_service import LanguageModelService
    from cognitive_workflow_rule_base import AgentRegistry, AgentCapability
    
    # 创建服务
    llm_service = LanguageModelService(llm_deepseek)
    rule_gen_service = RuleGenerationService(llm_service)
    
    # 创建包含test_agent的注册表（不包含system）
    agent_registry = AgentRegistry()
    test_capability = AgentCapability(
        id="test_agent",
        name="测试智能体",
        description="用于测试的智能体",
        supported_actions=["*"],
        api_specification="测试智能体规格"
    )
    agent_registry.register_capability(test_capability)
    
    print("1. 创建测试用的Agent Registry...")
    capabilities = agent_registry.list_all_capabilities()
    print(f"   包含的智能体能力: {[cap.id for cap in capabilities]}")
    
    # 创建故意失败的上下文
    print("\n2. 模拟失败上下文...")
    failure_context = {
        'error_message': 'Network connection failed',
        'failed_rule': {'action': 'connect to database'},
        'execution_context': {'attempt_count': 1}
    }
    
    print("\n3. 尝试生成错误恢复规则...")
    try:
        recovery_rules = rule_gen_service.generate_recovery_rules(failure_context)
        print(f"   生成了 {len(recovery_rules)} 个恢复规则")
        
        # 检查是否有使用system能力的规则
        system_rules = [rule for rule in recovery_rules if rule.agent_capability_id == 'system']
        if system_rules:
            print(f"   ⚠️  发现 {len(system_rules)} 个使用'system'能力的规则")
            for rule in system_rules:
                print(f"      - {rule.name}: {rule.agent_capability_id}")
                
                # 尝试获取这个能力（这应该会失败）
                try:
                    capability = agent_registry.get_capability('system')
                    print(f"      ✅ 找到system能力: {capability.name}")
                except ValueError as e:
                    print(f"      ❌ 错误: {e}")
                    return True
        else:
            print("   ✅ 没有使用'system'能力的规则")
            
    except Exception as e:
        print(f"   ❌ 规则生成失败: {e}")
        return False
        
    return False

def main():
    """主函数"""
    
    print("🚀 System 能力错误重现测试")
    print("目标：重现'未找到智能体能力: system'错误")
    print("="*60)
    
    try:
        # 测试1: 通过工作流触发
        test1_success = test_system_capability_error()
        
        # 测试2: 直接测试规则生成
        test2_success = test_direct_rule_generation()
        
        # 总结
        print("\n\n📊 测试结果总结:")
        print(f"   工作流触发错误: {'✅ 成功重现' if test1_success else '❌ 未重现'}")
        print(f"   直接规则生成: {'✅ 成功重现' if test2_success else '❌ 未重现'}")
        
        if test1_success or test2_success:
            print("\n🎯 错误重现成功！")
            print("\n🔍 问题分析:")
            print("   - rule_generation_service.py 中硬编码了'system'能力ID")
            print("   - 错误恢复规则使用了未注册的'system'智能体能力")
            print("   - create_production_rule_system 只注册传入的agents，没有默认system能力")
            
        else:
            print("\n❌ 未能重现预期的错误")
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试执行异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()