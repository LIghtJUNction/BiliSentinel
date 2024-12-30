import keyring
from .base import CredentialStorage

class LinuxKeyring(CredentialStorage):
    def __init__(self):
        self.service_name = "bilibili_blacklist"
        self.account = "default"
        
    def save(self, uid: str, credential: bytes) -> bool:
        """保存到系统keyring"""
        try:
            keyring.set_password(
                self.service_name,
                self.account,
                f"{uid}:{credential.hex()}"
            )
            return True
        except:
            return False
            
    def load(self) -> tuple[str, bytes]:
        """从系统keyring加载"""
        try:
            data = keyring.get_password(self.service_name, self.account)
            if data:
                uid, cred_hex = data.split(":", 1)
                return uid, bytes.fromhex(cred_hex)
        except:
            pass
        return None, None
        
    def clear(self) -> None:
        """清除keyring中的凭证"""
        try:
            keyring.delete_password(self.service_name, self.account)
        except:
            pass