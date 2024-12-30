from .base import CredentialStorage

class MemoryStorage(CredentialStorage):
    def __init__(self):
        self._data = None
        
    def save(self, uid: str, credential: bytes) -> bool:
        """内存中保存凭证"""
        self._data = (uid, credential)
        return True
        
    def load(self) -> tuple[str, bytes]:
        """从内存加载凭证"""
        return self._data if self._data else (None, None)
        
    def clear(self) -> None:
        """清除内存中的凭证"""
        self._data = None