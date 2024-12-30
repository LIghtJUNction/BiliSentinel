import os
import sys
import asyncio
import logging
import nest_asyncio
from bilibili_api import login, user, sync
from bilibili_api.user import RelationType, User
from utils.menu import Menu, console
from utils.rate_limiter import RateLimiter
from managers.menu_handlers import MenuHandlers
from managers.auth_manager import AuthManager
from managers.blacklist_manager import BlacklistManager

class QRCodeFilter(logging.Filter):
    """过滤重复的二维码轮询日志"""
    def __init__(self):
        super().__init__()
        self.last_qrcode_msg = None
        
    def filter(self, record):
        if "qrcode/poll" in record.msg:
            if self.last_qrcode_msg == record.msg:
                return False
            self.last_qrcode_msg = record.msg
        return True

class ProgressFilter(logging.Filter):
    """进度和消息过滤器"""
    def __init__(self):
        super().__init__()
        self.last_msg = None
        self.progress = console.status("[bold green]正在处理...[/bold green]", spinner="dots")
        
    def filter(self, record):
        if "HTTP Request" in record.msg:
            return record.levelno < logging.INFO  # 仅过滤INFO级别及以下
            
        # 处理二维码消息
        if "qrcode/poll" in record.msg:
            if self.last_msg == record.msg:
                return False
            self.last_msg = record.msg

            if "扫描二维码" in record.msg:
                console.print("\n[bold yellow]请使用手机扫描二维码登录[/bold yellow]")
            elif "点下确认" in record.msg:
                console.print("\n[b,ld yellow]请在手机上确认登录[/bold yellow]")
            return False
            
        # 显示API请求进度
        if "get_user_info" in record.msg:
            with self.progress:
                self.progress.update("[bold green]正在获取用户信息...[/bold green]")
            return False
        return True

class Application:
    def __init__(self):
        self.setup_logging()
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            logging.warning("nest_asyncio 未安装")
        self.auth_manager = AuthManager()
        self.menu_handlers = None

    @staticmethod
    def setup_logging():
        """配置日志"""
        handler = logging.StreamHandler(sys.stdout)
        handler.addFilter(ProgressFilter())
        
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[handler]
        )

    async def run(self):
        """应用主程序"""
        try:
            while True:
                # 认证
                auth_result = await self.auth_manager.authenticate()
                if not auth_result:
                    logging.error("认证失败")
                    return
                    
                credential, user_info = auth_result
                
                follower_count = user_info.get('follower', 0)
                username = user_info.get('name', '')
                uid = str(user_info.get('mid', ''))
                
                # 初始化菜单处理器
                self.menu_handlers = MenuHandlers(
                    credential=credential,
                    follower_count=follower_count, 
                    username=username,
                    uid=uid
                )
                
                await self.menu_handlers.handle_main_menu()
                
        except Exception as e:
            logging.error(f"程序运行出错: {e}")
            raise

def main():
    """程序入口"""
    try:
        app = Application()
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logging.info("程序被用户中断")
    except Exception as e:
        logging.error(f"程序异常退出: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
