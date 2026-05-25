import asyncio
import json
import sys


class StdioMcpClient:
    """
    A robust, asynchronous Stdio-based MCP Client that communicates with
    MCP Tool Servers using the JSON-RPC 2.0 specification over standard input/output pipes.
    """
    def __init__(self, command: str, args: list):
        self.command = command
        self.args = args
        self.process = None
        self.request_id = 1

    async def connect(self):
        """
        Spawns the MCP server process with standard pipes redirect.
        """
        try:
            self.process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to launch MCP server {self.command}: {str(e)}")

    async def _send_request(self, method: str, params: dict) -> dict:
        """
        Sends a standard JSON-RPC 2.0 request over stdin and reads response from stdout.
        """
        if not self.process or self.process.returncode is not None:
            raise RuntimeError("MCP Server process is not running.")

        current_id = self.request_id
        self.request_id += 1

        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": current_id
        }

        # Write to server stdin
        payload = json.dumps(request) + "\n"
        self.process.stdin.write(payload.encode("utf-8"))
        await self.process.stdin.drain()

        # Read response from server stdout
        response_line = await self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("MCP Server closed pipe unexpectedly.")

        response = json.loads(response_line.decode("utf-8").strip())
        if "error" in response:
            raise RuntimeError(f"MCP Server Error: {response['error']}")

        return response.get("result", {})

    async def list_tools(self) -> list:
        """
        Queries tools/list on the MCP server.
        """
        res = await self._send_request("tools/list", {})
        return res.get("tools", [])

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """
        Queries tools/call on the MCP server to execute a tool.
        """
        res = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        # Format tool result blocks
        content_blocks = res.get("content", [])
        output = []
        for block in content_blocks:
            if block.get("type") == "text":
                output.append(block.get("text", ""))
        return "\n".join(output)

    async def disconnect(self):
        """
        Gracefully kills the subprocess.
        """
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except Exception:
                pass
