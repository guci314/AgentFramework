# 技术栈

## 核心依赖
- **LangChain**: v0.1.0+ (langchain, langchain-core, langchain-openai)
- **Python AutoGen**: v0.2.0+ 用于代理生成
- **Python**: 需要 3.6+ 版本

## AI/LLM 集成
- **OpenAI**: 通过 langchain_openai.ChatOpenAI
- **Anthropic**: v0.25.0+ 用于 Claude 模型
- **Cohere**: 通过 langchain_cohere.ChatCohere
- **DeepSeek**: 通过 MCP 示例集成

## Token 管理
- **tiktoken**: v0.5.0+ 用于精确的 token 计数

## 执行环境
- **IPython**: v8.0.0+ 用于代码执行
- **Jupyter**: v1.0.0+ 用于笔记本支持

## HTTP 和网络
- **httpx**: v0.24.0+ 用于 HTTP 请求
- **requests**: v2.31.0+ 用于通用 HTTP 操作

## 工具和实用程序
- **beautifulsoup4**: v4.12.0+ 用于 HTML 解析
- **google-api-python-client**: v2.0.0+ 用于 Google APIs
- **python-dotenv**: v1.0.0+ 用于环境变量

## 测试
- **pytest**: 用于单元和集成测试
- **coverage**: 用于代码覆盖率分析
- **unittest**: Python 标准测试框架

## 配置
- 基于 YAML 的配置（config.yaml）
- 环境变量支持（.env 文件）
- SQLite 用于 LLM 响应缓存