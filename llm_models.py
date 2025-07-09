"""
语言模型定义模块

将所有语言模型定义集中在此文件中，与核心业务逻辑分离。
使用时按需导入，避免不必要的模型初始化。
"""

import os
import httpx
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建HTTP客户端
http_client = httpx.Client(
    proxy='socks5://127.0.0.1:7890',
    timeout=10,
    verify=False
)

# ============================================================================
# Gemini 系列模型
# ============================================================================

llm_gemini_2_flash_lite_google = ChatOpenAI(
    temperature=0,
    model="gemini-2.0-flash-lite-preview-02-05",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv('GEMINI_API_KEY'),
    http_client=http_client
)

llm_gemini_2_5_pro_exp_03_25_google = ChatOpenAI(
    temperature=0,
    model="gemini-2.5-pro-exp-03-25",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv('GEMINI_API_KEY'),
    http_client=http_client
)

llm_gemini_2_5_pro_preview_05_06_google = ChatOpenAI(
    temperature=0,
    model="gemini-2.5-pro-preview-05-06",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv('GEMINI_API_KEY'),
    http_client=http_client
)

llm_gemini_2_5_pro_preview_06_05_google = ChatOpenAI(
    temperature=0,
    model="gemini-2.5-pro-preview-06-05",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv('GEMINI_API_KEY'),
    http_client=http_client
)

llm_gemini_2_flash_google = ChatOpenAI(
    temperature=0,
    model="gemini-2.0-flash",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv('GEMINI_API_KEY'),
    max_tokens=4096,
    http_client=http_client
)

llm_gemini_2_5_flash_google = ChatOpenAI(
    temperature=0,
    model="models/gemini-2.5-flash",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv('GEMINI_API_KEY'),
    max_tokens=4096,
    http_client=http_client
)

llm_gemini_2_5_pro_google = ChatOpenAI(
    temperature=0,
    model="gemini-2.5-pro",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv('GEMINI_API_KEY'),
    max_tokens=4096,
    http_client=http_client
)

# ============================================================================
# DeepSeek 系列模型
# ============================================================================

llm_Qwen_QwQ_32B_siliconflow = ChatOpenAI(
    temperature=0,
    model="Qwen/QwQ-32B",
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv('SILICONFLOW_API_KEY'),
    max_tokens=8192
)

llm_DeepSeek_R1_Distill_Qwen_32B = ChatOpenAI(
    temperature=0,
    model="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv('SILICONFLOW_API_KEY'),
    max_tokens=8192
)

llm_DeepSeek_V3_siliconflow = ChatOpenAI(
    temperature=0,
    model="deepseek-ai/DeepSeek-V3",
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv('SILICONFLOW_API_KEY'),
    max_tokens=4096
)

llm_Pro_DeepSeek_V3_siliconflow = ChatOpenAI(
    temperature=0,
    model="Pro/deepseek-ai/DeepSeek-V3",
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv('SILICONFLOW_API_KEY'),
    max_tokens=4096
)

llm_DeepSeek_R1_siliconflow = ChatOpenAI(
    temperature=0,
    model="deepseek-ai/DeepSeek-R1",
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv('SILICONFLOW_API_KEY'),
    max_tokens=8192
)

llm_Pro_DeepSeek_R1_siliconflow = ChatOpenAI(
    temperature=0,
    model="Pro/deepseek-ai/DeepSeek-R1",
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv('SILICONFLOW_API_KEY'),
    max_tokens=8192
)

llm_Qwen_2_5_Coder_32B_Instruct_siliconflow = ChatOpenAI(
    temperature=0,
    model="Qwen/Qwen2.5-Coder-32B-Instruct",
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv('SILICONFLOW_API_KEY'),
    max_tokens=8192
)

llm_DeepSeek_R1_Distill_Qwen_32B_siliconflow = ChatOpenAI(
    temperature=0,
    model="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv('SILICONFLOW_API_KEY'),
    max_tokens=8192
)

llm_deepseek = ChatOpenAI(
    temperature=0,
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    max_tokens=8192
)

llm_deepseek_r1 = ChatOpenAI(
    temperature=0.6,
    model="deepseek-reasoner",
    base_url="https://api.deepseek.com",
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    max_tokens=8192
)

# ============================================================================
# OpenRouter 系列模型
# ============================================================================

llm_qwen_2_5_72b_instruct = ChatOpenAI(
    temperature=0,
    model="qwen/qwen-2.5-72b-instruct",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_gpt_4o_mini_openrouter = ChatOpenAI(
    temperature=0,
    model="openai/gpt-4o-mini",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_gemini_2_5_flash_preview_thinking_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.5-flash-preview:thinking",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_gemini_2_5_flash_preview_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.5-flash-preview",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_gemini_2_5_pro_exp_03_25_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.5-pro-exp-03-25:free",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_llama_4_scout_openrouter = ChatOpenAI(
    temperature=0,
    model="meta-llama/llama-4-scout",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_llama_4_maverick_openrouter = ChatOpenAI(
    temperature=0,
    model="meta-llama/llama-4-maverick",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_qwen_2_5_coder_32b_instruct = ChatOpenAI(
    temperature=0,
    model="qwen/qwen-2.5-coder-32b-instruct",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_qwq_32b = ChatOpenAI(
    temperature=0,
    model="qwen/qwq-32b",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_claude_35_sonnet = ChatOpenAI(
    temperature=0,
    model="anthropic/claude-3.5-sonnet:beta",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_claude_37_sonnet = ChatOpenAI(
    temperature=0,
    model="anthropic/claude-3.7-sonnet",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_claude_sonnet_4 = ChatOpenAI(
    temperature=0,
    model="anthropic/claude-sonnet-4",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_deepseek_r1_free_openrouter = ChatOpenAI(
    temperature=0,
    model="deepseek/deepseek-r1:free",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_claude_37_sonnet_thinking = ChatOpenAI(
    temperature=0,
    model="anthropic/claude-3.7-sonnet:thinking",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_o3_mini = ChatOpenAI(
    temperature=0,
    model="openai/o3-mini",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_gemini_2_flash_thinking_exp_free_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.0-flash-thinking-exp:free",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_gemini_2_flash_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.0-flash-001",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_gemini_2_flash_lite_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.0-flash-lite-preview-02-05:free",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_deepseek_openrouter = ChatOpenAI(
    temperature=0,
    model="deepseek/deepseek-chat-v3-0324:NovitaAI",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_deepseek_r1_openrouter = ChatOpenAI(
    temperature=0,
    model="deepseek/deepseek-r1",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_optimus_alpha_openrouter = ChatOpenAI(
    temperature=0,
    model="openrouter/optimus-alpha",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

# ============================================================================
# 懒加载支持
# ============================================================================

# 模型映射表
MODEL_MAPPING = {
    # Gemini 系列
    'gemini_2_5_flash': 'llm_gemini_2_5_flash_google',
    'gemini_2_5_pro': 'llm_gemini_2_5_pro_google',
    'gemini_2_flash': 'llm_gemini_2_flash_google',
    'gemini_2_flash_lite': 'llm_gemini_2_flash_lite_google',
    
    # DeepSeek 系列  
    'deepseek_v3': 'llm_DeepSeek_V3_siliconflow',
    'deepseek_r1': 'llm_DeepSeek_R1_siliconflow',
    'deepseek_chat': 'llm_deepseek',
    'deepseek_reasoner': 'llm_deepseek_r1',
    
    # Qwen 系列
    'qwen_qwq_32b': 'llm_Qwen_QwQ_32B_siliconflow',
    'qwen_2_5_coder_32b': 'llm_Qwen_2_5_Coder_32B_Instruct_siliconflow',
    'qwen_2_5_72b': 'llm_qwen_2_5_72b_instruct',
    
    # Claude 系列
    'claude_35_sonnet': 'llm_claude_35_sonnet',
    'claude_37_sonnet': 'llm_claude_37_sonnet',
    'claude_sonnet_4': 'llm_claude_sonnet_4',
    
    # OpenAI 系列
    'gpt_4o_mini': 'llm_gpt_4o_mini_openrouter',
    'o3_mini': 'llm_o3_mini',
}

from functools import lru_cache

@lru_cache(maxsize=None)
def get_model(model_name: str):
    """
    按需获取语言模型
    
    Args:
        model_name: 模型名称
        
    Returns:
        ChatOpenAI实例或None
    """
    if model_name in MODEL_MAPPING:
        attr_name = MODEL_MAPPING[model_name]
        return globals().get(attr_name)
    else:
        # 尝试直接按属性名获取
        return globals().get(model_name)

def list_models():
    """列出所有可用模型"""
    print("📋 可用模型列表:")
    for short_name, full_name in MODEL_MAPPING.items():
        print(f"  {short_name:20} -> {full_name}")

# 便捷访问函数
def get_default_model():
    """获取默认模型"""
    return get_model('gemini_2_5_flash')

def get_smart_model():
    """获取智能模型"""
    return get_model('gemini_2_5_pro')

def get_code_model():
    """获取代码模型"""
    return get_model('deepseek_v3')

print("💡 语言模型已加载。使用 get_model('model_name') 获取特定模型。")