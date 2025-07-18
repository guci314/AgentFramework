读取指定的Python文件内容，分析其中的任务需求，然后生成并运行一个配置好的visual debugger脚本。

使用方法：
/cognitive_debug <文件路径>

例如：
/cognitive_debug embodied_cognitive_workflow/hello_world_validation.py

工作流程：
1. 读取embodied_cognitive_workflow/demo/demo_visual_debugger_usage.py 学习visual debugger的用法
2. 读取指定文件（$ARGUMENTS）的内容
3. 分析文件中的任务需求（如函数定义、测试用例、Agent配置等）
4. 生成一个临时的debugger脚本（temp.py），配置适当的Agent和任务
5. **使用nohup运行脚本**：执行 `nohup python temp.py > debugger.log 2>&1 &` 在后台运行
6. 创建debugger.log文件记录输出
7. 显示进程信息，方便用户管理
8. **重要**：不要自动删除生成的文件（如hello_world.py等），让用户决定是否保留

执行细节：
- 运行命令：`nohup python temp.py > debugger.log 2>&1 &`
- 这会在后台启动GUI，输出重定向到debugger.log
- 使用 `tail -f debugger.log` 可以实时查看日志
- GUI窗口会保持独立运行，不受Claude Code超时影响

支持的文件类型：
- Python脚本 (.py)
- 测试文件
- 任务描述文件

调试器会根据文件内容自动：
- 识别需要执行的任务
- 配置合适的Agent（如Python专家、测试专家等）
- 设置适当的调试参数
- 启动可视化界面展示执行过程

运行说明：
- 脚本会使用 `nohup python temp.py &` 在后台运行
- GUI窗口会独立于Claude Code进程，不受超时限制影响
- 输出日志会保存在 `nohup.out` 文件中
- 如需查看日志：`cat nohup.out`
- 如需停止运行：找到进程ID并使用 `kill` 命令

手动运行选项：
- 如果nohup方式有问题，可以手动运行：`python temp.py`
- 或者使用screen/tmux等终端复用工具

注意事项：
- 生成的文件会保留在工作目录中，不会自动清理
- 确保有图形界面环境（X11）才能看到GUI窗口
- GUI进程会在后台运行，需要手动关闭窗口或终止进程