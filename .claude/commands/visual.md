启动具身认知工作流的可视化调试器 GUI。

执行步骤：
1. 运行 visual debugger: `python embodied_cognitive_workflow/visual_debugger.py`
2. 在弹出的GUI窗口中：
   - 点击"配置Agent"按钮设置LLM和Agent
   - 在任务文本框输入你的任务
   - 点击"开始"按钮开始调试
   - 使用"单步"查看每个认知步骤的详细信息
   - 使用"自动执行"运行完整流程

特性：
- 可视化四层认知架构的执行过程
- 显示每个步骤的输入/输出
- 支持多Agent协作调试
- 实时查看认知循环状态