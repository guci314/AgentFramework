#!/usr/bin/env python3
"""
Visual Debugger 认知循环演示 - 强制使用认知循环以显示状态分析和本我评估
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time

# 设置代理环境变量
os.environ["http_proxy"] = "http://127.0.0.1:7890"
os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cognitive_debugger import CognitiveDebugger, StepType
from embodied_cognitive_workflow import CognitiveAgent
from python_core import Agent
from llm_lazy import get_model

class CycleDebuggerGUI:
    """通用的认知调试器GUI"""
    
    def __init__(self, cognitive_agent=None):
        self.root = tk.Tk()
        self.root.title("认知调试器 - Visual Debugger")
        self.root.geometry("1200x800")
        
        self.debugger = None
        self.cognitive_agent = cognitive_agent  # 可以传入外部创建的CognitiveAgent
        self.is_running = False
        self.step_count = 0
        self.current_step_result = None  # 当前选中的步骤结果
        
        self._create_gui()
        
    def _create_gui(self):
        """创建GUI界面"""
        # 顶部控制区
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 配置显示区
        config_label = tk.Label(control_frame, text="配置:")
        config_label.pack(side=tk.LEFT)
        
        self.config_text = tk.Label(control_frame, text="未配置", fg="red")
        self.config_text.pack(side=tk.LEFT, padx=5)
        
        # 配置按钮
        self.btn_config = tk.Button(control_frame, text="配置Agent", command=self._show_config_dialog)
        self.btn_config.pack(side=tk.LEFT, padx=5)
        
        # 分隔符
        tk.Label(control_frame, text="|").pack(side=tk.LEFT, padx=5)
        
        # 控制按钮
        self.btn_start = tk.Button(control_frame, text="开始", command=self._start_debug, bg="green", fg="white")
        self.btn_start.pack(side=tk.LEFT, padx=2)
        
        self.btn_step = tk.Button(control_frame, text="单步", command=self._step_debug, state=tk.DISABLED)
        self.btn_step.pack(side=tk.LEFT, padx=2)
        
        self.btn_auto = tk.Button(control_frame, text="自动执行", command=self._auto_run, state=tk.DISABLED)
        self.btn_auto.pack(side=tk.LEFT, padx=2)
        
        self.btn_stop = tk.Button(control_frame, text="停止", command=self._stop_debug, state=tk.DISABLED, bg="red", fg="white")
        self.btn_stop.pack(side=tk.LEFT, padx=2)
        
        # 任务输入区域（放在控制按钮下方）
        task_frame = tk.Frame(self.root)
        task_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(task_frame, text="任务:").pack(side=tk.LEFT)
        
        # 创建任务输入框架，包含文本框和滚动条
        task_text_frame = tk.Frame(task_frame)
        task_text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 多行文本输入框
        self.task_text = tk.Text(task_text_frame, height=3, wrap=tk.WORD)
        self.task_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.task_text.insert("1.0", "输入您的任务...")
        
        # 为任务文本框添加滚动条
        task_scrollbar = tk.Scrollbar(task_text_frame, command=self.task_text.yview)
        task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_text.config(yscrollcommand=task_scrollbar.set)
        
        # 绑定点击事件清除默认文本
        self.task_text.bind("<FocusIn>", self._on_task_focus_in)
        self.task_text.bind("<FocusOut>", self._on_task_focus_out)
        
        # 主分割窗口
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧：步骤列表
        left_frame = ttk.LabelFrame(main_paned, text="执行步骤", padding=5)
        main_paned.add(left_frame, weight=1)
        
        self.step_listbox = tk.Listbox(left_frame)
        self.step_listbox.pack(fill=tk.BOTH, expand=True)
        self.step_listbox.bind('<<ListboxSelect>>', self._on_step_select)
        
        # 保存步骤结果用于后续显示
        self.step_results = []
        
        # 右侧：使用Notebook组件显示不同信息
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)
        
        # 创建Notebook
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: 工作流状态
        state_frame = ttk.Frame(self.notebook)
        self.notebook.add(state_frame, text="工作流状态")
        self.state_text = scrolledtext.ScrolledText(state_frame, height=20, wrap=tk.WORD)
        self.state_text.pack(fill=tk.BOTH, expand=True)
        
        # Tab 2: 步骤输入/输出
        io_frame = ttk.Frame(self.notebook)
        self.notebook.add(io_frame, text="步骤输入/输出")
        
        # 分割输入输出显示
        io_paned = ttk.PanedWindow(io_frame, orient=tk.VERTICAL)
        io_paned.pack(fill=tk.BOTH, expand=True)
        
        # 输入显示
        input_frame = ttk.LabelFrame(io_paned, text="输入", padding=5)
        io_paned.add(input_frame, weight=1)
        self.input_text = scrolledtext.ScrolledText(input_frame, height=10, wrap=tk.WORD)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
        # 输出显示
        output_frame = ttk.LabelFrame(io_paned, text="输出", padding=5)
        io_paned.add(output_frame, weight=1)
        self.output_text = scrolledtext.ScrolledText(output_frame, height=10, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # 底部状态栏
        self.status_bar = tk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def _start_debug(self):
        """开始调试"""
        task = self.task_text.get("1.0", "end-1c").strip()
        if not task or task == "输入您的任务...":
            tk.messagebox.showwarning("警告", "请输入任务")
            return
        
        # 检查是否已配置认知智能体
        if not self.cognitive_agent:
            tk.messagebox.showerror("错误", "请先配置Agent")
            return
        
        # 创建调试器
        self.debugger = CognitiveDebugger(self.cognitive_agent)
        self.debugger.start_debug(task)
        
        # 重置界面
        self.step_count = 0
        self.step_results = []
        self.step_listbox.delete(0, tk.END)
        self.state_text.delete(1.0, tk.END)
        self.input_text.delete(1.0, tk.END)
        self.output_text.delete(1.0, tk.END)
        
        # 更新按钮状态
        self.btn_start.config(state=tk.DISABLED)
        self.btn_step.config(state=tk.NORMAL)
        self.btn_auto.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.NORMAL)
        
        self._update_status("调试已启动")
        self._update_state()
        
    def _step_debug(self):
        """单步执行"""
        if not self.debugger:
            return
        
        # 在新线程中执行，避免阻塞GUI
        def execute():
            result = self.debugger.run_one_step()
            if result:
                self.step_count += 1
                
                # 在主线程中更新GUI
                self.root.after(0, lambda: self._add_step(result))
                self.root.after(0, self._update_state)
                
                if self.debugger.debug_state.is_finished:
                    self.root.after(0, self._on_finished)
        
        threading.Thread(target=execute, daemon=True).start()
        
    def _auto_run(self):
        """自动执行到完成"""
        if not self.debugger:
            return
        
        self.is_running = True
        self.btn_auto.config(state=tk.DISABLED)
        
        def auto_execute():
            while not self.debugger.debug_state.is_finished and self.is_running:
                result = self.debugger.run_one_step()
                if result:
                    self.step_count += 1
                    
                    # 在主线程中更新GUI
                    self.root.after(0, lambda r=result: self._add_step(r))
                    self.root.after(0, self._update_state)
                    
                    # 稍微延迟，让用户看到过程
                    time.sleep(0.3)
                else:
                    break
            
            if self.debugger.debug_state.is_finished:
                self.root.after(0, self._on_finished)
            else:
                self.root.after(0, lambda: self.btn_auto.config(state=tk.NORMAL))
        
        threading.Thread(target=auto_execute, daemon=True).start()
        
    def _stop_debug(self):
        """停止调试"""
        self.is_running = False
        self.debugger = None
        
        self.btn_start.config(state=tk.NORMAL)
        self.btn_step.config(state=tk.DISABLED)
        self.btn_auto.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.DISABLED)
        
        self._update_status("调试已停止")
        
    def _add_step(self, result):
        """添加步骤到列表"""
        step_info = f"{self.step_count}. {result.step_type.value} - {result.agent_layer}"
        
        # 添加执行时间
        if hasattr(result, 'execution_time'):
            step_info += f" ({result.execution_time:.3f}s)"
            
        self.step_listbox.insert(tk.END, step_info)
        self.step_listbox.see(tk.END)
        
        # 保存步骤结果
        self.step_results.append(result)
        
        # 根据步骤类型设置颜色
        color_map = {
            StepType.STATE_ANALYSIS: "blue",
            StepType.DECISION_MAKING: "purple",
            StepType.ID_EVALUATION: "orange",
            StepType.BODY_EXECUTION: "green",
            StepType.META_COGNITION_PRE: "brown",
            StepType.META_COGNITION_POST: "brown"
        }
        
        if result.step_type in color_map:
            self.step_listbox.itemconfig(tk.END, fg=color_map[result.step_type])
        elif hasattr(result, 'error') and result.error:
            self.step_listbox.itemconfig(tk.END, fg="red")
            
    def _update_state(self):
        """更新状态显示"""
        if not self.debugger:
            return
        
        self.state_text.delete(1.0, tk.END)
        
        debug_state = self.debugger.debug_state
        
        # 获取当前信息
        current_step = debug_state.current_step if hasattr(debug_state, 'current_step') else StepType.INIT
        is_finished = debug_state.is_finished
        
        # 获取工作流上下文
        ctx = debug_state.workflow_context
        if ctx:
            goal_achieved = ctx.goal_achieved
            current_state = ctx.current_state if ctx.current_state else "（尚未分析）"
            id_eval = ctx.id_evaluation if ctx.id_evaluation else "（尚未评估）"
            
            # 显示当前循环
            current_cycle = ctx.current_cycle
            
            # 获取历史记录
            history = ctx.history[-3:] if len(ctx.history) > 0 else []
            history_text = "\n".join(f"  - {h}" for h in history) if history else "  无"
        else:
            goal_achieved = False
            current_state = "无上下文"
            id_eval = "无上下文"
            current_cycle = 0
            history_text = "  无"
        
        # 构建状态信息
        state_info = f"""=== 调试状态 ===
当前步骤: {current_step.value}
已执行步骤: {self.step_count}
当前循环: 第 {current_cycle} 轮
调试状态: {'已完成' if is_finished else '进行中'}
目标达成: {'是' if goal_achieved else '否'}

=== 当前状态分析 (Ego) ===
{current_state}

=== 本我评估 (Id) ===
{id_eval}

=== 最近执行历史 ===
{history_text}

=== 最终结果 ===
{self._get_final_result()}
"""
        
        self.state_text.insert(tk.END, state_info)
        
        # 确保GUI更新
        self.root.update()
        
    def _on_finished(self):
        """执行完成时的处理"""
        self.is_running = False
        self.btn_auto.config(state=tk.DISABLED)
        self.btn_step.config(state=tk.DISABLED)
        self._update_status("执行完成")
        
        # 获取并显示最终结果
        final_result = self._get_final_result()
        if final_result != "执行中...":
            self._update_status(f"执行完成 - {final_result[:50]}...")
            
    def _get_final_result(self):
        """获取最终执行结果"""
        if not self.debugger or not self.debugger.debug_state.is_finished:
            return "执行中..."
        
        # 从步骤历史中查找最终化步骤的结果
        for step in reversed(self.debugger.debug_state.step_history):
            if step.step_type == StepType.FINALIZE:
                # 从debug_info中获取final_result
                if 'final_result' in step.debug_info:
                    final_result = step.debug_info['final_result']
                    if isinstance(final_result, dict) and 'return_value' in final_result:
                        return final_result['return_value'] or "认知循环执行完成"
                    return str(final_result)
        
        # 检查是否有BODY_EXECUTION步骤的结果
        for step in reversed(self.debugger.debug_state.step_history):
            if step.step_type == StepType.BODY_EXECUTION:
                if 'execution_result' in step.debug_info:
                    exec_result = step.debug_info['execution_result']
                    if isinstance(exec_result, dict) and exec_result.get('success'):
                        return exec_result.get('stdout', '执行成功')
        
        return "执行完成（无详细结果）"
    
    def _update_status(self, message):
        """更新状态栏"""
        self.status_bar.config(text=f"{message} | 步骤数: {self.step_count}")
    
    def _on_step_select(self, event):
        """当选择步骤时显示其输入输出"""
        selection = self.step_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index >= len(self.step_results):
            return
        
        # 获取选中的步骤结果
        result = self.step_results[index]
        
        # 清空显示
        self.input_text.delete(1.0, tk.END)
        self.output_text.delete(1.0, tk.END)
        
        # 显示输入信息
        input_info = self._format_step_input(result)
        self.input_text.insert(tk.END, input_info)
        
        # 显示输出信息
        output_info = self._format_step_output(result)
        self.output_text.insert(tk.END, output_info)
        
        # 切换到输入/输出标签页
        self.notebook.select(1)
    
    def _format_step_input(self, result):
        """格式化步骤输入信息"""
        info = f"=== 步骤类型: {result.step_type.value} ===\n"
        info += f"执行层级: {result.agent_layer}\n"
        info += f"执行时间: {result.execution_time:.3f}秒\n\n"
        
        # 根据步骤类型显示不同的输入信息
        if result.step_type == StepType.STATE_ANALYSIS:
            info += "=== 输入数据 ===\n"
            if hasattr(result, 'debug_info'):
                debug_info = result.debug_info
                
                # 显示当前上下文
                if 'context' in debug_info:
                    info += f"当前上下文:\n{debug_info['context']}\n"
                
                # 显示循环次数
                if 'cycle' in debug_info:
                    info += f"\n当前循环: 第 {debug_info['cycle']} 轮\n"
                
                # 显示其他输入信息
                if 'input' in debug_info:
                    info += f"\n其他输入:\n{debug_info['input']}\n"
            else:
                info += "任务: 分析当前状态\n"
                
        elif result.step_type == StepType.DECISION_MAKING:
            info += "=== 输入数据 ===\n"
            if hasattr(result, 'debug_info') and 'state_analysis' in result.debug_info:
                info += f"状态分析结果:\n{result.debug_info['state_analysis']}\n"
            if hasattr(result, 'debug_info') and 'available_agents' in result.debug_info:
                agents = result.debug_info['available_agents']
                if agents:
                    info += f"\n可用Agents:\n"
                    for agent in agents:
                        info += f"  - {agent}\n"
                        
        elif result.step_type == StepType.ID_EVALUATION:
            info += "=== 输入数据 ===\n"
            if hasattr(result, 'debug_info'):
                debug_info = result.debug_info
                
                # 显示评估请求
                if 'evaluation_request' in debug_info:
                    info += f"评估请求:\n{debug_info['evaluation_request']}\n"
                
                # 显示当前状态（如果没有评估请求）
                elif 'context' in debug_info:
                    info += f"当前上下文:\n{debug_info['context']}\n"
                
                
        elif result.step_type == StepType.BODY_EXECUTION:
            info += "=== 输入数据 ===\n"
            if hasattr(result, 'debug_info'):
                debug_info = result.debug_info
                
                # 显示执行者
                if 'selected_agent' in debug_info:
                    info += f"执行Agent: {debug_info['selected_agent']}\n"
                elif 'agent_name' in debug_info:
                    info += f"执行Agent: {debug_info['agent_name']}\n"
                
                # 显示执行指令
                if 'instruction' in debug_info:
                    info += f"\n执行指令:\n{debug_info['instruction']}\n"
                elif 'operation' in debug_info:
                    info += f"\n执行指令:\n{debug_info['operation']}\n"
                
                # 显示执行模式
                if 'execution_mode' in debug_info:
                    info += f"\n执行模式: {debug_info['execution_mode']}\n"
                
        else:
            if hasattr(result, 'debug_info') and 'input' in result.debug_info:
                info += f"=== 输入数据 ===\n{result.debug_info['input']}\n"
            else:
                info += "=== 输入数据 ===\n（无特定输入）\n"
                
        return info
    
    def _format_step_output(self, result):
        """格式化步骤输出信息"""
        info = f"=== 步骤输出: {result.step_type.value} ===\n\n"
        
        # 根据步骤类型显示不同的输出信息
        if result.step_type == StepType.STATE_ANALYSIS:
            if hasattr(result, 'debug_info'):
                debug_info = result.debug_info
                
                # 显示分析结果
                if 'analysis_result' in debug_info:
                    info += f"状态分析结果:\n{debug_info['analysis_result']}\n"
                elif 'state_analysis' in debug_info:
                    info += f"状态分析结果:\n{debug_info['state_analysis']}\n"
                
                # 显示循环信息
                if 'cycle' in debug_info:
                    info += f"\n当前循环: 第 {debug_info['cycle']} 轮\n"
                
                # 显示调用的方法
                if 'agent_method' in debug_info:
                    info += f"\n调用方法: {debug_info['agent_method']}\n"
            else:
                info += "（无状态分析结果）\n"
                
        elif result.step_type == StepType.DECISION_MAKING:
            if hasattr(result, 'debug_info'):
                debug_info = result.debug_info
                
                # 显示决策类型
                if 'decision_type' in debug_info:
                    info += f"决策类型: {debug_info['decision_type']}\n"
                
                # 显示执行指令
                if 'instruction' in debug_info:
                    info += f"\n执行指令:\n{debug_info['instruction']}\n"
                
                # 显示选择的Agent
                if 'selected_agent' in debug_info:
                    info += f"\n选定执行者: {debug_info['selected_agent']}\n"
                
                # 显示可用的Agents
                if 'available_agents' in debug_info:
                    info += f"\n可用执行者: {', '.join(debug_info['available_agents'])}\n"
                
                # 显示决策详情（如果有）
                if 'decision' in debug_info:
                    decision = debug_info['decision']
                    info += f"\n决策详情:\n"
                    info += f"  类型: {decision.get('type', '未知')}\n"
                    info += f"  内容: {decision.get('content', '无')}\n"
                    if 'target_agent' in decision:
                        info += f"  目标执行者: {decision['target_agent']}\n"
                    
        elif result.step_type == StepType.ID_EVALUATION:
            if hasattr(result, 'debug_info'):
                debug_info = result.debug_info
                
                # 显示评估结果
                if 'goal_achieved' in debug_info:
                    info += f"评估结果: {'目标已达成' if debug_info['goal_achieved'] else '目标未达成'}\n"
                
                # 显示评估JSON
                if 'evaluation_json' in debug_info:
                    info += f"\n原始评估数据:\n{debug_info['evaluation_json']}\n"
                
                # 显示评估结果文本
                if 'evaluation_result' in debug_info:
                    info += f"\n评估详情:\n{debug_info['evaluation_result']}\n"
                
                    
        elif result.step_type == StepType.BODY_EXECUTION:
            if hasattr(result, 'debug_info'):
                debug_info = result.debug_info
                
                # 显示执行者
                if 'selected_agent' in debug_info:
                    info += f"执行者: {debug_info['selected_agent']}\n"
                
                # 显示执行指令
                if 'instruction' in debug_info:
                    info += f"\n执行指令:\n{debug_info['instruction']}\n"
                
                # 显示执行结果
                if 'execution_result' in debug_info:
                    exec_result = debug_info['execution_result']
                    if isinstance(exec_result, dict):
                        info += f"\n执行状态: {'成功' if exec_result.get('success') else '失败'}\n"
                        if 'stdout' in exec_result:
                            info += f"\n执行输出:\n{exec_result['stdout']}\n"
                        if 'stderr' in exec_result and exec_result['stderr']:
                            info += f"\n错误输出:\n{exec_result['stderr']}\n"
                        if 'return_value' in exec_result:
                            info += f"\n返回值:\n{exec_result['return_value']}\n"
                    else:
                        info += f"\n执行结果:\n{exec_result}\n"
                    
        else:
            # 通用输出显示
            if hasattr(result, 'debug_info'):
                for key, value in result.debug_info.items():
                    if key not in ['input', 'task', 'available_agents', 'operation', 'agent_name']:
                        info += f"{key}: {value}\n"
                        
        # 显示错误信息
        if hasattr(result, 'error') and result.error:
            info += f"\n=== 错误信息 ===\n{result.error}\n"
            
        return info
    
    def _show_config_dialog(self):
        """显示配置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("配置认知智能体")
        dialog.geometry("600x500")
        
        # LLM选择
        tk.Label(dialog, text="选择LLM模型:").pack(pady=5)
        llm_var = tk.StringVar(value="gemini_2_5_flash")
        llm_options = ["gemini_2_5_flash", "gemini_2_5_pro", "deepseek_chat", "deepseek_v3", "qwen_qwq_32b"]
        llm_menu = ttk.Combobox(dialog, textvariable=llm_var, values=llm_options, state="readonly")
        llm_menu.pack(pady=5)
        
        # Agent列表
        tk.Label(dialog, text="配置Agents:").pack(pady=10)
        
        # Agent配置框架
        agents_frame = tk.Frame(dialog)
        agents_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Agent列表
        agent_configs = []
        
        def add_agent():
            """添加新的Agent配置"""
            agent_frame = tk.Frame(agents_frame)
            agent_frame.pack(fill=tk.X, pady=5)
            
            # Agent名称
            tk.Label(agent_frame, text="名称:").pack(side=tk.LEFT)
            name_entry = tk.Entry(agent_frame, width=20)
            name_entry.pack(side=tk.LEFT, padx=5)
            
            # API规格
            tk.Label(agent_frame, text="能力:").pack(side=tk.LEFT)
            api_entry = tk.Entry(agent_frame, width=40)
            api_entry.pack(side=tk.LEFT, padx=5)
            
            # 删除按钮
            def remove_agent():
                agent_configs.remove((name_entry, api_entry))
                agent_frame.destroy()
            
            tk.Button(agent_frame, text="删除", command=remove_agent).pack(side=tk.LEFT, padx=5)
            
            agent_configs.append((name_entry, api_entry))
        
        # 添加默认Agent
        add_agent()
        agent_configs[0][0].insert(0, "通用助手")
        agent_configs[0][1].insert(0, "通用任务执行能力")
        
        # 添加Agent按钮
        tk.Button(dialog, text="+ 添加Agent", command=add_agent).pack(pady=5)
        
        # 高级选项
        tk.Label(dialog, text="高级选项:").pack(pady=10)
        
        # 最大循环次数
        cycles_frame = tk.Frame(dialog)
        cycles_frame.pack()
        tk.Label(cycles_frame, text="最大循环次数:").pack(side=tk.LEFT)
        cycles_var = tk.IntVar(value=10)
        tk.Spinbox(cycles_frame, from_=1, to=50, textvariable=cycles_var, width=10).pack(side=tk.LEFT)
        
        # 认知模式
        mode_frame = tk.Frame(dialog)
        mode_frame.pack(pady=5)
        tk.Label(mode_frame, text="认知模式:").pack(side=tk.LEFT)
        mode_var = tk.StringVar(value="auto")
        tk.Radiobutton(mode_frame, text="自动", variable=mode_var, value="auto").pack(side=tk.LEFT)
        tk.Radiobutton(mode_frame, text="强制循环", variable=mode_var, value="force").pack(side=tk.LEFT)
        
        # 元认知
        meta_var = tk.BooleanVar(value=False)
        tk.Checkbutton(dialog, text="启用元认知", variable=meta_var).pack(pady=5)
        
        # 确认和取消按钮
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def confirm_config():
            """确认配置"""
            # 获取LLM
            llm = get_model(llm_var.get())
            
            # 创建Agents
            agents = []
            for name_entry, api_entry in agent_configs:
                name = name_entry.get().strip()
                api = api_entry.get().strip()
                if name and api:
                    agent = Agent(llm=llm)
                    agent.name = name
                    agent.set_api_specification(api)
                    agents.append(agent)
            
            if not agents:
                messagebox.showerror("错误", "至少需要配置一个Agent")
                return
            
            # 根据模式创建CognitiveAgent
            if mode_var.get() == "force":
                # 强制认知循环
                class ForceCycleCognitiveAgent(CognitiveAgent):
                    def _can_handle_directly(self, instruction: str) -> bool:
                        return False
                
                self.cognitive_agent = ForceCycleCognitiveAgent(
                    llm=llm,
                    agents=agents,
                    max_cycles=cycles_var.get(),
                    verbose=False,
                    enable_meta_cognition=meta_var.get()
                )
            else:
                # 正常模式
                self.cognitive_agent = CognitiveAgent(
                    llm=llm,
                    agents=agents,
                    max_cycles=cycles_var.get(),
                    verbose=False,
                    enable_meta_cognition=meta_var.get()
                )
            
            # 更新配置显示
            agent_names = ", ".join([a.name for a in agents])
            config_info = f"{llm_var.get()} | {len(agents)}个Agent ({agent_names[:30]}...)"
            self.config_text.config(text=config_info, fg="green")
            
            dialog.destroy()
        
        tk.Button(button_frame, text="确认", command=confirm_config).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        
    def _on_task_focus_in(self, event):
        """任务文本框获得焦点时清除默认文本"""
        if self.task_text.get("1.0", "end-1c") == "输入您的任务...":
            self.task_text.delete("1.0", "end")
    
    def _on_task_focus_out(self, event):
        """任务文本框失去焦点时恢复默认文本"""
        if not self.task_text.get("1.0", "end-1c").strip():
            self.task_text.insert("1.0", "输入您的任务...")
    
    def run(self):
        """运行GUI"""
        # 如果已经传入了cognitive_agent，更新配置显示
        if self.cognitive_agent:
            agents = getattr(self.cognitive_agent, 'agents', [])
            if agents:
                agent_names = ", ".join([a.name for a in agents])
                self.config_text.config(text=f"外部配置 | {len(agents)}个Agent", fg="green")
        
        self.root.mainloop()


def main():
    """主程序"""
    print("🚀 Visual Debugger - 通用认知调试器")
    print("=" * 60)
    
    import argparse
    parser = argparse.ArgumentParser(description="认知调试器")
    parser.add_argument("--mode", choices=["gui", "example"], default="gui",
                        help="运行模式: gui(配置界面) 或 example(示例)")
    args = parser.parse_args()
    
    if args.mode == "example":
        # 示例模式：创建预配置的CognitiveAgent
        print("运行示例模式...")
        print("创建示例CognitiveAgent：")
        print("- LLM: gemini_2_5_flash")
        print("- Agents: Python文件专家, 数学专家")
        print("-" * 60)
        
        # 创建示例Agent
        llm = get_model("gemini_2_5_flash")
        
        # Python文件专家
        file_agent = Agent(llm=llm)
        file_agent.name = "Python文件专家"
        file_agent.set_api_specification("专精Python代码创建、文件写入、单元测试编写和运行")
        
        # 数学专家
        math_agent = Agent(llm=llm)
        math_agent.name = "数学专家"
        math_agent.set_api_specification("专精数学计算、统计分析、数值处理")
        
        # 创建认知智能体
        cognitive_agent = CognitiveAgent(
            llm=llm,
            agents=[file_agent, math_agent],
            max_cycles=10,
            verbose=False,
            enable_meta_cognition=False
        )
        
        # 创建GUI并传入配置好的agent
        gui = CycleDebuggerGUI(cognitive_agent)
        
        # 设置示例任务
        gui.task_text.delete("1.0", tk.END)
        gui.task_text.insert("1.0", "创建一个计算1到100之和的Python脚本，并写单元测试验证结果")
        
    else:
        # GUI模式：让用户通过界面配置
        print("运行GUI配置模式...")
        print("请通过界面配置您的Agent")
        print("-" * 60)
        gui = CycleDebuggerGUI()
    
    gui.run()
    
    # 清理测试文件
    cleanup_files = ["hello_world.py", "test_hello_world.py", "sum_calculator.py", "test_sum_calculator.py"]
    for file in cleanup_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"✅ 测试文件 {file} 已清理")
    
    print("\n✅ 调试器已关闭")


if __name__ == "__main__":
    main()