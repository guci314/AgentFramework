#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = str(Path.cwd().parent)
sys.path.append(project_root)

from pythonTask import llm_deepseek
from cognitive_workflow_rule_base.services.task_translator import TaskTranslator
import logging

# 设置日志级别
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

print('🔍 直接调试TaskTranslator的LLM调用...')

task_translator = TaskTranslator(llm_deepseek)

# 直接测试LLM调用
prompt = task_translator._build_translation_prompt('计算1+2+3的结果')
print('📝 生成的提示词:')
print(prompt[:200] + '...')

try:
    # 直接调用LLM方法
    response = task_translator._call_llm_with_json_format(prompt)
    print(f'\n🔍 LLM原始响应:')
    print(f'Type: {type(response)}')
    print(f'Content: {response}')
    
    # 尝试解析响应
    result = task_translator._parse_translation_response(response)
    print(f'\n📊 解析结果:')
    print(f'  - granularity_level: {result.granularity_level}')
    print(f'  - confidence: {result.confidence}')
    
except Exception as e:
    print(f'❌ 调试失败: {e}')
    import traceback
    traceback.print_exc()