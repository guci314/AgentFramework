#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查模型缓存目录和下载位置
"""

import os
from pathlib import Path

def check_model_cache_directories():
    """检查模型缓存目录"""
    print("=== 模型缓存目录检查 ===\n")
    
    # 1. HuggingFace 默认缓存目录
    try:
        import transformers
        default_cache = transformers.utils.TRANSFORMERS_CACHE
        print(f"1. HuggingFace 默认缓存目录:")
        print(f"   {default_cache}")
        print(f"   是否存在: {os.path.exists(default_cache)}")
        
        if os.path.exists(default_cache):
            # 检查目录大小
            total_size = 0
            file_count = 0
            for root, dirs, files in os.walk(default_cache):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except:
                        pass
            
            print(f"   目录大小: {total_size / (1024**3):.2f} GB")
            print(f"   文件数量: {file_count}")
            
            # 列出已下载的模型
            print(f"   已下载的模型:")
            models_dir = os.path.join(default_cache, "models")
            if os.path.exists(models_dir):
                for item in os.listdir(models_dir):
                    if os.path.isdir(os.path.join(models_dir, item)):
                        print(f"     - {item}")
            else:
                print(f"     无已下载模型")
        
    except ImportError:
        print("   transformers库未安装")
    
    # 2. 环境变量缓存目录
    print(f"\n2. 环境变量 TRANSFORMERS_CACHE:")
    env_cache = os.environ.get('TRANSFORMERS_CACHE')
    if env_cache:
        print(f"   {env_cache}")
        print(f"   是否存在: {os.path.exists(env_cache)}")
    else:
        print("   未设置")
    
    # 3. 环境变量 HF_HOME
    print(f"\n3. 环境变量 HF_HOME:")
    hf_home = os.environ.get('HF_HOME')
    if hf_home:
        print(f"   {hf_home}")
        print(f"   是否存在: {os.path.exists(hf_home)}")
    else:
        print("   未设置")
    
    # 4. 项目本地缓存目录
    print(f"\n4. 项目本地目录:")
    local_dirs = ['./models', './cache', './.cache']
    for dir_path in local_dirs:
        abs_path = os.path.abspath(dir_path)
        exists = os.path.exists(dir_path)
        print(f"   {dir_path} -> {abs_path}")
        print(f"   是否存在: {exists}")
        if exists:
            try:
                size = sum(os.path.getsize(os.path.join(root, file))
                          for root, dirs, files in os.walk(dir_path)
                          for file in files)
                print(f"   目录大小: {size / (1024**2):.1f} MB")
            except:
                print(f"   无法计算大小")

def show_cache_configuration_examples():
    """显示缓存配置示例"""
    print("\n=== 缓存配置方法 ===\n")
    
    print("方法1: 使用默认缓存目录（推荐）")
    print("```python")
    print("# 模型会下载到 ~/.cache/huggingface/hub/")
    print("agent.configure_response_parser(")
    print("    parser_method='transformer',")
    print("    parser_config={")
    print("        'model_name': 'hfl/chinese-bert-wwm-ext'")
    print("    }")
    print(")")
    print("```")
    
    print("\n方法2: 指定项目本地缓存目录")
    print("```python")
    print("# 模型会下载到 ./models/ 目录")
    print("agent.configure_response_parser(")
    print("    parser_method='transformer',")
    print("    parser_config={")
    print("        'model_name': 'hfl/chinese-bert-wwm-ext',")
    print("        'cache_dir': './models'")
    print("    }")
    print(")")
    print("```")
    
    print("\n方法3: 通过环境变量设置全局缓存")
    print("```bash")
    print("export TRANSFORMERS_CACHE=/path/to/your/cache")
    print("export HF_HOME=/path/to/your/huggingface")
    print("```")
    
    print("\n方法4: 在代码中动态设置")
    print("```python")
    print("import os")
    print("os.environ['TRANSFORMERS_CACHE'] = '/path/to/cache'")
    print("# 然后配置解析器")
    print("```")

def show_model_size_info():
    """显示模型大小信息"""
    print("\n=== 常用模型大小参考 ===\n")
    
    models_info = [
        ("hfl/chinese-bert-wwm-ext", "~400MB", "中文BERT模型，推荐"),
        ("bert-base-chinese", "~400MB", "标准中文BERT"),
        ("hfl/chinese-roberta-wwm-ext", "~400MB", "中文RoBERTa模型"),
        ("paraphrase-multilingual-MiniLM-L12-v2", "~120MB", "多语言轻量级模型"),
        ("sentence-transformers/paraphrase-MiniLM-L6-v2", "~80MB", "英文轻量级模型")
    ]
    
    for model_name, size, description in models_info:
        print(f"模型: {model_name}")
        print(f"大小: {size}")
        print(f"说明: {description}")
        print()

if __name__ == "__main__":
    check_model_cache_directories()
    show_cache_configuration_examples()
    show_model_size_info()
    
    print("💡 建议:")
    print("1. 如果磁盘空间充足，使用默认缓存目录（~/.cache/huggingface/）")
    print("2. 如果需要项目隔离，使用 cache_dir='./models' 参数")
    print("3. 首次下载需要良好的网络连接和代理配置")
    print("4. 模型文件较大，建议在WiFi环境下载载")