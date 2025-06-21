"""
Configuration System for Enhanced Agent v2

This module provides a centralized configuration system that manages all operational
parameters for state management, AI optimization, and monitoring.
"""

import yaml
import json
import os
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class StateHistoryConfig:
    """Configuration for state history management"""
    max_length: int = 50
    enable_compression: bool = False
    compression_threshold: int = 1000  # 字符数阈值
    auto_cleanup: bool = True
    cleanup_interval_hours: int = 24

@dataclass
class AIUpdaterConfig:
    """Configuration for AI updater settings"""
    model_name: str = "deepseek-chat"
    api_base_url: str = "https://api.deepseek.com"
    timeout_seconds: int = 30
    max_retries: int = 3
    enable_caching: bool = True
    cache_ttl_minutes: int = 30
    temperature: float = 0.6
    max_tokens: int = 8192
    enable_fallback: bool = True
    fallback_strategies: list = field(default_factory=lambda: [
        "RETRY_SIMPLIFIED", "TEMPLATE_BASED", "RULE_BASED"
    ])

@dataclass
class MonitoringConfig:
    """Configuration for monitoring and logging"""
    log_level: str = "INFO"
    enable_performance_monitoring: bool = True
    reporting_interval_minutes: int = 60
    enable_memory_profiling: bool = False
    max_log_file_size_mb: int = 100
    log_rotation_count: int = 5
    enable_metrics_export: bool = False
    metrics_export_path: str = "./metrics"

@dataclass
class OptimizationConfig:
    """Configuration for performance optimization"""
    enable_instruction_caching: bool = True
    cache_size_limit: int = 1000
    enable_conditional_ai_calls: bool = True
    ai_call_cooldown_seconds: int = 5
    enable_batch_processing: bool = False
    batch_size: int = 10
    enable_async_processing: bool = False

@dataclass
class ApplicationConfig:
    """Main application configuration"""
    state_history: StateHistoryConfig = field(default_factory=StateHistoryConfig)
    ai_updater: AIUpdaterConfig = field(default_factory=AIUpdaterConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    
    # 全局设置
    debug_mode: bool = False
    environment: str = "development"  # development, testing, production
    config_version: str = "1.0"

class ConfigurationError(Exception):
    """Configuration related errors"""
    pass

class ConfigurationLoader:
    """Configuration file loader with validation and type safety"""
    
    DEFAULT_CONFIG_PATHS = [
        "config.yaml",
        "config.yml", 
        "config.json",
        "./config/config.yaml",
        "./config/config.yml",
        "./config/config.json"
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path
        self._config: Optional[ApplicationConfig] = None
        self._loaded = False
    
    def load_config(self, config_path: Optional[str] = None) -> ApplicationConfig:
        """
        Load configuration from file
        
        Args:
            config_path: Optional path to configuration file
            
        Returns:
            ApplicationConfig object
            
        Raises:
            ConfigurationError: If configuration cannot be loaded or is invalid
        """
        if config_path:
            self.config_path = config_path
        
        # 尝试找到配置文件
        actual_config_path = self._find_config_file()
        
        if not actual_config_path:
            logger.warning("No configuration file found, using default configuration")
            self._config = ApplicationConfig()
            self._loaded = True
            return self._config
        
        try:
            # 加载配置文件
            config_data = self._load_config_file(actual_config_path)
            
            # 验证和转换配置
            self._config = self._parse_config_data(config_data)
            self._loaded = True
            
            logger.info(f"Configuration loaded successfully from {actual_config_path}")
            return self._config
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {str(e)}") from e
    
    def get_config(self) -> ApplicationConfig:
        """
        Get current configuration
        
        Returns:
            ApplicationConfig object
            
        Raises:
            ConfigurationError: If configuration not loaded
        """
        if not self._loaded or self._config is None:
            return self.load_config()
        return self._config
    
    def reload_config(self) -> ApplicationConfig:
        """
        Reload configuration from file
        
        Returns:
            ApplicationConfig object
        """
        self._loaded = False
        self._config = None
        return self.load_config()
    
    def save_config(self, config: ApplicationConfig, 
                   output_path: Optional[str] = None) -> None:
        """
        Save configuration to file
        
        Args:
            config: Configuration to save
            output_path: Optional output path
        """
        if not output_path:
            output_path = self.config_path or "config.yaml"
        
        config_dict = self._config_to_dict(config)
        
        try:
            if output_path.endswith(('.yaml', '.yml')):
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_dict, f, default_flow_style=False, 
                             allow_unicode=True, indent=2)
            elif output_path.endswith('.json'):
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
            else:
                raise ConfigurationError(f"Unsupported config file format: {output_path}")
            
            logger.info(f"Configuration saved to {output_path}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {str(e)}") from e
    
    def _find_config_file(self) -> Optional[str]:
        """Find configuration file"""
        if self.config_path and os.path.exists(self.config_path):
            return self.config_path
        
        for path in self.DEFAULT_CONFIG_PATHS:
            if os.path.exists(path):
                return path
        
        return None
    
    def _load_config_file(self, config_path: str) -> Dict[str, Any]:
        """Load configuration file content"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith(('.yaml', '.yml')):
                    return yaml.safe_load(f) or {}
                elif config_path.endswith('.json'):
                    return json.load(f) or {}
                else:
                    raise ConfigurationError(f"Unsupported config file format: {config_path}")
        except Exception as e:
            raise ConfigurationError(f"Failed to read config file {config_path}: {str(e)}") from e
    
    def _parse_config_data(self, config_data: Dict[str, Any]) -> ApplicationConfig:
        """Parse configuration data into ApplicationConfig"""
        try:
            # 解析各个子配置
            state_history_data = config_data.get('state_history', {})
            ai_updater_data = config_data.get('ai_updater', {})
            monitoring_data = config_data.get('monitoring', {})
            optimization_data = config_data.get('optimization', {})
            
            # 创建配置对象
            config = ApplicationConfig(
                state_history=self._parse_state_history_config(state_history_data),
                ai_updater=self._parse_ai_updater_config(ai_updater_data),
                monitoring=self._parse_monitoring_config(monitoring_data),
                optimization=self._parse_optimization_config(optimization_data),
                debug_mode=config_data.get('debug_mode', False),
                environment=config_data.get('environment', 'development'),
                config_version=config_data.get('config_version', '1.0')
            )
            
            return config
            
        except Exception as e:
            raise ConfigurationError(f"Failed to parse configuration data: {str(e)}") from e
    
    def _parse_state_history_config(self, data: Dict[str, Any]) -> StateHistoryConfig:
        """Parse state history configuration"""
        return StateHistoryConfig(
            max_length=data.get('max_length', 50),
            enable_compression=data.get('enable_compression', False),
            compression_threshold=data.get('compression_threshold', 1000),
            auto_cleanup=data.get('auto_cleanup', True),
            cleanup_interval_hours=data.get('cleanup_interval_hours', 24)
        )
    
    def _parse_ai_updater_config(self, data: Dict[str, Any]) -> AIUpdaterConfig:
        """Parse AI updater configuration"""
        return AIUpdaterConfig(
            model_name=data.get('model_name', 'deepseek-chat'),
            api_base_url=data.get('api_base_url', 'https://api.deepseek.com'),
            timeout_seconds=data.get('timeout_seconds', 30),
            max_retries=data.get('max_retries', 3),
            enable_caching=data.get('enable_caching', True),
            cache_ttl_minutes=data.get('cache_ttl_minutes', 30),
            temperature=data.get('temperature', 0.6),
            max_tokens=data.get('max_tokens', 8192),
            enable_fallback=data.get('enable_fallback', True),
            fallback_strategies=data.get('fallback_strategies', [
                "RETRY_SIMPLIFIED", "TEMPLATE_BASED", "RULE_BASED"
            ])
        )
    
    def _parse_monitoring_config(self, data: Dict[str, Any]) -> MonitoringConfig:
        """Parse monitoring configuration"""
        return MonitoringConfig(
            log_level=data.get('log_level', 'INFO'),
            enable_performance_monitoring=data.get('enable_performance_monitoring', True),
            reporting_interval_minutes=data.get('reporting_interval_minutes', 60),
            enable_memory_profiling=data.get('enable_memory_profiling', False),
            max_log_file_size_mb=data.get('max_log_file_size_mb', 100),
            log_rotation_count=data.get('log_rotation_count', 5),
            enable_metrics_export=data.get('enable_metrics_export', False),
            metrics_export_path=data.get('metrics_export_path', './metrics')
        )
    
    def _parse_optimization_config(self, data: Dict[str, Any]) -> OptimizationConfig:
        """Parse optimization configuration"""
        return OptimizationConfig(
            enable_instruction_caching=data.get('enable_instruction_caching', True),
            cache_size_limit=data.get('cache_size_limit', 1000),
            enable_conditional_ai_calls=data.get('enable_conditional_ai_calls', True),
            ai_call_cooldown_seconds=data.get('ai_call_cooldown_seconds', 5),
            enable_batch_processing=data.get('enable_batch_processing', False),
            batch_size=data.get('batch_size', 10),
            enable_async_processing=data.get('enable_async_processing', False)
        )
    
    def _config_to_dict(self, config: ApplicationConfig) -> Dict[str, Any]:
        """Convert ApplicationConfig to dictionary"""
        return {
            'config_version': config.config_version,
            'environment': config.environment,
            'debug_mode': config.debug_mode,
            'state_history': {
                'max_length': config.state_history.max_length,
                'enable_compression': config.state_history.enable_compression,
                'compression_threshold': config.state_history.compression_threshold,
                'auto_cleanup': config.state_history.auto_cleanup,
                'cleanup_interval_hours': config.state_history.cleanup_interval_hours
            },
            'ai_updater': {
                'model_name': config.ai_updater.model_name,
                'api_base_url': config.ai_updater.api_base_url,
                'timeout_seconds': config.ai_updater.timeout_seconds,
                'max_retries': config.ai_updater.max_retries,
                'enable_caching': config.ai_updater.enable_caching,
                'cache_ttl_minutes': config.ai_updater.cache_ttl_minutes,
                'temperature': config.ai_updater.temperature,
                'max_tokens': config.ai_updater.max_tokens,
                'enable_fallback': config.ai_updater.enable_fallback,
                'fallback_strategies': config.ai_updater.fallback_strategies
            },
            'monitoring': {
                'log_level': config.monitoring.log_level,
                'enable_performance_monitoring': config.monitoring.enable_performance_monitoring,
                'reporting_interval_minutes': config.monitoring.reporting_interval_minutes,
                'enable_memory_profiling': config.monitoring.enable_memory_profiling,
                'max_log_file_size_mb': config.monitoring.max_log_file_size_mb,
                'log_rotation_count': config.monitoring.log_rotation_count,
                'enable_metrics_export': config.monitoring.enable_metrics_export,
                'metrics_export_path': config.monitoring.metrics_export_path
            },
            'optimization': {
                'enable_instruction_caching': config.optimization.enable_instruction_caching,
                'cache_size_limit': config.optimization.cache_size_limit,
                'enable_conditional_ai_calls': config.optimization.enable_conditional_ai_calls,
                'ai_call_cooldown_seconds': config.optimization.ai_call_cooldown_seconds,
                'enable_batch_processing': config.optimization.enable_batch_processing,
                'batch_size': config.optimization.batch_size,
                'enable_async_processing': config.optimization.enable_async_processing
            }
        }

# 全局配置实例
_global_config_loader: Optional[ConfigurationLoader] = None
_global_config: Optional[ApplicationConfig] = None

def get_config_loader() -> ConfigurationLoader:
    """Get global configuration loader instance"""
    global _global_config_loader
    if _global_config_loader is None:
        _global_config_loader = ConfigurationLoader()
    return _global_config_loader

def get_config() -> ApplicationConfig:
    """Get global configuration instance"""
    global _global_config
    if _global_config is None:
        loader = get_config_loader()
        _global_config = loader.get_config()
    return _global_config

def reload_config() -> ApplicationConfig:
    """Reload global configuration"""
    global _global_config
    loader = get_config_loader()
    _global_config = loader.reload_config()
    return _global_config

def initialize_config(config_path: Optional[str] = None) -> ApplicationConfig:
    """Initialize configuration system"""
    global _global_config_loader, _global_config
    _global_config_loader = ConfigurationLoader(config_path)
    _global_config = _global_config_loader.load_config()
    return _global_config 