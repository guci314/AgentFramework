# Claude Code Slash Commands 教程

## 📖 概述

Claude Code 的 slash commands 是在交互式会话中控制 Claude 行为的强大工具。它们提供了快速访问各种功能的方式，从基本的会话管理到高级的项目集成。

## 🎯 命令分类

### 1. 内置命令 (Built-in Commands)

#### `/help` - 获取帮助
```bash
/help
```
- **功能**: 显示所有可用命令的帮助信息
- **使用场景**: 当你忘记某个命令的语法时

#### `/clear` - 清除会话历史
```bash
/clear
```
- **功能**: 清除当前会话的对话历史
- **使用场景**: 重新开始一个新的上下文或清理混乱的对话

#### `/model` - 选择或更改AI模型
```bash
/model
/model gpt-4
/model claude-3-5-sonnet-20241022
```
- **功能**: 查看当前模型或切换到不同的AI模型
- **使用场景**: 根据任务需要选择最适合的模型

#### `/review` - 请求代码审查
```bash
/review
/review --focus security
/review --focus performance
```
- **功能**: 对当前代码进行全面审查
- **参数**: 
  - `--focus`: 指定审查重点（security, performance, style等）
- **使用场景**: 代码完成后进行质量检查

#### `/init` - 初始化项目
```bash
/init
/init --template python
```
- **功能**: 为项目创建 CLAUDE.md 指南文件
- **参数**: 
  - `--template`: 指定项目模板类型
- **使用场景**: 新项目开始时设置项目指南

### 2. 自定义命令 (Custom Commands)

#### 项目级别命令
在项目根目录创建 `.claude/commands/` 目录：

```bash
mkdir -p .claude/commands
```

创建自定义命令文件 `.claude/commands/deploy.md`：

```markdown
---
name: deploy
description: 部署应用到生产环境
arguments:
  - name: environment
    description: 目标环境
    required: true
---

# 部署命令

请执行以下部署步骤到 {{environment}} 环境：

1. 运行测试套件
2. 构建应用
3. 部署到 {{environment}}
4. 验证部署状态

```bash
npm test
npm run build
npm run deploy:{{environment}}
npm run verify:{{environment}}
```

请确认每个步骤都成功完成。
```

使用方式：
```bash
/deploy production
/deploy staging
```

#### 个人级别命令
在用户主目录创建 `~/.claude/commands/` 目录：

```bash
mkdir -p ~/.claude/commands
```

创建个人命令文件 `~/.claude/commands/analyze.md`：

```markdown
---
name: analyze
description: 分析代码质量和性能
arguments:
  - name: file
    description: 要分析的文件路径
    required: false
---

# 代码分析

{{#if file}}
请分析文件 {{file}} 的：
{{else}}
请分析当前项目的：
{{/if}}

1. 代码质量
2. 性能瓶颈
3. 安全问题
4. 最佳实践建议
5. 重构建议

请提供具体的改进建议和代码示例。
```

使用方式：
```bash
/analyze
/analyze src/main.py
```

### 3. MCP 命令 (Model Context Protocol)

MCP 命令通过连接的服务器动态发现，格式为：
```bash
/mcp__<server-name>__<prompt-name>
```

#### 常见 MCP 命令示例

##### 文件系统操作
```bash
/mcp__filesystem__read_file path/to/file.py
/mcp__filesystem__write_file path/to/new_file.py "content"
/mcp__filesystem__list_directory src/
```

##### Git 操作
```bash
/mcp__git__status
/mcp__git__commit "feat: add new feature"
/mcp__git__branch feature/new-feature
```

##### 数据库操作
```bash
/mcp__database__query "SELECT * FROM users"
/mcp__database__schema users
```

## 💡 高级使用技巧

### 1. 命令链式调用
```bash
/clear && /model claude-3-5-sonnet-20241022 && /review --focus security
```

### 2. 命令与文件引用结合
```bash
/review src/main.py --focus performance
```

### 3. 使用变量和模板
在自定义命令中使用 Handlebars 模板语法：

```markdown
---
name: test
description: 运行测试
arguments:
  - name: pattern
    description: 测试文件模式
    required: false
    default: "*.test.js"
---

# 运行测试

```bash
npm test {{pattern}}
```

{{#if pattern}}
运行匹配模式 "{{pattern}}" 的测试文件
{{else}}
运行所有测试文件
{{/if}}
```

### 4. 条件执行
```markdown
---
name: build
description: 构建项目
arguments:
  - name: mode
    description: 构建模式
    required: false
    default: "production"
---

# 构建项目

{{#if (eq mode "development")}}
```bash
npm run build:dev
```
{{else}}
```bash
npm run build:prod
npm run optimize
```
{{/if}}
```

## 🚀 实际应用场景

### 1. 项目开发流程
```bash
# 1. 初始化项目
/init --template python

# 2. 开发过程中切换模型
/model claude-3-5-sonnet-20241022

# 3. 代码审查
/review --focus security

# 4. 部署
/deploy staging
```

### 2. 调试和测试
```bash
# 1. 分析问题
/analyze src/problematic_file.py

# 2. 运行测试
/test unit

# 3. 检查代码覆盖率
/coverage
```

### 3. 文档生成
```bash
# 1. 生成API文档
/docs --type api

# 2. 生成用户手册
/docs --type user

# 3. 更新README
/readme
```

## 📝 最佳实践

### 1. 命名约定
- 使用简短但描述性的命令名
- 避免与内置命令冲突
- 使用动词开头（如 `deploy`, `test`, `build`）

### 2. 文档编写
- 总是包含 YAML 前置元数据
- 提供清晰的描述和参数说明
- 包含使用示例

### 3. 参数设计
- 必需参数放在前面
- 提供合理的默认值
- 使用清晰的参数名称

### 4. 错误处理
```markdown
---
name: deploy
description: 部署应用
arguments:
  - name: environment
    description: 目标环境
    required: true
---

# 部署到 {{environment}}

{{#unless environment}}
❌ 错误：必须指定目标环境
使用方式：/deploy <environment>
{{else}}

{{#if (eq environment "production")}}
⚠️  警告：即将部署到生产环境，请确认所有测试都已通过
{{/if}}

开始部署到 {{environment}} 环境...
{{/unless}}
```

## 🔧 故障排除

### 1. 命令不生效
- 检查命令文件路径是否正确
- 确认 YAML 前置元数据格式正确
- 验证命令名称没有冲突

### 2. 参数传递问题
- 确认参数名称与 YAML 定义匹配
- 检查必需参数是否都提供了
- 验证参数类型是否正确

### 3. MCP 命令不可用
- 确认相关 MCP 服务器已连接
- 检查服务器配置是否正确
- 验证服务器是否正在运行

## 📚 扩展阅读

- [Claude Code 官方文档](https://docs.anthropic.com/en/docs/claude-code)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [Handlebars 模板语法](https://handlebarsjs.com/)

---

通过掌握这些 slash commands，你可以大大提高使用 Claude Code 的效率，构建更加智能和自动化的开发工作流程。