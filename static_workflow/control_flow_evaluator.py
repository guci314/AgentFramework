"""
控制流条件评估器模块
==================

提供安全的表达式评估、变量插值和条件判断功能。
"""

import re
import ast
import operator
import logging
from typing import Dict, Any, Union, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SafeEvaluator:
    """安全的表达式评估器"""
    
    # 允许的操作符
    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.And: operator.and_,
        ast.Or: operator.or_,
        ast.Not: operator.not_,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    
    # 允许的内置函数
    ALLOWED_FUNCTIONS = {
        'abs': abs,
        'max': max,
        'min': min,
        'len': len,
        'sum': sum,
        'round': round,
        'int': int,
        'float': float,
        'str': str,
        'bool': bool,
        'isinstance': isinstance,
        'hasattr': hasattr,
        'getattr': getattr,
    }
    
    def __init__(self):
        self.variables = {}
    
    def set_variables(self, variables: Dict[str, Any]) -> None:
        """设置可用变量"""
        self.variables = variables.copy()
    
    def evaluate(self, expression: str) -> Any:
        """安全评估表达式"""
        try:
            # 预处理表达式：将AND/OR转换为Python的and/or
            processed_expr = self._preprocess_expression(expression)
            
            # 解析表达式
            tree = ast.parse(processed_expr, mode='eval')
            
            # 验证表达式安全性
            self._validate_ast(tree)
            
            # 评估表达式
            return self._eval_node(tree.body)
            
        except Exception as e:
            logger.error(f"表达式评估失败: {expression}, 错误: {e}")
            raise ValueError(f"表达式评估失败: {e}")
    
    def _preprocess_expression(self, expression: str) -> str:
        """预处理表达式，转换逻辑操作符"""
        # 将SQL风格的逻辑操作符转换为Python风格
        processed = expression.replace(' AND ', ' and ').replace(' OR ', ' or ')
        # 处理开头和结尾的AND/OR
        processed = processed.replace('AND ', 'and ').replace(' AND', ' and')
        processed = processed.replace('OR ', 'or ').replace(' OR', ' or')
        return processed
    
    def _validate_ast(self, tree: ast.AST) -> None:
        """验证AST树的安全性"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # 检查函数调用
                if isinstance(node.func, ast.Name):
                    if node.func.id not in self.ALLOWED_FUNCTIONS:
                        raise ValueError(f"不允许的函数调用: {node.func.id}")
                else:
                    raise ValueError("不允许的函数调用形式")
            
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                raise ValueError("不允许import语句")
            
            elif isinstance(node, ast.Attribute):
                # 允许某些属性访问
                if not self._is_safe_attribute(node):
                    raise ValueError(f"不允许的属性访问")
    
    def _is_safe_attribute(self, node: ast.Attribute) -> bool:
        """检查属性访问是否安全"""
        safe_attributes = {
            'stdout', 'stderr', 'success', 'code', 'return_value',
            'start_time', 'end_time', 'status', 'result',
            'year', 'month', 'day', 'hour', 'minute', 'second'
        }
        return node.attr in safe_attributes
    
    def _eval_node(self, node: ast.AST) -> Any:
        """递归评估AST节点"""
        if isinstance(node, ast.Constant):
            return node.value
        
        elif isinstance(node, ast.Name):
            if node.id in self.variables:
                return self.variables[node.id]
            elif node.id in self.ALLOWED_FUNCTIONS:
                return self.ALLOWED_FUNCTIONS[node.id]
            elif node.id == 'True':
                return True
            elif node.id == 'False':
                return False
            elif node.id == 'None':
                return None
            else:
                raise ValueError(f"未定义的变量: {node.id}")
        
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op = self.ALLOWED_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"不支持的二元操作符: {type(node.op)}")
            return op(left, right)
        
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op = self.ALLOWED_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"不支持的一元操作符: {type(node.op)}")
            return op(operand)
        
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator)
                op_func = self.ALLOWED_OPERATORS.get(type(op))
                if op_func is None:
                    raise ValueError(f"不支持的比较操作符: {type(op)}")
                if not op_func(left, right):
                    return False
                left = right
            return True
        
        elif isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                # 对于AND操作，如果任何一个为False，立即返回False
                for value in node.values:
                    if not self._eval_node(value):
                        return False
                return True
            elif isinstance(node.op, ast.Or):
                # 对于OR操作，如果任何一个为True，立即返回True
                for value in node.values:
                    if self._eval_node(value):
                        return True
                return False
            else:
                raise ValueError(f"不支持的布尔操作符: {type(node.op)}")
        
        elif isinstance(node, ast.Call):
            func = self._eval_node(node.func)
            args = [self._eval_node(arg) for arg in node.args]
            kwargs = {kw.arg: self._eval_node(kw.value) for kw in node.keywords}
            return func(*args, **kwargs)
        
        elif isinstance(node, ast.Attribute):
            obj = self._eval_node(node.value)
            return getattr(obj, node.attr)
        
        elif isinstance(node, ast.List):
            return [self._eval_node(elt) for elt in node.elts]
        
        elif isinstance(node, ast.Tuple):
            return tuple(self._eval_node(elt) for elt in node.elts)
        
        elif isinstance(node, ast.Dict):
            keys = [self._eval_node(k) for k in node.keys]
            values = [self._eval_node(v) for v in node.values]
            return dict(zip(keys, values))
        
        else:
            raise ValueError(f"不支持的AST节点类型: {type(node)}")


class VariableInterpolator:
    """变量插值器"""
    
    def __init__(self, variables: Dict[str, Any]):
        self.variables = variables
    
    def interpolate(self, text: str) -> str:
        """插值变量到文本中"""
        if not isinstance(text, str):
            return text
        
        # 查找 ${variable} 模式
        pattern = r'\$\{([^}]+)\}'
        
        def replace_var(match):
            var_name = match.group(1).strip()
            if var_name in self.variables:
                return str(self.variables[var_name])
            else:
                logger.warning(f"未找到变量: {var_name}")
                return match.group(0)  # 保持原样
        
        return re.sub(pattern, replace_var, text)


class ControlFlowEvaluator:
    """控制流条件评估器"""
    
    def __init__(self):
        self.evaluator = SafeEvaluator()
        self.interpolator = None
        self.context_variables = {}
        self.runtime_variables = {}
    
    def set_context(self, 
                   global_variables: Dict[str, Any] = None,
                   runtime_variables: Dict[str, Any] = None,
                   step_result: Any = None,
                   execution_stats: Dict[str, Any] = None) -> None:
        """设置评估上下文"""
        
        # 合并所有变量
        all_variables = {}
        
        if global_variables:
            all_variables.update(global_variables)
        
        if runtime_variables:
            all_variables.update(runtime_variables)
        
        # 添加步骤结果变量
        if step_result:
            if hasattr(step_result, 'success'):
                all_variables['step_success'] = step_result.success
                all_variables['success'] = step_result.success
                all_variables['last_result'] = step_result  # 添加last_result引用
                all_variables['test_result'] = step_result  # 添加test_result引用
                # 为了兼容使用returncode的工作流，将success转换为returncode风格
                all_variables['returncode'] = 0 if step_result.success else 1
            if hasattr(step_result, 'stdout'):
                all_variables['step_stdout'] = step_result.stdout
            if hasattr(step_result, 'stderr'):
                all_variables['step_stderr'] = step_result.stderr
            if hasattr(step_result, 'return_value'):
                all_variables['step_return_value'] = step_result.return_value
        
        # 添加执行统计
        if execution_stats:
            all_variables.update(execution_stats)
        
        # 添加时间相关变量
        now = datetime.now()
        all_variables.update({
            'current_time': now,
            'current_timestamp': now.timestamp(),
            'today': now.date(),
        })
        
        # 设置变量
        self.context_variables = all_variables
        self.evaluator.set_variables(all_variables)
        self.interpolator = VariableInterpolator(all_variables)
    
    def evaluate_condition(self, condition: str) -> bool:
        """评估条件表达式"""
        if not condition:
            return True
        
        try:
            # 先进行变量插值
            interpolated_condition = self.interpolator.interpolate(condition)
            logger.debug(f"评估条件: {condition} -> {interpolated_condition}")
            
            # 评估表达式
            result = self.evaluator.evaluate(interpolated_condition)
            
            # 确保返回布尔值
            return bool(result)
            
        except Exception as e:
            logger.error(f"条件评估失败: {condition}, 错误: {e}")
            return False
    
    def interpolate_value(self, value: Union[str, int, float, Any]) -> Any:
        """插值变量值"""
        if isinstance(value, str):
            return self.interpolator.interpolate(value)
        return value
    
    def evaluate_expression(self, expression: str) -> Any:
        """评估表达式并返回结果"""
        try:
            # 先进行变量插值
            interpolated_expr = self.interpolator.interpolate(expression)
            logger.debug(f"评估表达式: {expression} -> {interpolated_expr}")
            
            # 评估表达式
            return self.evaluator.evaluate(interpolated_expr)
            
        except Exception as e:
            logger.error(f"表达式评估失败: {expression}, 错误: {e}")
            raise
    
    def check_timeout(self, start_time: datetime, timeout_seconds: int) -> bool:
        """检查是否超时"""
        if not start_time or not timeout_seconds:
            return False
        
        elapsed = (datetime.now() - start_time).total_seconds()
        return elapsed > timeout_seconds
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量值"""
        return self.context_variables.get(name, default)
    
    def set_variable(self, name: str, value: Any) -> None:
        """设置运行时变量"""
        self.runtime_variables[name] = value
        self.context_variables[name] = value
        self.evaluator.set_variables(self.context_variables)
        if self.interpolator:
            self.interpolator.variables = self.context_variables