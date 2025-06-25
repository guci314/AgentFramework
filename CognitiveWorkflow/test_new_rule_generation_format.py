#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的规则生成格式和提示
"""

def test_simple_task_example():
    """展示简单任务的预期JSON输出格式"""
    
    print("=" * 60)
    print("简单任务示例：创建Hello World程序")
    print("=" * 60)
    
    # 模拟LLM的预期输出
    expected_output = """
{
  "rules": [
    {
      "rule_name": "实现Hello World程序",
      "trigger_condition": "需要创建一个Hello World程序",
      "action": "编写打印'Hello, World!'的代码",
      "agent_capability_id": "coder",
      "execution_phase": "problem_solving",
      "priority": 90,
      "expected_result": "可运行的Hello World程序"
    },
    {
      "rule_name": "验证程序输出",
      "trigger_condition": "Hello World程序已创建完成",
      "action": "运行程序并验证输出是否为'Hello, World!'",
      "agent_capability_id": "tester",
      "execution_phase": "verification",
      "priority": 80,
      "expected_result": "确认程序输出正确"
    }
  ]
}
"""
    
    print("预期LLM输出格式：")
    print(expected_output)
    
    print("\n✅ 特点：")
    print("- 跳过了收集阶段（简单任务）")
    print("- 只有2个规则（根据复杂度）")
    print("- 明确的JSON schema格式")
    print("- 三阶段中的执行和验证阶段")

def test_complex_task_example():
    """展示复杂任务的预期JSON输出格式"""
    
    print("\n" + "=" * 60)
    print("复杂任务示例：开发计算器应用")
    print("=" * 60)
    
    # 模拟LLM的预期输出
    expected_output = """
{
  "rules": [
    {
      "rule_name": "分析计算器需求",
      "trigger_condition": "需要开发一个计算器应用",
      "action": "分析计算器的功能需求，包括基本运算、界面设计等",
      "agent_capability_id": "analyst",
      "execution_phase": "information_gathering",
      "priority": 95,
      "expected_result": "详细的需求分析文档"
    },
    {
      "rule_name": "设计计算器架构",
      "trigger_condition": "需求分析已完成",
      "action": "设计计算器的模块架构和接口定义",
      "agent_capability_id": "analyst", 
      "execution_phase": "information_gathering",
      "priority": 90,
      "expected_result": "系统架构设计文档"
    },
    {
      "rule_name": "实现基本运算功能",
      "trigger_condition": "架构设计已完成",
      "action": "编写加减乘除四则运算的核心代码",
      "agent_capability_id": "coder",
      "execution_phase": "problem_solving",
      "priority": 85,
      "expected_result": "完成的运算模块代码"
    },
    {
      "rule_name": "实现用户界面",
      "trigger_condition": "基本运算功能已实现",
      "action": "创建计算器的用户界面，包括按钮和显示屏",
      "agent_capability_id": "coder",
      "execution_phase": "problem_solving", 
      "priority": 80,
      "expected_result": "完整的用户界面"
    },
    {
      "rule_name": "编写单元测试",
      "trigger_condition": "计算器功能已实现",
      "action": "为所有运算功能编写单元测试",
      "agent_capability_id": "tester",
      "execution_phase": "verification",
      "priority": 75,
      "expected_result": "完整的测试套件"
    },
    {
      "rule_name": "集成测试验证",
      "trigger_condition": "单元测试已编写",
      "action": "执行集成测试，验证整体功能正确性",
      "agent_capability_id": "tester",
      "execution_phase": "verification",
      "priority": 70,
      "expected_result": "所有测试通过的验证报告"
    }
  ]
}
"""
    
    print("预期LLM输出格式：")
    print(expected_output)
    
    print("\n✅ 特点：")
    print("- 包含完整三阶段（收集、执行、验证）")
    print("- 6个规则（适应复杂任务）")
    print("- 优先级递减（收集>执行>验证）")
    print("- 逻辑依赖的触发条件")

def test_schema_validation():
    """展示JSON schema的验证要点"""
    
    print("\n" + "=" * 60)
    print("JSON Schema 关键验证点")
    print("=" * 60)
    
    schema_points = [
        "✅ rule_name: 必须是有意义的字符串",
        "✅ trigger_condition: 自然语言条件，便于语义匹配",
        "✅ action: 具体的执行指令",
        "✅ agent_capability_id: 必须从可用能力列表中选择",
        "✅ execution_phase: 只能是 information_gathering|problem_solving|verification",
        "✅ priority: 1-100的数字，数字越大优先级越高",
        "✅ expected_result: 明确的期望结果描述"
    ]
    
    for point in schema_points:
        print(point)

def test_backward_compatibility():
    """展示向后兼容性支持"""
    
    print("\n" + "=" * 60)
    print("向后兼容性字段映射")
    print("=" * 60)
    
    mapping = {
        "新字段名": "旧字段名(兼容)",
        "rule_name": "name",
        "trigger_condition": "condition", 
        "execution_phase": "phase",
        "expected_result": "expected_outcome"
    }
    
    print("字段映射关系：")
    for new_field, old_field in mapping.items():
        print(f"  {new_field} <- {old_field}")
    
    print("\n✅ 系统同时支持新旧字段名，确保平滑升级")

if __name__ == "__main__":
    print("规则生成新格式测试和示例")
    
    test_simple_task_example()
    test_complex_task_example()
    test_schema_validation()
    test_backward_compatibility()
    
    print("\n" + "=" * 60)
    print("🎉 改进总结")
    print("=" * 60)
    print("1. 不再固定规则数量，根据任务复杂度灵活生成")
    print("2. 提供明确的JSON schema，减少格式错误")
    print("3. 采用三阶段模式（收集、执行、验证）")
    print("4. 简单任务可跳过收集阶段，提高效率")
    print("5. 支持新旧字段名，保证向后兼容")
    print("=" * 60)