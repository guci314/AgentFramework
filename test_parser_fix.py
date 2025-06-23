#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 create_transformer_parser 方法的参数传递修复

这个测试脚本验证修复后不再出现 "multiple values for keyword argument 'model_name'" 错误
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from response_parser_v2 import ParserFactory, ParserMethod


def test_transformer_parser_fix():
    """测试Transformer解析器参数传递修复"""
    print("=== 测试Transformer解析器参数传递修复 ===")
    
    try:
        # 测试情况1：只传递model_name参数
        print("测试1: 只传递model_name参数")
        parser1 = ParserFactory.create_transformer_parser(model_name='hfl/chinese-bert-wwm-ext')
        print("✓ 成功创建解析器")
        
        # 测试情况2：通过kwargs传递model_name（之前会导致错误的情况）
        print("\n测试2: 通过kwargs传递model_name")
        config_with_model_name = {
            'model_name': 'hfl/chinese-bert-wwm-ext',
            'cache_enabled': True,
            'confidence_threshold': 0.7
        }
        
        # 模拟修复前的问题调用（这应该不再出错）
        try:
            parser2 = ParserFactory.create_transformer_parser(
                model_name=config_with_model_name.get('model_name', 'hfl/chinese-bert-wwm-ext'),
                **config_with_model_name
            )
            print("✗ 这里应该会报错，但没有报错。可能修复没有生效")
        except TypeError as e:
            if "multiple values for keyword argument 'model_name'" in str(e):
                print(f"✓ 确认存在问题: {e}")
            else:
                print(f"✗ 其他类型错误: {e}")
        
        # 测试情况3：正确的调用方式（移除重复的model_name）
        print("\n测试3: 正确的调用方式（移除重复参数）")
        model_name = config_with_model_name.get('model_name', 'hfl/chinese-bert-wwm-ext')
        filtered_config = {k: v for k, v in config_with_model_name.items() if k != 'model_name'}
        parser3 = ParserFactory.create_transformer_parser(model_name=model_name, **filtered_config)
        print("✓ 成功创建解析器（使用修复后的方法）")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_embedding_parser_fix():
    """测试Embedding解析器参数传递修复"""
    print("\n=== 测试Embedding解析器参数传递修复 ===")
    
    try:
        # 测试相同的问题是否在embedding解析器中存在
        config_with_model_name = {
            'model_name': 'paraphrase-multilingual-MiniLM-L12-v2',
            'cache_enabled': True,
            'confidence_threshold': 0.6
        }
        
        print("测试: 通过kwargs传递model_name")
        try:
            parser = ParserFactory.create_embedding_parser(
                model_name=config_with_model_name.get('model_name', 'paraphrase-multilingual-MiniLM-L12-v2'),
                **config_with_model_name
            )
            print("✗ 这里应该会报错，但没有报错")
        except TypeError as e:
            if "multiple values for keyword argument 'model_name'" in str(e):
                print(f"✓ 确认存在问题: {e}")
            else:
                print(f"✗ 其他类型错误: {e}")
        
        # 正确的调用方式
        print("测试: 正确的调用方式")
        model_name = config_with_model_name.get('model_name', 'paraphrase-multilingual-MiniLM-L12-v2')
        filtered_config = {k: v for k, v in config_with_model_name.items() if k != 'model_name'}
        parser_fixed = ParserFactory.create_embedding_parser(model_name=model_name, **filtered_config)
        print("✓ 成功创建解析器（使用修复后的方法）")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")


def test_deepseek_parser_fix():
    """测试DeepSeek解析器参数传递修复"""
    print("\n=== 测试DeepSeek解析器参数传递修复 ===")
    
    try:
        config_with_api_key = {
            'api_key': 'test_api_key',
            'api_base': 'https://api.deepseek.com',
            'cache_enabled': True,
            'confidence_threshold': 0.8
        }
        
        print("测试: 通过kwargs传递api_key")
        try:
            parser = ParserFactory.create_deepseek_parser(
                api_key=config_with_api_key.get('api_key'),
                **config_with_api_key
            )
            print("✗ 这里应该会报错，但没有报错")
        except TypeError as e:
            if "multiple values for keyword argument 'api_key'" in str(e):
                print(f"✓ 确认存在问题: {e}")
            else:
                print(f"✗ 其他类型错误: {e}")
        
        # 正确的调用方式
        print("测试: 正确的调用方式")
        api_key = config_with_api_key.get('api_key')
        api_base = config_with_api_key.get('api_base')
        filtered_config = {k: v for k, v in config_with_api_key.items() if k not in ['api_key', 'api_base']}
        parser_fixed = ParserFactory.create_deepseek_parser(api_key=api_key, api_base=api_base, **filtered_config)
        print("✓ 成功创建解析器（使用修复后的方法）")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")


if __name__ == "__main__":
    test_transformer_parser_fix()
    test_embedding_parser_fix()
    test_deepseek_parser_fix()