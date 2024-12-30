from abc import ABC, abstractmethod
from typing import Any, Optional
import logging

class BaseStorage(ABC):
    """存储基类"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def save(self, data: Any) -> bool:
        """保存数据"""
        pass
        
    @abstractmethod
    async def load(self) -> Optional[Any]:
        """加载数据"""
        pass
        
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除数据"""
        pass
        
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查数据是否存在"""
        pass 