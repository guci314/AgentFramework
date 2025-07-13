from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
import json
import random
from typing import Dict, Any
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache
set_llm_cache(SQLiteCache(database_path=".langchain.db"))

# 导入 pythonTask 中的 Agent 类
from python_core import Agent, get_model("deepseek_chat")

# 设置HTTP代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

# 设置SOCKS代理（如果需要）
os.environ['SOCKS_PROXY'] = 'socks5://127.0.0.1:1080'

# 加载.env文件
load_dotenv()


# 1. 构造模拟的天气查询工具
@tool
def get_weather(city: str) -> Dict[str, Any]:
    """查询指定城市的天气信息
    
    Args:
        city: 要查询天气的城市名称
        
    Returns:
        包含天气信息的字典
    """
    # 模拟的天气数据
    weather_data = {
        "北京": {
            "temperature": random.randint(-5, 35),
            "condition": random.choice(["晴天", "多云", "阴天", "小雨", "大雨", "雪"]),
            "humidity": random.randint(20, 90),
            "wind_speed": random.randint(0, 50)
        },
        "上海": {
            "temperature": random.randint(0, 38),
            "condition": random.choice(["晴天", "多云", "阴天", "小雨", "大雨", "雷阵雨"]),
            "humidity": random.randint(40, 95),
            "wind_speed": random.randint(0, 40)
        },
        "广州": {
            "temperature": random.randint(10, 40),
            "condition": random.choice(["晴天", "多云", "阴天", "小雨", "大雨", "台风"]),
            "humidity": random.randint(50, 98),
            "wind_speed": random.randint(0, 60)
        },
        "深圳": {
            "temperature": random.randint(15, 38),
            "condition": random.choice(["晴天", "多云", "阴天", "小雨", "暴雨"]),
            "humidity": random.randint(55, 95),
            "wind_speed": random.randint(0, 45)
        },
        "成都": {
            "temperature": random.randint(5, 35),
            "condition": random.choice(["多云", "阴天", "小雨", "雾"]),
            "humidity": random.randint(60, 90),
            "wind_speed": random.randint(0, 20)
        }
    }
    
    # 获取城市天气，如果城市不在列表中，返回默认天气
    if city in weather_data:
        weather = weather_data[city]
    else:
        # 为未知城市生成随机天气
        weather = {
            "temperature": random.randint(0, 35),
            "condition": random.choice(["晴天", "多云", "阴天", "小雨"]),
            "humidity": random.randint(30, 80),
            "wind_speed": random.randint(0, 30)
        }
    
    return {
        "city": city,
        "temperature": weather["temperature"],
        "condition": weather["condition"],
        "humidity": weather["humidity"],
        "wind_speed": weather["wind_speed"],
        "unit": "摄氏度"
    }


@tool
def get_weather_forecast(city: str, days: int = 3) -> Dict[str, Any]:
    """获取指定城市未来几天的天气预报
    
    Args:
        city: 要查询天气的城市名称
        days: 预报天数，默认3天
        
    Returns:
        包含天气预报信息的字典
    """
    forecast = []
    conditions = ["晴天", "多云", "阴天", "小雨", "大雨", "雷阵雨"]
    
    for i in range(days):
        base_temp = random.randint(10, 30)
        forecast.append({
            "day": f"第{i+1}天",
            "high_temperature": base_temp + random.randint(5, 10),
            "low_temperature": base_temp - random.randint(0, 5),
            "condition": random.choice(conditions),
            "precipitation_probability": random.randint(0, 100)
        })
    
    return {
        "city": city,
        "forecast_days": days,
        "forecast": forecast
    }


# 3. 创建一个全局的 Agent 实例
# 使用 DeepSeek 模型创建 Agent
# 使用 skip_generation 和 skip_evaluation 以加快执行速度
python_agent = Agent(llm=get_model("deepseek_chat"), stateful=True, max_retries=1, skip_generation=True, skip_evaluation=False)


@tool
def execute_natural_language_command(command: str) -> str:
    """执行自然语言命令，可以进行计算、数据处理等任务
    
    Args:
        command: 要执行的自然语言命令，例如 "计算 123 + 456" 或 "生成一个包含5个随机数的列表"
        
    Returns:
        执行结果的字符串
    """
    try:
        # 使用 Agent 的 execute_sync 方法执行自然语言命令
        result = python_agent.execute_sync(command)
        
        # 当有实际代码执行时，返回执行结果
        if result.code and result.stdout:
            return result.stdout.strip()
        
        # 当 skip_generation=True 时，return_value 可能是嵌套的 Result 对象
        if result.return_value is not None:
            # 检查是否是嵌套的 Result 对象
            if hasattr(result.return_value, 'return_value'):
                # 这是 LLM 的文本回答，包含了计算过程
                return str(result.return_value.return_value)
            else:
                return str(result.return_value)
        
        # 处理错误
        if result.stderr:
            return f"错误: {result.stderr}"
        
        # 默认返回
        return "执行完成"
            
    except Exception as e:
        return f"执行失败: {str(e)}"


# 2. 使用DeepSeek语言模型演示function call
def demonstrate_deepseek_function_calling():
    """演示DeepSeek模型的function calling功能"""
    
    print("=== DeepSeek Function Calling 演示 ===\n")
    
    # 初始化DeepSeek模型
    get_model("deepseek_chat") = ChatOpenAI(
        temperature=0,
        model="deepseek-chat",  # 使用支持function calling的DeepSeek模型
        base_url="https://api.deepseek.com",
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        max_tokens=8192
    )
    
    # 创建工具列表
    tools = [get_weather, get_weather_forecast, execute_natural_language_command]
    
    # 创建prompt模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个智能助手，可以帮助用户查询天气信息和执行各种计算任务。请使用提供的工具来获取准确的数据或执行命令。"),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # 创建agent
    agent = create_tool_calling_agent(get_model("deepseek_chat"), tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    # 测试用例
    test_queries = [
        "北京今天天气怎么样？",
        "帮我计算 123 + 456 * 789",
        "生成一个包含10个1到100之间随机数的列表"
    ]
    
    # 执行演示
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 测试用例 {i} ---")
        print(f"用户查询: {query}")
        print("\n执行过程:")
        
        try:
            result = agent_executor.invoke({"input": query})
            print(f"\n最终回答: {result['output']}")
        except Exception as e:
            print(f"执行出错: {str(e)}")
        
        print("\n" + "="*50)


# 3. 直接使用工具绑定的方式（更简单的function calling方式）
def demonstrate_simple_function_calling():
    """演示更简单的function calling方式"""
    
    print("\n=== 简单DeepSeek Function Calling演示 ===\n")
    
    # 初始化DeepSeek模型并绑定工具
    get_model("deepseek_chat") = ChatOpenAI(
        temperature=0,
        model="deepseek-chat",
        base_url="https://api.deepseek.com",
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        max_tokens=8192
    ).bind_tools([get_weather, get_weather_forecast, execute_natural_language_command])
    
    # 测试查询用例
    test_queries = [
        "请查询北京的天气",
        "计算 123 + 456 * 789"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 测试用例 {i} ---")
        print(f"用户查询: {query}")
        
        # 重置消息历史
        messages = [HumanMessage(content=query)]
        
        # 调用模型
        response = get_model("deepseek_chat").invoke(messages)
        print(f"初始模型响应: {response.content}")
        
        # 如果模型返回了tool_calls，执行工具并让模型生成最终回答
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # 将初始响应添加到消息历史
            messages.append(response)
            
            # 执行所有工具调用
            for tool_call in response.tool_calls:
                print(f"\n工具调用: {tool_call['name']}")
                print(f"参数: {tool_call['args']}")
                
                # 执行工具
                if tool_call['name'] == 'get_weather':
                    result = get_weather.invoke(tool_call['args'])
                elif tool_call['name'] == 'get_weather_forecast':
                    result = get_weather_forecast.invoke(tool_call['args'])
                elif tool_call['name'] == 'execute_natural_language_command':
                    result = execute_natural_language_command.invoke(tool_call['args'])
                else:
                    result = {"error": "未知的工具调用"}
                
                # 根据工具类型处理结果
                if isinstance(result, str):
                    print(f"工具返回结果: {result}")
                    content = result
                else:
                    print(f"工具返回结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    content = json.dumps(result, ensure_ascii=False)
                
                # 将工具调用结果添加到消息历史
                tool_message = ToolMessage(
                    content=content,
                    tool_call_id=tool_call['id']
                )
                messages.append(tool_message)
            
            # 让模型根据工具调用结果生成最终回答
            print("\n=== 模型根据工具调用结果生成回答 ===")
            final_response = get_model("deepseek_chat").invoke(messages)
            print(f"最终回答: {final_response.content}")
        else:
            print("模型没有进行工具调用")
        
        print("\n" + "="*50)


if __name__ == "__main__":
    # 运行演示
    print("开始Function Calling演示...\n")
    
    # 只演示简单的function calling
    demonstrate_simple_function_calling()

     
    print("\n演示完成！")