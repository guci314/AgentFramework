# -*- coding: utf-8 -*-
"""
快速测试system能力错误

直接测试规则生成服务以快速重现错误
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent))

from pythonTask import llm_deepseek

def test_direct_rule_generation():
    """直接测试规则生成服务以触发错误"""
    
    print("🧪 直接测试规则生成服务")
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
    
    print("🚀 System 能力错误重现测试 (快速版)")
    print("目标：重现'未找到智能体能力: system'错误")
    print("="*60)
    
    try:
        # 直接测试规则生成
        success = test_direct_rule_generation()
        
        # 总结
        print("\n\n📊 测试结果总结:")
        print(f"   直接规则生成: {'✅ 成功重现' if success else '❌ 未重现'}")
        
        if success:
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