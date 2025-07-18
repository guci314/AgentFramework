import unittest
from hello_world import hello_world

class TestHelloWorld(unittest.TestCase):
    def test_hello_world(self):
        """测试hello_world函数返回值"""
        result = hello_world()
        self.assertEqual(result, "Hello, World!")

if __name__ == '__main__':
    unittest.main()
