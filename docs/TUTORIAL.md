# Antigravity CLI (Claude Code Python 版) 使用指南

欢迎使用 **Antigravity CLI**！本指南将详细介绍如何从零开始配置、运行并高效使用这个基于 **Python + LangGraph** 重新构建的 Claude Code 命令行开发助手。

---

## 1. 快速上手

### 1.1 安装与环境配置

项目支持 **Python >=3.9**。推荐使用虚拟环境进行安装，以避免污染系统全局的 Python 库。

```bash
# 1. 创建并激活 Python 虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 2. 升级 pip
.venv/bin/python3 -m pip install --upgrade pip

# 3. 以可编辑模式安装项目（包括开发和测试依赖）
.venv/bin/pip install -e ".[dev]"
```

### 1.2 运行单元测试验证

为了确保所有的本地工具链路工作正常，请执行 pytest 单元测试套件：

```bash
.venv/bin/pytest tests/
```

如果输出如下 `7 passed` 结果，即表示安装和工具环境一切就绪：
```text
tests/test_agent.py ..                                                   [ 28%]
tests/test_tools.py .....                                                [100%]

========================= 7 passed, 1 warning in 3.49s =========================
```

---

## 2. 模型与凭证配置

Antigravity 支持极其灵活的 API Gateway 和 Model 配置。您可以通过设置环境变量来控制它连接的后端大语言模型：

### 2.1 使用自定义 OpenAI 兼容接口（推荐，如 Ollama, LM Studio, vLLM, API 代理网关）
当配置了 `CLAUDE_BASE_URL` 时，系统将自动使用 `ChatOpenAI` 客户端适配对应的接口：

```bash
export CLAUDE_API_KEY="your-api-key"
export CLAUDE_BASE_URL="https://api.openai.com/v1"  # 或您本地的代理网关地址
export CLAUDE_MODEL_NAME="gpt-4o"  # 或者您的本地大模型代号
```

### 2.2 使用 Anthropic 官方接口
当未设置 `CLAUDE_BASE_URL`，但 `CLAUDE_MODEL_NAME` 以 `claude` 开头或 API KEY 具有 `sk-ant-` 前缀时，系统将使用官方 Anthropic 客户端：

```bash
export CLAUDE_API_KEY="sk-ant-your-key-here"
export CLAUDE_MODEL_NAME="claude-3-5-sonnet-20241022"
```

---

## 3. 运行助手

系统支持两种主要运行模式：**交互式 REPL 终端模式** 和 **单次执行 Print 模式**。

### 3.1 交互式终端模式 (REPL)
直接运行程序即可进入精美的 interactive 交互终端。它会自动解析当前的工作空间，并在命令提示符中高亮展示你当前所处的相对路径。

```bash
.venv/bin/claude-py
```

*   **输入命令**: 直接打字输入你的需求。例如 `帮我创建一个 tests/test_math.py 文件并添加基本的单元测试，然后用 pytest 运行它`。
*   **快捷指令**:
    *   `/clear`: 重置当前对话历史，重归初始状态。
    *   `/exit`: 优雅退出会话。
*   **指令历史**: 您可以使用键盘上的 [向上键 ↑] / [向下键 ↓] 来查找和回溯之前输入过的指令。

### 3.2 单次执行模式 (Print)
在脚本自动化、命令行管道中，可以使用 `-p` 或 `--print` 参数，一次性将结果打印到标准输出：

```bash
# 单次运行指定任务
.venv/bin/claude-py "运行 pytest tests/ 并修复任何可能出现的报警" -p

# 支持通过管道传入上下文
cat requirements.txt | .venv/bin/claude-py "升级 requirements.txt 中所有的库到最新版" -p
```

---

## 4. 最佳实践与建议

1.  **文件编辑的原子性**:
    *   当需要修改已有代码时，大模型在决策时会自动选用 `edit_file_tool` 代替 `write_file_tool`。
    *   在执行编辑前，大模型**必须**已经用 `read_file_tool` 阅读过此文件，否则编辑工具会拒绝执行。这保证了大模型不会基于过期的假设盲改代码。
2.  **Bash 路径移动**:
    *   您可以在对话中随意让 Agent 执行 `cd <path>`，我们的 Bash 拦截器会实时捕获 CWD 的变更。无需担心它在之后的命令中会跳回原目录。
3.  **安全隔离**:
    *   大模型在执行您下发的 Bash 任务时拥有很高的本地系统操作权限。因此，请确保仅在您信任的项目目录下启动此助手。
