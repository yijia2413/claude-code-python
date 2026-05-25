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
    "/ps": "列出所有后台并发运行的守护任务",
    "/logs": "查看后台守护任务日志，如 /logs 1",
    "/kill": "强行终止后台守护任务，如 /kill 1",
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

    if cmd == "/ps":
        from claude_code.daemon.task_manager import task_manager
        tasks = task_manager.list_tasks()
        if not tasks:
            console.print("[info]目前没有后台运行的任务。[/info]")
            return True, state
        
        from rich.table import Table
        table = Table(title="[bold blue]后台守护任务列表[/bold blue]")
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Command", style="green")
        table.add_column("CWD", style="dim yellow")
        table.add_column("Status", style="bold")
        table.add_column("PID", style="magenta")
        table.add_column("Elapsed (s)", style="blue", justify="right")

        for t in tasks:
            status_color = "green" if t["status"] == "RUNNING" else ("blue" if t["status"] == "COMPLETED" else "red")
            status_str = f"[{status_color}]{t['status']}[/{status_color}]"
            if t["status"] == "FAILED" and t["exit_code"] is not None:
                status_str += f" ({t['exit_code']})"
            table.add_row(
                str(t["id"]),
                t["command"],
                t["cwd"],
                status_str,
                str(t["pid"]) if t["pid"] else "-",
                str(t["elapsed"])
            )
        console.print(table)
        return True, state

    if cmd == "/logs":
        parts = command.strip().split()
        if len(parts) < 2:
            console.print("[danger]错误: 请指定任务 ID。用法: /logs <id>[/danger]")
            return True, state
        try:
            task_id = int(parts[1])
        except ValueError:
            console.print("[danger]错误: 任务 ID 必须是整数。[/danger]")
            return True, state

        from claude_code.daemon.task_manager import task_manager
        from rich.panel import Panel
        log_content = task_manager.get_task_log(task_id)
        console.print(Panel(
            log_content or "(日志暂无内容)",
            title=f"[bold blue]任务 {task_id} 日志输出 (尾部100行)[/bold blue]",
            border_style="cyan"
        ))
        return True, state

    if cmd == "/kill":
        parts = command.strip().split()
        if len(parts) < 2:
            console.print("[danger]错误: 请指定任务 ID。用法: /kill <id>[/danger]")
            return True, state
        try:
            task_id = int(parts[1])
        except ValueError:
            console.print("[danger]错误: 任务 ID 必须是整数。[/danger]")
            return True, state

        from claude_code.daemon.task_manager import task_manager
        success = task_manager.kill_task(task_id)
        if success:
            console.print(f"[info]已成功终止后台任务 {task_id}。[/info]")
        else:
            console.print(f"[danger]错误: 无法终止任务 {task_id}（可能不存在或已结束）。[/danger]")
        return True, state

    return True, state
