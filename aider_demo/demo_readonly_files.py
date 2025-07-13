#!/usr/bin/env python3
"""
演示如何使用aider的只读文件功能
"""
import os
import sys

# 添加父目录到Python路径以导入Agent框架
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput

def demo_readonly_files():
    """演示只读文件的使用"""
    
    # 创建一些示例文件
    # 1. 创建配置文件（只读）
    config_content = """
# 数据库配置
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "myapp",
    "user": "dbuser",
    "password": "dbpass"
}

# API配置
API_BASE_URL = "https://api.example.com/v1"
API_KEY = "your-api-key-here"
"""
    
    with open("config.py", "w") as f:
        f.write(config_content)
    
    # 2. 创建常量文件（只读）
    constants_content = """
# 应用常量
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30
DEFAULT_PAGE_SIZE = 20
CACHE_TTL = 3600  # 1小时

# 状态码
STATUS_SUCCESS = 200
STATUS_NOT_FOUND = 404
STATUS_ERROR = 500
"""
    
    with open("constants.py", "w") as f:
        f.write(constants_content)
    
    # 3. 创建一个需要修改的主文件
    main_content = """
# 主应用文件
import requests

def get_data():
    # TODO: 使用配置文件中的设置
    url = "http://localhost:8080/api/data"
    response = requests.get(url, timeout=10)
    return response.json()

def process_data(data):
    # TODO: 使用常量文件中的设置
    max_items = 10
    return data[:max_items]

if __name__ == "__main__":
    data = get_data()
    processed = process_data(data)
    print(processed)
"""
    
    with open("main_app.py", "w") as f:
        f.write(main_content)
    
    print("创建了示例文件：config.py, constants.py, main_app.py")
    print("\n现在使用aider修改main_app.py，参考只读文件...")
    
    try:
        # 设置aider
        io = InputOutput(yes=True)
        model = Model("deepseek/deepseek-chat")
        
        # 创建Coder，指定可编辑文件和只读文件
        coder = Coder.create(
            main_model=model,
            fnames=["main_app.py"],  # 可编辑的文件
            read_only_fnames=["config.py", "constants.py"],  # 只读参考文件
            io=io,
            auto_commits=False,
            dirty_commits=False
        )
        
        # 执行修改
        print("\n第一步：更新API配置")
        coder.run("更新main_app.py中的get_data函数，使用config.py中的API_BASE_URL和TIMEOUT_SECONDS")
        
        print("\n第二步：更新常量")
        coder.run("更新main_app.py中的process_data函数，使用constants.py中的DEFAULT_PAGE_SIZE")
        
        print("\n第三步：添加错误处理")
        coder.run("为get_data函数添加错误处理，使用constants.py中的STATUS_码常量和MAX_RETRIES进行重试")
        
        print("\n修改完成！查看main_app.py的变化。")
        
    except Exception as e:
        print(f"\n错误：{e}")
        print("\n可能是aider未安装或API密钥未设置。")
        print("请确保：")
        print("1. pip install aider-chat")
        print("2. export DEEPSEEK_API_KEY=your-api-key")

if __name__ == "__main__":
    demo_readonly_files()