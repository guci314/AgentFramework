# 最佳实践和故障排除指南

## 最佳实践

### 1. 工作流设计最佳实践

#### 1.1 状态感知工作流设计

**原则**: 设计能够有效利用全局状态的工作流

```python
# ✅ 好的做法：状态驱动的条件逻辑
def create_adaptive_workflow():
    return [
        {
            "type": "python",
            "code": """
# 检查当前状态并据此调整行为
current_state = workflow_state.get_global_state() if 'workflow_state' in globals() else ""

if "错误" in current_state:
    print("检测到之前的错误，启用保守模式")
    processing_mode = "conservative"
else:
    print("正常模式处理")
    processing_mode = "normal"
""",
            "description": "根据状态调整处理模式"
        }
    ]

# ❌ 不好的做法：忽略状态信息
def create_rigid_workflow():
    return [
        {
            "type": "python", 
            "code": "processing_mode = 'normal'  # 总是使用相同模式",
            "description": "固定处理模式"
        }
    ]
```

#### 1.2 状态描述规范

**原则**: 使用清晰、一致的状态描述

```python
# ✅ 好的状态描述
good_states = [
    "正在处理用户数据，已完成验证阶段，准备进行分析",
    "数据分析完成，发现3个异常值需要人工确认",
    "所有任务顺利完成，系统准备就绪"
]

# ❌ 不好的状态描述  
bad_states = [
    "执行了function_xyz()，返回值为dict",
    "状态更新",
    "处理中..."
]
```

#### 1.3 错误处理策略

**原则**: 设计优雅的错误处理和恢复机制

```python
def robust_workflow_step():
    return {
        "type": "python",
        "code": """
try:
    # 主要逻辑
    result = perform_critical_operation()
    
    # 成功时更新状态
    if 'workflow_state' in globals():
        workflow_state.set_global_state(
            f"关键操作成功完成，处理了{len(result)}项数据",
            source="success_handler"
        )
        
except Exception as e:
    # 错误处理
    print(f"操作失败: {e}")
    
    # 错误状态更新
    if 'workflow_state' in globals():
        workflow_state.set_global_state(
            f"操作遇到问题: {str(e)[:50]}，正在尝试恢复",
            source="error_handler"
        )
    
    # 尝试恢复
    result = attempt_recovery()
""",
        "description": "执行关键操作并处理可能的错误"
    }
```

### 2. 状态管理最佳实践

#### 2.1 状态粒度控制

**原则**: 保持适当的状态详细程度

```python
# ✅ 适当的状态粒度
def update_processing_state(processed_count, total_count, errors):
    progress_percent = (processed_count / total_count) * 100
    
    state = f"数据处理进行中，已完成{progress_percent:.1f}% ({processed_count}/{total_count})"
    
    if errors > 0:
        state += f"，发现{errors}个错误需要关注"
    
    return state

# ❌ 过于详细的状态
def overly_detailed_state():
    return """
    当前时间: 2024-01-15 14:30:22.123456
    内存使用: 245.7MB
    CPU使用率: 23.4%
    网络延迟: 45ms
    数据库连接: 活跃
    缓存命中率: 89.2%
    处理的记录ID: [1001, 1002, 1003, ...]
    """

# ❌ 过于简略的状态
def overly_simple_state():
    return "处理中"
```

#### 2.2 状态历史管理

**原则**: 合理管理状态历史，避免内存泄漏

```python
class StateManagementBestPractices:
    def __init__(self, workflow_state):
        self.workflow_state = workflow_state
    
    def periodic_cleanup(self):
        """定期清理策略"""
        memory_info = self.workflow_state.get_memory_usage()
        
        # 当内存使用超过阈值时清理
        if memory_info.get('estimated_memory_mb', 0) > 50:
            # 保留最近的重要状态
            history = self.workflow_state.get_state_history()
            important_states = [
                entry for entry in history
                if any(keyword in entry.state_snapshot 
                      for keyword in ['错误', '完成', '失败', '成功'])
            ]
            
            # 清理并重新添加重要状态
            self.workflow_state.clear_global_state()
            for state in important_states[-10:]:  # 保留最近10个重要状态
                self.workflow_state.set_global_state(
                    state.state_snapshot, 
                    source=f"cleanup_{state.source}"
                )
    
    def smart_state_compression(self, state: str) -> str:
        """智能状态压缩"""
        if len(state) <= 200:
            return state
        
        # 提取关键信息
        key_phrases = []
        sentences = state.split('。')
        
        for sentence in sentences:
            if any(keyword in sentence for keyword in 
                  ['完成', '错误', '失败', '成功', '进度', '问题']):
                key_phrases.append(sentence.strip())
        
        compressed = '。'.join(key_phrases)
        return compressed[:200] + '...' if len(compressed) > 200 else compressed
```

### 3. AI状态更新器最佳实践

#### 3.1 提示优化

**原则**: 设计高效、准确的提示模板

```python
# ✅ 优化的提示模板
OPTIMIZED_PROMPT = """
角色: 工作流状态分析师
任务: 基于执行结果生成简洁状态描述

输入信息:
- 任务: {task_description}
- 结果: {execution_result}
- 状态: {status}

要求:
1. 50字以内
2. 突出关键信息
3. 使用自然语言
4. 避免技术术语

示例格式: "数据处理完成80%，发现3个异常值需要确认"
"""

# ❌ 未优化的提示
POOR_PROMPT = """
请分析以下工作流执行情况并生成详细的状态描述，包括所有相关信息、技术细节、执行时间、内存使用情况、错误堆栈等等...
"""
```

#### 3.2 回退策略配置

**原则**: 设计多层次的回退机制

```python
from enum import Enum

class FallbackStrategy(Enum):
    RETRY_SIMPLIFIED = "retry_simplified"
    TEMPLATE_BASED = "template_based"
    RULE_BASED = "rule_based"
    MINIMAL_STATE = "minimal_state"
    NOTIFY_OPERATOR = "notify_operator"

# ✅ 推荐的回退策略配置
RECOMMENDED_FALLBACK_CONFIG = [
    FallbackStrategy.RETRY_SIMPLIFIED,    # 首先尝试简化重试
    FallbackStrategy.TEMPLATE_BASED,      # 然后使用模板生成
    FallbackStrategy.RULE_BASED,          # 基于规则生成
    FallbackStrategy.MINIMAL_STATE,       # 最小状态描述
    FallbackStrategy.NOTIFY_OPERATOR      # 最后通知操作员
]
```

### 4. 性能优化最佳实践

#### 4.1 缓存策略

```python
class PerformanceOptimization:
    def __init__(self):
        self.cache_hit_rate_target = 0.8  # 目标缓存命中率
        self.max_cache_size = 200
        
    def optimize_cache_usage(self, updater_service):
        """优化缓存使用"""
        stats = updater_service.get_cache_statistics()
        
        if stats['hit_rate'] < self.cache_hit_rate_target:
            # 增加缓存大小
            new_size = min(self.max_cache_size, stats['current_size'] * 1.5)
            updater_service.set_cache_size(int(new_size))
            
        # 调整TTL
        if stats['eviction_rate'] > 0.3:  # 驱逐率过高
            updater_service.set_cache_ttl(stats['current_ttl'] * 1.2)
```

#### 4.2 并发控制

```python
import asyncio
from asyncio import Semaphore

class ConcurrencyManager:
    def __init__(self, max_concurrent=3):
        self.semaphore = Semaphore(max_concurrent)
        self.active_requests = 0
        
    async def controlled_update(self, updater_service, context):
        """控制并发的状态更新"""
        async with self.semaphore:
            self.active_requests += 1
            try:
                result = await updater_service.update_state_async(context)
                return result
            finally:
                self.active_requests -= 1
    
    def get_load_info(self):
        """获取负载信息"""
        return {
            'active_requests': self.active_requests,
            'available_slots': self.semaphore._value,
            'utilization': self.active_requests / (self.active_requests + self.semaphore._value)
        }
```

## 故障排除指南

### 1. 常见问题诊断

#### 1.1 状态更新不生效

**症状**: 调用`set_global_state()`但状态没有改变

**诊断步骤**:
```python
def diagnose_state_update_issue(workflow_state):
    # 1. 检查状态更新是否启用
    if not workflow_state.is_state_update_enabled():
        print("❌ 状态更新已禁用")
        return "状态更新被禁用，请调用 enable_state_updates()"
    
    # 2. 检查是否有异常
    try:
        workflow_state.set_global_state("测试状态")
        print("✅ 状态更新功能正常")
    except Exception as e:
        print(f"❌ 状态更新异常: {e}")
        return f"状态更新出现异常: {e}"
    
    # 3. 检查内存使用
    memory_info = workflow_state.get_memory_usage()
    if memory_info.get('estimated_memory_mb', 0) > 100:
        print("⚠️  内存使用过高，可能影响性能")
        return "内存使用过高，建议清理状态历史"
    
    return "状态更新功能正常"
```

**解决方案**:
```python
# 解决方案1: 启用状态更新
workflow_state.enable_state_updates()

# 解决方案2: 清理内存
workflow_state.clear_global_state()

# 解决方案3: 检查线程安全
import threading
if isinstance(workflow_state._state_lock, threading.RLock):
    print("✅ 线程安全机制正常")
else:
    print("❌ 线程安全机制异常")
```

#### 1.2 AI状态更新失败

**症状**: AI状态更新器无法生成状态描述

**诊断步骤**:
```python
async def diagnose_ai_updater_issue(ai_updater):
    # 1. 检查健康状态
    health = await ai_updater.health_check()
    print(f"健康状态: {health}")
    
    # 2. 检查API配置
    config = ai_updater.get_llm_config()
    required_keys = ['model', 'api_base', 'api_key']
    
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"❌ 缺少配置: {key}")
            return f"配置不完整，缺少: {key}"
    
    # 3. 测试API连接
    try:
        test_context = {
            'task_description': '测试任务',
            'execution_result': {'success': True},
            'timestamp': '2024-01-15 10:00:00'
        }
        result = await ai_updater.update_state_async(test_context)
        print(f"✅ API测试成功: {result}")
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return f"API连接失败: {e}"
    
    return "AI状态更新器正常"
```

**解决方案**:
```python
# 解决方案1: 检查API密钥
import os
if not os.getenv('DEEPSEEK_API_KEY'):
    print("请设置 DEEPSEEK_API_KEY 环境变量")

# 解决方案2: 调整超时设置
ai_updater.set_llm_config({
    'timeout': 60,  # 增加超时时间
    'max_retries': 5  # 增加重试次数
})

# 解决方案3: 启用回退机制
ai_updater.set_fallback_strategies([
    FallbackStrategy.RETRY_SIMPLIFIED,
    FallbackStrategy.TEMPLATE_BASED,
    FallbackStrategy.MINIMAL_STATE
])
```

#### 1.3 性能问题

**症状**: 状态更新响应时间过长

**诊断步骤**:
```python
def diagnose_performance_issue(ai_updater):
    # 获取性能统计
    stats = ai_updater.get_update_statistics()
    
    print("性能诊断报告:")
    print(f"平均响应时间: {stats.get('average_response_time', 'N/A')}ms")
    print(f"成功率: {stats.get('success_rate', 'N/A')}%")
    print(f"缓存命中率: {stats.get('cache_hit_rate', 'N/A')}%")
    print(f"回退使用率: {stats.get('fallback_usage_rate', 'N/A')}%")
    
    # 性能问题识别
    issues = []
    
    if stats.get('average_response_time', 0) > 3000:
        issues.append("响应时间过长")
    
    if stats.get('success_rate', 1) < 0.9:
        issues.append("成功率过低")
    
    if stats.get('cache_hit_rate', 1) < 0.5:
        issues.append("缓存效率低")
    
    return issues
```

**解决方案**:
```python
# 解决方案1: 启用缓存
ai_updater.enable_caching(cache_size=200, ttl=600)

# 解决方案2: 优化提示模板
ai_updater.template_manager.optimize_templates()

# 解决方案3: 并发控制
concurrency_manager = ConcurrencyManager(max_concurrent=2)

# 解决方案4: 监控和调优
def auto_tune_performance(ai_updater):
    stats = ai_updater.get_update_statistics()
    
    # 动态调整超时
    if stats.get('timeout_rate', 0) > 0.1:
        current_timeout = ai_updater.get_llm_config().get('timeout', 30)
        ai_updater.set_llm_config({'timeout': current_timeout * 1.5})
    
    # 动态调整缓存
    if stats.get('cache_hit_rate', 0) < 0.6:
        ai_updater.increase_cache_size()
```

### 2. 错误代码参考

| 错误代码 | 描述 | 可能原因 | 解决方案 |
|---------|------|----------|----------|
| STATE_001 | 状态更新被禁用 | 调用了disable_state_updates() | 调用enable_state_updates() |
| STATE_002 | 状态类型错误 | 传入非字符串类型的状态 | 确保状态为字符串类型 |
| STATE_003 | 内存使用过高 | 状态历史过多 | 调用clear_global_state() |
| AI_001 | LLM API连接失败 | 网络问题或API密钥错误 | 检查网络和API配置 |
| AI_002 | 提示模板错误 | 模板格式不正确 | 检查模板语法 |
| AI_003 | 响应解析失败 | LLM返回格式异常 | 启用回退机制 |
| PERF_001 | 响应时间过长 | 网络延迟或模型负载高 | 调整超时和重试策略 |
| PERF_002 | 内存泄漏 | 缓存或历史记录未清理 | 启用自动清理 |

### 3. 调试工具和技巧

#### 3.1 状态查询工具

```python
# 使用内置的状态查询工具
from state_query_tool import StateQueryTool

query_tool = StateQueryTool(workflow_state)

# 查看状态概览
query_tool.show_overview()

# 查看详细历史
query_tool.show_history(limit=10)

# 导出状态数据
query_tool.export_data('state_dump.json')
```

#### 3.2 性能分析

```python
# 性能分析工具
from performance_monitor import get_performance_monitor

monitor = get_performance_monitor()

# 开始监控
monitor.start_monitoring()

# 执行工作流
agent.execute_workflow(workflow)

# 获取性能报告
report = monitor.get_performance_report()
print(report)
```

#### 3.3 日志分析

```python
import logging

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workflow_debug.log'),
        logging.StreamHandler()
    ]
)

# 启用结构化日志
import structlog
logger = structlog.get_logger(__name__)

logger.info("工作流开始", workflow_id="test_001")
```

### 4. 预防性维护

#### 4.1 定期健康检查

```python
async def system_health_check(agent):
    """系统健康检查"""
    health_report = {
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }
    
    # 检查状态管理
    try:
        memory_info = agent.workflow_state.get_memory_usage()
        health_report['checks']['state_management'] = {
            'status': 'healthy',
            'memory_usage_mb': memory_info.get('estimated_memory_mb', 0),
            'history_count': memory_info.get('history_count', 0)
        }
    except Exception as e:
        health_report['checks']['state_management'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # 检查AI更新器
    if hasattr(agent.workflow_state, '_ai_updater') and agent.workflow_state._ai_updater:
        try:
            ai_health = await agent.workflow_state._ai_updater.health_check()
            health_report['checks']['ai_updater'] = ai_health
        except Exception as e:
            health_report['checks']['ai_updater'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    return health_report
```

#### 4.2 自动优化

```python
class AutoOptimizer:
    def __init__(self, agent):
        self.agent = agent
        self.optimization_history = []
    
    def auto_optimize(self):
        """自动优化系统性能"""
        optimizations = []
        
        # 内存优化
        memory_info = self.agent.workflow_state.get_memory_usage()
        if memory_info.get('estimated_memory_mb', 0) > 50:
            self.agent.workflow_state.clear_global_state()
            optimizations.append("清理状态历史")
        
        # AI更新器优化
        if hasattr(self.agent.workflow_state, '_ai_updater'):
            ai_updater = self.agent.workflow_state._ai_updater
            if ai_updater:
                stats = ai_updater.get_update_statistics()
                
                # 缓存优化
                if stats.get('cache_hit_rate', 1) < 0.6:
                    ai_updater.optimize_cache()
                    optimizations.append("优化缓存配置")
                
                # 超时优化
                if stats.get('timeout_rate', 0) > 0.1:
                    config = ai_updater.get_llm_config()
                    config['timeout'] = config.get('timeout', 30) * 1.2
                    ai_updater.set_llm_config(config)
                    optimizations.append("调整超时设置")
        
        self.optimization_history.append({
            'timestamp': datetime.now().isoformat(),
            'optimizations': optimizations
        })
        
        return optimizations
```

## 总结

遵循这些最佳实践和故障排除指南，您可以：

1. **设计更可靠的工作流**: 利用状态感知和错误处理机制
2. **优化系统性能**: 通过缓存、并发控制和资源管理
3. **快速诊断问题**: 使用系统化的诊断方法和工具
4. **保持系统健康**: 通过预防性维护和自动优化

记住，良好的监控和日志记录是维护复杂系统的关键。定期检查系统健康状态，及时发现和解决潜在问题。
