import os
import unittest
from dotenv import load_dotenv
from pythonTask import llm_deepseek

# 加载环境变量
load_dotenv()


def load_api_key():
    """加载deepseek API密钥"""
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY环境变量未设置")
    return api_key


def check_deepseek_api_health():
    """检查deepseek API的健康状态"""
    try:
        # 加载API密钥
        api_key = load_api_key()
        
        # 进行简单的测试调用
        response = llm_deepseek.invoke("测试")
        
        # 检查响应是否有效
        if hasattr(response, 'content') and response.content:
            return True, "API连接正常"
        else:
            return False, "API响应无效"
            
    except ValueError as e:
        return False, f"API密钥配置错误: {str(e)}"
    except Exception as e:
        return False, f"API连接失败: {str(e)}"


def skip_if_api_unavailable(test_func):
    """装饰器：如果API不可用则跳过测试"""
    def wrapper(self):
        is_healthy, message = check_deepseek_api_health()
        if not is_healthy:
            self.skipTest(f"跳过测试，deepseek API不可用: {message}")
        return test_func(self)
    return wrapper


class TestAPIConfiguration(unittest.TestCase):
    """API配置测试"""
    
    def test_api_key_loading(self):
        """测试API密钥加载"""
        try:
            api_key = load_api_key()
            self.assertIsInstance(api_key, str)
            self.assertTrue(len(api_key) > 0)
        except ValueError:
            self.skipTest("DEEPSEEK_API_KEY环境变量未设置")
    
    def test_api_health_check(self):
        """测试API健康检查"""
        is_healthy, message = check_deepseek_api_health()
        if not is_healthy:
            self.skipTest(f"API健康检查失败: {message}")
        else:
            self.assertTrue(is_healthy)
            self.assertIn("正常", message)


if __name__ == '__main__':
    unittest.main(verbosity=2) 