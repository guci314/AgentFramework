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

print('🔧 测试修复后的TaskTranslator...')

task_translator = TaskTranslator(llm_deepseek)

# 测试简单指令
simple_instruction = '计算1+2+3的结果'

try:
    result = task_translator.translate_task(simple_instruction)
    print('\n📊 修复后的翻译结果:')
    print(f'  - extracted_task: {result.extracted_task}')
    print(f'  - granularity_level: {result.granularity_level}')
    print(f'  - confidence: {result.confidence}')
    print(f'  - reasoning: {result.reasoning[:100]}...')
    
    if result.granularity_level != 'unknown':
        print('✅ granularity_level问题已修复！')
    else:
        print('❌ granularity_level仍然是unknown')
    
except Exception as e:
    print(f'❌ 测试失败: {e}')
    import traceback
    traceback.print_exc()