from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from claude_code.compact.auto_compact import calculate_message_tokens, should_compact
from claude_code.compact.summarizer import compact_history


def test_token_calculator():
    messages = [
        HumanMessage(content="hello world"),
        AIMessage(content="how can I help you?"),
    ]
    # cl100k_base has 2 tokens for "hello world" + 5 tokens for the AI message, plus overhead
    tokens = calculate_message_tokens(messages)
    assert tokens > 0


def test_should_compact_detection():
    # Less than 6 messages should never trigger compact
    messages = [HumanMessage(content="hello")] * 4
    assert not should_compact(messages, threshold=10)

    # More than 6 messages with content exceeding threshold should trigger
    messages = [HumanMessage(content="some very long message text here to exceed the low threshold")] * 8
    assert should_compact(messages, threshold=5)


def test_compact_history_trimming(monkeypatch):
    # Mock LLM invoke so we don't hit external API during tests
    class MockResponse:
        content = "Merged high-density summary"

    class MockLLM:
        def invoke(self, messages):
            return MockResponse()

    monkeypatch.setattr("claude_code.compact.summarizer.get_llm", lambda: MockLLM())

    messages = [
        HumanMessage(content="turn 1"),
        AIMessage(content="response 1"),
        HumanMessage(content="turn 2"),
        AIMessage(content="response 2"),
        HumanMessage(content="turn 3"),
        AIMessage(content="response 3"),
        HumanMessage(content="turn 4"),
        AIMessage(content="response 4"),
    ]

    trimmed, summary = compact_history(messages, existing_summary="Existing memory")
    
    # We keep the last 6 messages, so 8 - 6 = 2 messages should be compacted away
    assert len(trimmed) == 6
    assert trimmed[0].content == "turn 2"  # First kept message
    assert summary == "Merged high-density summary"
