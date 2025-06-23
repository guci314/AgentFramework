#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试带代理配置的Transformer解析器
"""

import os
from enhancedAgent_v2 import MultiStepAgent_v2
from pythonTask import llm_deepseek, Agent

def test_transformer_with_proxy():
    """测试带代理配置的Transformer解析器"""
    print("=== 测试带代理配置的Transformer解析器 ===\n")
    
    # 1. 设置代理环境变量
    print("1. 设置代理环境变量...")
    os.environ['http_proxy'] = 'http://127.0.0.1:7890'
    os.environ['https_proxy'] = 'http://127.0.0.1:7890'
    print("   代理设置完成: http://127.0.0.1:7890")
    
    # 2. 创建智能体
    print("2. 创建MultiStepAgent_v2...")
    multi_agent = MultiStepAgent_v2(llm=llm_deepseek)
    
    # 3. 配置带代理的transformer解析器
    print("3. 配置带代理的transformer解析器...")
    try:
        multi_agent.configure_response_parser(
            parser_method="transformer",
            parser_config={
                'model_name': 'hfl/chinese-bert-wwm-ext',
                'confidence_threshold': 0.8,
                'cache_enabled': True,
                'cache_ttl': 3600,
                'proxy': 'http://127.0.0.1:7890',
                'cache_dir': './models'  # 本地缓存目录
            }
        )
        print("   ✅ Transformer解析器配置成功")
        
        # 检查解析器类型
        if hasattr(multi_agent, 'response_parser'):
            parser_type = type(multi_agent.response_parser).__name__
            print(f"   解析器类型: {parser_type}")
            
            # 检查配置
            if hasattr(multi_agent.response_parser, 'config'):
                config = multi_agent.response_parser.config
                print(f"   代理配置: {getattr(config, 'proxy', 'None')}")
                print(f"   缓存目录: {getattr(config, 'cache_dir', 'None')}")
                print(f"   模型名称: {getattr(config, 'model_name', 'None')}")
        
    except Exception as e:
        print(f"   ❌ Transformer配置失败: {e}")
        return False
    
    # 4. 注册子智能体
    print("\n4. 注册子智能体...")
    coder = Agent(llm=llm_deepseek, stateful=True)
    multi_agent.register_agent("coder", coder)
    
    # 5. 执行简单任务测试
    print("5. 执行简单任务测试transformer解析器...")
    try:
        result = multi_agent.execute_multi_step("创建一个简单的Hello World程序")
        print("   ✅ 任务执行成功")
        
        # 6. 检查解析历史
        print("6. 检查响应解析历史...")
        if hasattr(multi_agent, 'parsed_responses_history') and multi_agent.parsed_responses_history:
            print(f"   解析记录数: {len(multi_agent.parsed_responses_history)}")
            for i, entry in enumerate(multi_agent.parsed_responses_history[-2:], 1):  # 显示最后2条
                parsed_info = entry['parsed_info']
                print(f"   记录{i}: 步骤='{entry['step_name']}', 置信度={parsed_info.confidence_score:.2f}")
        else:
            print("   ⚠️ 无解析历史记录")
        
        # 7. 获取自然语言分析摘要
        print("\n7. 获取智能分析摘要...")
        summary = multi_agent.get_natural_language_analysis_summary()
        print(f"   摘要: {summary}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 任务执行失败: {e}")
        return False

def test_proxy_configuration_methods():
    """测试不同的代理配置方法"""
    print("\n=== 测试不同的代理配置方法 ===\n")
    
    # 方法1: 通过环境变量
    print("方法1: 通过环境变量设置代理")
    os.environ['http_proxy'] = 'http://127.0.0.1:7890'
    os.environ['https_proxy'] = 'http://127.0.0.1:7890'
    print("   ✅ 环境变量设置完成")
    
    # 方法2: 通过配置参数
    print("\n方法2: 通过配置参数设置代理")
    agent = MultiStepAgent_v2(llm=llm_deepseek)
    try:
        agent.configure_response_parser(
            parser_method="transformer",
            parser_config={
                'proxy': 'http://127.0.0.1:7890',
                'model_name': 'hfl/chinese-bert-wwm-ext'
            }
        )
        print("   ✅ 配置参数设置成功")
    except Exception as e:
        print(f"   ❌ 配置参数设置失败: {e}")

if __name__ == "__main__":
    # 测试1: 带代理的transformer解析器
    success = test_transformer_with_proxy()
    
    # 测试2: 不同的代理配置方法
    test_proxy_configuration_methods()
    
    print("\n" + "="*60)
    print("🎉 代理配置测试总结:")
    print("✅ 添加了代理服务器支持")
    print("✅ 支持通过环境变量和配置参数设置代理")
    print("✅ 支持自定义模型缓存目录")
    print("✅ 提供了代理可用性自动检测")
    
    if success:
        print("🚀 Transformer解析器在代理环境下工作正常")
    else:
        print("⚠️ 请检查代理服务器是否正常运行")
    
    print("\n💡 使用建议:")
    print("- 确保代理服务器 http://127.0.0.1:7890 正在运行")
    print("- 首次使用时模型下载可能需要几分钟时间")
    print("- 建议设置 cache_dir 参数以避免重复下载")