---
name: mcp-development
description: Build, test, debug and deploy MCP (Model Context Protocol) servers with Python or TypeScript, covering tool and resource definitions, transports, security, testing and deployment.
license: MIT
compatibility: opencode
metadata:
  category: ai-engineering
  stack: mcp
  version: "1.0.0"
orchestration:
  lead_for:
    - mcp-development
  support_for: []
  conflicts_with: []
---

# MCP Development

Use this skill when building, testing, debugging, or deploying an MCP (Model Context Protocol) server — a server that implements the Model Context Protocol to expose tools, resources, and prompts to AI agents.

The objective is to build MCP servers that are correct, observable, secure, and easy to iterate on.

## When to Use This Skill

Load this skill when the task involves any of the following:

- building a new MCP server from scratch
- adding tools, resources, or prompts to an existing MCP server
- debugging MCP protocol or tool-call failures
- switching between stdio and SSE transport
- testing an MCP server with an inspector or client
- reviewing MCP server design for security, error handling, or reliability
- migrating a tool-based API to the MCP protocol
- writing integration tests for MCP tools and resources

Do not load this skill for:

- general FastAPI or REST API design (use fastapi-backend skill)
- building non-MCP tool-use systems (use structured-output-reliability skill)
- general API security review (use security-review skill)

## Protocol Overview

MCP follows a client-server architecture where the host application (e.g. OpenCode, Claude Desktop) connects to MCP servers that provide capabilities.

### Core Concepts

| Concept | Purpose | Example |
|---------|---------|---------|
| **Tool** | An executable action the agent can invoke | `get_weather(city: str)` |
| **Resource** | Read-only data exposed to the agent | `file:///logs/app.log` |
| **Prompt** | A reusable template the agent can load | `summarize(article)` |
| **Transport** | How client and server communicate | stdio, SSE, WebSocket |
| **Capabilities** | What the server declares it supports | tools, resources, prompts, logging, sampling |

### Lifecycle

1. Server starts and connects via transport (stdio or SSE)
2. Client sends `initialize` request with protocol version and capabilities
3. Server responds with its supported protocol version and capabilities
4. Client sends `initialized` notification
5. Client and server exchange requests and notifications during the session
6. Either side may terminate the session

## Choosing a Transport

| Transport | Use When | Trade-offs |
|-----------|----------|------------|
| **stdio** | Server runs as a subprocess of the client | Low latency; no network attack surface; process lifecycle tied to client |
| **SSE** | Server runs remotely or needs to serve multiple clients | Supports HTTP middleware, auth, scaling; requires reconnection handling |

For local agent tools, stdio is the simplest and most secure choice. Use SSE when you need to deploy the server as a network service.

## Server Setup

### Python (FastMCP — Recommended)

FastMCP provides a high-level, decorator-based API for Python MCP servers.

```python
from fastmcp import FastMCP

server = FastMCP("my-server")

@server.tool()
def my_tool(param: str) -> str:
    """Tool description for agent."""
    return f"Result: {param}"

if __name__ == "__main__":
    server.run(transport="stdio")
```

For SSE transport:

```python
if __name__ == "__main__":
    server.run(transport="sse", host="0.0.0.0", port=8000)
```

### Python (Low-Level SDK)

```python
import asyncio
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent

server = Server("my-server")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="my_tool",
            description="Tool description",
            inputSchema={
                "type": "object",
                "properties": {
                    "param": {"type": "string", "description": "Parameter description"}
                },
                "required": ["param"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "my_tool":
        param = arguments.get("param", "")
        return [TextContent(type="text", text=f"Result: {param}")]
    raise ValueError(f"Unknown tool: {name}")
```

### TypeScript

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
const server = new Server(
  { name: "my-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: "my_tool",
    description: "Tool description",
    inputSchema: {
      type: "object",
      properties: {
        param: { type: "string", description: "Parameter description" }
      },
      required: ["param"]
    }
  }]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "my_tool") {
    const param = request.params.arguments?.param as string;
    return { content: [{ type: "text", text: `Result: ${param}` }] };
  }
  throw new Error(`Unknown tool: ${request.params.name}`);
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Defining Tools

### Tool Schema Contract

Every tool must define:

1. **name** — lowercase with hyphens; unique within the server
2. **description** — clear enough for an LLM to choose correctly
3. **inputSchema** — JSON Schema defining parameters, types, and constraints
4. **return type** — structured content the client can handle

### Tool Design Rules

- **Use narrow tools** over broad ones. Prefer `get_user_by_email(email)` over `execute_query(sql)`.
- **Validate every argument server-side.** Never trust LLM-generated arguments.
- **Make descriptions agent-friendly.** Describe *when* to call the tool, not just what it does.
- **Use required parameters** for mandatory inputs; use optional parameters with defaults otherwise.
- **Return structured content** (TextContent, ImageContent, EmbeddedResource) at the top level.
- **Do not return raw errors.** Catch exceptions and return user-friendly error messages in the content.

```python
@server.tool(description="Fetch a user's profile by their email address. Call this when you need user details like name, role, or department.")
def get_user(email: str) -> str:
    """Fetch user profile."""
    if not email or "@" not in email:
        return "Error: invalid email format"
    user = db.users.find_one({"email": email})
    if not user:
        return "Error: user not found"
    return f"User: {user['name']}, Role: {user['role']}"
```

### Progress Reporting for Long-Running Tools

```python
@server.tool()
async def process_batch(items: list[str], ctx: Context) -> str:
    results = []
    for i, item in enumerate(items):
        results.append(await process(item))
        ctx.report_progress(i + 1, len(items))
    return "\n".join(results)
```

## Defining Resources

Resources expose data to the agent via URI-based access.

```python
@server.resource("file:///logs/{log_id}")
def get_log(log_id: str) -> str:
    """Access a specific log file by ID."""
    content = log_storage.read(log_id)
    if content is None:
        return f"Error: log {log_id} not found"
    return content
```

```python
@server.resource("docs://api/reference")
def api_reference() -> str:
    """API reference documentation available to the agent."""
    return load_markdown("docs/api.md")
```

Resource URIs follow the scheme `{scheme}://{path}`. Use descriptive, hierarchical schemes that make the data source clear.

## Defining Prompts

Prompts are reusable templates the agent can load and optionally fill with arguments.

```python
@server.prompt()
def summarize(text: str, max_length: int = 200) -> str:
    """Summarize the given text."""
    return f"Summarize the following text in {max_length} words or fewer:\n\n{text}"
```

```python
@server.prompt()
def review_code(language: str, code: str) -> str:
    """Review code for bugs and security issues."""
    return f"""You are a {language} code reviewer. Review the following code for:
1. Logic bugs
2. Security vulnerabilities
3. Performance issues

```{language}
{code}
```"""
```

## Logging and Observability

### Server Logging

MCP supports structured logging from the server to the client.

```python
@server.tool()
async def fetch_data(url: str, ctx: Context) -> str:
    await ctx.info(f"Fetching data from {url}")
    try:
        data = await http_client.get(url)
        await ctx.debug(f"Received {len(data)} bytes")
        return data
    except Exception as e:
        await ctx.error(f"Failed to fetch {url}: {e}")
        raise
```

Log levels: `debug`, `info`, `notice`, `warning`, `error`, `critical`.

### Debugging with MCP Inspector

The MCP Inspector is a browser-based tool for testing and debugging MCP servers.

```bash
npx @modelcontextprotocol/inspector python server.py
# Opens http://localhost:5173 with an interactive inspector
```

The inspector lets you:
- view all registered tools, resources, and prompts
- invoke tools with custom arguments
- inspect full request/response payloads
- view server logs in real time
- simulate capability negotiation

### Common Debugging Steps

1. Run the server standalone to check startup errors:
   ```bash
   python server.py
   ```

2. Test with the inspector to verify tool calls work:
   ```bash
   npx @modelcontextprotocol/inspector python server.py
   ```

3. Check transport compatibility: ensure stdio servers don't write non-protocol output to stdout.

4. Validate JSON Schema: tool argument schemas must be valid JSON Schema (draft 2020-12 or compatible).

5. Check for hung connections: tools that block on I/O without timeouts will freeze the client-server session.

## Security

### Input Validation

Every tool argument comes from LLM output, which is untrusted. Validate all inputs server-side:

```python
@server.tool()
def delete_file(path: str) -> str:
    if not path.startswith("/allowed/directory/"):
        return "Error: path must be within allowed directory"
    if ".." in path:
        return "Error: path traversal detected"
    # ... proceed with deletion
```

### Capability Scoping

Declare only the capabilities the server needs:

```python
server = FastMCP("my-server")
# Only tools needed — no resources or prompts declared
# Agent cannot discover or use capabilities not declared
```

### Transport Security

- stdio: no network exposure; safe for local tools
- SSE: add authentication middleware for remote servers
- Always validate the origin of incoming requests in SSE mode
- Use TLS for production SSE/WebSocket servers

### Rate Limiting

For tools that access external APIs or databases, implement rate limiting per session:

```python
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_calls: int, window: timedelta):
        self.max_calls = max_calls
        self.window = window
        self.calls: list[datetime] = []

    def check(self) -> bool:
        now = datetime.now()
        self.calls = [c for c in self.calls if now - c < self.window]
        if len(self.calls) >= self.max_calls:
            return False
        self.calls.append(now)
        return True
```

### Error Handling

- Never expose stack traces or internal paths to the agent
- Return sanitized error messages as TextContent
- Log full errors server-side for debugging
- Use timeouts for all external calls

```python
@server.tool()
async def fetch_external(url: str, ctx: Context) -> str:
    try:
        result = requests.get(url, timeout=10)
        result.raise_for_status()
        return result.text
    except requests.Timeout:
        return "Error: external service timed out"
    except requests.RequestException as e:
        await ctx.error(f"External fetch failed: {e}")
        return "Error: external service unavailable"
```

## Testing

### Unit Tests

Test each tool function in isolation by calling it directly:

```python
def test_get_user():
    result = get_user(email="test@example.com")
    assert result.startswith("User:")
```

### Integration Tests with TestClient

FastMCP and the low-level SDK provide test utilities:

```python
from fastmcp import FastMCP
import pytest

server = FastMCP("test-server")

@server.tool()
def add(a: int, b: int) -> int:
    return a + b

@pytest.mark.asyncio
async def test_add_tool():
    async with server.test_client() as client:
        result = await client.call_tool("add", {"a": 1, "b": 2})
        assert result[0].text == "3"
```

### Protocol Compliance Tests

- Verify `initialize` handshake succeeds
- Verify `list_tools` returns expected tool schemas
- Verify `call_tool` with valid arguments returns expected content
- Verify `call_tool` with invalid arguments returns a graceful error
- Verify unknown tool names return appropriate errors
- Verify tool schemas are valid JSON Schema

### Test Checklist

- [ ] All tools handle both valid and invalid inputs
- [ ] Error responses do not leak internal paths or stack traces
- [ ] Tools with side effects are idempotent when possible
- [ ] Rate limits are tested under high call volume
- [ ] Transport reconnection is tested for SSE servers
- [ ] Tool descriptions are distinct enough for an LLM to disambiguate

## Completion Criteria

An MCP server implementation is complete only when:

- [ ] server initializes and connects via the chosen transport without errors
- [ ] all tools, resources, and prompts are declared in capabilities
- [ ] every tool validates its arguments server-side
- [ ] error responses are safe (no stack traces, no internal paths)
- [ ] tools with external dependencies have timeouts
- [ ] destructive tools have explicit confirmation or authorization checks
- [ ] tests exist for each tool with valid and invalid inputs
- [ ] MCP Inspector confirms all capabilities work as expected
- [ ] server can be shut down cleanly without resource leaks
- [ ] protocol version compatibility is documented

## Dependencies

- Python: `fastmcp` (recommended) or `mcp` SDK
- TypeScript: `@modelcontextprotocol/sdk`
- Inspector: `@modelcontextprotocol/inspector`
- Schema validation: `pydantic` (Python) or `zod` (TypeScript)
