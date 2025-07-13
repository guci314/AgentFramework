"""
简化的超我智能体提示词
针对LLM响应稳定性优化的提示模板
"""

def get_simplified_strategy_optimization_prompt(performance_data: str, context_data: str, goals_data: str) -> str:
    """简化的策略优化提示"""
    return f"""请分析并优化策略。

当前情况: {performance_data}
目标: {goals_data}

返回JSON格式:
{{
    "analysis": "简要分析",
    "strategies": ["策略1", "策略2"],
    "priority": "high"
}}"""

def get_simplified_strategy_regulation_prompt(context_data: str, goals_data: str) -> str:
    """简化的策略调节提示"""
    return f"""请评估当前策略。

上下文: {context_data}
目标: {goals_data}

返回JSON格式:
{{
    "assessment": "评估结果",
    "adjustment_needed": true,
    "recommended_strategy": "建议策略"
}}"""

def get_simplified_reflection_prompt(experience_data: str, outcome_data: str) -> str:
    """简化的反思提示"""
    return f"""请分析以下经验。

经验: {experience_data}
结果: {outcome_data}

返回JSON格式:
{{
    "lessons": ["经验1", "经验2"],
    "suggestions": ["建议1", "建议2"],
    "quality": 0.8
}}"""

def get_simplified_meta_learning_prompt(success_cases: str, failure_cases: str) -> str:
    """简化的元学习提示"""
    return f"""请提取学习模式。

成功案例: {success_cases}
失败案例: {failure_cases}

返回JSON格式:
{{
    "success_patterns": ["模式1", "模式2"],
    "failure_causes": ["原因1", "原因2"],
    "insights": "学习洞察"
}}"""

# 提示词优化原则
PROMPT_OPTIMIZATION_PRINCIPLES = {
    "length_limit": 500,  # 最大提示长度
    "json_simplicity": "使用简单的JSON结构",
    "clear_instructions": "使用直接明确的指令",
    "avoid_complex_examples": "避免复杂的示例",
    "single_task_focus": "每个提示专注单一任务"
}

def optimize_prompt_for_llm(original_prompt: str) -> str:
    """优化提示词以提高LLM响应率"""
    # 如果提示词太长，进行截断
    if len(original_prompt) > PROMPT_OPTIMIZATION_PRINCIPLES["length_limit"]:
        # 保留前后重要部分
        prefix = original_prompt[:200]
        suffix = original_prompt[-200:]
        return f"{prefix}...\n\n{suffix}"
    
    return original_prompt

def get_fallback_responses():
    """获取备用响应模板"""
    return {
        "strategy_optimization": {
            "analysis": "基础策略分析",
            "strategies": ["保持现状", "渐进改进"],
            "priority": "medium",
            "confidence": 0.7
        },
        "strategy_regulation": {
            "assessment": "策略基本适用",
            "adjustment_needed": False,
            "recommended_strategy": "继续当前策略",
            "confidence": 0.6
        },
        "reflection": {
            "lessons": ["经验积累", "持续改进"],
            "suggestions": ["保持良好习惯", "关注细节"],
            "quality": 0.7
        },
        "meta_learning": {
            "success_patterns": ["系统化方法", "持续学习"],
            "failure_causes": ["准备不足", "沟通不畅"],
            "insights": "注重基础建设和团队协作"
        }
    }