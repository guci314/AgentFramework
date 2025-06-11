# %%
from agent_base import Result
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

class AgentSpecification:
    """存储 Agent 元数据"""
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
        agent_specs: Optional[List[AgentSpecification]] = None,
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
        self.agent_specs = agent_specs if agent_specs is not None else []
        self.max_retries = max_retries
        self.thinker_chat_system_message = thinker_chat_system_message
        # 注册成员 Agent 到 StatefulExecutor 的变量空间
        for spec in self.agent_specs:
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
- execution: 执行性任务，会调用jupyter notebook执行代码对外部世界产生行为或观察，同时改变智能体的记忆（如执行代码、文件操作、数据写入等）
- information: 信息性任务，只是对智能体记忆的查询或修改，不会调用jupyter notebook（如查询数据、告知状态等）

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
- execution: 执行性任务，会调用jupyter notebook执行代码对外部世界产生行为或观察，同时改变智能体的记忆（如执行代码、文件操作、数据写入等）
- information: 信息性任务，只是对智能体记忆的查询或修改，不会调用jupyter notebook（如查询数据、告知状态等）

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
      "agent_name": "decision_maker",
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
        spec = AgentSpecification(name=name, instance=instance, description=description)
        self.agent_specs.append(spec)
        self.device.set_variable(spec.name, spec.instance)
        logger.debug(f"已注册 Agent: {name}")
    
    def ensure_decision_maker_agent(self):
        """确保注册了决策智能体（如果还没有的话）"""
        decision_maker_exists = any(spec.name == "decision_maker" for spec in self.agent_specs)
        if not decision_maker_exists:
            # 创建一个决策智能体
            decision_agent = Agent(llm=self.llm)
            decision_agent.api_specification = """
            决策智能体，负责分析执行结果并决定工作流的下一步操作。
            专门处理循环控制、条件分支和错误修复决策。
            """
            self.register_agent("decision_maker", decision_agent)
            logger.debug("自动注册了决策智能体")

    def plan_execution(self, main_instruction: str) -> List[Dict[str, Any]]:
        """
        根据主指令规划执行步骤，支持自定义提示词模板。
        """
        # 如果不是自主规划模式，确保有决策智能体 (方案2)
        if not self.use_autonomous_planning:
            self.ensure_decision_maker_agent()
        
        # 构建可用 Agent 的描述字符串
        available_agents_str = "\n".join(
            [f"- {spec.name}: {spec.description}" for spec in self.agent_specs]
        )
        if not available_agents_str:
            available_agents_str = "无可用 Agent。请确保已注册 Agent。"
            
        # 获取可用 Agent 名称列表
        available_agent_names = [spec.name for spec in self.agent_specs] or ["无"]
        
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
                "agent_name": self.agent_specs[0].name if self.agent_specs else "general_agent",
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
                    "agent_name": self.agent_specs[0].name if self.agent_specs else "general_agent",
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
                step["agent_name"] = self.agent_specs[0].name if self.agent_specs else "general_agent"
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
        """基于Agent记忆和系统状态判断步骤可执行性"""
        
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

返回格式：
可执行: true/false
原因: 具体说明
"""
        
        try:
            # 使用Agent的记忆进行判断
            response = self.chat_sync(check_prompt)
            response_text = response.return_value if response.return_value else response.stdout
            
            # 解析响应
            response_lower = response_text.lower()
            # 处理各种可能的格式：可执行: true, **可执行**: true, 可执行:true 等
            executable = (
                "可执行: true" in response_lower or 
                "可执行:true" in response_lower or
                "**可执行**: true" in response_lower or
                "**可执行**:true" in response_lower or
                "可执行**:" in response_lower and "true" in response_lower or
                "executable: true" in response_lower
            )
            
            # 提取原因
            reason_start = response_text.find("原因:")
            if reason_start != -1:
                reason = response_text[reason_start + 3:].strip()
            else:
                reason = response_text
            
            return executable, reason
            
        except Exception as e:
            logger.warning(f"判断步骤可执行性时出错: {e}")
            # 默认可执行，让Agent自己判断
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
    def execute_single_step(self, step: Dict[str, Any]) -> Optional[Result]:
        """执行计划中的单个步骤。"""
        
        agent_name = step.get("agent_name")
        instruction = step.get("instruction")
        instruction_type = step.get("instruction_type", "execution")  # 默认为execution类型
        if not agent_name or not instruction:
            return Result(False, "", "", "步骤缺少 agent_name 或 instruction")

        try:
            # 调用成员 Agent 执行
            # result = self.device.execute_code(
            #     f'{agent_name}.execute_sync("""{instruction}""")'
            # )
            result=None
            prompt=f"""
# 执行任务

## 任务类型
{instruction_type}

## 指令
{instruction}

## 执行者
{agent_name}


"""
            # 根据指令类型选择执行方式
            if instruction_type == "information":
                # information类型任务使用chat_stream - 只改变智能体记忆，不对外部环境产生行为
                response = self.chat_stream(prompt)
            else:
                # execution类型任务使用execute_stream - 会改变智能体记忆和外部环境
                response = self.execute_stream(prompt)
                
            # 处理响应流并收集结果
            response_text = ""
            for chunk in response:
                result=chunk
                if isinstance(chunk, str):
                    print(chunk,end="",flush=True)
                    response_text += chunk
                    
            # 根据指令类型解析结果
            if instruction_type == "information":
                # information类型任务：chat_stream返回字符串，构造成功的Result
                return Result(True, instruction, response_text, "", response_text)
            else:
                # execution类型任务：解析execute_stream返回的Result
                if isinstance(result, Result):
                    return result
                elif hasattr(result, "return_value") and isinstance(result.return_value, Result):
                    return result.return_value
                else:
                    # 如果返回的不是 Result，尝试构造一个失败的 Result
                    stdout = getattr(result, "stdout", str(result))
                    stderr = getattr(result, "stderr", None)
                    return Result(False, instruction, stdout, stderr, None)
        except Exception as e:
            return Result(False, instruction, "", str(e), None)

    #TODO: 整合到agent的execute方法
    def execute_multi_step(self, main_instruction: str, interactive: bool = False) -> str:
        """
        主入口：规划并执行多步骤任务 (方案2: 动态控制流)
        """
        # 存储原始目标和任务历史
        self.original_goal = main_instruction
        task_history = []
        
        # 重置工作流状态
        self.workflow_state = WorkflowState()
        
        # 规划步骤
        self.device.set_variable("previous_plan",None)
        plan = self.plan_execution(main_instruction)
        summary = ""
        retries = 0
        max_workflow_iterations = 50  # 防止无限循环
        workflow_iterations = 0
        
        # 提供原始目标作为上下文
        context = {"original_goal": main_instruction}

        while retries <= self.max_retries and workflow_iterations < max_workflow_iterations:
            workflow_iterations += 1
            plan = self.get_plan()
            
            # 使用智能调度选择下一个可执行步骤
            next_step_info = self.select_next_executable_step(plan)
            
            # 如果没有更多可执行步骤
            if not next_step_info:
                # 决策：是否真的全部完成了？
                last_result = None
                if task_history:
                    last_result = task_history[-1].get('result', None)
                
                decision = self.make_decision(
                    current_result=last_result,
                    task_history=task_history,
                    context=context
                )
                
                print(f"\n决策结果: {decision['action']}")
                print(f"原因: {decision['reason']}")
                
                # 如果决策是完成，则结束执行
                if decision['action'] == 'complete':
                    summary += "\n全部步骤执行完成。"
                    # 清除任何失败记录
                    if hasattr(self, 'device'):
                        try:
                            self.device.set_variable("previous_attempt_failed", False)
                            self.device.set_variable("previous_verification", None)
                        except Exception as e:
                            logger.warning(f"清除失败记录时出错: {e}")
                    break
                # 如果决策是生成新任务
                elif decision['action'] == 'generate_new_task' and decision.get('new_tasks'):
                    summary += "\n添加新任务并继续执行。"
                    self._add_new_tasks(decision.get('new_tasks', []))
                    plan = self.get_plan()
                    continue
                else:
                    # 如果决策是继续但没有更多步骤，或者是其他决策
                    summary += f"\n所有步骤已处理，决策为: {decision['action']}。"
                    break
            
            # 获取选择的步骤
            current_idx, current_step = next_step_info
            
            # 执行当前步骤
            print(f"\n执行步骤 {current_idx+1}/{len(plan)}: {current_step.get('name')}")
            
            # 标记为 running
            self.update_step_status(current_idx, "running")
            
            # 执行单个步骤
            exec_result = self.execute_single_step(current_step)
            
            # 记录任务历史
            task_history.append({
                'task': current_step,
                'result': exec_result,
                'timestamp': dt.now().isoformat()
            })
            
            # 更新状态
            if exec_result and exec_result.success:
                self.update_step_status(current_idx, "completed", exec_result)
                
                # 注释掉自动递增逻辑，因为智能调度会直接选择下一个步骤
                # self.workflow_state.current_step_index = current_idx + 1
                
                # 执行成功后，使用make_decision决定下一步
                decision = self.make_decision(
                    current_result=exec_result,
                    task_history=task_history,
                    context=context
                )
                
                print(f"\n决策结果: {decision['action']}")
                print(f"原因: {decision['reason']}")
                
                # 根据决策执行操作 (方案2: 支持控制流决策)
                if decision['action'] == 'complete':
                    summary += "\n决策为完成执行。"
                    # 清除任何失败记录
                    if hasattr(self, 'device'):
                        try:
                            self.device.set_variable("previous_attempt_failed", False)
                            self.device.set_variable("previous_verification", None)
                        except Exception as e:
                            logger.warning(f"清除失败记录时出错: {e}")
                    break
                
                elif decision['action'] == 'continue':
                    # 继续执行下一个步骤，什么都不需要做，让循环继续
                    summary += "\n继续执行下一个步骤。"
                    # continue 语句会让执行循环继续到下一轮，选择下一个可执行步骤
                    continue
                
                elif decision['action'] == 'generate_new_task' and decision.get('new_tasks'):
                    # 添加新任务到计划
                    for new_task in decision.get('new_tasks', []):
                        # 确保新任务有必要的字段
                        new_task_id = new_task.get('id', f"dynamic_{len(plan)}")
                        new_task['id'] = new_task_id
                        if 'status' not in new_task:
                            new_task['status'] = 'pending'
                        plan.append(new_task)
                    
                    # 更新计划
                    self.device.set_variable("current_plan", plan)
                    print(f"\n更新执行计划:\n{json.dumps(plan, ensure_ascii=False, indent=2)}\n")
                    summary += "\n添加新任务并继续执行。"
                    continue
                
                elif decision['action'] == 'jump_to':
                    target_step_id = decision.get('target_step_id')
                    if target_step_id:
                        self.jump_to_step(target_step_id)
                        summary += f"\n跳转到步骤: {target_step_id}"
                        # 跳转后继续循环，不要break，让下一次循环处理跳转的目标步骤
                        continue
                    else:
                        logger.warning("jump_to决策缺少target_step_id")
                
                elif decision['action'] == 'loop_back':
                    target_step_id = decision.get('target_step_id')
                    if target_step_id:
                        if self.loop_back_to_step(target_step_id):
                            summary += f"\n循环回到步骤: {target_step_id}"
                            # 循环后继续执行新的目标步骤
                            continue
                        else:
                            summary += f"\n循环回步骤失败，继续执行"
                    else:
                        logger.warning("loop_back决策缺少target_step_id")
                
                elif decision['action'] == 'generate_fix_task_and_loop':
                    if self.handle_generate_fix_task_and_loop(decision):
                        # 执行修复任务
                        current_idx += 1  # 移动到修复任务
                        self.workflow_state.current_step_index = current_idx
                        
                        # 检查并执行修复任务
                        plan = self.get_plan()  # 重新获取更新后的计划
                        if current_idx < len(plan):
                            fix_task = plan[current_idx]
                            print(f"\n执行修复任务: {fix_task.get('name')}")
                            
                            # 标记为运行中
                            self.update_step_status(current_idx, "running")
                            
                            # 执行修复任务
                            fix_result = self.execute_single_step(fix_task)
                            
                            # 记录修复任务历史
                            task_history.append({
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
                        if loop_target:
                            if self.loop_back_to_step(loop_target):
                                summary += f"\n生成修复任务并循环回到: {loop_target}"
                                # 继续执行循环目标步骤，不要break
                                continue
                            else:
                                summary += f"\n修复任务已达最大重试次数"
                                break
                        else:
                            # 如果没有循环目标，继续正常执行流程
                            continue
                    else:
                        summary += "\n修复任务生成失败或达到最大重试次数"
                        break
            else:
                # 步骤执行失败
                self.update_step_status(current_idx, "failed", exec_result)
                summary += f"\n步骤失败: {current_step.get('name')}"
                
                # 失败后，使用make_decision决定是否重试或生成新任务
                decision = self.make_decision(
                    current_result=exec_result,
                    task_history=task_history,
                    context=context
                )
                
                print(f"\n失败后决策: {decision['action']}")
                print(f"原因: {decision['reason']}")
                
                if decision['action'] == 'retry':
                    # 将当前步骤状态重置为未执行
                    self.update_step_status(current_idx, "pending")
                    summary += "\n将重试当前步骤。"
                    continue
                elif decision['action'] == 'continue':
                    # 继续执行下一个步骤
                    summary += "\n继续执行下一个步骤。"
                    continue
                elif decision['action'] == 'generate_new_task' and decision.get('new_tasks'):
                    # 添加新任务（可能是替代方案或修复任务）
                    for new_task in decision.get('new_tasks', []):
                        new_task_id = new_task.get('id', f"dynamic_{len(plan)}")
                        new_task['id'] = new_task_id
                        if 'status' not in new_task:
                            new_task['status'] = 'pending'
                        plan.append(new_task)
                    
                    # 更新计划
                    self.device.set_variable("current_plan", plan)
                    print(f"\n更新执行计划:\n{json.dumps(plan, ensure_ascii=False, indent=2)}\n")
                    summary += "\n添加替代任务并继续执行。"
                    continue
                else:
                    # 处理其他决策类型或默认行为
                    # 记录失败的步骤信息，准备下一次重试整个计划
                    failures = [
                        {"id": step.get("id"), "name": step.get("name"), "error": step.get("result", {}).get("stderr", "")}
                        for step in plan if step.get("status") == "failed"
                    ]
                    failure_verification = f"执行失败的步骤: {json.dumps(failures, ensure_ascii=False, indent=2)}"
                    
                    if hasattr(self, 'device'):
                        try:
                            self.device.set_variable("previous_attempt_failed", True)
                            self.device.set_variable("previous_verification", failure_verification)
                            self.device.set_variable("previous_plan", {"steps": plan})
                        except Exception as e:
                            logger.warning(f"设置失败记录时出错: {e}")
                    
                    # 增加重试计数
                    retries += 1
                    if retries <= self.max_retries:
                        summary += f"\n第{retries}次重试。"
                        # 重试时继续循环
                        continue
                    else:
                        summary += "\n已达最大重试次数。"
                        break
            # 如果是交互模式，等待用户输入
            if interactive:
                user_input = input("\n按Enter继续，输入'q'退出: ")
                if user_input.lower() == 'q':
                    summary += "\n用户请求退出。"
                    break

        # 生成最终执行摘要
        all_steps = plan
        completed_steps = [s for s in all_steps if s.get("status") == "completed"]
        failed_steps = [s for s in all_steps if s.get("status") == "failed"]
        pending_steps = [s for s in all_steps if s.get("status") not in ("completed", "failed", "skipped")]
        
        final_summary = f"""
## 执行摘要
- 总步骤数: {len(all_steps)}
- 已完成: {len(completed_steps)}
- 失败: {len(failed_steps)}
- 未执行: {len(pending_steps)}

{summary}
"""
        return final_summary

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
            f"- {spec.name}: {spec.description}" for spec in self.agent_specs
        ]) if self.agent_specs else "无可用智能体"
        
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

    # def _create_ipython_instance(self):
    #     """
    #     创建一个IPython实例用于执行代码
    #     """
    #     try:
    #         from IPython.core.interactiveshell import InteractiveShell
    #         # 创建配置对象
    #         from traitlets.config import Config
    #         c = Config()
    #         # 禁用matplotlib的自动配置
    #         c.InteractiveShell.pylab = None
    #         # 禁用各种可能导致GUI相关问题的功能
    #         c.InteractiveShell.autoindent = False
    #         c.InteractiveShell.colors = 'NoColor'
    #         c.InteractiveShell.confirm_exit = False
            
    #         # 添加额外的参数来避免循环导入问题
    #         # 禁用交互式自动加载，减少依赖冲突
    #         c.InteractiveShell.cache_size = 0
    #         c.InteractiveShell.autocall = 0
    #         c.InteractiveShell.automagic = False
            
    #         # 使用带有配置的InteractiveShell
    #         # 设置独立命名空间，减少与外部变量冲突
    #         ipython = InteractiveShell.instance(config=c, display_banner=False, user_ns={})
            
    #         # 预先导入常用模块，确保初始化正确
    #         ipython.run_cell("import sys, os")
            
    #         # 安全地配置matplotlib (如果有需要)
    #         try:
    #             # 设置matplotlib配置以避免GUI初始化
    #             ipython.run_cell("import matplotlib\nmatplotlib.use('Agg')")
    #         except Exception as e:
    #             # 忽略matplotlib相关错误
    #             pass
                
    #         return ipython
    #     except ImportError:
    #         logging.error("无法导入IPython，某些功能可能不可用")
    #         return None

#%%


#%%
# ====== 示例 main 代码块 ======
if __name__ == "__main__":
    # 设置代理服务器
    # import os
    # os.environ['http_proxy'] = 'http://127.0.0.1:7890'
    # os.environ['https_proxy'] = 'http://127.0.0.1:7890'
    
    # os.environ["AGENT_MAX_TOKENS"] = "1000000"
    from pythonTask import *
    from knowledge_agent import promgraming_knowledge
     
    
    # llm=llm_claude_sonnet_4
    # llm=llm_gemini_2_5_pro_preview_06_05_google
    llm=llm_deepseek
    
    # 实例化 MultiStepAgent_v2 时不传入 agent_specs
    multi_agent = MultiStepAgent_v2(llm=llm)

    # 使用 register_agent 动态注册 Agent
    # coder_agent = Agent(llm=llm)
    # multi_agent.register_agent(
    #     name="coder",
    #     instance=coder_agent,
    #     description="通用Agent"
    # )
    
    document_agent = Agent(llm=llm)
    document_agent.loadKnowledge(promgraming_knowledge)
    document_agent.loadKnowledge('如果指令要求你写文档，你应该调用gemini语言模型生成文档')
    document_agent.api_specification='''
    文档Agent,擅长写文档
    '''
    multi_agent.register_agent(
        name="document_agent",
        instance=document_agent
    )
    
    
    # 示例主指令
    # main_instruction = "请用python写一个hello world程序"
    main_instruction = """
    
    # 销售数据分析任务

sales_data.csv是销售数据文件，请使用此文件进行数据分析。

# 规则
1. 不要生成图表
2. 报告中必须包含每个地区，每个产品，每个销售人员的销售额
3. 分析报告保存到sales_analysis_report.md
4. 分析报告必须调用gemini模型生成

    """

    # 执行多步骤任务
    result = multi_agent.execute_multi_step(main_instruction)
    print("多步骤执行结果：")
    print(result)

#%%
if __name__ == "__main__":
    summary_prompt='''
    你的任务是创建一份详细的对话总结，密切关注用户的明确要求和你之前的行动。
    这份总结应该全面捕获技术细节、代码模式和架构决策，这些对于继续对话和支持任何后续任务都是必不可少的。
    你的总结应该按以下结构组织：
    上下文：继续对话所需的上下文。如果根据当前任务适用，这应该包括：
    之前的对话：关于整个与用户对话中讨论内容的高层次细节。这应该写得让别人能够跟上总体对话流程。
    当前工作：详细描述在此次总结请求之前正在进行的工作。特别注意对话中最近的消息。
    关键技术概念：列出所有重要的技术概念、技术、编码约定和讨论过的框架，这些可能与继续这项工作相关。
    相关文件和代码：如果适用，枚举为任务继续而检查、修改或创建的具体文件和代码部分。特别注意最近的消息和更改。
    问题解决：记录到目前为止解决的问题和任何正在进行的故障排除工作。
    待处理任务和下一步：概述你被明确要求处理的所有待处理任务，以及列出你将为所有未完成工作采取的下一步，如果适用的话。在能增加清晰度的地方包含代码片段。对于任何下一步，包含来自最近对话的直接引用，准确显示你正在处理的任务以及你停止的地方。这应该是逐字逐句的，以确保任务之间的上下文没有信息丢失。
    示例总结结构：
    之前的对话：
    [详细描述]
    当前工作：
    [详细描述]
    关键技术概念：
    [概念1]
    [概念2]
    [...]
    相关文件和代码：
    [文件名1]
    [此文件重要性的总结]
    [对此文件所做更改的总结，如有的话]
    [重要代码片段]
    [文件名2]
    [重要代码片段]
    [...]
    问题解决：
    [详细描述]
    待处理任务和下一步：
    [任务1详情和下一步]
    [任务2详情和下一步]
    [...]
    仅输出到目前为止的对话总结，不要添加任何其他评论或解释。
    '''

    resonse=multi_agent.chat_stream(summary_prompt)
    for chunk in resonse:
        print(chunk,end='',flush=True)

#%%
if __name__ == "__main__":
    import os
    # os.environ["AGENT_MAX_TOKENS"] = "1000000"
    from pythonTask import *
    from knowledge_agent import promgraming_knowledge
     
    # llm=llm_gemini_2_5_pro_preview_05_06_google
    llm=llm_deepseek
    

    # 实例化 MultiStepAgent_v2 时不传入 agent_specs
    multi_agent = MultiStepAgent_v2(llm=llm)

    # 使用 register_agent 动态注册 Agent
    # coder_agent = Agent(llm=llm)
    # multi_agent.register_agent(
    #     name="coder",
    #     instance=coder_agent,
    #     description="通用Agent"
    # )
    
    web_agent = Agent(llm=llm)
    web_agent.loadPythonModules(['aiTools'])
    web_agent.loadKnowledge('''
    如果指令要求你写文档，你应该调用gemini语言模型生成文档
    ## 调用语言模型示例
    from langchain_openai import ChatOpenAI
    from dotenv import load_dotenv
    load_dotenv()
    llm_gemini_2_flash_openrouter = ChatOpenAI(
        temperature=0,
        model="google/gemini-2.0-flash-001", 
        base_url='https://openrouter.ai/api/v1',
        api_key=os.getenv('OPENROUTER_API_KEY'
    )
    x:str=llm_gemini_2_flash_openrouter.invoke("你好").content
    print(x)
    ''')
    web_agent.api_specification='''
    web_agent,擅长搜索网络信息,抓取网页内容，生成报告
    '''
    multi_agent.register_agent(
        name="web_agent",
        instance=web_agent
    )
    
    
    # 示例主指令
    # main_instruction = "请用python写一个hello world程序"
    main_instruction = """
    
    # 任务
    1:使用关键词crewai 搜索网络信息，抓取搜索结果的前10个网页，把抓取到的网页合并保存在变量web_content中
    2:根据web_content调用gemini模型生成crewai教程，教程大约3000字，教程必须使用中文。教程需包含crewai的系统架构，核心组件，示例代码。
    3:教程保存在/home/guci/myModule/AiResearch/crewai_tutorial.md

    """

    # 执行多步骤任务
    result = multi_agent.execute_multi_step(main_instruction)
    print("多步骤执行结果：")
    print(result)

#%%

#%%
if __name__ == "__main__":
    import os
    os.environ["AGENT_MAX_TOKENS"] = "1000000"
    from pythonTask import *
    from knowledge_agent import promgraming_knowledge
     
    llm_qwen3_235b_openrouter = ChatOpenAI(
    temperature=0,
    model="qwen/qwen3-235b-a22b:NovitaAI", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
    )
    
    llm_qwen3_32b_openrouter = ChatOpenAI(
    temperature=0,
    model="qwen/qwen3-32b:NovitaAI", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
    )
    
    llm_qwen3_30b_openrouter = ChatOpenAI(
    temperature=0,
    model="qwen/qwen3-30b-a3b:NovitaAI", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
    )
    
    llm_qwen3_8b_openrouter = ChatOpenAI(
    temperature=0,
    model="qwen/qwen3-8b", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'),
    )
    
    
    # llm=llm_llama_4_maverick_openrouter 
    llm=llm_gemini_2_5_pro_preview_05_06_google
    # llm=llm_qwen3_30b_openrouter
    # llm=llm_Pro_DeepSeek_V3_siliconflow



    # 实例化 MultiStepAgent_v2 时不传入 agent_specs
    multi_agent = MultiStepAgent_v2(llm=llm)
    
    '''
    内存编程Agent有能力搜索互联网，抓取网页内容。
    '''
    
    researcher = Agent(llm=llm)
    researcher.loadPythonModules(['aiTools'])
    researcher.loadKnowledge('''
    ## 调用语言模型示例
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
llm_gemini_2_flash_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.0-flash-001", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'
)
x:str=llm_gemini_2_flash_openrouter.invoke("你好").content
print(x)

## 如果指令要求你写文档，你应该调用gemini语言模型生成文档
    ''')
    researcher.api_specification='''
    研究者，擅长搜索互联网，抓取网页内容，写报告。
    
    输入：
     研究主题
    
    输出：
    研究报告
    
    # 示例
    response=researcher.execute_stream('请搜索互联网，抓取网页内容，写个multi agent system报告') #response是一个迭代器，迭代器前面是过程信息，迭代器最后一个元素是Result对象
    result=None
    for chunk in response:
        result=chunk
        print(chunk,end='',flush=True)
        
    report=result.return_value #result.return_value中包含最终的报告
    print(report)
    
    '''
    multi_agent.register_agent(
        name="researcher",
        instance=researcher
    )
    
    # 使用 register_agent 动态注册 Agent
    coder = Agent(llm=llm)
    coder.loadKnowledge('''
    ## 调用语言模型示例
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
llm_gemini_2_flash_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.0-flash-001", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'
)
x:str=llm_gemini_2_flash_openrouter.invoke("你好").content
print(x)
    ''')
    # coder.loadPythonModules(['aiTools'])
    coder.api_specification='''
    内存编程Agent，擅长编写python代码。它在内存中的jupyter notebook中编写和运行代码。
    
    输入：
    1. 程序描述（或者运行程序的报错信息）
    2. context信息，编程需要的相关知识
    
    输出：
    程序代码和说明
    
    # 示例
    response=coder.execute_stream('写个函数生成斐波那契数列的第n个数') #response是一个迭代器，迭代器前面是过程信息，迭代器最后一个元素是Result对象
    result=None
    for chunk in response:
        result=chunk
        print(chunk,end='',flush=True)
        
    code=result.code #result.code中包含最终的代码
    print(code)
    
    '''
    multi_agent.register_agent(
        name="coder",
        instance=coder
    )
    
    code_file_editor = Agent(llm=llm)
    code_file_editor.loadKnowledge('''
    ## 编程任务示例代码
    import aider_demo.aider_programming_demo
    instruction = f"保存代码到{file_name}\n#代码\n{code}" 
    edit_file_names=[{file_name}] # 要编辑的文件列表
    read_only_files=[] # 只读文件列表，只读文件不会被修改，是要编辑的文件依赖的文件
    result=aider_demo.aider_programming_demo.programming(instruction,edit_file_names,read_only_files) # 执行编程任务
    print(result) # 打印编程任务结果

    ## 如果指令是编写或修改或保存python文件，优先使用aider_demo.aider_programming_demo.programming函数执行编程任务修改python文件。如果programming函数失败，直接使用python代码修改文件。
                                ''')
    
    code_file_editor.api_specification="""
    python文件编辑Agent，擅长编辑python文件。
    
    输入：
    1. 代码或者写个代码的指令
    2. 要编辑的文件列表
    3. 只读文件列表，只读文件不会被修改，是要编辑的文件依赖的文件
    
    输出：
    1. 编辑后的代码
    2. 编辑后的代码说明
    
    # 示例
    #假设代码保存在变量code中
    response=code_file_editor.execute_stream(f'''
    把代码保存到/home/guci/myModule/AiResearch/math1.py

    # 代码
    {code}
                                            ''')
    result=None
    for chunk in response:
        result=chunk
        print(chunk,end='',flush=True)
        
    print(result.return_value)
    """
    multi_agent.register_agent(
        name="code_file_editor",
        instance=code_file_editor
    )
    
    task_executer=Agent(llm=llm)
    task_executer.api_specification="""
    任务执行Agent，擅长执行任务。
    """
    multi_agent.register_agent(
        name="task_executer",
        instance=task_executer
    )
    
    # 示例主指令
    main_instruction_crewai = """
    
    # 任务
    1：调用coder写个crewai的示例程序。示例程序必须仅仅依赖context中的api key就可运行。示例程序必须演示crewai的SerperDevTool
    2：调用code_file_editor把程序保存在/home/guci/myModule/AiResearch/crewai_example.py
    
    # context
    ##  语言模型
    llm=aiTools.llm_openrouter("openrouter/meta-llama/llama-4-maverick")
    
    ## serper api key
    serper_api_key=ed33c6dd1d0591b3a7d60c14b000281b7ed37108

    # 验证任务成功的标准
    1.程序成功运行
    2.程序使用了crewai的SerperDevTool
    3.程序输出了正确的结果

    """
    
    # main_instruction = """
    
    # # 任务
    # 1：调用coder搜索互联网查找crewai的serper tool的使用方法。
    # 2：调用coder阅读/home/guci/myModule/AiResearch/crewai_example.py
    # 3：调用coder修改/home/guci/myModule/AiResearch/crewai_example.py，使用serper tool搜索互联网信息。
    # 4：调用code_file_editor把修改后的程序保存在/home/guci/myModule/AiResearch/crewai_example.py
    
    # # context
    # 语言模型请使用deepseek
    # from dotenv import load_dotenv
    # load_dotenv()
    # from langchain_openai import ChatOpenAI
    # llm_deepseek = ChatOpenAI(
    #     temperature=0,
    #     model="deepseek/deepseek-chat",  
    #     base_url="https://api.deepseek.com",
    #     api_key=os.getenv('DEEPSEEK_API_KEY'),
    #     max_tokens=8192
    # )
    
    # # serper api key
    # serper_api_key=ed33c6dd1d0591b3a7d60c14b000281b7ed37108


    # """
    
    main_instruction='''
    记忆压缩函数软件设计说明书（定制版）
1. 功能描述
本函数用于对一组对话消息（BaseMessage的list，且HumanMessage和AIMessage交替出现）进行记忆压缩。其目标是：
保持消息列表中最后10条消息内容不变；
对前面的消息进行总结压缩，生成一条人类消息（HumanMessage）和一条AI消息（AIMessage，内容为"ok"），替换原有的多条消息。
2. 输入输出
输入
类型：List[BaseMessage]
约束：消息类型为HumanMessage和AIMessage，且严格交替出现（即HumanMessage, AIMessage, HumanMessage, ...）
输出
类型：List[BaseMessage]
说明：前N-10条消息被压缩为一条HumanMessage和一条AIMessage，后10条消息保持原样。
3. 主要流程
分割消息
将输入消息列表分为两部分：前N-10条（需压缩），后10条（保持原样）。
压缩前段消息
将前N-10条消息内容进行合并、总结，生成一条HumanMessage（内容为合并/摘要后的内容）。
生成一条AIMessage，内容为"ok"。
拼接输出
将压缩后的两条消息与后10条原始消息合并，输出新的消息列表。



4. 关键点说明
摘要算法：summarize_messages可以简单实现为将所有HumanMessage和AIMessage的内容拼接，使用llm_gemini_2_flash_openrouter模型生成摘要。
消息类型：压缩后前两条消息分别为HumanMessage和AIMessage，AIMessage内容固定为"ok"。
边界处理：若消息总数≤10，则无需压缩，直接返回原消息列表。


    #任务
    实现上面的函数保存到/home/guci/myModule/AiResearch/message_compress.py
    '''

    # 执行多步骤任务
    result = multi_agent.execute_multi_step(main_instruction_crewai)
    print("多步骤执行结果：")
    print(result)
    
#%%
if __name__ == "__main__":
    
    instruction='''
    记忆压缩函数软件设计说明书（定制版）
1. 功能描述
from langchain_core.messages import HumanMessage,AIMessage,BaseMessage
本函数用于对一组对话消息（BaseMessage的list，且HumanMessage和AIMessage交替出现）进行记忆压缩。其目标是：
保持消息列表中最后10条消息内容不变；
对前面的消息进行总结压缩，生成一条人类消息（HumanMessage）和一条AI消息（AIMessage，内容为"ok"），替换原有的多条消息。
2. 输入输出
输入
类型：List[BaseMessage]
约束：消息类型为HumanMessage和AIMessage，且严格交替出现（即HumanMessage, AIMessage, HumanMessage, ...）
输出
类型：List[BaseMessage]
说明：前N-10条消息被压缩为一条HumanMessage和一条AIMessage，后10条消息保持原样。
3. 主要流程
分割消息
将输入消息列表分为两部分：前N-10条（需压缩），后10条（保持原样）。
压缩前段消息
将前N-10条消息内容进行合并、总结，生成一条HumanMessage（内容为合并/摘要后的内容）。总结请使用llm_gemini_2_flash_openrouter语言模型。
生成一条AIMessage，内容为"ok"。
拼接输出
将压缩后的两条消息与后10条原始消息合并，输出新的消息列表。

## 调用语言模型示例
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
llm_gemini_2_flash_openrouter = ChatOpenAI(
    temperature=0,
    model="google/gemini-2.0-flash-001", 
    base_url='https://openrouter.ai/api/v1',
    api_key=os.getenv('OPENROUTER_API_KEY'
)
x:str=llm_gemini_2_flash_openrouter.invoke("你好").content
print(x)

4. 关键点说明
摘要算法：summarize_messages可以简单实现为将所有HumanMessage和AIMessage的内容拼接，使用gemini模型生成摘要。
消息类型：压缩后前两条消息分别为HumanMessage和AIMessage，AIMessage内容固定为"ok"。
边界处理：若消息总数≤10，则无需压缩，直接返回原消息列表。


    #任务
    实现上面的函数,可以使用langchain的库
    '''
    from pythonTask import llm_gemini_2_5_pro_preview_05_06_google,llm_deepseek,llm_deepseek_r1
    from prompts import information_task_evaluate_message
    llm=llm_deepseek_r1
    agent=Agent(llm=llm,evaluation_system_messages=[information_task_evaluate_message])
    agent.loadKnowledge('''
    # 代码规范
    1. 代码注释请使用中文
    2. 除了功能代码，必须有测试代码
    3. 测试代码必须放到if __name__ == "__main__":中
    4. 多行注释请使用三个单引号，不要使用三个双引号
    
                        ''')
    response=agent.execute_stream(instruction)
    result=None
    for chunk in response:
        result=chunk
        print(chunk,end='',flush=True)

#%%
if __name__ == "__main__":
    instruction='''
    把代码保存到/home/guci/myModule/AiResearch/message_compress.py
    '''
    response=agent.execute_stream(instruction)
    result=None
    for chunk in response:
        result=chunk
        print(chunk,end='',flush=True)
        
        
#%%
if __name__ == "__main__":
    response=agent.chat_stream('请输出完整的代码，不要输出任何解释')
    result=None
    for chunk in response:
        result=chunk
        print(chunk,end='',flush=True)
#%%
if __name__ == "__main__":
    from autogen.code_utils import extract_code
    code=extract_code(result.return_value)[0][1]
    print(code)

#%%
if __name__ == "__main__":
    llm=llm_deepseek
    code_file_editor = Agent(llm=llm)
    code_file_editor.loadKnowledge('''
    ## 编程任务示例代码
    import aider_demo.aider_programming_demo
    instruction = f"保存代码到{file_name}\n#代码\n{code}" 
    edit_file_names=[{file_name}] # 要编辑的文件列表
    read_only_files=[] # 只读文件列表，只读文件不会被修改，是要编辑的文件依赖的文件
    result=aider_demo.aider_programming_demo.programming(instruction,edit_file_names,read_only_files) # 执行编程任务
    print(result) # 打印编程任务结果

    ## 如果指令是编写或修改或保存python文件，优先使用aider_demo.aider_programming_demo.programming函数执行编程任务修改python文件。如果programming函数失败，直接使用python代码修改文件。
                                ''')
    
    code_file_editor.api_specification="""
    python文件编辑Agent，擅长编辑python文件。
    
    输入：
    1. 代码或者写个代码的指令
    2. 要编辑的文件列表
    3. 只读文件列表，只读文件不会被修改，是要编辑的文件依赖的文件
    
    输出：
    1. 编辑后的代码
    2. 编辑后的代码说明
    
    # 示例
    #假设代码保存在变量code中
    response=code_file_editor.execute_stream(f'''
    把代码保存到/home/guci/myModule/AiResearch/math1.py

    # 代码
    {code}
                                            ''')
    result=None
    for chunk in response:
        result=chunk
        print(chunk,end='',flush=True)
        
    print(result.return_value)
    """
    
    instruction=f'''
    请把代码保存到/home/guci/myModule/AiResearch/message_compress.py
    # 代码
    {code}
    '''
    response=code_file_editor.execute_stream(instruction)
    result=None
    for chunk in response:
        result=chunk
        print(chunk,end='',flush=True)
        
# ====== 测试和示例代码 ======

if __name__ == "__main__":
    # 测试代码：DeepSeek Prover 模型
    from langchain_openai import ChatOpenAI
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    llm_prover_openrouter = ChatOpenAI(
        temperature=0,
        model="deepseek/deepseek-prover-v2", 
        base_url='https://openrouter.ai/api/v1',
        api_key=os.getenv('OPENROUTER_API_KEY'),
    )

    x=llm_prover_openrouter.invoke("扩散模型架构是图灵完备的吗？")
    print(x.content)
    
    x=llm_prover_openrouter.invoke("请证明1+1=2，只允许使用纯逻辑")
    print(x.content)
    
    x=llm_prover_openrouter.invoke("图灵完备意味着能实现任意智能吗？")
    print(x.content)

    x=llm_prover_openrouter.invoke("请用transformer架构实现一个通用图灵机，它能够模拟任意图灵机。代码注释请用中文。")
    print(x.content)

    from pythonTask import llm_deepseek_r1
    x=llm_deepseek_r1.invoke("请用transformer架构实现一个通用图灵机，它能够模拟任意图灵机。单元测试中模拟一个简单的图灵机。代码注释请用中文。")
    print(x.content)

if __name__ == "__main__":
    llm=llm_deepseek
    coder = Agent(llm=llm)
    code_file_editor = Agent(llm=llm)
    code_file_editor.loadKnowledge('''
    ## 编程任务示例代码
    import aider_demo.aider_programming_demo
    instruction = f"保存代码到{file_name}\n#代码\n{code}" 
    edit_file_names=[{file_name}] # 要编辑的文件列表
    read_only_files=[] # 只读文件列表，只读文件不会被修改，是要编辑的文件依赖的文件
    result=aider_demo.aider_programming_demo.programming(instruction,edit_file_names,read_only_files) # 执行编程任务
    print(result) # 打印编程任务结果

    ## 如果指令是编写或修改或保存python文件，优先使用aider_demo.aider_programming_demo.programming函数执行编程任务修改python文件。如果programming函数失败，直接使用python代码修改文件。
                                ''')
    task_executer=Agent(llm=llm)
    
#%%
if __name__ == "__main__":
    response=coder.execute_stream('''
    写一个函数，计算斐波那契数列的第n个数.
    
    ''')
    result:Result=None
    for chunk in response:
        result=chunk
        print(chunk,end='',flush=True)
            
#%%
if __name__ == "__main__":
    response=code_file_editor.execute_stream(f'''
    把代码保存到/home/guci/myModule/AiResearch/hello_world.py

    # 代码
    {result.code}
                                                ''')
    result=None
    for chunk in response:
        result=chunk
        print(chunk,end='',flush=True)

#%%
if __name__ == "__main__":
    response=task_executer.execute_stream(f'''
    运行/home/guci/myModule/AiResearch/hello_world.py，判断测试是否通过
    ''')
    result=None
    for chunk in response:
        result=chunk
        print(chunk,end='',flush=True)
        
#%%
if __name__ == "__main__":
    print(result.return_value)
#%%
# 设置代理服务器环境变量
import os

os.environ['https_proxy'] = 'socks5://127.0.0.1:7890'
os.environ['all_proxy'] = 'socks5://127.0.0.1:7890'

#%%
# 取消代理服务器环境变量设置
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None) 
os.environ.pop('all_proxy', None)


if __name__ == "__main__":
    # 设置代理服务器环境变量
    import os
    # os.environ['http_proxy'] = 'http://127.0.0.1:7890'
    # os.environ['https_proxy'] = 'http://127.0.0.1:7890'
    # os.environ['all_proxy'] = 'socks5://127.0.0.1:7890'

    # 示例1：自主规划模式（默认）
    from pythonTask import llm_llama_4_maverick_openrouter, llm_deepseek
    llm = llm_deepseek

    # 创建自主规划模式的多步骤智能体
    multi_agent_autonomous = MultiStepAgent_v2(llm=llm, use_autonomous_planning=True)
    coder_agent = Agent(llm=llm)
    multi_agent_autonomous.register_agent(
        name="coder",
        instance=coder_agent
    )

    # 自主规划模式 - AI会自主分解任务
    print("=== 自主规划模式示例 ===")
    main_instruction = "请用python写一个hello world程序"
    multi_agent_autonomous.execute_multi_step(main_instruction)



#%%
if __name__ == "__main__":
    from pythonTask import llm_gemini_2_5_pro_preview_05_06_google,llm_gemini_2_5_pro_preview_06_05_google,llm_deepseek,llm_claude_37_sonnet,llm_deepseek_r1
    
    # llm=llm_gemini_2_5_pro_preview_05_06_google

    # llm=llm_gemini_2_5_pro_preview_06_05_google
    llm=llm_deepseek
    # 创建 MultiStepAgent_v2 实例，使用工作流风格的提示词模板
    workflow_agent = MultiStepAgent_v2(
        llm=llm,
        use_autonomous_planning=False
        # planning_prompt_template=workflow_prompt_template
    )

    # 注册智能体
    coder_agent = Agent(llm=llm)
    coder_agent.loadKnowledge('''
                            保存代码到文件的时候，代码字符串应该使用三个双引号。代码内部的引号应该使用转义字符，以避免编译错误。
                            ''')
    coder_agent.api_specification='''
    通用编程智能体,擅长编写python代码
    '''
    workflow_agent.register_agent(
        name="coder",
        instance=coder_agent
    )

    test_agent = Agent(llm=llm)
    test_agent.api_specification='''
    软件测试智能体,擅长运行和测试python代码
    '''
    workflow_agent.register_agent(
        name="tester",
        instance=test_agent
    )

    # 执行任务
    result = workflow_agent.execute_multi_step("""
    1. coder: 实现一个简单的计算器类，包含加减乘除功能和完整单元测试
    2. coder: 把代码保存到simple_calculator.py
    3. tester: 运行simple_calculator.py，获得输出结果。
    4. decision_maker: 分析输出结果，测试通过则完成工作流，测试失败则生成修复任务并循环回到步骤3
    """)

# %%


# %%