#!/usr/bin/env python3
"""
示例：使用Agent批量处理文件
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from python_core import Agent
from llm_lazy import get_model
from aider_knowledge import aider_knowledge

def create_sample_files():
    """创建示例文件用于批量处理"""
    # 创建src目录
    os.makedirs('src', exist_ok=True)
    
    # 创建几个示例Python文件
    sample_files = {
        'src/utils.py': '''
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

def find_max(items):
    if not items:
        return None
    max_val = items[0]
    for item in items[1:]:
        if item > max_val:
            max_val = item
    return max_val
''',
        'src/processor.py': '''
class DataProcessor:
    def __init__(self):
        self.data = []
    
    def add_data(self, item):
        self.data.append(item)
    
    def process(self):
        results = []
        for item in self.data:
            results.append(item * 2)
        return results
''',
        'src/helpers.py': '''
def format_string(text, upper):
    if upper:
        return text.upper()
    else:
        return text.lower()

def validate_email(email):
    return '@' in email and '.' in email
'''
    }
    
    for filename, content in sample_files.items():
        with open(filename, 'w') as f:
            f.write(content)
    
    print("✅ 创建了示例文件：", list(sample_files.keys()))

def main():
    # 初始化标准Agent
    llm = get_model('deepseek_v3')
    agent = Agent(llm=llm, stateful=True)
    
    # 注入aider知识
    agent.loadKnowledge(aider_knowledge)
    
    # 创建示例文件
    create_sample_files()
    
    # 指令：批量优化代码
    instruction = """
    请使用aider批量处理src目录下的所有Python文件，进行以下优化：
    1. 添加类型注解
    2. 优化代码结构
    3. 添加文档字符串
    使用deepseek模型，设置适当的token限制
    """
    
    print("\n📦 开始批量处理文件...")
    result = agent.execute_sync(instruction)
    print(f"批量处理结果: {result.return_value}")

if __name__ == '__main__':
    main()