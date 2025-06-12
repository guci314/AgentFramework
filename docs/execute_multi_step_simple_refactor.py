"""
execute_multi_step 方法简化重构示例
将300行的复杂方法拆分为多个职责单一的方法
"""

class MultiStepAgent_v2(Agent):
    
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
                self._execute_workflow_iteration(context, interactive)
            except Exception as e:
                logger.error(f"工作流迭代失败: {e}")
                self._handle_workflow_error(context, e)
                break
        
        return self._generate_execution_summary(context)
    
    def _initialize_execution_context(self, main_instruction: str) -> Dict[str, Any]:
        """初始化执行上下文"""
        # 存储原始目标和任务历史
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
            'context': {"original_goal": main_instruction}
        }
    
    def _should_continue_execution(self, context: Dict[str, Any]) -> bool:
        """判断是否应该继续执行"""
        max_workflow_iterations = 50
        return (context['retries'] <= self.max_retries and 
                context['workflow_iterations'] < max_workflow_iterations)
    
    def _execute_workflow_iteration(self, context: Dict[str, Any], interactive: bool) -> None:
        """执行一个工作流迭代"""
        context['workflow_iterations'] += 1
        context['plan'] = self.get_plan()
        
        # 选择下一个可执行步骤
        next_step_info = self.select_next_executable_step(context['plan'])
        
        if not next_step_info:
            # 没有可执行步骤，进行决策
            self._handle_no_executable_steps(context)
            return
        
        # 执行选定的步骤
        current_idx, current_step = next_step_info
        execution_result = self._execute_single_workflow_step(
            current_idx, current_step, context
        )
        
        if execution_result['should_break']:
            return
            
        # 交互模式处理
        if interactive and self._check_user_interrupt():
            context['summary'] += "\n用户请求退出。"
            return
    
    def _handle_no_executable_steps(self, context: Dict[str, Any]) -> None:
        """处理没有可执行步骤的情况"""
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
        self._process_decision(decision, context)
    
    def _execute_single_workflow_step(self, current_idx: int, current_step: Dict, 
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个工作流步骤"""
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
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """处理步骤执行成功的情况"""
        self.update_step_status(current_idx, "completed", exec_result)
        
        # 执行成功后进行决策
        decision = self.make_decision(
            current_result=exec_result,
            task_history=context['task_history'],
            context=context['context']
        )
        
        print(f"\n决策结果: {decision['action']}")
        print(f"原因: {decision['reason']}")
        
        # 处理决策结果
        return self._process_success_decision(decision, context)
    
    def _handle_step_failure(self, current_idx: int, current_step: Dict, 
                           exec_result: Result, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理步骤执行失败的情况"""
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
    
    def _process_decision(self, decision: Dict[str, Any], context: Dict[str, Any]) -> None:
        """处理决策结果 - 通用版本"""
        action = decision['action']
        
        if action == 'complete':
            context['summary'] += "\n全部步骤执行完成。"
            self._clear_failure_records()
        elif action == 'generate_new_task' and decision.get('new_tasks'):
            context['summary'] += "\n添加新任务并继续执行。"
            self._add_new_tasks(decision.get('new_tasks', []))
            context['plan'] = self.get_plan()
        else:
            context['summary'] += f"\n所有步骤已处理，决策为: {action}。"
    
    def _process_success_decision(self, decision: Dict[str, Any], 
                                context: Dict[str, Any]) -> Dict[str, Any]:
        """处理成功后的决策"""
        action = decision['action']
        
        if action == 'complete':
            context['summary'] += "\n决策为完成执行。"
            self._clear_failure_records()
            return {'should_break': True}
            
        elif action == 'continue':
            context['summary'] += "\n继续执行下一个步骤。"
            return {'should_break': False}
            
        elif action == 'generate_new_task':
            return self._handle_generate_new_task_decision(decision, context)
            
        elif action in ['jump_to', 'loop_back']:
            return self._handle_navigation_decision(decision, context)
            
        elif action == 'generate_fix_task_and_loop':
            return self._handle_fix_task_decision(decision, context)
            
        return {'should_break': False}
    
    def _process_failure_decision(self, decision: Dict[str, Any], context: Dict[str, Any], 
                                current_idx: int) -> Dict[str, Any]:
        """处理失败后的决策"""
        action = decision['action']
        
        if action == 'retry':
            self.update_step_status(current_idx, "pending")
            context['summary'] += "\n将重试当前步骤。"
            return {'should_break': False}
            
        elif action == 'continue':
            context['summary'] += "\n继续执行下一个步骤。"
            return {'should_break': False}
            
        elif action == 'generate_new_task':
            return self._handle_generate_new_task_decision(decision, context)
            
        else:
            # 默认处理：增加重试次数
            return self._handle_retry_logic(context)
    
    def _handle_generate_new_task_decision(self, decision: Dict[str, Any], 
                                         context: Dict[str, Any]) -> Dict[str, Any]:
        """处理生成新任务的决策"""
        new_tasks = decision.get('new_tasks', [])
        if new_tasks:
            self._add_new_tasks(new_tasks)
            context['plan'] = self.get_plan()
            context['summary'] += "\n添加新任务并继续执行。"
        return {'should_break': False}
    
    def _handle_navigation_decision(self, decision: Dict[str, Any], 
                                  context: Dict[str, Any]) -> Dict[str, Any]:
        """处理跳转和循环决策"""
        action = decision['action']
        target_step_id = decision.get('target_step_id')
        
        if not target_step_id:
            logger.warning(f"{action}决策缺少target_step_id")
            return {'should_break': False}
        
        if action == 'jump_to':
            if self.jump_to_step(target_step_id):
                context['summary'] += f"\n跳转到步骤: {target_step_id}"
            
        elif action == 'loop_back':
            if self.loop_back_to_step(target_step_id):
                context['summary'] += f"\n循环回到步骤: {target_step_id}"
            else:
                context['summary'] += "\n循环失败"
        
        return {'should_break': False}
    
    def _handle_fix_task_decision(self, decision: Dict[str, Any], 
                                context: Dict[str, Any]) -> Dict[str, Any]:
        """处理修复任务决策"""
        if self.handle_generate_fix_task_and_loop(decision):
            # 这里需要执行修复任务的逻辑
            return self._execute_fix_task(decision, context)
        else:
            context['summary'] += "\n修复任务生成失败或达到最大重试次数"
            return {'should_break': True}
    
    def _execute_fix_task(self, decision: Dict[str, Any], 
                         context: Dict[str, Any]) -> Dict[str, Any]:
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
        
        return {'should_break': False}
    
    def _handle_retry_logic(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理重试逻辑"""
        # 记录失败信息
        self._record_failure_information(context)
        
        # 增加重试计数
        context['retries'] += 1
        if context['retries'] <= self.max_retries:
            context['summary'] += f"\n第{context['retries']}次重试。"
            return {'should_break': False}
        else:
            context['summary'] += "\n已达最大重试次数。"
            return {'should_break': True}
    
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