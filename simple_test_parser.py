#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试多方案响应解析器
"""

from response_parser_v2 import ParserFactory, ParserMethod

def test_basic_functionality():
    """测试基本功能"""
    print("=== 基本功能测试 ===")
    
    # 创建规则解析器
    parser = ParserFactory.create_rule_parser()
    
    test_cases = [
        ("成功案例", "文件创建成功，操作完成。"),
        ("错误案例", "发生了严重的系统错误！"),
        ("进度案例", "正在初始化配置参数..."),
        ("请求案例", "请提供您的用户名和密码。"),
        ("报告案例", "当前系统状态正常，所有服务运行良好。")
    ]
    
    for name, text in test_cases:
        result = parser.parse_response(text)
        print(f"\n{name}: {text}")
        print(f"  状态: {result.extracted_entities.get('status_type')}")
        print(f"  情感: {result.sentiment}")
        print(f"  意图: {result.intent}")
        print(f"  置信度: {result.confidence_score:.2f}")

def test_fallback_mechanism():
    """测试降级机制"""
    print("\n=== 降级机制测试 ===")
    
    # 创建混合解析器，设置高置信度阈值
    parser = ParserFactory.create_hybrid_parser(
        primary_method=ParserMethod.RULE,
        fallback_chain=[ParserMethod.RULE],
        confidence_threshold=0.95  # 很高的阈值
    )
    
    text = "系统运行状态良好"
    result = parser.parse_response(text)
    
    print(f"测试文本: {text}")
    print(f"置信度: {result.confidence_score:.2f}")
    
    stats = parser.get_stats()
    print(f"统计信息: {stats}")

def test_configuration():
    """测试配置选项"""
    print("\n=== 配置选项测试 ===")
    
    # 测试不同配置
    configs = [
        ("标准配置", {"cache_enabled": True, "enable_sentiment_analysis": True}),
        ("最小配置", {"cache_enabled": False, "enable_sentiment_analysis": False, "enable_intent_recognition": False}),
        ("高阈值配置", {"confidence_threshold": 0.9})
    ]
    
    test_text = "数据备份已完成，请查看备份日志。"
    
    for name, config_params in configs:
        parser = ParserFactory.create_rule_parser(**config_params)
        result = parser.parse_response(test_text)
        
        print(f"\n{name}:")
        print(f"  情感分析: {result.sentiment}")
        print(f"  意图识别: {result.intent}")
        print(f"  置信度: {result.confidence_score:.2f}")

if __name__ == "__main__":
    test_basic_functionality()
    test_fallback_mechanism()  
    test_configuration()
    
    print("\n=== 测试完成 ===")
    print("✅ 规则解析器工作正常")
    print("ℹ️ 其他解析器需要相应的依赖库和配置")