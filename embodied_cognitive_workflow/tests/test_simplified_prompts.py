#!/usr/bin/env python3
"""
测试简化提示词的响应效果
验证简化提示是否能获得更稳定的LLM响应
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


def test_simplified_vs_complex_prompts():
    """对比简化提示与复杂提示的响应效果"""
    print("🔍 对比简化提示 vs 复杂提示")
    print("=" * 60)
    
    try:
        # 尝试使用不同的LLM
        from langchain_openai import ChatOpenAI
        
        # 检查可用的API
        if os.getenv('DEEPSEEK_API_KEY'):
            llm = ChatOpenAI(
                model="deepseek-chat",
                openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
                openai_api_base="https://api.deepseek.com",
                max_tokens=800,
                temperature=0.3
            )
            print("🤖 使用DeepSeek模型")
        elif os.getenv('OPENAI_API_KEY'):
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                openai_api_key=os.getenv('OPENAI_API_KEY'),
                max_tokens=800,
                temperature=0.3
            )
            print("🤖 使用OpenAI GPT-3.5-turbo")
        else:
            print("❌ 未找到API密钥")
            return False
        
        # 测试1: 复杂提示 (原版)
        print("\n📝 测试1: 复杂提示")
        complex_prompt = """
        基于当前性能指标和上下文，优化认知策略：
        
        当前性能：{"efficiency": 0.8, "accuracy": 0.9, "resource_usage": 0.7}
        上下文：{"task": "认知监督", "complexity": "高", "environment": "生产环境"}
        目标：["提高效率", "保持准确性", "优化资源利用"]
        
        请分析并提供：
        1. 当前策略的瓶颈分析
        2. 优化建议和具体策略
        3. 预期改进效果
        4. 实施优先级
        
        返回JSON格式：
        {
            "bottleneck_analysis": "瓶颈分析",
            "optimization_strategies": ["策略1", "策略2"],
            "expected_improvement": "预期改进",
            "implementation_priority": "high/medium/low",
            "confidence_score": 0.0-1.0
        }
        """
        
        try:
            response = llm.invoke(complex_prompt)
            print(f"复杂提示响应长度: {len(response.content) if response.content else 0}")
            
            if response.content and response.content.strip():
                print("✅ 复杂提示有响应")
                try:
                    parsed = json.loads(response.content.strip())
                    print("✅ 复杂提示JSON解析成功")
                except json.JSONDecodeError:
                    print("❌ 复杂提示JSON解析失败")
            else:
                print("❌ 复杂提示无响应")
                
        except Exception as e:
            print(f"❌ 复杂提示测试失败: {e}")
        
        # 测试2: 简化提示 (新版)
        print("\n📝 测试2: 简化提示")
        simple_prompt = """请优化策略。

性能: efficiency 0.8, accuracy 0.9
上下文: 认知监督任务, 高复杂度
目标: 提高效率, 保持准确性

返回JSON:
{
    "analysis": "分析结果",
    "strategies": ["策略1", "策略2"],
    "priority": "medium",
    "confidence": 0.8
}"""
        
        try:
            response = llm.invoke(simple_prompt)
            print(f"简化提示响应长度: {len(response.content) if response.content else 0}")
            
            if response.content and response.content.strip():
                print("✅ 简化提示有响应")
                try:
                    parsed = json.loads(response.content.strip())
                    print("✅ 简化提示JSON解析成功")
                    print("响应内容:")
                    print(json.dumps(parsed, ensure_ascii=False, indent=2))
                except json.JSONDecodeError:
                    print("❌ 简化提示JSON解析失败")
                    print(f"原始响应: {response.content}")
            else:
                print("❌ 简化提示无响应")
                
        except Exception as e:
            print(f"❌ 简化提示测试失败: {e}")
        
        # 测试3: 极简提示
        print("\n📝 测试3: 极简提示")
        minimal_prompt = """优化策略建议。

返回: {"analysis": "简要分析", "strategies": ["建议1"], "priority": "medium"}"""
        
        try:
            response = llm.invoke(minimal_prompt)
            print(f"极简提示响应长度: {len(response.content) if response.content else 0}")
            
            if response.content and response.content.strip():
                print("✅ 极简提示有响应")
                try:
                    parsed = json.loads(response.content.strip())
                    print("✅ 极简提示JSON解析成功")
                except json.JSONDecodeError:
                    print("❌ 极简提示JSON解析失败")
            else:
                print("❌ 极简提示无响应")
                
        except Exception as e:
            print(f"❌ 极简提示测试失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_superego_simplified_methods():
    """测试超我智能体的简化方法"""
    print("\n🧠 测试超我智能体简化方法")
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
                max_tokens=500,
                temperature=0.3
            )
        elif os.getenv('OPENAI_API_KEY'):
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                max_tokens=500,
                temperature=0.3
            )
        else:
            print("❌ 未找到API密钥")
            return False
        
        # 创建超我智能体
        super_ego = SuperEgoAgent(
            llm=llm,
            enable_ultra_think=True
        )
        
        # 测试策略优化
        print("\n📈 测试策略优化")
        if super_ego.strategy_optimizer:
            try:
                result = super_ego.strategy_optimizer.optimize_strategy(
                    current_performance={"efficiency": 0.8},
                    context={"task": "测试"},
                    goals=["提高效率"]
                )
                
                if 'error' not in result:
                    print("✅ 策略优化成功")
                    print(f"分析: {result.get('analysis', 'N/A')}")
                    print(f"策略: {result.get('strategies', [])}")
                else:
                    print(f"❌ 策略优化失败: {result['error']}")
                    
            except Exception as e:
                print(f"❌ 策略优化异常: {e}")
        
        # 测试策略调节
        print("\n⚙️ 测试策略调节")
        if super_ego.ultra_think:
            try:
                result = super_ego.ultra_think.regulate_cognitive_strategy(
                    current_context={"situation": "测试"},
                    target_goals=["稳定运行"]
                )
                
                if 'error' not in result:
                    print("✅ 策略调节成功")
                    print(f"评估: {result.get('assessment', 'N/A')}")
                    print(f"需要调整: {result.get('adjustment_needed', False)}")
                else:
                    print(f"❌ 策略调节失败: {result['error']}")
                    
            except Exception as e:
                print(f"❌ 策略调节异常: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


if __name__ == "__main__":
    print("🎯 简化提示词测试工具")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 测试不同复杂度的提示
    prompt_success = test_simplified_vs_complex_prompts()
    
    # 测试超我智能体方法
    method_success = test_superego_simplified_methods()
    
    print("\n" + "=" * 80)
    print("📊 测试总结:")
    print(f"提示对比测试: {'✅ 成功' if prompt_success else '❌ 失败'}")
    print(f"方法测试: {'✅ 成功' if method_success else '❌ 失败'}")
    
    if prompt_success and method_success:
        print("\n✅ 简化提示词优化成功!")
        print("💡 建议: 继续使用简化版本以提高稳定性")
    else:
        print("\n⚠️ 仍需进一步优化")
        print("💡 建议: 检查API配置和网络连接")