# AgentFrameWork

## 安全配置指南
### API密钥配置
本项目使用环境变量来管理API密钥，确保敏感信息不会被提交到代码仓库。
#### 配置步骤:
1. 复制配置文件: cp .env.example .env
2. 编辑.env文件，填入您的真实API密钥
3. 安装依赖: pip install python-dotenv

### 重要提醒:
- 绝对不要将.env文件提交到git仓库
- 绝对不要在代码中硬编码API密钥
- .env文件已被添加到.gitignore中
