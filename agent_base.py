from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from typing import Iterator
import tiktoken # Add tiktoken import for accurate counting
import functools
import inspect
import random
import string
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple, Union, Optional, Callable
import os # 需要导入 os 模块

# 定义最大token数常量 (作为最终的后备)
MAX_TOKENS = 60000

#region Result
class Result:
    """
    执行结果类
    
    用于封装智能体执行操作后的结果信息，包括执行状态、代码、输出等。
    支持同步和异步执行结果的统一表示。
    
    注意：对于单元测试或验证类指令，success=True表示成功完成了测试或验证操作，
    而不是测试结果是否通过。测试或验证的实际结果（通过/失败）记录在return_value中。
        
    Attributes:
        success (bool): 执行成功标志
        code (str): 根据指令由语言模型生成的代码
        stdout (str): 标准输出内容
        stderr (str): 标准错误输出内容
        return_value (str): 执行结果的返回值
    """
    def __init__(self, success: bool, code: str, stdout: str = None, stderr: str = None, return_value: str = None):
        self.success = success
        self.code = code
        self.stdout = stdout
        self.stderr = stderr
        self.return_value = return_value
    
    def __str__(self) -> str:
        code = self.code or ""
        stdout = self.stdout or ""
        stderr = self.stderr or ""
        try:
            return_value = str(self.return_value) if self.return_value else ""
        except:
            return_value = ""
        return f''' 
            "success":{self.success} 
            "code":{code} 
            "stdout":{stdout} 
            "stderr":{stderr} 
            "return_value":{return_value} 
        '''
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'success': self.success,
            'code': self.code,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'return_value': self.return_value
        }
#endregion

#region reduce_memory_decorator (修改后)
def reduce_memory_decorator(func=None, *, max_tokens=None):
    """
    装饰器：在函数执行后检查memory大小，如果超过max_tokens则减少memory
    重要的是保持memory中message的交替顺序
    可以直接装饰函数或使用参数：@reduce_memory_decorator 或 @reduce_memory_decorator(max_tokens=1000)

    动态设置 max_tokens 的优先级:
    1. 装饰器参数: @reduce_memory_decorator(max_tokens=value)
    2. 环境变量: AGENT_MAX_TOKENS
    3. 全局常量: MAX_TOKENS
    """
    # 1. 确定最终生效的 max_tokens 值
    effective_max_tokens = MAX_TOKENS # 默认使用全局常量
    try:
        # 2. 尝试从环境变量读取
        env_max_tokens = os.environ.get("AGENT_MAX_TOKENS")
        if env_max_tokens is not None:
            effective_max_tokens = int(env_max_tokens)
    except (ValueError, TypeError):
        # 如果环境变量格式错误，则忽略，继续使用全局常量
        pass

    # 3. 如果装饰器直接提供了 max_tokens 参数，则优先使用它
    if max_tokens is not None:
        effective_max_tokens = max_tokens

    # --- 内部 decorator 和 _reduce_memory 保持不变，但使用 effective_max_tokens ---
    def decorator(decorated_func):
        @functools.wraps(decorated_func)
        def wrapper(*args, **kwargs):
            # 确保我们能够获取到agent对象
            agent = None
            # 更健壮地检查 agent 实例 (假设 AgentBase 是第一个参数)
            # 注意: 这里需要知道 AgentBase 的实际类定义才能进行 isinstance 检查
            # 为了不修改 AgentBase 定义本身，我们暂时保留原始的检查方式
            # 或者假设第一个参数总是 agent 实例
            if args: # 如果有位置参数
                 agent = args[0] # 假定第一个参数是self/agent实例


            # 使用上面确定的 effective_max_tokens
            limit_to_use = effective_max_tokens

            # 执行前检查memory大小
            if agent is not None and hasattr(agent, 'memory'):
                try:
                    # Attempt to get model name from llm object, fallback otherwise
                    model_name = agent.llm.model_name if hasattr(agent.llm, 'model_name') else "gpt-3.5-turbo"
                    encoding = tiktoken.encoding_for_model(model_name)
                except Exception: # Catch potential errors during encoding lookup
                    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo") # Fallback
                tokens = sum(len(encoding.encode(msg.content)) for msg in agent.memory)

                # 如果超过阈值，先减少memory
                if tokens > limit_to_use * 0.9: # 使用 limit_to_use
                    _reduce_memory(agent, limit_to_use, encoding) # 传递 limit_to_use

            # 执行原始函数
            result = decorated_func(*args, **kwargs)

            # 如果没有获取到agent，直接返回结果
            if agent is None or not hasattr(agent, 'memory'):
                return result

            # 执行后再次检查并减少memory
            # Use precise token count for check
            try:
                # Attempt to get model name from llm object, fallback otherwise
                model_name = agent.llm.model_name if hasattr(agent.llm, 'model_name') else "gpt-3.5-turbo"
                encoding = tiktoken.encoding_for_model(model_name)
            except Exception: # Catch potential errors during encoding lookup
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo") # Fallback
            tokens = sum(len(encoding.encode(msg.content)) for msg in agent.memory)
            if tokens > limit_to_use * 0.8: # 使用 limit_to_use
                _reduce_memory(agent, limit_to_use, encoding) # 传递 limit_to_use

            return result

        return wrapper

    # 用于内部减少memory的函数
    # --- _reduce_memory 函数本身不需要改变，因为它已经接受 max_tokens 参数 ---
    def _reduce_memory(agent, max_tokens_limit, encoding): # 参数名改为 max_tokens_limit 避免混淆
        """使用 tiktoken 精确计算并减少 agent 的 memory 以满足 max_tokens_limit 限制。
        优先保留 SystemMessage 和标记为 protected=True 的消息。
        然后从最新的普通消息开始向前填充剩余空间。
        """
        # 1. 分离必要消息和普通消息
        essential_messages = []
        other_messages = []
        for msg in agent.memory:
            # 保护 SystemMessages 和显式标记为 protected 的消息
            if isinstance(msg, SystemMessage) or (hasattr(msg, 'protected') and msg.protected):
                essential_messages.append(msg)
            else:
                other_messages.append(msg)

        # 2. 计算必要消息的 token
        used_tokens = sum(len(encoding.encode(msg.content)) for msg in essential_messages)

        # 3. 计算普通消息的可用 token
        available_tokens = max_tokens_limit - used_tokens # 使用传入的限制

        # 4. 从最新的普通消息开始，按 (Human, AI) 对填充剩余空间
        temp_memory_for_others = []
        tokens_for_others = 0
        human_ai_pairs = []

        # 收集所有 (Human, AI) 对，从后往前
        # 修正循环范围，确保检查到索引 0
        i = len(other_messages) - 1
        while i > 0:
            current_msg = other_messages[i]
            prev_msg = other_messages[i-1]
            # 寻找 AI 消息及其前面的人类消息
            if isinstance(current_msg, AIMessage) and isinstance(prev_msg, HumanMessage):
                human_ai_pairs.append((prev_msg, current_msg))
                i -= 2 # 跳过这对消息，继续向前找
            else:
                i -= 1 # 只向前移动一步

        # 从最新的对话对开始添加，直到 token 耗尽
        # human_ai_pairs 列表是从最新到最旧的顺序
        for human_msg, ai_msg in human_ai_pairs:
             try:
                 pair_tokens = len(encoding.encode(human_msg.content)) + len(encoding.encode(ai_msg.content))
             except Exception:
                 pair_tokens = (len(human_msg.content) + len(ai_msg.content)) // 2 # Fallback

             if tokens_for_others + pair_tokens <= available_tokens:
                 # 在列表开头插入，保持时间顺序（虽然最后会反转）
                 temp_memory_for_others.insert(0, ai_msg)
                 temp_memory_for_others.insert(0, human_msg)
                 tokens_for_others += pair_tokens
             else:
                 # 如果这对消息会导致超过限制，则停止添加
                 break

        # 确保 memory 中至少保留一对最新的对话（如果空间允许且存在对话对）
        if not temp_memory_for_others and human_ai_pairs:
            human_msg, ai_msg = human_ai_pairs[0] # 获取最新的一对
            try:
                pair_tokens = len(encoding.encode(human_msg.content)) + len(encoding.encode(ai_msg.content))
            except Exception:
                pair_tokens = (len(human_msg.content) + len(ai_msg.content)) // 2 # Fallback

            # 只有在这一对本身不超过可用空间时才添加
            if pair_tokens <= available_tokens:
                 temp_memory_for_others.extend([human_msg, ai_msg])
                 tokens_for_others += pair_tokens

        # 5. 合并必要消息和选定的普通消息
        new_memory = essential_messages + temp_memory_for_others

        # 6. 仅在内存确实被缩减时更新 agent 的 memory
        if len(new_memory) < len(agent.memory):
            agent.memory = new_memory
            agent.memory_overloaded = True # 标记发生了缩减
            # print(f"Memory reduced. New token count (estimated): {used_tokens + tokens_for_others}") # Optional debug print
        else:
            # 如果没有消息被移除（例如，已在限制内或只有必要消息）
            # 确保标志准确反映当前状态（如果之前为 true）。
            # 如果仅必要消息就超限，内存可能仍略高于 max_tokens。
            current_total_tokens = used_tokens + tokens_for_others
            if current_total_tokens <= max_tokens_limit: # 使用传入的限制
                 agent.memory_overloaded = False # 如果现在在限制内，则重置标志

    # 支持两种装饰器使用方式
    if func is None:
        # 如果 @reduce_memory_decorator 这样调用 (带参数或不带)
        # 将绑定了 effective_max_tokens 的 decorator 返回
        return decorator
    else:
        # 如果 @reduce_memory_decorator 这样调用 (直接装饰函数)
        # max_tokens 会是 None (因为它是关键字参数)
        # effective_max_tokens 会根据 环境变量 -> 全局常量 确定
        # 将应用了 wrapper 的函数返回
        return decorator(func)
#endregion

#region reduce_memory_decorator_compress (新增)
def reduce_memory_decorator_compress(func=None, *, max_tokens=None):
    """
    压缩版内存管理装饰器：在函数执行后检查memory大小，如果超过max_tokens则使用压缩策略减少memory
    压缩策略：保留protected消息和最后10条消息，压缩中间的消息
    可以直接装饰函数或使用参数：@reduce_memory_decorator_compress 或 @reduce_memory_decorator_compress(max_tokens=1000)

    动态设置 max_tokens 的优先级:
    1. 装饰器参数: @reduce_memory_decorator_compress(max_tokens=value)
    2. 环境变量: AGENT_MAX_TOKENS
    3. 全局常量: MAX_TOKENS
    """
    # 1. 确定最终生效的 max_tokens 值
    effective_max_tokens = MAX_TOKENS # 默认使用全局常量
    try:
        # 2. 尝试从环境变量读取
        env_max_tokens = os.environ.get("AGENT_MAX_TOKENS")
        if env_max_tokens is not None:
            effective_max_tokens = int(env_max_tokens)
    except (ValueError, TypeError):
        # 如果环境变量格式错误，则忽略，继续使用全局常量
        pass

    # 3. 如果装饰器直接提供了 max_tokens 参数，则优先使用它
    if max_tokens is not None:
        effective_max_tokens = max_tokens

    def decorator(decorated_func):
        @functools.wraps(decorated_func)
        def wrapper(*args, **kwargs):
            # 确保我们能够获取到agent对象
            agent = None
            if args: # 如果有位置参数
                 agent = args[0] # 假定第一个参数是self/agent实例

            # 使用上面确定的 effective_max_tokens
            limit_to_use = effective_max_tokens

            # 执行前检查memory大小
            if agent is not None and hasattr(agent, 'memory'):
                try:
                    # Attempt to get model name from llm object, fallback otherwise
                    model_name = agent.llm.model_name if hasattr(agent.llm, 'model_name') else "gpt-3.5-turbo"
                    encoding = tiktoken.encoding_for_model(model_name)
                except Exception: # Catch potential errors during encoding lookup
                    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo") # Fallback
                tokens = sum(len(encoding.encode(msg.content)) for msg in agent.memory)

                # 如果超过阈值，先减少memory
                if tokens > limit_to_use * 0.9: # 使用 limit_to_use
                    _reduce_memory_compress(agent, limit_to_use, encoding) # 使用压缩版本

            # 执行原始函数
            result = decorated_func(*args, **kwargs)

            # 如果没有获取到agent，直接返回结果
            if agent is None or not hasattr(agent, 'memory'):
                return result

            # 执行后再次检查并减少memory
            try:
                # Attempt to get model name from llm object, fallback otherwise
                model_name = agent.llm.model_name if hasattr(agent.llm, 'model_name') else "gpt-3.5-turbo"
                encoding = tiktoken.encoding_for_model(model_name)
            except Exception: # Catch potential errors during encoding lookup
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo") # Fallback
            tokens = sum(len(encoding.encode(msg.content)) for msg in agent.memory)
            if tokens > limit_to_use * 0.8: # 使用 limit_to_use
                _reduce_memory_compress(agent, limit_to_use, encoding) # 使用压缩版本

            return result

        return wrapper

    def _reduce_memory_compress(agent, max_tokens_limit, encoding):
        """使用压缩策略减少 agent 的 memory 以满足 max_tokens_limit 限制。
        策略：保留 protected 消息和最后10条消息，压缩中间的消息。
        """
        try:
            # 确保从当前目录导入
            from .message_compress import compress_messages
        except ImportError:
            # 备用导入方案
            from message_compress import compress_messages
        
        print(f"✅ 成功导入 compress_messages: {compress_messages.__module__}")
        
        # 1. 分离protected消息和普通消息
        protected_messages = []
        regular_messages = []
        
        for msg in agent.memory:
            # 保护 SystemMessages 和显式标记为 protected 的消息
            if isinstance(msg, SystemMessage) or (hasattr(msg, 'protected') and msg.protected):
                protected_messages.append(msg)
            else:
                regular_messages.append(msg)

        # 2. 计算protected消息的token数
        protected_tokens = sum(len(encoding.encode(msg.content)) for msg in protected_messages)
        
        # 3. 计算可用于普通消息的token数
        available_tokens = max_tokens_limit - protected_tokens
        
        print(f"\n🔄 开始消息压缩...")
        print(f"📊 原始消息统计: 总消息 {len(agent.memory)} 条 (保护消息 {len(protected_messages)} 条, 普通消息 {len(regular_messages)} 条)")
        print(f"🎯 Token限制: {max_tokens_limit}, 保护消息占用: {protected_tokens}, 普通消息可用: {available_tokens}")
        
        # 4. 处理普通消息
        try:
            # 直接调用compress_messages，它会自动处理保留最后10条消息的逻辑
            final_regular_messages = compress_messages(regular_messages)
        except Exception as e:
            # 如果压缩失败，fallback到原有的token限制策略
            print(f"❌ 压缩失败，使用fallback策略: {e}")
            final_regular_messages = _fallback_token_strategy(regular_messages, available_tokens, encoding)
        
        # 5. 检查最终结果是否符合token限制
        final_regular_tokens = sum(len(encoding.encode(msg.content)) for msg in final_regular_messages)
        
        # 如果仍然超过限制，使用fallback策略
        if final_regular_tokens > available_tokens:
            print(f"⚠️  压缩后仍超过限制，使用fallback策略进一步优化")
            final_regular_messages = _fallback_token_strategy(final_regular_messages, available_tokens, encoding)
        
        # 6. 组合最终的memory
        new_memory = protected_messages + final_regular_messages
        
        # 7. 更新agent的memory
        original_length = len(agent.memory)
        if len(new_memory) < original_length:
            agent.memory = new_memory
            agent.memory_overloaded = True # 标记发生了缩减
            print(f"✅ Memory压缩完成! 原始: {original_length} 条消息 → 压缩后: {len(new_memory)} 条消息")
            print(f"📈 最终构成: 保护消息 {len(protected_messages)} 条 + 普通消息 {len(final_regular_messages)} 条\n")
        else:
            # 如果没有消息被移除，检查是否需要重置标志
            total_tokens = protected_tokens + final_regular_tokens
            if total_tokens <= max_tokens_limit:
                agent.memory_overloaded = False
                print(f"✅ Memory在限制范围内，无需压缩\n")

    def _fallback_token_strategy(messages, available_tokens, encoding):
        """Fallback策略：基于token限制选择消息"""
        selected_messages = []
        used_tokens = 0
        
        # 从最新消息开始向前选择
        for msg in reversed(messages):
            try:
                msg_tokens = len(encoding.encode(msg.content))
            except Exception:
                msg_tokens = len(msg.content) // 2 # Fallback estimation
            
            if used_tokens + msg_tokens <= available_tokens:
                selected_messages.insert(0, msg) # 保持时间顺序
                used_tokens += msg_tokens
            else:
                break
        
        return selected_messages

    # 支持两种装饰器使用方式
    if func is None:
        return decorator
    else:
        return decorator(func)
#endregion

#region AgentBase
class AgentBase:
    '''
    智能体基类
    chat 和 execute 的划分确实反映了人类（以及可能是智能体）与世界交互的两种基本方式：通过语言进行交流和思考 (chat)，以及通过行动改变或感知世界 (execute)。
    意向性 (Intentionality): 哲学中指心灵状态（如信念、欲望、意图）指向或关于世界中对象的特性。
    chat 可以被看作是处理和表达意向性状态的主要方式，例如理解用户的意图，表达智能体的"信念"（知识库）或"意图"（下一步计划）。
    execute 则是将这些意向性状态（特别是行动意图）转化为实际行动的机制。
    '''
    def __init__(self, llm:BaseChatModel=None, system_message:str=None):
        self.llm = llm
        self.system_message = system_message
        self.memory = []
        # self.protected_messages = [] # 已移除，保护现在是消息对象的一个属性
        self.api_specification = None
        self.name = None
        self.memory_overloaded = False  # 添加内存超载标记
        
        if system_message:
            system_msg = SystemMessage(system_message)
            system_msg.protected = True # 将系统消息标记为受保护
            self.memory = [system_msg]
            # self.protected_messages = [system_msg] # 已移除

    def loadKnowledge(self, knowledge:str):
        '''
        加载知识到agent的记忆中，确保消息交替
        Args:
            knowledge: 知识
        '''
        human_msg = HumanMessage(knowledge)
        human_msg.protected = True # 将加载的知识标记为受保护
        ai_msg = AIMessage('ok')
        ai_msg.protected = True # 将对应的 AI 响应也标记为受保护
        # 确保消息交替
        if self.memory and isinstance(self.memory[-1], HumanMessage):
            self.memory.append(ai_msg)
            self.memory.append(human_msg)
        else:
            self.memory.append(human_msg)
            self.memory.append(ai_msg)
        # self.protected_messages.extend([human_msg, ai_msg]) # 已移除
    
    def calculate_memory_tokens(self, model_name: str = "gpt-3.5-turbo") -> int:
        '''
        计算memory的token数量
        Args:
            model_name: 模型名称
        Returns:
            int: token数量
        '''
        encoding = tiktoken.encoding_for_model(model_name)
        return sum(len(encoding.encode(msg.content)) for msg in self.memory)

    # @reduce_memory_decorator
    def execute_stream(self, instruction:str=None) -> Iterator[object]:
        '''
        执行流式方法
        Args:
            instruction: 执行指令
        Returns:
            Iterator[object]: 流式结果
            流式结果的结构是过程加状态。流的前面是过程，流的最后一个元素是最终状态。
        '''
        pass

    # @reduce_memory_decorator
    def execute_sync(self, instruction:str=None) -> Result:
        '''
        同步执行方法
        Args:
            instruction: 执行指令
        Returns:
            Result: 执行结果
        '''
        pass

    # @reduce_memory_decorator
    def chat_stream(self, message: str, response_format: Optional[Dict] = None) -> Iterator[object]:
        '''
        流式聊天方法
        Args:
            message: 聊天消息
        Returns:
            Iterator[object]: 流式结果，包括文本片段和最终的Result对象
        '''
        human_msg = HumanMessage(message)
        self.memory.append(human_msg)
        content = ''
        # Only pass response_format if it's not None to avoid API compatibility issues
        stream_kwargs = {}
        if response_format is not None:
            stream_kwargs['response_format'] = response_format
        chunks = self.llm.stream(self.memory, **stream_kwargs)
        for chunk in chunks:
            content += chunk.content
            yield chunk.content
        ai_msg = AIMessage(content)
        self.memory.append(ai_msg)
        yield Result(True, "", "", None, content)

    # @reduce_memory_decorator
    def chat_sync(self, message: str, response_format: Optional[Dict] = None) -> Result:
        '''
        同步聊天方法，确保消息交替
        Args:
            message: 聊天消息
        Returns:
            Result: 聊天结果
        '''
        human_msg = HumanMessage(message)
        self.memory.append(human_msg)
        # Only pass response_format if it's not None to avoid API compatibility issues
        invoke_kwargs = {}
        if response_format is not None:
            invoke_kwargs['response_format'] = response_format
        content = self.llm.invoke(self.memory, **invoke_kwargs).content
        ai_msg = AIMessage(content)
        self.memory.append(ai_msg)
        return Result(True, "", "", None, content)

    def classify_instruction(self, instruction: str) -> bool:
        '''
        判断用户指令是"思维"还是"动作"
        Args:
            instruction: 用户指令
        Returns:
            bool: 如果是动作类型返回True，否则返回False
        '''
        # 构建分类提示词
        classification_prompt = """# 输入类型判断指南

作为智能体，我需要准确判断用户的输入是"思维"还是"动作"，以便选择正确的处理方法。

## 思维（Thought）
- 定义：思维是指仅与智能体的内部记忆（memory）交互，不产生任何外部副作用的操作
- 特点：
  - 只读取和修改智能体的内部状态（记忆）
  - 不调用任何外部工具或API
  - 不修改外部世界
  - 结果仅依赖于输入和当前记忆状态
- 处理方法：使用思维处理方法
- 示例：
  - "请总结一下我们之前的对话"
  - "你能解释一下量子计算的基本原理吗？"
  - "根据我们之前的讨论，你认为哪种方案更好？"

## 动作（Action）
- 定义：动作是指会调用工具对外部世界产生副作用的操作
- 特点：
  - 需要调用外部工具、API或执行命令
  - 会修改外部世界（如文件系统、网络请求、数据库等）
  - 可能产生持久化的变化
  - 结果不仅依赖于输入和记忆，还依赖于外部环境
- 处理方法：使用动作处理方法
- 示例：
  - "请创建一个名为'project'的新文件夹"
  - "搜索关于人工智能的最新研究论文"
  - "将这段代码保存到文件中"
  - "连接到数据库并执行查询"

## 判断标准
1. 如果用户请求涉及外部工具调用、文件操作、网络请求或任何会改变外部世界的操作，则视为"动作"
2. 如果用户请求仅涉及信息检索、分析、总结或与智能体记忆的交互，则视为"思维"
3. 当不确定时，优先考虑是否为"动作"，因为错误地将动作当作思维处理可能导致无法完成用户请求

## 响应格式
请判断以下用户指令是否为"动作"类型。
如果是动作类型，请只返回"true"。
如果不是动作类型（即思维类型），请只返回"false"。
不要包含任何其他内容，不要解释原因，不要添加任何额外的文字。

请判断以下用户指令的类型：
{instruction}
"""
        
        # 创建临时消息列表，不修改原始记忆
        temp_messages = []
        human_msg = HumanMessage(classification_prompt.format(instruction=instruction))
        temp_messages.append(human_msg)
        
        # 调用LLM进行判断
        response = self.llm.invoke(temp_messages)
        
        # 解析响应
        try:
            # 提取响应中的true/false
            content = response.content.lower().strip()
            return "true" in content
        except Exception as e:
            # 如果解析失败，返回默认值（默认为动作类型）
            return True
    
#endregion
