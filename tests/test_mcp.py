import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from claude_code.mcp.client import StdioMcpClient


@pytest.mark.asyncio
async def test_mcp_client_rpc_roundtrip(monkeypatch):
    client = StdioMcpClient("uvx", ["mcp-server-sqlite"])
    
    # Mock subprocess streams
    mock_process = AsyncMock()
    mock_process.returncode = None
    mock_process.stdin = AsyncMock()
    mock_process.stdout = AsyncMock()
    
    # Simulate tools/list response
    mock_response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "tools": [
                {
                    "name": "query_db",
                    "description": "Run sqlite queries",
                    "inputSchema": {"type": "object"}
                }
            ]
        }
    }
    
    response_payload = json.dumps(mock_response).encode("utf-8") + b"\n"
    mock_process.stdout.readline = AsyncMock(return_value=response_payload)
    
    # Inject mock process
    client.process = mock_process
    
    # Test tools/list query
    tools = await client.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "query_db"
    
    # Verify JSON-RPC payload was written to stdin
    mock_process.stdin.write.assert_called_once()
    written_data = mock_process.stdin.write.call_args[0][0].decode("utf-8")
    request = json.loads(written_data.strip())
    assert request["method"] == "tools/list"
    assert request["id"] == 1
