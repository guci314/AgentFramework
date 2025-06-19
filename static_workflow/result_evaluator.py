#!/usr/bin/env python3
"""
智能测试结果评估器
使用deepseek模型判断测试或验证结果是否通过
"""

import json
import logging
import os
from typing import Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class TestResultEvaluator:
    """智能测试结果评估器"""
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.deepseek.com"):
        """
        初始化评估器
        
        Args:
            api_key: DeepSeek API密钥，如不提供则从环境变量DEEPSEEK_API_KEY获取
            base_url: DeepSeek API基础URL
        """
        if api_key is None:
            api_key = os.getenv('DEEPSEEK_API_KEY')
        
        if not api_key:
            raise ValueError("未提供DeepSeek API密钥，请设置DEEPSEEK_API_KEY环境变量或传递api_key参数")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = "deepseek-chat"
    
    def evaluate_test_result(self, 
                           result_code: str = None,
                           result_stdout: str = None, 
                           result_stderr: str = None,
                           result_return_value: str = None,
                           context: str = None) -> Dict[str, Any]:
        """
        使用deepseek模型判断测试结果是否通过
        
        Args:
            result_code: 执行的代码
            result_stdout: 标准输出
            result_stderr: 错误输出
            result_return_value: 返回值
            context: 额外上下文信息
            
        Returns:
            Dict包含判断结果: {
                "passed": bool,           # 测试是否通过
                "confidence": float,      # 置信度 (0-1)
                "reason": str,           # 判断理由
                "test_type": str,        # 识别的测试类型
                "details": dict          # 详细分析
            }
        """
        
        # 构建分析提示
        analysis_prompt = self._build_analysis_prompt(
            result_code, result_stdout, result_stderr, result_return_value, context
        )
        
        try:
            # 调用deepseek进行分析
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的测试结果分析专家，能够准确判断各种类型的测试、验证、构建结果是否成功。"
                    },
                    {
                        "role": "user", 
                        "content": analysis_prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=1000
            )
            
            # 解析JSON响应
            result_json = json.loads(response.choices[0].message.content)
            
            # 验证响应格式并设置默认值
            return self._validate_and_normalize_response(result_json)
            
        except Exception as e:
            logger.error(f"DeepSeek评估失败: {e}")
            # 返回保守的fallback结果
            return {
                "passed": False,
                "confidence": 0.1,
                "reason": f"AI评估失败，fallback判断: {str(e)}",
                "test_type": "unknown",
                "details": {
                    "error": str(e),
                    "fallback": True
                }
            }
    
    def _build_analysis_prompt(self, 
                              code: str = None,
                              stdout: str = None, 
                              stderr: str = None,
                              return_value: str = None,
                              context: str = None) -> str:
        """构建分析提示词"""
        
        prompt = """# 测试结果分析任务

请分析以下执行结果，判断测试、验证或构建是否成功通过。

**重要提示：不同测试框架的输出特性**
- unittest、pytest: 测试结果通常输出到 stderr（标准错误流）
- nose、doctest: 可能输出到 stdout 或 stderr  
- 构建工具: make、gradle 等通常输出到 stdout
- 错误信息、警告: 一般在 stderr，但不代表测试失败

## 执行信息
"""
        
        if code:
            prompt += f"""
### 执行的代码
```
{code[:1000]}{"..." if len(code) > 1000 else ""}
```
"""
        
        if stdout:
            prompt += f"""
### 标准输出 (stdout)
```
{stdout[:2000]}{"..." if len(stdout) > 2000 else ""}
```
"""
        
        if stderr:
            prompt += f"""
### 错误输出 (stderr)  
```
{stderr[:1000]}{"..." if len(stderr) > 1000 else ""}
```
"""
        
        if return_value:
            prompt += f"""
### 返回值 (return_value)
```
{str(return_value)[:1000]}{"..." if len(str(return_value)) > 1000 else ""}
```
"""
        
        if context:
            prompt += f"""
### 上下文信息
{context[:500]}{"..." if len(context) > 500 else ""}
"""
        
        prompt += """

## 分析要求

请基于以上信息，判断此次执行的测试/验证/构建是否成功通过。

### 判断标准
1. **单元测试**: 
   - unittest/pytest: 测试结果通常在stderr中，查找"OK"、"FAILED"、"passed"、"failed"等关键词
   - unittest成功: "Ran X tests...OK"
   - unittest失败: "FAILED (failures=X)" 或 "FAILED (errors=X)"
   - pytest成功: "X passed"
   - pytest失败: "X failed"
2. **集成测试**: 检查API响应、数据库连接、服务状态等
3. **代码检查**: 语法检查、linting、类型检查等
4. **构建任务**: 编译成功、打包完成、依赖安装等
5. **验证任务**: 数据验证、格式检查、业务逻辑验证等

**重要提醒**: stderr中的内容不一定是错误！unittest等测试框架将正常的测试结果输出到stderr。

### 输出格式
必须返回严格的JSON格式，包含以下字段：

```json
{
    "passed": true,                    // 布尔值：测试是否通过
    "confidence": 0.95,                // 浮点数：置信度(0-1)
    "reason": "所有12个测试用例通过",    // 字符串：判断理由
    "test_type": "unit_test",          // 字符串：识别的测试类型
    "details": {                       // 对象：详细分析
        "total_tests": 12,
        "passed_tests": 12,
        "failed_tests": 0,
        "error_indicators": [],
        "success_indicators": ["12 passed"]
    }
}
```

### test_type可选值
- "unit_test": 单元测试
- "integration_test": 集成测试  
- "build": 构建任务
- "lint": 代码检查
- "validation": 数据/格式验证
- "execution": 一般代码执行
- "unknown": 无法确定类型

### 特殊注意事项
1. 即使stderr有内容，也可能是警告而非错误
2. 某些测试框架成功时返回非零退出码
3. 注意区分测试框架的输出格式
4. 考虑不同编程语言的测试工具特点

请仔细分析，给出准确判断。
"""
        
        return prompt
    
    def _validate_and_normalize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """验证并规范化响应格式"""
        
        # 设置默认值
        normalized = {
            "passed": response.get("passed", False),
            "confidence": min(max(response.get("confidence", 0.5), 0.0), 1.0),
            "reason": response.get("reason", "AI分析结果"),
            "test_type": response.get("test_type", "unknown"),
            "details": response.get("details", {})
        }
        
        # 确保passed是布尔值
        if isinstance(normalized["passed"], str):
            normalized["passed"] = normalized["passed"].lower() in ["true", "yes", "pass", "passed", "success"]
        
        # 确保confidence是数字
        try:
            normalized["confidence"] = float(normalized["confidence"])
        except (ValueError, TypeError):
            normalized["confidence"] = 0.5
        
        return normalized
    
    def quick_evaluate(self, result_return_value: str) -> bool:
        """
        快速评估函数，返回简单的布尔结果
        
        Args:
            result_return_value: 测试结果的返回值
            
        Returns:
            bool: 测试是否通过
        """
        evaluation = self.evaluate_test_result(result_return_value=result_return_value)
        return evaluation["passed"]


class MockTestResultEvaluator(TestResultEvaluator):
    """模拟测试结果评估器，用于测试和开发"""
    
    def __init__(self):
        # 不需要真实的API密钥
        pass
    
    def evaluate_test_result(self, **kwargs) -> Dict[str, Any]:
        """模拟评估逻辑"""
        
        # 获取输出信息
        stdout = kwargs.get("result_stdout", "")
        stderr = kwargs.get("result_stderr", "")
        return_value = kwargs.get("result_return_value", "")
        
        # 简单的启发式判断
        combined_output = f"{stdout} {stderr} {return_value}".lower()
        
        # 失败指标
        fail_indicators = [
            "failed", "error", "exception", "traceback", 
            "assertion error", "test failed", "0 passed",
            "failure", "fatal", "critical", "1 failed", 
            "2 failed", "3 failed", "4 failed", "5 failed"
        ]
        
        # 成功指标  
        success_indicators = [
            "passed", "success", "ok", "all tests passed",
            "build successful", "completed successfully"
        ]
        
        has_failures = any(indicator in combined_output for indicator in fail_indicators)
        has_success = any(indicator in combined_output for indicator in success_indicators)
        
        # 特殊处理: "0 failed" 不应该被认为是失败
        if "0 failed" in combined_output:
            has_failures = False
        
        # 判断逻辑：如果同时存在成功和失败指标，优先判断为失败
        if has_failures:
            passed = False
            confidence = 0.8
            reason = "检测到失败指标"
        elif has_success:
            passed = True
            confidence = 0.8  
            reason = "检测到成功指标"
        elif stderr and not stdout:
            # 特殊处理：unittest等测试框架将结果输出到stderr
            # 检查stderr是否包含测试结果而非真正的错误
            unittest_patterns = [
                "ran", "test", "ok", "passed", "failed", 
                "errors", "failures", "skipped"
            ]
            is_test_output = any(pattern in stderr.lower() for pattern in unittest_patterns)
            
            if is_test_output:
                # 如果stderr包含测试相关输出，重新评估
                if "0 failed" in stderr.lower() or "ok" in stderr.lower():
                    passed = True
                    confidence = 0.7
                    reason = "unittest结果在stderr中显示测试通过"
                else:
                    passed = False
                    confidence = 0.7
                    reason = "unittest结果在stderr中显示测试失败"
            else:
                # 真正的错误输出
                passed = False
                confidence = 0.6
                reason = "仅有错误输出"
        else:
            passed = True
            confidence = 0.3
            reason = "默认判断为通过"
        
        return {
            "passed": passed,
            "confidence": confidence,
            "reason": reason,
            "test_type": "mock_evaluation",
            "details": {
                "fail_indicators_found": [ind for ind in fail_indicators if ind in combined_output],
                "success_indicators_found": [ind for ind in success_indicators if ind in combined_output]
            }
        }


# 便捷函数
def evaluate_with_deepseek(result_return_value: str, 
                          api_key: str = None,
                          use_mock: bool = False) -> Dict[str, Any]:
    """
    便捷函数：使用deepseek评估测试结果
    
    Args:
        result_return_value: 测试结果返回值
        api_key: DeepSeek API密钥
        use_mock: 是否使用模拟评估器
        
    Returns:
        评估结果字典
    """
    if use_mock or not api_key:
        evaluator = MockTestResultEvaluator()
    else:
        evaluator = TestResultEvaluator(api_key=api_key)
    
    return evaluator.evaluate_test_result(result_return_value=result_return_value)


def is_test_passed(result_return_value: str, 
                  api_key: str = None,
                  use_mock: bool = False) -> bool:
    """
    便捷函数：快速判断测试是否通过
    
    Args:
        result_return_value: 测试结果返回值
        api_key: DeepSeek API密钥 
        use_mock: 是否使用模拟评估器
        
    Returns:
        bool: 测试是否通过
    """
    evaluation = evaluate_with_deepseek(result_return_value, api_key, use_mock)
    return evaluation["passed"]


if __name__ == "__main__":
    # 测试示例
    print("🧪 测试智能结果评估器...")
    
    # 使用模拟评估器测试
    test_cases = [
        "12 tests passed, 0 failed",
        "ERROR: test_addition failed - AssertionError",
        "Build completed successfully",
        "3 passed, 2 failed, 1 error",
        "All checks passed ✓"
    ]
    
    for test_case in test_cases:
        result = evaluate_with_deepseek(test_case, use_mock=True)
        print(f"输入: {test_case}")
        print(f"判断: {'通过' if result['passed'] else '失败'} (置信度: {result['confidence']:.2f})")
        print(f"理由: {result['reason']}")
        print()