# %%
from agent_base import Result, reduce_memory_decorator_compress
from pythonTask import StatefulExecutor, Agent
from langchain_core.language_models import BaseChatModel
from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime as dt
from prompts import team_manager_system_message_share_state, team_manager_system_message_no_share_state
import logging
import sys

# 配置日志输出到控制台 - 只在没有配置过时才配置
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

logger = logging.getLogger(__name__)
# 只设置当前模块的日志级别，不影响全局配置
logger.setLevel(logging.DEBUG)

class RegisteredAgent:
    """存储已注册的 Agent 信息"""
    def __init__(self, name: str, instance: Agent, description: str):
        self.name = name
        self.instance = instance
        self.description = description

class WorkflowState:
    """工作流状态管理"""
    def __init__(self):
        self.current_step_index = 0
        self.loop_counters = {}      # {"loop_to_step3": 2}
        self.fix_counter = 0         # 修复任务计数
        self.loop_targets = []       # 循环目标历史
        self.max_loops = 5           # 最大循环次数限制
        self.context_variables = {}  # 上下文变量
        self.branch_history = []     # 分支历史

    def should_break_loop(self, target_step_id):
        """检查是否应该退出循环（防止无限循环）"""
        loop_key = f"loop_to_{target_step_id}"
        return self.loop_counters.get(loop_key, 0) >= self.max_loops
    
    def increment_loop_counter(self, target_step_id):
        """增加循环计数器"""
        loop_key = f"loop_to_{target_step_id}"
        self.loop_counters[loop_key] = self.loop_counters.get(loop_key, 0) + 1
    
    def reset_step_status_from(self, start_index, plan):
        """重置从指定索引开始的步骤状态"""
        for i in range(start_index, len(plan)):
            if plan[i].get('status') in ['completed', 'failed']:
                plan[i]['status'] = 'pending'

class MultiStepAgent_v2(Agent):
    """
    新版多步骤智能体：不依赖 workflow engine、state manager、agent registry。
    只实现 execute_multi_step，计划和状态存储在 StatefulExecutor 的变量中，成员 Agent 通过变量注册。
    """

    def __init__(
        self,
        llm: BaseChatModel,
        registered_agents: Optional[List[RegisteredAgent]] = None,
        max_retries: int = 3,
        thinker_system_message: Optional[str] = None,
        thinker_chat_system_message: Optional[str] = None,
        planning_prompt_template: Optional[str] = None,  # 新增参数
        use_autonomous_planning: bool = True,  # 新增：是否使用自主规划模式
    ):
        team_system_message=thinker_system_message
        if team_system_message is None:
            team_system_message=team_manager_system_message_no_share_state
        
        super().__init__(
            llm=llm,
            stateful=True,
            thinker_system_message=team_system_message,
            thinker_chat_system_message=thinker_chat_system_message,
            max_retries=max_retries,
        )
        self.device = StatefulExecutor()
        self.registered_agents = registered_agents if registered_agents is not None else []
        self.max_retries = max_retries
        self.thinker_chat_system_message = thinker_chat_system_message
        # 注册成员 Agent 到 StatefulExecutor 的变量空间
        for spec in self.registered_agents:
            self.device.set_variable(spec.name, spec.instance)
        # 初始化 current_plan
        self.device.set_variable("current_plan", [])
        # 初始化工作流状态 (方案2)
        self.workflow_state = WorkflowState()
        self.original_goal = ""
        self.use_autonomous_planning = use_autonomous_planning
        
        # 设置默认的计划生成提示词模板
        if planning_prompt_template:
            # 用户提供了自定义模板，使用翻译模式
            self.planning_prompt_template = planning_prompt_template
            self.use_autonomous_planning = False
        elif use_autonomous_planning:
            # 使用自主规划模式的默认模板
            self.planning_prompt_template = """
# 任务背景
你是一个多智能体团队的协调者，负责将复杂任务分解为可执行的步骤，并为每个步骤分配合适的执行者。

# 可用智能体列表
{available_agents_str}

# 主任务
{main_instruction}

# 三阶段执行计划框架
请将任务分解为三个关键阶段：

1. 信息收集阶段: 明确为达成目标需要收集哪些信息，每条信息为什么必要
2. 执行阶段: 具体的实现步骤，每一步如何利用收集的信息
3. 验证与修复阶段: 如何验证结果，以及在失败时需要收集什么额外信息来修复问题

# 输出要求
请将主任务分解为有序的步骤，每个步骤必须指定以下信息:
1. id: 步骤唯一标识符(建议使用"info1", "exec2", "verify3"等形式，以表明所属阶段)
2. name: 简短的步骤名称
3. instruction: 详细的执行指令，需要清晰明确
4. agent_name: 执行该步骤的智能体名称，必须从以下列表中选择: {available_agent_names}
5. instruction_type: 指令类型(execution/information) - 见下方说明
6. phase: 步骤所属阶段(information/execution/verification)
7. expected_output: 预期输出，明确该步骤应该产生什么结果
8. prerequisites: 执行此步骤需要满足的先决条件(自然语言描述)，如无要求则为"无"

# 智能体构成说明
每个智能体由两部分组成：
1. 记忆：存储对话历史、知识和状态信息
2. 有状态的jupyter notebook kernel：用于执行代码和与外部环境交互

# 指令类型说明
- execution: 执行性任务，会调用jupyter notebook执行代码对外部世界产生行为或观察，同时改变智能体的记忆（如执行代码、文件操作、数据写入、观察外部环境等）
- information: 信息性任务，只是对智能体记忆的查询或修改，不会调用jupyter notebook（如查询历史对话、告知状态等）

# 规划规则
1. 分析任务特点，合理拆分步骤
2. 根据每个智能体的专长分配任务
3. 用自然语言描述每个步骤的先决条件，而非硬编码依赖关系
4. 为每个步骤提供足够详细的指令
5. 信息收集阶段应彻底，确保执行阶段有足够输入数据
6. 执行阶段应明确如何使用前面步骤收集的信息
7. 验证阶段应定义明确的成功标准，并预见可能的失败场景
"""
        else:
            # 使用翻译模式的默认模板 (方案2: 动态决策控制)
            self.planning_prompt_template = """
# 任务背景
你是一个工作流翻译器，负责将用户用自然语言描述的步骤翻译成简单的线性执行计划。复杂的控制流逻辑（如循环、条件分支）将由决策者在执行过程中动态处理。

# 重要原则
- **严格按照用户定义的步骤进行翻译，不要添加、删除或修改步骤数量和核心内容**
- **保持用户原始步骤的顺序和主要意图不变**
- **将复杂的控制流（如while循环、if条件）简化为基本的线性步骤**
- **对于缺失的字段信息，可以基于上下文进行合理推测和补充**

# 可用智能体列表
{available_agents_str}

# 用户原始步骤描述
{main_instruction}

# 翻译要求
请将用户描述的工作流翻译成简单的线性步骤序列，每个步骤包含:
1. id: 步骤唯一标识符(建议使用"step1", "step2"等形式，按用户步骤顺序)
2. name: 基于用户步骤内容的简短名称
3. instruction: 用户原始步骤的详细描述，保持原意不变
4. agent_name: 最适合执行该步骤的智能体名称，必须从以下列表中选择: {available_agent_names}
5. instruction_type: 指令类型(execution/information) - 见下方说明
6. phase: 步骤类型(information/execution/verification)
7. expected_output: 基于步骤内容推断的预期输出
8. prerequisites: 执行此步骤需要满足的先决条件(自然语言描述)，如无要求则为"无"

# 智能体构成说明
每个智能体由两部分组成：
1. 记忆：存储对话历史、知识和状态信息
2. 有状态的jupyter notebook kernel：用于执行代码和与外部环境交互

# 指令类型说明
- execution: 执行性任务，会调用jupyter notebook执行代码对外部世界产生行为或观察，同时改变智能体的记忆（如执行代码、文件操作、数据写入、观察外部环境等）
- information: 信息性任务，只是对智能体记忆的查询或修改，不会调用jupyter notebook（如查询历史对话、告知状态等）

# 控制流处理原则
- **while循环**: 将循环体内的步骤提取为普通步骤，循环控制由决策者处理
- **if条件**: 将条件判断和分支操作提取为普通步骤，条件判断由决策者处理
- **复杂逻辑**: 分解为基本的执行步骤和决策步骤

# 翻译规则
1. **严格遵循用户步骤的数量和顺序**
2. **不要合并、拆分或重新组织用户的步骤**
3. **保持每个步骤的核心意图和主要内容**
4. 根据步骤内容选择最合适的智能体
5. 根据步骤性质判断instruction_type和phase
6. 用自然语言描述每个步骤的先决条件，而非硬编码依赖关系
7. **对于缺失字段的推测原则**：
   - agent_name: 根据步骤内容推测最适合的智能体
   - instruction_type: 根据步骤性质推测(需要调用jupyter notebook执行代码、文件操作、数据写入等选execution，仅需查询或修改智能体记忆选information)
   - phase: 根据步骤在整体流程中的作用推测(收集信息选information，具体实施选execution，检查验证选verification)
   - expected_output: 根据步骤描述推测可能的输出结果
   - prerequisites: 根据步骤间的逻辑关系描述先决条件
8. **对于instruction字段的处理**：保持用户原始描述，必要时可适当补充执行细节以确保可操作性

# 示例翻译

## 用户输入：
```
1. 调用coder实现计算器
2. 调用coder保存代码  
while true {{
    3. 调用tester运行测试
    4. 如果运行正确: 终止工作流
    5. 如果报错: 发给coder修复
}}
```

## 翻译输出：
```json
{{
  "steps": [
    {{
      "id": "step1",
      "name": "实现计算器",
      "instruction": "调用coder实现一个简单的计算器类，要包含单元测试",
      "agent_name": "coder",
      "instruction_type": "execution",
      "phase": "execution",
      "expected_output": "计算器类代码",
      "prerequisites": "无"
    }},
    {{
      "id": "step2", 
      "name": "保存代码",
      "instruction": "调用coder把代码保存到文件",
      "agent_name": "coder",
      "instruction_type": "execution",
      "phase": "execution",
      "expected_output": "代码文件",
      "prerequisites": "计算器代码已实现"
    }},
    {{
      "id": "step3",
      "name": "运行测试",
      "instruction": "调用tester运行测试，检查代码是否正确",
      "agent_name": "tester",
      "instruction_type": "execution", 
      "phase": "verification",
      "expected_output": "测试结果",
      "prerequisites": "代码文件已保存"
    }},
    {{
      "id": "step4",
      "name": "分析测试结果并决策",
      "instruction": "分析测试结果，如果测试通过则完成工作流，如果测试失败则生成修复任务并循环回到测试步骤",
      "agent_name": "tester",
      "instruction_type": "information",
      "phase": "verification", 
      "expected_output": "决策结果",
      "prerequisites": "测试已完成并有结果"
    }}
  ]
}}
```
"""

    def register_agent(self, name: str, instance: Agent):
        """注册一个新的 Agent。"""
        # 获取Agent的描述，如果没有api_specification属性则使用默认描述
        description = getattr(instance, 'api_specification', f"{name}智能体，通用任务执行者")
        spec = RegisteredAgent(name=name, instance=instance, description=description)
        self.registered_agents.append(spec)
        self.device.set_variable(spec.name, spec.instance)
        logger.debug(f"已注册 Agent: {name}")
    


    def plan_execution(self, main_instruction: str) -> List[Dict[str, Any]]:
        """
        根据主指令规划执行步骤，支持自定义提示词模板。
        """
        
        # 构建可用 Agent 的描述字符串
        available_agents_str = "\n".join(
            [f"- {spec.name}: {spec.description}" for spec in self.registered_agents]
        )
        if not available_agents_str:
            available_agents_str = "无可用 Agent。请确保已注册 Agent。"
            
        # 获取可用 Agent 名称列表
        available_agent_names = [spec.name for spec in self.registered_agents] or ["无"]
        
        # 检查是否有上一次失败的验证结果
        previous_attempt_failed = False
        previous_verification = None
        previous_plan = None
        
        if hasattr(self, 'device'):
            try:
                previous_attempt_failed_var = self.device.get_variable("previous_attempt_failed")
                previous_attempt_failed = previous_attempt_failed_var if previous_attempt_failed_var is not None else False
            except:
                previous_attempt_failed = False
                
            try:
                previous_verification = self.device.get_variable("previous_verification")
            except:
                previous_verification = None
                
            try:
                previous_plan = self.device.get_variable("previous_plan")
            except:
                previous_plan = None

        # 使用模板生成提示词
        planning_prompt = self.planning_prompt_template.format(
            available_agents_str=available_agents_str,
            main_instruction=main_instruction,
            available_agent_names=', '.join(available_agent_names)
        )

        # 如果有上一次失败的验证结果和执行计划，添加到提示中
        if previous_attempt_failed and previous_verification:
            if previous_plan:
                planning_prompt += f"""

# 上一次执行的计划
```json
{json.dumps(previous_plan, indent=2, ensure_ascii=False)}
```

⚠️ 注意：上一次执行计划未能达成目标，请仔细分析以下验证结果，并改进您的计划：

# 上一次验证失败的原因
{previous_verification}

# 改进建议
- 特别关注上一次失败的原因，确保新计划能解决这些问题
- 考虑添加更多的步骤或更健壮的验证方法
- 为已知的失败点设计专门的修复策略
"""

        # 添加输出格式要求
        first_agent_name = available_agent_names[0] if available_agent_names and available_agent_names[0] != "无" else "智能体名称"
        planning_prompt += f"""

# 输出格式
必须严格按照以下JSON格式输出:
```json
{{
  "steps": [
    {{
      "id": "step1",
      "name": "步骤名称",
      "instruction": "详细的执行指令...",
      "agent_name": "{first_agent_name}",
      "instruction_type": "execution",
      "expected_output": "预期输出",
      "dependencies": []
    }}
  ]
}}
```

# 重要提示
- 每个步骤都要指定指令类型(instruction_type)
- 确保步骤之间的数据流动清晰，后续步骤能够获取和使用前面步骤的输出结果
- 每个步骤都应有明确的目标和可验证的输出
- 步骤中的instruction不要使用三个双引号包裹
"""

        # 尝试使用更兼容的response_format（移除schema字段）
        response_format = {
            "type": "json_object"
        }

        try:
            # 使用chat_sync并添加response_format参数
            result = self.chat_sync(planning_prompt, response_format=response_format)
            # 从Result对象中提取内容
            if result.success:
                plan_result = result.return_value if result.return_value else result.stdout
            else:
                logger.warning(f"chat_sync返回失败: {result.stderr}")
                # 回退到无格式约束方式
                result = self.chat_sync(planning_prompt)
                plan_result = result.return_value if result.return_value else result.stdout

            from autogen.code_utils import extract_code
            
            # 判断是否接收到错误消息
            if isinstance(plan_result, str) and "error" in plan_result:
                error_obj = json.loads(plan_result)
                logger.warning(f"LLM响应包含错误: {error_obj.get('error')}")
                # 回退到再次尝试
                result = self.chat_sync(planning_prompt)
                plan_result = result.return_value if result.return_value else result.stdout
            
            # 尝试提取和解析JSON
            try:
                extracted_codes = extract_code(plan_result)
                if extracted_codes:
                    plan_data = json.loads(extracted_codes[0][1])
                else:
                    # 直接尝试解析整个响应
                    plan_data = json.loads(plan_result)
            except:
                # 如果提取失败，尝试直接解析
                plan_data = json.loads(plan_result)
                
            # 处理两种可能的格式：直接步骤数组或包含steps字段的对象
            if isinstance(plan_data, list):
                plan = plan_data  # 直接是步骤数组
                logger.debug(f"解析到步骤数组，共 {len(plan)} 个步骤")
            else:
                plan = plan_data.get("steps", [])  # 从对象中获取steps
                logger.debug(f"从对象中解析到步骤，共 {len(plan)} 个步骤")
        except Exception as e:
            logger.warning(f"计划生成第一次尝试失败: {e}")
            # 回退到普通方式再试一次
            try:
                from langchain_core.messages import HumanMessage
                # 检查thinker.memory最后一条是否为HumanMessage，如果是则删除
                if hasattr(self, "thinker") and hasattr(self.thinker, "memory") and self.thinker.memory:
                    last_msg = self.thinker.memory[-1]
                    if isinstance(last_msg, HumanMessage):
                        self.thinker.memory.pop()
                
                result = self.chat_sync(planning_prompt)
                plan_result = result.return_value if result.return_value else result.stdout
                
                # 尝试多种解析方式
                try:
                    # 首先判断plan_result是否以```json开头
                    if plan_result.startswith("```json"):
                        plan_result = plan_result[len("```json"):].strip()
                        # 去除结尾的```
                        if plan_result.endswith("```"):
                            plan_result = plan_result[:-len("```")]
                            
                    # 首先尝试直接解析
                    plan_data = json.loads(plan_result)
                    if isinstance(plan_data, list):
                        plan = plan_data
                    else:
                        plan = plan_data.get("steps", [])
                except:
                    # 尝试提取JSON部分
                    import re
                    json_matches = re.findall(r'\[[\s\S]*?\]|\{[\s\S]*?\}', plan_result)
                    if json_matches:
                        for json_str in json_matches:
                            try:
                                plan_data = json.loads(json_str)
                                if isinstance(plan_data, list):
                                    plan = plan_data
                                    break
                                elif isinstance(plan_data, dict) and "steps" in plan_data:
                                    plan = plan_data["steps"]
                                    break
                            except:
                                continue
                    
                    if not locals().get('plan'):
                        # 如果还是失败，尝试查找 JSON 数组格式
                        array_match = re.search(r'\[\s*\{.*?\}\s*\]', plan_result, re.DOTALL)
                        if array_match:
                            try:
                                plan = json.loads(array_match.group(0))
                            except:
                                plan = []
            except Exception as e2:
                logger.error(f"解析计划失败: {e2}")
                plan = []
        
        # 确保 plan 是列表且有内容
        if not isinstance(plan, list) or not plan:
            logger.warning("计划生成失败，使用单步回退计划")
            plan = [{
                "id": "fallback_step",
                "name": "执行完整任务",
                "instruction": main_instruction,
                "agent_name": self.registered_agents[0].name if self.registered_agents else "general_agent",
                "phase": "execution",
                "instruction_type": "execution",
                "expected_output": "任务完成结果",
                "prerequisites": "无"
            }]
        
        # 确保所有步骤都有必要的字段
        for i, step in enumerate(plan):
            if not isinstance(step, dict):
                logger.warning(f"步骤 {i} 不是字典格式，将被替换为默认步骤")
                plan[i] = {
                    "id": f"auto_{i}",
                    "name": f"自动步骤{i}",
                    "instruction": f"执行任务的第{i+1}部分",  # 避免直接使用原始指令
                    "agent_name": self.registered_agents[0].name if self.registered_agents else "general_agent",
                    "phase": "execution",
                    "instruction_type": "execution",
                    "expected_output": f"第{i+1}部分的执行结果",
                    "prerequisites": "无",
                    "status": "pending"
                }
                continue
                
            # 确保必要字段存在
            if "id" not in step:
                step["id"] = f"step_{i+1}"
            if "name" not in step:
                step["name"] = f"步骤{i+1}"
            if "instruction" not in step:
                step["instruction"] = f"执行任务的第{i+1}部分"  # 避免直接使用原始指令
            if "agent_name" not in step:
                step["agent_name"] = self.registered_agents[0].name if self.registered_agents else "general_agent"
            if "phase" not in step:
                step["phase"] = "execution"
            if "instruction_type" not in step:
                step["instruction_type"] = "execution"
            # 设置默认状态
            if "status" not in step:
                step["status"] = "pending"
            if "expected_output" not in step:
                step["expected_output"] = f"第{i+1}步的执行结果"
            # 向后兼容：将旧的dependencies转换为新的prerequisites
            if "dependencies" in step and not step.get("prerequisites"):
                deps = step["dependencies"]
                if deps:
                    step["prerequisites"] = f"需要完成步骤: {', '.join(deps)}"
                else:
                    step["prerequisites"] = "无"
                del step["dependencies"]
            elif "prerequisites" not in step:
                step["prerequisites"] = "无"
        
        self.device.set_variable("current_plan", plan)
        logger.debug(f"生成计划: {plan}")
        # 添加直接打印到控制台
        print(f"\n当前执行计划:\n{json.dumps(plan, ensure_ascii=False, indent=2)}\n")
        return plan

    # ====== 智能调度相关方法 ======
    
    def can_execute_step(self, step: Dict) -> Tuple[bool, str]:
        """基于Agent记忆和系统状态判断步骤可执行性（新版：要求LLM返回JSON）"""
        step_id = step.get('id')
        step_name = step.get('name')
        prerequisites = step.get('prerequisites', '无')
        instruction = step.get('instruction', '')

        # 如果先决条件为"无"，直接可执行
        if prerequisites in ['无', '']:
            return True, "无先决条件限制"

        # 构造判断提示
        check_prompt = f"""
根据当前状态判断步骤是否可以执行：

步骤ID: {step_id}
步骤名称: {step_name}
先决条件: {prerequisites}
指令概要: {instruction[:100]}...

请检查：
1. 当前系统状态是否满足先决条件
2. 所需文件/数据是否已准备好  
3. 前置步骤是否已完成

请严格按照如下JSON格式返回：
{{
  "executable": true/false,  // 是否可执行
  "reason": "具体说明"
}}
"""
        response_format = {"type": "json_object"}
        try:
            response = self.chat_sync(check_prompt, response_format=response_format)
            response_text = response.return_value if response.return_value else response.stdout
            import json
            # 兼容：有时LLM会返回代码块
            if isinstance(response_text, str):
                response_text = response_text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[len("```json"):].strip()
                    if response_text.endswith("```"):
                        response_text = response_text[:-3].strip()
            result = json.loads(response_text)
            executable = bool(result.get("executable", False))
            reason = result.get("reason", "无理由")
            return executable, reason
        except Exception as e:
            import logging
            logging.warning(f"判断步骤可执行性时出错: {e}")
            return True, "无法判断，默认可执行"
    
    def select_next_executable_step(self, plan: List[Dict]) -> Optional[Tuple[int, Dict]]:
        """智能选择下一个可执行步骤"""
        
        # 获取所有待执行步骤
        pending_steps = []
        for i, step in enumerate(plan):
            step_status = step.get('status')
            
            if step_status not in ('completed', 'skipped', 'running'):
                pending_steps.append((i, step))
        
        if not pending_steps:
            return None
        
        # 如果只有一个待执行步骤，直接返回
        if len(pending_steps) == 1:
            return pending_steps[0]
        
        # 筛选出可执行的步骤
        executable_steps = []
        for i, step in pending_steps:
            can_exec, reason = self.can_execute_step(step)
            if can_exec:
                executable_steps.append((i, step, reason))
        
        # 如果没有可执行步骤，返回None
        if not executable_steps:
            return None
        
        # 如果只有一个可执行步骤，直接返回
        if len(executable_steps) == 1:
            return executable_steps[0][:2]
        
        # 多个可执行步骤时，使用Agent记忆进行智能选择
        step_descriptions = []
        for i, (idx, step, reason) in enumerate(executable_steps):
            step_descriptions.append(f"{i+1}. 步骤{step.get('id')}: {step.get('name')} - {reason}")
        
        selection_prompt = f"""
当前有多个可执行步骤，请根据执行逻辑和当前状态选择最合适的下一步：

可执行步骤：
{chr(10).join(step_descriptions)}

选择标准：
1. 执行的逻辑顺序和优先级
2. 当前系统状态和资源情况
3. 任务的整体进度和目标

请选择一个步骤编号 (1-{len(executable_steps)})
返回格式: 选择: 数字
"""
        
        try:
            response = self.chat_sync(selection_prompt)
            response_text = response.return_value if response.return_value else response.stdout
            
            # 提取选择的数字
            import re
            match = re.search(r'选择[:：]\s*(\d+)', response_text)
            if match:
                selected_num = int(match.group(1))
                if 1 <= selected_num <= len(executable_steps):
                    selected_idx = selected_num - 1
                    return executable_steps[selected_idx][:2]
            
            # 解析失败，返回第一个
            logger.warning(f"解析步骤选择失败，默认选择第一个: {response_text}")
            return executable_steps[0][:2]
            
        except Exception as e:
            logger.warning(f"智能选择步骤时出错: {e}")
            # 出错时返回第一个可执行步骤
            return executable_steps[0][:2]
    
    def _add_new_tasks(self, new_tasks: List[Dict]):
        """添加新任务到计划中"""
        if not new_tasks:
            return
            
        plan = self.get_plan()
        for new_task in new_tasks:
            # 确保新任务有必要的字段
            new_task_id = new_task.get('id', f"dynamic_{len(plan)}")
            new_task['id'] = new_task_id
            if 'status' not in new_task:
                new_task['status'] = 'pending'
            if 'prerequisites' not in new_task:
                new_task['prerequisites'] = '无'
            
            plan.append(new_task)
        
        # 更新计划
        self.device.set_variable("current_plan", plan)
        logger.debug(f"添加了 {len(new_tasks)} 个新任务")

    def get_plan(self) -> List[Dict[str, Any]]:
        """从 StatefulExecutor 获取当前计划。"""
        return self.device.get_variable("current_plan") or []

    def update_step_status(self, step_idx: int, status: str, result: Any = None):
        """更新 current_plan 中某一步骤的状态和结果。"""
        # 更新基本状态和结束时间
        code_base = f'''
current_plan[{step_idx}]["status"] = "{status}"
current_plan[{step_idx}]["end_time"] = "{dt.now().isoformat()}"
'''
        self.device.execute_code(code_base)

        if result is not None:
            # 创建结果字典 (使用 Python 布尔值)
            result_dict = {
                "success": bool(getattr(result, "success", False)), # 确保是 Python bool
                "stdout": getattr(result, "stdout", None),
                "stderr": getattr(result, "stderr", None),
                "return_value": getattr(result, "return_value", None),
            }
            # 将结果字典存入 Executor 临时变量
            temp_var_name = f"_temp_result_{step_idx}"
            self.device.set_variable(temp_var_name, result_dict)

            # 更新 plan 中的 result 字段，引用临时变量
            code_result_update = f'current_plan[{step_idx}]["result"] = {temp_var_name}'
            self.device.execute_code(code_result_update)

            # 可选：清理临时变量（如果担心命名空间污染）
            # self.device.execute_code(f'del {temp_var_name}')

    # ====== 方案2: 控制流处理方法 ======
    
    def find_step_index_by_id(self, step_id: str) -> int:
        """根据步骤ID查找索引"""
        plan = self.get_plan()
        for i, step in enumerate(plan):
            if step.get("id") == step_id:
                return i
        return -1
    
    def jump_to_step(self, target_step_id: str):
        """跳转到指定步骤"""
        target_index = self.find_step_index_by_id(target_step_id)
        if target_index >= 0:
            # 获取当前计划
            plan = self.get_plan()
            
            # 将当前步骤到目标步骤之间的所有步骤标记为已跳过(跳过依赖关系问题)
            current_index = self.workflow_state.current_step_index
            for i in range(current_index, target_index):
                if i < len(plan) and plan[i].get('status') not in ('completed', 'skipped'):
                    plan[i]['status'] = 'skipped'
                    logger.debug(f"跳过步骤 {i}: {plan[i].get('name', plan[i].get('id'))}")
            
            # 更新计划
            self.device.set_variable("current_plan", plan)
            
            # 设置当前步骤索引
            self.workflow_state.current_step_index = target_index
            logger.debug(f"跳转到步骤: {target_step_id} (索引: {target_index})")
        else:
            logger.warning(f"找不到步骤ID: {target_step_id}")
    
    def loop_back_to_step(self, target_step_id: str):
        """循环回到指定步骤"""
        # 检查是否应该退出循环
        if self.workflow_state.should_break_loop(target_step_id):
            logger.warning(f"达到最大循环次数，停止循环到步骤: {target_step_id}")
            return False
        
        target_index = self.find_step_index_by_id(target_step_id)
        if target_index >= 0:
            # 重置从目标步骤开始的所有步骤状态
            plan = self.get_plan()
            self.workflow_state.reset_step_status_from(target_index, plan)
            self.device.set_variable("current_plan", plan)
            
            # 跳转到目标步骤
            self.workflow_state.current_step_index = target_index
            
            # 增加循环计数器
            self.workflow_state.increment_loop_counter(target_step_id)
            
            logger.debug(f"循环回到步骤: {target_step_id} (第{self.workflow_state.loop_counters.get(f'loop_to_{target_step_id}', 0)}次)")
            return True
        else:
            logger.warning(f"找不到步骤ID: {target_step_id}")
            return False
    
    def handle_generate_fix_task_and_loop(self, decision: Dict[str, Any]) -> bool:
        """处理生成修复任务并循环的复合决策"""
        target_step_id = decision.get('loop_target')
        
        # 检查循环次数
        if self.workflow_state.should_break_loop(target_step_id):
            logger.warning(f"已尝试修复{self.workflow_state.max_loops}次，停止循环")
            return False
        
        # 1. 生成修复任务
        fix_task = {
            "id": f"fix_{self.workflow_state.fix_counter}",
            "name": "代码修复",
            "instruction": decision.get('fix_instruction', '修复代码中的问题'),
            "agent_name": decision.get('fix_agent', 'coder'),
            "instruction_type": "execution",
            "phase": "execution",
            "expected_output": "修复后的代码",
            "prerequisites": "检测到需要修复的问题",
            "status": "pending"
        }
        
        # 如果有错误详情，添加到指令中
        if decision.get('error_details'):
            fix_task['instruction'] += f"\n\n错误详情:\n{decision['error_details']}"
        
        # 2. 将修复任务插入到当前位置之后
        plan = self.get_plan()
        current_index = self.workflow_state.current_step_index
        plan.insert(current_index + 1, fix_task)
        self.device.set_variable("current_plan", plan)
        
        # 3. 更新状态
        self.workflow_state.fix_counter += 1
        
        logger.debug(f"生成修复任务: {fix_task['id']}")
        print(f"\n生成修复任务: {fix_task['name']}")
        print(f"修复指令: {fix_task['instruction'][:100]}...")
        
        return True

    #TODO: 是否区分执行性和信息性任务?
    def execute_single_step(self, step: Dict[str, Any], task_history=None) -> Optional[Result]:
        """执行计划中的单个步骤。"""
        
        agent_name = step.get("agent_name")
        instruction = step.get("instruction")
        instruction_type = step.get("instruction_type", "execution")  # 默认为execution类型
        if not agent_name or not instruction:
            return Result(False, instruction, "", "步骤缺少 agent_name 或 instruction")

        try:
            # 查找指定的智能体
            target_agent = None
            for spec in self.registered_agents:
                if spec.name == agent_name:
                    target_agent = spec.instance
                    break
            
            # 如果找不到指定的智能体，返回错误
            if target_agent is None:
                return Result(False, instruction, "", f"找不到名为 '{agent_name}' 的智能体")

            # 获取前序步骤的结果
            previous_results = []
            if task_history is None:
                task_history = []
            for task in task_history:
                if task.get('result') and getattr(task.get('result'), 'success', False):
                    task_name = task.get('task', {}).get('name', '')
                    return_value = getattr(task.get('result'), 'return_value', '')
                    previous_results.append(f"步骤 {task_name} 的结果:\n{return_value}")

            # 构建包含前序结果的prompt
            prompt = f"""# 执行任务

## 指令
{instruction}

## 前序步骤结果
{chr(10).join(previous_results) if previous_results else "无前序步骤结果"}
"""
            # 使用目标智能体执行任务
            if instruction_type == "information":
                response = target_agent.chat_stream(prompt)
            else:
                response = target_agent.execute_stream(prompt)
                
            # 处理响应流并收集结果
            response_text = ""
            for chunk in response:
                result=chunk
                if isinstance(chunk, str):
                    print(chunk,end="",flush=True)
                    response_text += chunk
                    
            # 根据指令类型解析结果
            if instruction_type == "information":
                return Result(True, instruction, response_text, "", response_text)
            else:
                if isinstance(result, Result):
                    return result
                elif hasattr(result, "return_value") and isinstance(result.return_value, Result):
                    return result.return_value
                else:
                    stdout = getattr(result, "stdout", str(result))
                    stderr = getattr(result, "stderr", None)
                    return Result(False, instruction, stdout, stderr, None)
        except Exception as e:
            return Result(False, instruction, "", str(e), None)

    #TODO: 整合到agent的execute方法
    @reduce_memory_decorator_compress
    def execute_multi_step(self, main_instruction: str, interactive: bool = False) -> str:
        """
        主入口：规划并执行多步骤任务 - 重构后的简化版本
        """
        # 初始化执行上下文
        context = self._initialize_execution_context(main_instruction)
        
        # 主执行循环
        while self._should_continue_execution(context):
            try:
                # 执行一个工作流迭代
                should_break = self._execute_workflow_iteration(context, interactive)
                if should_break:
                    break
            except Exception as e:
                logger.error(f"工作流迭代失败: {e}")
                self._handle_workflow_error(context, e)
                break
        
        return self._generate_execution_summary(context)
    
    def _initialize_execution_context(self, main_instruction: str) -> Dict[str, Any]:
        """初始化执行上下文"""
        # 存储原始目标
        self.original_goal = main_instruction
        
        # 重置工作流状态
        self.workflow_state = WorkflowState()
        
        # 规划步骤
        self.device.set_variable("previous_plan", None)
        plan = self.plan_execution(main_instruction)
        
        return {
            'main_instruction': main_instruction,
            'plan': plan,
            'task_history': [],
            'summary': "",
            'retries': 0,
            'workflow_iterations': 0,
            'context': {"original_goal": main_instruction},
            'max_workflow_iterations': 50
        }
    
    def _should_continue_execution(self, context: Dict[str, Any]) -> bool:
        """判断是否应该继续执行"""
        return (context['retries'] <= self.max_retries and 
                context['workflow_iterations'] < context['max_workflow_iterations'])
    
    def _execute_workflow_iteration(self, context: Dict[str, Any], interactive: bool) -> bool:
        """
        执行一个工作流迭代
        
        Returns:
            bool: 是否应该跳出主循环
        """
        context['workflow_iterations'] += 1
        
        context['plan'] = self.get_plan()
        
        # 选择下一个可执行步骤
        next_step_info = self.select_next_executable_step(context['plan'])
        
        if not next_step_info:
            # 没有可执行步骤，进行决策
            return self._handle_no_executable_steps(context)
        
        # 执行选定的步骤
        current_idx, current_step = next_step_info
        should_break = self._execute_single_workflow_step(current_idx, current_step, context)
        
        if should_break:
            return True
            
        # 交互模式处理
        if interactive and self._check_user_interrupt():
            context['summary'] += "\n用户请求退出。"
            return True
            
        return False
    
    def _handle_no_executable_steps(self, context: Dict[str, Any]) -> bool:
        """
        处理没有可执行步骤的情况
        
        Returns:
            bool: 是否应该跳出主循环
        """
        # 获取最后一个执行结果
        last_result = None
        if context['task_history']:
            last_result = context['task_history'][-1].get('result', None)
        
        # 进行决策
        decision = self.make_decision(
            current_result=last_result,
            task_history=context['task_history'],
            context=context['context']
        )
        
        print(f"\n决策结果: {decision['action']}")
        print(f"原因: {decision['reason']}")
        
        # 处理决策结果
        return self._process_no_steps_decision(decision, context)
    
    def _process_no_steps_decision(self, decision: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        处理没有可执行步骤时的决策结果
        
        Returns:
            bool: 是否应该跳出主循环
        """
        action = decision['action']
        
        if action == 'complete':
            context['summary'] += "\n全部步骤执行完成。"
            self._clear_failure_records()
            return True
            
        elif action == 'generate_new_task' and decision.get('new_tasks'):
            context['summary'] += "\n添加新任务并继续执行。"
            self._add_new_tasks(decision.get('new_tasks', []))
            context['plan'] = self.get_plan()
            return False
            
        else:
            context['summary'] += f"\n所有步骤已处理，决策为: {action}。"
            return True
    
    def _execute_single_workflow_step(self, current_idx: int, current_step: Dict, 
                                     context: Dict[str, Any]) -> bool:
        """
        执行单个工作流步骤
        
        Returns:
            bool: 是否应该跳出主循环
        """
        # 显示执行信息
        plan = context['plan']
        print(f"\n执行步骤 {current_idx+1}/{len(plan)}: {current_step.get('name')}")
        
        # 标记为运行中
        self.update_step_status(current_idx, "running")
        
        # 执行步骤
        exec_result = self.execute_single_step(current_step, context['task_history'])
        
        # 记录任务历史
        context['task_history'].append({
            'task': current_step,
            'result': exec_result,
            'timestamp': dt.now().isoformat()
        })
        
        # 根据执行结果进行后续处理
        if exec_result and exec_result.success:
            return self._handle_step_success(current_idx, exec_result, context)
        else:
            return self._handle_step_failure(current_idx, current_step, exec_result, context)
    
    def _handle_step_success(self, current_idx: int, exec_result: Result, 
                           context: Dict[str, Any]) -> bool:
        """
        处理步骤执行成功的情况
        
        Returns:
            bool: 是否应该跳出主循环
        """
        self.update_step_status(current_idx, "completed", exec_result)
        
        # 执行成功后进行决策
        decision = self.make_decision(
            current_result=exec_result,
            task_history=context['task_history'],
            context=context['context']
        )
        
        print(f"\n决策结果: {decision['action']}")
        print(f"原因: {decision['reason']}")
        
        # 处理成功决策结果
        return self._process_success_decision(decision, context)
    
    def _handle_step_failure(self, current_idx: int, current_step: Dict, 
                           exec_result: Result, context: Dict[str, Any]) -> bool:
        """
        处理步骤执行失败的情况
        
        Returns:
            bool: 是否应该跳出主循环
        """
        # 更新步骤状态
        self.update_step_status(current_idx, "failed", exec_result)
        context['summary'] += f"\n步骤失败: {current_step.get('name')}"
        
        # 失败后进行决策
        decision = self.make_decision(
            current_result=exec_result,
            task_history=context['task_history'],
            context=context['context']
        )
        
        print(f"\n失败后决策: {decision['action']}")
        print(f"原因: {decision['reason']}")
        
        # 处理失败决策
        return self._process_failure_decision(decision, context, current_idx)
    
    def _process_success_decision(self, decision: Dict[str, Any], 
                                context: Dict[str, Any]) -> bool:
        """
        处理成功后的决策
        
        Returns:
            bool: 是否应该跳出主循环
        """
        action = decision['action']
        
        if action == 'complete':
            context['summary'] += "\n决策为完成执行。"
            self._clear_failure_records()
            return True
            
        elif action == 'continue':
            context['summary'] += "\n继续执行下一个步骤。"
            return False
            
        elif action == 'generate_new_task':
            return self._handle_generate_new_task_decision(decision, context)
            
        elif action in ['jump_to', 'loop_back']:
            return self._handle_navigation_decision(decision, context)
            
        elif action == 'generate_fix_task_and_loop':
            return self._handle_fix_task_decision(decision, context)
            
        return False
    
    def _process_failure_decision(self, decision: Dict[str, Any], context: Dict[str, Any], 
                                current_idx: int) -> bool:
        """
        处理失败后的决策
        
        Returns:
            bool: 是否应该跳出主循环
        """
        action = decision['action']
        
        if action == 'retry':
            self.update_step_status(current_idx, "pending")
            context['summary'] += "\n将重试当前步骤。"
            return False
            
        elif action == 'continue':
            context['summary'] += "\n继续执行下一个步骤。"
            return False
            
        elif action == 'generate_new_task':
            return self._handle_generate_new_task_decision(decision, context)
            
        else:
            # 默认处理：增加重试次数
            return self._handle_retry_logic(context)
    
    def _handle_generate_new_task_decision(self, decision: Dict[str, Any], 
                                         context: Dict[str, Any]) -> bool:
        """处理生成新任务的决策"""
        new_tasks = decision.get('new_tasks', [])
        if new_tasks:
            self._add_new_tasks(new_tasks)
            context['plan'] = self.get_plan()
            context['summary'] += "\n添加新任务并继续执行。"
        return False
    
    def _handle_navigation_decision(self, decision: Dict[str, Any], 
                                  context: Dict[str, Any]) -> bool:
        """处理跳转和循环决策"""
        action = decision['action']
        target_step_id = decision.get('target_step_id')
        
        if not target_step_id:
            logger.warning(f"{action}决策缺少target_step_id")
            return False
        
        if action == 'jump_to':
            if self.jump_to_step(target_step_id):
                context['summary'] += f"\n跳转到步骤: {target_step_id}"
            
        elif action == 'loop_back':
            if self.loop_back_to_step(target_step_id):
                context['summary'] += f"\n循环回到步骤: {target_step_id}"
            else:
                context['summary'] += "\n循环失败"
        
        return False
    
    def _handle_fix_task_decision(self, decision: Dict[str, Any], 
                                context: Dict[str, Any]) -> bool:
        """处理修复任务决策"""
        if self.handle_generate_fix_task_and_loop(decision):
            # 执行修复任务
            return self._execute_fix_task(decision, context)
        else:
            context['summary'] += "\n修复任务生成失败或达到最大重试次数"
            return True
    
    def _execute_fix_task(self, decision: Dict[str, Any], 
                         context: Dict[str, Any]) -> bool:
        """执行修复任务"""
        # 获取更新后的计划
        plan = self.get_plan()
        current_idx = self.workflow_state.current_step_index + 1
        
        if current_idx < len(plan):
            fix_task = plan[current_idx]
            print(f"\n执行修复任务: {fix_task.get('name')}")
            
            # 执行修复任务
            self.update_step_status(current_idx, "running")
            fix_result = self.execute_single_step(fix_task)
            
            # 记录修复任务历史
            context['task_history'].append({
                'task': fix_task,
                'result': fix_result,
                'timestamp': dt.now().isoformat()
            })
            
            # 更新修复任务状态
            if fix_result and fix_result.success:
                self.update_step_status(current_idx, "completed", fix_result)
                print(f"修复任务完成: {fix_task.get('name')}")
            else:
                self.update_step_status(current_idx, "failed", fix_result)
                print(f"修复任务失败: {fix_task.get('name')}")
        
        # 循环回到测试步骤
        loop_target = decision.get('loop_target')
        if loop_target and self.loop_back_to_step(loop_target):
            context['summary'] += f"\n生成修复任务并循环回到: {loop_target}"
        
        return False
    
    def _handle_retry_logic(self, context: Dict[str, Any]) -> bool:
        """
        处理重试逻辑
        
        Returns:
            bool: 是否应该跳出主循环
        """
        # 记录失败信息
        self._record_failure_information(context)
        
        # 增加重试计数
        context['retries'] += 1
        if context['retries'] <= self.max_retries:
            context['summary'] += f"\n第{context['retries']}次重试。"
            return False
        else:
            context['summary'] += "\n已达最大重试次数。"
            return True
    
    def _record_failure_information(self, context: Dict[str, Any]) -> None:
        """记录失败信息以供下次重试参考"""
        plan = context['plan']
        failures = [
            {
                "id": step.get("id"), 
                "name": step.get("name"), 
                "error": step.get("result", {}).get("stderr", "")
            }
            for step in plan if step.get("status") == "failed"
        ]
        
        failure_verification = f"执行失败的步骤: {json.dumps(failures, ensure_ascii=False, indent=2)}"
        
        try:
            self.device.set_variable("previous_attempt_failed", True)
            self.device.set_variable("previous_verification", failure_verification)
            self.device.set_variable("previous_plan", {"steps": plan})
        except Exception as e:
            logger.warning(f"设置失败记录时出错: {e}")
    
    def _check_user_interrupt(self) -> bool:
        """检查用户是否要求中断"""
        user_input = input("\n按Enter继续，输入'q'退出: ")
        return user_input.lower() == 'q'
    
    def _clear_failure_records(self) -> None:
        """清除失败记录"""
        try:
            self.device.set_variable("previous_attempt_failed", False)
            self.device.set_variable("previous_verification", None)
        except Exception as e:
            logger.warning(f"清除失败记录时出错: {e}")
    
    
    def _handle_workflow_error(self, context: Dict[str, Any], error: Exception) -> None:
        """处理工作流执行错误"""
        context['summary'] += f"\n工作流执行出错: {str(error)}"
        logger.error(f"工作流执行出错: {error}")
    
    def _generate_execution_summary(self, context: Dict[str, Any]) -> str:
        """生成最终执行摘要"""
        all_steps = context['plan']
        completed_steps = [s for s in all_steps if s.get("status") == "completed"]
        failed_steps = [s for s in all_steps if s.get("status") == "failed"]
        pending_steps = [s for s in all_steps if s.get("status") not in ("completed", "failed", "skipped")]
        
        return f"""
## 执行摘要
- 总步骤数: {len(all_steps)}
- 已完成: {len(completed_steps)}
- 失败: {len(failed_steps)}
- 未执行: {len(pending_steps)}

{context['summary']}
"""
    

    def make_decision(self, current_result, task_history=None, context=None):
        """
        分析当前执行结果并决定下一步操作
        
        Args:
            current_result: 当前执行结果（Result对象或其他结果）
            task_history: 任务执行历史记录（可选）
            context: 额外的上下文信息（可选）
            
        Returns:
            决策结果字典，包含action、reason和new_tasks
        """
        # 生成决策提示
        decision_prompt = self._generate_decision_prompt(current_result, task_history, context)
        
        # 调用LLM进行决策
        try:
            result = self.chat_sync(decision_prompt)
            if result.success:
                decision_text = result.return_value if result.return_value else result.stdout
                return self._parse_decision(decision_text)
            else:
                logger.warning(f"决策失败: {result.stderr}")
                # 默认决策 - 继续执行
                return {
                    'action': 'continue',
                    'reason': '决策过程出错，默认继续执行',
                    'new_tasks': []
                }
        except Exception as e:
            logger.error(f"决策过程异常: {e}")
            return {
                'action': 'continue',
                'reason': f'决策过程异常: {e}',
                'new_tasks': []
            }
    
    def _generate_decision_prompt(self, current_result, task_history=None, context=None):
        """
        生成用于决策的提示 (方案2: 支持循环和条件分支控制)
        
        Args:
            current_result: 当前执行结果
            task_history: 任务执行历史
            context: 额外的上下文信息
            
        Returns:
            决策提示字符串
        """
        # 获取当前计划和状态
        plan = self.get_plan()
        # 不再使用固定的current_step_index，而是基于任务历史确定当前状态
        
        # 获取可用智能体列表
        available_agents = "\n".join([
            f"- {spec.name}: {spec.description}" for spec in self.registered_agents
        ]) if self.registered_agents else "无可用智能体"
        
        # 格式化当前结果
        if isinstance(current_result, Result):
            result_str = f"成功: {current_result.success}\n"
            if current_result.stdout:
                result_str += f"输出: {current_result.stdout[:500]}{'...' if len(current_result.stdout) > 500 else ''}\n"
            if current_result.stderr:
                result_str += f"错误: {current_result.stderr}\n"
            if current_result.return_value:
                result_str += f"返回值: {current_result.return_value}\n"
        else:
            result_str = str(current_result)
        
        # 格式化任务历史（如果有）
        history_str = ""
        if task_history:
            try:
                history_items = []
                for item in task_history:
                    if isinstance(item, dict):
                        task = item.get('task', {})
                        task_id = task.get('id', 'unknown')
                        task_name = task.get('name', 'unnamed')
                        task_result = item.get('result', {})
                        task_success = getattr(task_result, 'success', False)
                        history_items.append(f"任务 {task_id} ({task_name}): {'成功' if task_success else '失败'}")
                history_str = "\n".join(history_items)
            except Exception as e:
                history_str = f"无法格式化任务历史: {e}"
        
        # 检查剩余任务
        completed_steps = [step for step in plan if step.get('status') == 'completed']
        pending_steps = [step for step in plan if step.get('status') not in ['completed', 'skipped']]
        remaining_steps_str = "\n".join([
            f"- {step.get('id')}: {step.get('name')}" for step in pending_steps
        ]) if pending_steps else "无剩余步骤"
        
        # 工作流状态信息  
        last_executed_step = None
        if task_history:
            last_executed_step = task_history[-1].get('task', {}).get('name', '无')
        
        workflow_state_str = f"""
最后执行步骤: {last_executed_step or '无'}
循环计数器: {self.workflow_state.loop_counters}
修复任务计数: {self.workflow_state.fix_counter}
"""
        
        # 格式化额外上下文（如果有）
        context_str = ""
        if context:
            if isinstance(context, dict):
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            else:
                context_str = str(context)
        
        # 生成决策提示
        prompt = f"""
# 执行决策分析 (方案2: 动态控制流)

## 当前执行状态
已完成步骤数: {len(completed_steps)}
剩余步骤数: {len(pending_steps)}

## 工作流状态
{workflow_state_str}

## 当前结果
{result_str}

## 任务历史
{history_str}

## 可用智能体
{available_agents}

## 剩余步骤
{remaining_steps_str}

## 原始目标
{self.original_goal}

## 额外上下文
{context_str}

## 决策任务
请分析当前执行状态和结果，决定下一步操作。可选的操作有：

### 基本决策类型：
1. **continue**: 继续执行下一个计划步骤
2. **complete**: 完成整个工作流（目标已达成）
3. **retry**: 重试当前步骤
4. **generate_new_task**: 生成新的任务

### 控制流决策类型（方案2新增）：
5. **jump_to**: 跳转到指定步骤ID
6. **loop_back**: 循环回到指定步骤ID
7. **generate_fix_task_and_loop**: 生成修复任务并循环回到测试步骤

## 决策策略

### 测试结果分析（针对测试步骤）
如果当前步骤是测试步骤，请根据测试结果决策：
- **测试成功**: 选择 `complete`
- **测试失败**: 选择 `generate_fix_task_and_loop`，生成修复任务并循环回到测试步骤

### 循环控制策略
- 检查循环次数是否超过限制（当前限制: {self.workflow_state.max_loops}次）
- 如果超过限制，选择 `complete` 并说明原因
- 如果需要修复错误，使用 `generate_fix_task_and_loop`

### 其他策略
- 信息不足: 生成信息收集任务
- 错误处理: 生成诊断和修复任务
- 替代方案: 尝试其他方法

## 输出格式
请以JSON格式返回你的决策：

```json
{{
  "action": "continue|complete|retry|generate_new_task|jump_to|loop_back|generate_fix_task_and_loop",
  "reason": "详细说明你的决策理由",
  "target_step_id": "目标步骤ID（仅用于jump_to和loop_back）",
  "loop_target": "循环目标步骤ID（仅用于generate_fix_task_and_loop）",
  "fix_instruction": "修复指令（仅用于generate_fix_task_and_loop）",
  "fix_agent": "修复智能体（仅用于generate_fix_task_and_loop）",
  "error_details": "错误详情（仅用于generate_fix_task_and_loop）",
  "new_tasks": [
    {{
      "id": "task_id",
      "name": "任务名称",
      "instruction": "详细指令",
      "agent_name": "执行智能体名称",
      "phase": "information|execution|verification",
      "prerequisites": "先决条件描述"
    }}
  ]
}}
```

重要提示：
1. 如果剩余步骤不为空且未达到目标，不要选择complete
2. 如果选择generate_new_task，必须提供完整的new_tasks数组
3. 如果选择控制流操作，必须提供相应的目标步骤ID
4. 新任务的agent_name必须从可用智能体列表中选择
5. 优先使用专门的控制流决策类型来处理循环和条件分支
"""
        return prompt
    
    def _parse_decision(self, decision_text):
        """
        解析决策文本为结构化决策
        
        Args:
            decision_text: 决策文本（可能包含JSON）
            
        Returns:
            解析后的决策字典
        """
        try:
            # 尝试提取JSON部分
            from autogen.code_utils import extract_code
            
            # 先尝试提取代码块
            extracted_json = extract_code(decision_text)
            if extracted_json:
                # 找到了代码块
                for lang, code in extracted_json:
                    if lang == "" or lang.lower() == "json":
                        try:
                            return json.loads(code)
                        except:
                            continue
            
            # 如果没有提取到代码块或解析失败，尝试直接解析
            try:
                return json.loads(decision_text)
            except:
                # 尝试查找JSON格式部分
                import re
                json_pattern = r'\{{[\s\S]*\}}'
                match = re.search(json_pattern, decision_text)
                if match:
                    try:
                        return json.loads(match.group(0))
                    except:
                        pass
            
            # 所有JSON解析方法都失败，使用简单的文本分析
            decision = {}
            if 'generate_new_task' in decision_text.lower():
                decision['action'] = 'generate_new_task'
            elif 'retry' in decision_text.lower():
                decision['action'] = 'retry'
            elif 'complete' in decision_text.lower():
                decision['action'] = 'complete'
            else:
                decision['action'] = 'continue'
            
            decision['reason'] = "基于文本分析的决策（JSON解析失败）"
            decision['new_tasks'] = []
            
            return decision
            
        except Exception as e:
            logger.error(f"决策解析失败: {e}")
            # 返回默认决策
            return {
                'action': 'continue',
                'reason': f'决策解析失败: {e}',
                'new_tasks': []
            }

