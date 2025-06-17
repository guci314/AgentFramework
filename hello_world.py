def hello_world():
    """返回'Hello, World!'字符串"""
    return "Hello, World!"

import unittest

class TestHelloWorld(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(hello_world(), "Hello, World!")

if __name__ == "__main__":
    unittest.main()
