import winreg
from .base import CredentialStorage

class WindowsRegistry(CredentialStorage):
    def __init__(self):
        self.key_path = r"Software\BilibiliBlacklist"
        
    def save(self, uid: str, credential: bytes) -> bool:
        """保存到注册表"""
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.key_path)
            winreg.SetValueEx(key, uid, 0, winreg.REG_BINARY, credential)
            winreg.CloseKey(key)
            return True
        except:
            return False
            
    def load(self) -> tuple[str, bytes]:
        """从注册表加载"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.key_path,
                0,
                winreg.KEY_READ
            )
            i = 0
            while True:
                try:
                    name, data, type_ = winreg.EnumValue(key, i)
                    if type_ == winreg.REG_BINARY:
                        return name, data
                    i += 1
                except WindowsError:
                    break
            winreg.CloseKey(key)
        except WindowsError:
            pass
        return None, None
        
    def clear(self) -> None:
        """清除注册表中的凭证"""
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, self.key_path)
        except WindowsError:
            pass