agent_api = """
# Agent 智能代理 API 文档

## 概述

Agent 是一个智能代理 能够将自然语言指令转换为可执行的 Python 代码。它执行完整的理解-编写-执行-评估-生成流程:
1. 理解用户指令
2. 编写符合要求的代码
3. 执行代码并获取结果
4. 评估执行结果是否满足要求
5. 生成人类可理解的最终回复

Agent 支持同步和流式两种执行模式 以及纯对话模式。

## 核心组件

### Result 类
```python
from pythonTask import Result

class Result:
    success: bool       # 执行是否成功
    code: str           # 执行的代码
    stdout: str         # 执行的标准输出
    stderr: str         # 执行的标准错误
    return_value: str   # 执行的返回值
```

Result 对象包含代码执行的完整结果 包括是否成功 代码内容 标准输出 标准错误和返回值。

### Agent 类初始化
```python
from pythonTask import Agent
from langchain_core.language_models import BaseChatModel
from typing import List

Agent(
    llm: BaseChatModel,                          # 主要语言模型
    stateful: bool = False,                      # 是否使用有状态执行器
    evaluate_llm: BaseChatModel = None,          # 用于评估的语言模型（默认与主模型相同）
    max_retries: int = 10,                       # 最大尝试次数
    skip_evaluation: bool = False,               # 是否跳过评估步骤
    skip_generation: bool = False,               # 是否跳过最终结果生成步骤
    thinker_system_message: str = None,          # 代码生成器的系统消息
    evaluation_system_messages: List[str] = None, # 评估器的系统消息列表
    thinker_chat_system_message: str = None      # 代码生成器聊天模式的系统消息
)
```

## 主要功能

### 执行指令,生成代码完成任务
- execute_sync(instruction: str) -> Result
- execute_stream(instruction: str) -> Iterator[object]
execute_stream方法执行时，会返回一个迭代器，迭代器前面返回一个字符串，字符串是代码执行的中间结果。迭代器最后一个元素是一个Result对象，Result对象是代码执行的最终结果。
#### 示例代码
agent=pythonTask.Agent(llm=llm_gemini_2_flash_openrouter,stateful=True)
prompt='''
写个函数计算斐波那契数列的第n个数,返回斐波那契数列的第10个数
'''
response=agent.execute_stream(prompt)
result:Result=None
for chunk in response:
    print(chunk,end='',flush=True)
    result=chunk
    
print(f'success:{result.success}')
print(f'code:{result.code}')
print(f'return_value:{result.return_value}')
print(f'stderr:{result.stderr}')
print(f'stdout:{result.stdout}')

- chat_stream(message: str) -> Iterator[str]
chat_stream方法执行时，会返回一个迭代器，迭代器每次返回一个字符串，字符串是代码执行的中间结果。chat_stream只调用语言模型生成回复，不执行代码。
#### 示例代码
from pythonTask import Agent,llm_deepseek,llm_gemini_2_flash_openrouter
agent=Agent(llm=llm_deepseek,evaluate_llm=llm_gemini_2_flash_openrouter,stateful=True,max_retries=10)
response=agent.chat_stream('写个python教程')
content=''
for chunk in response:
    content+=chunk
    print(chunk,end='',flush=True)
    result=chunk
print(content)


### 评估系统管理
- evaluate_all(result: Result, instruction: str = None) -> Tuple[bool, List[str]]
- loadEvaluationSystemMessage(evaluationSystemMessage: str) -> int
- resetEvaluators(evaluationSystemMessage: str = None) -> None

### 知识加载
- loadKnowledge(knowledge: str) -> None
- loadPythonModules(pythonModules: List[str]) -> None

### 纯对话功能
- chat_stream(message: str) -> Iterator[str]
- chat_sync(message: str) -> str

## 使用注意事项

1. 执行模式: 同步执行适合简单任务 流式执行适合复杂任务
2. 有状态执行: 有状态执行器适合多步骤交互
3. 错误处理: 检查Result.success判断执行是否成功

## 示例

```python
from pythonTask import Agent,llm_gemini_2_flash_openrouter
agent=Agent(llm=llm_gemini_2_flash_openrouter,stateful=True)
prompt='''
打印斐波那契数列的第五个数
'''
response=agent.execute_stream(prompt)
for chunk in response:
    print(chunk,end='',flush=True)
    
response=agent.chat_sync('中国的首都在哪里？')
print(response)


```

# 创建gemini语言模型的代码
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
llm_gemini_2_flash_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.0-flash-001", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY',

    response_format={"type": "text"})
)

# 从语言模型的输出中提取代码或者patch

from autogen.code_utils import extract_code

Extract code from a text.

Args:
    text (str or List): The content to extract code from. The content can be
        a string or a list, as returned by standard GPT or multimodal GPT.
    pattern (str, optional): The regular expression pattern for finding the
        code block. Defaults to CODE_BLOCK_PATTERN.
    detect_single_line_code (bool, optional): Enable the new feature for
        extracting single line code. Defaults to False.

Returns:
    list: A list of tuples, each containing the language and the code.
        If there is no code block in the input text, the language would be "unknown".
        If there is code block but the language is not specified, the language would be "".

## 示例
multi_code_text = '''
JavaScript示例：
```javascript
function sum(a, b) { return a + b; }
```

Python示例：
```python
def multiply(a, b):
    return a * b
```

Shell命令：
```sh
echo "Hello"
'''

// 提取所有代码块
code_blocks = extract_code(multi_code_text)

// 获取第一个Python代码块.  patch的代码块的lang是diff，python的代码块的lang是python
first_python_code = next(
    (code for lang, code in code_blocks if lang == 'python'), 
    None
)

if first_python_code:
    print("提取到的Python代码：")
    print(first_python_code)
else:
    print("未找到Python代码块")
    
# patch文件格式
patch文件最后必须要有一个空行

"""

promgraming_knowledge = """
## 编程规则
代码中的多行注释必须是三个单引号包裹的注释。

## 知识
unittest单元测试的测试结果在stderr中。stdout中是测试过程中打印的数据

使用命令python test_cm.py运行单元测试,不要使用unittest.TestLoader()

## 如果指令要求你"阅读或理解[x]"，指令的含义是：
把[x]打印出来，系统会把[x]的内容反馈到你的记忆
    
## 从文本中提取python代码的方法
from autogen.code_utils import extract_code
python_code = extract_code(python_code)[0][1]

## 调用语言模型示例
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
llm_gemini_2_flash_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.0-flash-001", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY')
)
x:str=llm_gemini_2_flash_openrouter.invoke("你好").content
print(x)

## 调用语言模型从文本中提取数据以json格式返回
import json
from pythonTask import llm_gemini_2_flash_openrouter
from autogen.code_utils import extract_code

# 构建提示 要求输出JSON格式
prompt = "请分析以下文本 判断其情感是积极还是消极 并以JSON格式返回结果。json有两个个字段，分别是sentiment,confidence。文本 '我今天非常开心'"

# 使用response_format参数指定返回JSON
response = llm_gemini_2_flash_openrouter.invoke(
    prompt,
    response_format={
        'type': 'json_object'
    }
)

json_str=extract_code(response.content)[0][1]

# 解析JSON响应
result = json.loads(json_str)
print(result)

# 可以直接访问JSON中的字段
sentiment = result.get("sentiment")
confidence = result.get("confidence", 0)
print(f"情感: {sentiment}, 置信度: {confidence}")

"""

aider_knowledge = """
## 编程任务示例代码
import aider_demo.aider_programming_demo
instruction = "在test_example.py中添加add函数测试用例" # 编程指令
edit_file_names=["/home/guci/myModule/AiResearch/aider_demo/test_example.py"] # 要编辑的文件列表
read_only_files=["/home/guci/myModule/AiResearch/aider_demo/example.py"] # 只读文件列表，只读文件不会被修改，是要编辑的文件依赖的文件
result=aider_demo.aider_programming_demo.programming(instruction,edit_file_names,read_only_files) # 执行编程任务
print(result) # 打印编程任务结果

## 如果指令是修改python文件，必须使用aider_demo.aider_programming_demo.programming函数执行编程任务修改python文件
"""
