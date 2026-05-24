import os
from typing import Annotated, List, TypedDict
from langchain_core.messages import BaseMessage


def merge_messages(left: List[BaseMessage], right: List[BaseMessage]) -> List[BaseMessage]:
    """
    State reducer for appending messages.
    """
    return left + right


class AgentState(TypedDict):
    # Chronological history of messages in the conversation
    messages: Annotated[List[BaseMessage], merge_messages]
    # Current active directory of the execution workspace
    current_working_directory: str
    # Active TODO checklist or plan details
    plan: str
