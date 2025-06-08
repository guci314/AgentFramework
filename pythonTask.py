# %%
import os
import json

# 导入psutil补丁，在其他导入之前修复可能的循环导入问题
try:
    import psutil_patch
    # 确保psutil已正确导入
    psutil_patch.ensure_psutil_imported()
except ImportError as e:
    print(f"Warning: Could not import psutil_patch: {e}")

from autogen.code_utils import extract_code,execute_code
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage,SystemMessage,BaseMessage,FunctionMessage
from langchain_core.language_models import BaseChatModel
from typing import Callable, Dict, List, Optional, Tuple, Union,Literal, Iterator
from langchain.prompts import ChatPromptTemplate,PromptTemplate
import subprocess
import time
import inspect
from IPython.terminal.interactiveshell import TerminalInteractiveShell
from IPython.utils.capture import capture_output
import mda.prompts
# from jupyterNotebookAutomation import CodeTracker,create_ipython_wrapper,get_functions,get_user_variables
import tempfile
from dotenv import load_dotenv
from importlib import import_module
from types import ModuleType
import inspect
import IPython
from functools import wraps  # 确保这行存在于导入部分
import sys
import logging

# 配置标准日志库
logging.basicConfig(
    level=logging.INFO,  # 设置级别为INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout) # 输出到控制台
    ]
)
logger = logging.getLogger("pythonTask") 

# 如果需要在代码中其他位置重新设置日志级别为INFO
# logging.getLogger().setLevel(logging.INFO)

# 辅助函数，用于映射旧的日志级别到标准库级别
def _map_log_level(custom_level_int):
    """Maps custom integer levels to standard logging levels."""
    if custom_level_int == 3: # DEBUG
        return logging.DEBUG
    elif custom_level_int == 2: # INFO
        return logging.INFO
    elif custom_level_int == 1: # ERROR
        return logging.ERROR
    elif custom_level_int == 0: # NONE
        # Effectively disable logging by setting a level higher than CRITICAL
        return logging.CRITICAL + 1
    else:
        # Default to INFO for unknown levels
        return logging.INFO

load_dotenv()  # 加载 .env 文件中的环境变量
max_turn = 10
import importlib
import mda.prompts
importlib.reload(mda.prompts)
from mda.prompts import default_evaluate_message

# 导入AgentBase和Result
from agent_base import AgentBase, Result,reduce_memory_decorator,reduce_memory_decorator_compress

from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache
set_llm_cache(SQLiteCache(database_path=".langchain.db"))

# from langchain_community.cache import InMemoryCache
# from langchain_core.globals import set_llm_cache

# set_llm_cache(InMemoryCache())
import httpx
# 创建一个httpx.Client
http_client=httpx.Client(
    proxy='socks5://127.0.0.1:7890',
    timeout=10,
    verify=False
)

from langchain_cohere import ChatCohere
from abc import abstractmethod

max_messages=50

# from cross_process_log_manager import log, log_expert_execution

llm_cohere = ChatCohere(
    cohere_api_key="yh0ImXh0u6VOqyAr9dsUfDIxoPg14n9Zu7MqbOU3", 
    model="command-a-03-2025"
)

llm_glm4=ChatOpenAI(
    temperature=0,
    model="GLM-4-Plus",  
    base_url="https://open.bigmodel.cn/api/paas/v4/",
    api_key="80bd464cdc10aa945760271173356885.VFVifqEfSV6syJia",
    max_tokens=8192,
)

llm_gemini_2_flash_lite_google=ChatOpenAI(
    temperature=0,
    model="gemini-2.0-flash-lite-preview-02-05", # deepseek-chat deepseek-coder 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv('GEMINI_API_KEY'),
    http_client=http_client
)

llm_gemini_2_5_pro_exp_03_25_google=ChatOpenAI(
    temperature=0,
    model="gemini-2.5-pro-exp-03-25", 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv('GEMINI_API_KEY'),
    http_client=http_client
)

llm_gemini_2_5_pro_preview_05_06_google=ChatOpenAI(
    temperature=0,
    model="gemini-2.5-pro-preview-05-06", 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv('GEMINI_API_KEY'),
    http_client=http_client
)

llm_gemini_2_5_pro_preview_06_05_google=ChatOpenAI(
    temperature=0,
    model="gemini-2.5-pro-preview-06-05", 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv('GEMINI_API_KEY'),
    http_client=http_client
)


llm_gemini_2_flash_google=ChatOpenAI(
    temperature=0,
    model="gemini-2.0-flash", # deepseek-chat deepseek-coder 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv('GEMINI_API_KEY'),
    max_tokens=4096,
    http_client=http_client
)

llm_gemini_2_flash_thinking_exp_google=ChatOpenAI(
    temperature=0,
    model="gemini-2.0-flash-thinking-exp-01-21", # deepseek-chat deepseek-coder 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv('GEMINI_API_KEY'),
    max_tokens=4096,
    http_client=http_client
)

llm_Qwen_QwQ_32B_siliconflow=ChatOpenAI(
    temperature=0,
    model="Qwen/QwQ-32B", # deepseek-chat deepseek-coder 
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv('SILICONFLOW_API_KEY'),
    max_tokens=8192
)

llm_DeepSeek_R1_Distill_Qwen_32B=ChatOpenAI(
    temperature=0,
    model="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B", # deepseek-chat deepseek-coder 
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv('SILICONFLOW_API_KEY'),
    max_tokens=8192
)

llm_DeepSeek_V3_siliconflow=ChatOpenAI(
    temperature=0,
    model="deepseek-ai/DeepSeek-V3", 
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv('SILICONFLOW_API_KEY'),
    max_tokens=4096
)

llm_Pro_DeepSeek_V3_siliconflow=ChatOpenAI(
    temperature=0,
    model="Pro/deepseek-ai/DeepSeek-V3", 
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv('SILICONFLOW_API_KEY'),
    max_tokens=4096
)

llm_DeepSeek_R1_siliconflow=ChatOpenAI(
    temperature=0,
    model="deepseek-ai/DeepSeek-R1", 
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv('SILICONFLOW_API_KEY'),
    max_tokens=8192
)

llm_Pro_DeepSeek_R1_siliconflow=ChatOpenAI(
    temperature=0,
    model="Pro/deepseek-ai/DeepSeek-R1", 
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv('SILICONFLOW_API_KEY'),
    max_tokens=8192
)

llm_Qwen_2_5_Coder_32B_Instruct_siliconflow=ChatOpenAI(
    temperature=0,
    model="Qwen/Qwen2.5-Coder-32B-Instruct", 
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv('SILICONFLOW_API_KEY'),
    max_tokens=8192
)

llm_DeepSeek_R1_Distill_Qwen_32B_siliconflow=ChatOpenAI(
    temperature=0,
    model="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B", 
    base_url="https://api.siliconflow.cn/v1",
    api_key=os.getenv('SILICONFLOW_API_KEY'),
    max_tokens=8192
)

llm_deepseek=ChatOpenAI(
    temperature=0,
    model="deepseek-chat",  
    base_url="https://api.deepseek.com",
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    max_tokens=8192
)

llm_deepseek_r1=ChatOpenAI(
    temperature=0.6,
    model="deepseek-reasoner",  
    base_url="https://api.deepseek.com",
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    max_tokens=8192
)

llm_gemini_25_pro_requesty=ChatOpenAI(
    temperature=0,
    model="google/gemini-2.5-pro-exp-03-25",  
    base_url="https://router.requesty.ai/v1",
    api_key='sk-a/b8oqq7QwqCuuFfx8j08zN3UiCoJSyx3vhFIe43p18Q/EGBPTToBQlb4YwgfnRwEofZ/ZHNynUizkNpPCiFVMBPnZ612dVAtpR6KqfjXg4=',
)

llm_qwen_2_5_72b_instruct = ChatOpenAI(
    temperature=0,
    model="qwen/qwen-2.5-72b-instruct", #"openai/gpt-4o-mini", #"openai/gpt-4o",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_gpt_4o_mini_openrouter = ChatOpenAI(
    temperature=0,
    model="openai/gpt-4o-mini", #"openai/gpt-4o-mini", #"openai/gpt-4o",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_gemini_2_5_flash_preview_thinking_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.5-flash-preview:thinking", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_gemini_2_5_flash_preview_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.5-flash-preview", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_gemini_2_5_pro_exp_03_25_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.5-pro-exp-03-25:free", #"openai/gpt-4o-mini", #"openai/gpt-4o",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_llama_4_scout_openrouter = ChatOpenAI(
    temperature=0,
    model="meta-llama/llama-4-scout", #"openai/gpt-4o-mini", #"openai/gpt-4o",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_llama_4_maverick_openrouter = ChatOpenAI(
    temperature=0,
    model="meta-llama/llama-4-maverick", #"openai/gpt-4o-mini", #"openai/gpt-4o",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_qwen_2_5_coder_32b_instruct = ChatOpenAI(
    temperature=0,
    model="qwen/qwen-2.5-coder-32b-instruct", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_qwq_32b = ChatOpenAI(
    temperature=0,
    model="qwen/qwq-32b", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_claude_35_sonnet = ChatOpenAI(
    temperature=0,
    model="anthropic/claude-3.5-sonnet:beta", #"openai/gpt-4o-mini", #"openai/gpt-4o",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_claude_37_sonnet = ChatOpenAI(
    temperature=0,
    model="anthropic/claude-3.7-sonnet", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_claude_sonnet_4 = ChatOpenAI(
    temperature=0,
    model="anthropic/claude-sonnet-4:beta", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_deepseek_r1_free_openrouter = ChatOpenAI(
    temperature=0,
    model="deepseek/deepseek-r1:free",
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_claude_37_sonnet_thinking = ChatOpenAI(
    temperature=0,
    model="anthropic/claude-3.7-sonnet:thinking", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_o3_mini = ChatOpenAI(
    temperature=0,
    model="openai/o3-mini", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_gemini_2_flash_thinking_exp_free_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.0-flash-thinking-exp:free", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)



llm_gemini_2_flash_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.0-flash-001", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_gemini_2_flash_lite_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.0-flash-lite-preview-02-05:free", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_deepseek_openrouter = ChatOpenAI(
    temperature=0,
    model="deepseek/deepseek-chat-v3-0324:NovitaAI", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_deepseek_r1_openrouter = ChatOpenAI(
    temperature=0,
    model="deepseek/deepseek-r1",     base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
)

llm_optimus_alpha_openrouter = ChatOpenAI(
        temperature=0,
        model="openrouter/optimus-alpha", #"openai/gpt-4o-mini", #"openai/gpt-4o",
        base_url='https://openrouter.ai/api/v1',
        api_key=os.getenv('OPENROUTER_API_KEY'),
)

class Device:
    '''
    执行器，执行Python代码。
    '''
    def execute_code(self,code:str)->Result:
        '''
        执行给定的Python代码，并返回执行结果。
        
        参数:
        code (str): 要执行的Python代码。
        
        返回:
        Result: 执行结果对象，包含执行成功与否、代码内容和输出信息。
        '''
        temp_file_path = None
        try:
            # 使用tempfile创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(code)
            
            result = subprocess.run(["python", temp_file_path], capture_output=True, text=True)
            
            if result.returncode == 0:
                return Result(True, code, result.stdout, result.stderr, result.returncode)
            else:
                return Result(False, code, result.stdout, result.stderr, result.returncode)
        except Exception as e:
            return Result(False, code, str(e), str(e), -1)
        finally:
            # 确保临时文件被删除，即使发生异常
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass  # 忽略删除临时文件时的错误
  
class StatefulExecutor(Device):
    '''
    有状态的执行器，执行Python代码。
    使用日志收集系统跟踪执行输出。
    '''
    def __init__(self):
        """
        初始化StatefulExecutor实例。
        
        Args:
            session_name (str, optional): 会话名称，用于日志标识。如未提供，将使用随机生成的名称。
            verbose (bool, optional): 是否启用详细日志输出。默认为True。
        """
        # 预先配置matplotlib使用非交互式后端
        import os
        # 设置matplotlib使用非交互式后端
        os.environ['MPLBACKEND'] = 'Agg'
        # 禁用matplotlib的交互功能
        os.environ['MATPLOTLIBRC'] = '/dev/null'
        self.ipython = self._create_ipython_instance()
    
    def execute_code(self, code: str) -> Result:
        '''
        执行给定的Python代码，并返回执行结果。
        
        参数:
        code (str): 要执行的Python代码。k
        
        返回:
        Result: 执行结果对象，包含执行成功与否、代码内容和输出信息。
        '''
        
        import sys
        from io import StringIO
        
        # 初始化输出变量，避免未定义错误
        output = ""
        
        try:
            # 在执行前尝试编译代码以捕获语法错误
            try:
                compile(code, '<string>', 'exec')
            except SyntaxError as e:
                # 直接捕获语法错误并返回
                error_msg = f"语法错误: {str(e)}"
                return Result(False, code, stdout="", stderr=error_msg, return_value=None)
            
            # 创建一个StringIO对象来捕获输出
            captured_output = StringIO()
            
            # 保存原始的stdout和stderr
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            
            # 创建一个同时写入原始stdout和捕获缓冲区的类
            class TeeOutput:
                def __init__(self, original, captured):
                    self.original = original
                    self.captured = captured
                
                def write(self, text):
                    self.original.write(text)
                    self.captured.write(text)
                    self.original.flush()  # 确保实时显示
                
                def flush(self):
                    self.original.flush()
                    self.captured.flush()
                
                @property
                def encoding(self):
                    return getattr(self.original, 'encoding', 'utf-8')
                
                @property
                def errors(self):
                    return getattr(self.original, 'errors', 'strict')
                
                @property
                def fileno(self):
                    return getattr(self.original, 'fileno', None)
                
                def isatty(self):
                    return getattr(self.original, 'isatty', lambda: False)()
                
                @property
                def mode(self):
                    return getattr(self.original, 'mode', 'w')
                
                @property
                def name(self):
                    return getattr(self.original, 'name', '<TeeOutput>')
            
            # 替换stdout和stderr
            sys.stdout = TeeOutput(original_stdout, captured_output)
            sys.stderr = TeeOutput(original_stderr, captured_output)
            
            try:
                # 执行代码
                result = self.ipython.run_cell(code)
                
                # 获取捕获的输出
                output = captured_output.getvalue()
                
                # 检查执行是否成功
                if result.success and result.error_in_exec is None:
                    # 组合返回值和标准输出
                    cell_result = result.result
                    
                    
                    # 添加返回值（如果有且不是None）
                    if cell_result is not None:
                        if output:
                            output += "\n"
                        output += repr(cell_result)
                    return_value=self.get_variable('return_value')
                    return Result(True, code, stdout=output, stderr=None, return_value=return_value)
                else:
                    # 执行失败，返回错误信息
                    error_msg = str(result.error_in_exec)
                    if output:
                        error_msg = f"{output}\n{error_msg}"
                    return Result(False, code, stdout=output, stderr=error_msg, return_value=None)
            except Exception as e:
                error_msg = f"执行异常: {str(e)}"
                return Result(False, code, stdout=output, stderr=error_msg, return_value=None)
            finally:
                # 恢复原始的stdout和stderr
                sys.stdout = original_stdout
                sys.stderr = original_stderr
            
        except Exception as e:
            error_msg = f"执行异常: {str(e)}"
            return Result(False, code, stdout=output, stderr=error_msg, return_value=None)
    
    def get_variable(self, var_name):
        '''
        获取IPython环境中的变量值
        
        参数:
        var_name (str): 变量名
        
        返回:
        any: 变量的值，如果不存在则返回None
        '''
        return self.ipython.user_ns.get(var_name)
    
    def set_variable(self, var_name, value):
        '''
        在IPython环境中设置变量值
        
        参数:
        var_name (str): 变量名
        value (any): 变量值
        '''
        self.ipython.user_ns[var_name] = value
        return True
      
    def _create_ipython_instance(self):
        """
        创建一个IPython实例用于执行代码
        """
        try:
            from IPython.core.interactiveshell import InteractiveShell
            # 创建配置对象
            from traitlets.config import Config
            c = Config()
            # 禁用matplotlib的自动配置
            c.InteractiveShell.pylab = None
            # 禁用各种可能导致GUI相关问题的功能
            c.InteractiveShell.autoindent = False
            c.InteractiveShell.colors = 'NoColor'
            c.InteractiveShell.confirm_exit = False
            # 使用带有配置的InteractiveShell
            ipython = InteractiveShell.instance(config=c, display_banner=False)
            
            # 安全地配置matplotlib (如果有需要)
            try:
                # 设置matplotlib配置以避免GUI初始化
                ipython.run_cell("import matplotlib\nmatplotlib.use('Agg')")
            except Exception as e:
                # 忽略matplotlib相关错误
                pass
                
            return ipython
        except ImportError:
            logging.error("无法导入IPython，某些功能可能不可用")
            return None

class Thinker(AgentBase):
    '''
    代码生成器，把自然语言指令翻译成Python代码并执行。
    包含了代码修改循环
    '''
    def __init__(self,llm:BaseChatModel, max_retries:int=10,thinker_system_message:str=None,thinker_chat_system_message:str=None,
    device:Device=None):
        '''
        Python引擎，把自然语言指令翻译成Python代码并执行。
        包含了代码修改循环
        '''
        super().__init__(llm, thinker_system_message)
        self.llm=llm
        self.thinker_system_message=thinker_system_message
        self.thinker_chat_system_message=thinker_chat_system_message
        self.device=device
        self.max_retries=max_retries
        if self.thinker_system_message is None:
            self.thinker_system_message=mda.prompts.thinker_system_message
            
        if self.thinker_chat_system_message is None:
            self.thinker_chat_system_message=mda.prompts.thinker_chat_system_message
        
        self.memory=[]
        # 如果系统消息不为空，则将其添加到记忆中
        if self.thinker_system_message is not None:
            self.memory.append(SystemMessage(self.thinker_system_message))
            
        # 当前代码
        self.current_code=''

    # def loadKnowledge(self,knowledge:str):
    #     '''
    #     加载知识
    #     '''
    #     self.memory.append(HumanMessage(knowledge))
    #     self.memory.append(AIMessage('ok'))
        
    
    @reduce_memory_decorator_compress
    def chat_stream(self, message: str, response_format: Optional[Dict] = None) -> Iterator[object]:
        """
        与 LLM 进行流式对话
        Args:
            message: 用户输入的消息
            response_format: 可选参数，指定返回格式的字典。例如 {"type": "json_object"}
        Yields:
            object: 模型响应的文本片段或Result对象
        """
        # 保存原始系统消息
        original_system = None
        if len(self.memory) > 0 and isinstance(self.memory[0], SystemMessage):
            original_system = self.memory[0]
            self.memory.remove(original_system)
        try:
            # 临时替换系统消息为聊天模式
            self.memory.insert(0, SystemMessage(self.thinker_chat_system_message))
            # 添加用户消息并获取响应
            self.memory.append(HumanMessage(message))
            content = ''
            # 根据是否提供response_format决定流式调用方式
            if response_format is not None:
                # 带有response_format的流式调用
                for chunk in self.llm.stream(self.memory, response_format=response_format):
                    content += chunk.content
                    yield chunk.content
            else:
                # 默认的流式调用
                for chunk in self.llm.stream(self.memory):
                    content += chunk.content
                    yield chunk.content
            self.memory.append(AIMessage(content))
        finally:
            # 移除临时的聊天模式系统消息
            self.memory.remove(self.memory[0])
            # 还原原始系统消息
            if original_system:
                self.memory.insert(0, original_system)
            # 检查thinker.memory最后一条是否为HumanMessage，如果是则删除
            if len(self.memory) > 0 and isinstance(self.memory[-1], HumanMessage):
                self.memory.pop()
        # 在最后添加一个Result对象
        yield Result(True, "", "", None, content)

    @reduce_memory_decorator_compress
    def chat_sync(self, message: str, response_format: Optional[Dict] = None) -> Result:
        """
        与 LLM 进行同步对话
        Args:
            message: 用户输入的消息
            response_format: 可选参数，指定返回格式的字典。例如 {"type": "json_object"}
        Returns:
            Result: 模型的响应结果，格式由response_format参数决定
        """
        # 保存原始系统消息
        original_system = None
        if len(self.memory) > 0 and isinstance(self.memory[0], SystemMessage):
            original_system = self.memory[0]
            self.memory.remove(original_system)
            
        # 临时替换系统消息为聊天模式
        self.memory.insert(0, SystemMessage(self.thinker_chat_system_message))
        
        # 添加用户消息
        self.memory.append(HumanMessage(message))
        
        # 根据是否提供response_format决定调用方式
        if response_format is not None:
            # 直接传递response_format字典
            response = self.llm.invoke(self.memory, response_format=response_format).content
        else:
            # 普通文本响应
            response = self.llm.invoke(self.memory).content
        
        # 添加AI消息到记忆
        self.memory.append(AIMessage(response))
        
        # 移除临时的聊天模式系统消息
        self.memory.remove(self.memory[0])
        
        # 还原原始系统消息
        if original_system:
            self.memory.insert(0, original_system)
        
        return Result(True, "", "", None, response)
    
    @reduce_memory_decorator_compress
    def execute_sync(self,instruction:str=None)->Result:
        '''
        编程
        直接根据instruction生成代码并执行。
        
        returns:
        Result: 最终结果
        '''
        current_instruction = instruction
        
        for i in range(self.max_retries):
            # region 生成代码
            self.memory.append(HumanMessage(current_instruction))
            content = self.llm.invoke(self.memory).content
            self.memory.append(AIMessage(content))
            
            # 安全地提取代码
            try:
                extracted = extract_code(content)
                if not extracted:
                    current_instruction = "无法从响应中提取代码，请重试。"
                    continue
                
                # current_code = extracted[0][1]
                self.current_code=''
                for language,code in extracted:
                    if language=='python':
                        self.current_code+='\n'+code
                
            except Exception as e:
                error_msg = f"代码提取失败：{str(e)}"
                current_instruction = error_msg
                continue
            #endregion
            
            # region 执行代码
            try:
                result = self.device.execute_code(self.current_code)
                
                if result.success:
                    self.memory.append(HumanMessage(f"当前执行结果：{result}"))
                    self.memory.append(AIMessage('ok'))
                    return result
                else:
                    self.memory.append(HumanMessage(f"代码执行失败：{result}"))
                    self.memory.append(AIMessage('failure'))
                    current_instruction = f"代码执行失败，请修改代码。\n当前代码输出：{result.stdout}\n当前代码错误：{result.stderr}\n当前代码返回值：{result.return_value}"
                    continue
            except Exception as e:
                error_msg = f"执行异常: {str(e)}"
                current_instruction = error_msg
                continue
            #endregion
            
        # 达到最大尝试次数
        return Result(False, self.current_code, "超过最大尝试次数，编程失败。")
    
    @reduce_memory_decorator_compress
    def execute_stream(self,instruction:str=None)->Iterator[object]:
        '''
        编程
        直接根据instruction生成代码并执行。
        返回 一个迭代器，每次迭代返回一个字符串，表示当前的执行结果。
        最终返回一个Result对象，表示最终结果。
        '''
        current_instruction = instruction
        
        for i in range(self.max_retries):
            # region 生成代码
            self.memory.append(HumanMessage(current_instruction))
            content = ''
            for chunk in self.llm.stream(self.memory):
                content += chunk.content
                yield chunk.content
            self.memory.append(AIMessage(content))

            # 安全地提取代码
            try:
                extracted = extract_code(content)
                if not extracted:
                    current_instruction = "无法从响应中提取代码，请重试。"
                    yield Result(False, '', '', '', "无法从响应中提取代码，请重试。")
                    continue

                self.current_code = extracted[0][1]
                # self.current_code=''
                # for language,code in extracted:
                #     if language=='python':
                #         self.current_code+='\n'+code
            except Exception as e:
                error_msg = f"代码提取失败：{str(e)}"
                current_instruction = error_msg
                yield Result(False, '', '', '', error_msg)
                continue
            #endregion
            
            
            try:
                #region 执行代码
                result = self.device.execute_code(self.current_code)
                
                # 安全处理可能的None值
                stdout = result.stdout or ""
                stderr = result.stderr or ""
                try:
                    return_value = result.return_value or ""
                except:
                    return_value = ""
                
                yield 'Thinker execute_stream'
                yield "\n当前命令：" + current_instruction
                yield "\n当前代码：" + self.current_code
                yield "\n当前标准输出：" + stdout
                yield "\n当前标准错误：" + stderr
                try:
                    yield "\n当前返回值：" + str(return_value)
                except:
                    yield "\n当前返回值：无法转换为字符串的结果"
                #endregion
                
                #region 如果执行成功，返回结果,结束迭代,如果执行失败，返回失败原因，继续迭代
                if result.success:
                    self.memory.append(HumanMessage(f"当前执行结果：{result}"))
                    self.memory.append(AIMessage('ok'))
                    yield result
                    return
                else:
                    self.memory.append(HumanMessage(f"代码执行失败：{result}"))
                    self.memory.append(AIMessage('failure'))
                    yield result
                    current_instruction = f"代码执行失败，请修改代码。\n当前代码输出：{result.stdout}\n当前代码错误：{result.stderr}\n当前代码返回值：{result.return_value}"
                    continue
                #endregion
            except Exception as e:
                # region 出现异常，返回异常原因，继续迭代
                error_msg = "执行异常: " + str(e)
                yield error_msg
                current_instruction = error_msg
                continue
                #endregion
            
            
        
        # 达到最大尝试次数
        yield Result(False, self.current_code,None,None,"超过最大尝试次数，编程失败。")

    @reduce_memory_decorator_compress
    def chat_sync(self, message: str, response_format: Optional[Dict] = None) -> Result:
        """
        与 LLM 进行同步对话
        Args:
            message: 用户输入的消息
            response_format: 可选参数，指定返回格式的字典。例如 {"type": "json_object"}
        Returns:
            Result: 模型的响应结果，格式由response_format参数决定
        """
        # 保存原始系统消息
        original_system = None
        if len(self.memory) > 0 and isinstance(self.memory[0], SystemMessage):
            original_system = self.memory[0]
            self.memory.remove(original_system)
            
        try:
            # 临时替换系统消息为聊天模式
            self.memory.insert(0, SystemMessage(self.thinker_chat_system_message))
            
            # 添加用户消息
            self.memory.append(HumanMessage(message))
            
            # 根据是否提供response_format决定调用方式
            if response_format is not None:
                # 直接传递response_format字典
                response = self.llm.invoke(self.memory, response_format=response_format).content
            else:
                # 普通文本响应
                response = self.llm.invoke(self.memory).content
            
            # 添加AI消息到记忆
            self.memory.append(AIMessage(response))
        finally:
            # 移除临时的聊天模式系统消息
            self.memory.remove(self.memory[0])
            
            # 还原原始系统消息
            if original_system:
                self.memory.insert(0, original_system)
                
            # 检查thinker.memory最后一条是否为HumanMessage，如果是则删除
            last_msg = self.memory[-1]
            if isinstance(last_msg, HumanMessage):
                self.memory.pop()
            
        return Result(True, "", "", None, response)


class Evaluator:
    '''行为评估器'''
    def __init__(self,llm:BaseChatModel,systemMessage:str,thinker:Thinker=None):
        self.llm=llm
        self.knowledges=[]
        self.thinker=thinker
        self.system_message=systemMessage
        if self.system_message is None:
            self.system_message=default_evaluate_message

    def loadKnowledge(self,knowledge:str):
        self.knowledges.append(knowledge)
        
    def evaluate(self,instruction:str,result:Result)->Tuple[bool,str]:
        '''
        评估任务是否完成.
        返回值：是否完成，原因
        '''
        # 导入需要的模块
        import re
        import json
        
        # 安全处理结果中可能的None值
        code = result.code or ""
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        # return_value = result.return_value or ""
        
        # 检查是否有明显错误
        if stderr and ("Error" in stderr or "Exception" in stderr):
            return False, f"代码执行出错: {stderr}"
        
        # 使用系统消息模板格式化提示
        try:
            prompt=PromptTemplate.from_template(self.system_message).format(
                instruction=instruction,
                result=result,
                knowledges=self.knowledges,
            )
            logging.debug("打印评估器提示模板:")
            logging.debug(f"系统消息长度: {len(self.system_message)} 字符")
            logging.debug(f"系统消息前100字符: {self.system_message[:100]}...")
        except Exception as e:
            logging.error(f"模板格式化错误: {str(e)}")
            return False, f"评估模板格式化失败: {str(e)}"
        
        # 尝试使用LLM进行评估
        counter=0
        while counter<3:
            try:
                logging.debug(f"尝试LLM评估 (第{counter+1}次)")
                x=self.llm.invoke(prompt)
                content = x.content
                logging.debug(f"LLM评估响应长度: {len(content)} 字符")
                logging.debug(f"LLM评估响应前200字符:\n{content[:200]}...")
                
                # 尝试从内容中提取代码块
                extracted = extract_code(content)
                if not extracted or len(extracted) == 0:
                    logging.debug("未从响应中提取到代码块，尝试直接解析JSON")
                    # 如果没有提取到代码块，尝试直接从内容中解析JSON
                    try:
                        # 尝试从文本中找到JSON格式的内容
                        json_pattern = r'(\{.*"taskIsComplete"\s*:\s*(true|false).*\})'
                        match = re.search(json_pattern, content, re.DOTALL)
                        
                        if match:
                            json_str = match.group(1)
                            logging.debug(f"找到JSON字符串: {json_str}")
                            j = json.loads(json_str)
                        else:
                            # 尝试查找任何花括号包围的内容
                            braces_pattern = r'(\{.*\})'
                            match = re.search(braces_pattern, content, re.DOTALL)
                            if match:
                                json_str = match.group(1)
                                logging.debug(f"找到可能的JSON字符串: {json_str}")
                                try:
                                    j = json.loads(json_str)
                                except:
                                    logging.debug("发现花括号内容，但非有效JSON")
                                    # 作为最后尝试，尝试提取true/false和原因
                                    is_complete = "true" in content.lower() and "false" not in content.lower()
                                    reason = "无法解析评估结果，基于文本判断"
                                    return is_complete, reason
                            else:
                                # 作为后备，尝试提取true/false和原因
                                logging.debug("未找到JSON格式内容，尝试基于文本判断")
                                is_complete = "true" in content.lower() and "false" not in content.lower()
                                reason = "无法解析评估结果，基于文本判断"
                                return is_complete, reason
                    except Exception as e:
                        logging.error(f"JSON解析尝试失败: {str(e)}")
                        counter += 1
                        continue
                else:
                    logging.debug(f"从响应中提取到代码块，语言: {extracted[0][0]}")
                    # 正常从代码块中提取JSON
                    try:
                        j = json.loads(extracted[0][1])
                    except:
                        logging.debug("代码块不是有效的JSON，尝试清理后重新解析")
                        # 如果代码块不是有效的JSON，尝试清理并重新解析
                        try:
                            cleaned_json = extracted[0][1].strip().replace("```", "").strip()
                            logging.debug(f"清理后的JSON字符串: {cleaned_json[:100]}...")
                            j = json.loads(cleaned_json)
                        except Exception as e:
                            logging.error(f"清理后JSON解析失败: {str(e)}")
                            counter += 1
                            continue
                
                # 提取任务完成状态和原因
                taskIsComplete = j.get('taskIsComplete', False)
                reason = j.get('reason', '未提供评估原因')
                
                # 处理可能的字符串类型的布尔值
                if isinstance(taskIsComplete, str):
                    logging.debug(f"任务完成状态是字符串类型: '{taskIsComplete}'")
                    taskIsComplete = taskIsComplete.lower() == 'true'
                
                logging.debug(f"任务是否完成：{taskIsComplete}")
                logging.debug(f"原因：{reason}")
                return taskIsComplete, reason
                
            except Exception as e:
                logging.error(f"评估过程出错: {str(e)}")
                counter += 1
        
        # 如果LLM评估失败，作为兜底使用简单的规则
        logging.info("三次LLM评估尝试均失败，使用兜底规则")
        # 通用任务成功判断（作为兜底）
        if "任务完成" in stdout and not stderr:
            logging.info("LLM评估失败，使用兜底判断：检测到'任务完成'")
            return True, "任务执行成功并输出了完成标记（兜底判断）"
        
        # 检查代码中是否包含断言（作为兜底）
        if "assert" in code and "任务完成" in stdout:
            logging.info("LLM评估失败，使用兜底判断：检测到断言验证并成功")
            return True, "代码包含断言验证并成功执行（兜底判断）"
        
        # 超过最大尝试次数，但看起来是一个成功的执行
        if result.success and stdout and not stderr:
            logging.info("评估失败，但代码执行成功，默认通过")
            return True, "代码执行成功，无法进行详细评估"
        
        # 超过最大尝试次数，返回默认值
        logging.info("评估失败，返回默认值")
        return False, "评估过程出错，无法判断任务是否完成"

class Agent(AgentBase):
    '''
    智能体
    run方法：输入自然语言，翻译成Python代码，执行代码，评估代码执行结果，生成最终结果
    chat方法：输入自然语言，输出自然语言，无副作用
    '''
    def __init__(self, llm:BaseChatModel,stateful:bool=True,evaluate_llm:BaseChatModel=None, max_retries:int=10,
                 skip_evaluation:bool=False,
                 skip_generation:bool=False,
                 thinker_system_message:str=None,
                 evaluation_system_messages:List[str]=None,
                 thinker_chat_system_message:str=None):
        self.llm = llm
        self.name=''
        if not evaluate_llm:
            self.evaluate_llm=self.llm
        else:
            self.evaluate_llm=evaluate_llm
        self.max_retries = max_retries
        self.skip_evaluation = skip_evaluation # 是否跳过评估
        self.skip_generation = skip_generation
        self.device=Device() if not stateful else StatefulExecutor() 
        self.thinker = Thinker(llm=self.llm, 
                                      max_retries=max_retries,
                                      thinker_system_message=thinker_system_message,
                                      thinker_chat_system_message=thinker_chat_system_message,
                                      device=self.device)
        
        # 初始化多个评估器
        self.evaluators = []
        if evaluation_system_messages:
            for system_message in evaluation_system_messages:
                evaluator = Evaluator(llm=self.evaluate_llm, systemMessage=system_message,thinker=self.thinker)
                self.evaluators.append(evaluator)
        else:
            # 如果没有提供评估消息，至少创建一个默认评估器
            self.evaluators.append(Evaluator(llm=self.evaluate_llm, systemMessage=default_evaluate_message,thinker=self.thinker))

    # @log_expert_execution()
    # @reduce_memory_decorator    
    def chat_stream(self,message:str,response_format:Optional[Dict]=None)->Iterator[object]:
        '''
        与LLM进行对话
        '''
        content = ""
        for chunk in self.thinker.chat_stream(message, response_format):
            if isinstance(chunk, str):
                content += chunk
                yield chunk
            elif isinstance(chunk, Result):
                yield chunk
            else:
                try:
                    chunk_str = str(chunk)
                    content += chunk_str
                    yield chunk_str
                except:
                    pass
        yield Result(True, "", "", None, content)
    
    # @log_expert_execution()    
    # @reduce_memory_decorator    
    def chat_sync(self,message:str,response_format:Optional[Dict]=None)->Result:
        '''
        与LLM进行同步对话
        '''
        return self.thinker.chat_sync(message,response_format)
    
    def loadEvaluationSystemMessage(self,evaluationSystemMessage:str):
        '''
        添加新的评估系统消息。
        这个方法会创建一个新的评估器并添加到现有评估器列表中，而不会清除现有评估器。
        如果需要清除现有评估器，请使用resetEvaluators方法。
        
        参数:
        evaluationSystemMessage (str): 评估器使用的系统消息
        
        返回:
        int: 当前评估器数量
        '''
        # 添加新的评估器，保留现有评估器
        new_evaluator = Evaluator(llm=self.evaluate_llm, systemMessage=evaluationSystemMessage, thinker=self.thinker)
        self.evaluators.append(new_evaluator)
        logging.info(f"已添加新的评估系统消息，当前评估器数量: {len(self.evaluators)}")
        return len(self.evaluators)

    def loadKnowledge(self, knowledge:str):
        '''
        加载知识
        '''
        self.thinker.loadKnowledge(knowledge)
        for evaluator in self.evaluators:
            evaluator.loadKnowledge(knowledge)

    def loadPythonModules(self,pythonModules:List[str]):
        '''
        加载python模块
        '''
        knowledge=""
        for module_name in pythonModules:
            module = import_module(module_name)
            knowledge+=f'以下python模块已经导入：{module_name}\n'
            knowledge+=f'模块源码如下：\n{inspect.getsource(module)}\n\n'
        self.loadKnowledge(knowledge)
        for module_name in pythonModules:
            if isinstance(self.device,StatefulExecutor):
                self.device.execute_code(f'import importlib\nimport {module_name}\nimportlib.reload({module_name})')   
        
    def evaluate_all(self, result:Result, instruction:str=None) -> Tuple[bool, List[str]]:
        '''
        使用所有评估器进行评估。如果任何一个评估器失败，立即返回失败结果。
        
        参数:
        result (Result): 代码执行结果
        instruction (str, optional): 用户的原始指令，用于评估。默认为None时使用"执行任务"作为占位符。
        
        返回值：(是否所有评估都通过, 评估原因列表)
        '''
        logging.info('=== 开始评估 ===')
        
        # 如果没有提供instruction，使用默认值
        if instruction is None:
            instruction = "执行任务"
        
        # 安全处理可能的None值
        stdout = result.stdout or ""
        
        
        # 打印执行结果的最后5000个字符
        last_5000_chars = stdout[-5000:] if len(stdout) > 5000 else stdout
        logging.debug(f'执行结果最后5000个字符:\n{last_5000_chars}')
        
        # 为了评估使用较短的输出
        result_for_eval = Result(
            result.success,
            result.code,
            last_5000_chars,
            result.stderr,
            result.return_value
        )

        reasons = []
        failures = []  # 收集失败的评估结果
        
        # 执行所有评估器的评估
        if self.evaluators:
            logging.info(f"使用 {len(self.evaluators)} 个评估器进行评估...")
            for i, evaluator in enumerate(self.evaluators):
                try:
                    logging.info(f"执行评估器 #{i+1}:")
                    # 传递用户的instruction，而不是固定的占位符
                    is_complete, reason = evaluator.evaluate(instruction, result_for_eval)
                    
                    if is_complete:
                        logging.info(f"评估器 #{i+1} 评估结果: 成功")
                        reasons.append(reason)
                    else:
                        logging.info(f"评估器 #{i+1} 评估结果: 失败 - {reason}")
                        failures.append(reason)
                        # 任何一个评估器失败，立即返回失败结果
                        logging.info("=== 评估总结 ===")
                        logging.info(f"至少一个评估器失败，整体评估结果: 失败")
                        logging.info(f"失败原因: {reason}")
                        return False, failures + reasons  # 将失败原因放在前面
                    
                except Exception as e:
                    error_msg = f"评估器 #{i+1} 异常: {str(e)}"
                    logging.error(error_msg)
                    reasons.append(error_msg)
                    # 继续下一个评估器，而不是立即失败
        
        # 如果有评估结果并且都通过了（没有提前返回False），则认为任务完成
        if reasons:
            logging.info("=== 评估总结 ===")
            logging.info(f"所有评估器都通过，整体评估结果: 成功")
            for i, reason in enumerate(reasons):
                logging.info(f"成功原因 #{i+1}: {reason}")
            return True, reasons
        
        # 兜底逻辑 - 如果没有评估结果，使用通用成功判断作为兜底
        logging.info("没有评估器返回结果，使用兜底逻辑...")
        
        # 通用成功判断 - 如果程序输出中包含"任务完成"并且没有错误
        if "任务完成" in last_5000_chars and not result.stderr:
            logging.info('检测到任务完成标记，评估通过（兜底逻辑）')
            return True, ["任务执行成功并输出了完成标记（通用判断）"]
        
        # 如果有断言和成功标记，也认为成功
        if "assert" in result.code and "任务完成" in last_5000_chars:
            logging.info('检测到断言验证并成功执行（兜底逻辑）')
            return True, ["代码包含断言验证并成功执行（通用判断）"]
        
        # 如果没有评估器结果，且通用判断也没通过，根据代码执行结果返回
        logging.info("=== 评估总结（兜底结果）===")
        if result.success:
            logging.info(f"代码执行成功，默认评估结果: 成功")
            return True, ["代码执行成功，无明确评估结果"]
        else:
            logging.info(f"代码执行失败，默认评估结果: 失败")
            return False, ["代码执行失败，无明确评估结果"]

    # @log_expert_execution()
    # @reduce_memory_decorator    
    def execute_sync(self, instruction:str) -> Result:
        # 首先判断指令是否为动作类型
        is_action = self.thinker.classify_instruction(instruction)
        if not is_action:
            # 如果不是动作类型，则调用chat_sync方法
            response = self.thinker.chat_sync(instruction)
            return Result(True, "", response, None, response)
            
        current_instruction = instruction
        
        # region 跳过评估循环
        if self.skip_evaluation:
            if self.skip_generation:
                return self.thinker.execute_sync(current_instruction)
            else:
                result = self.thinker.execute_sync(current_instruction)
                if isinstance(result, Result):
                    finalResult = self.generateResult_sync(instruction, result)
                    return Result(result.success, result.code, result.stdout,result.stderr,finalResult)
            return
        #endregion
        
        # region 评估循环
        for i in range(self.max_retries):
            # region 执行代码
            result = self.thinker.execute_sync(current_instruction)
            #endregion
            
            if result.success:
                # region 如果执行成功，执行评估，如果评估成功，生成最终结果，如果评估失败，使用失败原因作为下一次尝试的指令
                taskIsComplete, reasons = self.evaluate_all(result, instruction)
                
                
                if taskIsComplete:
                    if not self.skip_generation:
                        finalResult = self.generateResult_sync(instruction, result)
                        return Result(True, result.code, result.stdout,result.stderr,finalResult)
                    else:
                        return Result(True, result.code, result.stdout,result.stderr,result.return_value)
                else:
                    # 使用失败的原因作为下一次尝试的指令
                    # 失败的原因总是在返回的reasons列表的前面
                    failure_reason = reasons[0] if reasons else "未提供具体原因"
                    current_instruction = f"评估失败，请修改代码。原因：{failure_reason}\n当前代码输出：{result.stdout}\n当前代码错误：{result.stderr}\n当前代码返回值：{result.return_value}"
                    
                #endregion
            else:
                # region 如果执行失败，生成最终结果
                if not self.skip_generation:
                    finalResult = self.generateResult_sync(instruction, result)
                    return Result(False, result.code, result.stdout,result.stderr,finalResult)
                else:
                    return Result(False, result.code, result.stdout,result.stderr,result.return_value)
                #endregion
        #endregion
        
        print('超过最大尝试次数，编程失败。')
        return Result(False, '', '', '', '超过最大尝试次数，编程失败。')

    # @log_expert_execution()    
    # @reduce_memory_decorator    
    def execute_stream(self, instruction:str) -> Iterator[object]:
        '''
        执行指令，返回一个迭代器，迭代器每次返回一个字符串或Result对象
        '''
        # 如果不是动作类型，则调用chat_stream方法
        if not self.classify_instruction(instruction):
            logger.debug("指令类型：思维")
            yield from self.thinker.chat_stream(instruction)
            # content = ""
            # for chunk in self.thinker.chat_stream(instruction):
            #     if isinstance(chunk, str):
            #         content += chunk
            #         yield chunk
            #     elif isinstance(chunk, Result):
            #         yield chunk
            #     else:
            #         try:
            #             chunk_str = str(chunk)
            #             content += chunk_str
            #             yield chunk_str
            #         except:
            #             pass
            # yield Result(True, "", "", None, content)
            # return
            
        current_instruction = instruction
        
        # region 跳过评估循环
        if self.skip_evaluation:
            if self.skip_generation:
                last_result = None
                for r in self.thinker.execute_stream(current_instruction):
                    yield r
                    if isinstance(r, Result):
                        last_result = r
                if last_result is None:
                    yield Result(False, '', '', '', '未能获取到有效的执行结果')
            else:
                result = None
                # 保存最后一个结果用于生成最终输出
                for r in self.thinker.execute_stream(current_instruction):
                    yield r
                    if isinstance(r, Result):
                        result = r
                # 生成最终结果
                if isinstance(result, Result):
                    finalResult = ''
                    for chunk in self.generateResult_stream(instruction, result):
                        finalResult += chunk
                        yield chunk
                    yield Result(result.success, result.code, result.stdout, result.stderr, finalResult)
                else:
                    yield Result(False, '', '', '', '未能获取到有效的执行结果')
            return
        #endregion
        
        # region 评估循环
        for i in range(self.max_retries):
            result = None
            # 保存最后一个结果用于评估和生成
            for r in self.thinker.execute_stream(current_instruction):
                yield r
                # 只有当r是Result对象时才更新result
                if isinstance(r, Result):
                    result = r
            
            # 确保我们有一个有效的Result对象
            if not isinstance(result, Result):
                yield Result(False, '', '', '', '未能获取到有效的执行结果')
                continue
            #endregion
            
            try:
                if result.success:
                    # 编程成功，做评估循环
                    taskIsComplete, reasons = self.evaluate_all(result, instruction)
                    yield f"评估结果：\n是否成功：{taskIsComplete}\n理由:{reasons}"
                    if taskIsComplete:
                        # 评估成功
                        if not self.skip_generation:
                            # 如果需要生成，生成最终结果
                            finalResult = ''
                            for chunk in self.generateResult_stream(instruction, result):
                                finalResult += chunk
                                yield chunk
                            yield Result(True, result.code, result.stdout, result.stderr, finalResult)
                        else:
                            # 如果不需要生成，返回执行结果
                            yield Result(True, result.code, result.stdout, result.stderr, result.return_value)
                        return
                    else:
                        # 至少有一个评估失败，使用失败原因作为下一次尝试的指令
                        # 安全处理可能的None值
                        stdout = result.stdout or ""
                        stderr = result.stderr or ""
                        return_value = result.return_value or ""
                        
                        # 失败的原因总是在返回的reasons列表的前面
                        failure_reason = reasons[0] if reasons else "未提供具体原因"
                        current_instruction = f"评估失败，请修改代码。原因：{failure_reason}\n当前代码输出：{stdout}\n当前代码错误：{stderr}\n当前代码返回值：{return_value}"
                else:
                    # 编程失败，无需评估循环
                    if not self.skip_generation:
                        # 如果需要生成，生成最终结果
                        finalResult = ''
                        for chunk in self.generateResult_stream(instruction, result):
                            finalResult += chunk
                            yield chunk
                        yield Result(False, result.code, result.stdout, result.stderr, finalResult)
                    else:
                        # 如果不需要生成，返回执行结果
                        yield Result(False, result.code, result.stdout, result.stderr, result.return_value)
                    return
            except Exception as e:
                # 处理评估过程中的异常
                error_msg = f"评估或结果处理过程中出现错误: {str(e)}"
                logging.error(error_msg)
                yield error_msg
                
                # 跳过评估，直接使用结果
                if not self.skip_generation:
                    # 如果需要生成，生成最终结果
                    try:
                        finalResult = ''
                        for chunk in self.generateResult_stream(instruction, result):
                            finalResult += chunk
                            yield chunk
                        yield Result(result.success, result.code, result.stdout, result.stderr, finalResult)
                    except Exception as gen_error:
                        # 如果生成过程也失败，返回原始结果
                        yield f"生成最终响应时出错: {str(gen_error)}"
                        yield Result(result.success, result.code, result.stdout, result.stderr, str(gen_error))
                else:
                    # 如果不需要生成，返回执行结果
                    yield Result(result.success, result.code, result.stdout, result.stderr, result.return_value)
                return
            #endregion
            
        logging.info('超过最大尝试次数，编程失败。')
        yield Result(False, '', '', '', '超过最大尝试次数，编程失败。')
        yield '以下是重现错误的代码'
        prompt = '''把上一步的出现错误的代码输出出来，以供调试'''
        yield from self.chat_stream(prompt)
    
    def generateResult_sync(self, instruction:str, result:Result) -> str:
        '''
        生成最终结果
        '''
        logger.info('开始生成指令最终结果')
        # logger.info(f'instruction: {instruction}')
        logger.info(f'result.success: {result.success}')
        logger.info(f'result.code: {result.code}')
        logger.info(f'result.stdout: {result.stdout}')
        logger.info(f'result.stderr: {result.stderr}')
        logger.info(f'result.return_value: {result.return_value}')
        
        # 安全处理可能的None值
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        return_value = result.return_value or ""
        code = result.code or ""
        
        last_5000_chars = stdout[-5000:] if len(stdout) > 5000 else stdout
        
        generate_result_prompt = f'''
        我是个语言模型，根据用户的指令，我生成了Python代码，并执行了代码。
        请根据用户指令给用户生成回复。

        # 用户指令：
        
        {instruction}

        # 任务是否执行成功：
        {result.success}

        # 代码：
        {code}

        # 代码执行的标准输出：

        {last_5000_chars}

        # 代码执行的标准错误：

        {stderr}

        # 代码执行的返回值：

        {return_value}
        '''
        content = self.llm.invoke(generate_result_prompt).content
        return content
    #TODO  生成回复的提示词应该外部化    
    def generateResult_stream(self, instruction:str, result:Result) -> Iterator[str]:
        logger.info('开始生成指令最终结果')
        # logger.info(f'instruction: {instruction}')
        logger.info(f'result.success: {result.success}')
        logger.info(f'result.code: {result.code}')
        logger.info(f'result.stdout: {result.stdout}')
        logger.info(f'result.stderr: {result.stderr}')
        logger.info(f'result.return_value: {result.return_value}')
        
        # 安全处理可能的None值
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        return_value = result.return_value or ""
        code = result.code or ""
        
        last_5000_chars = stdout[-5000:] if len(stdout) > 5000 else stdout
        
        generate_result_prompt = f'''
        我是个语言模型，根据用户的指令，我生成了Python代码，并执行了代码。
        请根据用户指令给用户生成回复。

        # 用户指令：
        
        {instruction}

        # 任务是否执行成功：
        {result.success}

        # 代码：
        {code}

        # 代码执行的标准输出：

        {last_5000_chars}

        # 代码执行的标准错误：

        {stderr}

        # 代码执行的返回值：

        {return_value}
        
        '''
        
        
        for chunk in self.llm.stream(generate_result_prompt):
            yield chunk.content

    def resetEvaluators(self, evaluationSystemMessage: str = None):
        '''
        重置所有评估器。
        可以选择性地添加一个新的评估器。
        
        参数:
        evaluationSystemMessage (str, optional): 评估器使用的系统消息。如果提供，将创建一个新的评估器。
        '''
        # 清除所有现有评估器
        self.evaluators = []
        logging.info("已清除所有评估器")
        
        # 如果提供了评估系统消息，则添加一个新的评估器
        if evaluationSystemMessage is not None:
            self.evaluators.append(Evaluator(llm=self.evaluate_llm, systemMessage=evaluationSystemMessage, thinker=self.thinker))
            logging.info(f"已创建新评估器，当前评估器数量: {len(self.evaluators)}")
        else:
            # 如果没有提供评估消息，添加一个默认评估器
            self.evaluators.append(Evaluator(llm=self.evaluate_llm, systemMessage=default_evaluate_message, thinker=self.thinker))
            logging.info(f"已创建默认评估器，当前评估器数量: {len(self.evaluators)}")



# %%
# if __name__ == '__main__':
#     llm = llm_gemini_2_flash_lite_google
#     agent = Agent(llm=llm,stateful=True)
#     instruction = "写个hello world程序"
#     result=None
#     for chunk in agent.execute_stream(instruction):
#         print(chunk,end='',flush=True)
#         result=chunk
        
# %%

   
# %%
# if __name__ == '__main__':
#     custom_evaluate_message = '''
#     请判断是否完成了任务。请返回json格式的结果。
#     json有两个字段，taskIsComplete，值为true或false，reason字段，字符串类型，判断的理由。

#     # 判断规则：
#         hello world必须是中文的：你好，世界
        
#     # 知识：
#     {knowledges}

#     # 任务：

#     {instruction}


#     # 代码执行结果：

#     {result}

#     '''
#     llm = llm_gemini_2_flash_google
#     agent = Agent(llm=llm,stateful=True,max_retries=3)
#     agent.loadEvaluationSystemMessage(custom_evaluate_message)
#     instruction = "写个hello world程序"
#     result=None
#     for chunk in agent.execute_stream(instruction):
#         print(chunk,end='',flush=True)
#         result=chunk
        
#     print('*'*100)
#     # 注释掉有问题的print语句，这个result可能只在某些上下文中可用
#     # %%
#     print(result)
#     # %%
#     print(agent.device.get_variable('return_value'))
# %%
if __name__ == '__main__':
    # 创建有状态执行器示例
    executor = StatefulExecutor()
    
    # 示例1: 定义变量并使用
    code1 = """
x = 100
y = 200
result = x + y
print(f'计算结果: {result}')
return_value = 123
"""
    result1 = executor.execute_code(code1)
    print("\n示例1执行结果:")
    print(f"执行成功: {result1.success}")
    print(f"输出:\n{result1.stdout}")

    # 示例2: 使用之前定义的变量
    code2 = """
# 可以访问之前定义的变量
z = result * 2
print(f'之前的结果: {result}')
print(f'新的计算结果: {z}')
return_value = z
"""
    result2 = executor.execute_code(code2)
    print("\n示例2执行结果:")
    print(f"执行成功: {result2.success}")
    print(f"输出:\n{result2.stdout}")
    print(f"返回值:\n{result2.return_value}")

    # 示例3: 导入模块并进行计算
    code3 = """
import numpy as np

# 创建数组并计算
arr = np.array([1, 2, 3, 4, 5])
mean_value = np.mean(arr)
print(f'数组平均值: {mean_value}')
return_value = mean_value
"""
    result3 = executor.execute_code(code3)
    print("\n示例3执行结果:")
    print(f"执行成功: {result3.success}")
    print(f"输出:\n{result3.stdout}")
    print(f"返回值:\n{result3.return_value}")

