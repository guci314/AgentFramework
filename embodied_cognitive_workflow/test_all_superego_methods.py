#!/usr/bin/env python3
"""
全面测试SuperEgoAgent的所有方法
验证所有JSON输出方法都已更新为结构化输出
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


def test_all_superego_methods():
    """测试SuperEgoAgent的所有主要方法"""
    print("🧠 全面测试SuperEgoAgent方法")
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
        
        # 创建结构化模式SuperEgo
        print("\n🔹 创建结构化模式SuperEgo")
        super_ego = SuperEgoAgent(
            llm=llm,
            enable_ultra_think=True,
            use_structured_output=True
        )
        
        success_count = 0
        total_tests = 0
        
        # 测试1: 策略优化
        print("\n📈 测试策略优化")
        total_tests += 1
        try:
            result = super_ego.strategy_optimizer.optimize_strategy(
                {"efficiency": 0.8, "accuracy": 0.9},
                {"task": "测试", "environment": "开发"},
                ["提高性能", "减少错误"]
            )
            
            if 'error' not in result and _validate_strategy_schema(result):
                print("✅ 策略优化成功")
                success_count += 1
            else:
                print(f"❌ 策略优化失败或格式错误: {result}")
                
        except Exception as e:
            print(f"❌ 策略优化异常: {e}")
        
        # 测试2: 策略调节  
        print("\n⚙️ 测试策略调节")
        total_tests += 1
        try:
            result = super_ego.ultra_think.regulate_cognitive_strategy(
                {"situation": "测试场景", "load": "中等"},
                ["保持稳定", "优化性能"]
            )
            
            if 'error' not in result and _validate_regulation_schema(result):
                print("✅ 策略调节成功")
                success_count += 1
            else:
                print(f"❌ 策略调节失败或格式错误: {result}")
                
        except Exception as e:
            print(f"❌ 策略调节异常: {e}")
        
        # 测试3: 经验反思
        print("\n🤔 测试经验反思")
        total_tests += 1
        try:
            result = super_ego.reflection_engine.reflect_on_experience(
                {"action": "测试执行", "context": "开发环境"},
                {"success": True, "duration": 120}
            )
            
            if 'error' not in result and _validate_reflection_schema(result):
                print("✅ 经验反思成功")
                success_count += 1
            else:
                print(f"❌ 经验反思失败或格式错误: {result}")
                
        except Exception as e:
            print(f"❌ 经验反思异常: {e}")
        
        # 测试4: 认知监督
        print("\n👁️ 测试认知监督")
        total_tests += 1
        try:
            # 创建模拟的决策结果
            mock_ego_result = {
                "decision": "执行任务A",
                "reasoning": "基于当前情况分析",
                "confidence": 0.8
            }
            
            mock_id_result = {
                "motivation": "完成目标",
                "emotional_state": "专注",
                "energy_level": 0.9
            }
            
            result = super_ego.supervise_cognitive_process(
                ego_result=mock_ego_result,
                id_result=mock_id_result,
                context={"task": "测试监督"}
            )
            
            if result and 'supervision_summary' in result:
                print("✅ 认知监督成功")
                success_count += 1
            else:
                print(f"❌ 认知监督失败: {result}")
                
        except Exception as e:
            print(f"❌ 认知监督异常: {e}")
        
        # 测试5: 综合稳定性测试
        print("\n🔄 综合稳定性测试 (5次)")
        stability_success = 0
        for i in range(5):
            try:
                result = super_ego.strategy_optimizer.optimize_strategy(
                    {"metric": 0.7 + i * 0.05}, 
                    {"iteration": i}, 
                    [f"目标{i+1}"]
                )
                if 'error' not in result and _validate_strategy_schema(result):
                    stability_success += 1
            except Exception:
                pass
        
        stability_rate = (stability_success / 5) * 100
        print(f"稳定性测试成功率: {stability_rate:.1f}% ({stability_success}/5)")
        if stability_rate >= 80:
            success_count += 1
        total_tests += 1
        
        # 结果统计
        success_rate = (success_count / total_tests) * 100
        print(f"\n📊 总体测试结果: {success_rate:.1f}% ({success_count}/{total_tests})")
        
        return success_rate >= 80
        
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
    
    for field in required_fields:
        if field not in result:
            return False
    
    if not isinstance(result["analysis"], str):
        return False
    if not isinstance(result["strategies"], list) or len(result["strategies"]) == 0:
        return False
    if result["priority"] not in ["high", "medium", "low"]:
        return False
    if not isinstance(result["confidence"], (int, float)) or not (0.0 <= result["confidence"] <= 1.0):
        return False
    
    return True


def _validate_regulation_schema(result: dict) -> bool:
    """验证策略调节结果是否符合schema"""
    required_fields = ["assessment", "adjustment_needed", "recommended_strategy", "confidence"]
    
    for field in required_fields:
        if field not in result:
            return False
    
    if not isinstance(result["assessment"], str):
        return False
    if not isinstance(result["adjustment_needed"], bool):
        return False
    if not isinstance(result["recommended_strategy"], str):
        return False
    if not isinstance(result["confidence"], (int, float)) or not (0.0 <= result["confidence"] <= 1.0):
        return False
    
    return True


def _validate_reflection_schema(result: dict) -> bool:
    """验证反思结果是否符合schema"""
    required_fields = ["lessons", "suggestions", "quality"]
    
    for field in required_fields:
        if field not in result:
            return False
    
    if not isinstance(result["lessons"], list) or len(result["lessons"]) == 0:
        return False
    if not isinstance(result["suggestions"], list) or len(result["suggestions"]) == 0:
        return False
    if not isinstance(result["quality"], (int, float)) or not (0.0 <= result["quality"] <= 1.0):
        return False
    
    return True


def test_json_response_stability():
    """测试JSON响应稳定性"""
    print("\n📋 JSON响应稳定性专项测试")
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
                max_tokens=800,
                temperature=0.3
            )
        elif os.getenv('OPENAI_API_KEY'):
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                max_tokens=800,
                temperature=0.3
            )
        else:
            print("❌ 未找到API密钥")
            return False
        
        optimizer = StructuredResponseOptimizer(llm)
        
        # 大批量测试
        test_cases = [
            {"performance": {"speed": 0.7}, "context": {"env": "prod"}, "goals": ["optimize"]},
            {"performance": {"accuracy": 0.9}, "context": {"task": "analysis"}, "goals": ["maintain", "improve"]},
            {"performance": {"efficiency": 0.8}, "context": {"load": "high"}, "goals": ["stabilize"]},
        ]
        
        success_count = 0
        total_count = len(test_cases) * 3  # 每个测试案例重复3次
        
        for i, test_case in enumerate(test_cases):
            print(f"\n测试案例 {i+1}: {len(test_case['goals'])} 个目标")
            
            for attempt in range(3):
                try:
                    result = optimizer.optimize_strategy_structured(
                        test_case["performance"],
                        test_case["context"],
                        test_case["goals"]
                    )
                    
                    if _validate_strategy_schema(result):
                        success_count += 1
                        print(f"  尝试 {attempt+1}: ✅")
                    else:
                        print(f"  尝试 {attempt+1}: ❌ Schema验证失败")
                        
                except Exception as e:
                    print(f"  尝试 {attempt+1}: ❌ 异常: {e}")
        
        success_rate = (success_count / total_count) * 100
        print(f"\n📈 JSON响应稳定性: {success_rate:.1f}% ({success_count}/{total_count})")
        
        return success_rate >= 90
        
    except Exception as e:
        print(f"❌ 稳定性测试失败: {e}")
        return False


if __name__ == "__main__":
    print("🎯 SuperEgo Agent 全面测试工具")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 测试所有方法
    methods_success = test_all_superego_methods()
    
    # 测试JSON稳定性
    stability_success = test_json_response_stability()
    
    print("\n" + "=" * 80)
    print("📊 综合测试总结:")
    print(f"方法功能测试: {'✅ 成功' if methods_success else '❌ 失败'}")
    print(f"JSON稳定性测试: {'✅ 成功' if stability_success else '❌ 失败'}")
    
    if methods_success and stability_success:
        print("\n🎉 所有测试通过!")
        print("💡 SuperEgo Agent已完全支持结构化JSON输出")
        print("📈 建议在生产环境中使用 use_structured_output=True")
    else:
        print("\n⚠️ 部分测试失败")
        print("💡 建议检查失败的具体方法并进行调试")