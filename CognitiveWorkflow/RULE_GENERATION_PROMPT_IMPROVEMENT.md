# 规则生成提示改进

## 概述

对 `RuleGenerationService._generate_initial_rules` 方法进行了重大改进，使其更加明确、灵活和标准化。

## 主要改进

### 1. 移除固定规则数量限制

**改进前**:
```
请生成6-10个产生式规则，覆盖完整的执行流程。
```

**改进后**:
```
规则数量: 根据任务复杂度自行判断，简单任务2-3个规则，复杂任务可以更多
```

**优势**:
- 灵活适应不同复杂度的任务
- 避免为简单任务生成冗余规则
- 允许复杂任务生成足够的详细规则

### 2. 提供明确的JSON Schema

**改进前**:
```
每个规则需要包含：
1. 规则名称
2. 触发条件（IF部分，自然语言描述）
...
请以JSON格式返回规则列表。
```

**改进后**:
```json
{
  "rules": [
    {
      "rule_name": "规则名称（字符串）",
      "trigger_condition": "触发条件（IF部分，自然语言描述）",
      "action": "执行动作（THEN部分，自然语言指令）",
      "agent_capability_id": "智能体能力ID（必须从上述可用能力中选择）",
      "execution_phase": "执行阶段（information_gathering|problem_solving|verification）",
      "priority": 优先级数字（1-100，数字越大优先级越高）,
      "expected_result": "期望结果描述（字符串）"
    }
  ]
}
```

**优势**:
- 明确的数据结构定义
- 减少LLM输出格式错误
- 便于自动化解析和验证
- 提供字段类型和约束信息

### 3. 采用三阶段执行模式

**改进前**:
```
执行阶段（information_gathering/problem_solving/verification/cleanup）
```

**改进后**:
```
## 三阶段执行模式

请基于以下三阶段模式生成规则：

1. **收集阶段 (information_gathering)**: 分析需求、收集信息、理解问题
2. **执行阶段 (problem_solving)**: 实现主要功能、解决核心问题
3. **验证阶段 (verification)**: 测试结果、验证正确性、完善细节

**重要说明**: 简单直接的任务可以跳过收集阶段，直接从执行阶段开始。
```

**优势**:
- 清晰的阶段划分和职责定义
- 灵活的阶段跳过机制
- 符合软件开发的标准流程
- 便于规则优先级排序

### 4. 明确简单任务的处理方式

**新增内容**:
```
阶段分布: 
- 简单任务：可以只有执行和验证阶段
- 复杂任务：包含完整的收集、执行、验证三阶段
```

**优势**:
- 避免为简单任务生成不必要的收集规则
- 提高系统效率
- 减少规则执行的开销

## 配套技术改进

### 1. 更新字段映射

在 `_create_rule_from_data` 方法中添加了新旧字段名的兼容性支持：

```python
# 支持新旧字段名
phase_str = rule_data.get('execution_phase') or rule_data.get('phase', 'problem_solving')
rule_name = rule_data.get('rule_name') or rule_data.get('name', '未命名规则')
condition = rule_data.get('trigger_condition') or rule_data.get('condition', '')
expected_outcome = rule_data.get('expected_result') or rule_data.get('expected_outcome', '')
```

### 2. 确定性ID生成

替换了UUID生成，使用基于内容的哈希生成确定性ID：

```python
rule_id = f"rule_{hash(rule_name + str(rule_data)) % 1000000:06d}"
```

**优势**:
- 支持LLM缓存优化
- 同样的规则内容产生同样的ID
- 便于调试和追踪

## 提示工程改进

### 1. 结构化提示

使用Markdown格式的结构化提示，包含：
- 目标和可用能力
- 三阶段执行模式说明
- 明确的JSON Schema
- 详细的生成要求

### 2. 明确的约束和指导

```
## 生成要求

1. **规则数量**: 根据任务复杂度自行判断
2. **阶段分布**: 简单任务可跳过收集阶段
3. **条件描述**: 使用自然语言，便于语义匹配
4. **动作指令**: 具体明确，便于智能体理解和执行
5. **能力匹配**: agent_capability_id必须从可用能力列表中选择
6. **优先级**: 收集>执行>验证，同阶段内按重要性排序
```

### 3. 示例驱动

通过清晰的格式示例和约束说明，引导LLM生成高质量的规则。

## 实际应用效果

### 简单任务示例（Hello World程序）

**预期生成规则**:
```json
{
  "rules": [
    {
      "rule_name": "实现Hello World程序",
      "trigger_condition": "需要创建一个Hello World程序",
      "action": "编写打印'Hello, World!'的代码",
      "agent_capability_id": "coder",
      "execution_phase": "problem_solving",
      "priority": 90,
      "expected_result": "可运行的Hello World程序"
    },
    {
      "rule_name": "验证程序输出",
      "trigger_condition": "Hello World程序已创建完成",
      "action": "运行程序并验证输出是否为'Hello, World!'",
      "agent_capability_id": "tester",
      "execution_phase": "verification", 
      "priority": 80,
      "expected_result": "确认程序输出正确"
    }
  ]
}
```

### 复杂任务示例（开发计算器）

**预期生成规则**:
包含完整的三阶段规则，从需求分析、架构设计，到功能实现、测试验证。

## 向后兼容性

通过在字段映射中支持新旧字段名，确保：
- 现有的规则数据仍可正常加载
- 新的JSON schema逐步生效
- 平滑的系统升级路径

## 总结

这个改进显著提升了规则生成的质量和灵活性：

- ✅ **灵活性**: 根据任务复杂度生成适量规则
- ✅ **标准化**: 明确的JSON schema和字段定义
- ✅ **智能化**: 三阶段模式和简单任务优化
- ✅ **可靠性**: 更好的LLM输出格式控制
- ✅ **可维护性**: 清晰的提示结构和约束

系统现在能够更智能地为不同复杂度的任务生成适合的规则集，同时保持高质量的输出格式。