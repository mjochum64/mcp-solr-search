#!/usr/bin/env python3
"""
Simple script to test HTTP connections to the MCP server.
This bypasses the MCP client library and tests raw HTTP connections.
"""
import requests
import sys
import json
import socket
from urllib.parse import urljoin

def check_socket_connection(host='localhost', port=8765):
    """
    Test if a TCP socket connection can be established to the given host and port.
    
    Args:
        host (str): Hostname to connect to
        port (int): Port to connect to
        
    Returns:
        bool: True if connection succeeded, False otherwise
    """
    print(f"Testing socket connection to {host}:{port}...")
    try:
        # Create a socket object
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set a timeout for the connection attempt (2 seconds)
        s.settimeout(2)
        # Attempt to connect
        result = s.connect_ex((host, port))
        s.close()
        
        if result == 0:
            print(f"✅ Socket connection to {host}:{port} succeeded")
            return True
        else:
            print(f"❌ Socket connection to {host}:{port} failed (error code: {result})")
            return False
    except Exception as e:
        print(f"❌ Socket connection error: {str(e)}")
        return False

def test_mcp_tool_endpoint(base_url='http://localhost:8765', tool_name='search'):
    """
    Test a specific MCP tool endpoint using direct HTTP POST.
    
    Args:
        base_url (str): Base URL of the MCP server
        tool_name (str): Name of the tool to test
    """
    url = urljoin(base_url, f'/tool/{tool_name}')
    headers = {'Content-Type': 'application/json'}
    payload = {'query': '*:*', 'rows': 5}
    
    print(f"Testing HTTP POST to {url}...")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response body: {response.text[:500]}...")  # First 500 chars
        return response
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Error during request: {str(e)}")
        return None

def test_mcp_resource_endpoint(base_url='http://localhost:8765'):
    """
    Test an MCP resource endpoint using direct HTTP GET.
    
    Args:
        base_url (str): Base URL of the MCP server
    """
    # URL-encoded resource path for solr://search/*:*
    url = urljoin(base_url, '/resource/solr%3A%2F%2Fsearch%2F%2A%3A%2A')
    
    print(f"Testing HTTP GET to {url}...")
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response body: {response.text[:500]}...")  # First 500 chars
        return response
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Error during request: {str(e)}")
        return None

def check_server_info(base_url='http://localhost:8765'):
    """Test the MCP server info endpoint."""
    url = urljoin(base_url, '/server_info')
    
    print(f"Testing server info endpoint: {url}...")
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Server name: {data.get('name')}")
            print(f"Server version: {data.get('version')}")
            print(f"Available tools: {', '.join(data.get('tools', []))}")
            print(f"Available resources: {', '.join(data.get('resources', []))}")
        return response
    except Exception as e:
        print(f"❌ Error connecting to server info: {str(e)}")
        return None

def main():
    # Define server parameters (with defaults)
    host = 'localhost'
    port = 8765
    base_url = f'http://{host}:{port}'
    
    # Parse command-line arguments if provided
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        if '://' not in base_url:
            base_url = f'http://{base_url}'
    
    print(f"Testing MCP server at: {base_url}")
    print("=" * 50)
    
    # First check if the socket connection works
    socket_ok = check_socket_connection(host, port)
    print("=" * 50)
    
    # Try to get server info
    server_info = check_server_info(base_url)
    print("=" * 50)
    
    if not socket_ok:
        print("❌ Socket connection failed. The server may not be running or might be listening on a different port/interface.")
        print("Suggestions:")
        print("1. Check if the server is running")
        print("2. Verify it's binding to the correct interface (0.0.0.0 for all interfaces)")
        print("3. Check for firewall rules blocking the connection")
        print("4. Try using a different port")
        return
    
    # Test the tool endpoint
    test_mcp_tool_endpoint(base_url)
    print("=" * 50)
    
    # Test the resource endpoint
    test_mcp_resource_endpoint(base_url)

if __name__ == "__main__":
    main()