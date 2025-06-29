# 基于产生式规则的Agent包装器 - 使用示例

## 📋 快速开始

### 基础使用

```python
from pythonTask import Agent, llm_deepseek
from CognitiveWorkflow.cognitive_workflow_rule_base.cognitive_workflow_agent_wrapper import CognitiveAgent

# 1. 创建基础Agent
base_agent = Agent(llm=llm_deepseek)

# 2. 包装成认知Agent
cognitive_agent = CognitiveAgent(
    base_agent=base_agent,
    enable_auto_recovery=True,
    classification_cache_size=100
)

# 3. 智能执行指令
result = cognitive_agent.execute_instruction_syn("什么是机器学习？")
print(result)
```

## 🧠 智能指令分类演示

### 手动分类测试

```python
# 测试不同类型的指令分类
test_instructions = [
    "什么是Python？",               # 信息性指令
    "解释装饰器的工作原理",          # 信息性指令  
    "打印hello world",             # 单步骤执行指令
    "计算1+1",                     # 单步骤执行指令
    "开发一个Web应用",              # 多步骤执行指令
    "创建包含测试的计算器程序"       # 多步骤执行指令
]

for instruction in test_instructions:
    instruction_type, execution_mode = cognitive_agent.classify_instruction(instruction)
    print(f"指令: '{instruction}'")
    print(f"分类: {instruction_type} | {execution_mode}")
    print()
```

**预期输出：**
```
指令: '什么是Python？'
分类: informational | chat

指令: '解释装饰器的工作原理'  
分类: informational | chat

指令: '打印hello world'
分类: executable | single_step

指令: '计算1+1'
分类: executable | single_step

指令: '开发一个Web应用'
分类: executable | multi_step

指令: '创建包含测试的计算器程序'
分类: executable | multi_step
```

## ⚡ 同步执行示例

### 智能路由执行

```python
# 自动路由到最适合的执行方式
results = {}

# 信息性指令 → chat_sync
results['chat'] = cognitive_agent.execute_instruction_syn("什么是RESTful API？")

# 单步骤指令 → execute_sync  
results['execute'] = cognitive_agent.execute_instruction_syn("显示当前时间")

# 多步骤指令 → 认知工作流
results['workflow'] = cognitive_agent.execute_instruction_syn("开发一个简单的博客系统")

# 查看不同类型的返回结果
for exec_type, result in results.items():
    print(f"{exec_type}结果类型: {type(result).__name__}")
    if hasattr(result, 'return_value'):
        print(f"返回值: {result.return_value}")
    elif hasattr(result, 'final_message'):
        print(f"最终消息: {result.final_message}")
    else:
        print(f"结果: {str(result)[:100]}...")
    print()
```

### 结果类型说明

```python
# 不同执行方式返回不同类型的结果对象

# 1. 信息性指令 (chat_sync)
chat_result = cognitive_agent.execute_instruction_syn("解释Python GIL")
print(f"Chat结果: {type(chat_result)}")  # 通常是字符串

# 2. 单步骤指令 (execute_sync)
exec_result = cognitive_agent.execute_instruction_syn("计算2+2")
print(f"执行结果: {type(exec_result)}")  # Result对象
print(f"返回值: {exec_result.return_value}")

# 3. 多步骤指令 (认知工作流)
workflow_result = cognitive_agent.execute_instruction_syn("创建用户管理系统")
print(f"工作流结果: {type(workflow_result)}")  # WorkflowExecutionResult对象
print(f"是否成功: {workflow_result.is_successful}")
print(f"执行步骤: {workflow_result.total_iterations}")
```

## 🔄 流式执行示例

### 实时流式处理

```python
# 流式执行 - 获取实时进度
def stream_execution_demo(instruction):
    print(f"🎯 流式执行: {instruction}")
    print("-" * 50)
    
    results = []
    for update in cognitive_agent.execute_instruction_stream(instruction):
        results.append(update)
        
        # 判断是否为过程信息
        if isinstance(update, str):
            print(f"📝 过程: {update}")
        else:
            print(f"✅ 最终结果: {type(update).__name__}")
    
    return results

# 测试不同类型的流式执行
stream_execution_demo("什么是Docker容器？")        # 信息性
stream_execution_demo("列出当前目录文件")           # 单步骤
stream_execution_demo("设计一个任务管理应用")       # 多步骤
```

### 流式结果处理模式

```python
# 模式1: 分离过程和结果
def process_stream_results(instruction):
    stream_iterator = cognitive_agent.execute_instruction_stream(instruction)
    *process_updates, final_result = stream_iterator
    
    print("📊 执行过程:")
    for i, update in enumerate(process_updates):
        print(f"  {i+1}. {update}")
    
    print(f"\n🎯 最终结果:")
    print(f"  类型: {type(final_result).__name__}")
    return final_result

# 模式2: 实时处理
def real_time_stream(instruction):
    for update in cognitive_agent.execute_instruction_stream(instruction):
        if isinstance(update, str):
            print(update, flush=True)  # 实时显示过程
        else:
            return update  # 返回最终结果

# 使用示例
result1 = process_stream_results("解释微服务架构优缺点")
result2 = real_time_stream("创建数据分析脚本")
```

## 📊 性能监控和优化

### 性能统计查看

```python
# 获取详细的性能统计
stats = cognitive_agent.get_performance_stats()

print("📈 性能统计报告")
print("=" * 40)

# 分类统计
print(f"🔍 分类统计:")
print(f"  总分类次数: {stats['classification_stats']['total_classifications']}")
print(f"  缓存命中: {stats['classification_stats']['cache_hits']}")
print(f"  分类错误: {stats['classification_stats']['classification_errors']}")

# 缓存效率
print(f"\n💾 缓存效率:")
print(f"  缓存大小: {stats['cache_info']['size']}/{stats['cache_info']['max_size']}")
print(f"  命中率: {stats['cache_info']['hit_rate_percent']}%")

# 执行分布
print(f"\n⚡ 执行方式分布:")
for mode, percentage in stats['execution_distribution'].items():
    print(f"  {mode}: {percentage:.1f}%")

# 系统状态
engine_status = "🟢 正常" if stats['workflow_engine_status'] else "🔴 异常"
print(f"\n🔧 工作流引擎: {engine_status}")
```

### 缓存和统计管理

```python
# 缓存管理
print(f"当前缓存大小: {len(cognitive_agent._classification_cache)}")

# 清空缓存
cognitive_agent.clear_cache()
print("缓存已清空")

# 重置统计
cognitive_agent.reset_stats()
print("统计已重置")

# 查看包装器状态
print(f"包装器状态: {cognitive_agent}")
```

## 🎭 实际应用场景

### 场景1: 编程学习助手

```python
def programming_tutor_demo():
    """编程学习助手演示"""
    
    learning_queries = [
        "什么是面向对象编程？",           # 概念解释
        "Python中如何处理异常？",        # 技术说明
        "写一个快速排序算法",            # 代码实现
        "创建一个完整的Web API项目"      # 复杂项目
    ]
    
    for query in learning_queries:
        print(f"💬 学生问题: {query}")
        
        # 智能分类和执行
        result = cognitive_agent.execute_instruction_syn(query)
        
        # 根据结果类型提供不同的反馈
        if isinstance(result, str):
            print("📚 知识解答:", result[:200] + "...")
        elif hasattr(result, 'return_value'):
            print("💻 代码实现:", result.return_value)
        elif hasattr(result, 'final_message'):
            print("🏗️ 项目完成:", result.final_message)
        
        print()

programming_tutor_demo()
```

### 场景2: 智能代码助手

```python
def smart_coding_assistant():
    """智能代码助手演示"""
    
    # 工作流：从需求分析到代码实现
    tasks = [
        "解释这个需求：用户注册和登录功能",    # 需求分析
        "设计用户表的数据库结构",            # 设计
        "实现用户注册API",                   # 单一功能
        "创建完整的用户认证系统"             # 完整系统
    ]
    
    for task in tasks:
        print(f"🎯 任务: {task}")
        
        # 分类预测
        task_type, execution_mode = cognitive_agent.classify_instruction(task)
        print(f"📋 分类: {task_type} | {execution_mode}")
        
        # 执行策略说明
        if task_type == "informational":
            print("💡 策略: 提供解释和分析")
        elif execution_mode == "single_step":
            print("⚡ 策略: 直接生成代码")
        else:
            print("🧠 策略: 多步骤项目规划")
        
        print()

smart_coding_assistant()
```

### 场景3: 错误处理和恢复

```python
def error_handling_demo():
    """错误处理和自动恢复演示"""
    
    # 测试各种可能的错误情况
    problematic_instructions = [
        "执行一个不存在的命令",
        "读取一个不存在的文件", 
        "连接到无效的网址"
    ]
    
    for instruction in problematic_instructions:
        print(f"🧪 测试指令: {instruction}")
        
        try:
            result = cognitive_agent.execute_instruction_syn(instruction)
            print(f"✅ 执行成功: {result}")
        except Exception as e:
            print(f"❌ 执行失败: {e}")
            
            # 如果启用了自动恢复，包装器会尝试降级处理
            if cognitive_agent.enable_auto_recovery:
                print("🔧 自动恢复功能已启用")
        
        print()

error_handling_demo()
```

## 🔧 高级配置

### 自定义配置

```python
# 创建具有自定义配置的包装器
advanced_cognitive_agent = CognitiveAgent(
    base_agent=base_agent,
    enable_auto_recovery=True,        # 启用自动错误恢复
    classification_cache_size=200     # 增大缓存大小
)

# 检查配置
print(f"自动恢复: {advanced_cognitive_agent.enable_auto_recovery}")
print(f"缓存容量: {advanced_cognitive_agent._cache_max_size}")
print(f"工作流引擎: {advanced_cognitive_agent.workflow_engine is not None}")
```

### 与原始Agent方法比较

```python
# 对比包装器和原始Agent的执行方式
test_instruction = "解释Python装饰器"

print("🔄 方法对比测试")
print("-" * 40)

# 1. 原始Agent方法
print("1️⃣ 原始Agent:")
original_result = base_agent.chat_sync(test_instruction)
print(f"   结果: {type(original_result).__name__}")

# 2. 包装器智能路由
print("2️⃣ 智能包装器:")
wrapper_result = cognitive_agent.execute_instruction_syn(test_instruction)
print(f"   结果: {type(wrapper_result).__name__}")

# 3. 包装器手动分类
print("3️⃣ 手动分类:")
instruction_type, execution_mode = cognitive_agent.classify_instruction(test_instruction)
print(f"   分类: {instruction_type} | {execution_mode}")
```

## 💡 最佳实践

### 1. 指令编写建议

```python
# ✅ 好的指令示例
good_instructions = [
    "解释什么是RESTful API设计原则",      # 明确的信息请求
    "创建一个hello.py文件并输出Hello World",  # 具体的单步任务  
    "开发一个包含用户认证的Todo应用",        # 明确的多步项目
]

# ❌ 避免的指令示例  
bad_instructions = [
    "做点什么",                          # 模糊不清
    "帮我",                             # 缺乏具体内容
    "修复所有错误",                      # 缺乏上下文
]
```

### 2. 性能优化建议

```python
# 预热缓存 - 对常用指令进行预分类
common_instructions = [
    "什么是Python？",
    "显示当前时间", 
    "创建Web应用"
]

for instruction in common_instructions:
    cognitive_agent.classify_instruction(instruction)

print("缓存预热完成")
```

### 3. 错误处理策略

```python
def robust_execution(instruction):
    """健壮的执行策略"""
    try:
        # 优先使用智能包装器
        return cognitive_agent.execute_instruction_syn(instruction)
    except Exception as wrapper_error:
        print(f"⚠️ 包装器执行失败: {wrapper_error}")
        
        try:
            # 降级到基础Agent
            return base_agent.execute_sync(instruction)
        except Exception as base_error:
            print(f"❌ 基础Agent也失败: {base_error}")
            
            # 最后尝试对话模式
            return base_agent.chat_sync(f"请协助处理: {instruction}")

# 使用健壮执行策略
result = robust_execution("复杂的测试指令")
```

## 📚 总结

基于产生式规则的Agent包装器提供了：

### 🎯 核心优势
- **智能分类**: 自动识别指令类型和复杂度
- **智能路由**: 选择最优执行方式
- **无缝集成**: 保持原有Agent接口兼容
- **性能优化**: 缓存机制和统计监控
- **错误恢复**: 自动降级和异常处理

### 🚀 适用场景
- **编程学习**: 智能区分概念解释和代码实现
- **代码助手**: 自动选择单步执行或项目规划
- **任务自动化**: 智能处理简单和复杂任务
- **对话系统**: 提供智能的多模态交互

### 🔧 最佳实践
- 使用清晰明确的指令描述
- 定期监控性能统计
- 合理配置缓存大小
- 启用自动错误恢复机制

通过这个包装器，普通的Agent立即具备了认知推理能力，能够智能地处理各种类型的任务！🎉