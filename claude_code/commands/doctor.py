import platform
import sys
import subprocess
import httpx
from rich.console import Console
from rich.table import Table

console = Console()


def run_doctor_diagnosis() -> str:
    """
    Runs full environment diagnosis for Python, Git, and internet connectivity.
    """
    table = Table(title="Antigravity System Diagnosis Report", show_header=True, header_style="bold blue")
    table.add_column("Audit Component", style="cyan")
    table.add_column("Status / Result", style="green")

    # 1. OS & Platform
    os_info = f"{platform.system()} {platform.release()}"
    table.add_row("Operating System", os_info)

    # 2. Python Version
    py_ver = f"{sys.version.split()[0]} (Location: {sys.executable})"
    table.add_row("Python Environment", py_ver)

    # 3. Git integration
    try:
        git_ver = subprocess.check_output(["git", "--version"], text=True, stderr=subprocess.DEVNULL).strip()
        table.add_row("Git Integration", f"Available ({git_ver})")
    except Exception:
        table.add_row("Git Integration", "[red]Not Available[/red]")

    # 4. Network check to Anthropic / OpenAI
    try:
        # Check standard API connectivity with 2 seconds timeout
        res = httpx.get("https://api.openai.com/v1/models", timeout=2.0)
        table.add_row("OpenAI API Connectivity", f"Connected (Status {res.status_code})")
    except Exception as e:
        table.add_row("OpenAI API Connectivity", f"[red]Offline / Error ({str(e)})[/red]")

    try:
        res = httpx.get("https://api.anthropic.com/v1/messages", timeout=2.0)
        # Note: 400 Bad Request is expected because we didn't send auth headers, but it proves domain connectivity!
        table.add_row("Anthropic API Connectivity", f"Connected (Status {res.status_code})")
    except Exception as e:
        table.add_row("Anthropic API Connectivity", f"[red]Offline / Error ({str(e)})[/red]")

    # Capture outputs to print
    with console.capture() as capture:
        console.print(table)
        
    return capture.get()
