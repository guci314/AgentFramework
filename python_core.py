"""
Python执行核心模块

包含Agent、Device、StatefulExecutor等核心类，不包含语言模型定义。
导入速度快，适合只需要核心功能的场景。
"""

import os
import json
import sys
import logging
import tempfile
import subprocess
import time
import inspect
from importlib import import_module
from typing import Callable, Dict, List, Optional, Tuple, Union, Literal, Iterator
from functools import wraps
from dotenv import load_dotenv

# 导入psutil补丁
try:
    import psutil_patch
    psutil_patch.ensure_psutil_imported()
except ImportError as e:
    print(f"Warning: Could not import psutil_patch: {e}")

# 替换 autogen 导入，使用本地实现
import re

def extract_code(text: str, lang: str = None):
    """
    从文本中提取代码块
    返回 [(语言, 代码)] 的列表
    """
    # 匹配 ```language 或 ``` 开头的代码块
    pattern = r'```(?:(\w+)\s*)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        result = []
        for language, code in matches:
            # 如果没有指定语言，默认为 python
            if not language:
                language = 'python'
            result.append((language, code.strip()))
        return result
    else:
        # 如果没有找到代码块，尝试查找简单的代码模式
        lines = text.split('\n')
        code_lines = []
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith('import ') or 
                stripped.startswith('from ') or
                stripped.startswith('def ') or
                stripped.startswith('class ') or
                stripped.startswith('print(') or
                '=' in stripped and not stripped.startswith('#')):
                code_lines.append(line)
        
        if code_lines:
            return [('python', '\n'.join(code_lines))]
        else:
            return [('python', text)]

# 导入核心依赖
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage, BaseMessage, FunctionMessage
from langchain_core.language_models import BaseChatModel
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from IPython.terminal.interactiveshell import TerminalInteractiveShell
from IPython.utils.capture import capture_output
import prompts
import IPython

# 配置日志
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

logger = logging.getLogger("python_core")

def _map_log_level(custom_level_int):
    """Maps custom integer levels to standard logging levels."""
    if custom_level_int == 3:
        return logging.DEBUG
    elif custom_level_int == 2:
        return logging.INFO
    elif custom_level_int == 1:
        return logging.ERROR
    elif custom_level_int == 0:
        return logging.CRITICAL + 1
    else:
        return logging.INFO

load_dotenv()
max_turn = 5

# 导入AgentBase和Result
from agent_base import AgentBase, Result, reduce_memory_decorator, reduce_memory_decorator_compress
from prompts import default_evaluate_message

# 缓存配置
from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache
set_llm_cache(SQLiteCache(database_path=".langchain.db"))

max_messages = 50

class Device:
    '''
    执行器，执行Python代码。
    '''
    def execute_code(self, code: str) -> Result:
        '''
        执行给定的Python代码，并返回执行结果。
        
        参数:
        code (str): 要执行的Python代码。
        
        返回:
        Result: 执行结果对象，包含执行成功与否、代码内容和输出信息。
        '''
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(code)
            
            result = subprocess.run(["python", temp_file_path], capture_output=True, text=True)
            
            if result.returncode == 0:
                return Result(True, code, result.stdout, result.stderr, None)
            else:
                return Result(False, code, result.stdout, result.stderr, None)
        except Exception as e:
            return Result(False, code, str(e), str(e), None)
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

class StatefulExecutor(Device):
    '''
    有状态的执行器，执行Python代码。
    使用IPython实现状态保持。
    '''
    def __init__(self):
        # 预先配置matplotlib使用非交互式后端
        os.environ['MPLBACKEND'] = 'Agg'
        os.environ['MATPLOTLIBRC'] = '/dev/null'
        self.ipython = self._create_ipython_instance()
    
    def execute_code(self, code: str) -> Result:
        '''
        执行给定的Python代码，并返回执行结果。
        '''
        import sys
        from io import StringIO
        
        output = ""
        
        try:
            # 编译检查
            try:
                compile(code, '<string>', 'exec')
            except SyntaxError as e:
                error_msg = f"语法错误: {str(e)}"
                return Result(False, code, stdout="", stderr=error_msg, return_value=None)
            
            captured_output = StringIO()
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            
            class TeeOutput:
                def __init__(self, original, captured):
                    self.original = original
                    self.captured = captured
                
                def write(self, text):
                    self.original.write(text)
                    self.captured.write(text)
                    self.original.flush()
                
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
            
            sys.stdout = TeeOutput(original_stdout, captured_output)
            sys.stderr = TeeOutput(original_stderr, captured_output)
            
            try:
                result = self.ipython.run_cell(code)
                output = captured_output.getvalue()
                
                if result.success and result.error_in_exec is None:
                    cell_result = result.result
                    
                    if cell_result is not None:
                        if output:
                            output += "\n"
                        output += repr(cell_result)
                    return_value = self.get_variable('return_value')
                    return Result(True, code, stdout=output, stderr=None, return_value=return_value)
                else:
                    error_msg = str(result.error_in_exec)
                    if output:
                        error_msg = f"{output}\n{error_msg}"
                    return Result(False, code, stdout=output, stderr=error_msg, return_value=None)
            except Exception as e:
                error_msg = f"执行异常: {str(e)}"
                return Result(False, code, stdout=output, stderr=error_msg, return_value=None)
            finally:
                sys.stdout = original_stdout
                sys.stderr = original_stderr
            
        except Exception as e:
            error_msg = f"执行异常: {str(e)}"
            return Result(False, code, stdout=output, stderr=error_msg, return_value=None)
    
    def get_variable(self, var_name):
        '''获取IPython环境中的变量值'''
        return self.ipython.user_ns.get(var_name)
    
    def set_variable(self, var_name, value):
        '''在IPython环境中设置变量值'''
        self.ipython.user_ns[var_name] = value
        return True
      
    def _create_ipython_instance(self):
        """创建一个IPython实例用于执行代码"""
        try:
            from IPython.core.interactiveshell import InteractiveShell
            from traitlets.config import Config
            c = Config()
            c.InteractiveShell.autoindent = False
            c.InteractiveShell.colors = 'NoColor'
            ipython = InteractiveShell.instance(config=c, display_banner=False)
            
            try:
                ipython.run_cell("import matplotlib\nmatplotlib.use('Agg')")
            except Exception:
                pass
                
            return ipython
        except ImportError:
            logging.error("无法导入IPython，某些功能可能不可用")
            return None

class Thinker(AgentBase):
    '''
    代码生成器，把自然语言指令翻译成Python代码并执行。
    '''
    def __init__(self, llm: BaseChatModel, max_retries: int = 10, 
                 thinker_system_message: str = None,
                 thinker_chat_system_message: str = None,
                 device: Device = None):
        super().__init__(llm, thinker_system_message)
        self.llm = llm
        self.thinker_system_message = thinker_system_message
        self.thinker_chat_system_message = thinker_chat_system_message
        self.device = device
        self.max_retries = max_retries
        
        if self.thinker_system_message is None:
            self.thinker_system_message = prompts.thinker_system_message
            
        if self.thinker_chat_system_message is None:
            self.thinker_chat_system_message = prompts.thinker_chat_system_message
        
        self.memory = []
        if self.thinker_system_message is not None:
            self.memory.append(SystemMessage(self.thinker_system_message))
            
        self.current_code = ''

    @reduce_memory_decorator_compress
    def chat_stream(self, message: str, response_format: Optional[Dict] = None) -> Iterator[object]:
        """与 LLM 进行流式对话"""
        original_system = None
        if len(self.memory) > 0 and isinstance(self.memory[0], SystemMessage):
            original_system = self.memory[0]
            self.memory.remove(original_system)
        try:
            self.memory.insert(0, SystemMessage(self.thinker_chat_system_message))
            self.memory.append(HumanMessage(message))
            content = ''
            if response_format is not None:
                for chunk in self.llm.stream(self.memory, response_format=response_format):
                    content += chunk.content
                    yield chunk.content
            else:
                for chunk in self.llm.stream(self.memory):
                    content += chunk.content
                    yield chunk.content
            self.memory.append(AIMessage(content))
        finally:
            self.memory.remove(self.memory[0])
            if original_system:
                self.memory.insert(0, original_system)
            if len(self.memory) > 0 and isinstance(self.memory[-1], HumanMessage):
                self.memory.pop()
        yield Result(True, "", "", None, content)

    @reduce_memory_decorator_compress
    def chat_sync(self, message: str, response_format: Optional[Dict] = None) -> Result:
        """与 LLM 进行同步对话"""
        original_system = None
        if len(self.memory) > 0 and isinstance(self.memory[0], SystemMessage):
            original_system = self.memory[0]
            self.memory.remove(original_system)
            
        self.memory.insert(0, SystemMessage(self.thinker_chat_system_message))
        self.memory.append(HumanMessage(message))
        
        if response_format is not None:
            response = self.llm.invoke(self.memory, response_format=response_format).content
        else:
            response = self.llm.invoke(self.memory).content
        
        self.memory.append(AIMessage(response))
        self.memory.remove(self.memory[0])
        
        if original_system:
            self.memory.insert(0, original_system)
        
        return Result(True, "", "", None, response)

    @reduce_memory_decorator_compress
    def execute_sync(self, instruction: str = None) -> Result:
        '''编程，直接根据instruction生成代码并执行'''
        current_instruction = instruction
        
        for i in range(self.max_retries):
            # 生成代码
            self.memory.append(HumanMessage(current_instruction))
            content = self.llm.invoke(self.memory).content
            self.memory.append(AIMessage(content))
            
            # 提取代码
            try:
                extracted = extract_code(content)
                if not extracted:
                    current_instruction = "无法从响应中提取代码，请重试。"
                    continue
                
                self.current_code = ''
                for language, code in extracted:
                    if language == 'python':
                        self.current_code += '\n' + code
                
            except Exception as e:
                error_msg = f"代码提取失败：{str(e)}"
                current_instruction = error_msg
                continue
            
            # 执行代码
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
            
        return Result(False, self.current_code, "超过最大尝试次数，编程失败。")

    @reduce_memory_decorator_compress
    def execute_stream(self, instruction: str = None) -> Iterator[object]:
        '''编程，返回迭代器'''
        current_instruction = instruction
        
        for i in range(self.max_retries):
            # 生成代码
            self.memory.append(HumanMessage(current_instruction))
            content = ''
            for chunk in self.llm.stream(self.memory):
                content += chunk.content
                yield chunk.content
            self.memory.append(AIMessage(content))

            # 提取代码
            try:
                extracted = extract_code(content)
                if not extracted:
                    current_instruction = "无法从响应中提取代码，请重试。"
                    yield Result(False, '', '', '', "无法从响应中提取代码，请重试。")
                    continue

                self.current_code = extracted[0][1]
            except Exception as e:
                error_msg = f"代码提取失败：{str(e)}"
                current_instruction = error_msg
                yield Result(False, '', '', '', error_msg)
                continue
            
            try:
                # 执行代码
                result = self.device.execute_code(self.current_code)
                
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
            except Exception as e:
                error_msg = "执行异常: " + str(e)
                yield error_msg
                current_instruction = error_msg
                continue
        
        yield Result(False, self.current_code, None, None, "超过最大尝试次数，编程失败。")

    def generateResult_sync(self, instruction: str, result: Result) -> str:
        '''生成最终结果'''
        logger.info('开始生成指令最终结果')
        logger.info(f'result.success: {result.success}')
        logger.info(f'result.code: {result.code}')
        logger.info(f'result.stdout: {result.stdout}')
        logger.info(f'result.stderr: {result.stderr}')
        logger.info(f'result.return_value: {result.return_value}')
        
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

    def generateResult_stream(self, instruction: str, result: Result) -> Iterator[str]:
        logger.info('开始生成指令最终结果')
        logger.info(f'result.success: {result.success}')
        logger.info(f'result.code: {result.code}')
        logger.info(f'result.stdout: {result.stdout}')
        logger.info(f'result.stderr: {result.stderr}')
        logger.info(f'result.return_value: {result.return_value}')
        
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

class Evaluator:
    '''行为评估器'''
    def __init__(self, llm: BaseChatModel, systemMessage: str, thinker: Thinker = None):
        self.llm = llm
        self.knowledges = []
        self.thinker = thinker
        self.system_message = systemMessage
        if self.system_message is None:
            self.system_message = default_evaluate_message

    def loadKnowledge(self, knowledge: str):
        self.knowledges.append(knowledge)
        
    def evaluate(self, instruction: str, result: Result) -> Tuple[bool, str]:
        '''评估任务是否完成，返回值：是否完成，原因'''
        import re
        import json
        
        code = result.code or ""
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        
        # 检查是否有明显错误
        if stderr and ("Error" in stderr or "Exception" in stderr):
            return False, f"代码执行出错: {stderr}"
        
        # 使用系统消息模板格式化提示
        try:
            prompt = PromptTemplate.from_template(self.system_message).format(
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
        counter = 0
        while counter < 3:
            try:
                logging.debug(f"尝试LLM评估 (第{counter+1}次)")
                x = self.llm.invoke(prompt)
                content = x.content
                logging.debug(f"LLM评估响应长度: {len(content)} 字符")
                logging.debug(f"LLM评估响应前200字符:\n{content[:200]}...")
                
                # 尝试从内容中提取代码块
                extracted = extract_code(content)
                if not extracted or len(extracted) == 0:
                    logging.debug("未从响应中提取到代码块，尝试直接解析JSON")
                    try:
                        json_pattern = r'(\{.*"taskIsComplete"\s*:\s*(true|false).*\})'
                        match = re.search(json_pattern, content, re.DOTALL)
                        
                        if match:
                            json_str = match.group(1)
                            logging.debug(f"找到JSON字符串: {json_str}")
                            j = json.loads(json_str)
                        else:
                            braces_pattern = r'(\{.*\})'
                            match = re.search(braces_pattern, content, re.DOTALL)
                            if match:
                                json_str = match.group(1)
                                logging.debug(f"找到可能的JSON字符串: {json_str}")
                                try:
                                    j = json.loads(json_str)
                                except:
                                    logging.debug("发现花括号内容，但非有效JSON")
                                    is_complete = "true" in content.lower() and "false" not in content.lower()
                                    reason = "无法解析评估结果，基于文本判断"
                                    return is_complete, reason
                            else:
                                logging.debug("未找到JSON格式内容，尝试基于文本判断")
                                is_complete = "true" in content.lower() and "false" not in content.lower()
                                reason = "无法解析评估结果，基于文本判断"
                                return is_complete, reason
                    except Exception as e:
                        logging.error(f"JSON解析失败(直接): {str(e)}")
                        counter += 1
                        continue
                else:
                    logging.debug(f"从响应中提取到代码块，语言: {extracted[0][0]}")
                    try:
                        j = json.loads(extracted[0][1])
                    except:
                        logging.debug("代码块不是有效的JSON，尝试清理后重新解析")
                        try:
                            cleaned_json = extracted[0][1].strip().replace("```", "").strip()
                            logging.debug(f"清理后的JSON字符串: {cleaned_json[:100]}...")
                            j = json.loads(cleaned_json)
                        except Exception as e:
                            logging.error(f"JSON解析失败(清理后): {str(e)}")
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
        
        # 如果LLM评估失败，使用兜底规则
        logging.info("LLM评估尝试均失败，使用兜底规则")
        
        if "任务完成" in stdout and not stderr:
            logging.info("兜底判断: 检测到任务完成标记且无错误")
            return True, "任务执行成功并输出了完成标记（兜底判断）"
        elif "assert" in code and "任务完成" in stdout:
            logging.info("兜底判断: 检测到断言验证且任务完成")
            return True, "代码包含断言验证并成功执行（兜底判断）"
        elif result.success and stdout and not stderr:
            logging.info("兜底判断: 代码执行成功")
            return True, "代码执行成功，无法进行详细评估"
        else:
            logging.info("兜底判断: 评估失败")
            return False, "评估过程出错，无法判断任务是否完成"

class Agent(AgentBase):
    '''
    智能体
    run方法：输入自然语言，翻译成Python代码，执行代码，评估代码执行结果，生成最终结果
    chat方法：输入自然语言，输出自然语言，无副作用
    '''
    def __init__(self, llm: BaseChatModel, stateful: bool = True, evaluate_llm: BaseChatModel = None, 
                 max_retries: int = 10, skip_evaluation: bool = False, skip_generation: bool = False,
                 thinker_system_message: str = None, evaluation_system_messages: List[str] = None,
                 thinker_chat_system_message: str = None):
        self.llm = llm
        self.name = ''
        self.api_specification = None
        if not evaluate_llm:
            self.evaluate_llm = self.llm
        else:
            self.evaluate_llm = evaluate_llm
        self.max_retries = max_retries
        self.skip_evaluation = skip_evaluation
        self.skip_generation = skip_generation
        self.device = Device() if not stateful else StatefulExecutor()
        self.thinker = Thinker(llm=self.llm, 
                              max_retries=max_retries,
                              thinker_system_message=thinker_system_message,
                              thinker_chat_system_message=thinker_chat_system_message,
                              device=self.device)
        
        # 初始化多个评估器
        self.evaluators = []
        if evaluation_system_messages:
            for system_message in evaluation_system_messages:
                evaluator = Evaluator(llm=self.evaluate_llm, systemMessage=system_message, thinker=self.thinker)
                self.evaluators.append(evaluator)
        else:
            self.evaluators.append(Evaluator(llm=self.evaluate_llm, systemMessage=default_evaluate_message, thinker=self.thinker))

    def chat_stream(self, message: str, response_format: Optional[Dict] = None) -> Iterator[object]:
        '''与LLM进行流式对话'''
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
    
    def chat_sync(self, message: str, response_format: Optional[Dict] = None) -> Result:
        '''与LLM进行同步对话'''
        return self.thinker.chat_sync(message, response_format)
    
    def loadEvaluationSystemMessage(self, evaluationSystemMessage: str):
        '''添加新的评估系统消息'''
        new_evaluator = Evaluator(llm=self.evaluate_llm, systemMessage=evaluationSystemMessage, thinker=self.thinker)
        self.evaluators.append(new_evaluator)
        logging.info(f"已添加新的评估系统消息，当前评估器数量: {len(self.evaluators)}")
        return len(self.evaluators)

    def loadKnowledge(self, knowledge: str):
        '''加载知识'''
        self.thinker.loadKnowledge(knowledge)
        for evaluator in self.evaluators:
            evaluator.loadKnowledge(knowledge)

    def loadPythonModules(self, pythonModules: List[str]):
        '''
        加载python模块
        '''
        knowledge = ""
        for module_name in pythonModules:
            module = import_module(module_name)
            knowledge += f'以下python模块已经导入：{module_name}\n'
            knowledge += f'模块源码如下：\n{inspect.getsource(module)}\n\n'
        self.loadKnowledge(knowledge)
        for module_name in pythonModules:
            if isinstance(self.device, StatefulExecutor):
                self.device.execute_code(f'import importlib\nimport {module_name}\nimportlib.reload({module_name})')

    def evaluate_all(self, result: Result, instruction: str = None) -> Tuple[bool, List[str]]:
        '''使用所有评估器进行评估'''
        logging.info('=== 开始评估 ===')
        
        if instruction is None:
            instruction = "执行任务"
        
        stdout = result.stdout or ""
        last_5000_chars = stdout[-5000:] if len(stdout) > 5000 else stdout
        logging.debug(f'执行结果最后5000个字符:\n{last_5000_chars}')
        
        result_for_eval = Result(
            result.success,
            result.code,
            last_5000_chars,
            result.stderr,
            result.return_value
        )

        reasons = []
        failures = []
        
        if self.evaluators:
            logging.info(f"使用 {len(self.evaluators)} 个评估器进行评估...")
            for i, evaluator in enumerate(self.evaluators):
                try:
                    logging.info(f"执行评估器 #{i+1}:")
                    is_complete, reason = evaluator.evaluate(instruction, result_for_eval)
                    
                    if is_complete:
                        logging.info(f"评估器 #{i+1} 评估结果: 成功")
                        reasons.append(reason)
                    else:
                        logging.info(f"评估器 #{i+1} 评估结果: 失败 - {reason}")
                        failures.append(reason)
                        self._log_evaluation_summary("失败", f"评估器 #{i+1} 失败: {reason}")
                        return False, failures + reasons
                    
                except Exception as e:
                    error_msg = f"评估器 #{i+1} 异常: {str(e)}"
                    logging.error(error_msg)
                    reasons.append(error_msg)
        
        if reasons:
            success_reasons = "\n".join([f"#{i+1}: {reason}" for i, reason in enumerate(reasons)])
            self._log_evaluation_summary("成功", f"所有评估器都通过\n{success_reasons}")
            return True, reasons
        
        logging.info("没有评估器返回结果，使用兜底逻辑...")
        return self._apply_fallback_logic(result, last_5000_chars)
    
    def _log_evaluation_summary(self, status: str, details: str):
        """统一的评估总结日志输出"""
        logging.info("=== 评估总结 ===")
        logging.info(f"整体评估结果: {status}")
        logging.info(f"详细信息: {details}")
    
    def _apply_fallback_logic(self, result: Result, last_5000_chars: str) -> Tuple[bool, List[str]]:
        """应用兜底逻辑进行评估"""
        if "任务完成" in last_5000_chars and not result.stderr:
            logging.info('兜底判断: 检测到任务完成标记')
            return True, ["任务执行成功并输出了完成标记（兜底判断）"]
        
        if "assert" in result.code and "任务完成" in last_5000_chars:
            logging.info('兜底判断: 检测到断言验证并成功执行')
            return True, ["代码包含断言验证并成功执行（兜底判断）"]
        
        if result.success:
            self._log_evaluation_summary("成功(兜底)", "代码执行成功，无明确评估结果")
            return True, ["代码执行成功，无明确评估结果"]
        else:
            self._log_evaluation_summary("失败(兜底)", "代码执行失败，无明确评估结果")
            return False, ["代码执行失败，无明确评估结果"]

    def execute_sync(self, instruction: str) -> Result:
        """同步执行自然语言指令"""
        current_instruction = instruction
        
        # 跳过评估循环
        if self.skip_evaluation:
            if self.skip_generation:
                return self.thinker.execute_sync(current_instruction)
            else:
                result = self.thinker.execute_sync(current_instruction)
                if isinstance(result, Result):
                    finalResult = self.generateResult_sync(instruction, result)
                    return Result(result.success, result.code, result.stdout, result.stderr, finalResult)
            return
        
        # 评估循环
        for i in range(self.max_retries):
            result = self.thinker.execute_sync(current_instruction)
            
            if result.success:
                taskIsComplete, reasons = self.evaluate_all(result, instruction)
                
                if taskIsComplete:
                    if not self.skip_generation:
                        finalResult = self.generateResult_sync(instruction, result)
                        return Result(True, result.code, result.stdout, result.stderr, finalResult)
                    else:
                        return Result(True, result.code, result.stdout, result.stderr, result.return_value)
                else:
                    failure_reason = reasons[0] if reasons else "未提供具体原因"
                    current_instruction = f"评估失败，请修改代码。原因：{failure_reason}\n当前代码输出：{result.stdout}\n当前代码错误：{result.stderr}\n当前代码返回值：{result.return_value}"
                    
            else:
                if not self.skip_generation:
                    finalResult = self.generateResult_sync(instruction, result)
                    return Result(False, result.code, result.stdout, result.stderr, finalResult)
                else:
                    return Result(False, result.code, result.stdout, result.stderr, result.return_value)
        
        print('超过最大尝试次数，编程失败。')
        return Result(False, '', '', '', '超过最大尝试次数，编程失败。')

    def execute_stream(self, instruction: str) -> Iterator[object]:
        '''执行自然语言指令，返回迭代器'''
        current_instruction = instruction
        
        # 跳过评估循环
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
                for r in self.thinker.execute_stream(current_instruction):
                    yield r
                    if isinstance(r, Result):
                        result = r
                if isinstance(result, Result):
                    finalResult = ''
                    for chunk in self.generateResult_stream(instruction, result):
                        finalResult += chunk
                        yield chunk
                    yield Result(result.success, result.code, result.stdout, result.stderr, finalResult)
                else:
                    yield Result(False, '', '', '', '未能获取到有效的执行结果')
            return
        
        # 评估循环
        for i in range(self.max_retries):
            result = None
            for r in self.thinker.execute_stream(current_instruction):
                yield r
                if isinstance(r, Result):
                    result = r
            
            if not isinstance(result, Result):
                yield Result(False, '', '', '', '未能获取到有效的执行结果')
                continue
            
            try:
                if result.success:
                    taskIsComplete, reasons = self.evaluate_all(result, instruction)
                    if taskIsComplete:
                        if not self.skip_generation:
                            finalResult = ''
                            for chunk in self.generateResult_stream(instruction, result):
                                finalResult += chunk
                                yield chunk
                            yield Result(True, result.code, result.stdout, result.stderr, finalResult)
                        else:
                            yield Result(True, result.code, result.stdout, result.stderr, result.return_value)
                        return
                    else:
                        stdout = result.stdout or ""
                        stderr = result.stderr or ""
                        return_value = result.return_value or ""
                        
                        failure_reason = reasons[0] if reasons else "未提供具体原因"
                        current_instruction = f"评估失败，请修改代码。原因：{failure_reason}\n当前代码输出：{stdout}\n当前代码错误：{stderr}\n当前代码返回值：{return_value}"
                else:
                    if not self.skip_generation:
                        finalResult = ''
                        for chunk in self.generateResult_stream(instruction, result):
                            finalResult += chunk
                            yield chunk
                        yield Result(False, result.code, result.stdout, result.stderr, finalResult)
                    else:
                        yield Result(False, result.code, result.stdout, result.stderr, result.return_value)
                    return
            except Exception as e:
                error_msg = f"评估或结果处理过程中出现错误: {str(e)}"
                logging.error(error_msg)
                yield error_msg
                
                if not self.skip_generation:
                    try:
                        finalResult = ''
                        for chunk in self.generateResult_stream(instruction, result):
                            finalResult += chunk
                            yield chunk
                        yield Result(result.success, result.code, result.stdout, result.stderr, finalResult)
                    except Exception as gen_error:
                        yield f"生成最终响应时出错: {str(gen_error)}"
                        yield Result(result.success, result.code, result.stdout, result.stderr, str(gen_error))
                else:
                    yield Result(result.success, result.code, result.stdout, result.stderr, result.return_value)
                return
            
        logging.info('超过最大尝试次数，编程失败。')
        yield Result(False, '', '', '', '超过最大尝试次数，编程失败。')
        yield '以下是重现错误的代码'
        prompt = '''把上一步的出现错误的代码输出出来，以供调试'''
        yield from self.chat_stream(prompt)
    
    def generateResult_sync(self, instruction: str, result: Result) -> str:
        '''生成最终结果'''
        return self.thinker.generateResult_sync(instruction, result)
    
    def generateResult_stream(self, instruction: str, result: Result) -> Iterator[str]:
        '''生成最终结果流式'''
        return self.thinker.generateResult_stream(instruction, result)

    def resetEvaluators(self, evaluationSystemMessage: str = None):
        '''重置所有评估器'''
        self.evaluators = []
        logging.info("已清除所有评估器")
        
        if evaluationSystemMessage is not None:
            self.evaluators.append(Evaluator(llm=self.llm, systemMessage=evaluationSystemMessage, thinker=self.thinker))
            logging.info(f"已创建新评估器，当前评估器数量: {len(self.evaluators)}")
        else:
            self.evaluators.append(Evaluator(llm=self.llm, systemMessage=default_evaluate_message, thinker=self.thinker))
            logging.info(f"已创建默认评估器，当前评估器数量: {len(self.evaluators)}")

    def set_api_specification(self, api_spec: str):
        '''设置智能体的 API 规范说明'''
        self.api_specification = api_spec
        logging.info(f"已设置 API 规范: {api_spec}")
        
    def set_agent_name(self, name: str):
        '''设置智能体的名称'''
        self.name = name
        logging.info(f"已设置智能体名称: {name}")

print("💡 Python核心模块已加载。这是轻量级版本，不包含语言模型定义。")