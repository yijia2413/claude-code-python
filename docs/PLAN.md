# 用 Python + LangGraph 重构 Claude Code

本文档概述了在此代码库中，使用 **Python 3.10+ 和 LangGraph** 重新实现 Claude Code 核心功能的架构目标和系统设计。

## 架构与系统设计

我们将 Agent 构建为一个 LangGraph 状态机，结合交互式 CLI REPL。

### 1. 状态定义
LangGraph 工作流维护一个 `AgentState` 结构：
- `messages`: 标准的消息日志列表（User, AI, Tool）。
- `current_working_directory`: 当前活动的执行工作目录（绝对路径）。
- `plan`: 活动的任务计划或 TODO 文本。
- `system_prompt`: 根据当前活动 Git 分支、操作系统、目录文件以及实时时间动态组装生成。

### 2. 内置 Agent 工具链
我们在 Python 中实现了一系列高可靠性的本地工具：
- **`BashTool` (`execute_bash_tool`)**: 在本地系统上执行 shell 命令行。如果检测到 `cd` 命令，将自动提取并更新状态中的 `current_working_directory`。
- **`FileReadTool` (`read_file_tool`)**: 读取文件内容。支持行号输出（cat -n 风格）以及按需截断的起止行偏移量。内置对 `.ipynb` (Jupyter Notebook) 的优雅结构化解析渲染。
- **`FileWriteTool` (`write_file_tool`)**: 创建新文件或对现有文件进行完全覆写。
- **`FileEditTool` (`edit_file_tool`)**: 执行精确的 target 字符串局部替换（`old_string` -> `new_string`）。强制做匹配唯一性校验，杜绝破坏性编辑。
- **`GrepTool` / `GlobTool`**: 高性能的递归代码全局搜索与文件名通配符匹配。
- **`AskUserQuestionTool`**: 在 Agent 运行中途允许模型暂停执行并直接提问人类。

## 提议的代码目录结构

- `claude_code/`
  - `__init__.py`
  - `cli.py`: 命令行参数解析和交互式终端会话控制。
  - `agent.py`: LangGraph 状态图编译和动态系统提示词渲染。
  - `state.py`: 核心状态定义。
  - `tools/`:
    - `__init__.py`
    - `bash.py`
    - `file_read.py`
    - `file_write.py`
    - `file_edit.py`
    - `search.py`
    - `ask_user.py`
  - `utils/`: 核心通用实用工具。
- `docs/`
  - `PLAN.md`: 主体方案架构设计。
  - `TODO.md`: 活动的任务检查单。
  - `UPDATE.md`: 进行中的开发日志。
- `tests/`
  - `test_tools.py`
  - `test_agent.py`
- `pyproject.toml`
- `requirements.txt`

## 执行开发步骤
1. 定义项目的基本打包依赖配置 (`pyproject.toml`, `requirements.txt`)。
2. 针对所有的工具编写对应的 pytest 单元测试套件。
3. 在 `claude_code/tools/` 编写健壮、无 bug 的工具函数。
4. 编译 LangGraph 的 Agent 状态环流控制图。
5. 编写 interactive CLI 交互界面。
6. 进行全链路验证和迭代。
