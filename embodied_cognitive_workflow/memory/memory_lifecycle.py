"""
记忆生命周期管理

实现记忆的完整生命周期：创建→使用→归档→压缩→遗忘
"""

import json
import gzip
import shutil
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import logging
from pathlib import Path

from .interfaces import IMemory, MemoryItem, MemoryLayer
from .memory_manager import MemoryManager
from .utils import calculate_importance


logger = logging.getLogger(__name__)


class LifecycleStage(Enum):
    """记忆生命周期阶段"""
    CREATED = "created"          # 创建阶段
    ACTIVE = "active"           # 活跃使用阶段
    ARCHIVED = "archived"       # 归档阶段
    COMPRESSED = "compressed"   # 压缩存储阶段
    FORGOTTEN = "forgotten"     # 遗忘阶段


@dataclass
class LifecyclePolicy:
    """生命周期策略配置"""
    # 各阶段的时间阈值
    active_duration: timedelta = timedelta(days=7)       # 活跃期持续时间
    archive_after: timedelta = timedelta(days=30)       # 归档时间阈值
    compress_after: timedelta = timedelta(days=90)      # 压缩时间阈值
    forget_after: timedelta = timedelta(days=365)       # 遗忘时间阈值
    
    # 访问频率阈值
    min_access_for_active: int = 3                      # 保持活跃的最小访问次数
    min_importance_for_archive: float = 0.3             # 归档的最小重要性
    
    # 压缩配置
    compression_level: int = 6                          # gzip压缩级别(1-9)
    
    # 归档路径
    archive_path: Path = Path("./memory_archive")
    
    def __post_init__(self):
        """确保归档路径存在"""
        self.archive_path.mkdir(parents=True, exist_ok=True)


@dataclass
class LifecycleMetadata:
    """生命周期元数据"""
    stage: LifecycleStage
    created_at: datetime
    last_accessed: datetime
    access_count: int
    stage_transitions: List[Tuple[LifecycleStage, datetime]]
    archive_path: Optional[str] = None
    compressed: bool = False
    compression_ratio: Optional[float] = None


class MemoryLifecycleManager:
    """记忆生命周期管理器"""
    
    def __init__(self, 
                 memory_manager: MemoryManager,
                 policy: Optional[LifecyclePolicy] = None):
        """
        初始化生命周期管理器
        
        Args:
            memory_manager: 记忆管理器实例
            policy: 生命周期策略
        """
        self.memory_manager = memory_manager
        self.policy = policy or LifecyclePolicy()
        self.lifecycle_metadata: Dict[str, LifecycleMetadata] = {}
        
        # 创建归档子目录
        self.archive_dirs = {
            MemoryLayer.WORKING: self.policy.archive_path / "working",
            MemoryLayer.EPISODIC: self.policy.archive_path / "episodic",
            MemoryLayer.SEMANTIC: self.policy.archive_path / "semantic"
        }
        for dir_path in self.archive_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def track_memory(self, memory_id: str, layer: MemoryLayer) -> LifecycleMetadata:
        """
        开始跟踪记忆的生命周期
        
        Args:
            memory_id: 记忆ID
            layer: 记忆层级
            
        Returns:
            生命周期元数据
        """
        now = datetime.now()
        metadata = LifecycleMetadata(
            stage=LifecycleStage.CREATED,
            created_at=now,
            last_accessed=now,
            access_count=1,
            stage_transitions=[(LifecycleStage.CREATED, now)]
        )
        
        self.lifecycle_metadata[memory_id] = metadata
        logger.info(f"Started tracking memory {memory_id} in {layer.value} layer")
        
        return metadata
    
    def update_access(self, memory_id: str) -> bool:
        """
        更新记忆访问信息
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否更新成功
        """
        if memory_id not in self.lifecycle_metadata:
            return False
        
        metadata = self.lifecycle_metadata[memory_id]
        metadata.last_accessed = datetime.now()
        metadata.access_count += 1
        
        # 如果访问频繁，可能需要提升到活跃状态
        if (metadata.stage == LifecycleStage.CREATED and 
            metadata.access_count >= self.policy.min_access_for_active):
            self._transition_stage(memory_id, LifecycleStage.ACTIVE)
        
        return True
    
    def process_lifecycle(self) -> Dict[str, List[str]]:
        """
        处理所有记忆的生命周期转换
        
        Returns:
            各阶段转换的记忆ID列表
        """
        transitions = {
            "to_active": [],
            "to_archived": [],
            "to_compressed": [],
            "to_forgotten": []
        }
        
        now = datetime.now()
        
        for memory_id, metadata in list(self.lifecycle_metadata.items()):
            age = now - metadata.created_at
            idle_time = now - metadata.last_accessed
            
            # 根据策略进行阶段转换
            if metadata.stage == LifecycleStage.CREATED:
                if metadata.access_count >= self.policy.min_access_for_active:
                    self._transition_stage(memory_id, LifecycleStage.ACTIVE)
                    transitions["to_active"].append(memory_id)
                elif age > self.policy.active_duration:
                    # 如果创建后很少访问，直接归档
                    self._archive_memory(memory_id)
                    transitions["to_archived"].append(memory_id)
            
            elif metadata.stage == LifecycleStage.ACTIVE:
                if idle_time > self.policy.archive_after:
                    self._archive_memory(memory_id)
                    transitions["to_archived"].append(memory_id)
            
            elif metadata.stage == LifecycleStage.ARCHIVED:
                if idle_time > self.policy.compress_after:
                    self._compress_memory(memory_id)
                    transitions["to_compressed"].append(memory_id)
            
            elif metadata.stage == LifecycleStage.COMPRESSED:
                if idle_time > self.policy.forget_after:
                    self._forget_memory(memory_id)
                    transitions["to_forgotten"].append(memory_id)
        
        # 记录转换统计
        total_transitions = sum(len(v) for v in transitions.values())
        if total_transitions > 0:
            logger.info(f"Lifecycle transitions: {transitions}")
        
        return transitions
    
    def _transition_stage(self, memory_id: str, new_stage: LifecycleStage):
        """
        转换记忆生命周期阶段
        
        Args:
            memory_id: 记忆ID
            new_stage: 新阶段
        """
        if memory_id not in self.lifecycle_metadata:
            return
        
        metadata = self.lifecycle_metadata[memory_id]
        old_stage = metadata.stage
        metadata.stage = new_stage
        metadata.stage_transitions.append((new_stage, datetime.now()))
        
        logger.info(f"Memory {memory_id} transitioned from {old_stage.value} to {new_stage.value}")
    
    def _archive_memory(self, memory_id: str) -> bool:
        """
        归档记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否归档成功
        """
        # 查找记忆所在层
        memory_item = None
        layer = None
        
        for memory_layer in [MemoryLayer.WORKING, MemoryLayer.EPISODIC, MemoryLayer.SEMANTIC]:
            memory = self._get_memory_by_layer(memory_layer)
            if memory.exists(memory_id):
                memory_item = memory.get(memory_id)
                layer = memory_layer
                break
        
        if not memory_item or not layer:
            logger.warning(f"Memory {memory_id} not found for archiving")
            return False
        
        # 检查重要性
        importance = calculate_importance(str(memory_item.content))
        if importance < self.policy.min_importance_for_archive:
            logger.info(f"Memory {memory_id} not important enough for archiving (importance: {importance})")
            # 直接遗忘
            self._forget_memory(memory_id)
            return True
        
        # 创建归档文件
        archive_file = self.archive_dirs[layer] / f"{memory_id}.json"
        archive_data = {
            "memory_id": memory_id,
            "layer": layer.value,
            "content": memory_item.content,
            "metadata": memory_item.metadata,
            "created_at": memory_item.timestamp.isoformat(),
            "last_accessed": memory_item.last_accessed.isoformat() if memory_item.last_accessed else memory_item.timestamp.isoformat(),
            "access_count": memory_item.access_count,
            "lifecycle_metadata": {
                "archived_at": datetime.now().isoformat(),
                "importance": importance
            }
        }
        
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(archive_data, f, ensure_ascii=False, indent=2)
        
        # 更新元数据
        metadata = self.lifecycle_metadata[memory_id]
        metadata.archive_path = str(archive_file)
        self._transition_stage(memory_id, LifecycleStage.ARCHIVED)
        
        # 从活跃存储中删除
        memory = self._get_memory_by_layer(layer)
        memory.forget(memory_id)
        
        logger.info(f"Archived memory {memory_id} to {archive_file}")
        return True
    
    def _compress_memory(self, memory_id: str) -> bool:
        """
        压缩归档的记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否压缩成功
        """
        metadata = self.lifecycle_metadata.get(memory_id)
        if not metadata or not metadata.archive_path:
            return False
        
        archive_file = Path(metadata.archive_path)
        if not archive_file.exists():
            logger.warning(f"Archive file {archive_file} not found")
            return False
        
        # 压缩文件
        compressed_file = archive_file.with_suffix('.json.gz')
        
        with open(archive_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb', compresslevel=self.policy.compression_level) as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 计算压缩比
        original_size = archive_file.stat().st_size
        compressed_size = compressed_file.stat().st_size
        compression_ratio = 1 - (compressed_size / original_size) if original_size > 0 else 0
        
        # 删除原文件
        archive_file.unlink()
        
        # 更新元数据
        metadata.archive_path = str(compressed_file)
        metadata.compressed = True
        metadata.compression_ratio = compression_ratio
        self._transition_stage(memory_id, LifecycleStage.COMPRESSED)
        
        logger.info(f"Compressed memory {memory_id}, ratio: {compression_ratio:.2%}")
        return True
    
    def _forget_memory(self, memory_id: str) -> bool:
        """
        遗忘记忆（完全删除）
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否遗忘成功
        """
        metadata = self.lifecycle_metadata.get(memory_id)
        if not metadata:
            return False
        
        # 删除归档文件
        if metadata.archive_path:
            archive_file = Path(metadata.archive_path)
            if archive_file.exists():
                archive_file.unlink()
                logger.info(f"Deleted archive file {archive_file}")
        
        # 从各层尝试删除（如果还存在）
        for layer in [MemoryLayer.WORKING, MemoryLayer.EPISODIC, MemoryLayer.SEMANTIC]:
            memory = self._get_memory_by_layer(layer)
            if memory.exists(memory_id):
                memory.forget(memory_id)
        
        # 删除生命周期元数据
        del self.lifecycle_metadata[memory_id]
        
        logger.info(f"Forgotten memory {memory_id}")
        return True
    
    def restore_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """
        从归档中恢复记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            恢复的记忆项，如果失败则返回None
        """
        metadata = self.lifecycle_metadata.get(memory_id)
        if not metadata or not metadata.archive_path:
            logger.warning(f"No archive found for memory {memory_id}")
            return None
        
        archive_file = Path(metadata.archive_path)
        if not archive_file.exists():
            logger.warning(f"Archive file {archive_file} not found")
            return None
        
        # 读取归档数据
        try:
            if metadata.compressed:
                with gzip.open(archive_file, 'rt', encoding='utf-8') as f:
                    archive_data = json.load(f)
            else:
                with open(archive_file, 'r', encoding='utf-8') as f:
                    archive_data = json.load(f)
            
            # 重建记忆项
            memory_item = MemoryItem(
                id=archive_data["memory_id"],
                content=archive_data["content"],
                metadata=archive_data["metadata"],
                timestamp=datetime.fromisoformat(archive_data["created_at"]),
                last_accessed=datetime.now(),
                access_count=archive_data["access_count"] + 1
            )
            
            # 恢复到对应层
            layer = MemoryLayer(archive_data["layer"])
            memory = self._get_memory_by_layer(layer)
            memory.store(memory_item.id, memory_item.content, memory_item.metadata)
            
            # 更新生命周期状态
            self._transition_stage(memory_id, LifecycleStage.ACTIVE)
            metadata.archive_path = None
            metadata.compressed = False
            
            logger.info(f"Restored memory {memory_id} from archive")
            return memory_item
            
        except Exception as e:
            logger.error(f"Failed to restore memory {memory_id}: {e}")
            return None
    
    def get_lifecycle_stats(self) -> Dict[str, Any]:
        """
        获取生命周期统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "total_tracked": len(self.lifecycle_metadata),
            "by_stage": {},
            "average_age": timedelta(),
            "average_access_count": 0,
            "compression_stats": {
                "total_compressed": 0,
                "average_compression_ratio": 0.0
            }
        }
        
        # 按阶段统计
        for stage in LifecycleStage:
            stats["by_stage"][stage.value] = 0
        
        total_age = timedelta()
        total_access = 0
        total_compression_ratio = 0.0
        compressed_count = 0
        
        now = datetime.now()
        
        for metadata in self.lifecycle_metadata.values():
            stats["by_stage"][metadata.stage.value] += 1
            total_age += (now - metadata.created_at)
            total_access += metadata.access_count
            
            if metadata.compressed and metadata.compression_ratio:
                compressed_count += 1
                total_compression_ratio += metadata.compression_ratio
        
        # 计算平均值
        if self.lifecycle_metadata:
            stats["average_age"] = total_age / len(self.lifecycle_metadata)
            stats["average_access_count"] = total_access / len(self.lifecycle_metadata)
        
        if compressed_count > 0:
            stats["compression_stats"]["total_compressed"] = compressed_count
            stats["compression_stats"]["average_compression_ratio"] = \
                total_compression_ratio / compressed_count
        
        return stats
    
    def _get_memory_by_layer(self, layer: MemoryLayer) -> IMemory:
        """
        获取指定层的记忆接口
        
        Args:
            layer: 记忆层级
            
        Returns:
            记忆接口
        """
        if layer == MemoryLayer.WORKING:
            return self.memory_manager.working
        elif layer == MemoryLayer.EPISODIC:
            return self.memory_manager.episodic
        elif layer == MemoryLayer.SEMANTIC:
            return self.memory_manager.semantic
        else:
            raise ValueError(f"Unknown memory layer: {layer}")
    
    def cleanup_forgotten(self, days: int = 30) -> int:
        """
        清理已遗忘的记忆档案
        
        Args:
            days: 遗忘后保留的天数
            
        Returns:
            清理的文件数量
        """
        cleaned = 0
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for archive_dir in self.archive_dirs.values():
            for file_path in archive_dir.glob("*.json*"):
                # 检查文件修改时间
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff_date:
                    # 确保对应的记忆已经被遗忘
                    memory_id = file_path.stem.replace('.json', '')
                    if memory_id not in self.lifecycle_metadata:
                        file_path.unlink()
                        cleaned += 1
                        logger.info(f"Cleaned up forgotten archive: {file_path}")
        
        return cleaned