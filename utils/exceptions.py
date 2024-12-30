from typing import Optional

class BilibiliBlacklistError(Exception):
    """基础异常类"""
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause

class AuthError(BilibiliBlacklistError):
    """认证相关错误"""
    pass

class StorageError(BilibiliBlacklistError):
    """存储相关错误"""
    pass

class BlacklistError(BilibiliBlacklistError):
    """黑名单相关错误"""
    pass

class AuditError(BilibiliBlacklistError):
    """审核相关错误"""
    pass

class UIError(BilibiliBlacklistError):
    """界面相关错误"""
    pass 