# Antigravity CLI (Claude Code Python + LangGraph 重构版)

这是一个利用 **Python 和 LangGraph** 重新构建的顶级开发大模型助手 CLI，深度还原了 Claude Code 的核心交互与 Agent 推理能力。

## 架构

整个助手是作为一个 **LangGraph 状态机** 运转的，外层包裹了极具交互感的终端 **REPL 环流**：
- **动态工作空间上下文**: 每次发起大模型决策时，自动抓取最新的操作系统、本地时间、活动 Git 分支及修改状态、当前所处的绝对路径。
- **本地工具安全注入**: 围绕本地工作空间提供一系列的高可靠本地执行和代码操作工具。
- **命令行状态保持**: 借助自定义 shell 输出边界标记，可在连续的对话 turn 中完美跟踪终端 `cd` 目录切换的副作用。

---

## 核心工具链

- **`BashTool` (`execute_bash_tool`)**: 在本地系统上执行任何 Shell 命令行。如果检测到 `cd` 命令，将自动更新对话上下文中的工作目录状态。
- **`FileReadTool` (`read_file_tool`)**: 读取文件内容，输出带行号（cat -n 风格），支持起止行号截断读取。内置对 Jupyter Notebooks (`.ipynb`) 的优雅结构化解析渲染。
- **`FileWriteTool` (`write_file_tool`)**: 创建新文件或对现有文件进行完全覆写。
- **`FileEditTool` (`edit_file_tool`)**: 执行精确的 target 字符串局部替换（`old_string` -> `new_string`）。强制做匹配唯一性校验，杜绝破坏性编辑。
- **`GrepTool` / `GlobTool`**: 高性能的递归代码全局搜索与文件名通配符匹配。
- **`AskUserQuestionTool`**: 在 Agent 运行中途允许模型暂停执行并直接提问人类，收集关键答复。

---

## 安装与部署

1. 创建 Python 虚拟环境并升级 pip：
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install --upgrade pip
   ```

2. 以可编辑模式安装项目（包含开发和测试依赖）：
   ```bash
   .venv/bin/pip install -e ".[dev]"
   ```

3. 运行自动化单元测试套件：
   ```bash
   .venv/bin/pytest tests/
   ```

---

## 如何配置与运行

您仅需要配置 `CLAUDE_BASE_URL`、`CLAUDE_API_KEY` 和 `CLAUDE_MODEL_NAME` 环境变量，即可使用这个重构后的 Claude Code 助手：

```bash
# 1. 配置认证凭证与后端模型信息（这里以 OpenAI 或代理 Gateway 为例，亦可配置 Anthropic 官方密钥）
export CLAUDE_API_KEY="your-api-key"
export CLAUDE_BASE_URL="https://api.openai.com/v1"  # 或者是您本地的大模型代理网关
export CLAUDE_MODEL_NAME="gpt-4o"  # 或者是 claude-3-5-sonnet

# 2. 启动交互式 REPL 会话终端
.venv/bin/claude-py

# 3. 或者是通过 -p 参数进行非交互式的单次命令行输出
.venv/bin/claude-py "修复项目下所有的 py 文件的格式和引入导入顺序" -p
```
