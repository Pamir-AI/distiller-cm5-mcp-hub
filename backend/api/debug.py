"""
Debug API endpoints for MCP-Inspector integration
"""

import ast
import asyncio
import json
import time
import os
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pathlib import Path

from backend.models.project import (
    DebugRequest, DebugResponse, MCPServerInfo, MCPTool, ProjectStatus
)
from backend.services.project_manager import project_manager
from config.settings import settings

router = APIRouter()

class DebugManager:
    """Manages debug sessions and MCP-Inspector integration"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
    
    async def start_debug_session(self, project_id: str) -> bool:
        """Start a debug session for the project"""
        project = await project_manager.get_project(project_id)
        if not project:
            return False
        
        try:
            # Update project status
            project.status = ProjectStatus.DEBUGGING
            project.debug_session_active = True
            await project_manager._save_project_metadata(project)
            
            # Check if session already exists with tools
            if project_id in self.active_sessions:
                tools = self.active_sessions[project_id].get("tools", [])
                if tools:
                    print(f"🎯 Debug session started, using {len(tools)} cached tools")
                    return True
            
            # Initialize debug session if it doesn't exist
            if project_id not in self.active_sessions:
                self.active_sessions[project_id] = {
                    "start_time": time.time(),
                    "mcp_server": None,
                    "tools": [],
                    "resources": []
                }
            
            # Only discover tools if we don't have them cached
            tools = self.active_sessions[project_id].get("tools", [])
            if not tools:
                print(f"🔍 No cached tools found, discovering MCP capabilities...")
                await self._discover_mcp_capabilities(project_id)
            else:
                print(f"✅ Using {len(tools)} cached tools for debug session")
            
            return True
            
        except Exception as e:
            print(f"Failed to start debug session: {e}")
            return False
    
    async def stop_debug_session(self, project_id: str) -> bool:
        """Stop the debug session"""
        try:
            project = await project_manager.get_project(project_id)
            if project:
                project.debug_session_active = False
                project.status = ProjectStatus.CREATED
                await project_manager._save_project_metadata(project)
            
            if project_id in self.active_sessions:
                del self.active_sessions[project_id]
            
            if project_id in self.websocket_connections:
                await self.websocket_connections[project_id].close()
                del self.websocket_connections[project_id]
            
            return True
            
        except Exception as e:
            print(f"Failed to stop debug session: {e}")
            return False
    
    async def execute_tool(self, project_id: str, debug_request: DebugRequest) -> DebugResponse:
        """Execute an MCP tool"""
        if project_id not in self.active_sessions:
            raise HTTPException(status_code=400, detail="No active debug session")
        
        start_time = time.time()
        
        # DEBUG: Log exactly what we're receiving
        print(f"🐛 DEBUG - Tool execution request:")
        print(f"   📋 Tool name: {debug_request.tool_name}")
        print(f"   📋 Parameters: {debug_request.parameters}")
        print(f"   📋 Parameters type: {type(debug_request.parameters)}")
        if hasattr(debug_request, '__dict__'):
            print(f"   📋 Full request: {debug_request.__dict__}")
        
        try:
            # Get the project
            project = await project_manager.get_project(project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            # Execute the actual MCP tool
            result = await self._execute_real_tool(
                project, 
                debug_request.tool_name, 
                debug_request.parameters
            )
            
            execution_time = time.time() - start_time
            
            return DebugResponse(
                success=True,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return DebugResponse(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    async def get_server_info(self, project_id: str) -> MCPServerInfo:
        """Get MCP server information"""
        if project_id not in self.active_sessions:
            raise HTTPException(status_code=400, detail="No active debug session")
        
        session = self.active_sessions[project_id]
        
        return MCPServerInfo(
            name=f"MCP Server - {project_id}",
            version="1.0.0",
            tools=session.get("tools", []),
            resources=session.get("resources", [])
        )
    
    async def _discover_mcp_capabilities(self, project_id: str):
        """Discover MCP tools and resources from the project"""
        project = await project_manager.get_project(project_id)
        if not project:
            print(f"❌ Project not found: {project_id}")
            return

        project_path = Path(project.path)
        print(f"🔍 Discovering MCP tools in: {project_path}")
        print(f"📁 Project path exists: {project_path.exists()}")

        tools = []
        
        # Method 1: Try to get tools from running MCP server (real MCP protocol)
        try:
            print(f"🚀 Attempting to discover tools via MCP protocol...")
            main_files = ['main.py', 'server.py', 'app.py', '__main__.py']
            main_file = None
            
            for filename in main_files:
                if (project_path / filename).exists():
                    main_file = filename
                    break
            
            if main_file:
                mcp_client = MCPClient(project_path, main_file)
                try:
                    await mcp_client.start()
                    await mcp_client.initialize()
                    
                    # Get tools from the actual MCP server
                    mcp_tools = await mcp_client.list_tools()
                    
                    print(f"✅ Found {len(mcp_tools)} tools via MCP protocol")
                    
                    for tool in mcp_tools:
                        print(f"  🔧 {tool.get('name')}: {tool.get('description', 'No description')}")
                        tools.append(MCPTool(
                            name=tool.get('name', 'unnamed'),
                            description=tool.get('description', f"MCP Tool: {tool.get('name')}"),
                            parameters=tool.get('inputSchema', {"type": "object", "properties": {}})
                        ))
                    
                except Exception as e:
                    print(f"⚠️ MCP protocol discovery failed: {e}")
                    # Continue to static analysis fallback
                finally:
                    try:
                        await mcp_client.stop()
                    except:
                        pass
        except Exception as e:
            print(f"⚠️ Could not attempt MCP protocol discovery: {e}")
        
        # Method 2: Static analysis fallback (if no tools found via MCP protocol)
        if not tools:
            print(f"📝 No tools found via MCP protocol, trying static analysis...")
            await self._discover_tools_via_static_analysis(project_path, tools)
        
        print(f"📊 Total tools discovered: {len(tools)}")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        # Update session with discovered tools - ensure session exists first
        if project_id not in self.active_sessions:
            print(f"📝 Creating new session for project {project_id}")
            self.active_sessions[project_id] = {
                "start_time": time.time(),
                "tools": [],
                "resources": []
            }
        
        print(f"💾 Storing {len(tools)} tools in session")
        self.active_sessions[project_id]["tools"] = tools
        print(f"✅ Session updated successfully")

    async def _discover_tools_via_static_analysis(self, project_path: Path, tools: List):
        """Discover MCP tools via static code analysis (fallback method)"""
        # Look for Python files recursively, excluding common directories
        exclude_dirs = {'.venv', 'venv', '.git', '__pycache__', '.pytest_cache', 
                       'node_modules', '.mypy_cache', '.coverage', 'dist', 'build'}
        
        python_files_found = 0
        for py_file in project_path.rglob("*.py"):
            # Skip files in excluded directories - check the full path
            if any(exclude_dir in str(py_file) for exclude_dir in exclude_dirs):
                continue
                
            python_files_found += 1
            try:
                print(f"📄 Scanning file: {py_file.relative_to(project_path)}")
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                print(f"📝 File size: {len(content)} characters")
                print(f"🔍 Contains 'types.Tool': {'types.Tool' in content}")
                print(f"🔍 Contains '@server.list_tools': {'@server.list_tools' in content}")

                # Look for MCP tool definitions using types.Tool
                if "types.Tool" in content and "@server.list_tools" in content:
                    print(f"✨ Found MCP tool file, starting AST parsing...")
                    
                    # Parse the entire file as AST
                    try:
                        tree = ast.parse(content)
                        print(f"🌳 AST parsing successful")
                        
                        function_found = False
                        
                        # Walk through the module body directly instead of using ast.walk()
                        # This ensures we catch all top-level function definitions
                        def find_functions_in_node(node):
                            functions = []
                            if isinstance(node, ast.Module):
                                for child in node.body:
                                    functions.extend(find_functions_in_node(child))
                            elif isinstance(node, ast.FunctionDef):
                                functions.append(node)
                            elif isinstance(node, ast.ClassDef):
                                # Also check inside classes
                                for child in node.body:
                                    functions.extend(find_functions_in_node(child))
                            return functions
                        
                        all_functions = find_functions_in_node(tree)
                        print(f"📊 Found {len(all_functions)} total functions using direct traversal")
                        
                        for node in all_functions:
                            print(f"🔍 Checking function: {node.name} (line {node.lineno})")
                            
                            # Check decorators more thoroughly
                            for decorator in node.decorator_list:
                                print(f"  📝 Decorator type: {type(decorator)}")
                                
                                # Handle @server.list_tools() - Call with Attribute
                                if (isinstance(decorator, ast.Call) and 
                                    isinstance(decorator.func, ast.Attribute)):
                                    print(f"    🎯 Attribute name: {decorator.func.attr}")
                                    if decorator.func.attr == 'list_tools':
                                        print(f"✅ Found @server.list_tools function: {node.name}")
                                        function_found = True
                                        
                                        # Extract tools from return statement
                                        for child in ast.walk(node):
                                            if isinstance(child, ast.Return) and isinstance(child.value, ast.List):
                                                print(f"📋 Found return list with {len(child.value.elts)} elements")
                                                for i, tool_node in enumerate(child.value.elts):
                                                    print(f"🛠️ Processing tool {i+1}")
                                                    if isinstance(tool_node, ast.Call):
                                                        tool_info = self._extract_tool_from_ast(tool_node, content)
                                                        if tool_info and tool_info['name']:
                                                            print(f"✅ Found MCP tool: {tool_info['name']} - {tool_info['description']}")
                                                            tools.append(MCPTool(
                                                                name=tool_info['name'],
                                                                description=tool_info['description'],
                                                                parameters=tool_info['schema']
                                                            ))
                                                        else:
                                                            print(f"⚠️ Failed to extract tool info from node {i+1}")
                                                    else:
                                                        print(f"⚠️ Tool node {i+1} is not a Call: {type(tool_node)}")
                                                # Break after finding the first return list
                                                break
                                        break
                                    
                            if function_found:
                                break
                                
                        if not function_found:
                            print(f"⚠️ No @server.list_tools function found in AST, trying fallback...")
                            # Fallback to regex if AST parsing fails to find the function
                            self._extract_tools_with_regex(content, tools)
                                
                    except Exception as e:
                        print(f"❌ AST parsing failed for {py_file}: {e}, falling back to regex")
                        import traceback
                        traceback.print_exc()
                        # Fallback to regex if AST parsing fails
                        self._extract_tools_with_regex(content, tools)
                
                # Also look for tool handlers as a fallback
                elif "@server.call_tool" in content or "tool_handlers" in content:
                    print(f"🔄 Using tool handlers fallback...")
                    import re
                    
                    # Look for tool_handlers dictionary
                    handler_pattern = r'"([^"]+)":\s*(\w+)ToolHandler\(\)'
                    handler_matches = re.findall(handler_pattern, content)
                    
                    for tool_name, handler_class in handler_matches:
                        print(f"✅ Found tool handler: {tool_name}")
                        tools.append(MCPTool(
                            name=tool_name,
                            description=f"MCP Tool: {tool_name}",
                            parameters={"type": "object", "properties": {}}
                        ))
                
                # Additional fallback: look for function definitions with specific patterns
                elif "playwright" in py_file.name.lower() and "server" in py_file.name.lower():
                    print(f"🔄 Using function definitions fallback...")
                    import re
                    
                    # Look for typical MCP tool patterns
                    func_pattern = r'def (\w+)\([^)]*\):'
                    func_matches = re.findall(func_pattern, content)
                    
                    # Filter for likely tool functions
                    for func_name in func_matches:
                        if (not func_name.startswith('_') and 
                            'handle' in func_name and 
                            func_name != 'handle_call_tool'):
                            # Extract tool name from handler function name
                            tool_name = func_name.replace('handle_', '').replace('_tool', '')
                            print(f"📝 Found potential tool function: {tool_name}")
                            tools.append(MCPTool(
                                name=tool_name,
                                description=f"Playwright tool: {tool_name}",
                                parameters={"type": "object", "properties": {}}
                            ))

            except Exception as e:
                print(f"❌ Error scanning {py_file}: {e}")
                import traceback
                traceback.print_exc()
                continue

        print(f"📊 Scanned {python_files_found} Python files total")

    def _extract_tool_from_ast(self, tool_node, content):
        """Extract tool information from AST node"""
        tool_info = {"name": "", "description": "", "schema": {}}
        
        try:
            if isinstance(tool_node, ast.Call):
                # Extract keyword arguments from types.Tool call
                for keyword in tool_node.keywords:
                    if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                        tool_info["name"] = keyword.value.value
                    elif keyword.arg == "description" and isinstance(keyword.value, ast.Constant):
                        tool_info["description"] = keyword.value.value
                    elif keyword.arg == "inputSchema" and isinstance(keyword.value, ast.Dict):
                        # Convert AST dict to actual dict
                        tool_info["schema"] = self._ast_dict_to_dict(keyword.value)
                        
            return tool_info if tool_info["name"] else None
            
        except Exception as e:
            print(f"❌ Error extracting tool from AST: {e}")
            return None
            
    def _ast_dict_to_dict(self, ast_dict):
        """Convert AST dict node to Python dict"""
        try:
            result = {}
            for key_node, value_node in zip(ast_dict.keys, ast_dict.values):
                if isinstance(key_node, ast.Constant):
                    key = key_node.value
                    if isinstance(value_node, ast.Constant):
                        result[key] = value_node.value
                    elif isinstance(value_node, ast.Dict):
                        result[key] = self._ast_dict_to_dict(value_node)
                    elif isinstance(value_node, ast.List):
                        result[key] = [self._ast_value_to_python(item) for item in value_node.elts]
            return result
        except Exception as e:
            print(f"⚠️ AST dict conversion failed: {e}")
            return {"type": "object", "properties": {}}
    
    def _ast_value_to_python(self, ast_node):
        """Convert AST value node to Python value"""
        if isinstance(ast_node, ast.Constant):
            return ast_node.value
        elif isinstance(ast_node, ast.Dict):
            return self._ast_dict_to_dict(ast_node)
        elif isinstance(ast_node, ast.List):
            return [self._ast_value_to_python(item) for item in ast_node.elts]
        else:
            return str(ast_node)
            
    def _extract_tools_with_regex(self, content, tools):
        """Fallback regex-based tool extraction"""
        import re
        
        # Extract tool definitions from types.Tool(...) patterns with improved regex
        tool_pattern = r'types\.Tool\(\s*name\s*=\s*["\']([^"\']+)["\'][^}]*?description\s*=\s*["\']([^"\']*)["\']'
        matches = re.findall(tool_pattern, content, re.DOTALL)
        
        for tool_name, description in matches:
            print(f"✅ Found MCP tool (regex): {tool_name} - {description}")
            tools.append(MCPTool(
                name=tool_name,
                description=description or f"MCP Tool: {tool_name}",
                parameters={"type": "object", "properties": {}}
            ))

    async def _simulate_tool_execution(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Simulate tool execution for demonstration"""
        # This is a placeholder implementation
        # In reality, this would communicate with the actual MCP server
        
        await asyncio.sleep(0.1)  # Simulate execution time
        
        return {
            "tool": tool_name,
            "parameters": parameters,
            "result": f"Executed {tool_name} with parameters: {parameters}",
            "timestamp": time.time()
        }

    async def _execute_real_tool(self, project, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a real MCP tool using actual MCP protocol communication"""
        project_path = Path(project.path)
        
        # Look for main files in multiple locations
        main_files = ['main.py', 'server.py', 'app.py', '__main__.py']
        search_dirs = [
            project_path,                           # Root directory
            project_path / 'src',                   # src/ directory
            project_path / 'src' / 'playwright_server',  # specific playwright project structure
            project_path / 'server',                # server/ directory
        ]
        
        main_file_path = None
        main_file = None
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
                
            for filename in main_files:
                file_path = search_dir / filename
                if file_path.exists():
                    main_file_path = file_path
                    main_file = filename
                    print(f"📁 Found MCP server file: {file_path}")
                    break
            
            if main_file_path:
                break
        
        if not main_file_path:
            # Show all searched locations in error
            searched_locations = []
            for search_dir in search_dirs:
                if search_dir.exists():
                    searched_locations.append(str(search_dir))
            
            raise RuntimeError(
                f"No MCP server file found. Looking for: {', '.join(main_files)} "
                f"in directories: {', '.join(searched_locations)}"
            )
        
        print(f"🚀 Starting real MCP tool execution: {tool_name} with {parameters}")
        
        # Start MCP server process
        mcp_client = MCPClient(main_file_path.parent, main_file)
        await mcp_client.start()
        
        try:
            # Initialize MCP connection
            print(f"🔗 Initializing MCP connection...")
            init_result = await mcp_client.initialize()
            print(f"✅ MCP initialized: {init_result}")
            
            # List available tools to verify the tool exists
            print(f"📋 Listing available tools...")
            tools = await mcp_client.list_tools()
            print(f"🔧 Available tools: {[t.get('name') for t in tools]}")
            
            # Check if the requested tool exists
            tool_found = any(tool.get('name') == tool_name for tool in tools)
            if not tool_found:
                available_tools = [tool.get('name') for tool in tools]
                raise ValueError(f"Tool '{tool_name}' not found. Available tools: {available_tools}")
            
            # Execute the tool
            print(f"⚡ Executing tool '{tool_name}' with arguments: {parameters}")
            result = await mcp_client.call_tool(tool_name, parameters)
            print(f"🎯 Tool execution result: {result}")
            
            # Also capture any stderr output from the MCP server
            stderr_output = await mcp_client.get_stderr_output()
            if stderr_output:
                print(f"📝 MCP Server stderr output: {stderr_output}")
            
            return {
                "result": result,
                "tool_name": tool_name,
                "parameters": parameters,
                "mcp_server_stderr": stderr_output,
                "execution_method": "real_mcp_protocol"
            }
            
        finally:
            await mcp_client.stop()

class MCPClient:
    """MCP Client for communicating with MCP servers via JSON-RPC"""
    
    def __init__(self, project_path: Path, main_file: str):
        self.project_path = project_path
        self.main_file = main_file
        self.process = None
        self.request_id = 0
        self.stderr_buffer = []
    
    async def start(self):
        """Start the MCP server process"""
        env = os.environ.copy()
        env['PYTHONPATH'] = str(self.project_path)
        
        print(f"🚀 Starting MCP server: {self.main_file} in {self.project_path}")
        
        # Use the project's own venv Python if available, fallback to system Python
        # self.project_path is src/playwright_server, so we need to go up 2 levels to project root
        project_root = self.project_path.parent.parent  # Go up from src/playwright_server to project root
        project_venv_python = project_root / ".venv" / "bin" / "python"
        
        print(f"🔍 Looking for venv at: {project_venv_python}")
        if project_venv_python.exists():
            python_command = str(project_venv_python)
            print(f"📦 Using project's venv Python: {python_command}")
        else:
            python_command = settings.python_command
            print(f"⚠️ Project venv not found, using system Python: {python_command}")
        
        # Start the MCP server process with stdio communication
        print(f"🔧 Starting subprocess with command: {python_command} {self.main_file}")
        print(f"🔧 Working directory: {self.project_path}")
        print(f"🔧 Environment PYTHONPATH: {env.get('PYTHONPATH', 'Not set')}")
        
        self.process = await asyncio.create_subprocess_exec(
            python_command, self.main_file,
            cwd=str(self.project_path),
            env=env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        print(f"📋 Process created with PID: {self.process.pid}")
        
        # Start background task to capture stderr
        asyncio.create_task(self._capture_stderr())
        
        # Give the process a moment to start
        print(f"⏳ Waiting for process to initialize...")
        await asyncio.sleep(2)
        
        if self.process.returncode is not None:
            stderr_content = '\n'.join(self.stderr_buffer)
            print(f"❌ Process failed to start!")
            print(f"📝 Exit code: {self.process.returncode}")
            print(f"📝 Stderr content: {stderr_content}")
            raise RuntimeError(f"MCP server process failed to start (code: {self.process.returncode}). Stderr: {stderr_content}")
        
        print(f"✅ MCP server started with PID: {self.process.pid}")
    
    async def _capture_stderr(self):
        """Capture stderr output in the background"""
        if not self.process or not self.process.stderr:
            return
        
        try:
            while self.process.returncode is None:
                line = await self.process.stderr.readline()
                if line:
                    stderr_line = line.decode().strip()
                    print(f"[MCP-STDERR] {stderr_line}")
                    self.stderr_buffer.append(stderr_line)
                else:
                    break
        except Exception as e:
            print(f"Error capturing stderr: {e}")
    
    async def get_stderr_output(self):
        """Get collected stderr output"""
        return '\n'.join(self.stderr_buffer) if self.stderr_buffer else ""
    
    async def stop(self):
        """Stop the MCP server process"""
        if self.process and self.process.returncode is None:
            print(f"⏹️ Stopping MCP server process {self.process.pid}")
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
                print(f"✅ MCP server stopped gracefully")
            except asyncio.TimeoutError:
                print(f"🔪 Force killing MCP server process")
                self.process.kill()
                await self.process.wait()
    
    def _get_next_id(self):
        """Get the next request ID"""
        self.request_id += 1
        return self.request_id
    
    async def _send_request(self, method: str, params: dict = None):
        """Send a JSON-RPC request to the MCP server"""
        if not self.process or self.process.returncode is not None:
            raise RuntimeError("MCP server process is not running")
        
        request = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": method
        }
        
        if params:
            request["params"] = params
        
        # Send the request
        request_json = (json.dumps(request) + "\n").encode()
        print(f"📤 Sending MCP request: {method}")
        print(f"📋 Request details: {json.dumps(request, indent=2)}")
        
        self.process.stdin.write(request_json)
        await self.process.stdin.drain()
        
        # Read the response
        print(f"⏳ Waiting for MCP response...")
        response_line = await asyncio.wait_for(
            self.process.stdout.readline(), 
            timeout=30  # Increased timeout for tool execution
        )
        
        if not response_line:
            stderr_content = '\n'.join(self.stderr_buffer)
            raise RuntimeError(f"No response from MCP server. Stderr: {stderr_content}")
        
        response_text = response_line.decode().strip()
        print(f"📥 Received MCP response: {response_text}")
        
        try:
            response = json.loads(response_text)
        except json.JSONDecodeError as e:
            stderr_content = '\n'.join(self.stderr_buffer)
            raise RuntimeError(f"Invalid JSON response: {response_text}. Stderr: {stderr_content}")
        
        # Check for JSON-RPC errors
        if "error" in response:
            error = response["error"]
            raise RuntimeError(f"MCP Error {error.get('code', 'Unknown')}: {error.get('message', 'Unknown error')}")
        
        return response.get("result")
    
    async def initialize(self):
        """Initialize the MCP connection"""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "MCP Development Platform",
                "version": "1.0.0"
            }
        }
        
        result = await self._send_request("initialize", params)
        
        # Send initialized notification
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        notification_json = (json.dumps(notification) + "\n").encode()
        print(f"📤 Sending initialized notification")
        self.process.stdin.write(notification_json)
        await self.process.stdin.drain()
        
        return result
    
    async def list_tools(self):
        """List available tools from the MCP server"""
        result = await self._send_request("tools/list")
        return result.get("tools", [])
    
    async def call_tool(self, name: str, arguments: dict):
        """Call a specific tool on the MCP server"""
        params = {
            "name": name,
            "arguments": arguments
        }
        
        print(f"🔧 Calling tool '{name}' with arguments: {json.dumps(arguments, indent=2)}")
        result = await self._send_request("tools/call", params)
        print(f"📋 Raw tool result: {json.dumps(result, indent=2) if isinstance(result, dict) else result}")
        
        # Handle different result formats
        if isinstance(result, dict):
            # Check for MCP tool result format
            if "content" in result:
                # MCP standard result format
                content = result["content"]
                if isinstance(content, list) and len(content) > 0:
                    # Return the first content item
                    first_content = content[0]
                    if isinstance(first_content, dict) and "text" in first_content:
                        return first_content["text"]
                    return first_content
                return content
            elif "isError" in result and result["isError"]:
                # MCP error result
                raise RuntimeError(result.get("content", ["Unknown error"])[0])
            else:
                # Direct result
                return result
        
        return result

# Global debug manager instance
debug_manager = DebugManager()

@router.post("/debug/{project_id}/start")
async def start_debug_session(project_id: str):
    """Start a debug session"""
    success = await debug_manager.start_debug_session(project_id)
    if success:
        return {"message": "Debug session started", "project_id": project_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to start debug session")

@router.post("/debug/{project_id}/stop")
async def stop_debug_session(project_id: str):
    """Stop a debug session"""
    success = await debug_manager.stop_debug_session(project_id)
    if success:
        return {"message": "Debug session stopped", "project_id": project_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to stop debug session")

@router.post("/debug/{project_id}/execute", response_model=DebugResponse)
async def execute_tool(project_id: str, debug_request: DebugRequest):
    """Execute an MCP tool"""
    try:
        response = await debug_manager.execute_tool(project_id, debug_request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/{project_id}/info", response_model=MCPServerInfo)
async def get_debug_info(project_id: str):
    """Get debug session information"""
    try:
        info = await debug_manager.get_server_info(project_id)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/{project_id}/status")
async def get_debug_status(project_id: str):
    """Get the current debug session status"""
    try:
        project = await project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        is_active = project_id in debug_manager.active_sessions
        session_info = debug_manager.active_sessions.get(project_id, {})
        
        return {
            "active": is_active,
            "debug_session_active": project.debug_session_active,
            "start_time": session_info.get("start_time"),
            "tools_count": len(session_info.get("tools", [])),
            "resources_count": len(session_info.get("resources", []))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/{project_id}/tools")
async def get_debug_tools(project_id: str):
    """Get available tools for the debug session"""
    try:
        print(f"🔍 Getting tools for project: {project_id}")
        
        # Check if we already have a session with tools
        if project_id in debug_manager.active_sessions:
            tools = debug_manager.active_sessions[project_id].get("tools", [])
            if tools:
                print(f"✅ Using cached tools: {len(tools)} tools found")
                for tool in tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                response = {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.parameters
                        }
                        for tool in tools
                    ]
                }
                
                print(f"🚀 Returning {len(response['tools'])} cached tools to frontend")
                return response
        
        print(f"📝 No cached tools found, discovering tools...")
        # Only discover tools if we don't have them cached
        await debug_manager._discover_mcp_capabilities(project_id)
        
        # Create session if it doesn't exist
        if project_id not in debug_manager.active_sessions:
            print(f"⚠️ No session created after discovery, creating empty session...")
            debug_manager.active_sessions[project_id] = {
                "start_time": time.time(),
                "tools": [],
                "resources": []
            }
        
        session = debug_manager.active_sessions[project_id]
        tools = session.get("tools", [])
        
        print(f"📊 Session has {len(tools)} tools after discovery")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        response = {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.parameters
                }
                for tool in tools
            ]
        }
        
        print(f"🚀 Returning {len(response['tools'])} tools to frontend")
        return response
        
    except Exception as e:
        print(f"❌ Error in get_debug_tools: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/debug/{project_id}/test")
async def test_tool(project_id: str, debug_request: DebugRequest):
    """Test an MCP tool with given parameters"""
    try:
        # Check if project exists
        project = await project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # If no active session, try to discover tools
        if project_id not in debug_manager.active_sessions:
            await debug_manager._discover_mcp_capabilities(project_id)
            if project_id not in debug_manager.active_sessions:
                debug_manager.active_sessions[project_id] = {
                    "start_time": time.time(),
                    "tools": [],
                    "resources": []
                }
        
        # Execute the tool
        response = await debug_manager.execute_tool(project_id, debug_request)
        
        return {
            "success": response.success,
            "result": response.result,
            "error": response.error,
            "execution_time": response.execution_time
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "execution_time": 0.0
        }

@router.websocket("/debug/{project_id}/ws")
async def websocket_debug_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for real-time debug communication"""
    await websocket.accept()
    debug_manager.websocket_connections[project_id] = websocket
    
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "execute_tool":
                debug_request = DebugRequest(**message.get("data", {}))
                response = await debug_manager.execute_tool(project_id, debug_request)
                
                await websocket.send_text(json.dumps({
                    "type": "tool_response",
                    "data": response.model_dump()
                }))
            
            elif message.get("type") == "get_tools":
                info = await debug_manager.get_server_info(project_id)
                await websocket.send_text(json.dumps({
                    "type": "tools_list",
                    "data": [tool.model_dump() for tool in info.tools]
                }))
            
    except WebSocketDisconnect:
        if project_id in debug_manager.websocket_connections:
            del debug_manager.websocket_connections[project_id] 