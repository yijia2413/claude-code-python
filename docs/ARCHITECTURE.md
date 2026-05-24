# Antigravity CLI (Claude Code Python 重构版) 深度架构设计报告

本设计报告旨在详尽阐述 **Antigravity CLI**（Python + LangGraph 版 Claude Code）的模块关系、核心控制循环、路径追踪机制与精准编辑替换算法。报告中使用大量 **Mermaid 图表**，多维度拆解系统架构、算法流转与数据闭环，以便开发人员与架构师能够直观地进行理解与后续迭代。

---

## 1. 系统模块分层拓扑架构

系统采用清晰的四层架构设计，实现了 **交互展示层、逻辑流转控制层、模型调用层与本地文件系统执行层** 之间的完全解耦与数据管道通信：

```mermaid
graph TD
    %% 交互展示层
    subgraph Layer1 [1. 交互展示层 - CLI & REPL]
        A1[cli.py Entrypoint] -->|初始化命令行参数/会话历史| A2[PromptSession prompt-toolkit]
        A2 -->|捕获用户输入 Prompt| A3[Rich Rendering UI]
    end

    %% 逻辑流转控制层
    subgraph Layer2 [2. 逻辑流转控制层 - LangGraph Engine]
        B1[agent.py Graph Compiler] -->|流式驱动状态变更| B2[AgentState State Machine]
        B2 -->|Reducer 追加逻辑| B3[messages 列表]
        B2 -->|跟踪环境状态| B4[current_working_directory]
    end

    %% 模型调用与决策层
    subgraph Layer3 [3. 模型决策层 - LLM Node]
        C1[generate_system_message] -->|注入动态环境信息| C2[SystemMessage Compiler]
        C2 -->|合并会话消息| C3[get_llm Client Wrapper]
        C3 -->|API 凭证决策| C4{ChatAnthropic / ChatOpenAI}
    end

    %% 本地执行与工具链
    subgraph Layer4 [4. 执行与工具链层 - Local System & Filesystem]
        D1[TOOLS Registry] -->|execute_bash_tool| D2[Bash.py Execution Node]
        D1 -->|read_file_tool| D3[file_read.py cat -n / Jupyter]
        D1 -->|edit_file_tool| D4[file_edit.py Exact Replacement]
        D1 -->|write_file_tool| D5[file_write.py Overwrite]
        D1 -->|grep_search_tool / glob_files_tool| D6[search.py glob & grep]
        D1 -->|ask_user_tool| D7[ask_user.py console feedback]
    end

    %% 层级物理调用关系
    A3 -->|用户提示词| B2
    B1 -->|驱动节点| C2
    C4 -->|AIMessage tool_calls| B3
    B1 -->|路由驱动| D1
    D2 & D3 & D4 & D5 & D6 & D7 -->|ToolMessage 响应| B3
    D2 -.->|更新 working directory 副作用| B4
    B4 -.->|下一轮动态注入提示词| C1
```

---

## 2. LangGraph Agent 循环控制流 (Agent Loop)

系统的核心心跳基于 LangGraph 进行图状态编译与驱动。以下展示了每一个推理与执行 Turn 中，节点（Nodes）和条件边（Conditional Edges）的跳转拓扑与流转判定算法：

```mermaid
stateDiagram-v2
    [*] --> InitState : 1. 用户终端输入 Prompt
    
    state InitState {
        direction L
        [*] --> SystemPromptCompile : 动态组装环境上下文
        SystemPromptCompile --> CombineHistory : 合并当前 messages 消息队列
    }
    
    InitState --> AgentNode : 2. 状态推入 Agent 节点
    
    state AgentNode {
        LLM_ModelCall --> AI_Response : 获取大模型响应 (AIMessage)
    }
    
    AgentNode --> DecisionEdge : 3. 转入 should_continue 条件路由边
    
    state DecisionEdge <<choice>>
    
    DecisionEdge --> ToolsNode : AIMessage 附带 tool_calls (有工具调用请求)
    DecisionEdge --> FinalReply : AIMessage 无 tool_calls (直接文本答复)
    
    state ToolsNode {
        direction LR
        ParseCall --> GetToolFunction : 提取工具名与入参
        GetToolFunction --> CallSubprocess : 触发 Python 工具模块执行
        CallSubprocess --> GenerateToolMessage : 将 stdout/stderr 封装为 ToolMessage
    }
    
    ToolsNode --> UpdateState : 4. 更新全局状态 (追加消息, 同步工作目录)
    UpdateState --> InitState : 5. 闭环流转，再次请求 Agent 决策
    
    FinalReply --> OutputToConsole : 6. Rich UI Markdown 流式渲染
    OutputToConsole --> [*] : 等待用户下一轮输入
```

---

## 3. CWD 目录切换算法时序图 (BashTool CWD Injection)

传统无状态子进程在执行 `cd` 指令后，后续的命令会跳回原目录。我们设计了一套 **工作目录拦截与 CWD 动态反射机制**，通过在 Shell 执行指令尾部注入“边界分隔符”与 `pwd` 命令，实现完美的状态跟踪：

```mermaid
sequenceDiagram
    autonumber
    participant CLI as cli.py 终端会话
    participant AGT as agent.py (LangGraph 引擎)
    participant BSH as bash.py 执行器
    participant SUB as subprocess (Shell 子进程)

    CLI->>AGT: 用户输入: "cd src && git branch"
    Note over AGT: 读取当前状态 CWD (e.g. /home/user)
    AGT->>BSH: execute_bash("cd src && git branch", cwd="/home/user")
    
    Note over BSH: 在命令尾部进行边界注入裹包:<br/>({ cd src && git branch ; } ; EXIT_CODE=$? ;<br/>echo '___CWD_MARKER___' ; pwd ; exit $EXIT_CODE)
    
    BSH->>SUB: 派生 Shell 子进程，设置工作路径为 "/home/user"
    SUB->>SUB: 1. 执行用户指令 cd src && git branch<br/>2. 打印用户指令 stdout/stderr
    SUB->>SUB: 3. 打印边界分隔符: ___CWD_MARKER___
    SUB->>SUB: 4. 执行 pwd 打印最新目录: /home/user/src
    SUB-->>BSH: 返回完整的拼接字符与 EXIT_CODE
    
    Note over BSH: 解析边界字符：<br/>1. parts[0] -> 原始指令输出<br/>2. parts[1] -> 最新的绝对路径 "/home/user/src"
    
    BSH-->>AGT: 返回 { stdout, stderr, exit_code, new_cwd="/home/user/src" }
    Note over AGT: 更新 AgentState 字段:<br/>current_working_directory = "/home/user/src"
    AGT-->>CLI: 在控制台上渲染工具执行完成，下一轮指令默认进入新 CWD
```

---

## 4. 文件原子精准替换算法 (FileEdit unique replacement)

`FileEditTool` 用于在不重写全量代码（节省 Token）的情况下对局部代码进行替换。为了杜绝大模型在代码库中有多次匹配项时产生误改，系统内置了**唯一性深度校验算法**：

```mermaid
flowchart TD
    A([大模型下发文件编辑指令]) --> B[file_path 转换为绝对路径]
    B --> C{目标文件是否存在?}
    C -- 否 --> D{old_string 是否为空?}
    D -- 是 --> E[转换逻辑: 创建并覆盖新文件]
    D -- 否 --> F[抛出异常: FileNotFoundError]
    
    C -- 是 --> G[读取目标文件内容并转换为统一 LF 换行符]
    G --> H{AgentState 中该文件是否被 Read 过?}
    H -- 否/是局部视图 --> I[抛出异常: 拒绝无 Read 的盲改]
    H -- 是 --> J{文件在 Read 之后是否被外部篡改?}
    J -- 是 --> K[抛出异常: 文件被篡改，需重新 Read]
    
    J -- 否 --> L[统计 old_string 在内容中的 occurrences]
    L --> M{occurrences == 0 ?}
    M -- 是 --> N[抛出异常: old_string 未找到]
    
    M -- 否 --> O{occurrences > 1 ?}
    O -- 是 --> P{replace_all 是否为 True?}
    P -- 否 --> Q[抛出异常: 匹配项不唯一，拒绝编辑并提示增加上下文]
    P -- 是 --> R[全量替换: Replace All Matches]
    O -- 否 --> S[精准替换: 仅修改该唯一匹配项]
    
    R & S & E --> T[将修改写入磁盘]
    T --> U[通过 LSP 协议通知 LSP 服务器重新扫描 didSave]
    U --> V[更新 AgentState.readFileState 中的文件最新修改时间戳]
    V --> W([返回成功更新 ToolMessage 报告])
```

---

## 5. 交互终端会话处理流程 (REPL CLI Loop)

CLI 会话层通过 `prompt-toolkit` 的会话保持机制以及 `rich` 渲染管道，提供完美的异步高拟真终端控制：

```mermaid
flowchart TD
    A([启动 claude-py 进程]) --> B[解析 CLI 启动参数 --print / --bare]
    B --> C{是否配置 CLAUDE_API_KEY?}
    C -- 否 --> D[终端红字告警并退出进程]
    C -- 是 --> E[加载本地 ~/.claude_py_history 会话历史]
    
    E --> F[捕获当前系统 cwd 并生成提示行前缀]
    F --> G[等待用户敲击回车提交 Prompt]
    
    G --> H{指令是否为内置快捷键?}
    H -- /exit --> I([优雅退出进程, 保存历史])
    H -- /clear --> J[重置 AgentState 消息队列] --> F
    
    H -- 否: 正常开发需求 --> K[大模型决策 & 提取 Tool Calls]
    K --> L[进入 LangGraph 环流驱动流式呈现]
    L --> M[富文本展示 Thought 思维分析]
    M --> N[高亮呈现正在调用的工具与参数]
    N --> O[渲染并呈现最终 Markdown 回复]
    O --> F
```
