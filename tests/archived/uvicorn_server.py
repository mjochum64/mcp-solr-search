#!/usr/bin/env python3
"""
HTTP MCP Server for Apache Solr document search using Uvicorn directly.

This version bypasses the FastMCP run() method limitations by accessing the
underlying ASGI app and serving it with Uvicorn directly for HTTP access.
"""
import os
import json
import logging
import traceback
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import httpx
import uvicorn
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("uvicorn-mcp-server")

# Load environment variables
load_dotenv()

# MCP server configuration
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8765"))
MCP_SERVER_HOST = "0.0.0.0"  # Explicitly bind to all interfaces

# Solr connection configuration
SOLR_BASE_URL = os.getenv("SOLR_BASE_URL", "http://localhost:8983/solr")
SOLR_COLLECTION = os.getenv("SOLR_COLLECTION", "documents")
SOLR_USERNAME = os.getenv("SOLR_USERNAME", "")
SOLR_PASSWORD = os.getenv("SOLR_PASSWORD", "")


@dataclass
class SolrClient:
    """Client for interacting with Apache Solr."""
    
    base_url: str
    collection: str
    username: Optional[str] = None
    password: Optional[str] = None
    
    async def search(self, query: str) -> Dict[str, Any]:
        """
        Execute a simple search query against Solr.
        
        Args:
            query (str): The search query (q parameter)
            
        Returns:
            Dict[str, Any]: The search results from Solr
        """
        params = {
            "q": query,
            "wt": "json",
            "rows": 5,
        }
        
        auth = None
        if self.username and self.password:
            auth = (self.username, self.password)
            
        url = f"{self.base_url}/{self.collection}/select"
        
        try:
            logger.info(f"Sending Solr search request to {url} with query: {query}")
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, auth=auth)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error in Solr search: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"Error in search: {str(e)}"}


class SearchParams(BaseModel):
    """Parameters for a search query."""
    query: str = Field(description="The search query")


# Create the MCP server without lifespan
app = FastMCP("Uvicorn Solr Search")

# Initialize the solr client as a global variable
solr_client = SolrClient(
    base_url=SOLR_BASE_URL,
    collection=SOLR_COLLECTION,
    username=SOLR_USERNAME,
    password=SOLR_PASSWORD
)


@app.resource("solr://search/{query}")
async def search_solr(query: str):
    """
    Simple resource for searching Solr documents.
    
    Args:
        query (str): The search query
        
    Returns:
        str: JSON string with search results
    """
    try:
        logger.info(f"Processing search resource request with query: {query}")
        results = await solr_client.search(query)
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Error in search_solr resource: {e}")
        logger.error(traceback.format_exc())
        return json.dumps({"error": f"Error processing search: {str(e)}"}, indent=2)


@app.tool()
async def search(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool for basic document search.
    
    Args:
        params (Dict[str, Any]): Search parameters including query
        
    Returns:
        Dict[str, Any]: Search results
    """
    try:
        logger.info(f"Processing search tool request with params: {params}")
        search_params = SearchParams(**params)
        results = await solr_client.search(query=search_params.query)
        return results
    except Exception as e:
        logger.error(f"Error in search tool: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Error processing search: {str(e)}"}


async def test_solr_connection():
    """Test the Solr connection before starting the server."""
    try:
        logger.info("Testing Solr connection...")
        async with httpx.AsyncClient() as client:
            ping_url = f"{SOLR_BASE_URL}/{SOLR_COLLECTION}/admin/ping"
            response = await client.get(ping_url)
            response.raise_for_status()
            logger.info("Solr connection successful")
        return True
    except Exception as e:
        logger.warning(f"Solr connection test failed: {e}")
        logger.warning("Server will start but Solr searches may fail")
        return False


if __name__ == "__main__":
    # Set environment variables for the MCP server
    os.environ["MCP_PORT"] = str(MCP_SERVER_PORT)
    os.environ["HOST"] = MCP_SERVER_HOST
    os.environ["MCP_DEBUG"] = "1"  # Enable debug mode
    
    # Print diagnostics about the environment and configuration
    print("=" * 40)
    print(f"MCP Server Configuration:")
    print(f"- Host: {MCP_SERVER_HOST}")
    print(f"- Port: {MCP_SERVER_PORT}")
    print(f"- Environment variables set:")
    print(f"  - MCP_PORT={os.environ.get('MCP_PORT')}")
    print(f"  - HOST={os.environ.get('HOST')}")
    print(f"  - MCP_DEBUG={os.environ.get('MCP_DEBUG')}")
    print("=" * 40)
    
    # Test Solr connection before starting
    import asyncio
    asyncio.run(test_solr_connection())
    
    # Run the server using uvicorn directly
    # This bypasses the FastMCP.run() method which doesn't support host/port params in MCP 1.6.0
    logger.info(f"Starting Uvicorn MCP server on http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}...")
    print(f"Server starting on http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}")
    print(f"You can test with: curl -X POST http://localhost:{MCP_SERVER_PORT}/tool/search -H \"Content-Type: application/json\" -d '{{\"query\": \"*:*\", \"rows\": 5}}'")
    
    # Access the underlying ASGI app from FastMCP
    from inspect import getmembers
    
    # Try to find the ASGI app in the FastMCP instance
    try:
        # FastMCP may store its ASGI app in different attributes based on the version
        # Common attribute names: app, asgi_app, application, _app
        asgi_app = None
        
        # Check for known attribute names
        for attr in ['app', 'asgi_app', 'application', '_app']:
            if hasattr(app, attr):
                potential_app = getattr(app, attr)
                print(f"Found potential ASGI app in app.{attr}")
                asgi_app = potential_app
                break
        
        # If not found in known attributes, inspect all attributes
        if not asgi_app:
            print("Searching for ASGI app in all attributes...")
            for name, value in getmembers(app):
                # Skip private attributes and methods
                if name.startswith('_') and name != '_app':
                    continue
                print(f"Checking attribute: {name}")
            
            # Last resort: look at app.__dict__
            if hasattr(app, '__dict__'):
                print("App __dict__ keys:", app.__dict__.keys())
        
        # If we found an ASGI app, run it with uvicorn
        if asgi_app:
            print(f"Running ASGI app with uvicorn on {MCP_SERVER_HOST}:{MCP_SERVER_PORT}")
            uvicorn.run(asgi_app, host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)
        else:
            # If we can't find the ASGI app, fall back to passing the FastMCP instance directly
            # Some uvicorn versions can auto-detect ASGI apps
            print(f"Falling back to running FastMCP instance directly with uvicorn")
            uvicorn.run(app, host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)
    
    except Exception as e:
        logger.error(f"Error starting server with uvicorn: {e}")
        logger.error(traceback.format_exc())
        
        # Last resort: try running with the standard method
        print("\nFalling back to standard app.run() method")
        try:
            app.run()
        except Exception as e2:
            logger.error(f"Error with fallback method: {e2}")
            logger.error(traceback.format_exc())