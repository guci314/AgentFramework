"""
认知调试可视化工具

提供认知工作流的可视化调试界面，包括实时监控、断点管理、步骤跟踪等功能。
"""

import os
import json
import time
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from matplotlib.figure import Figure

# 处理相对导入问题
try:
    from .cognitive_debug_agent import CognitiveDebugAgent, CognitiveStep, CognitiveBreakpoint, BugReport, DebugLevel
except ImportError:
    # 当作为独立模块运行时，使用绝对导入
    from cognitive_debug_agent import CognitiveDebugAgent, CognitiveStep, CognitiveBreakpoint, BugReport, DebugLevel


class CognitiveDebugVisualizer:
    """认知调试可视化器"""
    
    def __init__(self, debug_agent: CognitiveDebugAgent):
        """
        初始化可视化器
        
        Args:
            debug_agent: 认知调试智能体实例
        """
        self.debug_agent = debug_agent
        self.debugger = debug_agent.debugger
        
        # GUI组件
        self.root = None
        self.notebook = None
        self.step_tree = None
        self.breakpoint_tree = None
        self.bug_tree = None
        self.console_text = None
        self.performance_canvas = None
        
        # 状态管理
        self.is_running = False
        self.refresh_thread = None
        self.auto_refresh = True
        self.refresh_interval = 1.0  # 秒
        
        # 数据缓存
        self.cached_steps = []
        self.cached_breakpoints = {}
        self.cached_bugs = []
    
    def create_gui(self):
        """创建GUI界面"""
        self.root = tk.Tk()
        self.root.title("认知调试器 - CognitiveDebugger")
        self.root.geometry("1200x800")
        
        # 创建主菜单
        self._create_menu()
        
        # 创建工具栏
        self._create_toolbar()
        
        # 创建主面板
        self._create_main_panels()
        
        # 启动自动刷新
        self._start_auto_refresh()
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出调试日志", command=self._export_debug_log)
        file_menu.add_command(label="导入断点配置", command=self._import_breakpoints)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 调试菜单
        debug_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="调试", menu=debug_menu)
        debug_menu.add_command(label="开始调试", command=self._start_debugging)
        debug_menu.add_command(label="停止调试", command=self._stop_debugging)
        debug_menu.add_separator()
        debug_menu.add_command(label="清除所有断点", command=self._clear_all_breakpoints)
        debug_menu.add_command(label="清除调试历史", command=self._clear_debug_history)
        
        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="刷新", command=self._refresh_all)
        view_menu.add_checkbutton(label="自动刷新", variable=tk.BooleanVar(value=True))
    
    def _create_toolbar(self):
        """创建工具栏"""
        toolbar_frame = tk.Frame(self.root)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        # 调试控制按钮
        tk.Button(toolbar_frame, text="▶ 开始", command=self._start_debugging).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar_frame, text="⏸ 暂停", command=self._pause_debugging).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar_frame, text="⏹ 停止", command=self._stop_debugging).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar_frame, text="↻ 刷新", command=self._refresh_all).pack(side=tk.LEFT, padx=2)
        
        # 分隔符
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 断点控制
        tk.Button(toolbar_frame, text="+ 添加断点", command=self._add_breakpoint_dialog).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar_frame, text="- 删除断点", command=self._remove_selected_breakpoint).pack(side=tk.LEFT, padx=2)
        
        # 状态显示
        self.status_label = tk.Label(toolbar_frame, text="状态: 空闲", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.RIGHT, padx=5)
    
    def _create_main_panels(self):
        """创建主面板"""
        # 创建笔记本控件
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 认知步骤面板
        self._create_steps_panel()
        
        # 断点管理面板
        self._create_breakpoints_panel()
        
        # Bug报告面板
        self._create_bugs_panel()
        
        # 性能监控面板
        self._create_performance_panel()
        
        # 控制台面板
        self._create_console_panel()
    
    def _create_steps_panel(self):
        """创建认知步骤面板"""
        steps_frame = ttk.Frame(self.notebook)
        self.notebook.add(steps_frame, text="认知步骤")
        
        # 步骤列表
        columns = ("步骤ID", "时间", "层级", "动作", "状态", "执行时间")
        self.step_tree = ttk.Treeview(steps_frame, columns=columns, show="headings")
        
        for col in columns:
            self.step_tree.heading(col, text=col)
            self.step_tree.column(col, width=120)
        
        # 滚动条
        step_scrollbar = ttk.Scrollbar(steps_frame, orient=tk.VERTICAL, command=self.step_tree.yview)
        self.step_tree.configure(yscrollcommand=step_scrollbar.set)
        
        # 布局
        self.step_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        step_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 双击事件
        self.step_tree.bind("<Double-1>", self._on_step_double_click)
    
    def _create_breakpoints_panel(self):
        """创建断点管理面板"""
        bp_frame = ttk.Frame(self.notebook)
        self.notebook.add(bp_frame, text="断点管理")
        
        # 上方控制区
        control_frame = tk.Frame(bp_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(control_frame, text="层级:").pack(side=tk.LEFT)
        self.bp_layer_var = tk.StringVar(value="自我")
        layer_combo = ttk.Combobox(control_frame, textvariable=self.bp_layer_var, 
                                  values=["自我", "本我", "身体", "超我"], state="readonly")
        layer_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Label(control_frame, text="条件:").pack(side=tk.LEFT, padx=(10, 0))
        self.bp_condition_var = tk.StringVar()
        condition_entry = tk.Entry(control_frame, textvariable=self.bp_condition_var, width=30)
        condition_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="添加断点", command=self._add_breakpoint).pack(side=tk.LEFT, padx=5)
        
        # 断点列表
        bp_columns = ("断点ID", "层级", "条件", "状态", "触发次数", "创建时间")
        self.breakpoint_tree = ttk.Treeview(bp_frame, columns=bp_columns, show="headings")
        
        for col in bp_columns:
            self.breakpoint_tree.heading(col, text=col)
            self.breakpoint_tree.column(col, width=150)
        
        # 滚动条
        bp_scrollbar = ttk.Scrollbar(bp_frame, orient=tk.VERTICAL, command=self.breakpoint_tree.yview)
        self.breakpoint_tree.configure(yscrollcommand=bp_scrollbar.set)
        
        # 布局
        self.breakpoint_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        bp_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_bugs_panel(self):
        """创建Bug报告面板"""
        bugs_frame = ttk.Frame(self.notebook)
        self.notebook.add(bugs_frame, text="Bug报告")
        
        # Bug列表
        bug_columns = ("Bug ID", "时间", "严重程度", "描述", "影响层级", "状态")
        self.bug_tree = ttk.Treeview(bugs_frame, columns=bug_columns, show="headings")
        
        for col in bug_columns:
            self.bug_tree.heading(col, text=col)
            self.bug_tree.column(col, width=150)
        
        # 滚动条
        bug_scrollbar = ttk.Scrollbar(bugs_frame, orient=tk.VERTICAL, command=self.bug_tree.yview)
        self.bug_tree.configure(yscrollcommand=bug_scrollbar.set)
        
        # 布局
        self.bug_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        bug_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 双击事件
        self.bug_tree.bind("<Double-1>", self._on_bug_double_click)
    
    def _create_performance_panel(self):
        """创建性能监控面板"""
        perf_frame = ttk.Frame(self.notebook)
        self.notebook.add(perf_frame, text="性能监控")
        
        # 创建matplotlib图表
        fig = Figure(figsize=(12, 6), dpi=100)
        
        # 执行时间趋势图
        self.time_subplot = fig.add_subplot(221)
        self.time_subplot.set_title("执行时间趋势")
        self.time_subplot.set_xlabel("时间")
        self.time_subplot.set_ylabel("执行时间(秒)")
        
        # 成功率图
        self.success_subplot = fig.add_subplot(222)
        self.success_subplot.set_title("成功率统计")
        
        # 层级分布图
        self.layer_subplot = fig.add_subplot(223)
        self.layer_subplot.set_title("层级执行分布")
        
        # Bug严重程度分布
        self.bug_subplot = fig.add_subplot(224)
        self.bug_subplot.set_title("Bug严重程度分布")
        
        # 创建画布
        self.performance_canvas = FigureCanvasTkAgg(fig, perf_frame)
        self.performance_canvas.draw()
        self.performance_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _create_console_panel(self):
        """创建控制台面板"""
        console_frame = ttk.Frame(self.notebook)
        self.notebook.add(console_frame, text="调试控制台")
        
        # 输入区域
        input_frame = tk.Frame(console_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(input_frame, text="命令:").pack(side=tk.LEFT)
        self.console_input = tk.Entry(input_frame)
        self.console_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.console_input.bind("<Return>", self._execute_console_command)
        
        tk.Button(input_frame, text="执行", command=self._execute_console_command).pack(side=tk.LEFT)
        
        # 输出区域
        self.console_text = scrolledtext.ScrolledText(console_frame, height=20)
        self.console_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加初始信息
        self._console_print("认知调试控制台已启动")
        self._console_print("可用命令: status, steps, breakpoints, bugs, help")
    
    def _start_debugging(self):
        """开始调试"""
        if self.debugger:
            self.debugger.is_debugging = True
            self._console_print("调试已启动")
            self._update_status("调试中")
    
    def _stop_debugging(self):
        """停止调试"""
        if self.debugger:
            self.debugger.is_debugging = False
            self._console_print("调试已停止")
            self._update_status("已停止")
    
    def _pause_debugging(self):
        """暂停调试"""
        if self.debugger:
            self.debugger.is_paused = not self.debugger.is_paused
            status = "已暂停" if self.debugger.is_paused else "运行中"
            self._console_print(f"调试状态: {status}")
            self._update_status(status)
    
    def _add_breakpoint(self):
        """添加断点"""
        layer = self.bp_layer_var.get()
        condition = self.bp_condition_var.get().strip()
        
        if not condition:
            messagebox.showwarning("警告", "请输入断点条件")
            return
        
        if self.debugger:
            bp_id = self.debugger.set_cognitive_breakpoint(layer, condition)
            self._console_print(f"已添加断点: {bp_id} - {condition}")
            self.bp_condition_var.set("")  # 清空输入框
            self._refresh_breakpoints()
    
    def _add_breakpoint_dialog(self):
        """添加断点对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加断点")
        dialog.geometry("400x200")
        dialog.grab_set()
        
        # 层级选择
        tk.Label(dialog, text="层级:").pack(pady=5)
        layer_var = tk.StringVar(value="自我")
        layer_combo = ttk.Combobox(dialog, textvariable=layer_var, 
                                  values=["自我", "本我", "身体", "超我"], state="readonly")
        layer_combo.pack(pady=5)
        
        # 条件输入
        tk.Label(dialog, text="条件:").pack(pady=5)
        condition_text = tk.Text(dialog, height=3, width=40)
        condition_text.pack(pady=5)
        
        # 按钮
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def add_bp():
            condition = condition_text.get("1.0", tk.END).strip()
            if condition and self.debugger:
                bp_id = self.debugger.set_cognitive_breakpoint(layer_var.get(), condition)
                self._console_print(f"已添加断点: {bp_id}")
                dialog.destroy()
                self._refresh_breakpoints()
        
        tk.Button(button_frame, text="添加", command=add_bp).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _remove_selected_breakpoint(self):
        """删除选中的断点"""
        selection = self.breakpoint_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的断点")
            return
        
        bp_id = self.breakpoint_tree.item(selection[0])['values'][0]
        if self.debugger and self.debugger.remove_breakpoint(bp_id):
            self._console_print(f"已删除断点: {bp_id}")
            self._refresh_breakpoints()
    
    def _clear_all_breakpoints(self):
        """清除所有断点"""
        if messagebox.askyesno("确认", "确定要清除所有断点吗？"):
            if self.debugger:
                self.debugger.breakpoints.clear()
                self._console_print("已清除所有断点")
                self._refresh_breakpoints()
    
    def _clear_debug_history(self):
        """清除调试历史"""
        if messagebox.askyesno("确认", "确定要清除调试历史吗？"):
            if self.debugger:
                self.debugger.cognitive_steps.clear()
                self.debugger.bug_reports.clear()
                self._console_print("已清除调试历史")
                self._refresh_all()
    
    def _refresh_all(self):
        """刷新所有面板"""
        self._refresh_steps()
        self._refresh_breakpoints()
        self._refresh_bugs()
        self._refresh_performance()
    
    def _refresh_steps(self):
        """刷新认知步骤"""
        if not self.debugger:
            return
        
        # 清空现有项目
        for item in self.step_tree.get_children():
            self.step_tree.delete(item)
        
        # 添加新步骤
        for step in self.debugger.cognitive_steps[-100:]:  # 只显示最近100步
            values = (
                step.step_id[:10],
                step.timestamp.strftime("%H:%M:%S"),
                step.layer,
                step.action[:20],
                "成功" if step.success else "失败",
                f"{step.execution_time:.3f}s"
            )
            self.step_tree.insert("", "end", values=values)
    
    def _refresh_breakpoints(self):
        """刷新断点列表"""
        if not self.debugger:
            return
        
        # 清空现有项目
        for item in self.breakpoint_tree.get_children():
            self.breakpoint_tree.delete(item)
        
        # 添加断点
        for bp_id, bp in self.debugger.breakpoints.items():
            values = (
                bp_id,
                bp.layer,
                bp.condition[:30],
                "激活" if bp.is_active else "禁用",
                bp.hit_count,
                bp.created_at.strftime("%m-%d %H:%M")
            )
            self.breakpoint_tree.insert("", "end", values=values)
    
    def _refresh_bugs(self):
        """刷新Bug报告"""
        if not self.debugger:
            return
        
        # 清空现有项目
        for item in self.bug_tree.get_children():
            self.bug_tree.delete(item)
        
        # 添加Bug报告
        for bug in self.debugger.bug_reports:
            values = (
                bug.bug_id[:15],
                bug.timestamp.strftime("%H:%M:%S"),
                bug.severity,
                bug.description[:30],
                bug.affected_layer,
                bug.status
            )
            self.bug_tree.insert("", "end", values=values)
    
    def _refresh_performance(self):
        """刷新性能监控图表"""
        if not self.debugger or not self.performance_canvas:
            return
        
        try:
            # 获取数据
            steps = self.debugger.cognitive_steps[-50:]  # 最近50步
            bugs = self.debugger.bug_reports
            
            # 清空所有子图
            self.time_subplot.clear()
            self.success_subplot.clear()
            self.layer_subplot.clear()
            self.bug_subplot.clear()
            
            if steps:
                # 执行时间趋势
                times = [step.timestamp for step in steps]
                exec_times = [step.execution_time for step in steps]
                self.time_subplot.plot(times, exec_times, 'b-')
                self.time_subplot.set_title("执行时间趋势")
                self.time_subplot.set_xlabel("时间")
                self.time_subplot.set_ylabel("执行时间(秒)")
                
                # 成功率统计
                success_count = sum(1 for step in steps if step.success)
                fail_count = len(steps) - success_count
                self.success_subplot.pie([success_count, fail_count], 
                                       labels=['成功', '失败'], 
                                       autopct='%1.1f%%',
                                       colors=['green', 'red'])
                self.success_subplot.set_title("成功率统计")
                
                # 层级分布
                layer_counts = {}
                for step in steps:
                    layer_counts[step.layer] = layer_counts.get(step.layer, 0) + 1
                
                if layer_counts:
                    self.layer_subplot.bar(layer_counts.keys(), layer_counts.values())
                    self.layer_subplot.set_title("层级执行分布")
                    self.layer_subplot.set_xlabel("层级")
                    self.layer_subplot.set_ylabel("执行次数")
            
            if bugs:
                # Bug严重程度分布
                severity_counts = {}
                for bug in bugs:
                    severity_counts[bug.severity] = severity_counts.get(bug.severity, 0) + 1
                
                if severity_counts:
                    colors = {'low': 'green', 'medium': 'yellow', 'high': 'orange', 'critical': 'red'}
                    bar_colors = [colors.get(severity, 'gray') for severity in severity_counts.keys()]
                    self.bug_subplot.bar(severity_counts.keys(), severity_counts.values(), color=bar_colors)
                    self.bug_subplot.set_title("Bug严重程度分布")
                    self.bug_subplot.set_xlabel("严重程度")
                    self.bug_subplot.set_ylabel("数量")
            
            # 调整布局并重绘
            self.performance_canvas.figure.tight_layout()
            self.performance_canvas.draw()
            
        except Exception as e:
            print(f"性能图表刷新失败: {e}")
    
    def _start_auto_refresh(self):
        """启动自动刷新"""
        if self.auto_refresh and not self.refresh_thread:
            self.is_running = True
            self.refresh_thread = threading.Thread(target=self._auto_refresh_loop, daemon=True)
            self.refresh_thread.start()
    
    def _auto_refresh_loop(self):
        """自动刷新循环"""
        while self.is_running:
            try:
                if self.root and self.root.winfo_exists():
                    self.root.after(0, self._refresh_all)
                    time.sleep(self.refresh_interval)
                else:
                    break
            except Exception as e:
                print(f"自动刷新错误: {e}")
                time.sleep(5)
    
    def _execute_console_command(self, event=None):
        """执行控制台命令"""
        command = self.console_input.get().strip()
        if not command:
            return
        
        self.console_input.delete(0, tk.END)
        self._console_print(f"> {command}")
        
        try:
            if command == "help":
                self._console_print("可用命令:")
                self._console_print("  status - 显示调试器状态")
                self._console_print("  steps - 显示认知步骤数量")
                self._console_print("  breakpoints - 显示断点信息")
                self._console_print("  bugs - 显示Bug报告")
                self._console_print("  clear - 清空控制台")
                
            elif command == "status":
                if self.debugger:
                    summary = self.debugger.get_debug_summary()
                    self._console_print(f"调试状态: {json.dumps(summary, ensure_ascii=False, indent=2)}")
                
            elif command == "steps":
                if self.debugger:
                    self._console_print(f"认知步骤总数: {len(self.debugger.cognitive_steps)}")
                
            elif command == "breakpoints":
                if self.debugger:
                    self._console_print(f"断点总数: {len(self.debugger.breakpoints)}")
                    for bp_id, bp in self.debugger.breakpoints.items():
                        self._console_print(f"  {bp_id}: {bp.condition} ({bp.hit_count}次触发)")
                
            elif command == "bugs":
                if self.debugger:
                    self._console_print(f"Bug报告总数: {len(self.debugger.bug_reports)}")
                    for bug in self.debugger.bug_reports[-5:]:
                        self._console_print(f"  {bug.bug_id}: {bug.description}")
                
            elif command == "clear":
                self.console_text.delete(1.0, tk.END)
                
            else:
                self._console_print(f"未知命令: {command}")
                
        except Exception as e:
            self._console_print(f"命令执行错误: {e}")
    
    def _console_print(self, message: str):
        """在控制台打印消息"""
        if self.console_text:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.console_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.console_text.see(tk.END)
    
    def _update_status(self, status: str):
        """更新状态栏"""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=f"状态: {status}")
    
    def _on_step_double_click(self, event):
        """认知步骤双击事件"""
        selection = self.step_tree.selection()
        if selection:
            step_id = self.step_tree.item(selection[0])['values'][0]
            self._show_step_details(step_id)
    
    def _on_bug_double_click(self, event):
        """Bug报告双击事件"""
        selection = self.bug_tree.selection()
        if selection:
            bug_id = self.bug_tree.item(selection[0])['values'][0]
            self._show_bug_details(bug_id)
    
    def _show_step_details(self, step_id: str):
        """显示步骤详情"""
        if not self.debugger:
            return
        
        # 查找步骤
        step = None
        for s in self.debugger.cognitive_steps:
            if s.step_id.startswith(step_id):
                step = s
                break
        
        if not step:
            return
        
        # 创建详情窗口
        details_window = tk.Toplevel(self.root)
        details_window.title(f"步骤详情 - {step_id}")
        details_window.geometry("600x500")
        
        # 详情文本
        details_text = scrolledtext.ScrolledText(details_window)
        details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 显示步骤信息
        step_info = f"""
步骤ID: {step.step_id}
时间: {step.timestamp}
层级: {step.layer}
动作: {step.action}
成功: {step.success}
执行时间: {step.execution_time}秒
错误信息: {step.error_message or '无'}

输入数据:
{json.dumps(step.input_data, ensure_ascii=False, indent=2)}

输出数据:
{json.dumps(step.output_data, ensure_ascii=False, indent=2)}

执行前状态:
{json.dumps(step.state_before, ensure_ascii=False, indent=2)}

执行后状态:
{json.dumps(step.state_after, ensure_ascii=False, indent=2)}

元数据:
{json.dumps(step.metadata, ensure_ascii=False, indent=2)}
        """
        
        details_text.insert(tk.END, step_info)
        details_text.config(state=tk.DISABLED)
    
    def _show_bug_details(self, bug_id: str):
        """显示Bug详情"""
        if not self.debugger:
            return
        
        # 查找Bug
        bug = None
        for b in self.debugger.bug_reports:
            if b.bug_id.startswith(bug_id):
                bug = b
                break
        
        if not bug:
            return
        
        # 创建详情窗口
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Bug详情 - {bug_id}")
        details_window.geometry("600x400")
        
        # 详情文本
        details_text = scrolledtext.ScrolledText(details_window)
        details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 显示Bug信息
        bug_info = f"""
Bug ID: {bug.bug_id}
时间: {bug.timestamp}
严重程度: {bug.severity}
描述: {bug.description}
影响层级: {bug.affected_layer}
状态: {bug.status}
建议修复: {bug.suggested_fix or '无'}

上下文:
{json.dumps(bug.context, ensure_ascii=False, indent=2)}
        """
        
        details_text.insert(tk.END, bug_info)
        details_text.config(state=tk.DISABLED)
    
    def _export_debug_log(self):
        """导出调试日志"""
        if not self.debugger:
            return
        
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                debug_data = {
                    'timestamp': datetime.now().isoformat(),
                    'steps': [asdict(step) for step in self.debugger.cognitive_steps],
                    'breakpoints': {bp_id: asdict(bp) for bp_id, bp in self.debugger.breakpoints.items()},
                    'bugs': [asdict(bug) for bug in self.debugger.bug_reports]
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(debug_data, f, ensure_ascii=False, indent=2, default=str)
                
                self._console_print(f"调试日志已导出到: {filename}")
                
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")
    
    def _import_breakpoints(self):
        """导入断点配置"""
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                breakpoints = data.get('breakpoints', {})
                imported_count = 0
                
                for bp_data in breakpoints.values():
                    if self.debugger:
                        self.debugger.set_cognitive_breakpoint(
                            bp_data['layer'], 
                            bp_data['condition']
                        )
                        imported_count += 1
                
                self._console_print(f"已导入 {imported_count} 个断点")
                self._refresh_breakpoints()
                
            except Exception as e:
                messagebox.showerror("错误", f"导入失败: {e}")
    
    def run(self):
        """运行可视化器"""
        self.create_gui()
        
        try:
            self.root.mainloop()
        finally:
            self.is_running = False
            if self.refresh_thread:
                self.refresh_thread.join(timeout=1)


# 示例用法
if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from pythonTask import Agent, llm_deepseek
    from embodied_cognitive_workflow import CognitiveAgent
    from cognitive_debug_agent import CognitiveDebugAgent
    
    # 创建测试实例
    base_agent = Agent(llm=llm_deepseek)
    ego_agent = base_agent
    id_agent = base_agent
    
    cognitive_agent = CognitiveAgent(
        ego=ego_agent,
        id=id_agent,
        body_agents={"main": base_agent},
        llm=llm_deepseek
    )
    
    debug_agent = CognitiveDebugAgent(
        cognitive_agent=cognitive_agent,
        llm=llm_deepseek,
        enable_debugging=True
    )
    
    # 创建并运行可视化器
    visualizer = CognitiveDebugVisualizer(debug_agent)
    visualizer.run()