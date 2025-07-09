"""
真正的懒加载语言模型模块

只在实际使用时才初始化模型，大幅提升导入速度。
"""

import os
from functools import lru_cache
from typing import Dict, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 模型配置字典（不包含实际的模型实例）
MODEL_CONFIGS = {
    # Gemini 系列
    'gemini_2_5_flash': {
        'model': 'models/gemini-2.5-flash',
        'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai/',
        'api_key_env': 'GEMINI_API_KEY',
        'max_tokens': 4096,
        'temperature': 0
    },
    'gemini_2_5_pro': {
        'model': 'gemini-2.5-pro',
        'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai/',
        'api_key_env': 'GEMINI_API_KEY',
        'max_tokens': 4096,
        'temperature': 0
    },
    'gemini_2_flash': {
        'model': 'gemini-2.0-flash',
        'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai/',
        'api_key_env': 'GEMINI_API_KEY',
        'max_tokens': 4096,
        'temperature': 0
    },
    'gemini_2_flash_lite': {
        'model': 'gemini-2.0-flash-lite-preview-02-05',
        'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai/',
        'api_key_env': 'GEMINI_API_KEY',
        'max_tokens': 4096,
        'temperature': 0
    },
    
    # DeepSeek 系列
    'deepseek_v3': {
        'model': 'deepseek-ai/DeepSeek-V3',
        'base_url': 'https://api.siliconflow.cn/v1',
        'api_key_env': 'SILICONFLOW_API_KEY',
        'max_tokens': 4096,
        'temperature': 0
    },
    'deepseek_r1': {
        'model': 'deepseek-ai/DeepSeek-R1',
        'base_url': 'https://api.siliconflow.cn/v1',
        'api_key_env': 'SILICONFLOW_API_KEY',
        'max_tokens': 8192,
        'temperature': 0
    },
    'deepseek_chat': {
        'model': 'deepseek-chat',
        'base_url': 'https://api.deepseek.com',
        'api_key_env': 'DEEPSEEK_API_KEY',
        'max_tokens': 8192,
        'temperature': 0
    },
    'deepseek_reasoner': {
        'model': 'deepseek-reasoner',
        'base_url': 'https://api.deepseek.com',
        'api_key_env': 'DEEPSEEK_API_KEY',
        'max_tokens': 8192,
        'temperature': 0.6
    },
    
    # Qwen 系列
    'qwen_qwq_32b': {
        'model': 'Qwen/QwQ-32B',
        'base_url': 'https://api.siliconflow.cn/v1',
        'api_key_env': 'SILICONFLOW_API_KEY',
        'max_tokens': 8192,
        'temperature': 0
    },
    'qwen_2_5_coder_32b': {
        'model': 'Qwen/Qwen2.5-Coder-32B-Instruct',
        'base_url': 'https://api.siliconflow.cn/v1',
        'api_key_env': 'SILICONFLOW_API_KEY',
        'max_tokens': 8192,
        'temperature': 0
    },
    'qwen_2_5_72b': {
        'model': 'qwen/qwen-2.5-72b-instruct',
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key_env': 'OPENROUTER_API_KEY',
        'max_tokens': 4096,
        'temperature': 0
    },
    
    # Claude 系列
    'claude_35_sonnet': {
        'model': 'anthropic/claude-3.5-sonnet:beta',
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key_env': 'OPENROUTER_API_KEY',
        'max_tokens': 4096,
        'temperature': 0
    },
    'claude_37_sonnet': {
        'model': 'anthropic/claude-3.7-sonnet',
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key_env': 'OPENROUTER_API_KEY',
        'max_tokens': 4096,
        'temperature': 0
    },
    'claude_sonnet_4': {
        'model': 'anthropic/claude-sonnet-4',
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key_env': 'OPENROUTER_API_KEY',
        'max_tokens': 4096,
        'temperature': 0
    },
    
    # OpenAI 系列
    'gpt_4o_mini': {
        'model': 'openai/gpt-4o-mini',
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key_env': 'OPENROUTER_API_KEY',
        'max_tokens': 4096,
        'temperature': 0
    },
    'o3_mini': {
        'model': 'openai/o3-mini',
        'base_url': 'https://openrouter.ai/api/v1',
        'api_key_env': 'OPENROUTER_API_KEY',
        'max_tokens': 4096,
        'temperature': 0
    }
}

# 创建HTTP客户端（懒加载）
_http_client = None

def _get_http_client():
    """懒加载HTTP客户端"""
    global _http_client
    if _http_client is None:
        try:
            import httpx
            _http_client = httpx.Client(
                proxy='socks5://127.0.0.1:7890',
                timeout=10,
                verify=False
            )
        except Exception:
            import httpx
            _http_client = httpx.Client(timeout=10, verify=False)
    return _http_client

@lru_cache(maxsize=None)
def get_model(model_name: str):
    """
    懒加载获取语言模型
    
    Args:
        model_name: 模型名称
        
    Returns:
        ChatOpenAI实例或None
    """
    if model_name not in MODEL_CONFIGS:
        available_models = ', '.join(MODEL_CONFIGS.keys())
        print(f"⚠️  未知模型名称: {model_name}")
        print(f"可用模型: {available_models}")
        return None
    
    config = MODEL_CONFIGS[model_name]
    api_key = os.getenv(config['api_key_env'])
    
    if not api_key:
        print(f"⚠️  缺少API密钥环境变量: {config['api_key_env']}")
        return None
    
    try:
        # 只在需要时才导入ChatOpenAI
        from langchain_openai import ChatOpenAI
        
        model = ChatOpenAI(
            temperature=config.get('temperature', 0),
            model=config['model'],
            base_url=config['base_url'],
            api_key=api_key,
            max_tokens=config.get('max_tokens', 4096),
            http_client=_get_http_client()
        )
        print(f"✅ 成功加载模型: {model_name}")
        return model
    except Exception as e:
        print(f"❌ 加载模型失败 {model_name}: {e}")
        return None

def list_models():
    """列出所有可用模型"""
    print("📋 可用模型列表:")
    for name, config in MODEL_CONFIGS.items():
        print(f"  {name:20} -> {config['model']}")
    return MODEL_CONFIGS

# 便捷访问函数
def get_default():
    """获取默认模型（Gemini 2.5 Flash）"""
    return get_model('gemini_2_5_flash')

def get_smart():
    """获取智能模型（Gemini 2.5 Pro）"""
    return get_model('gemini_2_5_pro')

def get_coder():
    """获取代码模型（DeepSeek V3）"""
    return get_model('deepseek_v3')

def get_reasoner():
    """获取推理模型（Qwen QwQ 32B）"""
    return get_model('qwen_qwq_32b')

# 兼容性映射（对应原pythonTask中的变量名）
COMPATIBILITY_MAPPING = {
    'llm_gemini_2_5_flash_google': 'gemini_2_5_flash',
    'llm_gemini_2_5_pro_google': 'gemini_2_5_pro',
    'llm_gemini_2_flash_google': 'gemini_2_flash',
    'llm_DeepSeek_V3_siliconflow': 'deepseek_v3',
    'llm_DeepSeek_R1_siliconflow': 'deepseek_r1',
    'llm_deepseek': 'deepseek_chat',
    'llm_deepseek_r1': 'deepseek_reasoner',
    'llm_Qwen_QwQ_32B_siliconflow': 'qwen_qwq_32b',
}

def get_model_by_old_name(old_name: str):
    """通过原pythonTask中的变量名获取模型"""
    if old_name in COMPATIBILITY_MAPPING:
        return get_model(COMPATIBILITY_MAPPING[old_name])
    else:
        print(f"⚠️  未知的旧模型名称: {old_name}")
        return None

def demo_lazy_loading():
    """演示懒加载的性能优势"""
    import time
    print("🚀 真正的懒加载语言模型演示")
    print("=" * 50)
    
    print("📋 可用模型:")
    list_models()
    
    print("\n⚡ 性能测试:")
    
    # 测试懒加载性能
    start_time = time.time()
    llm1 = get_model('gemini_2_5_flash')
    first_load_time = time.time() - start_time
    
    start_time = time.time()
    llm2 = get_model('gemini_2_5_flash')  # 第二次访问，使用缓存
    cached_load_time = time.time() - start_time
    
    print(f"首次加载耗时: {first_load_time:.3f}s")
    print(f"缓存加载耗时: {cached_load_time:.6f}s")
    if cached_load_time > 0:
        print(f"缓存性能提升: {first_load_time/cached_load_time:.0f}x")
    
    print(f"✅ 模型对象相同: {llm1 is llm2}")
    
    print("\n💡 使用建议:")
    print("1. 快速导入: from llm_lazy import get_model")
    print("2. 按需获取: llm = get_model('gemini_2_5_flash')")
    print("3. 便捷函数: llm = get_default()")

print("💡 真正的懒加载模型模块已加载。使用 get_model('model_name') 按需获取模型。")