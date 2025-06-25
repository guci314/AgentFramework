# -*- coding: utf-8 -*-
"""
测试Result类型转换修复

验证agent_base.Result和cognitive_workflow.Result之间的正确转换
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

from pythonTask import Agent, llm_deepseek
from cognitive_workflow_rule_base.services.agent_service import AgentService
from cognitive_workflow_rule_base.domain.entities import AgentRegistry, AgentCapability, WorkflowResult as CognitiveResult

# 导入agent_base.Result (需要模拟因为有命名冲突)
from agent_base import Result as AgentBaseResult


def test_agent_base_result_conversion():
    """测试agent_base.Result到cognitive_workflow.Result的转换"""
    
    print("🧪 测试Result类型转换修复")
    print("="*40)
    
    # 1. 创建测试环境
    print("1. 创建测试环境...")
    
    # 创建agent registry
    agent_registry = AgentRegistry()
    test_capability = AgentCapability(
        id="test_agent",
        name="测试智能体",
        description="用于测试Result类型转换的智能体",
        supported_actions=["*"],
        api_specification="测试智能体规格"
    )
    agent_registry.register_capability(test_capability)
    
    # 创建agent实例
    test_agent = Agent(llm=llm_deepseek)
    test_agent.api_specification = "测试智能体"
    
    agents = {"test_agent": test_agent}
    
    # 创建agent服务
    agent_service = AgentService(agent_registry, agents)
    
    print("   ✅ 测试环境创建完成")
    
    # 2. 模拟不同类型的Result进行转换测试
    print("\n2. 测试不同Result类型的转换...")
    
    test_cases = [
        {
            "name": "agent_base.Result (成功)",
            "input": AgentBaseResult(
                success=True,
                code="print('Hello World')",
                stdout="Hello World\n",
                stderr="",
                return_value="Hello World"
            ),
            "expected_success": True
        },
        {
            "name": "agent_base.Result (失败)",
            "input": AgentBaseResult(
                success=False,
                code="print(undefined_variable)",
                stdout="",
                stderr="NameError: name 'undefined_variable' is not defined",
                return_value=None
            ),
            "expected_success": False
        },
        {
            "name": "字符串",
            "input": "简单的字符串结果",
            "expected_success": True
        },
        {
            "name": "字典",
            "input": {
                "success": True,
                "message": "字典格式的结果",
                "data": {"key": "value"}
            },
            "expected_success": True
        },
        {
            "name": "cognitive_workflow.Result",
            "input": CognitiveResult(
                success=True,
                message="已经是正确格式的Result",
                data={"test": "data"}
            ),
            "expected_success": True
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n   测试: {test_case['name']}")
        
        try:
            # 调用转换方法
            converted_result = agent_service._convert_to_result(
                test_case["input"], 
                "测试指令"
            )
            
            # 验证结果类型
            if not isinstance(converted_result, CognitiveResult):
                print(f"      ❌ 返回类型错误: {type(converted_result)}")
                results.append(False)
                continue
            
            # 验证success字段
            if converted_result.success != test_case["expected_success"]:
                print(f"      ❌ success字段不匹配: 期望{test_case['expected_success']}, 实际{converted_result.success}")
                results.append(False)
                continue
            
            # 验证必要字段存在
            if not hasattr(converted_result, 'message'):
                print(f"      ❌ 缺少message字段")
                results.append(False)
                continue
            
            if not hasattr(converted_result, 'metadata'):
                print(f"      ❌ 缺少metadata字段")
                results.append(False)
                continue
            
            # 特殊验证agent_base.Result的转换
            if isinstance(test_case["input"], AgentBaseResult):
                if not isinstance(converted_result.data, dict):
                    print(f"      ❌ agent_base.Result转换后data应为dict类型")
                    results.append(False)
                    continue
                
                # 验证字段映射
                expected_fields = ['code', 'return_value', 'stdout', 'stderr']
                for field in expected_fields:
                    if field not in converted_result.data:
                        print(f"      ❌ 转换后缺少{field}字段")
                        results.append(False)
                        break
                else:
                    # 验证数据正确性
                    if converted_result.data['code'] != test_case["input"].code:
                        print(f"      ❌ code字段转换错误")
                        results.append(False)
                        continue
                    
                    if converted_result.data['return_value'] != test_case["input"].return_value:
                        print(f"      ❌ return_value字段转换错误")
                        results.append(False)
                        continue
                
                # 验证metadata
                if converted_result.metadata.get('source_type') != 'agent_base_result':
                    print(f"      ❌ source_type标记错误")
                    results.append(False)
                    continue
            
            print(f"      ✅ 转换成功")
            print(f"         Success: {converted_result.success}")
            print(f"         Message: {converted_result.message[:50]}...")
            print(f"         Source Type: {converted_result.metadata.get('source_type', 'unknown')}")
            
            results.append(True)
            
        except Exception as e:
            print(f"      ❌ 转换异常: {e}")
            results.append(False)
    
    # 3. 总结测试结果
    print(f"\n3. 测试结果总结:")
    print(f"   总测试案例: {len(test_cases)}")
    print(f"   成功案例: {sum(results)}")
    print(f"   失败案例: {len(results) - sum(results)}")
    print(f"   成功率: {sum(results)/len(results)*100:.1f}%")
    
    if all(results):
        print("\n🎉 所有Result类型转换测试通过！")
        return True
    else:
        print("\n⚠️  部分测试失败，需要进一步检查")
        return False


def test_real_agent_execution():
    """测试真实的智能体执行和结果转换"""
    
    print("\n🔍 测试真实智能体执行的Result转换")
    print("="*45)
    
    try:
        # 创建测试环境
        agent_registry = AgentRegistry()
        test_capability = AgentCapability(
            id="real_test_agent",
            name="真实测试智能体",
            description="执行真实任务的测试智能体",
            supported_actions=["*"],
            api_specification="真实测试智能体"
        )
        agent_registry.register_capability(test_capability)
        
        real_agent = Agent(llm=llm_deepseek)
        real_agent.api_specification = "真实测试智能体"
        
        agents = {"real_test_agent": real_agent}
        agent_service = AgentService(agent_registry, agents)
        
        # 执行简单指令
        print("执行指令: 计算 2 + 3 的结果")
        
        result = agent_service.execute_natural_language_instruction(
            "real_test_agent",
            "计算 2 + 3 的结果，并输出答案"
        )
        
        # 验证结果
        if isinstance(result, CognitiveResult):
            print("✅ 返回类型正确: cognitive_workflow.Result")
            print(f"   Success: {result.success}")
            print(f"   Message: {result.message}")
            print(f"   Has Data: {result.data is not None}")
            print(f"   Source Type: {result.metadata.get('source_type', 'unknown')}")
            
            if result.success:
                print("✅ 执行成功")
                return True
            else:
                print(f"⚠️  执行失败: {result.error_details}")
                return False
        else:
            print(f"❌ 返回类型错误: {type(result)}")
            return False
    
    except Exception as e:
        print(f"❌ 真实执行测试失败: {e}")
        return False


def main():
    """主函数"""
    
    print("🚀 Result类型转换修复验证")
    print("解决agent_base.Result和cognitive_workflow.Result的类型冲突")
    print("="*70)
    
    try:
        # 测试1: 类型转换逻辑
        conversion_passed = test_agent_base_result_conversion()
        
        # 测试2: 真实执行 (可选，可能比较慢)
        # real_execution_passed = test_real_agent_execution()
        
        # 总结
        print("\n📊 修复验证总结:")
        print("="*25)
        print(f"✅ 类型转换测试: {'通过' if conversion_passed else '失败'}")
        # print(f"✅ 真实执行测试: {'通过' if real_execution_passed else '失败'}")
        
        if conversion_passed:  # and real_execution_passed
            print("\n🎉 Result类型转换修复验证成功！")
            print("\n🔧 修复要点:")
            print("   ✓ 使用属性检查识别agent_base.Result")
            print("   ✓ 完整的字段映射(code, stdout, stderr, return_value)")
            print("   ✓ 保留原有信息在data字段中")
            print("   ✓ 正确设置错误详情")
            print("   ✓ 添加source_type元数据标记")
            print("   ✓ 兼容多种输入类型")
        else:
            print("\n⚠️  修复仍需完善")
    
    except Exception as e:
        print(f"\n❌ 验证异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()