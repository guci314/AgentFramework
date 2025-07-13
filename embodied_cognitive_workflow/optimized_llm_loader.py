#!/usr/bin/env python3
"""
优化的语言模型加载器 - 解决\1加载缓慢问题

使用懒加载模式，只在实际使用时才初始化语言模型，
大幅提升模块导入速度。
"""

import os
from functools import lru_cache
from typing import Dict, Optional
import httpx
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置代理
try:
    http_client = httpx.Client(
        proxies="http://127.0.0.1:7890",
        timeout=60.0
    )
except Exception:
    # 如果代理配置失败，使用默认客户端
    http_client = httpx.Client(timeout=60.0)

class LLMLoader:
    """懒加载语言模型管理器"""
    
    def __init__(self):
        self._models: Dict[str, ChatOpenAI] = {}
        self._configs = {
            # Google Gemini 系列
            'gemini_2_5_flash': {
                'model': 'models/gemini-2.5-flash',
                'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai/',
                'api_key_env': 'GEMINI_API_KEY',
                'max_tokens': 4096
            },
            'gemini_2_5_pro': {
                'model': 'gemini-2.5-pro',
                'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai/',
                'api_key_env': 'GEMINI_API_KEY',
                'max_tokens': 4096
            },
            'gemini_2_flash': {
                'model': 'gemini-2.0-flash',
                'base_url': 'https://generativelanguage.googleapis.com/v1beta/openai/',
                'api_key_env': 'GEMINI_API_KEY',
                'max_tokens': 4096
            },
            
            # DeepSeek 系列
            'deepseek_v3': {
                'model': 'deepseek-ai/DeepSeek-V3',
                'base_url': 'https://api.siliconflow.cn/v1',
                'api_key_env': 'SILICONFLOW_API_KEY',
                'max_tokens': 4096
            },
            'deepseek_r1': {
                'model': 'deepseek-ai/DeepSeek-R1',
                'base_url': 'https://api.siliconflow.cn/v1',
                'api_key_env': 'SILICONFLOW_API_KEY',
                'max_tokens': 8192
            },
            'deepseek_chat': {
                'model': 'deepseek-chat',
                'base_url': 'https://api.deepseek.com/v1',
                'api_key_env': 'DEEPSEEK_API_KEY',
                'max_tokens': 4096
            },
            
            # Qwen 系列
            'qwen_qwq_32b': {
                'model': 'Qwen/QwQ-32B',
                'base_url': 'https://api.siliconflow.cn/v1',
                'api_key_env': 'SILICONFLOW_API_KEY',
                'max_tokens': 8192
            },
            'qwen_2_5_coder_32b': {
                'model': 'Qwen/Qwen2.5-Coder-32B-Instruct',
                'base_url': 'https://api.siliconflow.cn/v1',
                'api_key_env': 'SILICONFLOW_API_KEY',
                'max_tokens': 4096
            }
        }
    
    @lru_cache(maxsize=None)
    def get_model(self, model_name: str) -> Optional[ChatOpenAI]:
        """
        懒加载获取语言模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            ChatOpenAI实例，如果配置不存在或API密钥缺失则返回None
        """
        if model_name in self._models:
            return self._models[model_name]
        
        if model_name not in self._configs:
            print(f"⚠️  未知的模型名称: {model_name}")
            return None
        
        config = self._configs[model_name]
        api_key = os.getenv(config['api_key_env'])
        
        if not api_key:
            print(f"⚠️  缺少API密钥环境变量: {config['api_key_env']}")
            return None
        
        try:
            model = ChatOpenAI(
                temperature=0,
                model=config['model'],
                base_url=config['base_url'],
                api_key=api_key,
                max_tokens=config.get('max_tokens', 4096),
                http_client=http_client
            )
            self._models[model_name] = model
            print(f"✅ 成功加载模型: {model_name}")
            return model
        except Exception as e:
            print(f"❌ 加载模型失败 {model_name}: {e}")
            return None
    
    def list_available_models(self) -> Dict[str, str]:
        """列出所有可用的模型配置"""
        return {name: config['model'] for name, config in self._configs.items()}
    
    def clear_cache(self):
        """清空模型缓存"""
        self._models.clear()
        self.get_model.cache_clear()
        print("🗑️  模型缓存已清空")

# 全局懒加载管理器
_llm_loader = LLMLoader()

# 便捷访问函数
def get_llm(model_name: str) -> Optional[ChatOpenAI]:
    """获取语言模型的便捷函数"""
    return _llm_loader.get_model(model_name)

# 为了向后兼容，提供最常用的模型作为属性
@property
def get_model("gemini_2_5_flash")():
    """最常用的Gemini Flash模型"""
    return get_llm('gemini_2_5_flash')

@property  
def get_model("deepseek_chat")_v3():
    """DeepSeek V3模型"""
    return get_llm('deepseek_v3')

@property
def llm_qwen_qwq_32b():
    """Qwen QwQ 32B模型"""
    return get_llm('qwen_qwq_32b')

# 模块级别的便捷访问
def demo_optimized_loading():
    """演示优化的加载性能"""
    import time
    
    print("🚀 优化的语言模型加载演示")
    print("=" * 50)
    
    # 显示可用模型
    print("📋 可用模型列表:")
    for name, model_id in _llm_loader.list_available_models().items():
        print(f"  - {name}: {model_id}")
    
    print("\n⚡ 性能对比:")
    print("传统方式: 导入时立即初始化49个模型 → 慢")
    print("优化方式: 按需懒加载模型 → 快")
    
    print("\n🧪 测试懒加载:")
    start_time = time.time()
    
    # 第一次访问 - 需要初始化
    model1 = get_llm('gemini_2_5_flash')
    first_load_time = time.time() - start_time
    
    # 第二次访问 - 使用缓存
    start_time = time.time()
    model2 = get_llm('gemini_2_5_flash')
    cached_load_time = time.time() - start_time
    
    print(f"首次加载耗时: {first_load_time:.3f}s")
    print(f"缓存加载耗时: {cached_load_time:.6f}s")
    print(f"性能提升: {first_load_time/cached_load_time:.0f}x")
    
    print(f"\n✅ 模型对象相同: {model1 is model2}")
    print("🎯 结论: 懒加载大幅提升模块导入速度，同时保持功能完整性")

if __name__ == "__main__":
    demo_optimized_loading()