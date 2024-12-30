import logging
import msvcrt
import os
import webbrowser
from bilibili_api import user
from utils.audit_history import AuditHistory
from utils.menu import Menu, console
from utils.points import PointSystem
from utils.rate_limiter import RateLimiter
from utils.audit_counter import AuditCounter
from rich.table import Table
from rich.panel import Panel
from utils.constants import (
    SCP_TYPES, AUDIT_RECORDS_DIR, MECHANICAL_RULES, 
    AUDIT_PAGE_LIMIT, TIME_WINDOW
)
import asyncio

class AuditManager:
    def __init__(self, credential, username, uid, audit_history):
        self.credential = credential
        self.username = username
        self.uid = uid
        self.audit_history = audit_history
        self.point_system = PointSystem()

    async def audit_scp(self, scp_type: str, uid: str):
        """审核指定的SCP文件"""
        try:
            # 获取待审核的UID列表
            file_path = os.path.join("blacklists", f"SCP-{scp_type}.txt")
            if not os.path.exists(file_path):
                console.print("[yellow]没有待审核的用户[/yellow]")
                return

            with open(file_path, "r", encoding="utf-8") as f:
                uids = [line.strip() for line in f if line.strip()]

            if not uids:
                console.print("[yellow]没有待审核的用户[/yellow]")
                return

            # 获取已审核记录
            audited = self.audit_history.get_audited_uids(scp_type)
            to_audit = [uid for uid in uids if uid not in audited]

            if not to_audit:
                console.print("[yellow]所有用户都已审核完成[/yellow]")
                return

            stats = {"total": len(to_audit), "keep": 0, "remove": 0}
            
            # 处理每个用户
            with console.status("[bold green]正在处理...[/bold green]") as status:
                for uid in to_audit:
                    # 获取用户详细信息
                    try:
                        target = user.User(uid=uid, credential=self.credential)
                        info = await target.get_user_info()
                        relation = await target.get_relation_info()
                        user_info = {
                            "uid": uid,
                            "uname": info.get("name", "未知"),
                            "info": info,
                            "relation": relation
                        }
                    except Exception as e:
                        user_info = {
                            "uid": uid,
                            "uname": "未知",
                            "info": None,
                            "relation": None
                        }

                    while True:
                        # 清屏
                        os.system('cls' if os.name == 'nt' else 'clear')
                        
                        # 显示用户信息面板
                        if user_info["info"] and user_info["relation"]:
                            table = Table(box=None)
                            table.add_column("项目", style="cyan")
                            table.add_column("内容")
                            
                            table.add_row("UID", str(user_info["uid"]))
                            table.add_row("用户名", user_info["info"].get("name", "未知"))
                            table.add_row("等级", f"LV{user_info['info'].get('level', 0)}")
                            table.add_row("关注数", f"{user_info['relation'].get('following', 0):,}")
                            table.add_row("粉丝数", f"{user_info['relation'].get('follower', 0):,}")
                            table.add_row("个性签名", user_info["info"].get("sign", ""))
                            
                            console.print(Panel(
                                table,
                                title=f"[bold cyan]目标信息 - {user_info['uname']}[/bold cyan]",
                                border_style="cyan"
                            ))
                        else:
                            console.print(Panel(
                                f"UID: {user_info['uid']}\n用户名: {user_info['uname']}",
                                title="[bold cyan]目标信息[/bold cyan]",
                                border_style="cyan"
                            ))

                        # 显示审核菜单
                        action = Menu.select(
                            f"审核 SCP-{scp_type}",
                            ["保留并继续", "移除并继续", "查看更多信息", "结束审核"]
                        )

                        if action == "保留并继续":
                            self.audit_history.add_record(scp_type, uid, True)
                            stats["keep"] += 1
                            console.print(f"[green]已保留: {user_info['uname']}({uid})[/green]")
                            await asyncio.sleep(0.5)
                            break
                            
                        elif action == "移除并继续":
                            self.audit_history.add_record(scp_type, uid, False)
                            stats["remove"] += 1
                            console.print(f"[yellow]已移除: {user_info['uname']}({uid})[/yellow]")
                            await asyncio.sleep(0.5)
                            break
                            
                        elif action == "查看更多信息":
                            webbrowser.open(f"https://space.bilibili.com/{uid}")
                            await asyncio.sleep(0.5)
                            continue
                            
                        elif action == "结束审核":
                            return

                    if action == "结束审核":
                        break

                    await asyncio.sleep(0.5)  # 处理下一个用户前的延迟

            # 显示审核结果
            if stats["keep"] > 0 or stats["remove"] > 0:
                points = stats["keep"] * 3  # 每审核一个用户得3分
                self.point_system.add_points(
                    self.uid,
                    points,
                    f"审核 SCP-{scp_type} ({stats['keep']} 个保留, {stats['remove']} 个移除)"
                )
                
                # 显示结果表格
                table = Table(show_header=True)
                table.add_column("项目", style="cyan")
                table.add_column("数量", justify="right", style="green")
                
                table.add_row("总计处理", str(stats["total"]))
                table.add_row("保留用户", str(stats["keep"]))
                table.add_row("移除用户", str(stats["remove"]))
                table.add_row("获得积分", f"+{points}")
                
                console.print(Panel(
                    table,
                    title="[bold cyan]审核结果[/bold cyan]"
                ))
                
                console.print("\n[yellow]按任意键继续...[/yellow]")
                msvcrt.getch()

        except Exception as e:
            logging.error(f"审核失败: {e}")
            console.print(f"\n[red]审核失败: {e}[/red]")
            console.print("\n[yellow]按任意键继续...[/yellow]")
            msvcrt.getch()