# Claude Code Slash Commands 实战示例

## 🎯 完整项目开发示例

### 场景1：创建 Python Web API 项目

#### 第1步：项目初始化
```bash
# 启动 Claude Code
claude

# 初始化项目
/init --template python

# 创建项目结构
mkdir -p src/api tests docs
```

#### 第2步：创建自定义命令
创建 `.claude/commands/setup.md`：

```markdown
---
name: setup
description: 设置Python Web API项目
arguments:
  - name: project_name
    description: 项目名称
    required: true
---

# 设置 {{project_name}} 项目

## 1. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

## 2. 安装依赖
```bash
pip install fastapi uvicorn pytest black flake8
pip freeze > requirements.txt
```

## 3. 创建基础API结构
请创建以下文件：
- `src/api/main.py` - 主应用文件
- `src/api/models.py` - 数据模型
- `src/api/routes.py` - API路由
- `tests/test_api.py` - 测试文件
```

使用命令：
```bash
/setup my_api_project
```

#### 第3步：开发和测试流程
创建 `.claude/commands/dev.md`：

```markdown
---
name: dev
description: 开发流程命令
arguments:
  - name: action
    description: 开发动作 (start|test|lint|format)
    required: true
---

# 开发流程：{{action}}

{{#if (eq action "start")}}
## 启动开发服务器
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```
访问 http://localhost:8000/docs 查看API文档

{{else if (eq action "test")}}
## 运行测试
```bash
pytest tests/ -v --cov=src
```

{{else if (eq action "lint")}}
## 代码检查
```bash
flake8 src/ tests/
```

{{else if (eq action "format")}}
## 代码格式化
```bash
black src/ tests/
```

{{else}}
❌ 未知动作：{{action}}
支持的动作：start, test, lint, format
{{/if}}
```

使用示例：
```bash
/dev start    # 启动开发服务器
/dev test     # 运行测试
/dev lint     # 代码检查
/dev format   # 格式化代码
```

## 🔧 Git 工作流示例

### 场景2：Git + CI/CD 集成

创建 `.claude/commands/git.md`：

```markdown
---
name: git
description: Git工作流命令
arguments:
  - name: action
    description: Git动作 (feature|commit|pr|release)
    required: true
  - name: name
    description: 分支名或提交信息
    required: false
---

# Git 工作流：{{action}}

{{#if (eq action "feature")}}
## 创建新功能分支
```bash
git checkout -b feature/{{name}}
git push -u origin feature/{{name}}
```

{{else if (eq action "commit")}}
## 提交代码
```bash
git add .
git commit -m "{{name}}"
git push
```

{{else if (eq action "pr")}}
## 创建Pull Request
```bash
gh pr create --title "{{name}}" --body "功能描述：{{name}}"
```

{{else if (eq action "release")}}
## 发布版本
```bash
git tag -a v{{name}} -m "Release v{{name}}"
git push origin v{{name}}
```

{{else}}
❌ 未知动作：{{action}}
支持的动作：feature, commit, pr, release
{{/if}}
```

使用示例：
```bash
/git feature user-auth          # 创建用户认证功能分支
/git commit "feat: add user authentication"  # 提交代码
/git pr "Add user authentication feature"    # 创建PR
/git release 1.0.0             # 发布版本
```

## 📊 数据分析项目示例

### 场景3：数据科学工作流

创建 `.claude/commands/data.md`：

```markdown
---
name: data
description: 数据分析命令
arguments:
  - name: task
    description: 数据任务 (clean|analyze|visualize|report)
    required: true
  - name: file
    description: 数据文件路径
    required: false
---

# 数据分析任务：{{task}}

{{#if (eq task "clean")}}
## 数据清洗
```python
import pandas as pd
import numpy as np

# 读取数据
{{#if file}}
df = pd.read_csv('{{file}}')
{{else}}
df = pd.read_csv('data/raw_data.csv')
{{/if}}

# 数据清洗步骤
df = df.dropna()                    # 删除缺失值
df = df.drop_duplicates()           # 删除重复值
df = df.reset_index(drop=True)      # 重置索引

# 保存清洗后的数据
df.to_csv('data/cleaned_data.csv', index=False)
print(f"清洗完成，数据shape: {df.shape}")
```

{{else if (eq task "analyze")}}
## 数据分析
```python
import pandas as pd
import numpy as np
from scipy import stats

# 读取数据
{{#if file}}
df = pd.read_csv('{{file}}')
{{else}}
df = pd.read_csv('data/cleaned_data.csv')
{{/if}}

# 基础统计
print("基础统计信息：")
print(df.describe())

# 相关性分析
print("\n相关性矩阵：")
print(df.corr())

# 分布分析
for col in df.select_dtypes(include=[np.number]).columns:
    print(f"\n{col} 的分布：")
    print(f"均值: {df[col].mean():.2f}")
    print(f"标准差: {df[col].std():.2f}")
    print(f"偏度: {stats.skew(df[col]):.2f}")
```

{{else if (eq task "visualize")}}
## 数据可视化
```python
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# 设置样式
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# 读取数据
{{#if file}}
df = pd.read_csv('{{file}}')
{{else}}
df = pd.read_csv('data/cleaned_data.csv')
{{/if}}

# 创建图表
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# 分布图
df.hist(ax=axes[0, 0], bins=30)
axes[0, 0].set_title('数据分布')

# 相关性热力图
sns.heatmap(df.corr(), annot=True, ax=axes[0, 1])
axes[0, 1].set_title('相关性矩阵')

# 箱线图
df.boxplot(ax=axes[1, 0])
axes[1, 0].set_title('箱线图')

# 散点图矩阵
pd.plotting.scatter_matrix(df, ax=axes[1, 1], alpha=0.5)
axes[1, 1].set_title('散点图矩阵')

plt.tight_layout()
plt.savefig('reports/data_visualization.png', dpi=300, bbox_inches='tight')
plt.show()
```

{{else if (eq task "report")}}
## 生成报告
```python
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 读取数据
{{#if file}}
df = pd.read_csv('{{file}}')
{{else}}
df = pd.read_csv('data/cleaned_data.csv')
{{/if}}

# 生成报告
report = f"""
# 数据分析报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 数据概览
- 数据量: {df.shape[0]} 行, {df.shape[1]} 列
- 数据类型: {df.dtypes.value_counts().to_dict()}

## 主要发现
{df.describe().to_string()}

## 建议
根据数据分析结果，建议采取以下行动：
1. 进一步清洗异常值
2. 特征工程优化
3. 模型训练准备
"""

# 保存报告
with open('reports/analysis_report.md', 'w', encoding='utf-8') as f:
    f.write(report)

print("报告已生成: reports/analysis_report.md")
```

{{else}}
❌ 未知任务：{{task}}
支持的任务：clean, analyze, visualize, report
{{/if}}
```

使用示例：
```bash
/data clean sales_data.csv      # 清洗数据
/data analyze                   # 分析数据
/data visualize                 # 生成可视化
/data report                    # 生成报告
```

## 🧪 测试和质量保证示例

### 场景4：自动化测试工作流

创建 `.claude/commands/qa.md`：

```markdown
---
name: qa
description: 质量保证命令
arguments:
  - name: type
    description: 测试类型 (unit|integration|e2e|performance|security)
    required: true
  - name: target
    description: 测试目标
    required: false
---

# 质量保证：{{type}}测试

{{#if (eq type "unit")}}
## 单元测试
```bash
# 运行单元测试
pytest tests/unit/ -v --cov=src --cov-report=html

# 生成覆盖率报告
open htmlcov/index.html  # Mac
# 或
start htmlcov/index.html # Windows
```

{{else if (eq type "integration")}}
## 集成测试
```bash
# 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 运行集成测试
pytest tests/integration/ -v --tb=short

# 清理测试环境
docker-compose -f docker-compose.test.yml down
```

{{else if (eq type "e2e")}}
## 端到端测试
```bash
# 启动完整环境
docker-compose up -d

# 运行端到端测试
pytest tests/e2e/ -v --html=reports/e2e_report.html

# 生成测试报告
echo "测试报告: reports/e2e_report.html"
```

{{else if (eq type "performance")}}
## 性能测试
```bash
# 使用 locust 进行性能测试
locust -f tests/performance/locustfile.py --host=http://localhost:8000

# 或使用 pytest-benchmark
pytest tests/performance/ --benchmark-only --benchmark-html=reports/benchmark.html
```

{{else if (eq type "security")}}
## 安全测试
```bash
# 依赖安全检查
safety check

# 代码安全扫描
bandit -r src/

# OWASP ZAP 扫描
zap-baseline.py -t http://localhost:8000
```

{{else}}
❌ 未知测试类型：{{type}}
支持的类型：unit, integration, e2e, performance, security
{{/if}}
```

使用示例：
```bash
/qa unit                    # 单元测试
/qa integration            # 集成测试
/qa e2e                    # 端到端测试
/qa performance            # 性能测试
/qa security               # 安全测试
```

## 📦 部署和运维示例

### 场景5：DevOps 工作流

创建 `.claude/commands/deploy.md`：

```markdown
---
name: deploy
description: 部署命令
arguments:
  - name: env
    description: 环境 (dev|staging|production)
    required: true
  - name: version
    description: 版本号
    required: false
---

# 部署到 {{env}} 环境

{{#if (eq env "dev")}}
## 开发环境部署
```bash
# 构建开发镜像
docker build -t myapp:dev .

# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 验证部署
curl http://localhost:8000/health
```

{{else if (eq env "staging")}}
## 预发布环境部署
```bash
# 运行所有测试
npm test

# 构建生产镜像
docker build -t myapp:staging .

# 推送到镜像仓库
docker push myapp:staging

# 部署到 Kubernetes
kubectl apply -f k8s/staging/

# 等待部署完成
kubectl rollout status deployment/myapp -n staging

# 验证部署
kubectl get pods -n staging
```

{{else if (eq env "production")}}
## 生产环境部署
⚠️ **警告：即将部署到生产环境**

请确认以下检查项：
- [ ] 所有测试都通过
- [ ] 代码已经过审查
- [ ] 已在staging环境验证
- [ ] 数据库迁移已准备好
- [ ] 回滚方案已准备

```bash
# 创建生产版本标签
{{#if version}}
git tag -a v{{version}} -m "Production release v{{version}}"
{{else}}
git tag -a v$(date +%Y%m%d-%H%M%S) -m "Production release $(date)"
{{/if}}

# 构建生产镜像
docker build -t myapp:production .

# 推送到生产仓库
docker push myapp:production

# 部署到生产环境
kubectl apply -f k8s/production/

# 监控部署状态
kubectl rollout status deployment/myapp -n production

# 验证部署
kubectl get pods -n production
curl https://api.myapp.com/health
```

{{else}}
❌ 未知环境：{{env}}
支持的环境：dev, staging, production
{{/if}}

## 部署后监控
```bash
# 查看应用日志
kubectl logs -f deployment/myapp -n {{env}}

# 监控资源使用
kubectl top pods -n {{env}}

# 检查服务状态
kubectl get svc -n {{env}}
```
```

使用示例：
```bash
/deploy dev                     # 部署到开发环境
/deploy staging                 # 部署到预发布环境
/deploy production 1.2.3        # 部署到生产环境
```

## 🔄 自动化工作流示例

### 场景6：CI/CD 集成

创建 `.claude/commands/ci.md`：

```markdown
---
name: ci
description: CI/CD 命令
arguments:
  - name: action
    description: CI动作 (build|test|deploy|status)
    required: true
  - name: branch
    description: 分支名
    required: false
---

# CI/CD 流水线：{{action}}

{{#if (eq action "build")}}
## 构建流水线
```bash
# 检查代码质量
npm run lint

# 运行测试
npm run test:ci

# 构建应用
npm run build

# 构建 Docker 镜像
docker build -t myapp:{{branch}} .

# 推送到镜像仓库
docker push myapp:{{branch}}
```

{{else if (eq action "test")}}
## 测试流水线
```bash
# 单元测试
npm run test:unit

# 集成测试
npm run test:integration

# 端到端测试
npm run test:e2e

# 生成测试报告
npm run test:report
```

{{else if (eq action "deploy")}}
## 部署流水线
```bash
# 部署到对应环境
{{#if (eq branch "main")}}
# 部署到生产环境
kubectl apply -f k8s/production/
{{else if (eq branch "develop")}}
# 部署到开发环境
kubectl apply -f k8s/development/
{{else}}
# 部署到特性分支环境
kubectl apply -f k8s/feature/
{{/if}}

# 验证部署
kubectl rollout status deployment/myapp
```

{{else if (eq action "status")}}
## 检查CI状态
```bash
# 查看 GitHub Actions 状态
gh workflow list

# 查看特定工作流运行状态
gh run list --workflow=ci.yml

# 查看部署状态
kubectl get deployments
```

{{else}}
❌ 未知动作：{{action}}
支持的动作：build, test, deploy, status
{{/if}}
```

使用示例：
```bash
/ci build main                  # 构建主分支
/ci test                       # 运行测试
/ci deploy feature-branch      # 部署特性分支
/ci status                     # 检查CI状态
```

## 📋 项目管理示例

### 场景7：任务和文档管理

创建 `.claude/commands/project.md`：

```markdown
---
name: project
description: 项目管理命令
arguments:
  - name: task
    description: 任务 (todo|docs|release|metrics)
    required: true
  - name: item
    description: 具体项目
    required: false
---

# 项目管理：{{task}}

{{#if (eq task "todo")}}
## TODO 管理
```bash
# 显示待办事项
cat TODO.md

# 添加新任务
echo "- [ ] {{item}}" >> TODO.md

# 显示进度
grep -c "- \[x\]" TODO.md | xargs echo "已完成："
grep -c "- \[ \]" TODO.md | xargs echo "待完成："
```

{{else if (eq task "docs")}}
## 文档管理
```bash
# 生成 API 文档
{{#if item}}
swagger-codegen generate -i {{item}} -l html2 -o docs/api/
{{else}}
swagger-codegen generate -i api/swagger.yml -l html2 -o docs/api/
{{/if}}

# 生成代码文档
pydoc -w src/

# 更新 README
echo "文档已更新：$(date)" >> README.md
```

{{else if (eq task "release")}}
## 发布管理
```bash
# 生成更新日志
{{#if item}}
git log --oneline --since="v{{item}}" > CHANGELOG.md
{{else}}
git log --oneline --since="1 week ago" > CHANGELOG.md
{{/if}}

# 创建发布标签
git tag -a v{{item}} -m "Release v{{item}}"

# 推送标签
git push origin v{{item}}

# 创建 GitHub 发布
gh release create v{{item}} --title "Release v{{item}}" --notes-file CHANGELOG.md
```

{{else if (eq task "metrics")}}
## 项目指标
```bash
# 代码统计
echo "代码行数："
find src/ -name "*.py" | xargs wc -l | tail -1

# 测试覆盖率
pytest --cov=src --cov-report=term-missing

# Git 提交统计
echo "本周提交次数："
git log --since="1 week ago" --oneline | wc -l

# 依赖更新检查
pip list --outdated
```

{{else}}
❌ 未知任务：{{task}}
支持的任务：todo, docs, release, metrics
{{/if}}
```

使用示例：
```bash
/project todo "添加用户认证功能"    # 添加待办事项
/project docs api/swagger.yml     # 生成文档
/project release 1.2.0           # 创建发布
/project metrics                 # 查看项目指标
```

## 🎯 工作流整合示例

### 完整的开发工作流

```bash
# 1. 项目初始化
/init --template python
/setup my-awesome-project

# 2. 开发新功能
/git feature user-authentication
/dev start

# 3. 开发过程中的检查
/review --focus security
/dev test
/dev lint

# 4. 提交代码
/git commit "feat: add user authentication with JWT"

# 5. 部署测试
/deploy staging
/qa integration

# 6. 创建发布
/git pr "Add user authentication feature"
/project release 1.1.0

# 7. 生产部署
/deploy production 1.1.0

# 8. 监控和维护
/ci status
/project metrics
```

这个完整的工作流展示了如何将各种 slash commands 结合起来，创建一个高效的开发、测试和部署流程。

## 💡 总结

通过这些实战示例，你可以看到 slash commands 的强大之处：

1. **标准化流程**：将复杂的操作封装成简单的命令
2. **提高效率**：减少重复性工作，自动化常见任务
3. **降低错误率**：预定义的命令减少人为错误
4. **团队协作**：统一的工作流程便于团队协作
5. **可扩展性**：可以根据项目需求创建自定义命令

开始使用这些示例，并根据你的具体需求进行调整和扩展！