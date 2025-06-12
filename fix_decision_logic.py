"""
修复决策逻辑的补丁
"""

def improved_make_decision(self, current_result, task_history=None, context=None):
    """
    改进的决策方法，避免无意义的循环
    """
    # 获取当前计划状态
    plan = self.get_plan()
    completed_steps = [s for s in plan if s.get('status') == 'completed']
    total_steps = len(plan)
    
    # 检查是否所有步骤都已完成
    if len(completed_steps) == total_steps and total_steps > 0:
        return {
            'action': 'complete',
            'reason': f'所有 {total_steps} 个步骤已成功完成',
            'new_tasks': []
        }
    
    # 检查是否有待执行步骤
    next_step = self.select_next_executable_step(plan)
    if not next_step:
        # 没有可执行步骤，但也没有全部完成，可能需要分析原因
        failed_steps = [s for s in plan if s.get('status') == 'failed']
        pending_steps = [s for s in plan if s.get('status') in ['pending', None]]
        
        if failed_steps and not pending_steps:
            # 有失败步骤，无待执行步骤
            return {
                'action': 'complete',
                'reason': f'工作流程已终止：{len(failed_steps)} 个步骤失败，无法继续执行',
                'new_tasks': []
            }
        elif not failed_steps and not pending_steps:
            # 无失败，无待执行，可能是跳过的步骤
            return {
                'action': 'complete', 
                'reason': '所有可执行步骤已完成，工作流程结束',
                'new_tasks': []
            }
    
    # 检查当前结果
    if current_result and hasattr(current_result, 'success'):
        if current_result.success:
            # 当前步骤成功，检查是否需要继续
            remaining_steps = [s for s in plan if s.get('status') not in ['completed', 'skipped', 'failed']]
            if remaining_steps:
                return {
                    'action': 'continue',
                    'reason': f'当前步骤成功完成，还有 {len(remaining_steps)} 个步骤待执行',
                    'new_tasks': []
                }
            else:
                return {
                    'action': 'complete',
                    'reason': '当前步骤成功完成，且无更多待执行步骤',
                    'new_tasks': []
                }
        else:
            # 当前步骤失败，决定如何处理
            return {
                'action': 'retry',
                'reason': '当前步骤执行失败，尝试重试',
                'new_tasks': []
            }
    
    # 默认继续执行
    return {
        'action': 'continue',
        'reason': '继续执行下一个可用步骤',
        'new_tasks': []
    }

def patch_decision_logic(agent):
    """为agent打补丁，使用改进的决策逻辑"""
    import types
    agent.make_decision = types.MethodType(improved_make_decision, agent)
    print("✅ 决策逻辑已打补丁")