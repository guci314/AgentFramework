"""
记忆管理系统工具函数
"""

import hashlib
import re
import uuid
from datetime import datetime
from typing import Set, List, Any
import json


class DateTimeEncoder(json.JSONEncoder):
    """支持datetime的JSON编码器"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def safe_json_dumps(obj: Any) -> str:
    """
    安全的JSON序列化，支持datetime等对象
    
    Args:
        obj: 要序列化的对象
        
    Returns:
        JSON字符串
    """
    return json.dumps(obj, cls=DateTimeEncoder, ensure_ascii=False)


def generate_memory_id(prefix: str = "mem") -> str:
    """
    生成唯一的记忆ID
    
    Args:
        prefix: ID前缀
        
    Returns:
        唯一ID
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    unique_part = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{unique_part}"


def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度（简单实现）
    
    Args:
        text1: 文本1
        text2: 文本2
        
    Returns:
        相似度分数（0-1）
    """
    # 转换为小写
    text1 = text1.lower()
    text2 = text2.lower()
    
    # 提取单词
    words1 = set(re.findall(r'\w+', text1))
    words2 = set(re.findall(r'\w+', text2))
    
    # 计算Jaccard相似度
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)


def extract_keywords(text: str, max_keywords: int = 10) -> Set[str]:
    """
    从文本中提取关键词（简单实现）
    
    Args:
        text: 输入文本
        max_keywords: 最大关键词数量
        
    Returns:
        关键词集合
    """
    # 转换为小写
    text = text.lower()
    
    # 提取单词
    words = re.findall(r'\w+', text)
    
    # 过滤停用词（简化版）
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'been', 'be',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
        'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which',
        'when', 'where', 'why', 'how', 'all', 'each', 'every', 'some', 'any'
    }
    
    # 统计词频
    word_freq = {}
    for word in words:
        if len(word) > 2 and word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # 选择频率最高的词作为关键词
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    keywords = set(word for word, _ in sorted_words[:max_keywords])
    
    return keywords


def serialize_content(content: Any) -> str:
    """
    序列化内容为字符串
    
    Args:
        content: 任意内容
        
    Returns:
        序列化后的字符串
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, (dict, list)):
        return json.dumps(content, ensure_ascii=False, default=str)
    else:
        return str(content)


def calculate_importance(content: Any, metadata: dict = None) -> float:
    """
    计算记忆项的重要性（0-1）
    
    Args:
        content: 记忆内容
        metadata: 元数据
        
    Returns:
        重要性分数
    """
    importance = 0.5  # 基础分数
    
    # 基于内容长度
    content_str = serialize_content(content)
    if len(content_str) > 500:
        importance += 0.1
    
    # 基于元数据
    if metadata:
        # 如果有错误标记，提高重要性
        if metadata.get('has_error'):
            importance += 0.2
        
        # 如果是决策点，提高重要性
        if metadata.get('is_decision'):
            importance += 0.2
        
        # 如果有明确的重要性标记
        if 'importance' in metadata:
            importance = metadata['importance']
    
    # 确保在0-1范围内
    return max(0.0, min(1.0, importance))


def merge_metadata(meta1: dict, meta2: dict) -> dict:
    """
    合并两个元数据字典
    
    Args:
        meta1: 第一个元数据
        meta2: 第二个元数据
        
    Returns:
        合并后的元数据
    """
    merged = meta1.copy()
    
    for key, value in meta2.items():
        if key in merged:
            # 如果都是列表，合并它们
            if isinstance(merged[key], list) and isinstance(value, list):
                merged[key] = list(set(merged[key] + value))
            # 如果都是字典，递归合并
            elif isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = merge_metadata(merged[key], value)
            # 否则使用新值
            else:
                merged[key] = value
        else:
            merged[key] = value
    
    return merged


def format_memory_display(item: 'MemoryItem', verbose: bool = False) -> str:
    """
    格式化记忆项用于显示
    
    Args:
        item: 记忆项
        verbose: 是否显示详细信息
        
    Returns:
        格式化的字符串
    """
    lines = []
    
    # 基本信息
    lines.append(f"ID: {item.id}")
    lines.append(f"Timestamp: {item.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Importance: {item.importance:.2f}")
    lines.append(f"Access Count: {item.access_count}")
    
    # 内容摘要
    content_str = serialize_content(item.content)
    if len(content_str) > 100 and not verbose:
        content_str = content_str[:100] + "..."
    lines.append(f"Content: {content_str}")
    
    # 元数据
    if verbose and item.metadata:
        lines.append("Metadata:")
        for key, value in item.metadata.items():
            lines.append(f"  {key}: {value}")
    
    return "\n".join(lines)