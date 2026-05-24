# Antigravity CLI (Claude Code Python + LangGraph Re-implementation)

A premium developer AI companion reconstructed in Python and LangGraph, replicating the core agentic capabilities of Claude Code.

## Architecture

Built entirely as a **LangGraph State Machine** wrapped with an interactive command-line **REPL interface**:
- Dynamic workspace context generation (OS, local time, active Git branch, CWD, and Git branch details).
- Robust local tools executing safely against the active folder.
- Real-time command directory tracking using custom stdout boundary tokens.

---

## Workspace Tools

- **`BashTool` (`execute_bash_tool`)**: Runs any workspace commands and dynamically maps current working directory shifts (`cd`).
- **`FileReadTool` (`read_file_tool`)**: Reads file contents with line numbers and line offset support. Integrates fully with Jupyter Notebooks (`.ipynb`).
- **`FileWriteTool` (`write_file_tool`)**: Creates absolute code files or does total rewrites.
- **`FileEditTool` (`edit_file_tool`)**: Safely performs exact target string replacements (`old_string` -> `new_string`) with target uniqueness validation.
- **`GrepTool` / `GlobTool`**: High-performance recursive codebase searches and pattern matching.
- **`AskUserQuestionTool`**: Directly queries the human during multi-turn executions for interactive feedback.

---

## Setup & Dependency Installation

1. Create a Python virtual environment and upgrade pip:
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install --upgrade pip
   ```

2. Install the project in editable mode including development dependencies:
   ```bash
   .venv/bin/pip install -e ".[dev]"
   ```

3. Run the automated test suite to verify tool correctness:
   ```bash
   .venv/bin/pytest tests/
   ```

---

## How to Configure and Run

Simply configure the base URL, API key, and model name to use your reconstructed Python Claude Code:

```bash
# Configure standard credentials
export CLAUDE_API_KEY="your-api-key"
export CLAUDE_BASE_URL="https://api.anthropic.com/v1"  # Or standard OpenAI custom gateway
export CLAUDE_MODEL_NAME="claude-3-5-sonnet-20241022"   # Or custom OpenAI models like gpt-4o

# Run interactive REPL session
.venv/bin/claude-py

# Or run in one-shot print mode
.venv/bin/claude-py "Create a simple test.py file and run it" -p
```
