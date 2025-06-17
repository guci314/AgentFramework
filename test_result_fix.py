#!/usr/bin/env python3
"""
测试修复后的Result对象支持
"""

print('测试修复后的Result对象支持...')

# 导入模块
from static_workflow.workflow_definitions import WorkflowLoader
from static_workflow.control_flow_evaluator import ControlFlowEvaluator

# 测试控制流评估器
evaluator = ControlFlowEvaluator()

# 模拟Result对象
class MockResult:
    def __init__(self, success):
        self.success = success
        self.stdout = 'test output'
        self.stderr = None
        self.code = 'test code'
        self.return_value = 'test return'

# 测试success条件
mock_result = MockResult(True)
evaluator.set_context(
    global_variables={'threshold': 0.8, 'test_coverage': 0.9},
    runtime_variables={},
    step_result=mock_result
)

# 测试条件评估
test_cases = [
    ('last_result.success == True', True),
    ('test_result.success == True', True), 
    ('returncode == 0', True),  # 应该通过转换支持
    ('last_result.success == False', False),
    ('test_result.success == True AND test_coverage >= threshold', True)
]

print('\n条件评估测试:')
all_passed = True
for condition, expected in test_cases:
    try:
        result = evaluator.evaluate_condition(condition)
        status = '✅' if result == expected else '❌'
        print(f'   {status} {condition} => {result} (期望: {expected})')
        if result != expected:
            all_passed = False
    except Exception as e:
        print(f'   ❌ {condition} => 错误: {e}')
        all_passed = False

if all_passed:
    print('\n🎉 所有条件评估测试通过!')
else:
    print('\n⚠️  部分测试失败，需要进一步调试')

# 测试工作流加载
print('\n工作流加载测试:')
loader = WorkflowLoader()
try:
    workflow = loader.load_from_file('static_workflow/workflow_examples/calculator_workflow.json')
    print(f'   ✅ 计算器工作流加载成功')
    
    # 验证条件使用success字段
    run_tests_step = None
    for step in workflow.steps:
        if step.id == 'run_tests':
            run_tests_step = step
            break
    
    if run_tests_step and run_tests_step.control_flow:
        condition = run_tests_step.control_flow.condition
        print(f'   ✅ 条件已更新为: {condition}')
        if 'success' in condition and 'True' in condition:
            print(f'   ✅ 正确使用success字段和Python布尔值')
        else:
            print(f'   ⚠️  可能仍需要调整')
    
except Exception as e:
    print(f'   ❌ 工作流加载失败: {e}')

print('\n✅ Result对象修复验证完成!')