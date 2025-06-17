#!/usr/bin/env python3
"""
使用 DeepSeek API 测试修复后的 TaskMaster 系统
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from task_master_agent import TaskMasterAgent, AgentSpecification
from pythonTask import Agent
from langchain_openai import ChatOpenAI
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_deepseek_llm():
    """创建 DeepSeek LLM 客户端"""
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        raise ValueError("未设置 DEEPSEEK_API_KEY 环境变量")
    
    # 使用 DeepSeek 官方 API
    llm = ChatOpenAI(
        temperature=0,
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key=api_key,
    )
    return llm


def create_deepseek_agents():
    """创建使用 DeepSeek 的智能体"""
    llm = create_deepseek_llm()
    
    # 创建编程智能体
    coder_agent = Agent(llm=llm, stateful=True)
    coder_agent.api_specification = "专门负责编程和代码实现的智能体，擅长Python、JavaScript等编程语言"
    
    # 创建测试智能体  
    tester_agent = Agent(llm=llm, stateful=True)
    tester_agent.loadKnowledge('unittest的输出在标准错误流，不是标准输出流')
    tester_agent.api_specification = "专门负责软件测试的智能体，擅长单元测试、集成测试和测试策略"
    
    # 创建文档智能体
    doc_agent = Agent(llm=llm, stateful=True)
    doc_agent.api_specification = "专门负责文档编写的智能体，擅长技术文档、API文档和用户手册"
    
    return [
        AgentSpecification("coder", coder_agent, "编程实现智能体"),
        AgentSpecification("tester", tester_agent, "软件测试智能体"),
        AgentSpecification("doc_writer", doc_agent, "文档编写智能体")
    ]


def test_taskmaster_with_deepseek():
    """使用 DeepSeek 测试 TaskMaster 系统"""
    print("🧠 使用 DeepSeek API 测试 TaskMaster 系统")
    print("=" * 60)
    
    try:
        # 1. 测试 DeepSeek 连接
        print("🔗 测试 DeepSeek API 连接...")
        llm = create_deepseek_llm()
        
        # 简单测试
        from langchain_core.messages import HumanMessage
        test_response = llm.invoke([HumanMessage(content="你好，请回复'DeepSeek 连接成功'")])
        print(f"✅ DeepSeek 响应: {test_response.content}")
        
        # 2. 创建项目目录
        project_dir = Path("./test_project_deepseek")
        project_dir.mkdir(exist_ok=True)
        print(f"📁 项目目录: {project_dir.resolve()}")
        
        # 3. 创建智能体
        print("\n🤖 创建 DeepSeek 智能体...")
        agent_specs = create_deepseek_agents()
        print(f"✅ 创建了 {len(agent_specs)} 个智能体:")
        for spec in agent_specs:
            print(f"   - {spec.name}: {spec.description}")
        
        # 4. 初始化 TaskMasterAgent
        print("\n⚙️ 初始化 TaskMasterAgent...")
        tm_agent = TaskMasterAgent(
            project_root=str(project_dir),
            llm=llm,
            agent_specs=agent_specs,
            auto_init=True
        )
        print("✅ TaskMasterAgent 初始化完成")
        
        # 5. 查看项目状态
        print("\n📊 查看项目状态...")
        status = tm_agent.get_project_status()
        print(f"📋 项目状态: {status}")
        
        # 6. 执行计算器任务
        print("\n🚀 执行多步骤任务...")
        # main_instruction = "创建一个简单的计算器应用，包含基本的加减乘除功能"
        main_instruction = "调用coder智能体，用python写一个hello world函数，要包含单元测试。保存到hello_world.py文件中。然后调用tester智能体运行这个文件验证单元测试通过"
        print(f"📝 任务指令: {main_instruction}")
        
        result = tm_agent.execute_multi_step(
            main_instruction=main_instruction,
            mode="tm_native",
            use_prd=False
        )
        
        print(f"\n📊 执行结果:")
        print(result)
        
        # 7. 查看生成的任务文件
        print("\n📁 查看生成的任务...")
        tasks_file = project_dir / ".taskmaster" / "tasks" / "tasks.json"
        if tasks_file.exists():
            import json
            with open(tasks_file, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
            
            tasks = tasks_data.get("master", {}).get("tasks", [])
            print(f"✅ 共生成 {len(tasks)} 个任务:")
            for task in tasks:
                print(f"   - 任务 {task.get('id')}: {task.get('title')}")
                print(f"     状态: {task.get('status')}")
                print(f"     分配给: {task.get('agent_name', 'N/A')}")
                print(f"     创建时间: {task.get('created', 'N/A')}")
                print()
        
        print("\n🎉 DeepSeek 测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"DeepSeek 测试失败: {e}")
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_taskmaster_with_deepseek()
    if success:
        print("\n🎯 TaskMaster + DeepSeek 系统测试成功！")
    else:
        print("\n💥 TaskMaster + DeepSeek 系统测试失败！")
        sys.exit(1)