#!/usr/bin/env python3
"""
Direct MCP Server for Apache Solr document search.

This version runs the server directly without development mode,
making it accessible to direct HTTP requests on port 8765.
"""
import os
import json
import logging
import traceback
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("direct-mcp-server")

# Load environment variables
load_dotenv()

# MCP server configuration
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8765"))
# Explicitly set the host to 0.0.0.0 to accept connections from all interfaces
MCP_SERVER_HOST = "0.0.0.0"

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
app = FastMCP("Direct Solr Search")

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
    
    async def test_solr():
        try:
            logger.info("Testing Solr connection...")
            async with httpx.AsyncClient() as client:
                ping_url = f"{SOLR_BASE_URL}/{SOLR_COLLECTION}/admin/ping"
                response = await client.get(ping_url)
                response.raise_for_status()
                logger.info("Solr connection successful")
        except Exception as e:
            logger.warning(f"Solr connection test failed: {e}")
            logger.warning("Server will start but Solr searches may fail")
    
    # Run the Solr connection test
    asyncio.run(test_solr())
    
    # Run the server - explicitly binding to 0.0.0.0 to accept all connections
    logger.info(f"Starting direct MCP server on http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}...")
    print(f"Server is now listening on http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}")
    print("You can test with: curl -X POST http://localhost:8765/tool/search -H \"Content-Type: application/json\" -d '{\"query\": \"*:*\", \"rows\": 5}'")
    
    try:
        # Try to enforce the binding settings
        import uvicorn
        import inspect
        from mcp.server.fastmcp import FastMCP
        
        # Print information about the FastMCP run method to understand how it's binding
        print("\nFastMCP run method signature:", inspect.signature(app.run))
        print("=" * 40)
        
        # Attempt direct binding with uvicorn if possible
        try:
            # First try the app.run() method with explicit parameters
            app.run(host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)
        except TypeError:
            # If that fails, try running without parameters (relies on env vars)
            print("TypeError with explicit parameters, falling back to environment variables")
            app.run()
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(traceback.format_exc())