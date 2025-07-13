import sys
import os
import unittest

# 确保能正确导入src模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src'))

from hello_world import hello_world

class TestHelloWorld(unittest.TestCase):
    """测试hello_world模块"""
    
    def test_returns_expected_string(self):
        """测试返回正确的字符串"""
        result = hello_world()
        self.assertEqual(result, "Hello, World!")
        
    def test_return_type(self):
        """测试返回类型为字符串"""
        result = hello_world()
        self.assertIsInstance(result, str)

if __name__ == '__main__':
    unittest.main()
