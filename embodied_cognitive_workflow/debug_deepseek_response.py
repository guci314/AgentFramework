#!/usr/bin/env python3
"""
调试DeepSeek API响应问题
专门针对DeepSeek模型的响应分析
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def test_deepseek_response():
    """测试DeepSeek API响应"""
    print("🔍 测试DeepSeek API响应")
    print("=" * 50)
    
    try:
        # 尝试导入不同的LLM客户端
        try:
            from langchain_community.chat_models import ChatDeepSeek
            print("✅ 成功导入ChatDeepSeek")
            llm_type = "ChatDeepSeek"
        except ImportError:
            try:
                from langchain_openai import ChatOpenAI
                print("✅ 使用ChatOpenAI作为DeepSeek客户端")
                llm_type = "ChatOpenAI"
            except ImportError:
                print("❌ 无法导入任何LLM客户端")
                return False
        
        # 检查API密钥
        deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if deepseek_key:
            print("✅ 找到DEEPSEEK_API_KEY")
            api_key = deepseek_key
            base_url = "https://api.deepseek.com"
        elif openai_key:
            print("✅ 找到OPENAI_API_KEY，使用OpenAI")
            api_key = openai_key  
            base_url = None
        else:
            print("❌ 未找到API密钥")
            return False
        
        # 初始化LLM
        if llm_type == "ChatDeepSeek" and deepseek_key:
            llm = ChatDeepSeek(
                model="deepseek-chat",
                deepseek_api_key=deepseek_key,
                max_tokens=1000,
                temperature=0.3
            )
            print("🤖 使用DeepSeek模型")
        else:
            from langchain_openai import ChatOpenAI
            if base_url:
                llm = ChatOpenAI(
                    model="deepseek-chat",
                    openai_api_key=api_key,
                    openai_api_base=base_url,
                    max_tokens=1000,
                    temperature=0.3
                )
                print("🤖 使用DeepSeek API (通过OpenAI接口)")
            else:
                llm = ChatOpenAI(
                    model="gpt-3.5-turbo",
                    openai_api_key=api_key,
                    max_tokens=1000,
                    temperature=0.3
                )
                print("🤖 使用OpenAI GPT-3.5-turbo")
        
        # 测试简单提示
        print("\n📝 测试1: 简单JSON响应")
        simple_prompt = """请用JSON格式回答：你好！
        
        返回格式：
        {
            "greeting": "你的问候",
            "status": "ok"
        }"""
        
        try:
            response = llm.invoke(simple_prompt)
            print(f"响应类型: {type(response)}")
            print(f"响应内容: '{response.content}'")
            print(f"响应长度: {len(response.content) if response.content else 0}")
            
            if response.content and response.content.strip():
                try:
                    parsed = json.loads(response.content.strip())
                    print("✅ JSON解析成功")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
                    print(f"原始内容: {repr(response.content)}")
            else:
                print("⚠️ 收到空响应")
                
        except Exception as e:
            print(f"❌ 简单测试失败: {e}")
        
        # 测试策略优化相似的提示
        print("\n📝 测试2: 策略优化提示")
        strategy_prompt = """基于当前性能指标，提供优化建议：

当前性能：{"efficiency": 0.8, "accuracy": 0.9}
目标：["提高效率"]

请返回JSON格式：
{
    "bottleneck_analysis": "分析内容", 
    "optimization_strategies": ["策略1"],
    "implementation_priority": "medium"
}"""
        
        try:
            response = llm.invoke(strategy_prompt)
            print(f"策略优化响应长度: {len(response.content) if response.content else 0}")
            
            if response.content and response.content.strip():
                print("✅ 策略优化有响应")
                try:
                    parsed = json.loads(response.content.strip())
                    print("✅ 策略优化JSON解析成功")
                    print(json.dumps(parsed, ensure_ascii=False, indent=2))
                except json.JSONDecodeError as e:
                    print(f"❌ 策略优化JSON解析失败: {e}")
                    print(f"原始响应: {response.content[:200]}...")
            else:
                print("⚠️ 策略优化收到空响应")
                
        except Exception as e:
            print(f"❌ 策略优化测试失败: {e}")
        
        # 测试超长提示的影响
        print("\n📝 测试3: 长提示处理")
        long_data = {"很长的数据": "x" * 1000}
        long_prompt = f"""分析以下数据：

数据：{json.dumps(long_data, ensure_ascii=False)}

请简单返回：{{"status": "analyzed"}}"""
        
        try:
            print(f"长提示长度: {len(long_prompt)} 字符")
            response = llm.invoke(long_prompt)
            
            if response.content and response.content.strip():
                print("✅ 长提示有响应")
            else:
                print("⚠️ 长提示收到空响应")
                
        except Exception as e:
            print(f"❌ 长提示测试失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def analyze_prompt_issues():
    """分析可能导致空响应的提示问题"""
    print("\n🔍 分析提示问题")
    print("=" * 50)
    
    # 检查超我智能体的提示模板
    problematic_patterns = [
        "过长的JSON示例",
        "复杂的嵌套结构",
        "中英文混合",
        "特殊字符",
        "过多的指令要求"
    ]
    
    print("🎯 可能导致空响应的问题:")
    for i, pattern in enumerate(problematic_patterns, 1):
        print(f"  {i}. {pattern}")
    
    print("\n💡 建议的解决方案:")
    print("  1. 简化提示词结构")
    print("  2. 减少JSON示例的复杂度") 
    print("  3. 使用更直接的指令")
    print("  4. 限制提示词长度")
    print("  5. 分步骤请求而不是一次性复杂请求")


def suggest_prompt_optimization():
    """建议提示优化策略"""
    print("\n🎯 提示优化建议")
    print("=" * 50)
    
    print("原始复杂提示 → 简化提示:")
    print()
    
    print("❌ 问题提示:")
    print("""基于当前性能指标和上下文，优化认知策略：

当前性能：{复杂的性能数据}
上下文：{复杂的上下文数据}  
目标：{复杂的目标列表}

请分析并提供：
1. 当前策略的瓶颈分析
2. 优化建议和具体策略  
3. 预期改进效果
4. 实施优先级

返回JSON格式：{复杂的JSON模板}""")
    
    print("\n✅ 优化提示:")
    print("""请提供策略优化建议。

简单返回：
{
    "analysis": "简要分析",
    "strategies": ["建议1", "建议2"],  
    "priority": "high"
}""")


if __name__ == "__main__":
    print("🔧 DeepSeek响应调试工具")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 运行测试
    success = test_deepseek_response()
    
    # 分析问题
    analyze_prompt_issues()
    
    # 建议优化
    suggest_prompt_optimization()
    
    print("\n" + "=" * 60)
    print("📊 调试总结:")
    if success:
        print("✅ 基础API连接正常")
        print("💡 重点检查提示词复杂度和长度")
    else:
        print("❌ API连接或配置有问题")
        print("💡 优先检查API密钥和网络连接")