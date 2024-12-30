import os
import json
import aiofiles
from typing import Any, Optional
from .base import BaseStorage
from utils.exceptions import StorageError

class FileStorage(BaseStorage):
    """文件存储实现"""
    
    def __init__(self, directory: str):
        super().__init__()
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
        
    def _get_path(self, key: str) -> str:
        """获取文件路径"""
        return os.path.join(self.directory, f"{key}.json")
        
    async def save(self, data: Any, key: str = "default") -> bool:
        """保存数据到文件"""
        try:
            path = self._get_path(key)
            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            return True
        except Exception as e:
            raise StorageError(f"保存数据失败: {e}")
            
    async def load(self, key: str = "default") -> Optional[Any]:
        """从文件加载数据"""
        try:
            path = self._get_path(key)
            if not os.path.exists(path):
                return None
                
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            raise StorageError(f"加载数据失败: {e}")
            
    async def delete(self, key: str) -> bool:
        """删除文件"""
        try:
            path = self._get_path(key)
            if os.path.exists(path):
                os.remove(path)
            return True
        except Exception as e:
            raise StorageError(f"删除数据失败: {e}")
            
    async def exists(self, key: str) -> bool:
        """检查文件是否存在"""
        return os.path.exists(self._get_path(key)) 