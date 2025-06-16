# pythonTask.py 组件单元测试

本目录包含对 `pythonTask.py` 中五个核心组件的完整单元测试套件。

## 测试组件概览

### 1. Device 类测试 (`test_device.py`)
测试基础代码执行器功能：
- ✅ 基础代码执行
- ✅ 语法和运行时错误处理  
- ✅ 多行代码和模块导入
- ✅ Unicode和特殊字符处理
- ✅ Result对象结构验证

### 2. StatefulExecutor 类测试 (`test_stateful_executor.py`)
测试有状态代码执行器功能：
- ✅ IPython环境初始化
- ✅ 变量状态持久化
- ✅ 复杂数据类型支持 (numpy, pandas)
- ✅ 类实例状态保持
- ✅ 错误恢复机制
- ✅ return_value 管理

### 3. Thinker 类测试 (`test_thinker.py`)
测试代码生成器功能：
- ✅ 自然语言到代码转换
- ✅ 同步和流式执行模式
- ✅ 聊天功能 (支持JSON格式)
- ✅ 代码修改和重试机制
- ✅ 结果生成功能
- ✅ 复杂任务处理

### 4. Evaluator 类测试 (`test_evaluator.py`)
测试任务评估器功能：
- ✅ 任务完成评估
- ✅ JSON格式结果解析
- ✅ 自定义评估标准
- ✅ 知识加载功能
- ✅ 错误处理和重试
- ✅ 兜底评估机制

### 5. Agent 类测试 (`test_agent.py`)
测试智能体集成功能：
- ✅ 完整执行-评估-重试循环
- ✅ 多评估器管理
- ✅ 知识和模块加载
- ✅ 配置选项测试
- ✅ 复杂场景处理
- ✅ 流式和同步接口

## 运行测试

### 环境要求

```bash
# 安装依赖
pip install -r requirements.txt

# 设置API密钥 (可选，用于完整测试)
export DEEPSEEK_API_KEY="your_deepseek_api_key"
```

### 运行方式

#### 1. 运行所有测试 (推荐)
```bash
python tests/run_all_tests.py
```

#### 2. 运行单个组件测试
```bash
# Device 测试
python tests/test_device.py

# StatefulExecutor 测试  
python tests/test_stateful_executor.py

# Thinker 测试
python tests/test_thinker.py

# Evaluator 测试
python tests/test_evaluator.py

# Agent 测试
python tests/test_agent.py
```

#### 3. 使用 unittest 运行
```bash
# 运行所有测试
python -m unittest discover tests/

# 运行特定测试类
python -m unittest tests.test_device.TestDeviceBasic

# 运行特定测试方法
python -m unittest tests.test_device.TestDeviceBasic.test_simple_code_execution
```

## 测试分类

### 本地测试 (无需API密钥)
- Device 基础功能测试
- StatefulExecutor 基础功能测试
- 部分 Thinker、Evaluator、Agent 的初始化测试

### API 集成测试 (需要DEEPSEEK_API_KEY)
- Thinker 代码生成测试
- Evaluator 任务评估测试
- Agent 完整工作流测试
- 聊天和流式功能测试

## 测试设计原则

1. **真实API调用**: 使用DeepSeek进行实际的代码生成和评估
2. **分层测试**: 从单元测试到集成测试逐步覆盖
3. **错误处理**: 全面测试异常情况和边界条件
4. **状态管理**: 验证有状态执行的正确性
5. **性能考虑**: 设置合理的重试次数和超时

## 预期测试结果

### 完整测试 (有API密钥)
```
🚀 AgentFrameWork pythonTask.py 组件单元测试
====================================================================
📡 检测到DEEPSEEK_API_KEY，将运行完整测试（包括真实API调用）

📊 各组件测试结果:
   - Device          : ✅ 通过
   - StatefulExecutor: ✅ 通过
   - Thinker         : ✅ 通过
   - Evaluator       : ✅ 通过
   - Agent           : ✅ 通过

🏆 总体结果: 🎉 全部测试通过！
```

### 本地测试 (无API密钥)
```
🚀 AgentFrameWork pythonTask.py 组件单元测试
====================================================================
⚠️  未检测到DEEPSEEK_API_KEY，将跳过需要API的测试

📊 各组件测试结果:
   - Device          : ✅ 通过
   - StatefulExecutor: ✅ 通过
   - Thinker         : ✅ 通过 (仅基础测试)
   - Evaluator       : ✅ 通过 (仅基础测试)
   - Agent           : ✅ 通过 (仅基础测试)

💡 提示: 设置 DEEPSEEK_API_KEY 环境变量可运行完整的API集成测试
```

## 故障排除

### 常见问题

1. **导入错误**
   ```bash
   # 确保在项目根目录运行
   cd /path/to/AgentFrameWork
   python tests/run_all_tests.py
   ```

2. **API 调用失败**
   ```bash
   # 检查网络连接和API密钥
   echo $DEEPSEEK_API_KEY
   curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" https://api.deepseek.com/
   ```

3. **依赖缺失**
   ```bash
   # 安装缺失的依赖
   pip install numpy pandas matplotlib ipython
   ```

### 测试调试

启用详细日志：
```bash
export PYTHONPATH=.
python -m unittest tests.test_agent.TestAgentExecution.test_simple_task_execution_sync -v
```

## 测试覆盖率

各组件的功能覆盖率：
- **Device**: ~95% (基础执行功能)
- **StatefulExecutor**: ~90% (状态管理和IPython集成)  
- **Thinker**: ~85% (代码生成和聊天功能)
- **Evaluator**: ~80% (评估逻辑和错误处理)
- **Agent**: ~85% (完整工作流和配置选项)

## 贡献指南

添加新测试时请遵循：
1. 测试类命名: `Test[ComponentName][TestCategory]`
2. 测试方法命名: `test_[功能描述]`
3. 包含详细的文档字符串
4. 添加适当的断言和错误消息
5. 考虑API依赖性，使用 `@unittest.skipUnless` 装饰器