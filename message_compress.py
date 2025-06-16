import os
from typing import List
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化语言模型
llm_gemini_25_flash_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.5-flash-preview-05-20", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY')
)

# DeepSeek模型配置
llm_deepseek = ChatOpenAI(
    temperature=0,
    model="deepseek-chat",  
    base_url="https://api.deepseek.com",
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    max_tokens=8192
)

def compress_messages(messages: List[BaseMessage], use_deepseek: bool = False) -> List[BaseMessage]:
    '''
    压缩对话消息列表，保留最后10条消息不变，压缩前面的消息为一条人类消息和一条AI消息
    
    参数:
        messages: 消息列表，HumanMessage和AIMessage交替出现
        use_deepseek: 是否使用DeepSeek模型，默认False
        
    返回:
        压缩后的消息列表
    '''
    # 输入验证
    if not isinstance(messages, list):
        raise TypeError(f"messages必须是列表类型，当前类型: {type(messages)}")
    
    if messages is None:
        raise TypeError("messages不能为None")
    
    # 边界处理：消息总数≤10，直接返回原消息列表
    if len(messages) <= 10:
        print("消息总数≤10，无需压缩")
        return messages
    
    # 分割消息：前N-10条和后10条
    compress_part = messages[:-10]
    keep_part = messages[-10:]
    
    print(f"压缩前消息数: {len(compress_part)}条")
    print(f"保留消息数: {len(keep_part)}条")
    
    # 提取需要压缩的消息内容
    conversation_text = ""
    for msg in compress_part:
        if isinstance(msg, HumanMessage):
            conversation_text += f"人类: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            conversation_text += f"AI: {msg.content}\n"
    
    # 生成摘要提示
    prompt = f"""你的任务是创建一份详细的对话总结，重点关注任务流程的连续性。
这份总结应该全面捕获任务状态、执行步骤和关键决策，确保后续步骤能够无缝继续。

请按以下结构组织总结：

**任务背景：**
- 整体任务目标和背景描述
- 任务的重要性和预期结果

**当前进度状态：**
- 任务执行到哪个阶段
- 当前状态的详细描述

**已完成步骤：**
- 已成功完成的具体操作和结果
- 重要的里程碑和成果

**关键信息和决策：**
- 重要的参数设置和配置信息
- 做出的关键决策及其原因
- 需要记住的技术细节或约束条件

**问题与解决方案：**
- 遇到的问题和挑战
- 采用的解决方案和workaround

**下一步行动：**
- 明确的待执行任务清单
- 具体的执行步骤和优先级
- 从最近对话中提取的确切要求（逐字保留以确保无信息丢失）

请完整总结以下对话内容：

{conversation_text}"""
    
    # 选择语言模型并调用生成摘要
    selected_llm = llm_deepseek if use_deepseek else llm_gemini_25_flash_openrouter
    summary = selected_llm.invoke(prompt).content
    
    # 更清晰地打印摘要内容
    print("\n" + "="*80)
    print("📝 压缩摘要内容：")
    print("="*80)
    print(summary)
    print("="*80 + "\n")
    
    # 创建压缩后的消息
    compressed_messages = [
        HumanMessage(content=summary),
        AIMessage(content="ok")
    ]
    
    # 拼接压缩后的消息和保留的消息
    result = compressed_messages + keep_part
    print(f"✅ 压缩完成，总消息数: {len(result)}条 (摘要消息 2条 + 保留消息 {len(keep_part)}条)")
    return result

# 测试代码
if __name__ == "__main__":
    # 创建测试消息列表
    test_messages = []
    for i in range(1, 16):  # 创建15条消息
        if i % 2 == 1:
            test_messages.append(HumanMessage(content=f"用户问题{i}"))
        else:
            test_messages.append(AIMessage(content=f"AI回答{i}"))
    
    print("原始消息数量:", len(test_messages))
    
    # 执行压缩
    compressed = compress_messages(test_messages)
    
    # 验证结果
    assert len(compressed) == 12, f"压缩后消息数应为12，实际为{len(compressed)}"
    assert isinstance(compressed[0], HumanMessage), "第一条消息应为HumanMessage"
    assert isinstance(compressed[1], AIMessage), "第二条消息应为AIMessage"
    assert compressed[1].content == "ok", "第二条消息内容应为'ok'"
    assert compressed[2:] == test_messages[-10:], "后10条消息应保持不变"
    
    print("测试通过")
    print("任务完成")