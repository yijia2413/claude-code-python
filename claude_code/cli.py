import argparse
import os
import sys
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
[dim]Re-implementing Claude Code with Python + LangGraph[/dim]

[bold yellow]CWD:[/bold yellow] [green]{cwd}[/green]
[dim]Commands: [bold]/clear[/bold] to reset, [bold]/exit[/bold] or [bold]Ctrl+C[/bold] to quit.[/dim]"""
    console.print(Panel(banner_text, border_style="blue", expand=False))


def format_thought_block(content: str) -> str:
    """
    Renders thought blocks beautifully.
    """
    return f"[thought]Thinking...[/thought]\n{content}"


def run_agent_loop(graph, state: dict, user_input: str) -> dict:
    """
    Streams the LangGraph steps to show tools executing and agent thinking.
    """
    state["messages"].append(HumanMessage(content=user_input))

    console.print("\n[bold agent]Antigravity[/bold agent] is analyzing...")

    # Run the compiled graph stream
    for event in graph.stream(state, stream_mode="updates"):
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

    return state


def main():
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
    if not api_key:
        console.print(
            "[danger]Error: CLAUDE_API_KEY is not configured.[/danger]",
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

        run_agent_loop(graph, state, prompt)
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
            user_input = session.prompt(prompt_str).strip()

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
            state = run_agent_loop(graph, state, user_input)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[info]Exiting session. Goodbye![/info]")
            break


if __name__ == "__main__":
    main()
