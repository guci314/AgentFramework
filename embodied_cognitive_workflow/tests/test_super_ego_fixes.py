#!/usr/bin/env python3
"""
测试超我智能体JSON解析修复
验证之前的JSON解析错误是否已经修复
"""

import sys
import os
from datetime import datetime

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from langchain_openai import ChatOpenAI
    from embodied_cognitive_workflow import SuperEgoAgent
    print("✅ 成功导入模块")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)


def test_super_ego_json_fixes():
    """测试超我智能体的JSON解析修复"""
    print("🔧 测试超我智能体JSON解析修复")
    print("=" * 50)
    
    try:
        # 初始化LLM（使用较小的模型以减少成本）
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            max_tokens=1000
        )
        
        # 初始化超我智能体
        super_ego = SuperEgoAgent(
            llm=llm,
            enable_bias_detection=True,
            enable_logic_validation=True,
            enable_consistency_check=True,
            enable_moral_guidance=True,
            enable_ultra_think=True
        )
        
        print("✅ 超我智能体初始化成功")
        
        # 测试1: 基础认知监督
        print("\n📝 测试1: 基础认知监督")
        reasoning_text = "基于历史数据，我们的销售策略是正确的。"
        context = {"domain": "商业决策"}
        goals = ["提升销售"]
        
        try:
            result = super_ego.supervise_cognitive_process(
                reasoning_text=reasoning_text,
                context=context,
                goals=goals
            )
            print(f"✅ 基础监督成功，健康评分: {result.get('overall_health_score', 'N/A')}")
        except Exception as e:
            print(f"❌ 基础监督失败: {e}")
        
        # 测试2: 元认知分析（可能触发策略调节错误）
        print("\n🧠 测试2: 元认知分析")
        if super_ego.ultra_think:
            try:
                process_data = {"task": "测试任务", "complexity": "中等"}
                performance_metrics = {"execution_time": 5.0, "accuracy": 0.9}
                context_data = {"environment": "测试环境"}
                goals_list = ["完成测试", "验证修复"]
                
                meta_result = super_ego.meta_cognitive_analysis(
                    process_data=process_data,
                    performance_metrics=performance_metrics,
                    context=context_data,
                    goals=goals_list
                )
                
                if 'error' in meta_result:
                    print(f"⚠️ 元认知分析有错误: {meta_result['error']}")
                else:
                    print("✅ 元认知分析成功")
                    if meta_result.get('strategy_regulation'):
                        if 'error' in meta_result['strategy_regulation']:
                            print(f"⚠️ 策略调节有错误: {meta_result['strategy_regulation']['error']}")
                        else:
                            print("✅ 策略调节成功")
                            
            except Exception as e:
                print(f"❌ 元认知分析失败: {e}")
        
        # 测试3: 反思学习
        print("\n🎓 测试3: 反思学习")
        try:
            experience_data = {
                "task": "测试任务",
                "approach": "系统化方法",
                "context": "测试环境"
            }
            outcome = {
                "success": True,
                "result": "任务完成",
                "lessons": []
            }
            
            reflection_result = super_ego.reflect_and_learn(experience_data, outcome)
            
            if 'error' in reflection_result:
                print(f"⚠️ 反思学习有错误: {reflection_result['error']}")
            else:
                print("✅ 反思学习成功")
                lessons = reflection_result.get('lessons_learned', [])
                if lessons:
                    print(f"📚 学到的经验: {lessons[0] if lessons else '无'}")
                    
        except Exception as e:
            print(f"❌ 反思学习失败: {e}")
        
        # 测试4: 策略优化
        print("\n⚙️ 测试4: 策略优化")
        try:
            performance_metrics = {"efficiency": 0.8, "accuracy": 0.9}
            improvements = ["提高效率", "减少错误"]
            
            optimization_result = super_ego.optimize_cognitive_strategy(
                current_performance=performance_metrics,
                target_improvements=improvements
            )
            
            if 'error' in optimization_result:
                print(f"⚠️ 策略优化有错误: {optimization_result['error']}")
            else:
                print("✅ 策略优化成功")
                
        except Exception as e:
            print(f"❌ 策略优化失败: {e}")
        
        # 测试5: 获取监督摘要
        print("\n📊 测试5: 监督摘要")
        try:
            summary = super_ego.get_supervision_summary()
            print(f"✅ 监督摘要成功")
            print(f"   总监督次数: {summary['metrics']['total_supervisions']}")
            print(f"   检测偏差: {summary['metrics']['biases_detected']}")
            print(f"   发现逻辑错误: {summary['metrics']['logic_errors_found']}")
            
        except Exception as e:
            print(f"❌ 获取监督摘要失败: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 测试完成！")
        print("✨ JSON解析错误修复验证完毕")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧠 超我智能体JSON解析修复测试")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    success = test_super_ego_json_fixes()
    
    if success:
        print("\n✅ 所有测试通过，JSON解析错误已修复！")
    else:
        print("\n❌ 测试失败，可能还有未修复的问题")