"""
测试环境设置模块
为所有测试文件提供统一的路径设置和导入
"""

import sys
import os

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# tests目录的父目录（embodied_cognitive_workflow）
parent_dir = os.path.dirname(current_dir)

# embodied_cognitive_workflow的父目录（AgentFrameWork）
grandparent_dir = os.path.dirname(parent_dir)

# 添加必要的路径
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if grandparent_dir not in sys.path:
    sys.path.insert(0, grandparent_dir)

# 设置代理（如果需要）
def setup_proxy():
    """设置HTTP代理"""
    os.environ["http_proxy"] = "http://127.0.0.1:7890"
    os.environ["https_proxy"] = "http://127.0.0.1:7890"

# 通用的测试设置
def setup_test_environment():
    """设置测试环境"""
    setup_proxy()
    print("✅ 测试环境设置完成")