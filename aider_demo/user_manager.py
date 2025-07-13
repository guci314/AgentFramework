from typing import Dict, Optional

class UserManager:
    """用户管理类，用于管理用户信息的增删改查"""
    
    def __init__(self) -> None:
        """初始化用户管理器，创建一个空字典存储用户"""
        self.users: Dict[str, Dict] = {}
    
    def add_user(self, username: str, user_info: Dict) -> None:
        """
        添加用户到管理器中
        
        Args:
            username: 用户名，作为唯一标识
            user_info: 包含用户信息的字典
            
        Raises:
            ValueError: 如果用户名已存在
        """
        if username in self.users:
            raise ValueError(f"用户名 {username} 已存在")
        self.users[username] = user_info
    
    def remove_user(self, username: str) -> Optional[Dict]:
        """
        从管理器中移除用户
        
        Args:
            username: 要移除的用户名
            
        Returns:
            被移除的用户信息字典，如果用户不存在则返回None
        """
        return self.users.pop(username, None)
