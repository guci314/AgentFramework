"""
基本 TaskMasterAgent 使用示例

展示如何使用 TaskMasterAgent 进行简单的任务管理和执行。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from langchain_openai import ChatOpenAI
from task_master_agent import TaskMasterAgent, AgentSpecification
from pythonTask import Agent, llm_deepseek_openrouter
from agent_base import Result
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_agents():
    """创建示例智能体"""
    # 使用 OpenRouter 的 DeepSeek 模型
    llm = llm_deepseek_openrouter
    
    # 创建编程智能体
    coder_agent = Agent(llm=llm, stateful=True)
    coder_agent.api_specification = "专门负责编程和代码实现的智能体，擅长Python、JavaScript等编程语言"
    
    # 创建测试智能体
    tester_agent = Agent(llm=llm, stateful=True)
    tester_agent.api_specification = "专门负责软件测试的智能体，擅长单元测试、集成测试和测试策略"
    
    # 创建文档智能体
    doc_agent = Agent(llm=llm, stateful=True)
    doc_agent.api_specification = "专门负责文档编写的智能体，擅长技术文档、API文档和用户手册"
    
    return [
        AgentSpecification("coder", coder_agent, "编程实现智能体"),
        AgentSpecification("tester", tester_agent, "软件测试智能体"),
        AgentSpecification("doc_writer", doc_agent, "文档编写智能体")
    ]


def basic_usage_example():
    """基本使用示例"""
    print("=== TaskMasterAgent 基本使用示例 ===\n")
    
    try:
        # 1. 创建项目目录
        project_dir = Path("./example_project")
        project_dir.mkdir(exist_ok=True)
        
        print(f"项目目录: {project_dir.resolve()}")
        
        # 2. 创建智能体
        print("\n1. 创建智能体...")
        agent_specs = create_sample_agents()
        print(f"创建了 {len(agent_specs)} 个智能体:")
        for spec in agent_specs:
            print(f"  - {spec.name}: {spec.description}")
        
        # 3. 初始化 TaskMasterAgent
        print("\n2. 初始化 TaskMasterAgent...")
        llm = llm_deepseek_openrouter
        
        tm_agent = TaskMasterAgent(
            project_root=str(project_dir),
            llm=llm,
            agent_specs=agent_specs,
            auto_init=True
        )
        
        print("TaskMasterAgent 初始化完成")
        
        # 4. 查看项目状态
        print("\n3. 查看项目状态...")
        status = tm_agent.get_project_status()
        print(f"项目状态: {status}")
        
        # 5. 执行简单任务
        print("\n4. 执行任务 (模拟模式)...")
        
        # 注意：这里使用模拟执行，实际使用时需要配置真实的 LLM API
        main_instruction = "创建一个简单的计算器应用，包含基本的加减乘除功能"
        
        print(f"任务指令: {main_instruction}")
        print("执行模式: tm_native (Task Master AI 原生模式)")
        
        # 由于是示例，我们使用 try-catch 来处理可能的 API 错误
        try:
            result = tm_agent.execute_multi_step(
                main_instruction=main_instruction,
                mode="tm_native",
                use_prd=False
            )
            print(f"\n执行结果:\n{result}")
            
        except Exception as e:
            print(f"\n模拟执行失败 (这在示例中是正常的): {e}")
            print("在实际使用中，请确保配置了正确的 LLM API 密钥")
        
        # 6. 展示其他功能
        print("\n5. 其他功能展示...")
        
        # 研究功能示例
        print("- 研究功能:")
        try:
            research_result = tm_agent.research("Python 计算器最佳实践")
            print(f"  研究结果: {research_result[:100]}...")
        except Exception as e:
            print(f"  研究功能模拟失败: {e}")
        
        # 复杂度分析示例
        print("- 复杂度分析:")
        try:
            complexity = tm_agent.get_complexity_analysis()
            print(f"  复杂度分析: {complexity}")
        except Exception as e:
            print(f"  复杂度分析模拟失败: {e}")
        
        print("\n=== 示例完成 ===")
        
    except Exception as e:
        logger.error(f"示例执行失败: {e}")
        raise


def mixed_mode_example():
    """混合模式使用示例"""
    print("\n=== 混合模式示例 ===\n")
    
    try:
        project_dir = Path("./example_project_mixed")
        project_dir.mkdir(exist_ok=True)
        
        agent_specs = create_sample_agents()
        llm = llm_deepseek_openrouter
        
        tm_agent = TaskMasterAgent(
            project_root=str(project_dir),
            llm=llm,
            agent_specs=agent_specs,
            auto_init=True
        )
        
        # 使用混合模式：Task Master AI 规划 + AgentFrameWork 执行
        main_instruction = "开发一个待办事项管理器"
        
        print(f"任务: {main_instruction}")
        print("模式: hybrid (混合模式)")
        
        try:
            result = tm_agent.execute_multi_step(
                main_instruction=main_instruction,
                mode="hybrid",
                use_prd=False
            )
            print(f"混合模式执行结果:\n{result}")
            
        except Exception as e:
            print(f"混合模式模拟失败: {e}")
        
    except Exception as e:
        logger.error(f"混合模式示例失败: {e}")


def prd_driven_example():
    """PRD 驱动开发示例"""
    print("\n=== PRD 驱动开发示例 ===\n")
    
    # 示例 PRD 内容
    prd_content = """
产品需求文档：简单博客系统

1. 功能需求
   1.1 用户管理
       - 用户注册和登录
       - 用户资料管理
       - 权限控制

   1.2 文章管理
       - 创建、编辑、删除文章
       - 文章分类和标签
       - 草稿保存功能

   1.3 评论系统
       - 用户评论功能
       - 评论审核
       - 回复评论

2. 技术要求
   - 后端：Python Flask/Django
   - 前端：HTML/CSS/JavaScript
   - 数据库：SQLite 或 PostgreSQL
   - 部署：Docker 容器化

3. 质量要求
   - 响应时间 < 2秒
   - 支持 1000 并发用户
   - 代码测试覆盖率 > 80%
   - 完整的 API 文档
"""
    
    try:
        project_dir = Path("./example_project_prd")
        project_dir.mkdir(exist_ok=True)
        
        agent_specs = create_sample_agents()
        llm = llm_deepseek_openrouter
        
        tm_agent = TaskMasterAgent(
            project_root=str(project_dir),
            llm=llm,
            agent_specs=agent_specs,
            auto_init=True
        )
        
        print("PRD 内容:")
        print(prd_content[:300] + "...")
        
        try:
            result = tm_agent.execute_multi_step(
                main_instruction="根据 PRD 开发博客系统",
                mode="tm_native",
                use_prd=True,
                prd_content=prd_content
            )
            print(f"PRD 驱动执行结果:\n{result}")
            
        except Exception as e:
            print(f"PRD 驱动模拟失败: {e}")
        
    except Exception as e:
        logger.error(f"PRD 驱动示例失败: {e}")


def configuration_example():
    """配置管理示例"""
    print("\n=== 配置管理示例 ===\n")
    
    try:
        from task_master.config import TaskMasterConfig
        
        # 创建自定义配置
        config = TaskMasterConfig()
        
        print("1. 默认配置:")
        print(f"  - 复杂度阈值: {config.get_complexity_threshold()}")
        print(f"  - 研究功能: {config.is_research_enabled()}")
        print(f"  - 自动扩展: {config.should_auto_expand_complex()}")
        
        # 修改配置
        print("\n2. 修改配置:")
        config.set("task_management.complexity_threshold", 7)
        config.set("ai_models.use_research", False)
        
        print(f"  - 新复杂度阈值: {config.get_complexity_threshold()}")
        print(f"  - 研究功能: {config.is_research_enabled()}")
        
        # 批量更新
        print("\n3. 批量更新配置:")
        config.update({
            "execution": {
                "max_retries": 5,
                "sync_frequency": "batch"
            }
        })
        
        exec_config = config.get_execution_config()
        print(f"  - 执行配置: {exec_config}")
        
        # 验证配置
        print("\n4. 配置验证:")
        is_valid = config.validate_config()
        print(f"  - 配置有效性: {is_valid}")
        
    except Exception as e:
        logger.error(f"配置管理示例失败: {e}")


if __name__ == "__main__":
    print("TaskMasterAgent 使用示例")
    print("=" * 50)
    
    # 检查环境
    if "OPENROUTER_API_KEY" not in os.environ:
        print("警告: 未设置 OPENROUTER_API_KEY 环境变量")
        print("示例将在模拟模式下运行，某些功能可能无法正常工作")
        print()
    else:
        print("已设置 OPENROUTER_API_KEY，使用真实 LLM 运行")
        print()
    
    try:
        # 运行示例
        basic_usage_example()
        mixed_mode_example()
        prd_driven_example()
        configuration_example()
        
        print("\n" + "=" * 50)
        print("所有示例执行完成!")
        print("\n使用说明:")
        print("1. 配置 OPENROUTER_API_KEY 环境变量以使用真实的 LLM")
        print("2. 查看生成的 example_project* 目录了解项目结构")
        print("3. 参考代码了解各种使用模式")
        
    except Exception as e:
        logger.error(f"示例程序失败: {e}")
        sys.exit(1)