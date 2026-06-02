import datetime
import os
import platform
import subprocess
import asyncio
from typing import Literal

from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END

from claude_code.state import AgentState
from claude_code.tools.bash import execute_bash
from claude_code.tools.file_read import read_file
from claude_code.tools.file_write import write_file
from claude_code.tools.file_edit import edit_file
from claude_code.tools.search import grep_search, glob_files
from claude_code.tools.ask_user import ask_user

# Define local tool instances using LangChain's @tool decorator

@tool
def execute_bash_tool(command: str, cwd: str) -> str:
    """
    Executes a bash command in the workspace.
    Supports running shell tools, compiling code, running tests, or performing git operations.
    The Cwd represents the working directory where the command will be run.
    """
    res = execute_bash(command, cwd)
    output = []
    if res["stdout"]:
        output.append(f"[stdout]\n{res['stdout']}")
    if res["stderr"]:
        output.append(f"[stderr]\n{res['stderr']}")
    output.append(f"[exit code] {res['exit_code']}")
    # Include new cwd if it changed
    if res["new_cwd"] != cwd:
        output.append(f"[new working directory] {res['new_cwd']}")
    return "\n".join(output)


@tool
def read_file_tool(file_path: str, start_line: int = None, end_line: int = None) -> str:
    """
    Reads a file from the workspace. Displays line numbers and supports .ipynb notebooks.
    Optionally specify start_line and end_line for line offsets.
    """
    try:
        return read_file(file_path, start_line, end_line)
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def write_file_tool(file_path: str, content: str) -> str:
    """
    Creates or overwrites a file with the given content.
    Creates parent directories automatically if they do not exist.
    """
    try:
        return write_file(file_path, content)
    except Exception as e:
        return f"Error writing file: {str(e)}"


@tool
def edit_file_tool(file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    """
    Performs exact string replacements in a file (old_string -> new_string).
    Fails if old_string is not found or is not unique (unless replace_all is True).
    """
    try:
        return edit_file(file_path, old_string, new_string, replace_all)
    except Exception as e:
        return f"Error editing file: {str(e)}"


@tool
def grep_search_tool(dir_path: str, query: str) -> str:
    """
    Performs a text search within files in the given directory recursively.
    """
    try:
        matches = grep_search(dir_path, query)
        if not matches:
            return "No matches found."
        return "\n".join(matches)
    except Exception as e:
        return f"Error performing search: {str(e)}"


@tool
def glob_files_tool(dir_path: str, pattern: str) -> str:
    """
    Lists files matching the glob pattern inside the directory recursively.
    """
    try:
        matches = glob_files(dir_path, pattern)
        if not matches:
            return "No matches found."
        return "\n".join(matches)
    except Exception as e:
        return f"Error matching files: {str(e)}"


@tool
def ask_user_tool(question: str) -> str:
    """
    Asks the user a clarifying question during execution and returns their response.
    """
    return ask_user(question)


# Registry of tools
TOOLS = [
    execute_bash_tool,
    read_file_tool,
    write_file_tool,
    edit_file_tool,
    grep_search_tool,
    glob_files_tool,
    ask_user_tool,
]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}
# Mark safe tools for concurrent execution
CONCURRENCY_SAFE_TOOLS = {"read_file_tool", "grep_search_tool", "glob_files_tool"}


def get_llm():
    """
    Configures the Chat Model based on config.yaml or environment variables.
    """
    from claude_code.config import get_active_provider_config
    
    # 1. Try to load from config.yaml first
    provider_cfg = get_active_provider_config()
    if provider_cfg:
        protocol = provider_cfg.get("protocol", "openai").lower()
        kwargs = {
            "model": provider_cfg.get("model", "claude-3-5-sonnet"),
            "api_key": provider_cfg.get("api_key") or "no-key",
            "temperature": 0,
        }
        if provider_cfg.get("base_url"):
            kwargs["base_url"] = provider_cfg.get("base_url")

        if protocol == "anthropic":
            return ChatAnthropic(**kwargs)
        else:
            return ChatOpenAI(**kwargs)

    # 2. Fallback to Environment Variables
    base_url = os.environ.get("CLAUDE_BASE_URL")
    api_key = os.environ.get("CLAUDE_API_KEY")
    model_name = os.environ.get("CLAUDE_MODEL_NAME", "claude-3-5-sonnet")

    # Determine protocol based on model name, API key prefix, or a protocol hint in base_url
    is_anthropic = model_name.startswith("claude") or (api_key and api_key.startswith("sk-ant-")) or (base_url and "anthropic" in base_url.lower())

    if is_anthropic:
        kwargs = {
            "model": model_name,
            "api_key": api_key or "no-key",
            "temperature": 0,
        }
        if base_url:
            kwargs["base_url"] = base_url
        return ChatAnthropic(**kwargs)

    # Fallback to standard OpenAI format
    kwargs = {
        "model": model_name,
        "api_key": api_key or "no-key",
        "temperature": 0,
    }
    if base_url:
        kwargs["base_url"] = base_url
    return ChatOpenAI(**kwargs)


def compile_git_info(cwd: str) -> str:
    """
    Gathers active git details of the workspace.
    """
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        
        status = subprocess.check_output(
            ["git", "status", "--short"],
            cwd=cwd,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        
        git_msg = f"Active Git Branch: {branch}\n"
        if status:
            git_msg += f"Git Status Changes:\n{status}"
        else:
            git_msg += "Git Directory Clean"
        return git_msg
    except Exception:
        return "Not inside a git repository."


def generate_system_message(state: AgentState) -> SystemMessage:
    """
    Assembles a rich dynamic system prompt for the developer companion agent.
    """
    cwd = state.get("current_working_directory", os.getcwd())
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os_info = f"{platform.system()} ({platform.release()})"
    git_info = compile_git_info(cwd)

    prompt = f"""You are Antigravity, a highly capable developer AI companion. You have access to tools for interacting with files and running terminal commands in the workspace.

## Active Workspace Information
- Current Local Time: {current_time}
- Operating System: {os_info}
- Working Directory: {cwd}
- {git_info}

## Tool Guidance
1. **BashTool (`execute_bash_tool`)**:
   - Run any command in the shell.
   - If you execute a `cd` command, the working directory will automatically update.
2. **FileReadTool (`read_file_tool`)**:
   - Read lines. Always read a file before modifying it to understand its contents.
3. **FileWriteTool (`write_file_tool`)**:
   - Write files cleanly.
4. **FileEditTool (`edit_file_tool`)**:
   - Prefer this tool for precise modifications inside existing code.
   - Do EXACT string replacements. The replacement MUST match characters and leading whitespace exactly.
5. **Grep/Glob Tools**:
   - Use these to search the codebase.
6. **AskUserQuestionTool (`ask_user_tool`)**:
   - Use this to prompt the user directly if you need feedback or clarifying questions.

Maintain premium standard practices: write robust, clean, and tested code.
"""
    summarized_history = state.get("summarized_history", "")
    if summarized_history:
        prompt += f"\n## 已压缩的早期对话摘要记录 (对话历史垃圾回收结果):\n{summarized_history}\n"

    return SystemMessage(content=prompt)


# LangGraph workflow definition

async def agent_node(state: AgentState) -> dict:
    """
    Agent node: gets the latest state, binds tools, formats system prompt, and calls model asynchronously.
    """
    messages = state.get("messages", [])
    summarized_history = state.get("summarized_history", "")

    llm = get_llm()
    llm_with_tools = llm.bind_tools(TOOLS)

    system_msg = generate_system_message(state)

    # Use ainvoke for async streaming support
    response = await llm_with_tools.ainvoke([system_msg] + messages)
    
    return {
        "messages": [response],
    }


async def run_single_tool(tool_call, cwd, permission_mode):
    """Executes a single tool asynchronously."""
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]
    tool_id = tool_call["id"]

    if tool_name == "execute_bash_tool" and "cwd" not in tool_args:
        tool_args["cwd"] = cwd

    # [Hooks]: PreToolUse Permission Mock Check
    if permission_mode != "bypass" and tool_name not in CONCURRENCY_SAFE_TOOLS:
        # Here we would normally evaluate `alwaysAllowRules`.
        # For now, we mock success.
        pass

    tool_fn = TOOLS_BY_NAME.get(tool_name)
    if tool_fn:
        try:
            # Run the synchronous tool function in a background thread
            res = await asyncio.to_thread(tool_fn.invoke, tool_args)
            return str(res), tool_name, tool_id
        except Exception as e:
            return f"Error executing tool: {str(e)}", tool_name, tool_id
    else:
        return f"Tool '{tool_name}' not found.", tool_name, tool_id


async def execute_tools_node(state: AgentState) -> dict:
    """
    Tool execution node: executes requested tool calls asynchronously.
    Uses asyncio.gather for concurrency safe tools (e.g., read, grep).
    """
    last_message = state["messages"][-1]
    tool_messages = []
    new_cwd = state.get("current_working_directory", os.getcwd())
    permission_mode = state.get("permission_mode", "default")

    all_safe = all(tc["name"] in CONCURRENCY_SAFE_TOOLS for tc in last_message.tool_calls)

    if all_safe:
        # Concurrent execution
        tasks = [run_single_tool(tc, new_cwd, permission_mode) for tc in last_message.tool_calls]
        results = await asyncio.gather(*tasks)
        for res, tool_name, tool_id in results:
            tool_messages.append(ToolMessage(content=res, tool_use_id=tool_id, name=tool_name))
    else:
        # Sequential execution
        for tc in last_message.tool_calls:
            res, tool_name, tool_id = await run_single_tool(tc, new_cwd, permission_mode)
            if tool_name == "execute_bash_tool":
                for line in res.split("\n"):
                    if line.startswith("[new working directory]"):
                        new_cwd = line.replace("[new working directory]", "").strip()
            tool_messages.append(ToolMessage(content=res, tool_use_id=tool_id, name=tool_name))

    return {
        "messages": tool_messages,
        "current_working_directory": new_cwd,
    }


async def compact_node(state: AgentState) -> dict:
    """
    Compact node: Triggers dialogue compaction dynamically when the token size exceeds threshold.
    """
    from claude_code.compact.summarizer import compact_history
    messages = state.get("messages", [])
    summarized_history = state.get("summarized_history", "")

    # compact_history will replace the messages list by setting replace_history=True flag
    new_messages, new_summarized_history = compact_history(messages, summarized_history)
    
    # Mark the first message (or the list) to inform the reducer to overwrite the history
    if new_messages:
        new_messages[0].additional_kwargs["replace_history"] = True

    return {
        "messages": new_messages,
        "summarized_history": new_summarized_history
    }


def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """
    Conditional router edge: routes to tools if tool_calls exist, else exits.
    """
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "__end__"


def check_compact(state: AgentState) -> Literal["compact", "agent"]:
    """
    Conditional router edge: routes to compact if threshold exceeded, else to agent.
    """
    from claude_code.compact.auto_compact import should_compact
    if should_compact(state.get("messages", [])):
        return "compact"
    return "agent"


def create_agent_graph():
    """
    Compiles the async LangGraph agent state graph.
    """
    workflow = StateGraph(AgentState)

    # Register nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", execute_tools_node)
    workflow.add_node("compact", compact_node)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add edges
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "__end__": END})
    workflow.add_conditional_edges("tools", check_compact, {"compact": "compact", "agent": "agent"})
    workflow.add_edge("compact", "agent")

    return workflow.compile()
