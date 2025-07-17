#!/usr/bin/env python3
"""
调试工作流中的AI评估数据传递
==========================

在工作流执行过程中添加日志来查看AI评估器接收到的具体数据。
"""

import os
import logging
from static_workflow.control_flow_evaluator import ControlFlowEvaluator
from static_workflow.result_evaluator import MockTestResultEvaluator
from agent_base import Result

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DebugMockTestResultEvaluator(MockTestResultEvaluator):
    """调试版本的MockTestResultEvaluator，添加详细日志"""
    
    def evaluate_test_result(self, **kwargs) -> dict:
        """模拟评估逻辑，添加详细日志"""
        
        logger.info("=" * 60)
        logger.info("🤖 AI评估器被调用")
        logger.info("=" * 60)
        
        # 记录所有输入参数
        for key, value in kwargs.items():
            logger.info(f"参数 {key}: {repr(value)}")
        
        # 获取输出信息
        stdout = kwargs.get("result_stdout", "")
        stderr = kwargs.get("result_stderr", "")
        return_value = kwargs.get("result_return_value", "")
        code = kwargs.get("result_code", "")
        
        logger.info(f"处理后的数据:")
        logger.info(f"  stdout: {repr(stdout)}")
        logger.info(f"  stderr: {repr(stderr)}")
        logger.info(f"  return_value: {repr(return_value)}")
        logger.info(f"  code: {repr(code)}")
        
        # 调用原始评估逻辑
        result = super().evaluate_test_result(**kwargs)
        
        logger.info(f"评估结果:")
        logger.info(f"  passed: {result['passed']}")
        logger.info(f"  confidence: {result['confidence']}")
        logger.info(f"  reason: {result['reason']}")
        logger.info(f"  details: {result['details']}")
        logger.info("=" * 60)
        
        return result


def test_debug_evaluator():
    """测试调试版本的评估器"""
    
    print("🧪 测试调试版本的AI评估器")
    print("=" * 60)
    
    # 创建测试数据
    test_result = Result(
        success=True,
        code="python -m unittest test_calculator.py -v",
        stdout="",
        stderr="test_add (test_calculator.TestCalculator) ... ok\ntest_divide (test_calculator.TestCalculator) ... ok\ntest_divide_by_zero (test_calculator.TestCalculator) ... ok\ntest_multiply (test_calculator.TestCalculator) ... ok\ntest_subtract (test_calculator.TestCalculator) ... ok\n\n----------------------------------------------------------------------\nRan 5 tests in 0.000s\n\nOK\n",
        return_value=0
    )
    
    # 创建调试评估器
    debug_evaluator = DebugMockTestResultEvaluator()
    
    # 测试评估
    result = debug_evaluator.evaluate_test_result(
        result_code=test_result.code,
        result_stdout=test_result.stdout,
        result_stderr=test_result.stderr,
        result_return_value=test_result.return_value
    )
    
    print(f"最终结果: {'通过' if result['passed'] else '失败'}")


def create_debug_control_flow_evaluator():
    """创建带调试功能的ControlFlowEvaluator"""
    
    debug_ai_evaluator = DebugMockTestResultEvaluator()
    evaluator = ControlFlowEvaluator(ai_evaluator=debug_ai_evaluator)
    
    return evaluator


if __name__ == "__main__":
    test_debug_evaluator()