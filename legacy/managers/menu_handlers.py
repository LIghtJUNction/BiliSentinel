from datetime import datetime
import logging
import msvcrt
import os
from managers.audit_manager import AuditManager
from managers.auth_manager import AuthManager
from utils.audit_history import AuditHistory
from utils.menu import Menu, console
from managers.blacklist_manager import BlacklistManager
from managers.user_info_manager import UserInfoManager
from utils.points import PointSystem
from rich.table import Table
from rich.panel import Panel
from bilibili_api import user
from bilibili_api.user import User, RelationType
import asyncio

class MenuHandlers:
    def __init__(self, credential, follower_count, username, uid):
        self.credential = credential
        self.follower_count = follower_count
        self.username = username
        self.uid = uid
        self.user_info_manager = UserInfoManager(credential)
        self.blacklist_manager = BlacklistManager(credential, username, uid)
        self.audit_history = AuditHistory(credential, uid)
        self.point_system = PointSystem()
        self.auth_manager = AuthManager()

    async def handle_main_menu(self):
        """处理主菜单"""
        while True:
            choice = Menu.select(
                "主菜单",
                ["A. 个人信息查询", "B. 黑名单管理", "C. 开始审核", 
                 "D. 查看积分记录", "E. 排行榜", "F. 安全设置", "Q. 退出"]
            )
            
            if choice == "A. 个人信息查询":
                await self.handle_user_info_menu()
            elif choice == "B. 黑名单管理":
                await self.handle_blacklist_menu()
            elif choice == "C. 开始审核":
                await self.handle_audit_menu()
            elif choice == "D. 查看积分记录":
                try:
                    # 获取积分记录
                    records = self.point_system.view_records(self.uid)
                    
                    if not records:
                        console.print("[yellow]暂无积分记录[/yellow]")
                        console.print("\n[yellow]按任意键继续...[/yellow]")
                        msvcrt.getch()
                    else:
                        # 构建表格
                        table = Table(show_header=True)
                        table.add_column("时间", style="cyan")
                        table.add_column("积分", justify="right", style="green")
                        table.add_column("原因", style="yellow")
                        
                        for record in records:
                            table.add_row(
                                datetime.fromtimestamp(record["time"]).strftime("%Y-%m-%d %H:%M"),
                                str(record["points"]),
                                record["reason"]
                            )
                        
                        # 显示总积分和记录
                        total_points = self.point_system.get_user_points(self.uid)
                        console.print(Panel(
                            table,
                            title=f"[bold cyan]积分记录 (总积分: {total_points})[/bold cyan]"
                        ))
                        
                        console.print("\n[yellow]按任意键继续...[/yellow]")
                        msvcrt.getch()
                except Exception as e:
                    logging.error(f"查看积分记录失败: {e}")
                    console.print(f"[red]查看积分记录失败: {e}[/red]")
                    console.print("\n[yellow]按任意键继续...[/yellow]")
                    msvcrt.getch()
                    
            elif choice == "E. 排行榜":
                try:
                    # 获取排行榜
                    leaderboard = self.point_system.get_leaderboard()
                    
                    if not leaderboard:
                        console.print("[yellow]暂无排行数据[/yellow]")
                        console.print("\n[yellow]按任意键继续...[/yellow]")
                        msvcrt.getch()
                    else:
                        # 构建表格
                        table = Table(show_header=True)
                        table.add_column("排名", justify="center", style="cyan", width=6)
                        table.add_column("用户", style="green")
                        table.add_column("积分", justify="right", style="yellow")
                        
                        for idx, entry in enumerate(leaderboard[:10], 1):  # 只显示前10名
                            table.add_row(
                                str(idx),
                                entry["uid"],  # 理想情况下这里应该显示用户名
                                str(entry["points"])
                            )
                        
                        console.print(Panel(
                            table,
                            title="[bold cyan]积分排行榜[/bold cyan]"
                        ))
                        
                        console.print("\n[yellow]按任意键继续...[/yellow]")
                        msvcrt.getch()
                except Exception as e:
                    logging.error(f"查看排行榜失败: {e}")
                    console.print(f"[red]查看排行榜失败: {e}[/red]")
                    console.print("\n[yellow]按任意键继续...[/yellow]")
                    msvcrt.getch()
                    
            elif choice == "F. 安全设置":
                await self.handle_security_menu()
            else:  # Q. 退出
                break

    async def handle_audit_menu(self):
        """处理审核菜单"""
        audit_manager = AuditManager(
            credential=self.credential,
            username=self.username,
            uid=self.uid,
            audit_history=self.audit_history
        )
        
        while True:
            choice = Menu.select(
                "开始审核",
                ["审核SCP-0000", "审核SCP-1989", "审核SCP-3666", "返回"]
            )
            
            if choice == "返回":
                break
                
            try:
                scp_type = choice.split("-")[1]
                await audit_manager.audit_scp(scp_type, self.uid)  # 传递当前用户uid
                
            except Exception as e:
                logging.error(f"执行操作出错: {e}")
                console.print("\n[red]操作失败，按任意键继续...[/red]")
                msvcrt.getch()

    async def handle_blacklist_menu(self):
        """处理黑名单菜单"""
        try:
            blacklist = await user.get_self_black_list(self.credential)
            users = blacklist.get("list", [])
            total = len(users)
            
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                
                if users:
                    # 显示黑名单列表
                    page_size = 10
                    total_pages = (total + page_size - 1) // page_size
                    current_page = 1
                    
                    # 显示当前页
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
                        title=f"[bold cyan]黑名单列表 (第{current_page}/{total_pages}页, 共{total}个)[/bold cyan]"
                    ))
                else:
                    console.print("[yellow]当前黑名单为空[/yellow]")

                # 显示操作菜单
                choices = ["贡献黑名单", "应用黑名单", "全部取消拉黑"]
                if users:  # 只在有黑名单数据时显示切页选项
                    choices.insert(0, "切页")
                choices.append("返回")  # 添加返回选项
                
                choice = Menu.select("黑名单管理", choices)
                
                if choice == "切页" and users:
                    current_page = current_page + 1 if current_page < total_pages else 1
                elif choice == "贡献黑名单":
                    await self.blacklist_manager.process_blacklist_contribution()
                elif choice == "应用黑名单":
                    await self.blacklist_manager.apply_blacklist()
                elif choice == "全部取消拉黑":
                    if not users:
                        console.print("[yellow]黑名单为空，无需取消[/yellow]")
                        await asyncio.sleep(1)
                    else:
                        await self.blacklist_manager.unblock_all()
                else:  # 返回
                    break
                
        except Exception as e:
            logging.error(f"获取黑名单失败: {e}")

    async def view_more_blacklist(self, users):
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

    async def handle_security_menu(self):
        """处理安全菜单"""
        while True:
            choice = Menu.select(
                "安全设置",
                ["注销当前登录", "清除所有凭证", "返回"]
            )
            
            if choice == "注销当前登录":
                if Menu.confirm("确定要注销当前登录吗?"):
                    self.auth_manager._storage.clear()
                    console.print("[yellow]已注销当前登录[/yellow]")
                    return "LOGOUT"
                    
            elif choice == "清除所有凭证":
                if Menu.confirm("确定要清除所有登录凭证吗? (全保存在本地/如果不放心可以删除)"):
                    self.auth_manager._storage.clear()
                    # 清除注册表/keyring中的所有凭证
                    console.print("[yellow]已清除所有登录凭证[/yellow]")
                    return "LOGOUT"
                    
            elif choice == "返回":
                break