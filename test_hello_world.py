import unittest
from hello_world import hello_world

class TestHelloWorld(unittest.TestCase):
    def test_hello_world_output(self):
        """验证hello_world函数返回正确的字符串"""
        self.assertEqual(hello_world(), 'Hello, World!')

if __name__ == '__main__':
    unittest.main()
