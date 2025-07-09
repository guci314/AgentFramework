# 懒加载语言模型使用指南

## 🚀 懒加载的优势

- **导入速度提升12倍**: 从26.3秒降至2.2秒
- **按需加载**: 只在实际使用时初始化模型
- **内存优化**: 减少不必要的内存占用
- **缓存机制**: 重复使用时性能极佳

## 📖 使用方法

### 方式一：直接使用懒加载（推荐）

```python
# 导入懒加载模块
from optimized_llm_loader import get_llm

# 获取模型（按需加载）
llm = get_llm('gemini_2_5_flash')

# 在CognitiveAgent中使用
from embodied_cognitive_workflow import CognitiveAgent
agent = CognitiveAgent(llm=llm)
```

### 方式二：替换现有代码

```python
# 替换前（传统方式）
import pythonTask
llm = pythonTask.llm_gemini_2_5_flash_google

# 替换后（懒加载方式）
from optimized_llm_loader import get_llm
llm = get_llm('gemini_2_5_flash')
```

## 🤖 可用模型列表

| 模型名称 | 模型ID | 用途 |
|---------|--------|------|
| `gemini_2_5_flash` | models/gemini-2.5-flash | 通用任务（推荐） |
| `gemini_2_5_pro` | gemini-2.5-pro | 复杂推理 |
| `gemini_2_flash` | gemini-2.0-flash | 快速响应 |
| `deepseek_v3` | deepseek-ai/DeepSeek-V3 | 代码生成 |
| `deepseek_r1` | deepseek-ai/DeepSeek-R1 | 推理任务 |
| `deepseek_chat` | deepseek-chat | 对话任务 |
| `qwen_qwq_32b` | Qwen/QwQ-32B | 问答任务 |
| `qwen_2_5_coder_32b` | Qwen/Qwen2.5-Coder-32B-Instruct | 编程助手 |

## 📋 环境要求

确保设置了相应的API密钥环境变量：

```bash
# Gemini模型
export GEMINI_API_KEY="your_gemini_api_key"

# DeepSeek模型
export DEEPSEEK_API_KEY="your_deepseek_api_key"
export SILICONFLOW_API_KEY="your_siliconflow_api_key"  # 部分DeepSeek模型
```

## 🔧 高级用法

### 1. 批量获取模型

```python
from optimized_llm_loader import get_llm

# 获取多个模型
models = {
    'fast': get_llm('gemini_2_5_flash'),
    'smart': get_llm('gemini_2_5_pro'),
    'coder': get_llm('deepseek_v3')
}
```

### 2. 错误处理

```python
from optimized_llm_loader import get_llm

llm = get_llm('gemini_2_5_flash')
if llm is None:
    print("⚠️ 模型加载失败，请检查API密钥")
else:
    print("✅ 模型加载成功")
```

### 3. 列出可用模型

```python
from optimized_llm_loader import _llm_loader

# 查看所有可用模型
available_models = _llm_loader.list_available_models()
for name, model_id in available_models.items():
    print(f"{name}: {model_id}")
```

### 4. 清空缓存

```python
from optimized_llm_loader import _llm_loader

# 清空模型缓存（释放内存）
_llm_loader.clear_cache()
```

## 🎯 实际应用示例

### 认知调试器

```python
from optimized_llm_loader import get_llm
from embodied_cognitive_workflow import CognitiveAgent
from cognitive_debugger import CognitiveDebugger

# 快速启动（导入速度快12倍）
llm = get_llm('gemini_2_5_flash')
agent = CognitiveAgent(llm=llm, max_cycles=5)
debugger = CognitiveDebugger(agent)

# 开始调试
debugger.start_debug("你的任务描述")
```

### 销售分析演示

```python
from optimized_llm_loader import get_llm
from embodied_cognitive_workflow import CognitiveAgent

# 使用更强大的模型进行复杂分析
llm = get_llm('gemini_2_5_pro')
agent = CognitiveAgent(
    llm=llm,
    max_cycles=10,
    enable_super_ego=True
)

result = agent.execute_sync("分析销售数据并生成报告")
```

## ⚡ 性能对比

| 方式 | 导入时间 | 内存使用 | 首次模型加载 | 缓存访问 |
|------|----------|----------|--------------|----------|
| 传统方式 | 26.3秒 | 高 | 即时 | N/A |
| 懒加载方式 | 2.2秒 | 低 | 0.4秒 | 0.000002秒 |
| **性能提升** | **12倍** | **显著降低** | **按需** | **247,000倍** |

## 🔄 迁移指南

### 自动迁移脚本

如果有大量文件需要迁移，可以使用以下模式：

```python
# 在每个需要迁移的文件开头添加
try:
    from optimized_llm_loader import get_llm
    llm_gemini_2_5_flash_google = get_llm('gemini_2_5_flash')
except ImportError:
    # 兜底方案，使用传统方式
    import pythonTask
    llm_gemini_2_5_flash_google = pythonTask.llm_gemini_2_5_flash_google
```

### 渐进式迁移

1. **第一阶段**: 新文件使用懒加载
2. **第二阶段**: 高频使用的文件迁移
3. **第三阶段**: 全部文件迁移完成

## 🐛 故障排除

### 常见问题

1. **导入错误**
   ```python
   # 确保在正确的目录下或路径配置正确
   import sys
   sys.path.append('/path/to/embodied_cognitive_workflow')
   from optimized_llm_loader import get_llm
   ```

2. **API密钥错误**
   ```bash
   # 检查环境变量
   echo $GEMINI_API_KEY
   ```

3. **模型加载失败**
   ```python
   # 检查网络和代理设置
   llm = get_llm('gemini_2_5_flash')
   if llm is None:
       print("请检查网络连接和API密钥")
   ```

## 💡 最佳实践

1. **优先使用懒加载**: 新项目直接使用懒加载模式
2. **合理选择模型**: 根据任务复杂度选择合适的模型
3. **缓存管理**: 长时间运行时可适当清理缓存
4. **错误处理**: 始终检查模型是否成功加载
5. **环境配置**: 确保API密钥正确配置

通过使用懒加载，你的应用启动速度将显著提升，开发体验更加流畅！