# Claude Code Python TODO List

Below is the structured list of tasks for reconstructing Claude Code in Python + LangGraph.

- [ ] **Phase 1: Environment & Project Setup**
  - [ ] Create `pyproject.toml` and `requirements.txt`
  - [ ] Set up `.gitignore` for Python environments and cache
- [ ] **Phase 2: Core Workspace Tools**
  - [ ] Implement `BashTool` with dynamic cwd updates
  - [ ] Implement `FileReadTool` with Jupyter notebook (`.ipynb`) support
  - [ ] Implement `FileWriteTool` for creation and complete overwrites
  - [ ] Implement `FileEditTool` with exact string replacement and uniqueness validation
  - [ ] Implement `GrepTool` and `GlobTool` for codebase searches
  - [ ] Implement `AskUserQuestionTool` for interactive mid-turn prompt questions
- [ ] **Phase 3: LangGraph Agent Loop**
  - [ ] Define state definitions in `state.py`
  - [ ] Construct the dynamic system prompt with active environment context
  - [ ] Compile the LangGraph agent state graph (Agent node + Tool Router node) in `agent.py`
- [ ] **Phase 4: CLI Interface**
  - [ ] Setup the terminal REPL using `prompt-toolkit` and `rich` in `cli.py`
  - [ ] Implement real-time streaming of thinking blocks, active tool calls, and final responses
- [ ] **Phase 5: Testing & Verification**
  - [ ] Write tool tests in `tests/test_tools.py`
  - [ ] Write integration and flow tests in `tests/test_agent.py`
  - [ ] Verify execution using `pytest`
