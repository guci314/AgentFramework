#!/usr/bin/env python3
"""
状态查询工具 - 为AI代理框架提供命令行状态查询和显示功能
"""

import argparse
import json
import pickle
import sys
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
import difflib
from pathlib import Path
import re

# 尝试导入rich库以获得更好的显示效果
try:
    from rich.console import Console
    from rich.table import Table
    from rich.tree import Tree
    from rich.json import JSON
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress
    from rich.prompt import Prompt, Confirm
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

# 导入项目模块
try:
    from enhancedAgent_v2 import WorkflowState, StateHistoryEntry
    from config_system import ConfigurationLoader
    AGENT_MODULES_AVAILABLE = True
except ImportError:
    AGENT_MODULES_AVAILABLE = False
    print("Warning: Agent modules not available. Some features may be limited.")


class StateQueryTool:
    """状态查询工具主类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化状态查询工具"""
        self.config_path = config_path or "config.yaml"
        self.config = None
        self.workflow_state = None
        
        # 加载配置
        self._load_config()
        
        # 初始化显示组件
        self.use_rich = RICH_AVAILABLE
        if not self.use_rich:
            print("Rich library not available. Using basic text output.")
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if AGENT_MODULES_AVAILABLE:
                loader = ConfigurationLoader()
                self.config = loader.load_config(self.config_path)
                print(f"✅ Configuration loaded from {self.config_path}")
            else:
                print("⚠️ Configuration system not available")
        except Exception as e:
            print(f"⚠️ Failed to load configuration: {e}")
    
    def create_sample_state(self) -> 'WorkflowState':
        """创建示例状态数据用于演示"""
        if not AGENT_MODULES_AVAILABLE:
            print("❌ Agent modules not available. Cannot create sample state.")
            return None
        
        # 创建WorkflowState实例
        state = WorkflowState()
        
        # 添加一些示例状态
        sample_states = [
            "系统初始化完成，准备开始工作流执行",
            "正在执行第一个任务：数据收集和预处理",
            "数据收集完成，发现1000条有效记录，开始数据清洗",
            "数据清洗完成，准备进行分析阶段",
            "分析阶段完成，生成了3个关键洞察和5个建议",
            "开始生成最终报告，整合所有分析结果",
            "工作流执行完成，所有任务已成功完成"
        ]
        
        sources = ["system", "task_executor", "data_processor", "analyzer", "report_generator"]
        
        for i, state_text in enumerate(sample_states):
            source = sources[i % len(sources)]
            state.set_global_state(state_text, source=source)
        
        return state
    
    def load_state_from_file(self, file_path: str) -> Optional['WorkflowState']:
        """从文件加载状态数据"""
        try:
            path = Path(file_path)
            if not path.exists():
                self._print_error(f"File not found: {file_path}")
                return None
            
            if path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 这里需要实现从JSON重建WorkflowState的逻辑
                    # 暂时返回None，实际实现中需要根据JSON结构重建
                    self._print_warning("JSON loading not yet implemented")
                    return None
            
            elif path.suffix.lower() == '.pkl':
                with open(file_path, 'rb') as f:
                    state = pickle.load(f)
                    if isinstance(state, WorkflowState):
                        return state
                    else:
                        self._print_error(f"Invalid state file format: {type(state)}")
                        return None
            
            else:
                self._print_error(f"Unsupported file format: {path.suffix}")
                return None
                
        except Exception as e:
            self._print_error(f"Failed to load state from {file_path}: {e}")
            return None
    
    def save_state_to_file(self, state: 'WorkflowState', file_path: str, format: str = 'json'):
        """保存状态到文件"""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'json':
                # 将状态转换为JSON格式
                state_data = {
                    'global_state': state.get_global_state(),
                    'state_update_enabled': state.is_state_update_enabled(),
                    'history': []
                }
                
                # 添加历史记录
                history = state.get_state_history()
                for entry in history:
                    state_data['history'].append({
                        'timestamp': entry.timestamp.isoformat(),
                        'state': entry.state_snapshot,
                        'source': entry.source
                    })
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            elif format.lower() == 'pkl':
                with open(file_path, 'wb') as f:
                    pickle.dump(state, f)
            
            elif format.lower() == 'csv':
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Timestamp', 'State', 'Source'])
                    
                    history = state.get_state_history()
                    for entry in history:
                        writer.writerow([
                            entry.timestamp.isoformat(),
                            entry.state,
                            entry.source
                        ])
            
            elif format.lower() == 'md':
                self._export_to_markdown(state, file_path)
            
            else:
                self._print_error(f"Unsupported format: {format}")
                return
            
            self._print_success(f"State saved to {file_path}")
            
        except Exception as e:
            self._print_error(f"Failed to save state to {file_path}: {e}")
    
    def _export_to_markdown(self, state: 'WorkflowState', file_path: str):
        """导出状态为Markdown格式"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# 工作流状态报告\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 当前状态
            f.write("## 当前状态\n\n")
            current_state = state.get_global_state()
            f.write(f"```\n{current_state}\n```\n\n")
            
            # 状态更新设置
            f.write("## 状态管理设置\n\n")
            f.write(f"- 状态更新启用: {state.is_state_update_enabled()}\n")
            
            # 内存分析
            if hasattr(state, 'analyze_memory_usage'):
                f.write("- 内存分析:\n")
                try:
                    memory_info = state.analyze_memory_usage()
                    for key, value in memory_info.items():
                        f.write(f"  - {key}: {value}\n")
                except:
                    f.write("  - 内存分析不可用\n")
            
            f.write("\n")
            
            # 历史记录
            f.write("## 状态历史\n\n")
            history = state.get_state_history()
            
            if history:
                f.write("| 时间 | 来源 | 状态 |\n")
                f.write("|------|------|------|\n")
                
                for entry in history:
                    timestamp = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    state_preview = entry.state[:50] + "..." if len(entry.state) > 50 else entry.state
                    f.write(f"| {timestamp} | {entry.source} | {state_preview} |\n")
            else:
                f.write("无历史记录\n")
    
    def display_current_state(self, state: 'WorkflowState'):
        """显示当前状态"""
        if self.use_rich:
            current_state = state.get_global_state()
            panel = Panel(
                current_state,
                title="[bold blue]当前状态[/bold blue]",
                border_style="blue"
            )
            console.print(panel)
        else:
            print("=== 当前状态 ===")
            print(state.get_global_state())
            print()
    
    def display_state_history(self, state: 'WorkflowState', limit: Optional[int] = None, 
                            source_filter: Optional[str] = None, 
                            search_term: Optional[str] = None):
        """显示状态历史"""
        history = state.get_state_history()
        
        # 应用过滤器
        if source_filter:
            history = [entry for entry in history if entry.source == source_filter]
        
        if search_term:
            history = [entry for entry in history if search_term.lower() in entry.state_snapshot.lower()]
        
        if limit:
            history = history[-limit:]
        
        if not history:
            self._print_warning("No history entries found matching the criteria")
            return
        
        if self.use_rich:
            table = Table(title="状态历史")
            table.add_column("时间", style="cyan", no_wrap=True)
            table.add_column("来源", style="magenta")
            table.add_column("状态", style="white")
            
            for entry in history:
                timestamp = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                state_preview = entry.state_snapshot[:80] + "..." if len(entry.state_snapshot) > 80 else entry.state_snapshot
                table.add_row(timestamp, entry.source, state_preview)
            
            console.print(table)
        else:
            print("=== 状态历史 ===")
            for i, entry in enumerate(history, 1):
                timestamp = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                print(f"{i}. [{timestamp}] ({entry.source})")
                print(f"   {entry.state}")
                print()
    
    def compare_states(self, state1_text: str, state2_text: str, 
                      label1: str = "State 1", label2: str = "State 2"):
        """比较两个状态"""
        if self.use_rich:
            # 使用rich显示差异
            diff_lines = list(difflib.unified_diff(
                state1_text.splitlines(keepends=True),
                state2_text.splitlines(keepends=True),
                fromfile=label1,
                tofile=label2,
                lineterm=''
            ))
            
            if diff_lines:
                diff_text = ''.join(diff_lines)
                panel = Panel(
                    diff_text,
                    title=f"[bold yellow]状态对比: {label1} vs {label2}[/bold yellow]",
                    border_style="yellow"
                )
                console.print(panel)
            else:
                console.print("[green]两个状态相同[/green]")
        else:
            print(f"=== 状态对比: {label1} vs {label2} ===")
            diff_lines = list(difflib.unified_diff(
                state1_text.splitlines(keepends=True),
                state2_text.splitlines(keepends=True),
                fromfile=label1,
                tofile=label2,
                lineterm=''
            ))
            
            if diff_lines:
                for line in diff_lines:
                    print(line.rstrip())
            else:
                print("两个状态相同")
            print()
    
    def display_memory_analysis(self, state: 'WorkflowState'):
        """显示内存分析"""
        if not hasattr(state, 'analyze_memory_usage'):
            self._print_warning("Memory analysis not available")
            return
        
        try:
            analysis = state.analyze_memory_usage()
            
            if self.use_rich:
                table = Table(title="内存使用分析")
                table.add_column("指标", style="cyan")
                table.add_column("值", style="magenta")
                table.add_column("单位", style="white")
                
                for key, value in analysis.items():
                    if isinstance(value, (int, float)):
                        if 'size' in key.lower() or 'bytes' in key.lower():
                            unit = "bytes"
                            if value > 1024:
                                value = f"{value/1024:.2f}"
                                unit = "KB"
                            if float(value) > 1024:
                                value = f"{float(value)/1024:.2f}"
                                unit = "MB"
                        else:
                            unit = ""
                    else:
                        unit = ""
                    
                    table.add_row(key, str(value), unit)
                
                console.print(table)
            else:
                print("=== 内存使用分析 ===")
                for key, value in analysis.items():
                    print(f"{key}: {value}")
                print()
                
        except Exception as e:
            self._print_error(f"Failed to analyze memory: {e}")
    
    def interactive_mode(self, state: 'WorkflowState'):
        """交互式模式"""
        if self.use_rich:
            console.print("[bold green]进入交互式状态查询模式[/bold green]")
            console.print("输入 'help' 查看可用命令，输入 'quit' 退出")
        else:
            print("=== 交互式状态查询模式 ===")
            print("输入 'help' 查看可用命令，输入 'quit' 退出")
        
        while True:
            try:
                if self.use_rich:
                    command = Prompt.ask("[bold blue]查询命令[/bold blue]")
                else:
                    command = input("查询命令> ").strip()
                
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0].lower()
                
                if cmd == 'quit' or cmd == 'exit':
                    break
                elif cmd == 'help':
                    self._show_help()
                elif cmd == 'current':
                    self.display_current_state(state)
                elif cmd == 'history':
                    limit = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
                    self.display_state_history(state, limit=limit)
                elif cmd == 'search':
                    if len(parts) < 2:
                        self._print_error("Usage: search <term>")
                        continue
                    search_term = ' '.join(parts[1:])
                    self.display_state_history(state, search_term=search_term)
                elif cmd == 'filter':
                    if len(parts) < 2:
                        self._print_error("Usage: filter <source>")
                        continue
                    source = parts[1]
                    self.display_state_history(state, source_filter=source)
                elif cmd == 'memory':
                    self.display_memory_analysis(state)
                elif cmd == 'export':
                    if len(parts) < 3:
                        self._print_error("Usage: export <format> <filename>")
                        continue
                    format_type = parts[1]
                    filename = parts[2]
                    self.save_state_to_file(state, filename, format_type)
                elif cmd == 'compare':
                    if len(parts) < 3:
                        self._print_error("Usage: compare <index1> <index2>")
                        continue
                    try:
                        idx1, idx2 = int(parts[1]), int(parts[2])
                        history = state.get_state_history()
                        if 0 <= idx1 < len(history) and 0 <= idx2 < len(history):
                            self.compare_states(
                                history[idx1].state, 
                                history[idx2].state,
                                f"Entry {idx1}", 
                                f"Entry {idx2}"
                            )
                        else:
                            self._print_error("Invalid history indices")
                    except ValueError:
                        self._print_error("Invalid indices")
                else:
                    self._print_error(f"Unknown command: {cmd}. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\n退出交互模式")
                break
            except Exception as e:
                self._print_error(f"Command error: {e}")
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = """
可用命令:
  current                    - 显示当前状态
  history [limit]           - 显示状态历史 (可选择显示最近N条)
  search <term>             - 搜索包含指定词语的状态
  filter <source>           - 按来源过滤状态历史
  memory                    - 显示内存使用分析
  export <format> <file>    - 导出状态 (格式: json, csv, md, pkl)
  compare <idx1> <idx2>     - 比较两个历史状态
  help                      - 显示此帮助信息
  quit/exit                 - 退出交互模式
        """
        
        if self.use_rich:
            console.print(Panel(help_text, title="[bold blue]帮助信息[/bold blue]", border_style="blue"))
        else:
            print(help_text)
    
    def _print_success(self, message: str):
        """打印成功消息"""
        if self.use_rich:
            console.print(f"[green]✅ {message}[/green]")
        else:
            print(f"✅ {message}")
    
    def _print_error(self, message: str):
        """打印错误消息"""
        if self.use_rich:
            console.print(f"[red]❌ {message}[/red]")
        else:
            print(f"❌ {message}")
    
    def _print_warning(self, message: str):
        """打印警告消息"""
        if self.use_rich:
            console.print(f"[yellow]⚠️ {message}[/yellow]")
        else:
            print(f"⚠️ {message}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI代理框架状态查询工具")
    parser.add_argument("--config", "-c", help="配置文件路径", default="config.yaml")
    parser.add_argument("--file", "-f", help="状态文件路径")
    parser.add_argument("--interactive", "-i", action="store_true", help="进入交互模式")
    parser.add_argument("--current", action="store_true", help="显示当前状态")
    parser.add_argument("--history", type=int, metavar="N", help="显示最近N条历史记录")
    parser.add_argument("--memory", action="store_true", help="显示内存分析")
    parser.add_argument("--export", nargs=2, metavar=("FORMAT", "FILE"), help="导出状态到文件")
    parser.add_argument("--sample", action="store_true", help="使用示例数据")
    parser.add_argument("--search", help="搜索状态历史")
    parser.add_argument("--filter", help="按来源过滤状态历史")
    
    args = parser.parse_args()
    
    # 创建查询工具实例
    tool = StateQueryTool(config_path=args.config)
    
    # 加载或创建状态
    if args.file:
        state = tool.load_state_from_file(args.file)
        if not state:
            return 1
    elif args.sample:
        state = tool.create_sample_state()
        if not state:
            return 1
    else:
        if not AGENT_MODULES_AVAILABLE:
            print("❌ Agent modules not available and no state file provided.")
            print("Use --sample to create sample data or --file to load from file.")
            return 1
        
        # 创建空状态
        state = WorkflowState()
        tool._print_warning("Using empty state. Use --sample for demo data or --file to load existing state.")
    
    # 执行命令
    if args.interactive:
        tool.interactive_mode(state)
    else:
        if args.current:
            tool.display_current_state(state)
        
        if args.history is not None:
            tool.display_state_history(state, limit=args.history)
        
        if args.memory:
            tool.display_memory_analysis(state)
        
        if args.search:
            tool.display_state_history(state, search_term=args.search)
        
        if args.filter:
            tool.display_state_history(state, source_filter=args.filter)
        
        if args.export:
            format_type, filename = args.export
            tool.save_state_to_file(state, filename, format_type)
        
        # 如果没有指定任何操作，显示当前状态和简短历史
        if not any([args.current, args.history is not None, args.memory, 
                   args.search, args.filter, args.export]):
            tool.display_current_state(state)
            tool.display_state_history(state, limit=5)
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 