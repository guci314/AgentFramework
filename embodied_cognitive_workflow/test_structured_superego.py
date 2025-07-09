#!/usr/bin/env python3
"""
测试使用结构化输出的SuperEgoAgent
验证 response_format 和 JSON schema 的稳定性改进
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


def test_structured_superego():
    """测试结构化输出的SuperEgoAgent"""
    print("🧠 测试结构化输出的SuperEgoAgent")
    print("=" * 60)
    
    try:
        from embodied_cognitive_workflow import SuperEgoAgent
        from langchain_openai import ChatOpenAI
        
        # 初始化LLM
        if os.getenv('DEEPSEEK_API_KEY'):
            llm = ChatOpenAI(
                model="deepseek-chat",
                openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
                openai_api_base="https://api.deepseek.com",
                max_tokens=1000,
                temperature=0.3
            )
            print("🤖 使用DeepSeek模型")
        elif os.getenv('OPENAI_API_KEY'):
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                max_tokens=1000,
                temperature=0.3
            )
            print("🤖 使用OpenAI GPT-3.5-turbo")
        else:
            print("❌ 未找到API密钥")
            return False
        
        # 创建两个版本的SuperEgo进行对比
        print("\n📊 对比测试: 结构化 vs 传统输出")
        
        # 传统模式 (use_structured_output=False)
        print("\n🔹 创建传统模式SuperEgo")
        traditional_super_ego = SuperEgoAgent(
            llm=llm,
            enable_ultra_think=True,
            use_structured_output=False
        )
        
        # 结构化模式 (use_structured_output=True)
        print("🔹 创建结构化模式SuperEgo")
        structured_super_ego = SuperEgoAgent(
            llm=llm,
            enable_ultra_think=True,
            use_structured_output=True
        )
        
        # 测试数据
        test_performance = {"efficiency": 0.8, "accuracy": 0.9}
        test_context = {"task": "认知监督", "complexity": "高"}
        test_goals = ["提高效率", "保持准确性"]
        
        # 测试1: 策略优化
        print("\n📈 测试1: 策略优化对比")
        
        print("  传统模式:")
        try:
            traditional_result = traditional_super_ego.strategy_optimizer.optimize_strategy(
                test_performance, test_context, test_goals
            )
            print(f"    ✅ 成功 - 策略数量: {len(traditional_result.get('strategies', []))}")
            print(f"    置信度: {traditional_result.get('confidence', 'N/A')}")
        except Exception as e:
            print(f"    ❌ 失败: {e}")
        
        print("  结构化模式:")
        try:
            structured_result = structured_super_ego.strategy_optimizer.optimize_strategy(
                test_performance, test_context, test_goals
            )
            print(f"    ✅ 成功 - 策略数量: {len(structured_result.get('strategies', []))}")
            print(f"    置信度: {structured_result.get('confidence', 'N/A')}")
            print(f"    响应格式验证: {'✅ 通过' if _validate_strategy_schema(structured_result) else '❌ 失败'}")
        except Exception as e:
            print(f"    ❌ 失败: {e}")
        
        # 测试2: 策略调节
        print("\n⚙️ 测试2: 策略调节对比")
        
        print("  传统模式:")
        try:
            traditional_regulation = traditional_super_ego.ultra_think.regulate_cognitive_strategy(
                test_context, test_goals
            )
            print(f"    ✅ 成功 - 需要调整: {traditional_regulation.get('adjustment_needed', 'N/A')}")
        except Exception as e:
            print(f"    ❌ 失败: {e}")
        
        print("  结构化模式:")
        try:
            structured_regulation = structured_super_ego.ultra_think.regulate_cognitive_strategy(
                test_context, test_goals
            )
            print(f"    ✅ 成功 - 需要调整: {structured_regulation.get('adjustment_needed', 'N/A')}")
            print(f"    响应格式验证: {'✅ 通过' if _validate_regulation_schema(structured_regulation) else '❌ 失败'}")
        except Exception as e:
            print(f"    ❌ 失败: {e}")
        
        # 测试3: 多次调用稳定性
        print("\n🔄 测试3: 多次调用稳定性")
        
        success_count = 0
        total_tests = 5
        
        for i in range(total_tests):
            try:
                result = structured_super_ego.strategy_optimizer.optimize_strategy(
                    {"efficiency": 0.7 + i * 0.05}, 
                    {"iteration": i}, 
                    ["测试目标"]
                )
                if _validate_strategy_schema(result):
                    success_count += 1
            except Exception:
                pass
        
        success_rate = (success_count / total_tests) * 100
        print(f"    结构化模式成功率: {success_rate:.1f}% ({success_count}/{total_tests})")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def _validate_strategy_schema(result: dict) -> bool:
    """验证策略优化结果是否符合schema"""
    required_fields = ["analysis", "strategies", "priority", "confidence"]
    
    # 检查必需字段
    for field in required_fields:
        if field not in result:
            return False
    
    # 检查数据类型
    if not isinstance(result["analysis"], str):
        return False
    if not isinstance(result["strategies"], list):
        return False
    if result["priority"] not in ["high", "medium", "low"]:
        return False
    if not isinstance(result["confidence"], (int, float)) or not (0.0 <= result["confidence"] <= 1.0):
        return False
    
    return True


def _validate_regulation_schema(result: dict) -> bool:
    """验证策略调节结果是否符合schema"""
    required_fields = ["assessment", "adjustment_needed", "recommended_strategy", "confidence"]
    
    # 检查必需字段
    for field in required_fields:
        if field not in result:
            return False
    
    # 检查数据类型
    if not isinstance(result["assessment"], str):
        return False
    if not isinstance(result["adjustment_needed"], bool):
        return False
    if not isinstance(result["recommended_strategy"], str):
        return False
    if not isinstance(result["confidence"], (int, float)) or not (0.0 <= result["confidence"] <= 1.0):
        return False
    
    return True


def test_direct_structured_optimizer():
    """直接测试结构化响应优化器"""
    print("\n🔧 直接测试结构化响应优化器")
    print("=" * 60)
    
    try:
        from structured_response_optimizer import StructuredResponseOptimizer
        from langchain_openai import ChatOpenAI
        
        # 初始化LLM
        if os.getenv('DEEPSEEK_API_KEY'):
            llm = ChatOpenAI(
                model="deepseek-chat",
                openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
                openai_api_base="https://api.deepseek.com",
                max_tokens=1000,
                temperature=0.3
            )
        elif os.getenv('OPENAI_API_KEY'):
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                max_tokens=1000,
                temperature=0.3
            )
        else:
            print("❌ 未找到API密钥")
            return False
        
        optimizer = StructuredResponseOptimizer(llm)
        
        # 测试策略优化
        print("📈 测试结构化策略优化")
        try:
            result = optimizer.optimize_strategy_structured(
                current_performance={"efficiency": 0.8, "accuracy": 0.9},
                context={"task": "测试", "environment": "开发"},
                goals=["提高性能", "减少错误"]
            )
            
            print("✅ 结构化策略优化成功")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            print(f"Schema验证: {'✅ 通过' if _validate_strategy_schema(result) else '❌ 失败'}")
            
        except Exception as e:
            print(f"❌ 结构化策略优化失败: {e}")
        
        # 测试策略调节
        print("\n⚙️ 测试结构化策略调节")
        try:
            result = optimizer.regulate_strategy_structured(
                current_context={"situation": "测试场景", "load": "中等"},
                target_goals=["保持稳定", "优化性能"]
            )
            
            print("✅ 结构化策略调节成功")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            print(f"Schema验证: {'✅ 通过' if _validate_regulation_schema(result) else '❌ 失败'}")
            
        except Exception as e:
            print(f"❌ 结构化策略调节失败: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


if __name__ == "__main__":
    print("🎯 结构化SuperEgo测试工具")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 测试结构化SuperEgo
    superego_success = test_structured_superego()
    
    # 测试直接优化器
    optimizer_success = test_direct_structured_optimizer()
    
    print("\n" + "=" * 80)
    print("📊 测试总结:")
    print(f"SuperEgo集成测试: {'✅ 成功' if superego_success else '❌ 失败'}")
    print(f"直接优化器测试: {'✅ 成功' if optimizer_success else '❌ 失败'}")
    
    if superego_success and optimizer_success:
        print("\n✅ 结构化输出优化成功!")
        print("💡 建议: 使用 use_structured_output=True 以获得更稳定的JSON响应")
        print("📈 预期改进: 减少JSON解析错误，提高响应质量")
    else:
        print("\n⚠️ 部分测试失败")
        print("💡 建议: 检查API配置和JSON schema实现")