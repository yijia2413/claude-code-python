import tiktoken
from typing import List
from langchain_core.messages import BaseMessage

# Define a token limit threshold (e.g. 10,000 tokens for testing, or 120,000 for production)
# Let's set a default, but allow configurations
TOKEN_COMPACTION_THRESHOLD = 20000  # 20k tokens threshold


def calculate_message_tokens(messages: List[BaseMessage]) -> int:
    """
    Accurately calculates total token count in a message list using tiktoken.
    """
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
    except Exception:
        # Fallback to rough estimate if encoding is missing (1 word ~ 1.3 tokens)
        total_chars = sum(len(msg.content) for msg in messages if isinstance(msg.content, str))
        return int(total_chars / 4)

    total_tokens = 0
    for msg in messages:
        if not msg.content:
            continue
        if isinstance(msg.content, str):
            total_tokens += len(encoding.encode(msg.content))
        elif isinstance(msg.content, list):
            # Handle multimodal or complex block inputs
            for block in msg.content:
                if isinstance(block, dict) and "text" in block:
                    total_tokens += len(encoding.encode(block["text"]))
                elif isinstance(block, str):
                    total_tokens += len(encoding.encode(block))
                    
        # Add basic overhead for message properties and tool calls
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            total_tokens += 100 * len(msg.tool_calls)
            
    return total_tokens


def should_compact(messages: List[BaseMessage], threshold: int = TOKEN_COMPACTION_THRESHOLD) -> bool:
    """
    Determines if the message list has exceeded the compaction token threshold.
    """
    # Keep at least 6 messages to preserve immediate conversation turns
    if len(messages) <= 6:
        return False
    return calculate_message_tokens(messages) > threshold
