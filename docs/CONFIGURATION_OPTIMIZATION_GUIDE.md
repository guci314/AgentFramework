# 配置和优化指南

## 概述

本指南详细介绍了AI代理框架v2版本中全局状态管理和AI状态更新器的配置参数、优化策略和性能调优方法。

## 配置参数

### 基础配置文件 (config.yaml)

```yaml
# 全局状态管理配置
workflow_state:
  max_history_size: 50              # 最大历史记录数
  enable_compression: true          # 启用状态压缩
  auto_cleanup: true               # 自动清理过期状态
  
# AI状态更新器配置
ai_state_updater:
  enabled: true                    # 启用AI状态更新
  model: "deepseek-chat"          # 使用的LLM模型
  update_frequency: "after_each_step"  # 更新频率
  
# LLM配置
llm_deepseek:
  model: "deepseek-chat"
  api_base: "https://api.deepseek.com/v1"
  temperature: 0.6
  max_tokens: 8192
  timeout: 30
  
# 性能监控配置
performance_monitor:
  enabled: true
  collection_interval: 5           # 数据收集间隔(秒)
  max_metrics_history: 1000       # 最大指标历史数量
```

### 环境变量配置

```bash
# API密钥
export DEEPSEEK_API_KEY="your-deepseek-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# 日志配置
export LOG_LEVEL="INFO"
export LOG_FORMAT="structured"

# 性能配置
export MAX_CONCURRENT_REQUESTS=3
export REQUEST_TIMEOUT=30
```

## 优化策略

### 1. 提示工程优化

#### 模板优化原则
- **简洁明确**: 避免冗余信息，专注核心要求
- **上下文相关**: 根据不同场景定制模板
- **变量合理**: 使用有意义的变量名和默认值

#### 示例优化前后对比

**优化前:**
```python
prompt = f"""
请分析以下工作流执行情况并生成状态描述。
任务: {task}
结果: {result}
时间: {time}
其他信息: {other}
请详细描述当前状态，包括所有相关信息。
"""
```

**优化后:**
```python
prompt = f"""
基于执行结果生成简洁的状态描述:
- 任务: {task}
- 状态: {'成功' if success else '异常'}
- 关键信息: {key_info}

要求: 50字以内，突出重点。
"""
```

### 2. LLM API调用优化

#### 批量处理
```python
# 批量状态更新
async def update_states_batch(contexts: List[Dict]) -> List[str]:
    tasks = [update_state_async(ctx) for ctx in contexts]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

#### 缓存策略
```python
# 智能缓存配置
CACHE_CONFIG = {
    'max_size': 200,           # 最大缓存条目数
    'ttl': 300,               # 生存时间(秒)
    'cache_similar': True,     # 缓存相似请求
    'similarity_threshold': 0.8 # 相似度阈值
}
```

#### 请求去重
```python
# 避免重复请求
def deduplicate_requests(contexts: List[Dict]) -> List[Dict]:
    seen = set()
    unique_contexts = []
    
    for ctx in contexts:
        key = generate_cache_key(ctx)
        if key not in seen:
            seen.add(key)
            unique_contexts.append(ctx)
    
    return unique_contexts
```

### 3. 内存优化

#### 状态历史管理
```python
# 动态历史大小调整
def adjust_history_size(memory_usage: float) -> int:
    if memory_usage > 0.8:  # 内存使用超过80%
        return 25           # 减少历史大小
    elif memory_usage < 0.5:  # 内存使用低于50%
        return 100          # 增加历史大小
    else:
        return 50           # 保持默认大小
```

#### 状态压缩
```python
# 长状态描述压缩
def compress_state(state: str, max_length: int = 200) -> str:
    if len(state) <= max_length:
        return state
    
    # 保留关键信息的智能压缩
    sentences = state.split('。')
    important_sentences = []
    
    for sentence in sentences:
        if any(keyword in sentence for keyword in ['错误', '完成', '进度', '问题']):
            important_sentences.append(sentence)
    
    compressed = '。'.join(important_sentences)
    return compressed[:max_length] + '...' if len(compressed) > max_length else compressed
```

### 4. 性能调优

#### 并发控制
```python
# 限制并发请求数
import asyncio
from asyncio import Semaphore

class ConcurrencyController:
    def __init__(self, max_concurrent: int = 3):
        self.semaphore = Semaphore(max_concurrent)
    
    async def controlled_request(self, request_func, *args, **kwargs):
        async with self.semaphore:
            return await request_func(*args, **kwargs)
```

#### 超时管理
```python
# 智能超时配置
TIMEOUT_CONFIG = {
    'simple_requests': 10,     # 简单请求超时
    'complex_requests': 30,    # 复杂请求超时
    'batch_requests': 60,      # 批量请求超时
}

def get_timeout(request_type: str, context_size: int) -> int:
    base_timeout = TIMEOUT_CONFIG.get(request_type, 30)
    
    # 根据上下文大小调整超时
    if context_size > 1000:
        return base_timeout * 2
    elif context_size > 500:
        return base_timeout * 1.5
    else:
        return base_timeout
```

#### 错误处理优化
```python
# 智能重试策略
class SmartRetryConfig:
    def __init__(self):
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 10.0
        self.exponential_base = 2.0
        
        # 不同错误类型的重试策略
        self.error_strategies = {
            'ConnectionError': {'max_retries': 5, 'base_delay': 2.0},
            'TimeoutError': {'max_retries': 3, 'base_delay': 1.0},
            'RateLimitError': {'max_retries': 10, 'base_delay': 5.0},
        }
    
    def get_retry_config(self, error_type: str) -> dict:
        return self.error_strategies.get(error_type, {
            'max_retries': self.max_retries,
            'base_delay': self.base_delay
        })
```

## 性能监控和调优

### 关键性能指标 (KPIs)

#### 响应时间指标
```python
# 监控指标定义
PERFORMANCE_METRICS = {
    'ai_state_update_latency': {
        'target': 2000,        # 目标延迟(ms)
        'warning': 3000,       # 警告阈值
        'critical': 5000,      # 严重阈值
    },
    'llm_api_latency': {
        'target': 1500,
        'warning': 2500,
        'critical': 4000,
    },
    'state_persistence_latency': {
        'target': 50,
        'warning': 100,
        'critical': 200,
    }
}
```

#### 成功率指标
```python
# 成功率监控
SUCCESS_RATE_TARGETS = {
    'ai_state_updates': 0.95,      # 95%成功率
    'llm_api_calls': 0.98,         # 98%成功率
    'fallback_recovery': 0.99,     # 99%回退成功率
}
```

### 性能分析工具

#### 使用状态查询工具
```bash
# 查看性能统计
python state_query_tool.py --sample --memory

# 导出性能数据
python state_query_tool.py --export json performance_data.json

# 实时监控
python state_query_tool.py --interactive
```

#### 性能测试脚本
```python
# 性能压力测试
python test_performance_load.py

# 边界条件测试
python tests/test_stress_boundary.py
```

## 故障排除指南

### 常见性能问题

#### 1. 响应时间过长

**症状**: AI状态更新耗时超过5秒

**诊断步骤**:
```python
# 检查各组件延迟
stats = updater_service.get_performance_statistics()
print(f"LLM调用延迟: {stats['llm_latency_avg']}ms")
print(f"解析延迟: {stats['parsing_latency_avg']}ms")
print(f"总延迟: {stats['total_latency_avg']}ms")
```

**解决方案**:
1. 优化提示模板长度
2. 增加并发限制
3. 启用缓存机制
4. 调整超时配置

#### 2. 内存使用过高

**症状**: 系统内存占用持续增长

**诊断步骤**:
```python
# 检查内存使用
memory_info = workflow_state.get_memory_usage()
print(f"状态历史大小: {memory_info['history_size_mb']} MB")
print(f"缓存大小: {memory_info['cache_size_mb']} MB")
```

**解决方案**:
1. 减少历史记录数量
2. 启用状态压缩
3. 定期清理缓存
4. 调整内存限制

#### 3. API调用失败率高

**症状**: LLM API调用经常失败

**诊断步骤**:
```python
# 检查错误统计
error_stats = updater_service.get_error_statistics()
for error_type, count in error_stats.items():
    print(f"{error_type}: {count} 次")
```

**解决方案**:
1. 检查API密钥和配额
2. 调整重试策略
3. 启用回退机制
4. 优化请求频率

## 最佳实践总结

### 1. 配置管理
- 使用配置文件而非硬编码
- 环境特定的配置分离
- 敏感信息使用环境变量
- 定期审查和更新配置

### 2. 性能优化
- 合理设置缓存策略
- 控制并发请求数量
- 优化提示模板长度
- 监控关键性能指标

### 3. 错误处理
- 实施多层回退机制
- 智能重试策略
- 详细错误日志记录
- 用户友好的错误消息

### 4. 监控和维护
- 定期性能评估
- 主动监控系统健康
- 及时处理性能警告
- 持续优化和改进

## 参考资料

- [性能监控文档](../performance_monitor.py)
- [状态查询工具](../state_query_tool.py)
- [配置系统文档](../config_system.py)
- [测试指南](../tests/README.md)
