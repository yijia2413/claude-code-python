import os
from langchain_core.messages import HumanMessage, AIMessage
from claude_code.agent import create_agent_graph, should_continue


def test_agent_graph_compiles():
    graph = create_agent_graph()
    assert graph is not None


def test_should_continue_edge():
    # Test case 1: AIMessage with tool calls
    ai_msg_with_tools = AIMessage(
        content="calling bash tool",
        tool_calls=[{"name": "execute_bash_tool", "args": {"command": "ls"}, "id": "1", "type": "tool_call"}]
    )
    state_with_tools = {"messages": [ai_msg_with_tools]}
    assert should_continue(state_with_tools) == "tools"

    # Test case 2: AIMessage without tool calls
    ai_msg_no_tools = AIMessage(content="completed final answer.")
    state_no_tools = {"messages": [ai_msg_no_tools]}
    assert should_continue(state_no_tools) == "__end__"
