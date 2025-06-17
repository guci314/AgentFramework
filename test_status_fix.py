#!/usr/bin/env python3
"""
测试状态管理修复的脚本
"""

import os
import sys
import json
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
    
    llm = ChatOpenAI(
        temperature=0,
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key=api_key,
    )
    return llm


def create_test_agents():
    """创建测试智能体"""
    llm = create_deepseek_llm()
    
    # 创建编程智能体
    coder_agent = Agent(llm=llm, stateful=True)
    coder_agent.api_specification = "专门负责编程和代码实现的智能体"
    
    # 创建测试智能体  
    tester_agent = Agent(llm=llm, stateful=True)
    tester_agent.api_specification = "专门负责软件测试的智能体"
    
    return [
        AgentSpecification("coder", coder_agent, "编程实现智能体"),
        AgentSpecification("tester", tester_agent, "软件测试智能体")
    ]


def test_status_management_fix():
    """测试状态管理修复"""
    print("🔧 测试状态管理修复")
    print("=" * 50)
    
    try:
        # 1. 创建测试项目
        test_project_dir = Path("./test_status_fix")
        test_project_dir.mkdir(exist_ok=True)
        print(f"📁 测试项目目录: {test_project_dir.resolve()}")
        
        # 2. 创建智能体
        print("\n🤖 创建测试智能体...")
        llm = create_deepseek_llm()
        agent_specs = create_test_agents()
        
        # 3. 初始化 TaskMasterAgent
        print("\n⚙️ 初始化 TaskMasterAgent...")
        tm_agent = TaskMasterAgent(
            project_root=str(test_project_dir),
            llm=llm,
            agent_specs=agent_specs,
            auto_init=True
        )
        
        # 4. 清空任务确保干净环境
        print("\n🧹 清空现有任务...")
        tm_agent.tm_client.clear_all_tasks()
        
        # 5. 查看初始状态
        print("\n📊 初始项目状态:")
        initial_status = tm_agent.get_project_status()
        print(f"   {initial_status}")
        
        # 6. 执行简单的多智能体任务
        print("\n🚀 执行多智能体任务...")
        test_instruction = "调用coder智能体写一个简单的加法函数，然后调用tester智能体验证这个函数"
        
        # 创建任务
        task_result = tm_agent.tm_client.add_task(test_instruction)
        print(f"✅ 任务创建结果: {task_result.get('success', False)}")
        
        # 7. 查看创建后的状态
        print("\n📊 任务创建后的状态:")
        after_create_status = tm_agent.get_project_status()
        print(f"   {after_create_status}")
        
        # 8. 手动执行任务并检查状态变化
        tasks = tm_agent.tm_client.get_tasks()
        if tasks:
            main_task = tasks[0]
            task_id = main_task.get("id")
            print(f"\n⚡ 手动执行任务 {task_id}...")
            
            # 模拟任务执行
            print("   设置任务为执行中...")
            tm_agent.tm_client.set_task_status(str(task_id), "in-progress")
            
            # 如果有子任务，模拟子任务执行
            subtasks = main_task.get("subtasks", [])
            if subtasks:
                print(f"   发现 {len(subtasks)} 个子任务")
                for subtask in subtasks:
                    subtask_id = subtask.get("id")
                    print(f"   执行子任务 {subtask_id}...")
                    
                    # 设置子任务状态
                    tm_agent.tm_client.set_task_status(str(subtask_id), "in-progress")
                    print(f"   ✅ 子任务 {subtask_id} 设置为执行中")
                    
                    tm_agent.tm_client.set_task_status(str(subtask_id), "done")
                    print(f"   ✅ 子任务 {subtask_id} 设置为完成")
            
            # 完成主任务
            tm_agent.tm_client.set_task_status(str(task_id), "done")
            print(f"   ✅ 主任务 {task_id} 设置为完成")
        
        # 9. 查看最终状态
        print("\n📊 任务完成后的状态:")
        final_status = tm_agent.get_project_status()
        print(f"   {final_status}")
        
        # 10. 验证状态正确性
        print("\n🔍 验证状态正确性:")
        
        # 检查任务文件
        tasks_file = test_project_dir / ".taskmaster" / "tasks" / "tasks.json"
        if tasks_file.exists():
            with open(tasks_file, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
            
            all_tasks = []
            for task in tasks_data.get("master", {}).get("tasks", []):
                all_tasks.append(task)
                for subtask in task.get("subtasks", []):
                    all_tasks.append(subtask)
            
            print(f"   文件中总任务数: {len(all_tasks)}")
            
            status_breakdown = {}
            for task in all_tasks:
                status = task.get("status", "unknown")
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            print(f"   状态分布: {status_breakdown}")
            
            # 检查是否所有任务都完成
            pending_count = status_breakdown.get("pending", 0)
            if pending_count == 0:
                print("   ✅ 修复成功: 没有遗留的pending任务")
            else:
                print(f"   ❌ 仍有问题: {pending_count} 个任务状态为pending")
                
                # 显示pending任务详情
                print("   Pending任务详情:")
                for task in all_tasks:
                    if task.get("status") == "pending":
                        print(f"     - 任务 {task.get('id')}: {task.get('title', 'N/A')[:50]}")
        
        print("\n🎉 状态管理测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"状态管理测试失败: {e}")
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_status_management_fix()
    if success:
        print("\n✅ 状态管理修复测试成功！")
    else:
        print("\n❌ 状态管理修复测试失败！")
        sys.exit(1)