# Claude Code Python 开发任务检查清单

以下是用 Python + LangGraph 重构 Claude Code 的结构化任务列表。

- [x] **第 1 阶段：环境与项目初始化**
  - [x] 创建 `pyproject.toml` 和 `requirements.txt`
  - [x] 配置 `.gitignore` 以忽略 Python 虚拟环境和编译缓存
- [x] **第 2 阶段：核心工作空间工具链**
  - [x] 实现支持 CWD 动态跟踪的 `BashTool`
  - [x] 实现支持 Jupyter notebook (`.ipynb`) 原生解析的 `FileReadTool`
  - [x] 实现支持自动创建父目录的 `FileWriteTool`
  - [x] 实现支持精准替换和唯一性校验的 `FileEditTool`
  - [x] 实现支持快速搜索和匹配的 `GrepTool` 与 `GlobTool`
  - [x] 实现支持交互式人机交互的 `AskUserQuestionTool`
- [x] **第 3 阶段：LangGraph Agent 状态机环流**
  - [x] 在 `state.py` 中定义全局 TypedDict 状态
  - [x] 在 `agent.py` 中实现动态收集系统状态的 SystemMessage 生成器
  - [x] 编译 LangGraph 的核心执行状态图 (Agent 决策节点 + Tool 路由执行节点)
- [x] **第 4 阶段：CLI 终端会话交互**
  - [x] 在 `cli.py` 中利用 `prompt-toolkit` 和 `rich` 搭建终端 REPL 控制层
  - [x] 支持在终端上流式渲染思维行为、被调用的工具参数以及最终的 Markdown 答复
- [x] **第 5 阶段：自动化测试与质量验证**
  - [x] 在 `tests/test_tools.py` 中编写完备的工具边界单元测试
  - [x] 在 `tests/test_agent.py` 中编写集成与条件状态路由测试
  - [x] 成功执行 `pytest` 并且 7 个测试用例全部绿灯通过
