import unittest
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from hello import hello_world

class TestHelloWorld(unittest.TestCase):
    def test_hello_world_output(self):
        """测试hello_world函数输出是否正确"""
        result = hello_world()
        self.assertEqual(result, "Hello, World!")
        self.assertIsInstance(result, str)
        
    def test_hello_world_not_empty(self):
        """测试hello_world函数返回值不为空"""
        result = hello_world()
        self.assertTrue(len(result) > 0)

if __name__ == '__main__':
    unittest.main()