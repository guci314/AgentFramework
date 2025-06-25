#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试规则生成失败时的错误处理
验证删除 _create_basic_rules 方法后，系统是否能正确抛出异常而不是使用回退规则
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'cognitive_workflow_rule_base'))

from unittest.mock import Mock
from services.rule_generation_service import RuleGenerationService
from services.language_model_service import LanguageModelService
from domain.entities import AgentRegistry, AgentCapability

def test_rule_generation_failure():
    """测试规则生成失败时是否正确抛出异常"""
    
    print("测试规则生成失败处理...")
    
    # 创建一个会失败的模拟LLM
    mock_llm = Mock()
    mock_llm.invoke.return_value = Mock(content="无效的JSON响应")  # 故意返回无效响应
    
    # 创建语言模型服务
    llm_service = LanguageModelService(mock_llm)
    
    # 创建规则生成服务
    rule_generation_service = RuleGenerationService(llm_service)
    
    # 创建一个简单的智能体注册表
    agent_registry = AgentRegistry()
    capability = AgentCapability(
        id="test_agent",
        name="Test Agent",
        description="Test agent for validation",
        supported_actions=["*"]
    )
    agent_registry.register_capability(capability)
    
    print("✓ 服务和模拟环境创建完成")
    
    # 测试1: 验证 generate_rule_set 方法会抛出异常
    print("\n测试1: 验证 generate_rule_set 在LLM失败时抛出异常")
    try:
        rule_set = rule_generation_service.generate_rule_set("创建一个简单的Hello World程序", agent_registry)
        print("❌ 测试失败：应该抛出异常但却成功返回了规则集")
        return False
    except Exception as e:
        print(f"✅ 测试成功：正确抛出异常 - {type(e).__name__}: {str(e)}")
    
    # 测试2: 验证 _generate_initial_rules 方法会抛出异常
    print("\n测试2: 验证 _generate_initial_rules 在LLM失败时抛出异常")
    try:
        rules = rule_generation_service._generate_initial_rules("测试目标", "测试能力描述")
        print("❌ 测试失败：应该抛出异常但却成功返回了规则")
        return False
    except Exception as e:
        print(f"✅ 测试成功：正确抛出异常 - {type(e).__name__}: {str(e)}")
    
    # 测试3: 验证 _create_fallback_rule_set 方法会抛出异常
    print("\n测试3: 验证 _create_fallback_rule_set 方法抛出异常")
    try:
        rule_set = rule_generation_service._create_fallback_rule_set("测试目标", agent_registry)
        print("❌ 测试失败：应该抛出异常但却成功返回了规则集")
        return False
    except Exception as e:
        print(f"✅ 测试成功：正确抛出异常 - {type(e).__name__}: {str(e)}")
    
    print("\n🎉 所有测试通过！规则生成失败时能正确抛出异常，不再使用回退规则。")
    return True

def test_method_not_exists():
    """测试 _create_basic_rules 方法是否已被删除"""
    
    print("\n测试 _create_basic_rules 方法是否已被删除...")
    
    # 创建服务实例
    mock_llm = Mock()
    llm_service = LanguageModelService(mock_llm)
    rule_generation_service = RuleGenerationService(llm_service)
    
    # 检查方法是否存在
    if hasattr(rule_generation_service, '_create_basic_rules'):
        print("❌ 测试失败：_create_basic_rules 方法仍然存在")
        return False
    else:
        print("✅ 测试成功：_create_basic_rules 方法已被成功删除")
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("规则生成失败处理测试")
    print("=" * 60)
    
    success1 = test_rule_generation_failure()
    success2 = test_method_not_exists()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 所有测试通过！")
        print("✅ 系统现在在规则生成失败时会直接报错")
        print("✅ 不再使用不可靠的回退规则")
        print("✅ 错误信息更清晰，便于调试")
        exit_code = 0
    else:
        print("❌ 部分测试失败")
        exit_code = 1
    
    print("=" * 60)
    sys.exit(exit_code)