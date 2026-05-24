from typing import List, Tuple
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from claude_code.agent import get_llm


def compact_history(
    messages: List[BaseMessage], existing_summary: str = ""
) -> Tuple[List[BaseMessage], str]:
    """
    Summarizes older messages in the conversation, removes them, and returns
    the updated message list alongside the new consolidated high-density Markdown summary.
    """
    # Keep the last 6 messages to preserve active context
    messages_to_compact = messages[:-6]
    messages_to_keep = messages[-6:]

    # Format the messages into a readable conversation history for the LLM
    conversation_text = []
    for msg in messages_to_compact:
        sender = "AI" if msg.type == "ai" else "User" if msg.type == "human" else "Tool"
        content = msg.content
        conversation_text.append(f"[{sender}]: {content}")
    
    conversation_history = "\n".join(conversation_text)

    existing_summary_header = (
        f"## 既有的历史摘要日志：\n{existing_summary}\n" if existing_summary else ""
    )

    prompt = f"""你是一个会话记忆归纳专家。请将以下早期的多轮对话内容压缩为一个高密度的 Markdown 摘要日志。

## 指南：
1. 你需要保留这期间所有的关键开发事实、已完成的文件修改路径、运行过的终端命令以及重要的代码设计结论。
2. 去除冗余的客套话和具体的大段代码。
3. 请完全用中文输出高质量的摘要日志。

{existing_summary_header}

## 待归纳的最新多轮对话内容：
{conversation_history}

请输出更新合并后的终极 Markdown 摘要日志：
"""

    try:
        llm = get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        new_summary = response.content.strip()
    except Exception as e:
        # Fail safe: if summarization fails, don't drop the messages
        return messages, existing_summary

    return messages_to_keep, new_summary
