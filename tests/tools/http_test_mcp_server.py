#!/usr/bin/env python3
"""
Simple HTTP-based test client for the MCP server.
This script uses standard HTTP requests to interact with the MCP server
without requiring the MCP client libraries.
"""
import asyncio
import json
import httpx

# MCP Server URL
MCP_SERVER_URL = "http://localhost:8765"

async def test_mcp_server():
    """Test the MCP server using direct HTTP requests."""
    async with httpx.AsyncClient() as client:
        print("Testing MCP server connectivity...")
        
        # 1. First test basic connectivity using the info endpoint
        try:
            response = await client.get(f"{MCP_SERVER_URL}/mcp/v1/info")
            if response.status_code == 200:
                print("✓ Server is reachable")
                info = response.json()
                print(f"Server name: {info.get('name')}")
                print(f"Available tools: {', '.join(info.get('tools', []))}")
                print(f"Available resources: {', '.join(info.get('resources', []))}")
                print("\n" + "-" * 60 + "\n")
            else:
                print(f"✗ Server returned status {response.status_code}")
                print(response.text)
                return
        except Exception as e:
            print(f"✗ Connection error: {e}")
            print("Make sure the MCP server is running on http://localhost:8765")
            return
        
        # 2. Test the search tool
        print("Testing 'search' tool...")
        try:
            tool_url = f"{MCP_SERVER_URL}/mcp/v1/tools/search"
            payload = {
                "query": "Apache",
                "filter_query": "category:technology",
                "rows": 3
            }
            
            response = await client.post(tool_url, json=payload)
            if response.status_code == 200:
                search_results = response.json()
                print("✓ Search tool successful")
                print(json.dumps(search_results, indent=2))
            else:
                print(f"✗ Search tool failed with status {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"✗ Error testing search tool: {e}")
            
        print("\n" + "-" * 60 + "\n")
        
        # 3. Test the get_document tool
        print("Testing 'get_document' tool...")
        try:
            tool_url = f"{MCP_SERVER_URL}/mcp/v1/tools/get_document"
            payload = {
                "id": "doc1"
            }
            
            response = await client.post(tool_url, json=payload)
            if response.status_code == 200:
                doc_result = response.json()
                print("✓ get_document tool successful")
                print(json.dumps(doc_result, indent=2))
            else:
                print(f"✗ get_document tool failed with status {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"✗ Error testing get_document tool: {e}")
            
        print("\n" + "-" * 60 + "\n")
        
        # 4. Test the search resource
        print("Testing 'solr://search/{query}' resource...")
        try:
            # URL encode the resource string
            resource_name = "solr://search/Python"
            encoded_resource = httpx.URL(f"{MCP_SERVER_URL}/mcp/v1/resources").join(
                resource_name
            )
            
            response = await client.get(str(encoded_resource))
            if response.status_code == 200:
                resource_result = response.text  # Resources return plain strings
                print("✓ Resource request successful")
                print(resource_result)
            else:
                print(f"✗ Resource request failed with status {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"✗ Error testing resource: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())