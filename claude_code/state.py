import os
from typing import Annotated, List, TypedDict
from langchain_core.messages import BaseMessage


def merge_messages(left: List[BaseMessage], right: List[BaseMessage]) -> List[BaseMessage]:
    """
    State reducer for appending messages.
    If the right list has a special flag `replace_history`, it replaces the left list entirely.
    """
    if right and isinstance(right[0], BaseMessage) and right[0].additional_kwargs.get("replace_history"):
        return right
    return left + right


class AgentState(TypedDict):
    # Chronological history of messages in the conversation
    messages: Annotated[List[BaseMessage], merge_messages]
    # Current active directory of the execution workspace
    current_working_directory: str
    # Active TODO checklist or plan details
    plan: str
    # High-density Markdown summary of older compacted conversation history
    summarized_history: str
    # Unique identifier for this agent task (useful for subagents)
    agent_id: str
    # Global permission mode (default, auto, plan, bypass)
    permission_mode: str
