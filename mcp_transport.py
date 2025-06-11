"""
Standalone MCP Transport Layer
Supports stdio, HTTP, and SSE transports for MCP servers
"""

import asyncio
import argparse
from typing import Dict, Any, Callable, List
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json

# Optional MCP imports - gracefully handle if not available
try:
    import mcp.server.stdio
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Create dummy classes for when MCP is not available
    class InitializationOptions:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class NotificationOptions:
        pass


class MCPTransport:
    """Standalone MCP transport layer that can be used with any MCP server"""
    
    def __init__(self, 
                 server_name: str,
                 server_version: str = "0.1.0",
                 server_description: str = "MCP Server"):
        self.server_name = server_name
        self.server_version = server_version
        self.server_description = server_description
        
        # Handler functions - to be set by the using server
        self.list_tools_handler: Callable = None
        self.call_tool_handler: Callable = None
        self.list_resources_handler: Callable = None
        self.read_resource_handler: Callable = None
        self.list_prompts_handler: Callable = None
        self.get_prompt_handler: Callable = None
        self.health_check_handler: Callable = None
        
        # MCP server instance for stdio transport
        self.mcp_server = None
    
    def set_handlers(self,
                    list_tools: Callable = None,
                    call_tool: Callable = None,
                    list_resources: Callable = None,
                    read_resource: Callable = None,
                    list_prompts: Callable = None,
                    get_prompt: Callable = None,
                    health_check: Callable = None):
        """Set the handler functions for MCP operations"""
        self.list_tools_handler = list_tools
        self.call_tool_handler = call_tool
        self.list_resources_handler = list_resources if list_resources else []
        self.read_resource_handler = read_resource if read_resource else []
        self.list_prompts_handler = list_prompts if list_prompts else []
        self.get_prompt_handler = get_prompt if get_prompt else []
        self.health_check_handler = health_check
    
    def set_mcp_server(self, server):
        """Set the MCP server instance for stdio transport"""
        self.mcp_server = server
    
    async def handle_mcp_request(self, data: dict, transport: str = "http"):
        """Handle MCP JSON-RPC requests consistently across endpoints"""
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        print(f"Method: {method}")
        print(f"Params: {params}")
        print(f"Request ID: {request_id}")
        
        try:
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": True},
                            "resources": {"subscribe": True, "listChanged": True},
                            "prompts": {},
                            "experimental": {}
                        },
                        "serverInfo": {
                            "name": self.server_name,
                            "version": self.server_version
                        }
                    }
                }
                if transport == "sse":
                    yield f"data: {json.dumps(response)}\n\n"
                else:
                    yield response
            
            elif method == "tools/list":
                if self.list_tools_handler:
                    tools = await self.list_tools_handler()
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"tools": [tool.model_dump() for tool in tools]}
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"tools": []}
                    }
                
                if transport == "sse":
                    yield f"data: {json.dumps(response)}\n\n"
                else:
                    yield response
            
            elif method == "tools/call":
                if self.call_tool_handler:
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    result = await self.call_tool_handler(tool_name, arguments)
                    response = {
                        "jsonrpc": "2.0", 
                        "id": request_id,
                        "result": {
                            "content": [content.model_dump() for content in result]
                        }
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": "Tools not supported"}
                    }
                
                if transport == "sse":
                    yield f"data: {json.dumps(response)}\n\n"
                else:
                    yield response
            
            elif method == "resources/list":
                if self.list_resources_handler:
                    resources = await self.list_resources_handler()
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"resources": [
                            {
                                "uri": str(resource.uri), 
                                "name": resource.name, 
                                "description": resource.description, 
                                "mimeType": resource.mimeType, 
                                "annotations": getattr(resource, 'annotations', None)
                            } for resource in resources
                        ]}
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"resources": []}
                    }
                
                if transport == "sse":
                    yield f"data: {json.dumps(response)}\n\n"
                else:
                    yield response
            
            elif method == "resources/read":
                if self.read_resource_handler:
                    uri = params.get("uri")
                    from pydantic import AnyUrl
                    parsed_uri = AnyUrl(uri)
                    result = await self.read_resource_handler(parsed_uri)
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "contents": [{"uri": str(uri), "mimeType": "application/json", "text": result}]
                        }
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": "Resources not supported"}
                    }
                
                if transport == "sse":
                    yield f"data: {json.dumps(response)}\n\n"
                else:
                    yield response
            
            elif method == "prompts/list":
                if self.list_prompts_handler:
                    prompts = await self.list_prompts_handler()
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"prompts": [prompt.model_dump() for prompt in prompts]}
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"prompts": []}
                    }
                
                if transport == "sse":
                    yield f"data: {json.dumps(response)}\n\n"
                else:
                    yield response
            
            elif method == "prompts/get":
                if self.get_prompt_handler:
                    name = params.get("name")
                    arguments = params.get("arguments")
                    result = await self.get_prompt_handler(name, arguments)
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": result.model_dump()
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": "Prompts not supported"}
                    }
                
                if transport == "sse":
                    yield f"data: {json.dumps(response)}\n\n"
                else:
                    yield response
            
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }
                
                if transport == "sse":
                    yield f"data: {json.dumps(response)}\n\n"
                else:
                    yield response
                
        except Exception as e:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -1, "message": str(e)}
            }
            
            if transport == "sse":
                yield f"data: {json.dumps(response)}\n\n"
            else:
                yield response
    
    def create_fastapi_app(self, transport_type: str, host: str, port: int) -> FastAPI:
        """Create and configure FastAPI application"""
        app = FastAPI(title=self.server_description, version=self.server_version)
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, be more specific
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Root endpoint handlers
        @app.get("/")
        async def root_get():
            """Handle GET requests to root endpoint"""
            endpoint = "/sse" if transport_type == 'sse' else "/mcp"
            
            tools = []
            resources = []
            if self.list_tools_handler:
                try:
                    tool_list = await self.list_tools_handler()
                    tools = [tool.name for tool in tool_list]
                except:
                    pass
            
            if self.list_resources_handler:
                try:
                    resource_list = await self.list_resources_handler()
                    resources = [str(resource.uri) for resource in resource_list]
                except:
                    pass
            
            return JSONResponse({
                "service": self.server_description,
                "version": self.server_version,
                "status": "running",
                "transport": transport_type,
                "mcp_available": MCP_AVAILABLE,
                "endpoints": {
                    "mcp": "/mcp" if transport_type == 'http' else None,
                    "sse": "/sse" if transport_type == 'sse' else None,
                    "health": "/health"
                },
                "capabilities": {
                    "tools": tools,
                    "resources": resources
                },
                "message": f"{self.server_description} is running. Use {endpoint} for MCP requests."
            })
        
        @app.post("/")
        async def root_post(request: Request):
            """Handle POST requests to root endpoint - treat as MCP requests"""
            endpoint = "/sse" if transport_type == 'sse' else "/mcp"
            
            try:
                data = await request.json()
                # Check if this looks like an MCP request
                if isinstance(data, dict) and "method" in data:
                    # This appears to be an MCP request, handle it
                    async for response in self.handle_mcp_request(data, transport="http"):
                        return JSONResponse(response)
                        break
                else:
                    # Not an MCP request, return service info
                    return JSONResponse({
                        "service": self.server_description,
                        "version": self.server_version,
                        "status": "running",
                        "transport": transport_type,
                        "mcp_available": MCP_AVAILABLE,
                        "message": "For MCP requests, send JSON-RPC formatted data with 'method' field.",
                        "example_request": {
                            "jsonrpc": "2.0",
                            "id": "1",
                            "method": "tools/list",
                            "params": {}
                        }
                    })
            except Exception as e:
                return JSONResponse({
                    "service": self.server_description,
                    "version": self.server_version,
                    "status": "running",
                    "transport": transport_type,
                    "mcp_available": MCP_AVAILABLE,
                    "error": f"Request processing error: {str(e)}",
                    "message": f"Use {endpoint} for proper MCP requests."
                })
        
        if transport_type == 'sse':
            @app.get("/sse")
            async def sse_get_endpoint():
                """Handle SSE connection establishment"""
                async def generate_events():
                    # Keep connection alive
                    while True:
                        yield f"data: {json.dumps({'type': 'ping'})}\n\n"
                        await asyncio.sleep(30)  # Send ping every 30 seconds
                
                return StreamingResponse(
                    generate_events(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                        "Access-Control-Allow-Headers": "*",
                    }
                )

            @app.post("/sse")
            async def sse_endpoint(request: Request):
                """Handle MCP requests over Server-Sent Events"""
                try:
                    data = await request.json()
                    
                    return StreamingResponse(
                        self.handle_mcp_request(data, transport="sse"),
                        media_type="text/event-stream",
                        headers={
                            "Cache-Control": "no-cache",
                            "Connection": "keep-alive",
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                            "Access-Control-Allow-Headers": "*",
                        }
                    )
                    
                except Exception as e:
                    error_data = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                    }
                    async def error_response():
                        yield f"data: {json.dumps(error_data)}\n\n"
                    
                    return StreamingResponse(
                        error_response(),
                        media_type="text/event-stream"
                    )
        
        @app.post("/mcp")
        async def mcp_endpoint(request: Request):
            """Handle MCP JSON-RPC requests over HTTP"""
            try:
                data = await request.json()
                # Get the first (and only) yielded response from the generator
                async for response in self.handle_mcp_request(data, transport="http"):
                    return JSONResponse(response)
                    break
                    
            except Exception as e:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                })
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            base_health = {
                "status": "healthy", 
                "server": self.server_name,
                "version": self.server_version,
                "transport": transport_type,
                "mcp_available": MCP_AVAILABLE
            }
            
            # Add custom health check if available
            if self.health_check_handler:
                try:
                    custom_health = await self.health_check_handler()
                    base_health.update(custom_health)
                except Exception as e:
                    base_health["custom_health_error"] = str(e)
            
            return base_health
        
        @app.options("/mcp")
        @app.options("/sse")
        @app.options("/")
        async def options_handler():
            """Handle CORS preflight requests"""
            return JSONResponse(
                content="OK",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                }
            )
        
        return app
    
    def create_argument_parser(self, description: str = None) -> argparse.ArgumentParser:
        """Create standard argument parser for MCP transport"""
        if not description:
            description = f'{self.server_description} MCP Server'
        
        parser = argparse.ArgumentParser(description=description)
        parser.add_argument('--transport', choices=['stdio', 'http', 'sse'], default='stdio',
                           help='Transport type: stdio (default), http, or sse')
        parser.add_argument('--host', default='localhost', 
                           help='Host for HTTP transport (default: localhost)')
        parser.add_argument('--port', type=int, default=3000,
                           help='Port for HTTP transport (default: 3000)')
        return parser
    
    async def run_server(self, transport: str, host: str = 'localhost', port: int = 3000):
        """Run the MCP server with the specified transport"""
        if transport in ['http', 'sse']:
            app = self.create_fastapi_app(transport, host, port)
            
            transport_type = "SSE" if transport == 'sse' else "HTTP"
            endpoint = "/sse" if transport == 'sse' else "/mcp"
            
            print(f"🚀 Starting {self.server_description} on {transport_type} transport")
            print(f"📡 Server running at: http://{host}:{port}")
            print(f"🔧 MCP endpoint: http://{host}:{port}{endpoint}")
            print(f"❤️ Health check: http://{host}:{port}/health")
            
            config = uvicorn.Config(
                app=app,
                host=host,
                port=port,
                log_level="info"
            )
            server_instance = uvicorn.Server(config)
            await server_instance.serve()
            
        else:
            # stdio transport
            if not MCP_AVAILABLE:
                raise ValueError("MCP package not available. stdio transport requires 'mcp' package. Use 'http' or 'sse' transport instead.")
            
            if not self.mcp_server:
                raise ValueError("MCP server instance not set for stdio transport")
            
            print(f"🚀 Starting {self.server_description} on stdio transport")
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                await self.mcp_server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=self.server_name,
                        server_version=self.server_version,
                        capabilities=self.mcp_server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                ) 
