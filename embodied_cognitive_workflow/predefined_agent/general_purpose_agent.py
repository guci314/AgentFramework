#!/usr/bin/env python3
"""
通用目的智能体工厂方法

提供预定义的通用目的智能体实例创建功能。
该智能体包含各种实用的编程知识和最佳实践。
"""

import os
import sys
from typing import Optional

# 添加父目录到Python路径以导入核心模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from python_core import Agent
from llm_lazy import get_model

# 通用编程知识库
general_purpose_knowledge = """
# 通用编程知识库

## Python 单元测试输出流知识

### 🔥 重要：unittest 的输出流特性
**unittest 模块的测试结果输出在标准错误流（stderr）而不是标准输出流（stdout）！**

### 为什么这很重要？
- 捕获测试输出时必须使用 `stderr` 而不是 `stdout`
- 管道重定向时需要使用 `2>&1` 来合并输出流
- 在 subprocess 中运行测试时要设置 `capture_output=True` 或同时捕获 stdout 和 stderr

### 正确的测试运行方式
```python
import subprocess
import sys

# ❌ 错误：只捕获 stdout（看不到测试结果）
result = subprocess.run([sys.executable, '-m', 'unittest', 'test_module'], 
                       stdout=subprocess.PIPE, text=True)
print(result.stdout)  # 这里看不到测试结果！

# ✅ 正确：捕获 stderr
result = subprocess.run([sys.executable, '-m', 'unittest', 'test_module'], 
                       capture_output=True, text=True)
print("测试输出：")
print(result.stderr)  # 测试结果在这里！
print("返回码：", result.returncode)  # 0 表示测试通过

# ✅ 或者使用 pytest（输出在 stdout）
result = subprocess.run([sys.executable, '-m', 'pytest', 'test_module.py'], 
                       capture_output=True, text=True)
print(result.stdout)  # pytest 的输出在 stdout
```

### 命令行重定向
```bash
# 查看测试输出
python -m unittest test_module 2>&1

# 保存测试结果到文件
python -m unittest test_module 2> test_results.txt

# 同时显示和保存
python -m unittest test_module 2>&1 | tee test_results.txt
```

### unittest 的详细输出模式
```bash
# 普通模式（只显示点和错误）
python -m unittest test_module

# 详细模式（显示每个测试方法）
python -m unittest -v test_module

# 更详细的输出
python -m unittest -v test_module 2>&1
```

### 与其他测试框架的对比
| 测试框架 | 输出流 | 捕获方法 |
|---------|--------|----------|
| unittest | stderr | capture_output=True 或 stderr=PIPE |
| pytest | stdout | capture_output=True 或 stdout=PIPE |
| nose2 | stdout | capture_output=True 或 stdout=PIPE |
| doctest | stdout | capture_output=True 或 stdout=PIPE |

### 实际示例：运行测试并解析结果
```python
import subprocess
import sys
import re

def run_unittest_and_parse(test_module):
    '''运行 unittest 并解析测试结果'''
    # 运行测试
    result = subprocess.run(
        [sys.executable, '-m', 'unittest', '-v', test_module],
        capture_output=True,
        text=True
    )
    
    # 测试输出在 stderr
    output = result.stderr
    
    # 解析测试结果
    # 查找测试统计信息
    stats_match = re.search(r'Ran (\d+) tests? in ([\d.]+)s', output)
    if stats_match:
        test_count = int(stats_match.group(1))
        test_time = float(stats_match.group(2))
        print(f"运行了 {test_count} 个测试，耗时 {test_time:.3f} 秒")
    
    # 检查是否有失败
    if 'FAILED' in output:
        failures = re.findall(r'FAILED \(.*?(\d+).*?\)', output)
        print(f"测试失败！失败数: {failures[0] if failures else '未知'}")
    elif 'OK' in output:
        print("所有测试通过！")
    
    # 返回详细输出供进一步分析
    return {
        'success': result.returncode == 0,
        'output': output,
        'returncode': result.returncode
    }

# 使用示例
result = run_unittest_and_parse('test_my_module')
if not result['success']:
    print("测试失败的详细信息：")
    print(result['output'])
```

### 在 CI/CD 中处理 unittest 输出
```yaml
# GitHub Actions 示例
- name: Run Python tests
  run: |
    # 合并 stdout 和 stderr，确保看到所有输出
    python -m unittest discover -v 2>&1
    
# 或者分别保存
- name: Run tests with separate outputs
  run: |
    python -m unittest discover -v > stdout.log 2> stderr.log
    # 测试结果在 stderr.log 中
    cat stderr.log
```

### 调试提示
如果你发现运行 unittest 时"看不到输出"，请检查：
1. 是否只捕获了 stdout（应该捕获 stderr）
2. 是否使用了正确的重定向（2>&1 而不是 1>&2）
3. IDE 或编辑器是否正确配置了错误流显示
4. 是否使用了 `-v` 参数来获得详细输出

### 常见问题解答

**Q: 为什么 unittest 使用 stderr？**
A: unittest 的设计哲学是将测试结果视为"诊断信息"而非"程序输出"，因此使用 stderr。这样可以让被测试的程序正常使用 stdout。

**Q: 如何在 Python 代码中同时捕获 stdout 和 stderr？**
A: 使用 `capture_output=True` 或者分别设置 `stdout=PIPE, stderr=PIPE`。

**Q: 如何让 unittest 的输出显示在 stdout？**
A: 可以使用重定向：`python -m unittest 2>&1`，或者考虑使用 pytest，它默认输出到 stdout。

记住：**在处理 unittest 输出时，永远不要忘记它使用的是 stderr！**
"""

def create_general_purpose_agent(model_name: str = 'deepseek_chat', stateful: bool = True) -> Agent:
    """
    创建预配置的通用目的智能体
    
    Args:
        model_name (str): 语言模型名称，默认为 'deepseek_chat'
        stateful (bool): 是否使用有状态执行器，默认为 True
    
    Returns:
        Agent: 配置了通用编程知识的智能体实例
    
    Example:
        >>> agent = create_general_purpose_agent()
        >>> result = agent.execute_sync("如何正确捕获 unittest 的输出？")
        >>> print(result.return_value)
    """
    try:
        # 获取语言模型
        llm = get_model(model_name)
        if llm is None:
            raise ValueError(f"无法获取模型: {model_name}")
        
        # 创建智能体实例
        agent = Agent(llm=llm, stateful=stateful)
        
        # 注入通用编程知识
        agent.loadKnowledge(general_purpose_knowledge)
        
        # 设置智能体名称和API规范
        agent.set_agent_name("通用编程助手")
        agent.set_api_specification(
            "通用目的编程智能体，专门了解 unittest 输出流特性。"
            "知道 unittest 的测试结果输出在 stderr 而不是 stdout。"
        )
        
        print(f"✅ 成功创建通用目的智能体 (模型: {model_name})")
        return agent
        
    except Exception as e:
        print(f"❌ 创建通用目的智能体失败: {e}")
        raise

def test_general_purpose_agent():
    """测试通用目的智能体功能"""
    print("=== 测试通用目的智能体 ===\n")
    
    try:
        # 创建智能体
        agent = create_general_purpose_agent()
        
        # 测试关于 unittest 输出流的问题
        test_questions = [
            "为什么我运行 unittest 时看不到测试结果？",
            "如何正确捕获 unittest 的测试输出？",
            "写一个示例展示如何在 subprocess 中运行 unittest 并捕获输出"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n测试问题 {i}: {question}")
            print("-" * 50)
            
            result = agent.chat_sync(question)
            
            if result.success:
                print(f"回答：\n{result.return_value}")
            else:
                print(f"执行失败：{result.stderr}")
            
            print("-" * 50)
        
    except Exception as e:
        print(f"测试失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    # 设置代理环境变量
    os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
    os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890" 
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    
    # 运行测试
    test_general_purpose_agent()