# 用户快速开始指南

## 功能概述

AI代理框架v2版本引入了两个重要的新功能：

### 🔄 全局状态管理
全局状态管理让您的工作流能够"记住"执行过程中的重要信息，为后续步骤提供上下文。这就像给工作流添加了"记忆"功能。

**主要优势:**
- **上下文感知**: 每个步骤都能了解之前发生了什么
- **智能决策**: 基于历史状态做出更好的执行选择
- **错误恢复**: 在出现问题时能够更好地恢复

### 🤖 AI驱动状态更新
AI状态更新器会自动分析工作流的执行情况，并生成易于理解的状态描述。不再需要手动跟踪复杂的执行状态。

**主要优势:**
- **自动化**: 无需手动更新状态信息
- **智能化**: AI理解执行结果并生成有意义的描述
- **可靠性**: 多重回退机制确保状态更新的稳定性

## 快速开始 - 全局状态管理

### 步骤1: 创建支持全局状态的工作流

```python
from enhancedAgent_v2 import EnhancedAgent

# 创建增强代理实例
agent = EnhancedAgent()

# 工作流会自动包含全局状态管理
workflow = [
    {
        "type": "python",
        "code": "print('开始数据处理任务')",
        "description": "初始化数据处理"
    },
    {
        "type": "python", 
        "code": "data = list(range(100))",
        "description": "生成测试数据"
    },
    {
        "type": "python",
        "code": "processed_data = [x * 2 for x in data]",
        "description": "处理数据"
    }
]
```

### 步骤2: 启用状态更新并执行工作流

```python
# 确保状态更新已启用（默认启用）
agent.workflow_state.enable_state_updates()

# 执行工作流
result = agent.execute_workflow(workflow)

# 查看当前全局状态
current_state = agent.workflow_state.get_global_state()
print(f"当前状态: {current_state}")
```

### 步骤3: 查看状态历史

```python
# 获取状态历史
history = agent.workflow_state.get_state_history(limit=5)

for entry in history:
    print(f"{entry.timestamp}: {entry.state_snapshot}")
    print(f"来源: {entry.source}")
    print("-" * 50)
```

### 步骤4: 手动更新状态（可选）

```python
# 在关键节点手动设置状态
agent.workflow_state.set_global_state(
    "数据处理完成，准备进行下一阶段分析",
    source="manual"
)
```

## 快速开始 - AI状态更新器

### 步骤1: 配置AI状态更新器

首先确保您的配置文件包含必要的设置：

```yaml
# config.yaml
llm_deepseek:
  model: "deepseek-chat"
  api_base: "https://api.deepseek.com/v1"
  api_key: "your-deepseek-api-key"  # 或使用环境变量
  temperature: 0.6
  max_tokens: 8192
  timeout: 30

ai_state_updater:
  enabled: true
  update_frequency: "after_each_step"
```

### 步骤2: 设置环境变量

```bash
# 设置API密钥
export DEEPSEEK_API_KEY="your-deepseek-api-key"
```

### 步骤3: 创建AI增强的工作流

```python
from enhancedAgent_v2 import EnhancedAgent

# 创建代理实例
agent = EnhancedAgent()

# AI状态更新器会在每个步骤后自动运行
workflow = [
    {
        "type": "python",
        "code": """
import requests
import json

# 模拟API调用
try:
    # 这里是示例代码，实际使用时替换为真实API
    response = {"status": "success", "data": {"count": 150}}
    print(f"API调用成功，获得{response['data']['count']}条记录")
except Exception as e:
    print(f"API调用失败: {e}")
""",
        "description": "调用外部API获取数据"
    },
    {
        "type": "python",
        "code": """
# 数据验证
valid_records = 142
invalid_records = 8

print(f"数据验证完成：有效记录{valid_records}条，无效记录{invalid_records}条")

if invalid_records > 0:
    print("发现数据质量问题，需要进一步处理")
""",
        "description": "验证数据质量"
    }
]

# 执行工作流，AI会自动更新状态
result = agent.execute_workflow(workflow)
```

### 步骤4: 查看AI生成的状态

```python
# 查看最新的AI生成状态
current_state = agent.workflow_state.get_global_state()
print(f"AI生成的状态描述: {current_state}")

# 查看状态历史，了解AI如何描述每个步骤
history = agent.workflow_state.get_state_history()
for entry in history:
    if entry.source == "ai_updater":
        print(f"AI状态更新: {entry.state_snapshot}")
```

## 实际应用示例

### 示例1: 数据处理管道

```python
from enhancedAgent_v2 import EnhancedAgent

agent = EnhancedAgent()

# 数据处理工作流
data_pipeline = [
    {
        "type": "python",
        "code": """
# 模拟从数据库加载数据
import random
data_size = random.randint(1000, 5000)
print(f"从数据库加载了{data_size}条记录")
""",
        "description": "从数据库加载原始数据"
    },
    {
        "type": "python", 
        "code": """
# 数据清洗
import random
clean_rate = random.uniform(0.85, 0.95)
cleaned_records = int(data_size * clean_rate)
removed_records = data_size - cleaned_records

print(f"数据清洗完成：保留{cleaned_records}条，移除{removed_records}条无效记录")
""",
        "description": "执行数据清洗"
    },
    {
        "type": "python",
        "code": """
# 数据转换
processed_records = cleaned_records
print(f"数据转换完成，处理了{processed_records}条记录")

# 检查处理结果
if processed_records > 3000:
    print("数据量充足，可以进行高级分析")
else:
    print("数据量较少，建议使用基础分析方法")
""",
        "description": "执行数据转换和分析准备"
    }
]

# 执行工作流
result = agent.execute_workflow(data_pipeline)

# 查看AI生成的完整状态描述
print("\n=== AI状态更新历史 ===")
history = agent.workflow_state.get_state_history()
for i, entry in enumerate(history):
    if entry.source == "ai_updater":
        print(f"步骤{i+1}: {entry.state_snapshot}")
```

### 示例2: 错误处理和恢复

```python
# 包含错误处理的工作流
error_handling_workflow = [
    {
        "type": "python",
        "code": """
# 模拟可能失败的操作
import random

success_rate = 0.7  # 70%成功率
if random.random() < success_rate:
    print("操作成功：文件处理完成")
    operation_result = "success"
else:
    print("操作失败：文件损坏或不存在")
    operation_result = "failed"
    raise Exception("文件处理失败")
""",
        "description": "执行可能失败的文件操作"
    },
    {
        "type": "python",
        "code": """
# 错误恢复逻辑
if 'operation_result' in globals() and operation_result == "failed":
    print("启动错误恢复流程")
    print("尝试使用备份文件")
    operation_result = "recovered"
else:
    print("继续正常流程")
""",
        "description": "错误恢复处理"
    }
]

try:
    result = agent.execute_workflow(error_handling_workflow)
except Exception as e:
    print(f"工作流执行遇到问题: {e}")
    
# AI会智能地描述错误情况和恢复过程
current_state = agent.workflow_state.get_global_state()
print(f"\n最终状态: {current_state}")
```

## 高级功能

### 1. 自定义状态更新

```python
# 在特定条件下手动设置状态
def custom_state_check(agent):
    current_state = agent.workflow_state.get_global_state()
    
    if "错误" in current_state:
        agent.workflow_state.set_global_state(
            "检测到错误状态，已启动人工干预流程",
            source="custom_logic"
        )
```

### 2. 状态查询和分析

```python
# 分析状态历史趋势
def analyze_state_trend(agent):
    history = agent.workflow_state.get_state_history()
    
    error_count = sum(1 for entry in history if "错误" in entry.state_snapshot)
    success_count = sum(1 for entry in history if "成功" in entry.state_snapshot)
    
    print(f"错误状态次数: {error_count}")
    print(f"成功状态次数: {success_count}")
    print(f"成功率: {success_count / len(history) * 100:.1f}%")
```

### 3. 性能监控

```python
# 检查性能指标
def check_performance(agent):
    # 获取内存使用情况
    memory_info = agent.workflow_state.get_memory_usage()
    print(f"状态管理内存使用: {memory_info}")
    
    # 如果有AI状态更新器统计
    if hasattr(agent.workflow_state, '_ai_updater') and agent.workflow_state._ai_updater:
        stats = agent.workflow_state._ai_updater.get_update_statistics()
        print(f"AI更新统计: {stats}")
```

## 常见问题解答

### Q: 如何禁用AI状态更新？

```python
# 临时禁用状态更新
agent.workflow_state.disable_state_updates()

# 执行不需要状态跟踪的操作
agent.execute_workflow(simple_workflow)

# 重新启用
agent.workflow_state.enable_state_updates()
```

### Q: 如何查看详细的执行日志？

```python
import logging

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)

# 或者使用配置文件
# config.yaml中设置 log_level: DEBUG
```

### Q: 状态历史占用内存过多怎么办？

```python
# 清理状态历史
agent.workflow_state.clear_global_state()

# 或者调整历史大小限制
# 在config.yaml中设置 max_history_size: 25
```

### Q: AI状态更新不准确怎么办？

```python
# 手动设置更准确的状态
agent.workflow_state.set_global_state(
    "手动设置的准确状态描述",
    source="manual_correction"
)

# 或者在配置中调整AI模型参数
# config.yaml中调整 temperature 和 max_tokens
```

## 下一步

现在您已经掌握了基础用法，可以：

1. 查看[技术文档](./GLOBAL_STATE_ARCHITECTURE.md)了解更多细节
2. 阅读[配置指南](./CONFIGURATION_OPTIMIZATION_GUIDE.md)进行性能优化
3. 参考[最佳实践指南](./BEST_PRACTICES_TROUBLESHOOTING.md)设计更好的工作流
4. 查看项目中的示例代码获取更多灵感

## 支持和帮助

如果遇到问题，请：

1. 查看[故障排除指南](./BEST_PRACTICES_TROUBLESHOOTING.md)
2. 检查日志文件中的错误信息
3. 使用性能监控工具诊断问题
4. 参考项目文档或联系技术支持
