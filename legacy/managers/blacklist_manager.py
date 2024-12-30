from datetime import datetime
import msvcrt
import os
import logging
import webbrowser
from bilibili_api import user
from bilibili_api.user import RelationType, User
from utils.audit_history import AuditHistory
from utils.menu import Menu, console
from utils.points import PointSystem
from utils.rate_limiter import RateLimiter
from rich.table import Table
from rich.panel import Panel
from utils.counter import SCPCounter
from utils.constants import (
    BLACKLIST_DIR, MAX_BLACKLIST_NORMAL, 
    MAX_BLACKLIST_VIP, SCP_FILES, POINT_RULES
)
import asyncio
import random
from rich.live import Live

class BlacklistManager:
    def __init__(self, credential, username, uid):
        self.credential = credential
        self.username = username
        self.uid = uid
        self.blacklist_dir = "blacklists"
        self.rate_limiter = RateLimiter()
        self.point_system = PointSystem()  # 初始化积分系统
        
        # 确保黑名单目录存在
        if not os.path.exists(self.blacklist_dir):
            os.makedirs(self.blacklist_dir)

    async def process_blacklist_contribution(self):
        """处理黑名单贡献"""
        try:
            # 获取当前黑名单
            blacklist = await user.get_self_black_list(self.credential)
            if not blacklist.get("list"):
                console.print("[yellow]当前黑名单为空[/yellow]")
                return
            
            total = len(blacklist["list"])
            console.print(f"\n[yellow]共发现 {total} 个黑名单用户[/yellow]\n")
            
            # 选择要贡献的黑名单
            scp_type = Menu.select(
                "选择要贡献的黑名单",
                ["SCP-0000", "SCP-1989", "SCP-3666", "返回"]
            )
            
            if scp_type == "返回":
                return
            
            scp_type = scp_type.split("-")[1]
            existing_uids = self._get_scp_file_uids(scp_type)
            
            stats = {"total": total, "added": 0, "skipped": 0}
            
            # 处理每个用户
            with console.status("[bold green]正在处理...[/bold green]") as status:
                for entry in blacklist["list"]:
                    uid = str(entry["mid"])
                    uname = entry.get("uname", uid)
                    
                    if uid in existing_uids:
                        stats["skipped"] += 1
                        console.print(f"[yellow]已存在，跳过: {uname}({uid})[/yellow]")
                        continue

                    # 获取用户详细信息
                    try:
                        target = user.User(uid=uid, credential=self.credential)
                        info = await target.get_user_info()
                        relation = await target.get_relation_info()
                        user_info = {
                            "uid": uid,
                            "uname": uname,
                            "info": info,
                            "relation": relation
                        }
                    except Exception as e:
                        user_info = {
                            "uid": uid,
                            "uname": uname,
                            "info": None,
                            "relation": None
                        }

                    # 构建信息面板
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
                        
                        info_panel = Panel(
                            table,
                            title=f"[bold cyan]目标信息 - {user_info['uname']}[/bold cyan]",
                            border_style="cyan"
                        )
                    else:
                        info_panel = Panel(
                            f"UID: {user_info['uid']}\n用户名: {user_info['uname']}",
                            title="[bold cyan]目标信息[/bold cyan]",
                            border_style="cyan"
                        )

                    while True:
                        # 使用新的菜单方法，传入信息面板
                        action = Menu.select(
                            "选择操作",
                            ["添加到黑名单", "跳过此用户", "打开用户主页", "结束贡献"],
                            info_panel=info_panel
                        )
                        
                        if action == "添加到黑名单":
                            file_path = os.path.join(self.blacklist_dir, f"SCP-{scp_type}.txt")
                            with open(file_path, "a", encoding="utf-8") as f:
                                f.write(f"{uid}\n")
                            stats["added"] += 1
                            console.print(f"[green]已添加: {uname}({uid})[/green]")
                            await asyncio.sleep(0.5)
                            break
                            
                        elif action == "跳过此用户":
                            stats["skipped"] += 1
                            console.print(f"[yellow]已跳过: {uname}({uid})[/yellow]")
                            await asyncio.sleep(0.5)
                            break
                            
                        elif action == "打开用户主页":
                            webbrowser.open(f"https://space.bilibili.com/{uid}")
                            await asyncio.sleep(0.5)
                            continue
                            
                        elif action == "结束贡献":
                            return  # 直接结束整个贡献流程

                    if action == "结束贡献":
                        break

                    await asyncio.sleep(0.5)  # 处理下一个用户前的延迟

            # 显示结果和添加积分
            if stats["added"] > 0:
                points = POINT_RULES["CONTRIBUTE"][f"SCP_{scp_type}"] * stats["added"]
                self.point_system.add_points(
                    self.uid,
                    points,
                    f"贡献 {stats['added']} 个用户到 SCP-{scp_type}"
                )
                
                # 显示结果表格
                table = Table(show_header=True)
                table.add_column("项目", style="cyan")
                table.add_column("数量", justify="right", style="green")
                
                table.add_row("总计处理", str(stats["total"]))
                table.add_row("新增用户", str(stats["added"]))
                table.add_row("已存在跳过", str(stats["skipped"]))
                table.add_row("获得积分", f"+{points}")
                
                console.print(Panel(
                    table,
                    title="[bold cyan]贡献结果[/bold cyan]"
                ))
            
            console.print("\n[yellow]按任意键继续...[/yellow]")
            msvcrt.getch()
            
        except Exception as e:
            logging.error(f"处理黑名单贡献失败: {e}")
            console.print(f"\n[red]处理失败: {e}[/red]")
            console.print("\n[yellow]按任意键继续...[/yellow]")
            msvcrt.getch()

    async def get_blacklist_info(self, uid: str):
        """获取黑名单用户信息"""
        try:
            target_user = User(int(uid), self.credential)
            info = await target_user.get_relation_info()
            return {
                "uname": info.get("uname", "未知用户"),
                "mid": uid,
                "mtime": info.get("mtime", 0),
                "source": info.get("source", 0)
            }
        except Exception as e:
            logging.error(f"获取用户信息失败: {e}")
            return None

    async def apply_blacklist(self):
        """应用黑名单"""
        try:
            # 显示SCP文件列表和说明
            table = Table(show_header=True)
            table.add_column("SCP编号", style="cyan", width=10)
            table.add_column("说明", style="green")
            
            table.add_row("SCP-0000", "社区共建黑名单，经由人工验证")
            table.add_row("SCP-1989", "机器自动收集的人机黑名单，未经广泛验证")
            table.add_row("SCP-3666", "机器自动收集的麦片黑名单，未经广泛验证")

            console.print(Panel(table, title="[bold cyan]可用黑名单列表[/bold cyan]"))

            # 选择要应用的黑名单
            scp_type = Menu.select(
                "选择要应用的黑名单",
                ["SCP-0000", "SCP-1989", "SCP-3666", "返回"]
            )
            
            if scp_type == "返回":
                return

            # 选择应用范围
            scope = Menu.select(
                "选择应用范围",
                ["关注列表", "粉丝列表", "全部", "返回"]
            )
            
            if scope == "返回":
                return

            # 根据选择的范围询问额外操作
            additional_actions = []
            if scope == "粉丝列表":
                action = Menu.select(
                    "额外操作",
                    [
                        "仅拉黑",
                        "拉黑并移除粉丝",
                        "返回"
                    ]
                )
                if action == "返回":
                    return
                if action == "拉黑并移除粉丝":
                    additional_actions.append(RelationType.REMOVE_FANS)

            elif scope == "关注列表":
                action = Menu.select(
                    "额外操作",
                    [
                        "仅拉黑",
                        "拉黑并取消关注",
                        "返回"
                    ]
                )
                if action == "返回":
                    return
                if action == "拉黑并取消关注":
                    additional_actions.append(RelationType.UNSUBSCRIBE)

            elif scope == "全部":
                action = Menu.select(
                    "额外操作",
                    [
                        "仅拉黑",
                        "拉黑并移除粉丝",
                        "拉黑并取消关注",
                        "拉黑并同时执行以上操作",
                        "返回"
                    ]
                )
                if action == "返回":
                    return
                if action == "拉黑并移除粉丝":
                    additional_actions.append(RelationType.REMOVE_FANS)
                elif action == "拉黑并取消关注":
                    additional_actions.append(RelationType.UNSUBSCRIBE)
                elif action == "拉黑并同时执行以上操作":
                    additional_actions.extend([RelationType.REMOVE_FANS, RelationType.UNSUBSCRIBE])

            # 读取选定的SCP黑名单
            file_path = os.path.join(self.blacklist_dir, f"{scp_type}.txt")
            if not os.path.exists(file_path):
                console.print(f"[yellow]{scp_type}文件不存在[/yellow]")
                return

            with open(file_path, "r", encoding="utf-8") as f:
                blacklist_uids = set(line.strip() for line in f if line.strip())

            if not blacklist_uids:
                console.print(f"[yellow]{scp_type}黑名单为空[/yellow]")
                return

            total = len(blacklist_uids)
            
            # 显示确认提示
            console.print(f"\n[yellow]将从{scp_type}中读取{total}个用户进行拉黑[/yellow]")
            console.print("[yellow]为避免触发风控，操作将会有一定延迟[/yellow]")
            if not Menu.confirm("是否继续?"):
                return

            # 初始化统计
            stats = {
                "total": total,
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "details": []
            }

            # 执行拉黑
            with console.status("[bold green]正在处理...[/bold green]") as status:
                for idx, uid in enumerate(blacklist_uids, 1):
                    try:
                        target_user = User(int(uid), self.credential)
                        status.update(f"[bold green]正在处理 ({idx}/{total}): {uid}[/bold green]")
                        
                        # 等待速率限制
                        await self.rate_limiter.wait()

                        # 获取用户信息
                        try:
                            user_info = await target_user.get_user_info()
                            uname = user_info.get("name", uid)
                        except:
                            uname = uid

                        # 检查是否已经拉黑
                        relation_info = await target_user.get_relation_info()
                        if relation_info.get("attribute") == 128:  # 128表示已拉黑
                            stats["skipped"] += 1
                            console.print(f"[yellow]用户已在黑名单中: {uname}({uid})[/yellow]")
                            continue

                        # 执行拉黑
                        await target_user.modify_relation(RelationType.BLOCK)
                        stats["success"] += 1
                        console.print(f"[cyan]已拉黑用户: {uname}({uid})[/cyan]")

                        # 执行额外操作
                        for action in additional_actions:
                            await self.rate_limiter.wait()
                            await target_user.modify_relation(action)
                            action_name = "移除粉丝" if action == RelationType.REMOVE_FANS else "取消关注"
                            console.print(f"[cyan]已{action_name}: {uname}({uid})[/cyan]")
                            
                        # 添加随机延迟(2-4秒)以避免请求过快
                        delay = random.uniform(2, 4)
                        await asyncio.sleep(delay)
                        
                    except Exception as e:
                        stats["failed"] += 1
                        stats["details"].append({
                            "uname": uname if 'uname' in locals() else uid,
                            "uid": uid,
                            "reason": str(e)
                        })
                        logging.error(f"拉黑用户{uid}失败: {e}")
                        # 出错时增加延迟
                        await asyncio.sleep(5)

                # 显示处理结果
                self._display_results(scp_type, stats)

        except Exception as e:
            logging.error(f"应用黑名单失败: {e}")

    def _display_results(self, scp_type: str, stats: dict):
        """显示处理结果"""
        # 创建结果表格
        table = Table(show_header=True)
        table.add_column("项目", style="cyan")
        table.add_column("数量", justify="right", style="green")
        
        table.add_row("黑名单总数", str(stats["total"]))
        table.add_row("处理用户数", str(stats["processed"]))
        table.add_row("成功拉黑", str(stats["success"]))
        table.add_row("拉黑失败", str(stats["failed"]))
        table.add_row("已在黑名单", str(stats["skipped"]))
        
        console.print(Panel(
            table,
            title=f"[bold cyan]{scp_type} 处理结果[/bold cyan]"
        ))

        # 显示失败详情
        if stats["failed"] > 0:
            failed_table = Table(show_header=True)
            failed_table.add_column("用户名", style="red")
            failed_table.add_column("UID", style="red")
            failed_table.add_column("原因", style="yellow")
            
            for detail in stats["details"]:
                if detail["status"] == "failed":
                    failed_table.add_row(
                        detail["uname"],
                        detail["uid"],
                        detail["reason"]
                    )
            
            console.print(Panel(
                failed_table,
                title="[bold red]失败详情[/bold red]"
            ))

    async def _process_following(self, blacklist_uids: set, stats: dict) -> None:
        """处理关注列表"""
        page = 1
        current_user = User(int(self.credential.dedeuserid), self.credential)
        
        try:
            while True:
                following = await current_user.get_following_list(pn=page)
                if not following or "list" not in following:
                    break
                
                for user_info in following["list"]:
                    uid = str(user_info["mid"])
                    uname = user_info.get("uname", uid)
                    stats["processed"] += 1
                    
                    if uid in blacklist_uids:
                        result = await self._block_user(uid)
                        if result["success"]:
                            stats["success"] += 1
                            console.print(f"[cyan]已拉黑用户: {uname}({uid})[/cyan]")
                        else:
                            stats["failed"] += 1
                            stats["details"].append({
                                "uname": uname,
                                "uid": uid,
                                "status": "failed",
                                "reason": result["reason"]
                            })
                    else:
                        stats["skipped"] += 1
                
                if page * 20 >= following.get("total", 0):
                    break
                page += 1
                await asyncio.sleep(1)
                
        except Exception as e:
            logging.error(f"处理关注列表失败: {e}")

    async def _process_followers(self, blacklist_uids: set, stats: dict) -> None:
        """处理粉丝列表"""
        page = 1
        current_user = User(int(self.credential.dedeuserid), self.credential)
        
        try:
            while True:
                followers = await current_user.get_followers_list(pn=page)
                if not followers or "list" not in followers:
                    break
                
                for user_info in followers["list"]:
                    uid = str(user_info["mid"])
                    uname = user_info.get("uname", uid)
                    stats["processed"] += 1
                    
                    if uid in blacklist_uids:
                        result = await self._block_user(uid)
                        if result["success"]:
                            stats["success"] += 1
                            console.print(f"[cyan]已拉黑用户: {uname}({uid})[/cyan]")
                        else:
                            stats["failed"] += 1
                            stats["details"].append({
                                "uname": uname,
                                "uid": uid,
                                "status": "failed",
                                "reason": result["reason"]
                            })
                    else:
                        stats["skipped"] += 1
                
                if page * 20 >= followers.get("total", 0):
                    break
                page += 1
                await asyncio.sleep(1)
                
        except Exception as e:
            logging.error(f"处理粉丝列表失败: {e}")

    async def _block_user(self, uid: str) -> dict:
        """拉黑用户"""
        try:
            target_user = User(int(uid), self.credential)
            current_user = User(int(self.credential.dedeuserid), self.credential)
            
            # 检查是否已经拉黑
            relation_info = await target_user.get_relation_info()
            if relation_info.get("attribute") == 128:
                return {
                    "success": False,
                    "reason": "用户已在黑名单中"
                }
            
            # 获取粉丝数并设置对应的限制
            user_info = await current_user.get_user_info()
            follower_count = user_info.get("follower", 0)
            max_limit = self.max_blacklist_vip if follower_count >= 10000 else self.max_blacklist_normal

            # 检查拉黑数量限制
            if self.current_blacklist_count >= max_limit:
                limit_msg = "1000" if follower_count < 10000 else "10000"
                return {
                    "success": False,
                    "reason": f"已达到最大拉黑数量限制({limit_msg}人)"
                }

            # 执行拉黑
            await target_user.modify_relation(RelationType.BLOCK)
            self.current_blacklist_count += 1  # 更新计数
            
            return {
                "success": True,
                "reason": ""
            }
        except Exception as e:
            return {
                "success": False,
                "reason": str(e)
            }

    async def unblock_all(self):
        """取消所有拉黑"""
        try:
            # 获取当前黑名单
            blacklist = await user.get_self_black_list(self.credential)
            users = blacklist.get("list", [])
            
            if not users:
                console.print("[yellow]当前黑名单为空[/yellow]")
                return

            total = len(users)
            
            # 显示确认提示
            console.print(f"[yellow]即将取消拉黑 {total} 个用户[/yellow]")
            console.print("[yellow]为避免触发风控，操作将会有一定延迟[/yellow]")
            if not Menu.confirm("是否继续?"):
                return

            # 初始化统计
            stats = {
                "total": total,
                "success": 0,
                "failed": 0,
                "details": []
            }

            # 执行取消拉黑
            with console.status("[bold green]正在处理...[/bold green]") as status:
                for idx, user_info in enumerate(users, 1):
                    uid = str(user_info["mid"])
                    target_user = User(int(uid), self.credential)
                    uname = user_info.get("uname", uid)
                    
                    try:
                        status.update(f"[bold green]正在处理 ({idx}/{total}): {uname}[/bold green]")
                        
                        # 等待速率限制
                        await self.rate_limiter.wait()

                        # 执行取消拉黑 - 使用 UNBLOCK 来取消拉黑
                        await target_user.modify_relation(RelationType.UNBLOCK)
                        stats["success"] += 1
                        console.print(f"[cyan]已取消拉黑: {uname}({uid})[/cyan]")
                        
                        # 添加随机延迟(2-4秒)以避免请求过快
                        delay = random.uniform(2, 4)
                        await asyncio.sleep(delay)
                        
                    except Exception as e:
                        stats["failed"] += 1
                        stats["details"].append({
                            "uname": uname,
                            "uid": uid,
                            "reason": str(e)
                        })
                        logging.error(f"取消拉黑用户{uid}失败: {e}")
                        # 出错时增加延迟
                        await asyncio.sleep(5)

                # 显示处理结果
                self._display_unblock_results(stats)

        except Exception as e:
            logging.error(f"取消拉黑失败: {e}")

    def _display_unblock_results(self, stats: dict):
        """显示取消拉黑结果"""
        # 创建结果表格
        table = Table(show_header=True)
        table.add_column("项目", style="cyan")
        table.add_column("数量", justify="right", style="green")
        
        table.add_row("总计处理", str(stats["total"]))
        table.add_row("成功取消", str(stats["success"]))
        table.add_row("取消失败", str(stats["failed"]))
        
        console.print(Panel(
            table,
            title="[bold cyan]取消拉黑结果[/bold cyan]"
        ))

        # 显示失败详情
        if stats["failed"] > 0:
            failed_table = Table(show_header=True)
            failed_table.add_column("用户名", style="red")
            failed_table.add_column("UID", style="red")
            failed_table.add_column("原因", style="yellow")
            
            for detail in stats["details"]:
                failed_table.add_row(
                    detail["uname"],
                    detail["uid"],
                    detail["reason"]
                )
            
            console.print(Panel(
                failed_table,
                title="[bold red]失败详情[/bold red]"
            ))

    def _get_scp_file_uids(self, scp_type: str) -> set:
        """获取SCP文件中的所有UID
        
        Args:
            scp_type: SCP类型 (0000/1989/3666)
            
        Returns:
            set: 文件中的UID集合
        """
        try:
            file_path = os.path.join(self.blacklist_dir, f"SCP-{scp_type}.txt")
            if not os.path.exists(file_path):
                return set()
            
            with open(file_path, "r", encoding="utf-8") as f:
                return {line.strip() for line in f if line.strip()}
            
        except Exception as e:
            logging.error(f"读取SCP-{scp_type}文件失败: {e}")
            return set()

    def _display_user_info(self, user_info):
        """显示用户信息面板"""
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
