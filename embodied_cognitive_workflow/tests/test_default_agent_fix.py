"""
测试默认Agent修复

验证使用默认Agent时，Ego不会选择"自我智能体"。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embodied_cognitive_workflow import CognitiveAgent
from llm_lazy import get_model


def main():
    """测试默认Agent修复"""
    
    # 设置代理
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"
    
    # 获取语言模型
    llm = get_model('gemini_2_5_flash')
    
    # 创建认知智能体（不传入agents，使用默认Agent）
    cognitive_agent = CognitiveAgent(
        llm=llm,
        max_cycles=3,
        verbose=True,
        enable_meta_cognition=False
    )
    
    print("=== 测试默认Agent修复 ===\n")
    print("使用默认Agent（未传入agents参数）")
    print(f"默认Agent名称: {cognitive_agent.agents[0].name}")
    print(f"默认Agent能力: {cognitive_agent.agents[0].api_specification}")
    print()
    
    # 测试任务
    task = "计算 100 + 200 的结果"
    
    print(f"测试任务：{task}")
    print("-" * 60)
    
    result = cognitive_agent.execute_sync(task)
    
    if result.success:
        print(f"\n✅ 任务执行成功")
        print(f"结果：{result.return_value}")
    else:
        print(f"\n❌ 任务执行失败")
        print(f"错误：{result.stderr}")
    
    # 检查执行历史
    print("\n检查执行历史中的Agent选择：")
    print("-" * 60)
    found_self_agent = False
    found_default_agent = False
    
    for history in cognitive_agent.execution_history:
        if "执行者：" in history:
            print(f"找到执行者日志: {history}")
            if "自我智能体" in history:
                found_self_agent = True
                print("❌ 错误：发现了'自我智能体'的引用")
            if "默认执行器" in history:
                found_default_agent = True
                print("✅ 正确：使用了'默认执行器'")
    
    print("\n测试结果：")
    if found_self_agent:
        print("❌ 失败：Ego仍然选择了'自我智能体'")
    elif found_default_agent:
        print("✅ 成功：Ego正确选择了'默认执行器'")
    else:
        print("⚠️ 警告：未找到执行者选择的日志")


if __name__ == "__main__":
    main()