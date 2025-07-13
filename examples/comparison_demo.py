"""
MultiStepAgent_v2 vs TaskMasterAgent 对比演示

展示两个实现之间的差异和各自的优势。
"""

import os
import sys
from pathlib import Path
import tempfile
import shutil

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from langchain_openai import ChatOpenAI
from task_master_agent import TaskMasterAgent, AgentSpecification
from python_core import Agent
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class MockLLM:
    """模拟 LLM 用于演示"""
    def __init__(self, model_name="mock-model"):
        self.model = model_name
    
    def invoke(self, messages, **kwargs):
        class MockResponse:
            content = '{"action": "continue", "reason": "模拟演示决策"}'
        return MockResponse()


def create_demo_agents(llm):
    """创建演示用的智能体"""
    # 创建专业智能体
    architect = Agent(llm=llm, stateful=True)
    architect.api_specification = "系统架构师，负责设计系统架构和技术选型"
    
    developer = Agent(llm=llm, stateful=True)
    developer.api_specification = "开发工程师，负责代码实现和功能开发"
    
    tester = Agent(llm=llm, stateful=True)
    tester.api_specification = "测试工程师，负责质量保证和测试策略"
    
    devops = Agent(llm=llm, stateful=True)
    devops.api_specification = "DevOps工程师，负责部署和运维工作"
    
    return [
        AgentSpecification("architect", architect, "系统架构师"),
        AgentSpecification("developer", developer, "开发工程师"),
        AgentSpecification("tester", tester, "测试工程师"),
        AgentSpecification("devops", devops, "DevOps工程师")
    ]


def demo_multistep_v2():
    """演示 MultiStepAgent_v2 的功能"""
    print("\n" + "="*60)
    print("🔹 MultiStepAgent_v2 演示")
    print("="*60)
    
    try:
        from enhancedAgent_v2 import MultiStepAgent_v2
        
        llm = MockLLM("gpt-3.5-turbo")
        agent_specs = create_demo_agents(llm)
        
        # 创建 MultiStepAgent_v2 实例
        print("📝 创建 MultiStepAgent_v2...")
        agent = MultiStepAgent_v2(
            llm=llm,
            agent_specs=agent_specs,
            max_retries=3
        )
        
        print("✅ MultiStepAgent_v2 创建成功")
        print(f"   - 注册智能体: {len(agent_specs)} 个")
        print(f"   - 执行模式: 传统模式")
        print(f"   - 任务存储: 内存中")
        
        # 展示特性
        print("\n🎯 主要特性:")
        print("   ✓ 基于 LLM 的任务规划")
        print("   ✓ 简单的先决条件检查")
        print("   ✓ 基本的工作流状态管理")
        print("   ✓ 多智能体协作执行")
        print("   ✓ 内存管理和压缩")
        
        # 模拟执行（不实际调用 API）
        instruction = "开发一个电商网站"
        print(f"\n🚀 模拟执行任务: {instruction}")
        print("   - 任务规划: 使用内置 LLM 提示词")
        print("   - 执行方式: 线性步骤执行")
        print("   - 状态管理: WorkflowState 类")
        print("   - 决策制定: 基本决策选项")
        
        return True
        
    except ImportError as e:
        print(f"❌ 无法导入 MultiStepAgent_v2: {e}")
        return False
    except Exception as e:
        print(f"❌ MultiStepAgent_v2 演示失败: {e}")
        return False


def demo_task_master_agent():
    """演示 TaskMasterAgent 的功能"""
    print("\n" + "="*60)
    print("🔸 TaskMasterAgent 演示")
    print("="*60)
    
    try:
        # 创建临时项目目录
        temp_dir = tempfile.mkdtemp(prefix="tm_demo_")
        
        llm = MockLLM("gpt-4")
        agent_specs = create_demo_agents(llm)
        
        # 创建 TaskMasterAgent 实例
        print("📝 创建 TaskMasterAgent...")
        agent = TaskMasterAgent(
            project_root=temp_dir,
            llm=llm,
            agent_specs=agent_specs,
            auto_init=True
        )
        
        print("✅ TaskMasterAgent 创建成功")
        print(f"   - 项目路径: {temp_dir}")
        print(f"   - 注册智能体: {len(agent_specs)} 个")
        print(f"   - 执行模式: 3种模式可选")
        print(f"   - 任务存储: 持久化项目结构")
        
        # 展示特性
        print("\n🎯 主要特性:")
        print("   ✓ Task Master AI 智能规划")
        print("   ✓ 复杂度分析和评估")
        print("   ✓ 强大的依赖关系管理")
        print("   ✓ 智能任务扩展")
        print("   ✓ 增强决策系统 (12种选项)")
        print("   ✓ AI 研究功能")
        print("   ✓ 项目级管理和协作")
        print("   ✓ 完整的配置系统")
        print("   ✓ 双向状态同步")
        
        # 展示不同执行模式
        instruction = "开发一个电商网站"
        print(f"\n🚀 任务: {instruction}")
        
        print("\n📋 可用执行模式:")
        print("   1. tm_native  - Task Master AI 原生模式")
        print("      • 完全使用 Task Master AI 规划和管理")
        print("      • 智能任务分解和依赖分析")
        print("      • AI 驱动的复杂度评估")
        
        print("   2. hybrid     - 混合模式")
        print("      • Task Master AI 规划 + AgentFrameWork 执行")
        print("      • 最佳的兼容性和功能性")
        print("      • 适合渐进式迁移")
        
        print("   3. legacy     - 兼容模式")
        print("      • 调用原始 MultiStepAgent_v2 逻辑")
        print("      • 完全向后兼容")
        print("      • 用于对比和验证")
        
        # 展示高级功能
        print("\n🔬 高级功能演示:")
        
        # 项目状态
        status = agent.get_project_status()
        print(f"   📊 项目状态: {status.get('total_tasks', 0)} 个任务")
        
        # 配置管理
        config = agent.config
        print(f"   ⚙️  配置管理: 复杂度阈值 {config.get_complexity_threshold()}")
        
        # 研究功能
        print("   🔍 研究功能: 可进行 AI 辅助技术研究")
        
        # 增强决策
        print("   🧠 增强决策: 12种智能决策选项")
        
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return True
        
    except Exception as e:
        print(f"❌ TaskMasterAgent 演示失败: {e}")
        return False


def feature_comparison():
    """功能对比表"""
    print("\n" + "="*80)
    print("📊 功能对比详表")
    print("="*80)
    
    features = [
        ("特性", "MultiStepAgent_v2", "TaskMasterAgent"),
        ("-" * 25, "-" * 20, "-" * 20),
        ("任务规划", "内置 LLM 规划", "Task Master AI 智能分解"),
        ("依赖管理", "简单先决条件", "强大依赖图管理"),
        ("复杂度分析", "❌ 无", "✅ AI 驱动评估"),
        ("任务扩展", "❌ 手动", "✅ 自动智能扩展"),
        ("决策选项", "🔶 基本 (4种)", "✅ 增强 (12种)"),
        ("研究功能", "❌ 无", "✅ 内置 AI 研究"),
        ("项目管理", "🔶 内存存储", "✅ 持久化结构"),
        ("团队协作", "🔶 基础支持", "✅ 标签、分支功能"),
        ("配置管理", "🔶 简单参数", "✅ 完整配置系统"),
        ("状态同步", "❌ 无", "✅ 双向同步"),
        ("执行模式", "🔶 单一模式", "✅ 3种模式"),
        ("向后兼容", "✅ 原生", "✅ 兼容模式"),
        ("学习成本", "🔶 中等", "🔶 中等"),
        ("性能开销", "✅ 较低", "🔶 中等"),
        ("功能丰富度", "🔶 基础", "✅ 丰富"),
        ("适用场景", "简单到中等项目", "中等到复杂项目")
    ]
    
    # 打印对比表
    for feature, v2, tm in features:
        print(f"{feature:<25} | {v2:<20} | {tm}")
    
    print("\n图例:")
    print("✅ 优秀  🔶 良好  ❌ 缺失")


def usage_recommendations():
    """使用建议"""
    print("\n" + "="*60)
    print("💡 使用建议")
    print("="*60)
    
    print("\n🎯 选择 MultiStepAgent_v2 当:")
    print("   ✓ 项目相对简单，任务数量较少")
    print("   ✓ 不需要复杂的依赖管理")
    print("   ✓ 希望保持轻量级的实现")
    print("   ✓ 已有稳定的工作流程")
    print("   ✓ 不需要项目级管理功能")
    
    print("\n🎯 选择 TaskMasterAgent 当:")
    print("   ✓ 项目复杂，需要智能任务分解")
    print("   ✓ 需要强大的依赖关系管理")
    print("   ✓ 希望利用 AI 研究和决策功能")
    print("   ✓ 需要项目级管理和协作")
    print("   ✓ 希望使用最新的 Task Master AI 功能")
    
    print("\n🔄 迁移策略:")
    print("   1. 保持现有 MultiStepAgent_v2 代码不变")
    print("   2. 在新项目中试用 TaskMasterAgent")
    print("   3. 使用 TaskMasterAgent 的 legacy 模式进行对比")
    print("   4. 逐步迁移到 hybrid 或 tm_native 模式")
    print("   5. 根据项目需求选择最适合的实现")
    
    print("\n⚡ 性能考虑:")
    print("   • MultiStepAgent_v2: 更轻量，适合简单场景")
    print("   • TaskMasterAgent: 功能丰富，适合复杂项目")
    print("   • 可以在同一项目中混合使用两种实现")


def main():
    """主演示函数"""
    print("🚀 AgentFrameWork: MultiStepAgent_v2 vs TaskMasterAgent 对比演示")
    print("=" * 80)
    
    print("\n本演示将展示两种多步骤智能体实现的特性和差异:")
    print("• MultiStepAgent_v2: 传统的多步骤智能体实现")
    print("• TaskMasterAgent: 基于 Task Master AI 的新一代实现")
    
    # 检查环境
    if "OPENAI_API_KEY" not in os.environ:
        print("\n⚠️  注意: 未设置 OPENAI_API_KEY，演示将使用模拟模式")
    
    # 演示两种实现
    v2_success = demo_multistep_v2()
    tm_success = demo_task_master_agent()
    
    # 功能对比
    feature_comparison()
    
    # 使用建议
    usage_recommendations()
    
    # 总结
    print("\n" + "="*60)
    print("📝 演示总结")
    print("="*60)
    
    print(f"\n✅ MultiStepAgent_v2 演示: {'成功' if v2_success else '失败'}")
    print(f"✅ TaskMasterAgent 演示: {'成功' if tm_success else '失败'}")
    
    if v2_success and tm_success:
        print("\n🎉 两种实现都可以正常工作!")
        print("   您可以根据项目需求选择最适合的实现")
    elif tm_success:
        print("\n✨ TaskMasterAgent 可以正常工作!")
        print("   建议在新项目中使用 TaskMasterAgent")
    elif v2_success:
        print("\n🔧 只有 MultiStepAgent_v2 可用")
        print("   建议继续使用现有实现")
    else:
        print("\n❌ 两种实现都遇到了问题")
        print("   请检查环境配置和依赖安装")
    
    print("\n📚 更多信息:")
    print("   • 查看 TASK_MASTER_INTEGRATION_GUIDE.md 了解详细使用方法")
    print("   • 运行 examples/basic_task_master.py 进行实际测试")
    print("   • 查看 test_task_master_agent.py 了解测试用例")
    
    print("\n🎯 下一步建议:")
    print("   1. 根据项目复杂度选择合适的实现")
    print("   2. 在测试环境中验证功能")
    print("   3. 逐步迁移现有项目（如果需要）")
    print("   4. 探索 TaskMasterAgent 的高级功能")


if __name__ == "__main__":
    main()