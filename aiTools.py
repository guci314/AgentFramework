from googleapiclient.discovery import build
from typing import Any, Dict,List
import requests
from bs4 import BeautifulSoup
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from llm_lazy import get_modelnv()  # 加载 .env 文件中的环境变量

# 设置代理服务器
proxy_server = "http://127.0.0.1:7890"
os.environ['http_proxy'] = proxy_server
os.environ['https_proxy'] = proxy_server


# 实例化gemini语言模型的代码
llm_gemini_2_flash_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.0-flash-001", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'))

def llm_openrouter(model: str = "openrouter/meta-llama/llama-4-maverick") -> ChatOpenAI:
    """返回配置好的OpenRouter语言模型实例
    
    Args:
        model: 要使用的模型名称，默认为llama-4-maverick
        
    Returns:
        ChatOpenAI实例
    """
    return ChatOpenAI(
        temperature=0,
        model=model,
        base_url='https://openrouter.ai/api/v1',
        api_key=os.getenv('OPENROUTER_API_KEY')
)



def search(query:str,site:str=None, **kwargs)->List[Dict[str, str]]:
    '''
    谷歌搜索
    :param query:搜索关键词
    :param site:搜索网站
    可选的kwargs:
    num: 搜索结果数量
    返回值:搜索结果字典列表，字典格式为
    {
        "title": "xxx",
        "link": "xxx"
    }
    
    '''
    api_key = os.getenv('GOOGLE_API_KEY') 
    cse_id = os.getenv('GOOGLE_CSE_ID')
    service = build("customsearch", "v1", developerKey=api_key)
    if site:
        query=query+" site:"+site
    res=service.cse().list(q=query, cx=cse_id, **kwargs).execute()
    results=[]
    for item in res['items']:
        results.append({
            "title": item['title'],
            "link": item['link'],
            })
    return results


def readWebPage(url: str) -> str:
    '''
    读取网页内容，去掉html标签，JavaScript代码，保留纯文本
    :param url: 网页url
    :return: 网页纯文本内容，如果失败则返回None
    '''
    try:
        page = requests.get(url)
        page.encoding = page.apparent_encoding  # 自动判断编码
        soup = BeautifulSoup(page.text, 'html.parser')

        for script_or_style in soup(["script", "style"]):
            script_or_style.extract()

        text = soup.get_text()
        return text
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None
