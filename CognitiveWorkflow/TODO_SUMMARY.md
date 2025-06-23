# CognitiveWorkflow TODO 完整指南

本文档提供 CognitiveWorkflow 模块的完整TODO管理，包括进度跟踪、技术实现指南和详细规格说明。

## 📊 项目概览

### 整体进度
- **总计功能**: 5个
- **已完成**: 1个 ✅ (20%)
- **待实现**: 4个 ⏳ (80%)
- **高优先级**: 1个 (架构重构)
- **中优先级**: 3个 (功能增强)

### 最新进展
**🎉 动态任务添加功能已完成实现！** (2024-12-21)

---

## 📍 功能状态总览

| 序号 | 功能名称 | 位置 | 优先级 | 复杂度 | 状态 | 完成日期 |
|------|----------|------|--------|--------|------|----------|
| 1 | 动态任务添加 | `_apply_plan_modification()` 1428行 | 高 | 中 | ✅ **已完成** | 2024-12-21 |
| 2 | **架构重构：认知管理者** | 整体架构 | **高** | **高** | ⏳ **待实现** | - |
| 3 | 智能补充任务生成 | `_handle_no_executable_tasks()` 1403行 | 中 | 高 | ⏳ 待实现 | - |
| 4 | 动态任务移除 | `_apply_plan_modification()` 1444行 | 中 | 低 | ⏳ 待实现 | - |
| 5 | 动态任务修改 | `_apply_plan_modification()` 1448行 | 中 | 中 | ⏳ 待实现 | - |

---

## ✅ 已完成功能详情

### 1. 动态任务添加 - 计划修正的核心功能
**完成状态**: ✅ **已实现** (2024-12-21)  
**位置**: `CognitiveWorkflowEngine._apply_plan_modification()` 方法  
**文件**: `cognitive_workflow.py` 第1428行

#### 功能描述
实现运行时动态添加新任务的能力，这是计划修正机制的核心功能。

#### 已实现功能
1. ✅ 解析modification_decision中的新任务数据
2. ✅ 创建CognitiveTask对象并添加到task_list
3. ✅ 验证新任务的有效性（agent存在、先决条件合理等）
4. ✅ 重新计算任务ID以避免冲突（微秒级时间戳）
5. ✅ 记录任务添加的审计日志

#### 实现方法
- `_add_dynamic_tasks()` - 主要实现逻辑
- `_generate_dynamic_task_id()` - ID生成器
- `_validate_new_task_data()` - 数据验证
- `_create_cognitive_task_from_data()` - 任务对象创建

#### 主要特性
- 支持运行时动态添加新任务到认知工作流
- 4层数据验证机制（必填字段、智能体存在性、任务阶段、指令类型）
- 微秒级时间戳ID生成，确保唯一性
- 详细的错误处理和日志记录
- 与现有工作流系统无缝集成

#### 测试状态
- ✅ 单元测试：11/11 通过
- ✅ 集成测试：1/1 通过
- ✅ 功能完整性验证通过

#### 文档
- 详细设计文档：`docs_task/动态任务添加.md`

#### 影响范围
影响工作流的动态适应能力，是实现真正智能工作流的关键

---

## ⏳ 待实现功能详情

### 2. 架构重构：认知管理者 - 统一任务管理
**优先级**: 高 | **复杂度**: 高 | **状态**: ⏳ 待实现

**位置**: 整体架构重构  
**影响文件**: `cognitive_workflow.py` 全文  
**当前状态**: CognitivePlanner和CognitiveDecider职责重叠，需要合并

#### 功能描述
将CognitivePlanner（规划者）和CognitiveDecider（决策者）合并为CognitiveManager（认知管理者），统一任务管理职责。

#### 重构目标
1. **消除职责重叠**：两个组件都在生成任务，存在代码重复
2. **简化架构**：从3个核心组件减少到2个（Manager + Executor）
3. **提高代码复用**：统一任务生成、LLM调用、JSON解析逻辑
4. **便于维护**：相关功能集中在一个类中

#### 需要实现
1. 创建CognitiveManager类，整合两个组件的功能
2. 迁移任务生成逻辑：`generate_initial_tasks()`, `generate_recovery_tasks()`, `generate_dynamic_tasks()`
3. 迁移决策逻辑：`find_executable_tasks()`, `select_next_task()`, `evaluate_workflow_status()`
4. 提取公共工具方法：`_generate_tasks_from_prompt()`, `_create_task_from_data()`
5. 更新CognitiveWorkflowEngine以使用新的管理者
6. 编写完整的测试用例确保功能不丢失

#### 设计文档
详细设计方案：`认知管理者重构设计文档.md`

#### 影响范围
这是一个重大架构变更，影响整个认知工作流系统的核心结构

---

### 3. 智能补充任务生成 - 增强复杂场景处理能力
**优先级**: 中 | **复杂度**: 高 | **状态**: ⏳ 待实现

**位置**: `CognitiveWorkflowEngine._handle_no_executable_tasks()` 方法  
**文件**: `cognitive_workflow.py` 第1403行  
**当前状态**: 仅处理失败任务的修复，无法生成新的补充任务

#### 功能描述
当没有可执行任务时，智能分析并生成必要的补充任务。

#### 需要实现
1. 基于当前状态和原始目标分析缺失的任务
2. 检测是否需要额外的信息收集任务
3. 生成前置条件准备任务（如环境配置、依赖安装）
4. 支持目标细化：将模糊目标分解为具体任务
5. 智能任务推荐：基于上下文变量推荐相关任务

#### 示例实现
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

#### 影响范围
提升工作流的自主性和完整性

---

### 4. 动态任务移除 - 计划优化功能
**优先级**: 中 | **复杂度**: 低 | **状态**: ⏳ 待实现

**位置**: `CognitiveWorkflowEngine._apply_plan_modification()` 方法  
**文件**: `cognitive_workflow.py` 第1444行  
**当前状态**: 空实现（pass）

#### 功能描述
实现运行时移除无效或不必要任务的能力。

#### 需要实现
1. 解析要移除的任务ID列表
2. 检查任务依赖关系，确保移除安全
3. 更新相关任务的先决条件
4. 从task_list中移除指定任务
5. 记录任务移除的原因和影响

#### 示例实现
```python
task_ids_to_remove = modification_decision.get('details', {}).get('task_ids', [])
for task_id in task_ids_to_remove:
    task_to_remove = next((t for t in self.task_list if t.id == task_id), None)
    if task_to_remove and task_to_remove.status == TaskStatus.PENDING:
        self.task_list.remove(task_to_remove)
        logger.info(f"移除任务: {task_id}")
```

#### 影响范围
提升计划优化能力，避免执行不必要的任务

---

### 5. 动态任务修改 - 计划适应功能
**优先级**: 中 | **复杂度**: 中 | **状态**: ⏳ 待实现

**位置**: `CognitiveWorkflowEngine._apply_plan_modification()` 方法  
**文件**: `cognitive_workflow.py` 第1448行  
**当前状态**: 空实现（pass）

#### 功能描述
实现运行时修改现有任务属性的能力。

#### 需要实现
1. 解析要修改的任务ID和修改内容
2. 支持修改任务的指令、先决条件、预期输出等
3. 验证修改后的任务仍然有效
4. 更新任务的updated_at时间戳
5. 记录任务修改的历史版本

#### 示例实现
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

#### 影响范围
提升计划适应性，支持任务级别的动态调整

---

## 🛠️ 实现指南

### 推荐实现顺序
1. ~~**动态任务添加** (高优先级)~~ ✅ **已完成**
2. **🔥 架构重构：认知管理者** (高优先级) - 统一架构，消除重复
3. **智能补充任务生成** (中优先级) - 增强自主性
4. **动态任务移除** (中优先级) - 计划优化
5. **动态任务修改** (中优先级) - 精细调整

### 技术考虑
- 所有动态修改操作都需要考虑线程安全
- 任务ID生成需要避免冲突 ✅ (已解决，使用微秒级时间戳)
- 修改操作需要完整的审计日志 ✅ (动态任务添加已实现)
- 需要验证修改后的任务列表仍然逻辑一致

### 测试策略
- 为每个功能编写单元测试 ✅ (动态任务添加已完成)
- 集成测试验证动态修改不会破坏工作流 ✅ (动态任务添加已完成)
- 性能测试确保动态操作不影响执行效率

---

## 📊 优先级分析矩阵

| 功能 | 复杂度 | 影响范围 | 用户价值 | 推荐优先级 | 状态 |
|------|--------|----------|----------|------------|------|
| 动态任务添加 | 中 | 高 | 高 | 🔥 高 | ✅ 已完成 |
| 架构重构：认知管理者 | 高 | 极高 | 高 | 🔥 高 | ⏳ 待实现 |
| 智能补充任务生成 | 高 | 高 | 高 | ⚡ 中 | ⏳ 待实现 |
| 动态任务移除 | 低 | 中 | 中 | ⚡ 中 | ⏳ 待实现 |
| 动态任务修改 | 中 | 中 | 中 | ⚡ 中 | ⏳ 待实现 |

---

## 🧪 测试验证状态

### 已完成测试
- ✅ **动态任务添加功能**
  - 单元测试：11/11 通过
  - 集成测试：1/1 通过
  - 功能完整性验证通过

### 待测试功能
- ⏳ 智能补充任务生成 - 待实现后测试
- ⏳ 动态任务移除 - 待实现后测试
- ⏳ 动态任务修改 - 待实现后测试

### 整体系统验证
- ✅ 代码添加 TODO 标注后仍能正常运行
- ✅ 所有未实现方法都已标注
- ✅ 演示程序运行成功，100% 成功率
- ✅ 系统功能完整性未受影响
- ✅ **动态任务添加功能完整测试通过**

---

## 🎯 项目愿景

### 当前状态
**进度**: 20% 完成 (1/5 功能已实现)

### 完成后的预期效果
实现所有TODO后，CognitiveWorkflow将具备：

- ✅ **完整的动态计划修正能力**: 可在运行时添加、移除、修改任务 (添加功能已完成，包含修复任务能力)
- **自主任务补充能力**: 检测并生成缺失的必要任务
- **真正的认知工作流**: 具备自我调整和优化的能力

这将使CognitiveWorkflow成为一个真正智能的、自适应的工作流执行引擎。

---

## 📋 TODO标注规范

每个 TODO 标注包含：
- **优先级标识**: `[优先级：高/中/低]`
- **功能名称**: 简明的功能描述
- **当前状态**: 说明现有实现程度
- **需要实现**: 详细的实现要求列表
- **示例实现**: 具体的代码实现示例
- **影响范围**: 说明对系统的影响

---

## 📚 相关文档

- 动态任务添加详细设计：`docs_task/动态任务添加.md`
- 核心理念文档：`认知工作流的核心理念.md`
- 项目架构：`DIRECTORY_GUIDE.md`

---

## 📈 更新日志

- **2024-12-21**: 动态任务添加功能实现完成
- **2024-12-21**: TODO文档合并完成
- **2024-12-21**: 测试验证通过，功能可投入使用

---

## 🔧 架构优化建议

### 修复任务机制简化
**发现**: 当前系统存在两套修复机制，存在功能重叠：

1. **传统修复机制**: `_handle_task_failure()` → `planner.generate_recovery_tasks()`
2. **动态任务添加**: `plan_modification_decision()` → 智能分析并添加修复任务

**建议**: 
- **保留动态任务添加的修复能力**：更智能、更灵活，能根据上下文做出更好的修复决策
- **简化传统修复机制**：可以将 `_handle_task_failure()` 改为调用动态任务添加机制，避免代码重复
- **统一修复策略**：所有修复任务都通过动态任务添加机制生成，确保一致性

**优势**:
- 消除代码重复
- 统一修复逻辑
- 更智能的修复决策
- 更好的可维护性

这个优化可以在架构重构时一并实现。

---

**最后更新**: 2024-12-21  
**代码行数**: ~1757行  
**测试状态**: ✅ 通过  
**项目状态**: 积极开发中 