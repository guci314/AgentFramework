#!/usr/bin/env python3
"""
调试LLM响应问题
检查为什么LLM返回空响应
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
    print("✅ 成功导入ChatOpenAI")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)


def test_llm_response():
    """测试LLM响应"""
    print("🔍 测试LLM响应")
    print("=" * 40)
    
    try:
        # 初始化LLM
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            max_tokens=1000
        )
        
        # 测试简单的策略优化提示
        test_prompt = """
        基于当前性能指标和上下文，优化认知策略：
        
        当前性能：{"efficiency": 0.8, "accuracy": 0.9}
        上下文：{"task": "测试任务", "complexity": "中等"}
        目标：["提高效率", "保持准确性"]
        
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
        
        print("📤 发送测试提示...")
        print(f"提示长度: {len(test_prompt)} 字符")
        
        # 调用LLM
        response = llm.invoke(test_prompt)
        
        print("📥 LLM响应:")
        print(f"响应类型: {type(response)}")
        print(f"响应内容: '{response.content}'")
        print(f"响应长度: {len(response.content)} 字符")
        
        if not response.content.strip():
            print("⚠️ 响应为空！")
            return False
        
        # 尝试解析JSON
        import json
        try:
            parsed = json.loads(response.content.strip())
            print("✅ JSON解析成功:")
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
            return True
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            print("原始响应内容:")
            print(repr(response.content))
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_prompt():
    """测试简单提示"""
    print("\n🔍 测试简单提示")
    print("=" * 40)
    
    try:
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            max_tokens=500
        )
        
        simple_prompt = "请用JSON格式回答：你好，今天天气如何？格式：{\"greeting\": \"回应\", \"weather\": \"天气描述\"}"
        
        print("📤 发送简单提示...")
        response = llm.invoke(simple_prompt)
        
        print("📥 简单提示响应:")
        print(f"响应内容: '{response.content}'")
        print(f"响应长度: {len(response.content)} 字符")
        
        if response.content.strip():
            print("✅ 简单提示有响应")
            return True
        else:
            print("❌ 简单提示也无响应")
            return False
            
    except Exception as e:
        print(f"❌ 简单提示测试失败: {e}")
        return False


if __name__ == "__main__":
    print("🔧 LLM响应调试工具")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 检查API密钥
    import os
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️ 警告: 未找到OPENAI_API_KEY环境变量")
    else:
        print("✅ 找到OPENAI_API_KEY环境变量")
    
    # 测试简单提示
    simple_success = test_simple_prompt()
    
    # 测试复杂提示
    complex_success = test_llm_response()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"简单提示: {'✅ 成功' if simple_success else '❌ 失败'}")
    print(f"复杂提示: {'✅ 成功' if complex_success else '❌ 失败'}")
    
    if not simple_success:
        print("\n💡 建议:")
        print("1. 检查OPENAI_API_KEY是否正确设置")
        print("2. 检查网络连接")
        print("3. 检查API额度")
    elif not complex_success:
        print("\n💡 建议:")
        print("1. 简化提示词")
        print("2. 增加max_tokens")
        print("3. 调整temperature参数")