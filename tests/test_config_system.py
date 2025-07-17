"""
Test Configuration System

This module tests the configuration system functionality including loading, 
validation, and error handling.
"""

import unittest
import tempfile
import os
import yaml
import json
from config_system import (
    ConfigurationLoader, ApplicationConfig, ConfigurationError,
    StateHistoryConfig, AIUpdaterConfig, MonitoringConfig, OptimizationConfig,
    get_config, initialize_config
)

class TestConfigurationSystem(unittest.TestCase):
    """Test cases for configuration system"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_default_configuration(self):
        """Test loading default configuration when no file exists"""
        loader = ConfigurationLoader()
        config = loader.load_config()
        
        # 验证默认配置
        self.assertIsInstance(config, ApplicationConfig)
        self.assertEqual(config.config_version, "1.0")
        self.assertEqual(config.environment, "development")
        self.assertFalse(config.debug_mode)
        
        # 验证子配置
        self.assertIsInstance(config.state_history, StateHistoryConfig)
        self.assertEqual(config.state_history.max_length, 50)
        
        self.assertIsInstance(config.ai_updater, AIUpdaterConfig)
        self.assertEqual(config.ai_updater.model_name, "deepseek-chat")
        
        self.assertIsInstance(config.monitoring, MonitoringConfig)
        self.assertEqual(config.monitoring.log_level, "INFO")
        
        self.assertIsInstance(config.optimization, OptimizationConfig)
        self.assertTrue(config.optimization.enable_instruction_caching)
    
    def test_yaml_configuration_loading(self):
        """Test loading configuration from YAML file"""
        # 创建测试配置文件
        config_data = {
            'config_version': '2.0',
            'environment': 'testing',
            'debug_mode': True,
            'state_history': {
                'max_length': 100,
                'enable_compression': True
            },
            'ai_updater': {
                'model_name': 'test-model',
                'temperature': 0.8
            },
            'monitoring': {
                'log_level': 'DEBUG',
                'enable_performance_monitoring': False
            },
            'optimization': {
                'enable_instruction_caching': False,
                'cache_size_limit': 500
            }
        }
        
        config_path = os.path.join(self.temp_dir, 'test_config.yaml')
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        # 加载配置
        loader = ConfigurationLoader(config_path)
        config = loader.load_config()
        
        # 验证配置
        self.assertEqual(config.config_version, '2.0')
        self.assertEqual(config.environment, 'testing')
        self.assertTrue(config.debug_mode)
        
        self.assertEqual(config.state_history.max_length, 100)
        self.assertTrue(config.state_history.enable_compression)
        
        self.assertEqual(config.ai_updater.model_name, 'test-model')
        self.assertEqual(config.ai_updater.temperature, 0.8)
        
        self.assertEqual(config.monitoring.log_level, 'DEBUG')
        self.assertFalse(config.monitoring.enable_performance_monitoring)
        
        self.assertFalse(config.optimization.enable_instruction_caching)
        self.assertEqual(config.optimization.cache_size_limit, 500)
    
    def test_json_configuration_loading(self):
        """Test loading configuration from JSON file"""
        config_data = {
            'config_version': '1.5',
            'environment': 'production',
            'ai_updater': {
                'model_name': 'production-model',
                'max_tokens': 4096
            }
        }
        
        config_path = os.path.join(self.temp_dir, 'test_config.json')
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        loader = ConfigurationLoader(config_path)
        config = loader.load_config()
        
        self.assertEqual(config.config_version, '1.5')
        self.assertEqual(config.environment, 'production')
        self.assertEqual(config.ai_updater.model_name, 'production-model')
        self.assertEqual(config.ai_updater.max_tokens, 4096)
    
    def test_partial_configuration(self):
        """Test loading partial configuration with default values"""
        config_data = {
            'environment': 'staging',
            'ai_updater': {
                'model_name': 'staging-model'
            }
        }
        
        config_path = os.path.join(self.temp_dir, 'partial_config.yaml')
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        loader = ConfigurationLoader(config_path)
        config = loader.load_config()
        
        # 验证部分配置被加载
        self.assertEqual(config.environment, 'staging')
        self.assertEqual(config.ai_updater.model_name, 'staging-model')
        
        # 验证默认值仍然存在
        self.assertEqual(config.config_version, '1.0')  # 默认值
        self.assertEqual(config.ai_updater.temperature, 0.6)  # 默认值
        self.assertEqual(config.state_history.max_length, 50)  # 默认值
    
    def test_invalid_configuration_file(self):
        """Test handling of invalid configuration file"""
        # 创建无效的YAML文件
        config_path = os.path.join(self.temp_dir, 'invalid_config.yaml')
        with open(config_path, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        loader = ConfigurationLoader(config_path)
        
        with self.assertRaises(ConfigurationError):
            loader.load_config()
    
    def test_nonexistent_configuration_file(self):
        """Test handling of nonexistent configuration file"""
        nonexistent_path = os.path.join(self.temp_dir, 'nonexistent.yaml')
        loader = ConfigurationLoader(nonexistent_path)
        
        # 应该回退到默认配置
        config = loader.load_config()
        self.assertIsInstance(config, ApplicationConfig)
        self.assertEqual(config.config_version, '1.0')
    
    def test_unsupported_file_format(self):
        """Test handling of unsupported file format"""
        config_path = os.path.join(self.temp_dir, 'config.txt')
        with open(config_path, 'w') as f:
            f.write("some content")
        
        loader = ConfigurationLoader(config_path)
        
        with self.assertRaises(ConfigurationError):
            loader.load_config()
    
    def test_configuration_reload(self):
        """Test configuration reloading"""
        # 创建初始配置
        config_data = {'environment': 'initial'}
        config_path = os.path.join(self.temp_dir, 'reload_config.yaml')
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        loader = ConfigurationLoader(config_path)
        config1 = loader.load_config()
        self.assertEqual(config1.environment, 'initial')
        
        # 修改配置文件
        config_data['environment'] = 'reloaded'
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        # 重新加载
        config2 = loader.reload_config()
        self.assertEqual(config2.environment, 'reloaded')
    
    def test_global_configuration_functions(self):
        """Test global configuration functions"""
        # 创建测试配置
        config_data = {'environment': 'global_test'}
        config_path = os.path.join(self.temp_dir, 'global_config.yaml')
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        # 初始化全局配置
        config = initialize_config(config_path)
        self.assertEqual(config.environment, 'global_test')
        
        # 获取全局配置
        global_config = get_config()
        self.assertEqual(global_config.environment, 'global_test')
    
    def test_fallback_strategies_validation(self):
        """Test validation of fallback strategies"""
        config_data = {
            'ai_updater': {
                'fallback_strategies': [
                    'RETRY_SIMPLIFIED',
                    'TEMPLATE_BASED',
                    'CUSTOM_STRATEGY'  # 这个应该被保留，即使不在预定义列表中
                ]
            }
        }
        
        config_path = os.path.join(self.temp_dir, 'fallback_config.yaml')
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        loader = ConfigurationLoader(config_path)
        config = loader.load_config()
        
        expected_strategies = ['RETRY_SIMPLIFIED', 'TEMPLATE_BASED', 'CUSTOM_STRATEGY']
        self.assertEqual(config.ai_updater.fallback_strategies, expected_strategies)
    
    def test_configuration_with_comments(self):
        """Test loading YAML configuration with comments"""
        yaml_content = """
        # This is a test configuration
        config_version: "1.0"
        environment: "test"  # Test environment
        
        # AI Configuration
        ai_updater:
          model_name: "test-model"  # Model for testing
          temperature: 0.5
        """
        
        config_path = os.path.join(self.temp_dir, 'commented_config.yaml')
        with open(config_path, 'w') as f:
            f.write(yaml_content)
        
        loader = ConfigurationLoader(config_path)
        config = loader.load_config()
        
        self.assertEqual(config.config_version, '1.0')
        self.assertEqual(config.environment, 'test')
        self.assertEqual(config.ai_updater.model_name, 'test-model')
        self.assertEqual(config.ai_updater.temperature, 0.5)

class TestConfigurationIntegration(unittest.TestCase):
    """Integration tests for configuration system"""
    
    def test_configuration_with_existing_yaml(self):
        """Test loading configuration from existing config.yaml"""
        if os.path.exists('config.yaml'):
            loader = ConfigurationLoader('config.yaml')
            config = loader.load_config()
            
            # 验证配置加载成功
            self.assertIsInstance(config, ApplicationConfig)
            print(f"Loaded configuration version: {config.config_version}")
            print(f"Environment: {config.environment}")
            print(f"AI Model: {config.ai_updater.model_name}")
            print(f"Log Level: {config.monitoring.log_level}")
        else:
            self.skipTest("config.yaml not found")

def run_basic_tests():
    """Run basic configuration system tests"""
    print("=== Configuration System Tests ===")
    
    try:
        # 测试默认配置
        print("\n1. Testing default configuration...")
        loader = ConfigurationLoader()
        config = loader.get_config()
        print(f"✓ Default config loaded: version={config.config_version}, env={config.environment}")
        
        # 测试配置文件加载（如果存在）
        print("\n2. Testing config file loading...")
        if os.path.exists('config.yaml'):
            file_loader = ConfigurationLoader('config.yaml')
            file_config = file_loader.load_config()
            print(f"✓ Config file loaded: version={file_config.config_version}, env={file_config.environment}")
            print(f"  AI Model: {file_config.ai_updater.model_name}")
            print(f"  Max tokens: {file_config.ai_updater.max_tokens}")
            print(f"  Cache enabled: {file_config.ai_updater.enable_caching}")
            print(f"  Log level: {file_config.monitoring.log_level}")
        else:
            print("✓ No config.yaml found, using defaults")
        
        # 测试全局配置
        print("\n3. Testing global configuration...")
        global_config = get_config()
        print(f"✓ Global config accessible: {type(global_config).__name__}")
        
        print("\n✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # 运行基本测试
    success = run_basic_tests()
    
    if success:
        print("\n" + "="*50)
        print("Running detailed unit tests...")
        unittest.main(verbosity=2)
    else:
        print("\n❌ Basic tests failed, skipping unit tests")
        exit(1) 