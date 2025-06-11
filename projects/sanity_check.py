#!/usr/bin/env python3
"""
Universal sanity check script for MCP Servers
Tests basic MCP functionality: server info and tool listing
Works with any MCP server implementation
"""

import argparse
import json
import requests
import sys
from typing import Dict, Any

def create_endpoints_config(port: int) -> list:
    """Create endpoint configurations with the specified port"""
    return [
        {
            "name": "SSE Transport",
            "url": f"http://localhost:{port}/sse",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "text/event-stream",  # Accept SSE format
            },
            "is_sse": True
        },
        {
            "name": "Streamable HTTP Transport", 
            "url": f"http://localhost:{port}/mcp",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            "is_sse": False
        }
    ]

def parse_sse_response(response_text: str) -> Dict[str, Any]:
    """Parse SSE event-stream response to extract JSON data"""
    lines = response_text.strip().split('\n')
    for line in lines:
        if line.startswith('data: '):
            json_data = line[6:]  # Remove 'data: ' prefix
            if json_data.strip():
                try:
                    return json.loads(json_data)
                except json.JSONDecodeError as e:
                    print(f"   ⚠️  Failed to parse SSE JSON: {e}")
                    print(f"   📄 Raw data: {json_data}")
                    return {}
    return {}

def make_mcp_request(endpoint_config: Dict[str, Any], method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make an MCP JSON-RPC request to the server"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method
    }
    
    if params:
        payload["params"] = params
    
    try:
        response = requests.post(
            endpoint_config["url"], 
            json=payload, 
            headers=endpoint_config["headers"], 
            timeout=10
        )
        response.raise_for_status()
        
        # Handle different response formats
        if endpoint_config.get("is_sse", False):
            # Parse SSE event-stream format
            return parse_sse_response(response.text)
        else:
            # Parse regular JSON
            return response.json()
            
    except requests.exceptions.RequestException as e:
        raise e

def test_endpoint(endpoint_config: Dict[str, Any]) -> bool:
    """Test a specific endpoint"""
    print(f"\n🔍 Testing {endpoint_config['name']} at {endpoint_config['url']}")
    
    try:
        # Test 1: Initialize
        print("   📡 Testing initialize...")
        response = make_mcp_request(endpoint_config, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "universal-sanity-check",
                "version": "1.0.0"
            }
        })
        
        if "error" in response:
            print(f"   ❌ Initialize failed: {response['error']}")
            return False
        
        if not response:  # Empty response
            print(f"   ❌ Initialize failed: Empty response")
            return False
        
        result = response.get("result", {})
        server_info = result.get("serverInfo", {})
        
        print(f"   ✅ Initialize successful!")
        print(f"      📛 Name: {server_info.get('name', 'Unknown')}")
        print(f"      📋 Version: {server_info.get('version', 'Unknown')}")
        print(f"      🔧 Protocol Version: {result.get('protocolVersion', 'Unknown')}")
        
        # Test 2: List tools
        print("   🔧 Testing tools/list...")
        response = make_mcp_request(endpoint_config, "tools/list")
        
        if "error" in response:
            print(f"   ❌ Tools list failed: {response['error']}")
            return False
        
        if not response:  # Empty response
            print(f"   ❌ Tools list failed: Empty response")
            return False
        
        result = response.get("result", {})
        tools = result.get("tools", [])
        
        if not tools:
            print("   ⚠️  No tools found (this might be normal for some servers)")
        else:
            print(f"   ✅ Found {len(tools)} tools")
            
            # Show first few tools
            for i, tool in enumerate(tools[:3], 1):
                name = tool.get("name", "Unknown")
                description = tool.get("description", "No description")
                if len(description) > 60:
                    description = description[:57] + "..."
                print(f"      {i}. 🔧 {name}: {description}")
            
            if len(tools) > 3:
                print(f"      ... and {len(tools) - 3} more tools")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection failed")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"   ❌ HTTP error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_server_connectivity(port: int):
    """Test basic connectivity to the server"""
    print("🔍 Testing basic server connectivity...")
    
    try:
        # Try the health endpoint first if it exists
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            print(f"✅ Server is responding via /health (status: {response.status_code})")
            return True
        except requests.exceptions.RequestException:
            pass  # Health endpoint might not exist, try other methods
        
        # Try a simple GET request to root with short timeout (server might use SSE)
        try:
            response = requests.get(f"http://localhost:{port}", timeout=2)
            print(f"✅ Server is responding (status: {response.status_code})")
            return True
        except requests.exceptions.ReadTimeout:
            # Server responded but kept connection open (likely SSE) - this is OK
            print(f"✅ Server is responding (SSE stream detected)")
            return True
        except requests.exceptions.ConnectionError:
            print(f"❌ ERROR: Could not connect to server at http://localhost:{port}")
            print("   Make sure your MCP server is running on this port")
            return False
            
    except Exception as e:
        print(f"⚠️  Server connectivity check failed: {e}")
        return False

def main():
    """Run the sanity check"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Universal sanity check script for MCP Servers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Test on default port 8000
  %(prog)s --port 3000        # Test on port 3000
  %(prog)s -p 9000            # Test on port 9000
        """
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port number to test (default: 8000)"
    )
    
    args = parser.parse_args()
    
    print("🚀 Universal MCP Server - Sanity Check")
    print("=" * 60)
    print(f"🌐 Testing multiple transport endpoints on port {args.port}")
    print()
    
    # Create endpoint configurations with the specified port
    endpoints_to_test = create_endpoints_config(args.port)
    
    # Test 0: Basic connectivity
    connectivity_ok = test_server_connectivity(args.port)
    if not connectivity_ok:
        sys.exit(1)
    
    # Test each endpoint
    successful_endpoints = []
    failed_endpoints = []
    
    for endpoint_config in endpoints_to_test:
        if test_endpoint(endpoint_config):
            successful_endpoints.append(endpoint_config["name"])
        else:
            failed_endpoints.append(endpoint_config["name"])
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"   Basic Connectivity: {'✅ PASS' if connectivity_ok else '❌ FAIL'}")
    
    if successful_endpoints:
        print(f"   ✅ Working Endpoints ({len(successful_endpoints)}):")
        for endpoint in successful_endpoints:
            print(f"      • {endpoint}")
    
    if failed_endpoints:
        print(f"   ❌ Failed Endpoints ({len(failed_endpoints)}):")
        for endpoint in failed_endpoints:
            print(f"      • {endpoint}")
    
    if successful_endpoints:
        print("\n🎉 At least one transport is working correctly!")
        print("💡 Recommendation: Use the working endpoint for your MCP client")
        print(f"💡 Working endpoints available on port {args.port}")
        if "SSE Transport" in successful_endpoints:
            print("🌟 SSE Transport is working - great for streaming responses!")
        if "Streamable HTTP Transport" in successful_endpoints:
            print("🌟 HTTP Transport is working - great for standard JSON-RPC!")
        sys.exit(0)
    else:
        print("\n💥 No transports are working. Check the server configuration.")
        print("💡 Make sure your MCP server is running and supports these transports:")
        print(f"   • SSE endpoint: http://localhost:{args.port}/sse")
        print(f"   • HTTP endpoint: http://localhost:{args.port}/mcp")
        sys.exit(1)

if __name__ == "__main__":
    main() 