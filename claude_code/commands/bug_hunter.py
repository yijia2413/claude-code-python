import os
import subprocess
from rich.console import Console
from rich.panel import Panel

console = Console()


def run_bug_hunter_analysis(cwd: str) -> str:
    """
    Runs automated pytest dry run to scan for failures and tracebacks,
    offering quick debugging guidance.
    """
    console.print("[info]Bug Hunter is scanning workspace for active issues...[/info]")
    
    try:
        # Run pytest dry run or command to locate errors
        res = subprocess.run(
            [".venv/bin/pytest", "--collect-only"],
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=10,
        )
        
        if res.returncode != 0:
            err_msg = f"[danger]Pytest Collection Failed![/danger]\n\n[red]{res.stderr or res.stdout}[/red]"
            panel = Panel(err_msg, title="Bug Hunter Report", border_style="red")
        else:
            panel = Panel("[green]No collection failures found. Pytest suite is ready to run.[/green]\nTip: Run [bold].venv/bin/pytest[/bold] to check full runtime verification.", title="Bug Hunter Report", border_style="green")
            
    except Exception as e:
        panel = Panel(f"Error running Bug Hunter: {str(e)}", title="Bug Hunter Report", border_style="red")

    with console.capture() as capture:
        console.print(panel)
        
    return capture.get()
