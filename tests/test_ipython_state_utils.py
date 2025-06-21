import os
import sys
import tempfile
import pytest
import dill
from ipython_state_utils import saveIpython, loadIpython
from IPython.testing.globalipapp import get_ipython
from types import ModuleType

@pytest.fixture(scope="module")
def ipython():
    """获取全局IPython实例"""
    return get_ipython()

def test_save_and_load_ipython_state(ipython):
    """测试保存和加载IPython环境状态"""
    # 创建简单可序列化的测试对象
    ipython.user_ns['test_var'] = 42
    
    # 定义不依赖外部环境的简单函数
    def test_func():
        return 'hello'
    ipython.user_ns['test_func'] = test_func
    
    # 定义简单类
    class TestClass:
        pass
    ipython.user_ns['TestClass'] = TestClass

    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix='.dill', delete=False) as tmp_file:
        file_path = tmp_file.name

    try:
        # 保存环境状态
        assert saveIpython(ipython, file_path) is True
        assert os.path.exists(file_path)
        assert os.path.getsize(file_path) > 0

        # 修改环境状态
        ipython.user_ns['test_var'] = 0
        def changed_func():
            return 'changed'
        ipython.user_ns['test_func'] = changed_func
        # 修改TestClass而不是添加新的类
        class ModifiedTestClass:
            pass
        ipython.user_ns['TestClass'] = ModifiedTestClass

        # 加载保存的状态
        assert loadIpython(ipython, file_path) is True

        # 验证状态恢复
        assert ipython.user_ns['test_var'] == 42
        assert ipython.user_ns['test_func']() == 'hello'
        # 检查TestClass是否被恢复为原始类
        assert ipython.user_ns['TestClass'].__name__ == 'TestClass'
    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            os.unlink(file_path)
        # 清理创建的对象
        del ipython.user_ns['test_var']
        del ipython.user_ns['test_func']
        del ipython.user_ns['TestClass']
        if 'ChangedClass' in ipython.user_ns:
            del ipython.user_ns['ChangedClass']

def test_save_with_invalid_ipython():
    """测试无效IPython实例的保存"""
    with tempfile.NamedTemporaryFile(suffix='.dill') as tmp_file:
        assert saveIpython(None, tmp_file.name) is False

def test_load_with_invalid_ipython():
    """测试无效IPython实例的加载"""
    with tempfile.NamedTemporaryFile(suffix='.dill') as tmp_file:
        assert loadIpython(None, tmp_file.name) is False

def test_load_nonexistent_file(ipython):
    """测试加载不存在的文件"""
    assert loadIpython(ipython, "/path/to/nonexistent/file.dill") is False

def test_skip_unsupported_objects(ipython):
    """测试跳过不受支持的对象"""
    # 创建模块对象（应该被跳过）
    module = ModuleType('test_module')
    ipython.user_ns['test_module'] = module
    
    # 创建特殊变量（应该被跳过）
    ipython.user_ns['__special__'] = "should be skipped"
    ipython.user_ns['_ih'] = "input history"
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix='.dill', delete=False) as tmp_file:
        file_path = tmp_file.name
    
    try:
        # 保存环境状态
        assert saveIpython(ipython, file_path) is True
        
        # 检查保存的对象
        with open(file_path, 'rb') as f:
            state = dill.load(f)
            
        # 验证不支持的对象没有被保存
        assert 'test_module' not in state
        assert '__special__' not in state
        assert '_ih' not in state
    finally:
        if os.path.exists(file_path):
            os.unlink(file_path)

def test_save_and_load_with_run_cell(ipython):
    """测试通过run_cell定义的对象能否正确保存和加载"""
    # 使用run_cell定义简单对象（避免捕获外部变量）
    ipython.run_cell("run_cell_var = 100")
    # 使用绝对简单的函数定义
    ipython.run_cell("def run_cell_func(): pass")
    ipython.run_cell("class RunCellClass: pass")
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix='.dill', delete=False) as tmp_file:
        file_path = tmp_file.name
    
    try:
        # 保存环境状态
        assert saveIpython(ipython, file_path) is True
        
        # 修改环境状态
        ipython.run_cell("run_cell_var = 0")
        ipython.run_cell("def run_cell_func(): pass")
        ipython.run_cell("class ChangedClass: pass")
        
        # 加载保存的状态
        assert loadIpython(ipython, file_path) is True
        
        # 验证状态恢复
        assert ipython.user_ns['run_cell_var'] == 100
        # 直接检查函数是否存在，而不是调用它
        assert 'run_cell_func' in ipython.user_ns
        assert ipython.user_ns['RunCellClass'].__name__ == 'RunCellClass'
        # 注意：状态恢复不会删除新添加的对象，只覆盖同名对象
        # 所以不检查ChangedClass是否存在
    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            os.unlink(file_path)
        # 清理创建的对象
        for name in ['run_cell_var', 'run_cell_func', 'RunCellClass']:
            if name in ipython.user_ns:
                del ipython.user_ns[name]
        # 单独清理可能存在的ChangedClass
        if 'ChangedClass' in ipython.user_ns:
            del ipython.user_ns['ChangedClass']

if __name__ == "__main__":
    # 当直接执行此脚本时，运行所有测试
    pytest.main([__file__])
