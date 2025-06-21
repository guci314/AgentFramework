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
