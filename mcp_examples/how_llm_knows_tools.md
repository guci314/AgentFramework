# 语言模型如何识别工具功能

当使用 `bind_tools()` 方法时，语言模型通过以下机制了解每个工具的功能：

## 1. @tool 装饰器的作用

`@tool` 装饰器会从函数中提取以下信息：

```python
@tool
def get_weather(city: str) -> Dict[str, Any]:
    """查询指定城市的天气信息
    
    Args:
        city: 要查询天气的城市名称
        
    Returns:
        包含天气信息的字典
    """
    # 函数实现...
```

装饰器会提取：
- **函数名称**: `get_weather` - 作为工具的唯一标识符
- **函数文档字符串**: 整个 docstring 作为工具的描述
- **函数签名**: 参数类型和名称

## 2. 工具信息的结构化

工具信息被转换为 OpenAI Function Calling 格式：

```json
{
  "name": "get_weather",
  "description": "查询指定城市的天气信息\n\n    Args:\n        city: 要查询天气的城市名称\n\n    Returns:\n        包含天气信息的字典",
  "parameters": {
    "type": "object",
    "properties": {
      "city": {
        "type": "string"
      }
    },
    "required": ["city"]
  }
}
```

## 3. bind_tools() 的工作流程

```python
llm_with_tools = llm.bind_tools([get_weather, get_weather_forecast, execute_natural_language_command])
```

当调用 `bind_tools()` 时：

1. 每个工具被转换为标准的 function 定义
2. 这些定义被添加到 API 请求的 `tools` 参数中
3. 语言模型接收到这些工具定义，了解：
   - 可用的工具名称
   - 每个工具的功能描述
   - 需要的参数和参数类型

## 4. 实际的 API 请求

当你调用绑定了工具的模型时，实际发送给 API 的请求类似于：

```json
{
  "messages": [
    {"role": "user", "content": "北京天气怎么样？"}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "查询指定城市的天气信息...",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {"type": "string"}
          },
          "required": ["city"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

## 5. 语言模型的决策过程

语言模型基于以下信息决定使用哪个工具：

1. **用户查询内容**: "北京天气怎么样？"
2. **可用工具列表**: 
   - `get_weather`: "查询指定城市的天气信息"
   - `get_weather_forecast`: "获取指定城市未来几天的天气预报"
   - `execute_natural_language_command`: "执行自然语言命令，可以进行计算、数据处理等任务"

3. **匹配过程**:
   - 模型识别出"北京"是城市名
   - "天气"匹配到 `get_weather` 工具的描述
   - 决定调用 `get_weather` 并传入参数 `{"city": "北京"}`

## 6. 最佳实践

为了让语言模型更好地理解工具功能：

1. **清晰的函数名**: 使用描述性的名称，如 `get_weather` 而不是 `func1`

2. **详细的文档字符串**: 
   ```python
   """执行自然语言命令，可以进行计算、数据处理等任务
   
   Args:
       command: 要执行的自然语言命令，例如 "计算 123 + 456" 或 "生成一个包含5个随机数的列表"
       
   Returns:
       包含执行结果的字典
   """
   ```

3. **明确的参数类型**: 使用类型注解，如 `city: str`

4. **提供使用示例**: 在 docstring 中包含具体例子

## 7. 工具选择的影响因素

- **系统提示词**: 会影响模型的工具选择偏好
- **工具描述的清晰度**: 越清晰的描述，模型选择越准确
- **参数名称**: 有意义的参数名有助于模型理解
- **上下文**: 之前的对话历史会影响工具选择

这就是语言模型如何知道每个工具的功能并正确使用它们的完整机制。