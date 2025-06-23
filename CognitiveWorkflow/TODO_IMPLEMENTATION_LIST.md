# CognitiveWorkflow 未实现功能清单

本文档详细列出了 CognitiveWorkflow 模块中所有未实现的功能，按优先级排序，并提供具体的实现建议。

## 📋 总览

- **总计未实现功能**: 5个
- **高优先级**: 1个
- **中优先级**: 4个
- **低优先级**: 0个

---

## 🔥 高优先级 TODO

### 1. 动态任务添加 - 计划修正的核心功能
**位置**: `CognitiveWorkflowEngine._apply_plan_modification()` 方法  
**文件**: `cognitive_workflow.py` 第1370行  
**当前状态**: 空实现（pass）

**功能描述**:
实现运行时动态添加新任务的能力，这是计划修正机制的核心功能。

**需要实现**:
1. 解析modification_decision中的新任务数据
2. 创建CognitiveTask对象并添加到task_list
3. 验证新任务的有效性（agent存在、先决条件合理等）
4. 重新计算任务ID以避免冲突
5. 记录任务添加的审计日志

**示例实现**:
```python
new_tasks_data = modification_decision.get('details', {}).get('new_tasks', [])
for task_data in new_tasks_data:
    new_task = CognitiveTask(
        id=f"dynamic_{len(self.task_list)+1}",
        name=task_data['name'],
        instruction=task_data['instruction'],
        agent_name=task_data['agent_name'],
        instruction_type=task_data['instruction_type'],
        phase=TaskPhase(task_data['phase']),
        expected_output=task_data['expected_output'],
        precondition=task_data['precondition']
    )
    self.task_list.append(new_task)
    logger.info(f"添加新任务: {new_task.id}")
```

**影响范围**: 影响工作流的动态适应能力，是实现真正智能工作流的关键

---

## ⚡ 中优先级 TODO

### 2. 智能修复任务解析 - 完善修复任务生成
**位置**: `CognitivePlanner.generate_recovery_tasks()` 方法  
**文件**: `cognitive_workflow.py` 第619行  
**当前状态**: 简化实现，只生成基本重试任务

**功能描述**:
将当前的简单重试机制升级为智能修复任务生成系统。

**需要实现**:
1. 解析LLM返回的JSON格式修复任务列表
2. 支持多种修复策略：参数调整、环境修复、依赖安装等
3. 根据错误类型生成针对性修复任务
4. 支持修复任务链：修复A → 修复B → 重试原任务

**示例实现**:
```python
try:
    json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
    if json_match:
        result_json = json.loads(json_match.group())
        recovery_tasks = []
        for task_data in result_json.get('recovery_tasks', []):
            recovery_task = CognitiveTask(
                id=task_data['id'],
                name=task_data['name'],
                instruction=task_data['instruction'],
                # ... 其他属性
            )
            recovery_tasks.append(recovery_task)
        return recovery_tasks
except json.JSONDecodeError:
    logger.warning("修复任务JSON解析失败，使用简单重试")
```

**影响范围**: 提升错误恢复能力，减少人工干预需求

### 3. 智能补充任务生成 - 增强复杂场景处理能力
**位置**: `CognitiveWorkflowEngine._handle_no_executable_tasks()` 方法  
**文件**: `cognitive_workflow.py` 第1350行  
**当前状态**: 仅处理失败任务的修复，无法生成新的补充任务

**功能描述**:
当没有可执行任务时，智能分析并生成必要的补充任务。

**需要实现**:
1. 基于当前状态和原始目标分析缺失的任务
2. 检测是否需要额外的信息收集任务
3. 生成前置条件准备任务（如环境配置、依赖安装）
4. 支持目标细化：将模糊目标分解为具体任务
5. 智能任务推荐：基于上下文变量推荐相关任务

**示例实现**:
```python
if not failed_tasks and pending_tasks:
    # 分析阻塞原因
    blocked_analysis = self._analyze_blocked_tasks(pending_tasks)
    if blocked_analysis['needs_new_tasks']:
        new_tasks = self.planner.generate_supplementary_tasks(
            self.global_state.original_goal,
            blocked_analysis,
            self.global_state
        )
        if new_tasks:
            self.task_list.extend(new_tasks)
            return True
```

**影响范围**: 提升工作流的自主性和完整性

### 4. 动态任务移除 - 计划优化功能
**位置**: `CognitiveWorkflowEngine._apply_plan_modification()` 方法  
**文件**: `cognitive_workflow.py` 第1390行  
**当前状态**: 空实现（pass）

**功能描述**:
实现运行时移除无效或不必要任务的能力。

**需要实现**:
1. 解析要移除的任务ID列表
2. 检查任务依赖关系，确保移除安全
3. 更新相关任务的先决条件
4. 从task_list中移除指定任务
5. 记录任务移除的原因和影响

**示例实现**:
```python
task_ids_to_remove = modification_decision.get('details', {}).get('task_ids', [])
for task_id in task_ids_to_remove:
    task_to_remove = next((t for t in self.task_list if t.id == task_id), None)
    if task_to_remove and task_to_remove.status == TaskStatus.PENDING:
        self.task_list.remove(task_to_remove)
        logger.info(f"移除任务: {task_id}")
```

**影响范围**: 提升计划优化能力，避免执行不必要的任务

### 5. 动态任务修改 - 计划适应功能
**位置**: `CognitiveWorkflowEngine._apply_plan_modification()` 方法  
**文件**: `cognitive_workflow.py` 第1410行  
**当前状态**: 空实现（pass）

**功能描述**:
实现运行时修改现有任务属性的能力。

**需要实现**:
1. 解析要修改的任务ID和修改内容
2. 支持修改任务的指令、先决条件、预期输出等
3. 验证修改后的任务仍然有效
4. 更新任务的updated_at时间戳
5. 记录任务修改的历史版本

**示例实现**:
```python
modifications = modification_decision.get('details', {}).get('modifications', [])
for mod in modifications:
    task_id = mod['task_id']
    task = next((t for t in self.task_list if t.id == task_id), None)
    if task and task.status == TaskStatus.PENDING:
        if 'instruction' in mod:
            task.instruction = mod['instruction']
        if 'precondition' in mod:
            task.precondition = mod['precondition']
        task.updated_at = dt.now()
        logger.info(f"修改任务: {task_id}")
```

**影响范围**: 提升计划适应性，支持任务级别的动态调整

---

## 🛠️ 实现建议

### 实现顺序推荐
1. **动态任务添加** (高优先级) - 基础功能，其他功能依赖于此
2. **智能修复任务解析** (中优先级) - 提升错误恢复能力
3. **智能补充任务生成** (中优先级) - 增强自主性
4. **动态任务移除** (中优先级) - 计划优化
5. **动态任务修改** (中优先级) - 精细调整

### 技术考虑
- 所有动态修改操作都需要考虑线程安全
- 任务ID生成需要避免冲突
- 修改操作需要完整的审计日志
- 需要验证修改后的任务列表仍然逻辑一致

### 测试策略
- 为每个功能编写单元测试
- 集成测试验证动态修改不会破坏工作流
- 性能测试确保动态操作不影响执行效率

---

## 📊 实现优先级矩阵

| 功能 | 复杂度 | 影响范围 | 用户价值 | 推荐优先级 |
|------|--------|----------|----------|------------|
| 动态任务添加 | 中 | 高 | 高 | 🔥 高 |
| 智能修复任务解析 | 中 | 中 | 高 | ⚡ 中 |
| 智能补充任务生成 | 高 | 高 | 中 | ⚡ 中 |
| 动态任务移除 | 低 | 中 | 中 | ⚡ 中 |
| 动态任务修改 | 中 | 中 | 中 | ⚡ 中 |

---

## 🎯 完成后的预期效果

实现所有TODO后，CognitiveWorkflow将具备：

- **完整的动态计划修正能力**: 可在运行时添加、移除、修改任务
- **智能错误恢复机制**: 根据错误类型生成针对性修复策略
- **自主任务补充能力**: 检测并生成缺失的必要任务
- **真正的认知工作流**: 具备自我调整和优化的能力

这将使CognitiveWorkflow成为一个真正智能的、自适应的工作流执行引擎。 