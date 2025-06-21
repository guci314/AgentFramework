"""
IPython环境状态保存和恢复工具

功能:
1. saveIpython: 保存当前IPython环境中的用户定义对象（变量、函数、类）到文件
2. loadIpython: 从文件恢复IPython环境状态

可行性:
✅ 已实现核心功能并通过单元测试
✅ 适合保存简单编程环境状态（基础变量/函数/类）
✅ 支持Jupyter笔记本和IPython环境

主要缺陷:
⚠️ 对象序列化限制:
   - 无法处理特殊对象（数据库连接、文件句柄等）
   - 日志中会出现警告: "无法序列化对象 xxx: cannot pickle 'yyy' object"
⚠️ 环境恢复不完全:
   - 不恢复系统对象（模块、内置对象）
   - 不清理新增对象（只覆盖同名对象）
⚠️ 潜在问题:
   - 依赖冲突（恢复的类可能依赖未恢复的模块）
   - 大型环境序列化性能问题
   - 版本兼容性问题（Python/dill版本差异）
   - 安全风险（加载不可信文件可能执行恶意代码）

最佳实践:
1. 适用场景:
   saveIpython(ip, "simple_env.dill")  # 基础变量/函数/类
   # 避免保存含外部资源的环境
2. 使用前检查:
   import dill
   if not dill.pickles(your_object): print("对象无法序列化")
3. 恢复后操作:
   # 手动清理不需要的对象
   for obj in ['tmp_var']:
       if obj in ip.user_ns: del ip.user_ns[obj]

改进方向:
- 增加选择性保存（白名单/黑名单）
- 添加对象依赖分析
- 实现增量保存功能
- 增加版本兼容性检查
"""

import dill
import os
import logging
from types import ModuleType
import IPython

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ipython_state")

def saveIpython(ipython: IPython.core.interactiveshell.InteractiveShell, 
                file_path: str) -> bool:
    """
    保存IPython环境状态到文件（包括变量、函数和类）
    
    参数:
    ipython: IPython实例（通过 get_ipython() 获取）
    file_path: 保存路径
    
    返回: 成功返回True，否则False
    """
    if ipython is None:
        logger.error("IPython实例不能为None")
        return False
        
    try:
        state = {}
        ns = ipython.user_ns
        logger.info(f"开始保存IPython状态，共{len(ns)}个对象")
        
        for name, obj in ns.items():
            # 过滤条件：跳过模块、内置对象和特殊变量
            skip_conditions = [
                isinstance(obj, ModuleType),  # 跳过模块
                name.startswith('__') and name.endswith('__'),  # 跳过__builtins__等
                name.startswith('_ih'),  # 跳过输入历史
                name.startswith('_oh'),  # 跳过输出历史
                name.startswith('_dh'),  # 跳过目录历史
                name in ['exit', 'quit', 'get_ipython']  # 跳过特殊命令
            ]
            
            if any(skip_conditions):
                continue
                
            try:
                # 尝试序列化对象
                state[name] = dill.dumps(obj)
                logger.debug(f"已序列化对象: {name} ({type(obj).__name__})")
            except Exception as e:
                logger.warning(f"无法序列化对象 {name}: {str(e)}")
        
        with open(file_path, 'wb') as f:
            dill.dump(state, f)
            
        logger.info(f"成功保存 {len(state)} 个对象到: {file_path}")
        return True
    except Exception as e:
        logger.error(f"保存状态失败: {str(e)}")
        return False

def loadIpython(ipython: IPython.core.interactiveshell.InteractiveShell, 
                file_path: str) -> bool:
    """
    从文件加载IPython环境状态（恢复变量、函数和类）
    
    参数:
    ipython: IPython实例（通过 get_ipython() 获取）
    file_path: 加载路径
    
    返回: 成功返回True，否则False
    """
    if ipython is None:
        logger.error("IPython实例不能为None")
        return False
        
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return False
        
    try:
        with open(file_path, 'rb') as f:
            state = dill.load(f)
            
        ns = ipython.user_ns
        success_count = 0
        total_count = len(state)
        
        for name, serialized_obj in state.items():
            try:
                obj = dill.loads(serialized_obj)
                ns[name] = obj
                success_count += 1
                logger.info(f"已恢复对象: {name} ({type(obj).__name__})")
            except Exception as e:
                logger.error(f"加载对象 {name} 失败: {str(e)}")
                
        logger.info(f"成功恢复 {success_count}/{total_count} 个对象")
        return True
    except Exception as e:
        logger.error(f"加载状态失败: {str(e)}")
        return False
