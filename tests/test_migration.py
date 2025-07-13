#!/usr/bin/env python3
"""
测试模块迁移是否成功
验证所有测试文件都能正常导入新的模块
"""

import os
import sys
import importlib.util

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import(module_name, test_name=""):
    """测试模块导入"""
    try:
        # 动态导入模块
        spec = importlib.util.spec_from_file_location(module_name, f"{module_name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        print(f"✅ {test_name or module_name} 导入成功")
        return True
    except Exception as e:
        print(f"❌ {test_name or module_name} 导入失败: {e}")
        return False

def test_core_modules():
    """测试核心模块导入"""
    print("🔧 测试核心模块导入...")
    results = []
    
    # 测试核心模块
    results.append(test_import("python_core", "python_core (核心组件)"))
    results.append(test_import("llm_lazy", "llm_lazy (懒加载模型)"))
    results.append(test_import("agent_base", "agent_base (基础类)"))
    
    return all(results)

def test_test_modules():
    """测试测试模块导入"""
    print("\n🧪 测试测试模块导入...")
    results = []
    
    # 测试各个测试模块
    test_modules = [
        "test_device",
        "test_stateful_executor", 
        "test_basic_components",
        "test_thinker",
        "test_evaluator",
        "test_agent"
    ]
    
    for module in test_modules:
        results.append(test_import(module, f"{module} (测试模块)"))
    
    return all(results)

def test_lazy_loading():
    """测试懒加载功能"""
    print("\n⚡ 测试懒加载功能...")
    
    try:
        from llm_lazy import get_model, list_models
        
        # 测试模型列表
        models = list_models()
        print(f"✅ 模型列表获取成功，共 {len(models)} 个模型")
        
        # 测试模型获取（不需要API密钥）
        if os.getenv('DEEPSEEK_API_KEY'):
            model = get_model('deepseek_v3')
            print(f"✅ 模型获取成功: {type(model).__name__}")
        else:
            print("⚠️  跳过模型获取测试（缺少API密钥）")
        
        return True
    except Exception as e:
        print(f"❌ 懒加载测试失败: {e}")
        return False

def test_component_creation():
    """测试组件创建"""
    print("\n🏗️  测试组件创建...")
    
    try:
        # 设置临时API密钥以避免导入错误
        if not os.getenv('DEEPSEEK_API_KEY'):
            os.environ['DEEPSEEK_API_KEY'] = 'fake_key_for_testing'
        
        from python_core import Device, StatefulExecutor, Thinker, Evaluator, Agent
        from llm_lazy import get_model
        
        # 测试Device
        device = Device()
        print("✅ Device 创建成功")
        
        # 测试StatefulExecutor
        executor = StatefulExecutor()
        print("✅ StatefulExecutor 创建成功")
        
        # 测试需要LLM的组件（仅测试创建，不实际调用）
        if os.getenv('DEEPSEEK_API_KEY') and os.getenv('DEEPSEEK_API_KEY') != 'fake_key_for_testing':
            llm = get_model('deepseek_v3')
            
            thinker = Thinker(llm=llm, device=device)
            print("✅ Thinker 创建成功")
            
            evaluator = Evaluator(llm=llm, systemMessage="test")
            print("✅ Evaluator 创建成功")
            
            agent = Agent(llm=llm, stateful=True)
            print("✅ Agent 创建成功")
        else:
            print("⚠️  跳过LLM组件创建测试（缺少API密钥）")
        
        return True
    except Exception as e:
        print(f"❌ 组件创建测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Agent Framework 模块迁移测试")
    print("=" * 50)
    
    # 显示当前环境
    has_api_key = bool(os.getenv('DEEPSEEK_API_KEY')) and os.getenv('DEEPSEEK_API_KEY') != 'fake_key_for_testing'
    print(f"📍 测试环境: {'完整测试' if has_api_key else '基础测试（无API密钥）'}")
    
    # 运行测试
    results = []
    results.append(test_core_modules())
    results.append(test_test_modules())
    results.append(test_lazy_loading())
    results.append(test_component_creation())
    
    # 总结结果
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    
    test_names = ["核心模块导入", "测试模块导入", "懒加载功能", "组件创建"]
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n🎯 总体结果: {success_count}/{total_count} 测试通过")
    
    if all(results):
        print("🎉 所有测试通过！模块迁移成功！")
        return True
    else:
        print("⚠️  部分测试失败，请检查错误信息")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)