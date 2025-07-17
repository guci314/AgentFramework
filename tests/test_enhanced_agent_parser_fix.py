#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 enhancedAgent_v2.py 中的解析器初始化修复

验证在真实的Agent环境中，解析器初始化不再出现参数重复错误
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from response_parser_v2 import ParserMethod

# 设置日志
logging.basicConfig(level=logging.INFO)


def test_agent_parser_initialization():
    """测试Agent中解析器初始化"""
    print("=== 测试Agent中解析器初始化修复 ===")
    
    # 模拟agent初始化时的parser_config
    test_configs = [
        {
            "method": ParserMethod.TRANSFORMER,
            "config": {
                'model_name': 'hfl/chinese-bert-wwm-ext',
                'cache_enabled': True,
                'confidence_threshold': 0.7
            },
            "expected_model": 'hfl/chinese-bert-wwm-ext'
        },
        {
            "method": ParserMethod.EMBEDDING,
            "config": {
                'model_name': 'paraphrase-multilingual-MiniLM-L12-v2',
                'cache_enabled': False,
                'confidence_threshold': 0.6
            },
            "expected_model": 'paraphrase-multilingual-MiniLM-L12-v2'
        },
        {
            "method": ParserMethod.DEEPSEEK,
            "config": {
                'api_key': 'test_key_12345',
                'api_base': 'https://api.deepseek.com',
                'cache_enabled': True,
                'max_retries': 3
            },
            "expected_api_key": 'test_key_12345'
        }
    ]
    
    # 导入ParserFactory
    from response_parser_v2 import ParserFactory
    
    for i, test_case in enumerate(test_configs, 1):
        method = test_case["method"]
        parser_config = test_case["config"]
        
        print(f"\n测试 {i}: {method.value} 解析器")
        print(f"配置: {parser_config}")
        
        try:
            # 模拟enhancedAgent_v2.py中的初始化逻辑
            if method == ParserMethod.TRANSFORMER:
                model_name = parser_config.get('model_name', 'hfl/chinese-bert-wwm-ext')
                # 应用修复：移除重复的model_name
                transformer_config = {k: v for k, v in parser_config.items() if k != 'model_name'}
                response_parser = ParserFactory.create_transformer_parser(model_name=model_name, **transformer_config)
                
            elif method == ParserMethod.EMBEDDING:
                model_name = parser_config.get('model_name', 'paraphrase-multilingual-MiniLM-L12-v2')
                # 应用修复：移除重复的model_name
                embedding_config = {k: v for k, v in parser_config.items() if k != 'model_name'}
                response_parser = ParserFactory.create_embedding_parser(model_name=model_name, **embedding_config)
                
            elif method == ParserMethod.DEEPSEEK:
                api_key = parser_config.get('api_key')
                # 应用修复：移除重复的api_key和api_base
                deepseek_config = {k: v for k, v in parser_config.items() if k not in ['api_key', 'api_base']}
                api_base = parser_config.get('api_base')
                response_parser = ParserFactory.create_deepseek_parser(api_key=api_key, api_base=api_base, **deepseek_config)
            
            print(f"✓ 成功创建 {method.value} 解析器")
            
            # 验证配置是否正确传递
            if hasattr(response_parser, 'config'):
                print(f"  解析器配置: method={response_parser.config.method.value}")
                if method == ParserMethod.TRANSFORMER and 'expected_model' in test_case:
                    expected_model = test_case['expected_model']
                    actual_model = response_parser.config.model_name
                    if actual_model == expected_model:
                        print(f"  ✓ 模型名称正确: {actual_model}")
                    else:
                        print(f"  ✗ 模型名称不匹配: 期望 {expected_model}, 实际 {actual_model}")
                
                if method == ParserMethod.DEEPSEEK and 'expected_api_key' in test_case:
                    expected_api_key = test_case['expected_api_key']
                    actual_api_key = response_parser.config.api_key
                    if actual_api_key == expected_api_key:
                        print(f"  ✓ API密钥正确: {actual_api_key}")
                    else:
                        print(f"  ✗ API密钥不匹配: 期望 {expected_api_key}, 实际 {actual_api_key}")
            
        except Exception as e:
            print(f"✗ 创建 {method.value} 解析器失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n=== 测试完成 ===")


def test_agent_parser_with_old_method():
    """测试使用旧方法（应该失败）"""
    print("\n=== 测试使用旧方法（验证问题确实存在）===")
    
    from response_parser_v2 import ParserFactory
    
    # 模拟旧的错误调用方式
    parser_config = {
        'model_name': 'hfl/chinese-bert-wwm-ext',
        'cache_enabled': True,
        'confidence_threshold': 0.7
    }
    
    try:
        # 这应该会失败
        model_name = parser_config.get('model_name', 'hfl/chinese-bert-wwm-ext')
        response_parser = ParserFactory.create_transformer_parser(model_name=model_name, **parser_config)
        print("✗ 旧方法竟然成功了，这不应该发生")
    except TypeError as e:
        if "multiple values for keyword argument 'model_name'" in str(e):
            print(f"✓ 确认旧方法存在问题: {e}")
        else:
            print(f"✗ 其他错误: {e}")
    except Exception as e:
        print(f"✗ 意外错误: {e}")


if __name__ == "__main__":
    test_agent_parser_initialization()
    test_agent_parser_with_old_method()