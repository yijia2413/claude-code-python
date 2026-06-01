import argparse
import os
import sys
import asyncio
from typing import List

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.theme import Theme

from claude_code.agent import create_agent_graph

# Custom rich theme for high-end CLI aesthetics
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
    "thought": "dim white italic",
    "tool": "bold green",
    "agent": "bold blue",
    "user": "bold yellow",
})
console = Console(theme=custom_theme)


def print_banner(cwd: str):
    banner_text = f"""[bold blue]Antigravity CLI[/bold blue] [dim]v0.1.0[/dim]
[dim]Re-implementing Claude Code with Python + LangGraph (Async Engine)[/dim]

[bold yellow]CWD:[/bold yellow] [green]{cwd}[/green]
[dim]Commands: [bold]/clear[/bold] to reset, [bold]/exit[/bold] or [bold]Ctrl+C[/bold] to quit.[/dim]"""
    console.print(Panel(banner_text, border_style="blue", expand=False))


def format_thought_block(content: str) -> str:
    """
    Renders thought blocks beautifully.
    """
    return f"[thought]Thinking...[/thought]\n{content}"


async def run_agent_loop(graph, state: dict, user_input: str) -> dict:
    """
    Streams the LangGraph steps to show tools executing and agent thinking asynchronously.
    """
    state["messages"].append(HumanMessage(content=user_input))

    console.print("\n[bold agent]Antigravity[/bold agent] is analyzing...")

    # Run the compiled async graph stream
    async for event in graph.astream(state, stream_mode="updates"):
        for node_name, node_update in event.items():
            if node_name == "agent":
                # Agent responded
                latest_msg = node_update["messages"][-1]
                state["messages"].append(latest_msg)

                # Render thinking/content beautifully
                if latest_msg.content:
                    console.print(Markdown(latest_msg.content))

                # Render scheduled tool calls
                if latest_msg.tool_calls:
                    for call in latest_msg.tool_calls:
                        console.print(
                            f"[tool]Tool Call:[/tool] [bold]{call['name']}[/bold](args: [dim]{call['args']}[/dim])"
                        )

            elif node_name == "tools":
                # Tools executed
                tool_msgs = node_update["messages"]
                for msg in tool_msgs:
                    state["messages"].append(msg)
                    # Check if bash changed directory
                    if msg.name == "execute_bash_tool":
                        for line in msg.content.split("\n"):
                            if line.startswith("[new working directory]"):
                                state["current_working_directory"] = line.replace(
                                    "[new working directory]", ""
                                ).strip()

                console.print(f"[bold green]✓ Tools execution completed.[/bold green]")
                
            elif node_name == "compact":
                # Compact happened
                state["messages"] = node_update["messages"]
                state["summarized_history"] = node_update.get("summarized_history", "")
                console.print("[info]Context window compacted successfully.[/info]")

    return state


async def main_async():
    parser = argparse.ArgumentParser(description="Antigravity developer companion CLI.")
    parser.add_argument(
        "prompt", nargs="?", default=None, help="The initial prompt to execute."
    )
    parser.add_argument(
        "-p",
        "--print",
        action="store_true",
        help="Print response and exit (non-interactive mode).",
    )
    parser.add_argument(
        "--bare",
        action="store_true",
        help="Minimal mode: skip environment checks and dynamic prompts.",
    )
    args = parser.parse_args()

    # Load credentials validation
    api_key = os.environ.get("CLAUDE_API_KEY")
    base_url = os.environ.get("CLAUDE_BASE_URL")
    model_name = os.environ.get("CLAUDE_MODEL_NAME")

    # If CLI is running in --bare mode, skip Keychain checks and input prompts
    if not args.bare:
        from claude_code.keyring.auth import get_api_key, set_api_key, get_base_url, get_model_name
        
        # 1. Load missing variables from secure storage
        if not api_key:
            api_key = get_api_key()
            if api_key:
                os.environ["CLAUDE_API_KEY"] = api_key
                console.print("[info]✓ 已从系统安全凭证管理器 (Keychain) 成功免密加载 CLAUDE_API_KEY。[/info]")

        if not base_url:
            base_url = get_base_url()
            if base_url:
                os.environ["CLAUDE_BASE_URL"] = base_url
                console.print(f"[info]✓ 已从系统安全凭证管理器 (Keychain) 成功加载 CLAUDE_BASE_URL: {base_url}[/info]")

        if not model_name:
            model_name = get_model_name()
            if model_name:
                os.environ["CLAUDE_MODEL_NAME"] = model_name
                console.print(f"[info]✓ 已从系统安全凭证管理器 (Keychain) 成功加载 CLAUDE_MODEL_NAME: {model_name}[/info]")

        # 2. If still missing API Key and NOT in non-interactive mode, prompt interactive session to bind it
        if not api_key and not args.print and not args.prompt:
            console.print("[warning]提示: 未检测到环境变量 CLAUDE_API_KEY。[/warning]")
            try:
                # Prompt API KEY securely using prompt_toolkit's session
                from prompt_toolkit import prompt as pk_prompt
                api_key_input = pk_prompt("请输入您的 CLAUDE_API_KEY (隐式输入): ", is_password=True).strip()
                if api_key_input:
                    api_key = api_key_input
                    os.environ["CLAUDE_API_KEY"] = api_key
                    
                    # Ask if user wants to save in keychain
                    save_choice = pk_prompt("是否安全存储至系统 Keychain？下一次运行将免输入。 (y/n) [y]: ").strip().lower()
                    if save_choice in ("", "y", "yes"):
                        if set_api_key(api_key):
                            console.print("[info]✓ API Key 已安全存储至 Keychain。[/info]")
                        else:
                            console.print("[warning]⚠️ 无法将 API Key 写入 Keychain (可能是当前系统无凭证后端)。[/warning]")
                else:
                    console.print("[danger]Error: CLAUDE_API_KEY is not configured and cannot be empty.[/danger]")
                    sys.exit(1)
            except KeyboardInterrupt:
                console.print("\n[info]操作已取消。[/info]")
                sys.exit(1)
        elif not api_key:
            # Fallback for headless non-interactive mode
            console.print(
                "[danger]Error: CLAUDE_API_KEY is not configured in non-interactive mode.[/danger]",
                style="bold red",
            )
            console.print(
                "Please configure your environment: export CLAUDE_API_KEY='your-key'"
            )
            sys.exit(1)

    graph = create_agent_graph()
    current_cwd = os.getcwd()

    # Setup core conversation state
    state = {
        "messages": [],
        "current_working_directory": current_cwd,
        "plan": "",
        "agent_id": "main",
        "permission_mode": "default",
        "summarized_history": ""
    }

    # Handle Print / Non-interactive Mode
    if args.print or args.prompt:
        prompt = args.prompt
        if not prompt:
            # Read from stdin if prompt is empty in print mode
            prompt = sys.stdin.read().strip()
        
        if not prompt:
            console.print("[danger]Error: No prompt provided for print mode.[/danger]")
            sys.exit(1)

        await run_agent_loop(graph, state, prompt)
        sys.exit(0)

    # Interactive Mode (Default)
    print_banner(current_cwd)
    
    # Store command prompt history locally
    history_file = os.path.expanduser("~/.claude_py_history")
    session = PromptSession(history=FileHistory(history_file))

    while True:
        try:
            cwd = state.get("current_working_directory", os.getcwd())
            prompt_str = f"claude-py:{os.path.basename(cwd)} $ "
            user_input = await session.prompt_async(prompt_str)
            user_input = user_input.strip()

            if not user_input:
                continue

            if user_input.startswith("/"):
                from claude_code.commands.manager import handle_slash_command
                handled, state = handle_slash_command(user_input, state)
                if not handled:
                    # User requested exit
                    console.print("[info]Goodbye![/info]")
                    break
                continue

            # Run agent processing
            state = await run_agent_loop(graph, state, user_input)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[info]Exiting session. Goodbye![/info]")
            break

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
