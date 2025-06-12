"""
调试工作流状态的脚本
"""

def debug_workflow_state(agent):
    """调试工作流状态"""
    print("=== 工作流状态调试 ===")
    
    # 1. 检查当前计划
    plan = agent.get_plan()
    print(f"当前计划步骤数: {len(plan)}")
    
    for i, step in enumerate(plan):
        status = step.get('status', 'unknown')
        name = step.get('name', 'unnamed')
        print(f"  步骤 {i+1}: {name} - 状态: {status}")
    
    # 2. 检查工作流状态
    print(f"\n当前步骤索引: {agent.workflow_state.current_step_index}")
    print(f"循环计数器: {agent.workflow_state.loop_counters}")
    print(f"修复计数器: {agent.workflow_state.fix_counter}")
    
    # 3. 检查下一个可执行步骤
    next_step = agent.select_next_executable_step(plan)
    if next_step:
        idx, step = next_step
        print(f"\n下一个可执行步骤: 索引{idx}, 名称: {step.get('name')}")
    else:
        print("\n没有可执行步骤")
    
    # 4. 统计步骤状态
    completed = [s for s in plan if s.get('status') == 'completed']
    failed = [s for s in plan if s.get('status') == 'failed']
    pending = [s for s in plan if s.get('status') in ['pending', None]]
    
    print(f"\n状态统计:")
    print(f"  已完成: {len(completed)}")
    print(f"  失败: {len(failed)}")
    print(f"  待执行: {len(pending)}")
    
    return {
        'plan': plan,
        'next_step': next_step,
        'stats': {
            'completed': len(completed),
            'failed': len(failed),
            'pending': len(pending)
        }
    }

# 使用示例
if __name__ == "__main__":
    # 假设你有一个 agent 实例
    # debug_info = debug_workflow_state(your_agent)
    # print("调试完成")
    pass