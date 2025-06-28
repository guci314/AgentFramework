#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 RulePhase 与三阶段执行模式的对齐
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'cognitive_workflow_rule_base'))

def test_rule_phase_alignment():
    """测试 RulePhase 枚举与三阶段模式的对齐"""
    
    print("=" * 60)
    print("测试 RulePhase 与三阶段执行模式对齐")
    print("=" * 60)
    
    try:
        from domain.value_objects import RulePhase
        
        # 检查三阶段是否都存在
        expected_phases = [
            ("INFORMATION_GATHERING", "information_gathering"),
            ("EXECUTION", "execution"), 
            ("VERIFICATION", "verification")
        ]
        
        print("✅ 检查三阶段枚举值:")
        for phase_name, phase_value in expected_phases:
            phase = getattr(RulePhase, phase_name)
            assert phase.value == phase_value
            print(f"  {phase_name} = '{phase_value}' ✓")
        
        # 检查是否移除了 CLEANUP 阶段
        print("\n✅ 检查 CLEANUP 阶段是否已移除:")
        if hasattr(RulePhase, 'CLEANUP'):
            print("  ❌ CLEANUP 阶段仍然存在")
            return False
        else:
            print("  ✓ CLEANUP 阶段已成功移除")
        
        # 检查枚举总数
        print(f"\n✅ 检查阶段总数:")
        phase_count = len(list(RulePhase))
        if phase_count == 3:
            print(f"  ✓ 阶段总数正确: {phase_count} 个")
        else:
            print(f"  ❌ 阶段总数错误: {phase_count} 个，应该是 3 个")
            return False
        
        # 测试所有阶段的字符串值
        print(f"\n✅ 所有阶段的字符串值:")
        for phase in RulePhase:
            print(f"  {phase.name} = '{phase.value}'")
        
        print(f"\n🎉 所有测试通过！RulePhase 与三阶段执行模式完全对齐")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_json_schema_compatibility():
    """测试 JSON schema 兼容性"""
    
    print("\n" + "=" * 60)
    print("测试 JSON Schema 兼容性")
    print("=" * 60)
    
    # 模拟从 JSON 解析的规则数据
    test_rules = [
        {
            "rule_name": "收集需求信息",
            "execution_phase": "information_gathering",
            "expected": True
        },
        {
            "rule_name": "实现核心功能", 
            "execution_phase": "execution",
            "expected": True
        },
        {
            "rule_name": "验证功能正确性",
            "execution_phase": "verification", 
            "expected": True
        },
        {
            "rule_name": "旧格式实现功能",
            "execution_phase": "problem_solving",  # 旧的阶段值，应该成功（兼容性）
            "expected": True
        },
        {
            "rule_name": "清理临时文件",
            "execution_phase": "cleanup",  # 不存在的阶段，应该失败
            "expected": False
        }
    ]
    
    try:
        from domain.value_objects import RulePhase
        
        for rule_data in test_rules:
            rule_name = rule_data["rule_name"]
            phase_str = rule_data["execution_phase"]
            expected = rule_data["expected"]
            
            # 模拟 _create_rule_from_data 中的转换逻辑
            if phase_str == 'problem_solving':
                phase_str = 'execution'
                
            try:
                phase = RulePhase(phase_str)
                if expected:
                    print(f"  ✓ {rule_name}: '{rule_data['execution_phase']}' -> {phase.name}")
                else:
                    print(f"  ❌ {rule_name}: '{rule_data['execution_phase']}' 应该失败但成功了")
                    return False
            except ValueError:
                if not expected:
                    print(f"  ✓ {rule_name}: '{rule_data['execution_phase']}' 正确失败（阶段不存在）")
                else:
                    print(f"  ❌ {rule_name}: '{rule_data['execution_phase']}' 应该成功但失败了")
                    return False
        
        print(f"\n🎉 JSON Schema 兼容性测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 兼容性测试失败: {e}")
        return False

if __name__ == "__main__":
    print("RulePhase 对齐测试")
    
    success1 = test_rule_phase_alignment()
    success2 = test_json_schema_compatibility()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 所有测试通过！")
        print("✅ RulePhase 与三阶段执行模式完全对齐")
        print("✅ JSON Schema 兼容性正常")
        print("✅ 系统概念模型一致")
        exit_code = 0
    else:
        print("❌ 部分测试失败")
        exit_code = 1
    
    print("=" * 60)
    sys.exit(exit_code)