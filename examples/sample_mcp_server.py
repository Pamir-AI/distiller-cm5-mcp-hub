#!/usr/bin/env python3
"""
Sample MCP Server for Testing
A comprehensive example MCP server with various tools for demonstration
"""

import asyncio
import json
import time
import os
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional


class SampleMCPServer:
    """Sample MCP Server with various tools for testing"""
    
    def __init__(self):
        self.name = "Sample MCP Server"
        self.version = "1.0.0"
        self.start_time = time.time()
        self.call_count = 0
        
    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        uptime = time.time() - self.start_time
        return {
            "name": self.name,
            "version": self.version,
            "uptime_seconds": uptime,
            "call_count": self.call_count,
            "capabilities": ["tools", "resources"],
            "tools_count": len(await self.list_tools())
        }
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        return [
            {
                "name": "echo",
                "description": "Echo back the input message with optional formatting",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo back"
                        },
                        "uppercase": {
                            "type": "boolean",
                            "description": "Convert message to uppercase",
                            "default": False
                        },
                        "repeat": {
                            "type": "integer",
                            "description": "Number of times to repeat the message",
                            "default": 1,
                            "minimum": 1,
                            "maximum": 10
                        }
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "calculate",
                "description": "Perform basic mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["add", "subtract", "multiply", "divide", "power", "sqrt"],
                            "description": "Mathematical operation to perform"
                        },
                        "a": {
                            "type": "number",
                            "description": "First number"
                        },
                        "b": {
                            "type": "number",
                            "description": "Second number (not required for sqrt)"
                        }
                    },
                    "required": ["operation", "a"]
                }
            },
            {
                "name": "hash_text",
                "description": "Generate hash of input text using various algorithms",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to hash"
                        },
                        "algorithm": {
                            "type": "string",
                            "enum": ["md5", "sha1", "sha256", "sha512"],
                            "description": "Hash algorithm to use",
                            "default": "sha256"
                        },
                        "encoding": {
                            "type": "string",
                            "enum": ["hex", "base64"],
                            "description": "Output encoding format",
                            "default": "hex"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "get_timestamp",
                "description": "Get current timestamp in various formats",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "enum": ["unix", "iso", "readable", "custom"],
                            "description": "Timestamp format",
                            "default": "iso"
                        },
                        "custom_format": {
                            "type": "string",
                            "description": "Custom strftime format (only used with format='custom')",
                            "default": "%Y-%m-%d %H:%M:%S"
                        },
                        "timezone": {
                            "type": "string",
                            "description": "Timezone (UTC, local, or timezone name)",
                            "default": "UTC"
                        }
                    }
                }
            },
            {
                "name": "generate_data",
                "description": "Generate various types of test data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data_type": {
                            "type": "string",
                            "enum": ["uuid", "random_string", "random_number", "lorem_ipsum"],
                            "description": "Type of data to generate"
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of items to generate",
                            "default": 1,
                            "minimum": 1,
                            "maximum": 100
                        },
                        "length": {
                            "type": "integer",
                            "description": "Length for string data types",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 1000
                        },
                        "min_value": {
                            "type": "number",
                            "description": "Minimum value for random numbers",
                            "default": 0
                        },
                        "max_value": {
                            "type": "number",
                            "description": "Maximum value for random numbers",
                            "default": 100
                        }
                    },
                    "required": ["data_type"]
                }
            },
            {
                "name": "server_stats",
                "description": "Get server statistics and status",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "include_system": {
                            "type": "boolean",
                            "description": "Include system information",
                            "default": False
                        }
                    }
                }
            }
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool with given arguments"""
        self.call_count += 1
        
        try:
            if name == "echo":
                return await self._tool_echo(arguments)
            elif name == "calculate":
                return await self._tool_calculate(arguments)
            elif name == "hash_text":
                return await self._tool_hash_text(arguments)
            elif name == "get_timestamp":
                return await self._tool_get_timestamp(arguments)
            elif name == "generate_data":
                return await self._tool_generate_data(arguments)
            elif name == "server_stats":
                return await self._tool_server_stats(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
                
        except Exception as e:
            return {
                "error": str(e),
                "tool": name,
                "arguments": arguments
            }
    
    async def _tool_echo(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Echo tool implementation"""
        message = args.get("message", "")
        uppercase = args.get("uppercase", False)
        repeat = args.get("repeat", 1)
        
        if uppercase:
            message = message.upper()
        
        result = " ".join([message] * repeat)
        
        return {
            "echo": result,
            "original": args.get("message"),
            "modifications": {
                "uppercase": uppercase,
                "repeat": repeat
            },
            "length": len(result)
        }
    
    async def _tool_calculate(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate tool implementation"""
        operation = args.get("operation")
        a = args.get("a")
        b = args.get("b")
        
        result = None
        
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Division by zero")
            result = a / b
        elif operation == "power":
            result = a ** b
        elif operation == "sqrt":
            if a < 0:
                raise ValueError("Cannot take square root of negative number")
            result = a ** 0.5
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        return {
            "result": result,
            "operation": operation,
            "operands": {"a": a, "b": b} if b is not None else {"a": a},
            "expression": self._format_expression(operation, a, b, result)
        }
    
    def _format_expression(self, op: str, a: float, b: Optional[float], result: float) -> str:
        """Format mathematical expression"""
        if op == "add":
            return f"{a} + {b} = {result}"
        elif op == "subtract":
            return f"{a} - {b} = {result}"
        elif op == "multiply":
            return f"{a} × {b} = {result}"
        elif op == "divide":
            return f"{a} ÷ {b} = {result}"
        elif op == "power":
            return f"{a}^{b} = {result}"
        elif op == "sqrt":
            return f"√{a} = {result}"
        return f"{op}({a}, {b}) = {result}"
    
    async def _tool_hash_text(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Hash text tool implementation"""
        import base64
        
        text = args.get("text", "")
        algorithm = args.get("algorithm", "sha256")
        encoding = args.get("encoding", "hex")
        
        # Get hash function
        if algorithm == "md5":
            hasher = hashlib.md5()
        elif algorithm == "sha1":
            hasher = hashlib.sha1()
        elif algorithm == "sha256":
            hasher = hashlib.sha256()
        elif algorithm == "sha512":
            hasher = hashlib.sha512()
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        # Calculate hash
        hasher.update(text.encode('utf-8'))
        
        # Format output
        if encoding == "hex":
            hash_value = hasher.hexdigest()
        elif encoding == "base64":
            hash_value = base64.b64encode(hasher.digest()).decode('utf-8')
        else:
            raise ValueError(f"Unknown encoding: {encoding}")
        
        return {
            "hash": hash_value,
            "algorithm": algorithm,
            "encoding": encoding,
            "input_length": len(text),
            "hash_length": len(hash_value)
        }
    
    async def _tool_get_timestamp(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get timestamp tool implementation"""
        format_type = args.get("format", "iso")
        custom_format = args.get("custom_format", "%Y-%m-%d %H:%M:%S")
        timezone = args.get("timezone", "UTC")
        
        now = datetime.now()
        
        if format_type == "unix":
            timestamp = time.time()
        elif format_type == "iso":
            timestamp = now.isoformat()
        elif format_type == "readable":
            timestamp = now.strftime("%A, %B %d, %Y at %I:%M:%S %p")
        elif format_type == "custom":
            timestamp = now.strftime(custom_format)
        else:
            raise ValueError(f"Unknown format: {format_type}")
        
        return {
            "timestamp": timestamp,
            "format": format_type,
            "timezone": timezone,
            "unix_time": time.time(),
            "iso_time": now.isoformat()
        }
    
    async def _tool_generate_data(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data tool implementation"""
        import uuid
        import random
        import string
        
        data_type = args.get("data_type")
        count = args.get("count", 1)
        length = args.get("length", 10)
        min_value = args.get("min_value", 0)
        max_value = args.get("max_value", 100)
        
        data = []
        
        for _ in range(count):
            if data_type == "uuid":
                data.append(str(uuid.uuid4()))
            elif data_type == "random_string":
                chars = string.ascii_letters + string.digits
                data.append(''.join(random.choice(chars) for _ in range(length)))
            elif data_type == "random_number":
                if isinstance(min_value, int) and isinstance(max_value, int):
                    data.append(random.randint(min_value, max_value))
                else:
                    data.append(random.uniform(min_value, max_value))
            elif data_type == "lorem_ipsum":
                words = ["lorem", "ipsum", "dolor", "sit", "amet", "consectetur", 
                        "adipiscing", "elit", "sed", "do", "eiusmod", "tempor", 
                        "incididunt", "ut", "labore", "et", "dolore", "magna", "aliqua"]
                selected_words = random.choices(words, k=min(length, len(words)))
                data.append(" ".join(selected_words))
            else:
                raise ValueError(f"Unknown data type: {data_type}")
        
        return {
            "data": data if count > 1 else data[0],
            "type": data_type,
            "count": count,
            "parameters": {
                "length": length,
                "min_value": min_value,
                "max_value": max_value
            }
        }
    
    async def _tool_server_stats(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Server stats tool implementation"""
        include_system = args.get("include_system", False)
        
        uptime = time.time() - self.start_time
        stats = {
            "server_info": await self.get_server_info(),
            "performance": {
                "uptime_seconds": uptime,
                "uptime_formatted": self._format_uptime(uptime),
                "total_calls": self.call_count,
                "calls_per_second": self.call_count / uptime if uptime > 0 else 0
            }
        }
        
        if include_system:
            stats["system"] = {
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                "platform": os.name,
                "cwd": os.getcwd(),
                "pid": os.getpid()
            }
        
        return stats
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        
        return " ".join(parts)


async def test_server():
    """Test the MCP server functionality"""
    server = SampleMCPServer()
    
    print(f"🚀 Testing {server.name} v{server.version}")
    print("=" * 50)
    
    # Get server info
    info = await server.get_server_info()
    print(f"📊 Server Info: {info}")
    print()
    
    # List tools
    tools = await server.list_tools()
    print(f"🔧 Available tools ({len(tools)}):")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")
    print()
    
    # Test each tool
    test_cases = [
        ("echo", {"message": "Hello MCP!", "uppercase": True, "repeat": 2}),
        ("calculate", {"operation": "add", "a": 15, "b": 27}),
        ("calculate", {"operation": "sqrt", "a": 64}),
        ("hash_text", {"text": "Hello World", "algorithm": "sha256"}),
        ("get_timestamp", {"format": "readable"}),
        ("generate_data", {"data_type": "uuid", "count": 3}),
        ("server_stats", {"include_system": True})
    ]
    
    print("🧪 Running test cases:")
    for tool_name, arguments in test_cases:
        print(f"\n  Testing {tool_name} with {arguments}")
        result = await server.call_tool(tool_name, arguments)
        print(f"  Result: {json.dumps(result, indent=2, default=str)}")
    
    print("\n✅ All tests completed!")


async def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        await test_server()
    else:
        # Start server in interactive mode
        server = SampleMCPServer()
        print(f"🚀 Starting {server.name} v{server.version}")
        print("📡 Server ready for MCP protocol communication")
        print("🔧 Use 'python sample_mcp_server.py test' to run tests")
        
        # Keep server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Server shutting down...")


if __name__ == "__main__":
    asyncio.run(main()) 