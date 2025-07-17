#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试消息压缩功能的脚本
"""

from message_compress import compress_messages
from langchain_core.messages import HumanMessage, AIMessage

def test_message_compression():
    """测试消息压缩功能并显示摘要内容"""
    print("🚀 开始测试消息压缩功能...")
    
    # 创建测试消息列表（超过10条以触发压缩）
    test_messages = []
    
    # 模拟一个真实的对话场景
    conversations = [
        ("用户", "你好，我需要分析一份销售数据"),
        ("AI", "好的，我可以帮您分析销售数据。请问您有什么具体的分析需求吗？"),
        ("用户", "我想要分析每个地区的销售表现"),
        ("AI", "明白了。为了分析地区销售表现，我需要查看您的数据文件。请问数据文件的格式是什么？"),
        ("用户", "数据文件是CSV格式，名为sales_data.csv"),
        ("AI", "好的，我将读取sales_data.csv文件并分析各地区的销售表现。"),
        ("用户", "还需要分析每个产品的销售额"),
        ("AI", "收到，我会同时分析地区和产品的销售数据。"),
        ("用户", "请生成一份详细的分析报告"),
        ("AI", "我将为您生成包含地区分析和产品分析的详细报告。"),
        ("用户", "报告要保存为markdown格式"),
        ("AI", "明白，我会将报告保存为markdown格式的文件。"),
        ("用户", "请使用gemini模型来生成报告内容"),
        ("AI", "好的，我将调用gemini模型来生成高质量的分析报告内容。"),
        ("用户", "开始执行分析任务"),
        ("AI", "正在开始执行销售数据分析任务...")
    ]
    
    # 将对话转换为消息对象
    for i, (speaker, content) in enumerate(conversations):
        if speaker == "用户":
            test_messages.append(HumanMessage(content=content))
        else:
            test_messages.append(AIMessage(content=content))
    
    print(f"📊 创建了 {len(test_messages)} 条测试消息")
    print(f"📝 对话内容涉及：销售数据分析、地区分析、产品分析、报告生成等")
    print("\n" + "="*50)
    
    # 执行压缩
    try:
        compressed_messages = compress_messages(test_messages)
        
        print(f"\n✅ 压缩测试完成！")
        print(f"📈 结果统计：")
        print(f"   - 原始消息数：{len(test_messages)} 条")
        print(f"   - 压缩后消息数：{len(compressed_messages)} 条")
        print(f"   - 压缩率：{(1 - len(compressed_messages)/len(test_messages))*100:.1f}%")
        
        # 验证压缩结果的结构
        print(f"\n🔍 压缩结果验证：")
        print(f"   - 第1条消息类型：{type(compressed_messages[0]).__name__}")
        print(f"   - 第2条消息类型：{type(compressed_messages[1]).__name__}")
        print(f"   - 第2条消息内容：{compressed_messages[1].content}")
        print(f"   - 保留的原始消息数：{len(compressed_messages) - 2} 条")
        
        return True
        
    except Exception as e:
        print(f"❌ 压缩测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_message_compression()
    if success:
        print(f"\n🎉 测试成功完成！压缩摘要已在上方显示。")
    else:
        print(f"\n💥 测试失败，请检查错误信息。") 