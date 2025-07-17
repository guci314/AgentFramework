#!/usr/bin/env python3
"""简单的模板系统测试"""

import sys
sys.path.append('.')

try:
    from enhancedAgent_v2 import PromptTemplateManager, PromptScenario
    print("🎯 测试动态模板系统")
    
    # 创建模板管理器
    manager = PromptTemplateManager()
    print(f"✅ 模板管理器初始化成功")
    
    # 列出所有模板
    templates = manager.list_templates()
    print(f"📋 加载了{len(templates)}个模板:")
    for scenario, version, description in templates:
        print(f"  - {scenario.value} v{version}: {description}")
    
    # 测试模板渲染
    test_vars = {
        'main_instruction': '创建计算器',
        'step_description': '初始化项目',
        'step_type': 'setup'
    }
    
    system_msg, user_msg = manager.render_template(PromptScenario.INITIALIZATION, test_vars)
    print(f"\n✅ 初始化模板渲染成功")
    print(f"📤 系统消息长度: {len(system_msg)}")
    print(f"📤 用户消息长度: {len(user_msg)}")
    
    print("\n🎉 动态模板系统测试完成！")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
