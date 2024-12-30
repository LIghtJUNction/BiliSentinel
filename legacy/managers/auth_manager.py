import os
import sys
import logging
import base64
import hashlib
import json
from cryptography.fernet import Fernet
from bilibili_api import Credential, login, user, settings, sync
from bilibili_api.login import (
    login_with_password, 
    login_with_sms, 
    send_sms, 
    PhoneNumber, 
    Check
)
from utils.menu import Menu, console
from utils.constants import PBKDF2_ITERATIONS
from bilibili_api.user import User

class AuthManager:
    def __init__(self):
        self._encrypted_credential = None
        self._uid = None
        self._storage = self._init_storage()
        settings.geetest_auto_open = False
        self._load_credential()
        
    def _init_storage(self):
        """初始化凭证存储"""
        if sys.platform == "win32":
            from .storage.windows import WindowsRegistry
            return WindowsRegistry()
        elif sys.platform == "linux":
            from .storage.linux import LinuxKeyring
            return LinuxKeyring()
        elif sys.platform == "darwin":
            from .storage.macos import MacKeychain
            return MacKeychain()
        else:
            from .storage.memory import MemoryStorage
            return MemoryStorage()
            
    def _save_credential(self):
        """保存加密凭证"""
        if self._encrypted_credential and self._uid:
            self._storage.save(self._uid, self._encrypted_credential)
            
    def _load_credential(self):
        """加载加密凭证"""
        try:
            data = self._storage.load()
            if data:
                self._uid, self._encrypted_credential = data
                # 验证凭证
                credential = self._decrypt_credential(self._encrypted_credential)
                user_info = sync(user.get_self_info(credential))
                if not user_info:
                    raise ValueError("无效凭证")
        except:
            self._encrypted_credential = None
            self._uid = None
        
    def _derive_key(self, uid: str) -> bytes:
        """从UID派生加密密钥"""
        salt = b"bilibili_credential_v1"
        key = hashlib.pbkdf2_hmac(
            'sha256',
            uid.encode(),
            salt,
            iterations=PBKDF2_ITERATIONS
        )
        return base64.urlsafe_b64encode(key[:32])
        
    def _encrypt_credential(self, credential: Credential, uid: str) -> bytes:
        """加密凭证"""
        key = self._derive_key(uid)
        f = Fernet(key)
        data = {
            "sessdata": credential.sessdata,
            "bili_jct": credential.bili_jct,
            "buvid3": credential.buvid3,
            "dedeuserid": uid  # 添加 DedeUserID
        }
        return f.encrypt(json.dumps(data).encode())
        
    def _decrypt_credential(self, encrypted: bytes) -> Credential:
        """解密凭证"""
        if not self._uid:
            raise ValueError("UID未初始化")
        key = self._derive_key(self._uid)
        f = Fernet(key)
        data = json.loads(f.decrypt(encrypted))
        return Credential(
            sessdata=data["sessdata"],
            bili_jct=data["bili_jct"],
            buvid3=data["buvid3"],
            dedeuserid=data.get("dedeuserid", self._uid)  # 使用存储的UID
        )
        
    async def authenticate(self):
        """用户认证
        
        Returns:
            tuple: (credential, user_info) 如果认证成功
            None: 如果认证失败
        """
        try:
            if not self._encrypted_credential:
                choice = Menu.select(
                    "登录方式",
                    ["扫码登录(终端)", "扫码登录(窗口)", "密码登录", "验证码登录"]
                )
                
                credential = None
                
                if choice == "扫码登录(终端)":
                    console.print("\n[yellow]请使用手机扫描终端二维码登录[/yellow]")
                    credential = login.login_with_qrcode_term()
                    
                elif choice == "扫码登录(窗口)":
                    console.print("\n[yellow]请扫描弹出窗口中的二维码登录[/yellow]")
                    credential = login.login_with_qrcode()
                    
                elif choice == "密码登录":
                    username = input("\n请输入手机号/邮箱：").strip()
                    password = input("请输入密码：").strip()
                    console.print("\n[yellow]正在登录...[/yellow]")
                    c = login_with_password(username, password)
                    if isinstance(c, Check):
                        console.print("[red]需要验证,请使用扫码登录[/red]")
                        return await self.authenticate()
                    credential = c
                    
                elif choice == "验证码登录":
                    phone = input("\n请输入手机号：").strip()
                    console.print("\n[yellow]正在发送验证码...[/yellow]")
                    send_sms(PhoneNumber(phone, country="+86"))
                    code = input("请输入验证码：").strip()
                    c = login_with_sms(PhoneNumber(phone, country="+86"), code)
                    if isinstance(c, Check):
                        console.print("[red]需要验证,请使用扫码登录[/red]")
                        return await self.authenticate()
                    credential = c
                
                if not credential:
                    raise ValueError("登录失败")
                    
                # 验证凭证
                try:
                    credential.raise_for_no_bili_jct()
                    credential.raise_for_no_sessdata()
                except:
                    raise ValueError("登录凭证无效")
                
                # 获取用户信息并加密存储
                current_user = User(int(credential.dedeuserid), credential)
                user_info = await current_user.get_user_info()
                self._uid = str(user_info['mid'])
                
                # 更新credential添加DedeUserID
                credential = Credential(
                    sessdata=credential.sessdata,
                    bili_jct=credential.bili_jct,
                    buvid3=credential.buvid3,
                    dedeuserid=self._uid
                )
                
                self._encrypted_credential = self._encrypt_credential(credential, self._uid)
                self._save_credential()
                
                logging.info(f"欢迎 {user_info['name']}!")
                return credential, user_info
                
            # 使用已存储的凭证
            credential = self._decrypt_credential(self._encrypted_credential)
            current_user = User(int(credential.dedeuserid), credential)
            user_info = await current_user.get_user_info()
            if not user_info:
                self._encrypted_credential = None
                return await self.authenticate()
                
            return credential, user_info
            
        except Exception as e:
            logging.error(f"认证失败: {e}")
            self._encrypted_credential = None
            self._storage.clear()
            return await self.authenticate()