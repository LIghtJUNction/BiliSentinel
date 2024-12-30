from typing import Optional, Tuple
import logging
from bilibili_api import Credential, login, user
from data.storage.base import BaseStorage
from data.models.user import UserInfo
from utils.exceptions import AuthError
from utils.decorators import error_handler, retry

class AuthService:
    """认证服务"""
    
    def __init__(self, storage: BaseStorage):
        self.storage = storage
        self.logger = logging.getLogger(self.__class__.__name__)
        self._credential: Optional[Credential] = None
        self._user_info: Optional[UserInfo] = None
        
    @property
    def is_authenticated(self) -> bool:
        """是否已认证"""
        return self._credential is not None
        
    @error_handler(error_types=(AuthError,))
    async def login(self) -> Tuple[Credential, UserInfo]:
        """登录流程"""
        try:
            # 尝试加载已存储的凭证
            if stored_data := await self.storage.load():
                self._credential = Credential.from_dict(stored_data["credential"])
                self._user_info = UserInfo(**stored_data["user_info"])
                if await self._verify_credential():
                    return self._credential, self._user_info
                    
            # 需要重新登录
            self._credential = await self._handle_login()
            self._user_info = await self._fetch_user_info()
            
            # 保存凭证
            await self._save_credential()
            
            return self._credential, self._user_info
            
        except Exception as e:
            raise AuthError("登录失败", cause=e)
            
    @retry(max_retries=3)
    async def _verify_credential(self) -> bool:
        """验证凭证有效性"""
        try:
            current_user = user.User(self._credential)
            user_info = await current_user.get_user_info()
            return bool(user_info)
        except:
            return False
            
    async def _handle_login(self) -> Credential:
        """处理登录过程"""
        try:
            # 使用二维码登录
            login_key = login.login_with_qrcode()
            credential = await login_key.login()
            return credential
        except Exception as e:
            raise AuthError("登录过程失败", cause=e)
            
    async def _fetch_user_info(self) -> UserInfo:
        """获取用户信息"""
        try:
            current_user = user.User(self._credential)
            info = await current_user.get_user_info()
            
            return UserInfo(
                uid=str(info["mid"]),
                name=info["name"],
                level=info["level"],
                follower=info["follower"],
                following=info["following"],
                sign=info["sign"]
            )
        except Exception as e:
            raise AuthError("获取用户信息失败", cause=e)
            
    async def _save_credential(self):
        """保存凭证"""
        try:
            data = {
                "credential": self._credential.to_dict(),
                "user_info": self._user_info.__dict__
            }
            await self.storage.save(data)
        except Exception as e:
            raise AuthError("保存凭证失败", cause=e) 