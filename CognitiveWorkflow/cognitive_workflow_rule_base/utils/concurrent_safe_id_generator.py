#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并发安全ID生成器

为多工作流引擎并发运行提供安全的唯一ID生成机制。
"""

import threading
import time
import hashlib
import os
import uuid
from typing import Set, Optional
from datetime import datetime
from pathlib import Path


class ConcurrentSafeIdGenerator:
    """
    并发安全的ID生成器
    
    特性：
    1. 进程内唯一性保证（内存锁）
    2. 进程间唯一性保证（文件锁）
    3. 时间戳+随机+进程ID组合
    4. 冲突检测和重试机制
    """
    
    _instance = None
    _lock = threading.Lock()
    _generated_ids: Set[str] = set()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.process_id = os.getpid()
            self.thread_id = threading.get_ident()
            self.counter = 0
            self.lock_dir = Path("./.cognitive_workflow_data/locks")
            self.lock_dir.mkdir(parents=True, exist_ok=True)
            self._initialized = True
    
    def generate_workflow_id(self, goal: str, max_retries: int = 10) -> str:
        """
        生成并发安全的工作流ID
        
        Args:
            goal: 工作流目标
            max_retries: 最大重试次数
            
        Returns:
            str: 唯一的工作流ID
            
        Raises:
            RuntimeError: 如果超过最大重试次数仍然冲突
        """
        for attempt in range(max_retries):
            workflow_id = self._generate_unique_workflow_id(goal)
            
            # 检查内存中的冲突
            with self._lock:
                if workflow_id not in self._generated_ids:
                    # 检查文件系统中的冲突
                    if self._check_file_system_uniqueness(workflow_id):
                        # 创建锁文件确保唯一性
                        if self._acquire_id_lock(workflow_id):
                            self._generated_ids.add(workflow_id)
                            return workflow_id
            
            # 如果冲突，等待一小段时间后重试
            time.sleep(0.001 * (attempt + 1))  # 指数退避
        
        raise RuntimeError(f"无法在{max_retries}次重试后生成唯一工作流ID")
    
    def generate_rule_set_id(self, goal: str) -> str:
        """生成规则集ID"""
        base_hash = hashlib.md5(goal.encode('utf-8')).hexdigest()[:8]
        timestamp = int(time.time() * 1000000)  # 微秒级时间戳
        return f"ruleset_{base_hash}_{timestamp}_{self.process_id}_{self._get_next_counter()}"
    
    def generate_state_id(self, workflow_id: str, iteration: int) -> str:
        """生成状态ID"""
        timestamp = int(time.time() * 1000000)  # 微秒级时间戳
        return f"{workflow_id}_state_{iteration}_{timestamp}_{self._get_next_counter()}"
    
    def generate_execution_id(self, rule_id: str) -> str:
        """生成执行记录ID"""
        timestamp = int(time.time() * 1000000)  # 微秒级时间戳
        rule_hash = hashlib.md5(rule_id.encode('utf-8')).hexdigest()[:6]
        return f"exec_{rule_hash}_{timestamp}_{self.process_id}_{self._get_next_counter()}"
    
    def release_workflow_id(self, workflow_id: str) -> None:
        """释放工作流ID（工作流完成时调用）"""
        with self._lock:
            self._generated_ids.discard(workflow_id)
        
        # 删除锁文件
        lock_file = self.lock_dir / f"{workflow_id}.lock"
        try:
            if lock_file.exists():
                lock_file.unlink()
        except Exception:
            pass  # 忽略删除锁文件的错误
    
    def _generate_unique_workflow_id(self, goal: str) -> str:
        """生成基础的工作流ID"""
        # 清理目标字符串，保留前20个字符
        clean_goal = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in goal)[:20]
        
        # 高精度时间戳（包含毫秒和微秒）
        now = datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%M%S') + f"_{now.microsecond:06d}"
        
        # 进程和线程信息
        process_info = f"{self.process_id}_{self.thread_id}"
        
        # 计数器
        counter = self._get_next_counter()
        
        # 随机组件
        random_suffix = uuid.uuid4().hex[:8]
        
        return f"workflow_{clean_goal}_{timestamp}_{process_info}_{counter}_{random_suffix}"
    
    def _get_next_counter(self) -> int:
        """获取下一个计数器值"""
        self.counter += 1
        return self.counter
    
    def _check_file_system_uniqueness(self, workflow_id: str) -> bool:
        """检查文件系统中的唯一性"""
        # 检查状态文件
        state_dir = Path("./.cognitive_workflow_data/states")
        if state_dir.exists():
            for state_file in state_dir.glob(f"state_{workflow_id}*"):
                if state_file.exists():
                    return False
        
        # 检查规则集文件
        rules_dir = Path("./.cognitive_workflow_data/rules")
        if rules_dir.exists():
            for rules_file in rules_dir.glob(f"*{workflow_id}*"):
                if rules_file.exists():
                    return False
        
        return True
    
    def _acquire_id_lock(self, workflow_id: str) -> bool:
        """获取ID锁"""
        lock_file = self.lock_dir / f"{workflow_id}.lock"
        
        try:
            # 使用排他方式创建锁文件
            with open(lock_file, 'x') as f:
                f.write(f"{self.process_id}_{self.thread_id}_{datetime.now().isoformat()}")
            return True
        except FileExistsError:
            # 锁文件已存在，说明ID被其他进程使用
            return False
        except Exception:
            # 其他错误，为安全起见返回False
            return False


class SafeFileOperations:
    """
    安全的文件操作工具类
    
    提供原子性文件写入和冲突处理机制。
    """
    
    @staticmethod
    def atomic_write_json(file_path: Path, data: dict, max_retries: int = 3) -> bool:
        """
        原子性写入JSON文件
        
        Args:
            file_path: 文件路径
            data: 要写入的数据
            max_retries: 最大重试次数
            
        Returns:
            bool: 是否写入成功
        """
        import json
        import tempfile
        import shutil
        
        for attempt in range(max_retries):
            try:
                # 确保目录存在
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 写入临时文件
                with tempfile.NamedTemporaryFile(
                    mode='w', 
                    encoding='utf-8',
                    dir=file_path.parent,
                    delete=False,
                    suffix='.tmp'
                ) as temp_file:
                    json.dump(data, temp_file, ensure_ascii=False, indent=2)
                    temp_file.flush()
                    os.fsync(temp_file.fileno())  # 强制写入磁盘
                    temp_path = temp_file.name
                
                # 原子性重命名
                shutil.move(temp_path, file_path)
                return True
                
            except Exception as e:
                # 清理临时文件
                try:
                    if 'temp_path' in locals():
                        Path(temp_path).unlink(missing_ok=True)
                except Exception:
                    pass
                
                if attempt == max_retries - 1:
                    raise e
                
                # 短暂等待后重试
                time.sleep(0.01 * (attempt + 1))
        
        return False
    
    @staticmethod
    def safe_read_json(file_path: Path, max_retries: int = 3) -> Optional[dict]:
        """
        安全读取JSON文件
        
        Args:
            file_path: 文件路径
            max_retries: 最大重试次数
            
        Returns:
            Optional[dict]: 读取的数据，失败返回None
        """
        import json
        
        for attempt in range(max_retries):
            try:
                if not file_path.exists():
                    return None
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
                    
            except (json.JSONDecodeError, IOError) as e:
                if attempt == max_retries - 1:
                    raise e
                
                # 短暂等待后重试
                time.sleep(0.01 * (attempt + 1))
        
        return None
    
    @staticmethod
    def check_file_conflict(file_path: Path) -> bool:
        """
        检查文件是否存在冲突
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否存在冲突
        """
        if not file_path.exists():
            return False
        
        # 检查文件是否被锁定或正在写入
        try:
            # 尝试以排他模式打开文件
            with open(file_path, 'r+'):
                pass
            return False
        except (PermissionError, IOError):
            # 文件被锁定，存在冲突
            return True


# 全局单例实例
id_generator = ConcurrentSafeIdGenerator()