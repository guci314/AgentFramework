#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多方案响应解析器
测试四种解析方法：rule, transformer, deepseek, embedding
"""

import os
import sys
import logging
from response_parser_v2 import (
    ParserFactory, ParserMethod, ParserConfig,
    MultiMethodResponseParser, ParsedStateInfo
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_rule_parser():
    """测试规则解析器"""
    print("\n=== 测试规则解析器 ===")
    
    parser = ParserFactory.create_rule_parser()
    
    test_cases = [
        "文件创建成功，操作完成。",
        "发生了严重的系统错误！",
        "正在初始化配置参数...",
        "请提供您的用户名和密码。",
        "任务执行完毕，结果已保存到report.txt文件中。"
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        result = parser.parse_response(test_text)
        print(f"\n测试案例 {i}: {test_text}")
        print(f"  主要内容: {result.main_content}")
        print(f"  状态类型: {result.extracted_entities.get('status_type')}")
        print(f"  情感倾向: {result.sentiment}")
        print(f"  意图识别: {result.intent}")
        print(f"  置信度: {result.confidence_score:.3f}")
        print(f"  质量评级: {result.quality_metrics.get('overall_quality')}")

def test_transformer_parser():
    """测试Transformer解析器"""
    print("\n=== 测试Transformer解析器 ===")
    
    try:
        parser = ParserFactory.create_transformer_parser()
        
        test_text = "数据库连接建立成功，查询操作正常执行。"
        result = parser.parse_response(test_text)
        
        print(f"测试文本: {test_text}")
        print(f"状态类型: {result.extracted_entities.get('status_type')}")
        print(f"置信度: {result.confidence_score:.3f}")
        print(f"提取方法: {result.extracted_entities.get('extraction_method', 'unknown')}")
        
        if result.extracted_entities.get('extraction_method') == 'transformer':
            print("✅ Transformer解析器工作正常")
        else:
            print("⚠️ Transformer解析器降级到规则方法")
            
    except Exception as e:
        print(f"❌ Transformer解析器测试失败: {e}")

def test_deepseek_parser():
    """测试DeepSeek解析器"""
    print("\n=== 测试DeepSeek解析器 ===")
    
    # 检查是否有API密钥
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("⚠️ 未设置DEEPSEEK_API_KEY环境变量，跳过DeepSeek测试")
        return
    
    try:
        parser = ParserFactory.create_deepseek_parser(api_key=api_key)
        
        test_text = "用户认证失败，请检查用户名和密码是否正确。"
        result = parser.parse_response(test_text)
        
        print(f"测试文本: {test_text}")
        print(f"主要内容: {result.main_content}")
        print(f"状态类型: {result.extracted_entities.get('status_type')}")
        print(f"情感倾向: {result.sentiment}")
        print(f"意图识别: {result.intent}")
        print(f"置信度: {result.confidence_score:.3f}")
        print(f"提取方法: {result.extracted_entities.get('extraction_method', 'unknown')}")
        
        if result.extracted_entities.get('extraction_method') == 'deepseek':
            print("✅ DeepSeek解析器工作正常")
        else:
            print("⚠️ DeepSeek解析器降级到规则方法")
            
    except Exception as e:
        print(f"❌ DeepSeek解析器测试失败: {e}")

def test_embedding_parser():
    """测试嵌入解析器"""
    print("\n=== 测试嵌入解析器 ===")
    
    try:
        parser = ParserFactory.create_embedding_parser()
        
        test_text = "网络连接超时，无法访问远程服务器。"
        result = parser.parse_response(test_text)
        
        print(f"测试文本: {test_text}")
        print(f"状态类型: {result.extracted_entities.get('status_type')}")
        print(f"情感倾向: {result.sentiment}")
        print(f"置信度: {result.confidence_score:.3f}")
        print(f"最大相似度: {result.extracted_entities.get('max_similarity', 0):.3f}")
        print(f"提取方法: {result.extracted_entities.get('extraction_method', 'unknown')}")
        
        if result.extracted_entities.get('extraction_method') == 'embedding':
            print("✅ 嵌入解析器工作正常")
        else:
            print("⚠️ 嵌入解析器降级到规则方法")
            
    except Exception as e:
        print(f"❌ 嵌入解析器测试失败: {e}")

def test_hybrid_parser():
    """测试混合解析器"""
    print("\n=== 测试混合解析器 ===")
    
    # 创建具有完整降级链的混合解析器
    fallback_chain = [ParserMethod.RULE, ParserMethod.EMBEDDING]
    
    try:
        parser = ParserFactory.create_hybrid_parser(
            primary_method=ParserMethod.RULE,
            fallback_chain=fallback_chain,
            confidence_threshold=0.9  # 设置较高的阈值来触发降级
        )
        
        test_text = "操作超时，系统自动回滚到之前的状态。"
        result = parser.parse_response(test_text)
        
        print(f"测试文本: {test_text}")
        print(f"状态类型: {result.extracted_entities.get('status_type')}")
        print(f"置信度: {result.confidence_score:.3f}")
        
        # 检查统计信息
        stats = parser.get_stats()
        print(f"解析统计: {stats}")
        
        if stats['fallback_usage']:
            print("✅ 混合解析器降级功能工作正常")
        else:
            print("ℹ️ 混合解析器未触发降级")
            
    except Exception as e:
        print(f"❌ 混合解析器测试失败: {e}")

def test_config_variations():
    """测试不同配置选项"""
    print("\n=== 测试配置选项 ===")
    
    # 测试禁用缓存
    config1 = ParserConfig(
        method=ParserMethod.RULE,
        cache_enabled=False,
        enable_sentiment_analysis=False,
        enable_intent_recognition=False
    )
    parser1 = MultiMethodResponseParser(config1)
    
    test_text = "配置更新完成。"
    result1 = parser1.parse_response(test_text)
    
    print(f"禁用缓存和分析功能:")
    print(f"  情感倾向: {result1.sentiment}")
    print(f"  意图识别: {result1.intent}")
    
    # 测试启用所有功能
    config2 = ParserConfig(
        method=ParserMethod.RULE,
        cache_enabled=True,
        enable_sentiment_analysis=True,
        enable_intent_recognition=True,
        confidence_threshold=0.5
    )
    parser2 = MultiMethodResponseParser(config2)
    
    result2 = parser2.parse_response(test_text)
    
    print(f"启用所有功能:")
    print(f"  情感倾向: {result2.sentiment}")
    print(f"  意图识别: {result2.intent}")

def test_performance():
    """测试性能"""
    print("\n=== 性能测试 ===")
    
    import time
    
    parser = ParserFactory.create_rule_parser()
    
    test_texts = [
        "任务执行成功" * 10,  # 重复文本测试缓存
        "发生错误，请检查日志",
        "正在处理请求...",
    ] * 100  # 300个测试案例
    
    start_time = time.time()
    
    for text in test_texts:
        result = parser.parse_response(text)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"处理 {len(test_texts)} 个响应")
    print(f"总耗时: {total_time:.3f} 秒")
    print(f"平均耗时: {(total_time/len(test_texts)*1000):.3f} 毫秒/个")
    
    # 检查统计信息
    stats = parser.get_stats()
    print(f"平均置信度: {stats['average_confidence']:.3f}")
    print(f"成功率: {stats['success_rate']:.3f}")

def main():
    """主测试函数"""
    print("开始测试多方案响应解析器...")
    
    # 基础功能测试
    test_rule_parser()
    
    # 高级方法测试
    test_transformer_parser()
    test_deepseek_parser()
    test_embedding_parser()
    
    # 混合解析器测试
    test_hybrid_parser()
    
    # 配置测试
    test_config_variations()
    
    # 性能测试
    test_performance()
    
    print("\n=== 测试完成 ===")
    print("提示:")
    print("- 要测试DeepSeek API，请设置环境变量: export DEEPSEEK_API_KEY=your_key")
    print("- 要使用Transformer功能，请安装: pip install transformers torch")
    print("- 要使用嵌入功能，请安装: pip install sentence-transformers")

if __name__ == "__main__":
    main()