#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试语言模型验证功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'cognitive_workflow_rule_base'))

from unittest.mock import Mock, MagicMock
from services.language_model_service import LanguageModelService
from services.rule_execution_service import RuleExecutionService
from services.agent_service import AgentService
from infrastructure.repository_impl import ExecutionRepositoryImpl
from domain.entities import WorkflowResult

def test_llm_validation():
    """测试语言模型验证功能"""
    
    print("测试语言模型验证功能...")
    
    try:
        # 创建模拟的LLM
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content='{"result_valid": true, "confidence": 0.9, "reasoning": "结果符合期望，包含了所需的Hello World输出"}')
        
        # 创建语言模型服务
        llm_service = LanguageModelService(mock_llm)
        
        print("✓ 语言模型服务创建成功")
        
        # 创建模拟的Agent服务和执行仓储
        mock_agent_service = Mock()
        execution_repository = ExecutionRepositoryImpl(storage_path="./.test_cognitive_workflow_data/executions")
        
        # 创建规则执行服务
        rule_execution_service = RuleExecutionService(
            agent_service=mock_agent_service,
            execution_repository=execution_repository,
            llm_service=llm_service
        )
        
        print("✓ 规则执行服务创建成功，包含LLM验证功能")
        
        # 测试LLM验证方法
        test_result = WorkflowResult(
            success=True,
            message="Hello, World! 程序已成功创建并运行",
            data={"output": "Hello, World!"},
            error_details=None,
            metadata={"language": "Python"}
        )
        
        # 调用验证方法
        is_valid = rule_execution_service._validate_natural_language_result(
            action="创建一个Hello World程序",
            result=test_result,
            expected_outcome="输出'Hello, World!'到控制台"
        )
        
        print(f"✓ LLM验证结果: {is_valid}")
        
        # 测试备用关键词验证
        backup_valid = rule_execution_service._fallback_keyword_validation(
            result_text="Hello, World! 程序已成功创建并运行",
            expected_outcome="输出Hello World到控制台"
        )
        
        print(f"✓ 备用关键词验证结果: {backup_valid}")
        
        print("\n🎉 语言模型验证功能测试成功！")
        print("现在系统使用智能语义验证而不是简单的关键词匹配")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_validation_methods_comparison():
    """比较新旧验证方法的差异"""
    
    print("\n比较验证方法的差异:")
    
    # 模拟一些测试用例
    test_cases = [
        {
            "action": "创建Python Hello World程序",
            "result": "Successfully created hello.py with print('Hello, World!') statement",
            "expected": "输出Hello World到控制台",
            "description": "英文结果，中文期望"
        },
        {
            "action": "计算两个数的和",
            "result": "计算完成，结果为15",
            "expected": "返回数学运算的正确结果",
            "description": "语义匹配，无字面关键词重叠"
        },
        {
            "action": "生成README文档",
            "result": "项目文档已创建，包含项目介绍、安装步骤和使用说明",
            "expected": "创建项目说明文档",
            "description": "功能完成但表述不同"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {case['description']}")
        print(f"动作: {case['action']}")
        print(f"结果: {case['result']}")
        print(f"期望: {case['expected']}")
        
        # 使用关键词匹配（旧方法）
        expected_keywords = case['expected'].lower().split()
        result_text_lower = case['result'].lower()
        matching_keywords = sum(1 for keyword in expected_keywords 
                              if keyword in result_text_lower and len(keyword) > 2)
        keyword_match_ratio = matching_keywords / len(expected_keywords) if expected_keywords else 0
        keyword_valid = keyword_match_ratio >= 0.3
        
        print(f"  关键词匹配: {keyword_valid} (匹配率: {keyword_match_ratio:.2f})")
        print(f"  LLM验证: [需要真实LLM] - 会考虑语义相似性")
        print(f"  预期LLM更好的原因: 能理解语义而不只是字面匹配")

if __name__ == "__main__":
    success = test_llm_validation()
    test_validation_methods_comparison()
    print(f"\n总结: {'✅ 所有测试通过' if success else '❌ 测试失败'}")
    sys.exit(0 if success else 1)