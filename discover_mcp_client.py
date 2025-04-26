#!/usr/bin/env python3
"""
This script attempts to discover the correct MCP client module structure.
It will try different import paths and report which ones are available.
"""
import sys
import importlib

def test_import(module_path):
    """Test if a module can be imported and return details about it."""
    try:
        module = importlib.import_module(module_path)
        print(f"✓ Successfully imported: {module_path}")
        
        # Try to find Client class
        if hasattr(module, "Client"):
            print(f"  ✓ Found Client class in {module_path}")
            return True
        else:
            print(f"  ✗ No Client class in {module_path}")
            
        # Print available attributes
        attrs = [attr for attr in dir(module) if not attr.startswith("_")]
        if attrs:
            print(f"  Available attributes: {', '.join(attrs[:10])}")
            if len(attrs) > 10:
                print(f"  ... and {len(attrs) - 10} more")
        return False
    except ImportError as e:
        print(f"✗ Import failed for: {module_path}")
        print(f"  Error: {e}")
        return False

# List of potential MCP client module paths to try
potential_paths = [
    "mcp",
    "mcp.client",
    "mcp.client.sync",
    "mcp.client.async_client",
    "mcp.client.lowlevel",
    "mcp.client.highlevel",
    "mcp.api",
    "mcp.api.client"
]

print("Attempting to discover MCP client module structure...\n")

# Try searching for modules
success = False
for path in potential_paths:
    if test_import(path):
        success = True
        print(f"\nRecommendation: Try 'from {path} import Client'\n")

# If we found the base module but not the client, check its contents
if not success and test_import("mcp"):
    import mcp
    print("\nExploring mcp package structure:")
    
    # Try to find all modules
    mcp_dir = dir(mcp)
    modules = [item for item in mcp_dir if not item.startswith("_")]
    print(f"Available modules in mcp: {', '.join(modules)}")
    
    # If we found a 'client' attribute, check its structure
    if hasattr(mcp, "client"):
        print("\nExploring mcp.client structure:")
        client_dir = dir(mcp.client)
        client_attrs = [item for item in client_dir if not item.startswith("_")]
        print(f"Available attributes in mcp.client: {', '.join(client_attrs)}")
        
print("\nNote: If none of these imports work, check if the MCP package is properly installed.")
print("You can install it with: pip install mcp[cli]")