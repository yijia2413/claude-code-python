# Recreating Claude Code in Python + LangGraph

This document outlines the design and architectural goals for recreating Claude Code's capabilities inside this repository using **Python 3.10+ and LangGraph**.

## Architecture & System Design

We build the agent as a LangGraph State Machine, coupled with an interactive CLI REPL.

### 1. State Definition
The LangGraph workflow maintains an `AgentState`:
- `messages`: Standard message logs (User, AI, Tool).
- `current_working_directory`: The active path of execution.
- `plan`: Active planner notes.
- `system_prompt`: Generated dynamically with active branch, OS, files, and time context.

### 2. Built-in Agent Tools
We implement high-reliability tools in Python:
- **`BashTool` (`run_command`)**: Runs shell commands on the local machine and updates the state's `current_working_directory` upon executing `cd`.
- **`FileReadTool` (`read_file`)**: Reads file contents with line-numbering and line-range limitations. Supports `.ipynb` parsing.
- **`FileWriteTool` (`write_file`)**: Writes absolute code files or overwrites existing ones.
- **`FileEditTool` (`edit_file`)**: Performs robust exact string replacement (`old_string` -> `new_string`) with uniqueness checks.
- **`GrepTool` / `GlobTool`**: High-performance codebase searching and matching.
- **`AskUserQuestionTool`**: Allows the agent to prompt the human directly in the middle of execution.

## Proposed Code Structure

- `claude_code/`
  - `__init__.py`
  - `cli.py`: Command Line interface and interactive REPL.
  - `agent.py`: LangGraph compilations and dynamic system prompts.
  - `state.py`: Core state schemas.
  - `tools/`:
    - `__init__.py`
    - `bash.py`
    - `file_read.py`
    - `file_write.py`
    - `file_edit.py`
    - `search.py`
    - `ask_user.py`
  - `utils/`: Core utilities and helpers.
- `docs/`
  - `PLAN.md`: Main architecture and plan.
  - `TODO.md`: Tasks checklist.
  - `UPDATE.md`: Ongoing update logs.
- `tests/`
  - `test_tools.py`
  - `test_agent.py`
- `pyproject.toml`
- `requirements.txt`

## Execution Steps
1. Define the base project configuration (`pyproject.toml`, `requirements.txt`).
2. Write unit tests for tools.
3. Write clean, robust tool implementations under `claude_code/tools/`.
4. Compile the LangGraph agent state graph.
5. Create the command-line REPL.
6. Verify and iterate.
