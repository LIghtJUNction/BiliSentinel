from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
import msvcrt
import os

console = Console()

class Menu:
    @staticmethod
    def select(title: str, options: list, info_panel=None) -> str:
        """显示选择菜单
        
        Args:
            title: 菜单标题
            options: 选项列表
            info_panel: 要显示在菜单上方的信息面板
            
        Returns:
            str: 选中的选项
        """
        current = 0
        
        def render():
            # 清屏
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # 如果有信息面板，先显示它
            if info_panel:
                console.print(info_panel)
            
            # 显示菜单
            menu_items = []
            for idx, option in enumerate(options):
                if idx == current:
                    menu_items.append(f"[cyan]→ {option}[/cyan]")
                else:
                    menu_items.append(f"  {option}")
            
            console.print(Panel(
                "\n".join(menu_items),
                title=f"[bold cyan]{title}[/bold cyan]"
            ))
            console.print("↑↓ 选择 | Enter 确认 | ESC 返回")

        with Live(auto_refresh=False) as live:
            while True:
                render()
                live.refresh()
                
                # 获取按键
                key = msvcrt.getch()
                
                if key == b'\xe0':  # 方向键前缀
                    key = msvcrt.getch()
                    if key == b'H':  # 上
                        current = (current - 1) % len(options)
                    elif key == b'P':  # 下
                        current = (current + 1) % len(options)
                elif key == b'\r':  # 回车
                    return options[current]
                elif key == b'\x1b':  # ESC
                    return "返回"

    @staticmethod
    def confirm(message: str) -> bool:
        """显示确认对话框"""
        return Prompt.ask(message, choices=["y", "n"], default="n") == "y"