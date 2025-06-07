#!/usr/bin/env python3
"""
基本测试文件 - 验证AgentFrameWork是否正常工作
"""

def test_imports():
    """测试基本导入是否正常"""
    try:
        # 测试主要组件导入
        from enhancedAgent_v2 import MultiStepAgent_v2, AgentSpecification, WorkflowState
        from agent_base import AgentBase, Result
        from pythonTask import Agent, StatefulExecutor
        from mda import prompts
        from mda import ddd_framework
        
        print("✅ 所有核心组件导入成功！")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    try:
        # 创建一个简单的Result对象
        from agent_base import Result
        result = Result(True, "test_code", "success", None, "test_return")
        assert result.success == True
        
        # 创建AgentSpecification
        from enhancedAgent_v2 import AgentSpecification
        from agent_base import AgentBase
        
        # 模拟一个简单的智能体
        class MockAgent(AgentBase):
            def __init__(self):
                self.api_specification = "测试智能体"
        
        agent = MockAgent()
        spec = AgentSpecification("test_agent", agent, "测试描述")
        assert spec.name == "test_agent"
        
        print("✅ 基本功能测试通过！")
        return True
    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AgentFrameWork 测试开始...")
    print()
    
    # 测试导入
    import_ok = test_imports()
    print()
    
    # 测试基本功能
    if import_ok:
        test_basic_functionality()
    
    print()
    print("🏁 测试完成！") 