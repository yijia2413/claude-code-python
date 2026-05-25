import json
import os
import asyncio
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, create_model, Field

from claude_code.mcp.client import StdioMcpClient

# Global registry of active MCP clients
# Key: server_name, Value: StdioMcpClient
ACTIVE_MCP_CLIENTS = {}


def load_mcp_config() -> dict:
    """
    Loads MCP config from ~/.claude/mcp.json or returns empty default.
    """
    config_path = os.path.expanduser("~/.claude/mcp.json")
    if not os.path.exists(config_path):
        # Create empty template
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        default_config = {"mcpServers": {}}
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=2)
        return default_config

    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception:
        return {"mcpServers": {}}


async def initialize_mcp_servers() -> list:
    """
    Connects to all configured MCP servers and registers their tools dynamically.
    Returns a list of LangChain StructuredTool objects.
    """
    config = load_mcp_config()
    servers = config.get("mcpServers", {})
    
    mcp_tools = []
    
    for name, srv_config in servers.items():
        command = srv_config.get("command")
        args = srv_config.get("args", [])
        
        if not command:
            continue
            
        client = StdioMcpClient(command, args)
        try:
            await client.connect()
            # Cache active client
            ACTIVE_MCP_CLIENTS[name] = client
            
            # Query tool list
            tools_def = await client.list_tools()
            for t in tools_def:
                tool_name = f"mcp_{name}_{t['name']}"
                tool_desc = t.get("description", f"MCP Tool from server {name}")
                
                # Define dynamic execution callback
                # We capture client and original tool name using closures
                def make_call(c=client, orig_name=t['name']):
                    async def call_wrapper(**kwargs):
                        return await c.call_tool(orig_name, kwargs)
                    return lambda **kwargs: asyncio.run(call_wrapper(**kwargs))

                # Build StructuredTool from dynamic schema
                mcp_tools.append(StructuredTool.from_function(
                    func=make_call(),
                    name=tool_name,
                    description=tool_desc,
                ))
        except Exception:
            # Silently skip offline servers
            continue
            
    return mcp_tools


def close_mcp_servers():
    """
    Terminates all active MCP processes.
    """
    for client in ACTIVE_MCP_CLIENTS.values():
        try:
            asyncio.run(client.disconnect())
        except Exception:
            pass
    ACTIVE_MCP_CLIENTS.clear()
