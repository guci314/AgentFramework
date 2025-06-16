# Task Master AI 常见问题解答 (FAQ)

## 安装和配置问题

### Q1: 如何安装Task Master AI？

**A:** Task Master AI可以通过npm全局安装：

```bash
npm install -g task-master-ai
```

如果遇到权限问题，可以使用：
```bash
sudo npm install -g task-master-ai
```

或者配置npm使用不需要sudo的目录。

### Q2: 初始化项目失败，显示"Permission denied"

**A:** 这通常是权限问题：

1. 确保当前目录有写权限
2. 使用 `ls -la` 检查目录权限
3. 如果需要，使用 `chmod 755 .` 给予适当权限

### Q3: 如何配置AI模型和API密钥？

**A:** 使用以下步骤配置：

```bash
# 交互式配置
task-master models --setup

# 查看当前配置
task-master models

# 设置特定模型
task-master models --set-main="gpt-4" --set-research="perplexity-llama-3.1-sonar-large-128k-online"
```

API密钥需要在以下位置配置：
- CLI使用：项目根目录的 `.env` 文件
- MCP使用：`.cursor/mcp.json` 文件的 `env` 部分

### Q4: 支持哪些AI模型？

**A:** Task Master AI支持多种AI模型：

- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3-sonnet, Claude-3-haiku
- **Google**: Gemini-pro
- **Perplexity**: 各种在线研究模型
- **Ollama**: 本地模型支持
- **OpenRouter**: 通过OpenRouter访问的模型

## 使用问题

### Q5: 任务分解不准确怎么办？

**A:** 可以尝试以下方法：

1. **使用研究模式**：
   ```bash
   task-master expand --id 1 --research
   ```

2. **提供更详细的上下文**：
   ```bash
   task-master expand --id 1 --prompt "这是一个React前端项目，使用TypeScript"
   ```

3. **手动调整子任务**：
   ```bash
   task-master add-subtask --parent 1 --title "具体子任务标题"
   ```

4. **清除并重新分解**：
   ```bash
   task-master clear-subtasks --id 1
   task-master expand --id 1 --force --research
   ```

### Q6: 如何处理循环依赖？

**A:** Task Master AI会自动检测循环依赖：

```bash
# 验证依赖关系
task-master validate-dependencies

# 自动修复依赖问题
task-master fix-dependencies
```

如果仍有问题，手动移除有问题的依赖：
```bash
task-master remove-dependency --id 3 --depends-on 1
```

### Q7: 任务状态管理的最佳实践是什么？

**A:** 建议的状态流程：

1. **pending** → **in-progress** → **done**
2. 使用其他状态：
   - **review**: 需要代码审查
   - **blocked**: 被阻塞等待其他条件
   - **deferred**: 延期处理
   - **cancelled**: 取消的任务

```bash
# 设置任务状态
task-master set-status --id 1 --status in-progress
```

### Q8: 如何备份和恢复任务数据？

**A:** 任务数据存储在 `.taskmaster/tasks/tasks.json` 文件中：

```bash
# 备份
cp .taskmaster/tasks/tasks.json .taskmaster/tasks/tasks.json.backup

# 恢复
cp .taskmaster/tasks/tasks.json.backup .taskmaster/tasks/tasks.json

# 重新生成任务文件
task-master generate
```

## 性能和优化问题

### Q9: AI响应太慢怎么办？

**A:** 优化AI响应速度的方法：

1. **使用更快的模型**：
   ```bash
   task-master models --set-main="gpt-3.5-turbo"
   ```

2. **减少上下文长度**：
   - 避免过长的任务描述
   - 分批处理大量任务

3. **使用本地模型**：
   ```bash
   task-master models --set-main="llama2" --ollama
   ```

4. **设置代理**（如果网络受限）：
   ```bash
   export HTTP_PROXY=http://127.0.0.1:7890
   export HTTPS_PROXY=http://127.0.0.1:7890
   ```

### Q10: 如何优化大型项目的性能？

**A:** 大型项目优化建议：

1. **使用标签分组**：
   ```bash
   task-master add-tag --name "backend"
   task-master use-tag --name "backend"
   ```

2. **分阶段管理**：
   - 只展开当前阶段的任务
   - 完成一个阶段后再展开下一个

3. **定期清理**：
   - 移除已完成且不再需要的任务
   - 整理依赖关系

## 错误处理

### Q11: "模块未找到"错误

**A:** 这通常是安装或路径问题：

```bash
# 重新安装
npm uninstall -g task-master-ai
npm install -g task-master-ai

# 或者使用npx
npx task-master-ai --version
```

### Q12: JSON格式错误

**A:** 如果tasks.json损坏：

1. **从备份恢复**（如果有）
2. **重新初始化**：
   ```bash
   rm .taskmaster/tasks/tasks.json
   task-master init
   ```

3. **手动修复JSON**：使用JSON验证工具检查语法

### Q13: API密钥错误

**A:** 检查API密钥配置：

1. **验证密钥格式**：确保没有多余的空格或字符
2. **检查权限**：确保API密钥有正确的权限
3. **测试连接**：
   ```bash
   # 测试基本功能
   task-master add-task --prompt "测试任务"
   ```

## 集成和协作

### Q14: 如何与Git集成？

**A:** 推荐的Git集成实践：

1. **提交任务文件**：
   ```bash
   git add .taskmaster/
   git commit -m "Update task management"
   ```

2. **分支工作流**：
   ```bash
   # 为功能分支创建标签
   task-master add-tag --name "feature-login" --from-branch
   ```

3. **合并策略**：处理任务冲突时使用任务移动功能

### Q15: 团队协作最佳实践？

**A:** 团队使用建议：

1. **标准化配置**：团队成员使用相同的模型配置
2. **任务命名规范**：制定统一的任务命名标准
3. **状态约定**：团队约定状态的使用规则
4. **定期同步**：定期提交和同步任务状态
5. **文档记录**：重要决策记录在任务详情中

## 高级功能

### Q16: 如何使用研究功能？

**A:** 研究功能使用方法：

```bash
# 基本研究查询
task-master research --query "React性能优化最佳实践"

# 保存到特定任务
task-master research --query "数据库设计模式" --save-to 5.2

# 包含项目上下文
task-master research --query "微服务架构" --task-ids "1,2,3" --include-project-tree
```

### Q17: 如何自定义任务模板？

**A:** 虽然Task Master AI目前没有内置模板功能，但可以：

1. **保存常用命令**为shell脚本
2. **创建标准PRD模板**用于不同类型项目
3. **使用标签**组织不同类型的任务

## 故障排除

### Q18: 命令无响应

**A:** 故障排除步骤：

1. **检查网络连接**
2. **验证API密钥**
3. **查看日志**：
   ```bash
   # 设置调试模式
   export TASKMASTER_LOG_LEVEL=debug
   task-master list
   ```

4. **重启进程**：杀死可能的僵尸进程

### Q19: 如何获取帮助？

**A:** 获取帮助的途径：

1. **内置帮助**：
   ```bash
   task-master --help
   task-master <command> --help
   ```

2. **查看版本信息**：
   ```bash
   task-master --version
   ```

3. **社区支持**：
   - GitHub Issues
   - 社区论坛
   - 官方文档

4. **调试信息**：
   ```bash
   task-master models  # 查看配置状态
   task-master validate-dependencies  # 检查数据完整性
   ```

---

## 联系和反馈

如果本FAQ没有解决您的问题，请：

1. 查看官方文档获取最新信息
2. 在GitHub上提交Issue
3. 加入用户社区讨论
4. 联系技术支持

记住提供以下信息有助于快速解决问题：
- Task Master AI版本号
- 操作系统信息
- 错误消息完整内容
- 重现问题的步骤 