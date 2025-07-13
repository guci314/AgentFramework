# 重构后的 enhancedAgent_v2.py 
# 主要重构了 execute_multi_step 方法，将其拆分为多个小方法

from agent_base import Result, reduce_memory_decorator
from python_core import StatefulExecutor, Agent
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
    重构后的多步骤智能体：execute_multi_step 方法被拆分为多个小方法
    """

    def __init__(
        self,
        llm: BaseChatModel,
        agent_specs: Optional[List[AgentSpecification]] = None,
        max_retries: int = 3,
        thinker_system_message: Optional[str] = None,
        thinker_chat_system_message: Optional[str] = None,
        planning_prompt_template: Optional[str] = None,
        use_autonomous_planning: bool = True,
    ):
        team_system_message = thinker_system_message
        if team_system_message is None:
            team_system_message = team_manager_system_message_no_share_state
        
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
        
        # 初始化工作流状态
        self.workflow_state = WorkflowState()
        self.original_goal = ""
        self.use_autonomous_planning = use_autonomous_planning
        
        # 省略其他初始化代码...

    # ====== 重构后的 execute_multi_step 方法及其辅助方法 ======
    
    @reduce_memory_decorator
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
        exec_result = self.execute_single_step(current_step)
        
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
    
    def _add_new_tasks(self, new_tasks: List[Dict[str, Any]]) -> None:
        """添加新任务到计划"""
        plan = self.get_plan()
        
        for new_task in new_tasks:
            # 确保新任务有必要的字段
            new_task_id = new_task.get('id', f"dynamic_{len(plan)}")
            new_task['id'] = new_task_id
            if 'status' not in new_task:
                new_task['status'] = 'pending'
            plan.append(new_task)
        
        # 更新计划
        self.device.set_variable("current_plan", plan)
        print(f"\n更新执行计划:\n{json.dumps(plan, ensure_ascii=False, indent=2)}\n")
    
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

    # ====== 其他方法保持不变 ======
    # 这里需要包含原文件中的其他方法，如 make_decision, plan_execution 等
    # 为了简洁，这里省略了其他方法的实现
    
    def register_agent(self, name: str, instance: Agent):
        """注册一个新的 Agent。"""
        description = getattr(instance, 'api_specification', f"{name}智能体，通用任务执行者")
        spec = AgentSpecification(name=name, instance=instance, description=description)
        self.agent_specs.append(spec)
        self.device.set_variable(spec.name, spec.instance)
        logger.debug(f"已注册 Agent: {name}")
    
    def get_plan(self):
        """获取当前计划"""
        try:
            return self.device.get_variable("current_plan") or []
        except:
            return []
    
    def update_step_status(self, step_index: int, status: str, result: Optional[Result] = None):
        """更新步骤状态"""
        plan = self.get_plan()
        if 0 <= step_index < len(plan):
            plan[step_index]['status'] = status
            if result:
                plan[step_index]['result'] = result
            self.device.set_variable("current_plan", plan)
    
    # 需要包含原文件中的其他所有方法...
    # 为了演示重构效果，这里只展示核心的重构部分