#!/usr/bin/env python3
"""
简化版：使用Agent创建算术解释器
"""
import os
import sys

# 设置代理服务器
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890" 
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

# 添加父目录到Python路径以导入Agent框架
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Agent
from llm_lazy import get_model

# 创建标准Agent
llm = get_model('deepseek_chat')
agent = Agent(llm=llm, stateful=True)

# 简单的Claude Code知识
agent.loadKnowledge("""
编写Python代码时遵循以下原则：
1. 使用类型注解
2. 编写文档字符串
3. 妥善处理错误
4. 代码结构清晰
""")

if __name__ == "__main__":
    print("=== 创建算术解释器 ===\n")
    
    # 使用execute_sync直接执行，避免流式输出的问题
    result = agent.execute_sync("""
    创建一个算术解释器文件 arithmetic_interpreter.py，要求：
    1. 支持加减乘除和括号
    2. 有简单的词法分析和语法分析
    3. 包含错误处理
    4. 在文件底部添加测试代码：
       if __name__ == "__main__":
           print("Test: 2 + 3 * 4 =", interpret("2 + 3 * 4"))
           print("Test: (2 + 3) * 4 =", interpret("(2 + 3) * 4"))
    
    使用递归下降解析器实现。
    """)
    
    if result.success:
        print("\n✅ 算术解释器创建成功！")
        print(f"输出：{result.return_value[:200]}..." if len(result.return_value) > 200 else result.return_value)
        
        # 检查文件是否创建
        if os.path.exists("arithmetic_interpreter.py"):
            print("\n文件已创建：arithmetic_interpreter.py")
            print("\n运行测试：")
            os.system("python arithmetic_interpreter.py")
    else:
        print("\n❌ 创建失败")
        print(f"错误：{result.return_value}")