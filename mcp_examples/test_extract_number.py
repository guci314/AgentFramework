#!/usr/bin/env python3
"""测试数字提取逻辑"""

import re

# 测试文本
test_texts = [
    """123 + 456 的计算结果是：

123 + 456 = 579

如果你需要计算其他数字的和，可以告诉我！""",
    
    """要计算 123 + 456 × 789，我们需要遵循数学中的运算顺序（先乘除后加减）。

1. 先计算乘法部分：456 × 789 = 359,784
2. 然后加上 123：123 + 359,784 = 359,907

最终结果是：
123 + 456 × 789 = 359,907""",

    """计算结果：123 + 456 = 579"""
]

print("=== 测试数字提取 ===\n")

for i, text in enumerate(test_texts, 1):
    print(f"测试 {i}:")
    print(f"文本片段: {text[:50]}...")
    
    # 查找所有 "= 数字" 的模式
    matches = re.findall(r'=\s*([\d,]+(?:\.\d+)?)', text)
    print(f"所有匹配: {matches}")
    
    if matches:
        # 获取最后一个匹配
        last_match = matches[-1].replace(',', '')
        print(f"最终结果: {last_match}")
    else:
        print("没有找到匹配")
    
    print("-" * 50)