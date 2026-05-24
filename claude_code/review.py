import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from claude_code.agent import get_llm

console = Console()


def load_source_code() -> str:
    """
    Loads all core Python module files as context.
    """
    files_to_read = [
        "claude_code/state.py",
        "claude_code/agent.py",
        "claude_code/cli.py",
        "claude_code/tools/bash.py",
        "claude_code/tools/file_read.py",
        "claude_code/tools/file_write.py",
        "claude_code/tools/file_edit.py",
        "claude_code/tools/search.py",
    ]
    
    context = []
    for f in files_to_read:
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as file_obj:
                context.append(f"=== File: {f} ===\n{file_obj.read()}\n")
    return "\n".join(context)


def run_subagent_review(agent_name: str, system_prompt: str, code_context: str) -> str:
    """
    Spawns an LLM subagent review using the configured credentials.
    """
    llm = get_llm()
    prompt = f"{system_prompt}\n\n以下是待评审的系统源代码：\n\n{code_context}"
    
    console.print(f"\n[bold blue]Sub-Agent ({agent_name})[/bold blue] 正在审计源码中...")
    
    # Standard Chat message invoke
    from langchain_core.messages import HumanMessage
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


def main():
    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        console.print("[bold red]错误: CLAUDE_API_KEY 未配置，无法启动大模型 Sub-Agent 评审。[/bold red]")
        sys.exit(1)

    console.print(Panel(
        "[bold blue]Claude Code Python Sub-Agent 联席评审系统[/bold blue]\n"
        "[dim]启动安全审计、系统架构、代码健壮性三大 Sub-Agent 进行交叉评审[/dim]",
        border_style="blue"
    ))

    code_context = load_source_code()

    # Define specialized system prompts
    agents = {
        "安全审计 Sub-Agent": (
            "你是一个专业的代码安全审计专家。请对以下 Python 代码进行深度的安全评估。 "
            "重点关注：Shell 注入漏洞（尤其是 Bash 命令行执行中的 shell=True 注入安全隐患）、 "
            "UNC 路径穿越、敏感认证密钥暴露等安全风险。 "
            "请用中文输出详尽的 Markdown 审计报告，使用规范的分级安全警告。"
        ),
        "架构与设计 Sub-Agent": (
            "你是一个顶级的系统架构设计专家。请对以下 Python 代码以及基于 LangGraph 的控制流进行深度评审。 "
            "重点关注：状态定义 AgentState 的完备性、LangGraph 控制节点及条件转移的合理性、 "
            "Bash 执行中 CWD 切换状态在状态机多轮对话中的同步隔离一致性、以及系统在挂起或超时等异常场景下的状态保护机制。 "
            "请用中文输出详尽的 Markdown 架构评审报告。"
        ),
        "代码稳定性与健壮性 Sub-Agent": (
            "你是一个优秀的代码质量与健壮性专家。请对以下 Python 代码进行深度审查。 "
            "重点关注：异常与边界保护（越界、文件不存在等防护）、Jupyter 笔记本结构化解析的容错处理、 "
            "文件编辑工具 FileEditTool 唯一性精准替换匹配算法的稳健度、以及整体单元测试套件的覆盖范围。 "
            "请用中文输出详尽的 Markdown 健壮性审查报告。"
        )
    }

    os.makedirs("docs/reviews", exist_ok=True)

    for name, system_prompt in agents.items():
        report = run_subagent_review(name, system_prompt, code_context)
        
        # Save report
        filename = "docs/reviews/" + name.split(" ")[0].replace("安全审计", "security_review").replace("架构与设计", "architecture_review").replace("代码稳定性与健壮性", "code_quality_review") + ".md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
            
        console.print(f"[bold green]✓ {name} 评审完成，报告已保存至 {filename}[/bold green]")
        console.print(Markdown(report[:300] + "\n\n...(余下报告已保存至文件)..."))


if __name__ == "__main__":
    main()
