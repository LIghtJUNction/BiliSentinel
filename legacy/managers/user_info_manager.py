from datetime import datetime
import logging
import msvcrt
import os
from bilibili_api import user
from bilibili_api.user import HistoryType
from utils.menu import Menu, console
from utils.rate_limiter import RateLimiter
from rich.table import Table
from rich.panel import Panel
from typing import Union, Optional
import json

class UserInfoManager:
    def __init__(self, credential):
        self.credential = credential
        self.rate_limiter = RateLimiter()

    async def _format_info_table(self, info, title="信息"):
        """格式化信息为表格"""
        table = Table(title=title, show_header=True)
        table.add_column("项目", style="cyan")
        table.add_column("内容", style="green")
        
        if isinstance(info, dict):
            if "data" in info:  # 处理历史记录
                if isinstance(info["data"], list):
                    for idx, item in enumerate(info["data"], 1):
                        table.add_row(
                            f"记录 {idx}",
                            f"{item.get('title', '未知标题')} - {item.get('author_name', '未知作者')}"
                        )
                    return table
            for key, value in info.items():
                if not isinstance(value, (dict, list)):
                    table.add_row(str(key), str(value))
        else:
            table.add_row("结果", str(info))
            
        return table

    async def _get_info(self, info_type):
        """获取信息"""
        try:
            await self.rate_limiter.wait()
            if info_type == "个人信息":
                return await user.get_self_info(self.credential)
            elif info_type == "特别关注":
                return await user.get_self_special_followings(self.credential)
            elif info_type == "悄悄关注":
                return await user.get_self_whisper_followings(self.credential)
            elif info_type == "好友列表":
                return await user.get_self_friends(self.credential)
            elif info_type == "黑名单":
                return await user.get_self_black_list(self.credential)
            elif info_type == "历史消息":
                # 修正API调用
                return await user.get_self_history_new(self.credential)
            elif info_type == "硬币数量":
                coins = await user.get_self_coins(self.credential)
                return {"硬币数量": coins}
        except Exception as e:
            logging.error(f"获取{info_type}失败: {e}")
            return None

    async def show_info_submenu(self):
        """显示个人信息子菜单"""
        while True:
            choices = [
                "账号基本信息",
                "数据统计",
                "视频投稿",
                "动态列表", 
                "特别关注",
                "悄悄关注",
                "追番追剧",
                "投稿相簿",
                "黑名单列表",
                "返回"
            ]
            
            choice = Menu.select("个人信息查询", choices)
            if choice == "返回":
                break
                
            os.system('cls' if os.name == 'nt' else 'clear')
            console.print(f"[yellow]正在获取{choice}...[/yellow]")
            
            try:
                await self.rate_limiter.wait()

                if choice == "账号基本信息":
                    await self._display_account_info()
                elif choice == "数据统计":
                    await self._display_user_stats()
                elif choice == "视频投稿":
                    await self._display_videos()
                elif choice == "动态列表":
                    await self._display_dynamics() 
                elif choice == "特别关注":
                    await self._display_special_followings()
                elif choice == "悄悄关注": 
                    await self._display_whisper_followings()
                elif choice == "追番追剧":
                    await self._display_bangumi()
                elif choice == "投稿相簿":
                    await self._display_albums()
                elif choice == "黑名单列表":
                    info = await user.get_self_black_list(self.credential)
                    await self._display_blacklist(info)

                console.print("\n[yellow]按任意键继续...[/yellow]")
                msvcrt.getch()
                
            except Exception as e:
                logging.error(f"获取{choice}失败: {e}")
                console.print(f"\n[red]获取{choice}失败: {e}[/red]")
                msvcrt.getch()

    async def _display_basic_info(self):
        """显示基础账号信息"""
        info = await user.get_self_info(self.credential)
        if not info:
            return
            
        table = Table(show_header=False)
        table.add_column("项目", style="cyan")
        table.add_column("内容", style="green")
        
        # 添加更多信息行
        details = [
            ("UID", info.get('mid')),
            ("昵称", info.get('name')),
            ("等级", f"LV{info.get('level', 0)}"),
            ("性别", info.get('sex', '保密')),
            ("生日", info.get('birthday', '未设置')),
            ("注册时间", info.get('jointime', '未知')),
            ("大会员状态", "是" if info.get('vip', {}).get('status') == 1 else "否"),
            ("个性签名", info.get('sign', '这个人很懒,什么都没写')),
            ("硬币数", await user.get_self_coins(self.credential))
        ]
        
        for item, value in details:
            table.add_row(item, str(value))
            
        console.print(Panel(table, title="[bold cyan]账号基本信息[/bold cyan]"))

    async def _display_special_followings(self):
        """显示特别关注"""
        try:
            # 获取特别关注列表 (返回的是 UID 数组)
            special_uids = await user.get_self_special_followings(
                credential=self.credential,
                pn=1,
                ps=50
            )
            
            if not special_uids:
                console.print("[yellow]暂无特别关注[/yellow]")
                return
            
            # 获取用户详细信息
            users = []
            for uid in special_uids:
                u = user.User(uid=uid, credential=self.credential)
                info = await u.get_user_info()
                relation_info = await u.get_relation_info()
                
                if info:
                    users.append({
                        "mid": uid,
                        "uname": info.get("name", "未知用户"),
                        "mtime": info.get("jointime", 0),  # 使用注册时间作为关注时间
                        "following": relation_info.get("following", 0),
                        "follower": relation_info.get("follower", 0)
                    })
                
            # 修改显示表格的列
            table = Table(show_header=True)
            table.add_column("序号", justify="center", style="cyan", width=6)
            table.add_column("用户名", style="green")
            table.add_column("UID", justify="center")
            table.add_column("关注数", justify="right")
            table.add_column("粉丝数", justify="right")
            
            # 显示前10个用户
            for idx, item in enumerate(users[:10], 1):
                table.add_row(
                    str(idx),
                    item["uname"],
                    str(item["mid"]),
                    f"{item['following']:,}",
                    f"{item['follower']:,}"
                )
            
            console.print(Panel(
                table,
                title=f"[bold cyan]特别关注 (共{len(users)}个)[/bold cyan]"
            ))
            
            # 如果有更多用户，显示分页
            if len(users) > 10:
                if Menu.confirm("是否查看下一页?"):
                    await self._display_more_special_followings(users[10:])
                
        except Exception as e:
            logging.error(f"获取特别关注失败: {e}")
            console.print(f"[red]获取特别关注失败: {e}[/red]")

    async def _display_more_special_followings(self, users):
        """分页显示更多特别关注用户"""
        page_size = 10
        total = len(users)
        pages = (total + page_size - 1) // page_size
        current_page = 1
        
        while current_page <= pages:
            start = (current_page - 1) * page_size
            end = min(start + page_size, total)
            page_users = users[start:end]
            
            table = Table(show_header=True)
            table.add_column("序号", justify="center", style="cyan", width=6)
            table.add_column("用户名", style="green")
            table.add_column("UID", justify="center")
            table.add_column("关注数", justify="right")
            table.add_column("粉丝数", justify="right")
            
            for idx, item in enumerate(page_users, start + 1):
                table.add_row(
                    str(idx),
                    item["uname"],
                    str(item["mid"]),
                    f"{item['following']:,}",
                    f"{item['follower']:,}"
                )
            
            console.print(Panel(
                table,
                title=f"[bold cyan]特别关注 (第{current_page}/{pages}页)[/bold cyan]"
            ))
            
            if current_page < pages:
                if not Menu.confirm("是否查看下一页?"):
                    break
            current_page += 1

    async def get_user_details(self, uid: str) -> tuple:
        """获取用户详细信息"""
        try:
            info = await user.get_user_info(uid)
            if not info:
                return None, None

            user_table = Table(show_header=False)
            user_table.add_column("项目", style="cyan")
            user_table.add_column("内容", style="green")

            details = [
                ("UID", uid),
                ("用户名", info['name']),
                ("等级", info.get('level', 0)),
                ("大会员", "是" if info.get('vip', {}).get('status') == 1 else "否"),
                ("关注数", f"{info.get('following', 0):,}"),
                ("粉丝数", f"{info.get('follower', 0):,}"),
                ("个性签名", info.get('sign', '无'))
            ]
            
            for item, value in details:
                user_table.add_row(item, str(value))

            return info, user_table

        except Exception as e:
            logging.error(f"获取用户 {uid} 信息失败: {e}")
            return None, None

    async def get_relation(self, uid: str) -> dict:
        """获取与用户的关系
        
        Args:
            uid (str): 用户UID
            
        Returns:
            dict: 用户关系信息
        """
        try:
            # 获取关系状态
            relation = await user.get_relation(uid)
            # 获取详细信息
            relation_info = await user.get_relation_info()
            
            if relation and relation_info:
                return {
                    "relation": relation,
                    "following": relation_info.get("following", 0),
                    "follower": relation_info.get("follower", 0),
                    "whisper": relation_info.get("whisper", 0),
                    "black": relation_info.get("black", 0)
                }
        except Exception as e:
            logging.error(f"获取用户 {uid} 关系失败: {e}")
            
        return None

    async def get_history(self, 
                         history_type: HistoryType = HistoryType.ALL,
                         ps: int = 20,
                         view_at: Optional[int] = None,
                         max_id: Optional[int] = None) -> list:
        """获取用户历史记录
        
        Args:
            history_type (HistoryType): 历史记录类型
            ps (int): 每页条数
            view_at (int, optional): 时间戳
            max_id (int, optional): 截止目标ID
            
        Returns:
            list: 历史记录列表
        """
        try:
            history = await user.get_self_history_new(
                credential=self.credential,
                _type=history_type,
                ps=ps,
                view_at=view_at,
                max=max_id
            )
            return history.get("data", {}).get("list", [])
            
        except Exception as e:
            logging.error(f"获取历史记录失败: {e}")
            return []

    async def _display_user_stats(self):
        """显示用户数据统计"""
        try:
            # 使用 get_self_info 获取基础信息
            info = await user.get_self_info(self.credential)
            
            table = Table(show_header=False)
            table.add_column("项目", style="cyan")
            table.add_column("数值", style="green")
            
            details = [
                ("等级", f"LV{info.get('level', 0)}"),
                ("硬币", f"{info.get('coins', 0):,}"),
                ("关注数", f"{info.get('following', 0):,}"),
                ("粉丝数", f"{info.get('follower', 0):,}"),
                ("动态数", f"{info.get('dynamic', 0):,}")
            ]
            
            for item, value in details:
                table.add_row(item, value)
                
            console.print(Panel(table, title="[bold cyan]数据统计[/bold cyan]"))
            
        except Exception as e:
            logging.error(f"获取数据统计失败: {e}")

    async def _display_videos(self):
        """显示视频投稿"""
        try:
            # 创建用户实例
            target = user.User(uid=self.credential.dedeuserid, credential=self.credential)
            
            # 获取视频列表
            videos = await target.get_videos()
            if not videos or "list" not in videos:
                console.print("[yellow]暂无视频投稿[/yellow]")
                return
            
            video_list = videos["list"].get("vlist", [])
            if not video_list:
                console.print("[yellow]暂无视频投稿[/yellow]")
                return
            
            table = Table(show_header=True)
            table.add_column("序号", justify="center", style="cyan", width=6)
            table.add_column("标题", style="green")
            table.add_column("播放", justify="right")
            table.add_column("弹幕", justify="right")
            table.add_column("发布时间", justify="center")
            
            for idx, video in enumerate(video_list[:10], 1):
                table.add_row(
                    str(idx),
                    video.get("title", "未知")[:30],
                    f"{video.get('play', 0):,}",
                    f"{video.get('video_review', 0):,}",
                    datetime.fromtimestamp(
                        video.get("created", 0)
                    ).strftime("%Y-%m-%d %H:%M")
                )
            
            console.print(Panel(
                table,
                title=f"[bold cyan]视频投稿 (共{len(video_list)}个)[/bold cyan]"
            ))
            
            # 分页显示
            if len(video_list) > 10:
                if Menu.confirm("是否查看下一页?"):
                    await self._display_more_videos(video_list[10:])
                
        except Exception as e:
            logging.error(f"获取视频投稿失败: {e}")
            console.print(f"[red]获取视频投稿失败: {e}[/red]")

    async def _display_more_videos(self, videos):
        """分页显示更多视频"""
        page_size = 10
        total = len(videos)
        pages = (total + page_size - 1) // page_size
        current_page = 1
        
        while current_page <= pages:
            start = (current_page - 1) * page_size
            end = min(start + page_size, total)
            page_videos = videos[start:end]
            
            table = Table(show_header=True)
            table.add_column("序号", justify="center", style="cyan", width=6)
            table.add_column("标题", style="green")
            table.add_column("播放", justify="right")
            table.add_column("弹幕", justify="right")
            table.add_column("发布时间", justify="center")
            
            for idx, video in enumerate(page_videos, start + 1):
                table.add_row(
                    str(idx),
                    video.get("title", "未知")[:30],
                    f"{video.get('play', 0):,}",
                    f"{video.get('video_review', 0):,}",
                    datetime.fromtimestamp(
                        video.get("created", 0)
                    ).strftime("%Y-%m-%d %H:%M")
                )
            
            console.print(Panel(
                table,
                title=f"[bold cyan]视频投稿 (第{current_page}/{pages}页)[/bold cyan]"
            ))
            
            if current_page < pages:
                if not Menu.confirm("是否查看下一页?"):
                    break
            current_page += 1

    async def _display_dynamics(self):
        """显示动态列表"""
        try:
            target = user.User(uid=self.credential.dedeuserid, credential=self.credential)
            dynamics = await target.get_dynamics()  # 使用旧版API可能更稳定
            
            if not dynamics or "cards" not in dynamics:
                console.print("[yellow]暂无动态[/yellow]")
                return

            table = Table(show_header=True)
            table.add_column("序号", justify="center", style="cyan", width=6)
            table.add_column("类型", style="magenta", width=10)
            table.add_column("内容", style="green")
            table.add_column("时间", justify="center", width=16)
            
            for idx, card in enumerate(dynamics["cards"][:10], 1):
                card_data = card.get("card", "{}")
                try:
                    content = json.loads(card_data).get("item", {}).get("description", "无内容")
                except:
                    content = "无法解析的内容"
                    
                pub_time = datetime.fromtimestamp(
                    card.get("desc", {}).get("timestamp", 0)
                ).strftime("%Y-%m-%d %H:%M")
                
                table.add_row(
                    str(idx),
                    str(card.get("desc", {}).get("type", "未知")),
                    content[:50] + "..." if len(content) > 50 else content,
                    pub_time
                )
            
            console.print(Panel(table, title="[bold cyan]动态列表[/bold cyan]"))
            
        except Exception as e:
            logging.error(f"获取动态列表失败: {e}")

    async def _display_whisper_followings(self):
        """显示悄悄关注"""
        try:
            # 获取悄悄关注列表
            whisper = await user.get_self_whisper_followings(
                credential=self.credential,
                pn=1,
                ps=50
            )
            
            # API返回的是一个列表
            if isinstance(whisper, list):
                await self._display_following_table(whisper, "悄悄关注")
            else:
                console.print("[yellow]暂无悄悄关注[/yellow]")
            
        except Exception as e:
            logging.error(f"获取悄悄关注失败: {e}")
            console.print(f"[red]获取悄悄关注失败: {e}[/red]")

    async def _display_bangumi(self):
        """显示追番追剧"""
        try:
            target = user.User(uid=self.credential.dedeuserid, credential=self.credential)
            bangumi = await target.get_subscribed_bangumi()
            
            if not bangumi or not bangumi.get("list"):
                console.print("[yellow]暂无追番追剧[/yellow]")
                return
                
            table = Table(show_header=True)
            table.add_column("序号", justify="center", style="cyan", width=6)
            table.add_column("标题", style="green")
            table.add_column("类型", justify="center")
            table.add_column("追番状态", justify="center")
            
            for idx, item in enumerate(bangumi["list"][:10], 1):
                table.add_row(
                    str(idx),
                    item.get("title", "未知标题"),
                    "番剧" if item.get("season_type") == 1 else "剧集",
                    item.get("progress", "未开始")
                )
                
            console.print(Panel(table, title="[bold cyan]追番追剧[/bold cyan]"))
            
        except Exception as e:
            logging.error(f"获取追番追剧失败: {e}")

    async def _display_albums(self):
        """显示投稿相簿"""
        try:
            albums = await user.get_album(self.credential)
            if not albums or "items" not in albums:
                console.print("[yellow]暂无相簿[/yellow]")
                return
                
            await self._display_album_table(albums["items"])
            
        except Exception as e:
            logging.error(f"获取投稿相簿失败: {e}")
            console.print(f"[red]获取投稿相簿失败: {e}[/red]")

    async def _display_account_info(self):
        """显示基础账号信息"""
        try:
            info = await user.get_self_info(self.credential)
            if not info:
                raise ValueError("获取用户信息失败")
                
            table = Table(show_header=False)
            table.add_column("项目", style="cyan")
            table.add_column("内容", style="green")
            
            details = [
                ("UID", info.get('mid')),
                ("昵称", info.get('name')),
                ("等级", f"LV{info.get('level', 0)}"),
                ("性别", info.get('sex', '保密')),
                ("生日", info.get('birthday', '未设置')), 
                ("注册时间", info.get('jointime', '未知')),
                ("大会员", "是" if info.get('vip', {}).get('status') == 1 else "否"),
                ("个性签名", info.get('sign', '这个人很懒,什么都没写'))
            ]
            
            for item, value in details:
                table.add_row(item, str(value))
                
            console.print(Panel(table, title="[bold cyan]账号基本信息[/bold cyan]"))
            
        except Exception as e:
            logging.error(f"获取账号信息失败: {e}")
            raise

    async def _display_user_info(self):
        """显示用户信息菜单"""
        options = {
            "视频投稿": self._display_videos,
            "动态列表": self._display_dynamics,
            "特别关注": self._display_special_followings,
            "悄悄关注": self._display_whisper_followings,
            "追番追剧": self._display_bangumi,
            "投稿相簿": self._display_albums,
            "黑名单列表": self._display_blacklist
        }
        
        while True:
            choice = Menu.select("选择要查看的信息", list(options.keys()))
            if choice == "返回":
                break
                
            await options[choice]()
            if not Menu.confirm("继续查看其他信息?"):
                break

    async def _display_blacklist(self, info):
        """显示黑名单列表"""
        try:
            if not info or "list" not in info:
                console.print("[yellow]黑名单为空[/yellow]")
                return
            
            users = info["list"]
            page_size = 10
            current_page = 1
            total_pages = (len(users) + page_size - 1) // page_size
            
            while current_page <= total_pages:
                start = (current_page - 1) * page_size
                end = min(start + page_size, len(users))
                page_users = users[start:end]
                
                table = Table(show_header=True)
                table.add_column("序号", justify="center", style="cyan", width=6)
                table.add_column("用户名", style="green")
                table.add_column("UID", justify="center")
                table.add_column("拉黑时间", justify="center")
                table.add_column("来源", justify="center")
                
                for idx, item in enumerate(page_users, start + 1):
                    table.add_row(
                        str(idx),
                        item.get("uname", "未知用户"),
                        str(item.get("mid", "未知")),
                        datetime.fromtimestamp(
                            item.get("mtime", 0)
                        ).strftime("%Y-%m-%d %H:%M"),
                        "手动拉黑" if item.get("source", 0) == 1 else "系统自动"
                    )
                
                console.print(Panel(
                    table,
                    title=f"[bold cyan]黑名单列表 (第{current_page}/{total_pages}页, 共{len(users)}个)[/bold cyan]"
                ))
                
                if current_page < total_pages:
                    if not Menu.confirm("是否查看下一页?"):
                        break
                current_page += 1
                
        except Exception as e:
            logging.error(f"显示黑名单失败: {e}")

    async def _display_more_blacklist(self, users):
        """分页显示更多黑名单用户"""
        page_size = 10
        total = len(users)
        pages = (total + page_size - 1) // page_size
        current_page = 1
        
        while current_page <= pages:
            start = (current_page - 1) * page_size
            end = min(start + page_size, total)
            page_users = users[start:end]
            
            table = Table(show_header=True)
            table.add_column("序号", justify="center", style="cyan", width=6)
            table.add_column("用户名", style="green")
            table.add_column("UID", justify="center")
            table.add_column("拉黑时间", justify="center")
            table.add_column("来源", justify="center")
            
            for idx, item in enumerate(page_users, start + 1):
                table.add_row(
                    str(idx),
                    item.get("uname", "未知用户"),
                    str(item.get("mid", "未知")),
                    datetime.fromtimestamp(
                        item.get("mtime", 0)
                    ).strftime("%Y-%m-%d %H:%M"),
                    "手动拉黑" if item.get("source", 0) == 1 else "系统自动"
                )
            
            console.print(Panel(
                table,
                title=f"[bold cyan]黑名单列表 (第{current_page}/{pages}页)[/bold cyan]"
            ))
            
            if current_page < pages:
                if not Menu.confirm("是否查看下一页?"):
                    break
            current_page += 1

    async def _display_following_table(self, users, title="关注列表"):
        """显示关注用户列表"""
        try:
            if not users:
                console.print("[yellow]列表为空[/yellow]")
                return
            
            table = Table(show_header=True)
            table.add_column("序号", justify="center", style="cyan", width=6)
            table.add_column("用户名", style="green")
            table.add_column("UID", justify="center")
            table.add_column("关注时间", justify="center")
            
            # 显示前10个用户
            for idx, item in enumerate(users[:10], 1):
                table.add_row(
                    str(idx),
                    item.get("uname", "未知用户"),
                    str(item.get("mid", "未知")),
                    datetime.fromtimestamp(
                        item.get("mtime", 0)
                    ).strftime("%Y-%m-%d %H:%M")
                )
            
            console.print(Panel(
                table,
                title=f"[bold cyan]{title} (共{len(users)}个)[/bold cyan]"
            ))
            
            # 如果有更多用户，显示分页
            if len(users) > 10:
                if Menu.confirm("是否查看下一页?"):
                    await self._display_more_followings(users[10:], title)
                
        except Exception as e:
            logging.error(f"显示{title}失败: {e}")

    async def _display_more_followings(self, users, title):
        """分页显示更多关注用户"""
        page_size = 10
        total = len(users)
        pages = (total + page_size - 1) // page_size
        current_page = 1
        
        while current_page <= pages:
            start = (current_page - 1) * page_size
            end = min(start + page_size, total)
            page_users = users[start:end]
            
            table = Table(show_header=True)
            table.add_column("序号", justify="center", style="cyan", width=6)
            table.add_column("用户名", style="green")
            table.add_column("UID", justify="center")
            table.add_column("关注时间", justify="center")
            
            for idx, item in enumerate(page_users, start + 1):
                table.add_row(
                    str(idx),
                    item.get("uname", "未知用户"),
                    str(item.get("mid", "未知")),
                    datetime.fromtimestamp(
                        item.get("mtime", 0)
                    ).strftime("%Y-%m-%d %H:%M")
                )
            
            console.print(Panel(
                table,
                title=f"[bold cyan]{title} (第{current_page}/{pages}页)[/bold cyan]"
            ))
            
            if current_page < pages:
                if not Menu.confirm("是否查看下一页?"):
                    break
            current_page += 1

    async def _display_album_table(self, albums):
        """显示相簿列表"""
        try:
            if not albums:
                console.print("[yellow]暂无相簿[/yellow]")
                return
            
            table = Table(show_header=True)
            table.add_column("序号", justify="center", style="cyan", width=6)
            table.add_column("标题", style="green")
            table.add_column("浏览", justify="right")
            table.add_column("点赞", justify="right")
            table.add_column("发布时间", justify="center")
            
            for idx, item in enumerate(albums[:10], 1):
                table.add_row(
                    str(idx),
                    item.get("title", "无标题")[:30],
                    str(item.get("view", 0)),
                    str(item.get("like", 0)),
                    datetime.fromtimestamp(
                        item.get("upload_time", 0)
                    ).strftime("%Y-%m-%d %H:%M")
                )
            
            console.print(Panel(table, title="[bold cyan]相簿列表[/bold cyan]"))
            
        except Exception as e:
            logging.error(f"显示相簿列表失败: {e}")
