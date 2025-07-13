#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = str(Path.cwd().parent)
sys.path.append(project_root)

from llm_lazy import get_modelnitive_workflow_rule_base.services.task_translator import TaskTranslator
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

print('🧪 测试简化后的TaskTranslator（移除granularity_level）...')

task_translator = TaskTranslator(get_model("deepseek_chat"))

# 测试简单指令
simple_instruction = '计算1+2+3的结果'

try:
    result = task_translator.translate_task(simple_instruction)
    print('\n📊 翻译结果:')
    print(f'  - extracted_task: {result.extracted_task}')
    print(f'  - filtered_context: {result.filtered_context}')
    print(f'  - confidence: {result.confidence}')
    print(f'  - reasoning: {result.reasoning[:100]}...')
    print(f'  - boundary_constraints: {result.boundary_constraints}')
    
    # 验证granularity_level属性不存在
    if hasattr(result, 'granularity_level'):
        print('❌ granularity_level属性仍然存在')
    else:
        print('✅ granularity_level属性已成功移除')
    
    print(f'\n🎯 专注核心功能：TaskTranslator只做任务提取，不做层次分类')
    print(f'   这符合真正的层次化认知架构：每层自主决策是否需要递归')
    
except Exception as e:
    print(f'❌ 测试失败: {e}')
    import traceback
    traceback.print_exc()