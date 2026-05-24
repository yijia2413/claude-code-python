from typing import Tuple, Dict, Any
from rich.console import Console

from claude_code.tools.file_undo import pop_and_undo
from claude_code.commands.doctor import run_doctor_diagnosis
from claude_code.commands.bug_hunter import run_bug_hunter_analysis

console = Console()

# Defined commands and descriptions
COMMANDS_HELP = {
    "/help": "显示此帮助菜单",
    "/clear": "清空对话会话历史记录",
    "/exit": "退出终端会话",
    "/undo": "撤销上一次的文件编辑/写入操作",
    "/doctor": "运行系统诊断（Python/Git/网络连通性）",
    "/bug": "启动 Bug Hunter 自动扫描诊断开发错误",
}


def handle_slash_command(command: str, state: dict) -> Tuple[bool, dict]:
    """
    Parses and routes slash commands.
    Returns a tuple: (handled_bool, updated_state)
    """
    cmd = command.strip().split()[0]

    if cmd not in COMMANDS_HELP:
        console.print(f"[danger]错误: 未知指令 '{cmd}'。输入 /help 查看支持的指令。[/danger]")
        return True, state

    if cmd == "/exit":
        # Handled in cli.py directly, return False here
        return False, state

    if cmd == "/help":
        console.print("\n[bold blue]支持的命令行快捷指令 (Slash Commands)：[/bold blue]")
        for k, v in COMMANDS_HELP.items():
            console.print(f"  [bold cyan]{k:<10}[/bold cyan] : {v}")
        console.print()
        return True, state

    if cmd == "/clear":
        # Handled in cli.py but reset state here as well
        state = {
            "messages": [],
            "current_working_directory": state.get("current_working_directory"),
            "plan": "",
            "summarized_history": "",
        }
        console.print("[info]会话已成功清空。[/info]")
        return True, state

    if cmd == "/undo":
        res = pop_and_undo()
        console.print(f"[info]{res}[/info]")
        return True, state

    if cmd == "/doctor":
        res = run_doctor_diagnosis()
        console.print(res)
        return True, state

    if cmd == "/bug":
        cwd = state.get("current_working_directory")
        res = run_bug_hunter_analysis(cwd)
        console.print(res)
        return True, state

    return True, state
