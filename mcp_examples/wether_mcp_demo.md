# 任务描述

1:写个模拟的天气查询mcp工具
2：写个demo使用claude sonnet语言模型调用天气查询mcp

# context

claude sonnet语言模型：

import os
from dotenv import load_dotenv
load_dotenv()
import httpx

# 设置代理服务器环境变量
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'


from langchain_openai import ChatOpenAI
llm_claude_sonnet_4 = ChatOpenAI(
    temperature=0,
    model="anthropic/claude-sonnet-4", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)