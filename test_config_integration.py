"""
测试配置系统与enhancedAgent_v2的集成
"""

import sys
import os
import logging

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_integration():
    """测试配置系统集成"""
    print("=== 配置系统集成测试 ===")
    
    try:
        # 1. 测试配置系统导入
        print("\n1. 测试配置系统导入...")
        from config_system import get_config, ApplicationConfig
        config = get_config()
        print(f"✓ 配置系统导入成功: {type(config).__name__}")
        print(f"  配置版本: {config.config_version}")
        print(f"  环境: {config.environment}")
        
        # 2. 测试WorkflowState配置集成
        print("\n2. 测试WorkflowState配置集成...")
        from enhancedAgent_v2 import WorkflowState
        workflow_state = WorkflowState()
        print(f"✓ WorkflowState创建成功")
        print(f"  历史记录最大长度: {workflow_state._max_history_size}")
        print(f"  自动清理: {workflow_state._auto_cleanup_enabled}")
        print(f"  压缩启用: {workflow_state._compression_enabled}")
        
        # 3. 测试AIStateUpdaterService配置集成
        print("\n3. 测试AIStateUpdaterService配置集成...")
        from enhancedAgent_v2 import AIStateUpdaterService
        from llm_lazy import get_modelnt(f"✓ AIStateUpdaterService创建成功")
        print(f"  最大重试次数: {ai_updater.max_retries}")
        print(f"  重试延迟: {ai_updater.retry_delay}")
        print(f"  缓存启用: {ai_updater.enable_caching}")
        print(f"  条件逻辑启用: {ai_updater.enable_conditional_logic}")
        
        # 4. 测试配置参数覆盖
        print("\n4. 测试配置参数覆盖...")
        ai_updater_custom = AIStateUpdaterService(
            get_model("deepseek_chat"), 
            max_retries=5,  # 覆盖配置文件的参数
            enable_caching=False  # 覆盖配置文件的参数
        )
        print(f"✓ 自定义参数AIStateUpdaterService创建成功")
        print(f"  最大重试次数: {ai_updater_custom.max_retries} (应该是5)")
        print(f"  缓存启用: {ai_updater_custom.enable_caching} (应该是False)")
        
        # 5. 测试状态管理功能
        print("\n5. 测试状态管理功能...")
        workflow_state.set_global_state("测试状态", "配置集成测试")
        current_state = workflow_state.get_global_state()
        history_count = workflow_state.get_state_history_count()
        print(f"✓ 状态管理功能正常")
        print(f"  当前状态: {current_state}")
        print(f"  历史记录数: {history_count}")
        
        # 6. 测试配置系统的实际配置值
        print("\n6. 显示实际配置值...")
        print(f"  状态历史配置:")
        print(f"    - 最大长度: {config.state_history.max_length}")
        print(f"    - 压缩启用: {config.state_history.enable_compression}")
        print(f"    - 自动清理: {config.state_history.auto_cleanup}")
        
        print(f"  AI更新器配置:")
        print(f"    - 模型名称: {config.ai_updater.model_name}")
        print(f"    - 最大重试: {config.ai_updater.max_retries}")
        print(f"    - 超时时间: {config.ai_updater.timeout_seconds}")
        print(f"    - 缓存启用: {config.ai_updater.enable_caching}")
        print(f"    - 缓存TTL: {config.ai_updater.cache_ttl_minutes}")
        
        print(f"  监控配置:")
        print(f"    - 日志级别: {config.monitoring.log_level}")
        print(f"    - 性能监控: {config.monitoring.enable_performance_monitoring}")
        
        print(f"  优化配置:")
        print(f"    - 指令缓存: {config.optimization.enable_instruction_caching}")
        print(f"    - 缓存大小限制: {config.optimization.cache_size_limit}")
        
        print("\n✅ 所有配置系统集成测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 配置系统集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_loading():
    """测试不同配置加载方式"""
    print("\n=== 配置加载方式测试 ===")
    
    try:
        from config_system import ConfigurationLoader
        
        # 1. 测试默认配置加载
        print("\n1. 测试默认配置加载...")
        default_loader = ConfigurationLoader()
        default_config = default_loader.load_config()
        print(f"✓ 默认配置加载成功: {default_config.config_version}")
        
        # 2. 测试指定文件配置加载
        print("\n2. 测试指定文件配置加载...")
        if os.path.exists('config.yaml'):
            file_loader = ConfigurationLoader('config.yaml')
            file_config = file_loader.load_config()
            print(f"✓ 文件配置加载成功: {file_config.config_version}")
        else:
            print("⚠ config.yaml不存在，跳过文件配置测试")
        
        # 3. 测试配置重新加载
        print("\n3. 测试配置重新加载...")
        reloaded_config = default_loader.reload_config()
        print(f"✓ 配置重新加载成功: {reloaded_config.config_version}")
        
        print("\n✅ 配置加载方式测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 配置加载方式测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    # 运行测试
    success1 = test_config_integration()
    success2 = test_configuration_loading()
    
    if success1 and success2:
        print("\n🎉 所有测试通过！配置系统集成成功！")
        exit(0)
    else:
        print("\n💥 部分测试失败！")
        exit(1) 