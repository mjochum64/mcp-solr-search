#!/usr/bin/env python3
"""
Minimal MCP Server for Apache Solr to test MCP 1.6.0 compatibility.

This is a stripped-down version of the server to isolate and fix TaskGroup errors.
"""
import os
import logging
import json
import traceback
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
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
logger = logging.getLogger("minimal-mcp-server")

# Load environment variables
load_dotenv()

# MCP server configuration
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8765"))
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")

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


@asynccontextmanager
async def lifespan(app):
    """
    Lifespan context manager for the MCP server.
    
    Args:
        app: The MCP application instance
        
    Yields:
        None: In MCP 1.6.0, the lifespan must yield None or nothing
    """
    logger.info("Initializing minimal MCP server resources...")
    
    # Initialize the Solr client
    solr_client = SolrClient(
        base_url=SOLR_BASE_URL,
        collection=SOLR_COLLECTION,
        username=SOLR_USERNAME,
        password=SOLR_PASSWORD
    )
    
    # Store in app state
    app.state.solr_client = solr_client
    
    # Test Solr connection
    try:
        logger.info("Testing Solr connection...")
        async with httpx.AsyncClient() as client:
            ping_url = f"{SOLR_BASE_URL}/{SOLR_COLLECTION}/admin/ping"
            response = await client.get(ping_url)
            response.raise_for_status()
            logger.info("Solr connection successful")
    except Exception as e:
        logger.warning(f"Solr connection test failed: {e}")
    
    # Simple yield with no return value
    yield
    
    # Cleanup when server stops
    logger.info("Server shutting down...")


# Create the MCP server
app = FastMCP("Minimal Solr Search", lifespan=lifespan)


@app.resource("test://hello")
async def hello_resource():
    """
    Simple test resource.
    
    Returns:
        str: A greeting message
    """
    return "Hello from Minimal MCP Server!"


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
        solr_client = app.state.solr_client
        results = await solr_client.search(query)
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Error in search_solr resource: {e}")
        logger.error(traceback.format_exc())
        return json.dumps({"error": f"Error processing search: {str(e)}"}, indent=2)


@app.tool()
async def echo(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple echo tool for testing.
    
    Args:
        params (Dict[str, Any]): Parameters to echo back
        
    Returns:
        Dict[str, Any]: The same parameters echoed back
    """
    logger.info(f"Echo tool called with params: {params}")
    return {"echoed": params}


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
        solr_client = app.state.solr_client
        
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
    
    # Run the server
    logger.info(f"Starting minimal MCP server on http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}...")
    try:
        app.run()
    except Exception as e:
        logger.error(f"Error starting MCP server: {e}")
        logger.error(traceback.format_exc())
