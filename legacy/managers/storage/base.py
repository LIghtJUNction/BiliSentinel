from abc import ABC, abstractmethod

class CredentialStorage(ABC):
    @abstractmethod
    def save(self, uid: str, credential: bytes) -> bool:
        """保存凭证"""
        pass
        
    @abstractmethod
    def load(self) -> tuple[str, bytes]:
        """加载凭证"""
        pass
        
    @abstractmethod
    def clear(self) -> None:
        """清除凭证"""
        pass