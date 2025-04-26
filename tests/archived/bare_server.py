#!/usr/bin/env python3
"""
Ultra minimal MCP server for testing MCP 1.6.0 compatibility.

This is the most basic server implementation possible to isolate TaskGroup errors.
"""
import os
import json
import logging
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
logger = logging.getLogger("bare-mcp-server")

# Load environment variables
load_dotenv()

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
            import traceback
            logger.error(traceback.format_exc())
            return {"error": f"Error in search: {str(e)}"}


class SearchParams(BaseModel):
    """Parameters for a search query."""
    query: str = Field(description="The search query")


# Create the MCP server without lifespan
app = FastMCP("Bare Solr Search")

# Initialize the solr client as a global variable
solr_client = SolrClient(
    base_url=SOLR_BASE_URL,
    collection=SOLR_COLLECTION,
    username=SOLR_USERNAME,
    password=SOLR_PASSWORD
)


@app.resource("test://hello")
async def hello_resource():
    """Simple test resource."""
    return "Hello from bare MCP server!"


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
        import traceback
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
        import traceback
        logger.error(traceback.format_exc())
        return {"error": f"Error processing search: {str(e)}"}


if __name__ == "__main__":
    # Set required environment variables
    os.environ["MCP_PORT"] = "8765"
    os.environ["HOST"] = "0.0.0.0"
    
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
    
    # Run the server
    logger.info(f"Starting bare MCP server on http://0.0.0.0:8765...")
    try:
        app.run()
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        import traceback
        logger.error(traceback.format_exc())