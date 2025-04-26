#!/usr/bin/env python3
"""
Direct FastAPI Server for Apache Solr document search.

This server mimics the MCP functionality but uses FastAPI directly to ensure
HTTP accessibility on port 8765. This approach addresses the limitation in
MCP 1.6.0 where the FastMCP server doesn't expose a standard HTTP interface.
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
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fastapi-solr-server")

# Load environment variables
load_dotenv()

# Server configuration
SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8765"))
SERVER_HOST = "0.0.0.0"  # Explicitly bind to all interfaces

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


# Input models for validation
class SearchParams(BaseModel):
    """Parameters for a search query."""
    query: str = Field(description="The search query")
    rows: int = Field(default=5, description="Number of results to return")


# Initialize FastAPI app
app = FastAPI(
    title="Solr Search API",
    description="API for searching Apache Solr documents",
    version="1.0.0"
)

# Initialize the solr client
solr_client = SolrClient(
    base_url=SOLR_BASE_URL,
    collection=SOLR_COLLECTION,
    username=SOLR_USERNAME,
    password=SOLR_PASSWORD
)


@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    logger.info("Starting FastAPI Solr Search server")
    
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
        logger.warning("Server will start but Solr searches may fail")


# Server info endpoint (mimics MCP server_info)
@app.get("/server_info")
async def server_info():
    """Get server information (mimics MCP server_info endpoint)."""
    return {
        "name": "Solr Search API",
        "version": "1.0.0",
        "tools": ["search"],
        "resources": ["solr://search/{query}"]
    }


# Tool endpoint for search (mimics MCP tool endpoint)
@app.post("/tool/search")
async def tool_search(params: SearchParams):
    """
    Search endpoint that mimics the MCP tool interface.
    
    Args:
        params (SearchParams): Search parameters
        
    Returns:
        Dict[str, Any]: Search results from Solr
    """
    try:
        logger.info(f"Processing search tool request with params: {params}")
        results = await solr_client.search(query=params.query)
        return results
    except Exception as e:
        logger.error(f"Error in search tool: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing search: {str(e)}")


# Resource endpoint for search (mimics MCP resource endpoint)
@app.get("/resource/solr://search/{query}")
async def resource_search(query: str):
    """
    Resource endpoint that mimics the MCP resource interface.
    
    Args:
        query (str): The search query
        
    Returns:
        str: JSON string with search results
    """
    try:
        logger.info(f"Processing search resource request with query: {query}")
        results = await solr_client.search(query=query)
        return results
    except Exception as e:
        logger.error(f"Error in search resource: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing search: {str(e)}")


# Fallback for direct URL-encoded resource URLs
@app.get("/resource/{path:path}")
async def resource_fallback(path: str, request: Request):
    """Fallback handler for URL-encoded resource paths."""
    try:
        # Handle URL-encoded paths like "solr%3A%2F%2Fsearch%2F%2A%3A%2A"
        if path.startswith("solr://search/") or path.startswith("solr%3A%2F%2Fsearch%2F"):
            # Extract the query part
            query = path.split("/")[-1]
            logger.info(f"Fallback resource handler processing query: {query}")
            results = await solr_client.search(query=query)
            return results
        else:
            return {"error": f"Unsupported resource path: {path}"}
    except Exception as e:
        logger.error(f"Error in resource fallback: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing resource: {str(e)}")


if __name__ == "__main__":
    # Print startup information
    print("=" * 40)
    print(f"FastAPI Solr Search Server")
    print(f"- Host: {SERVER_HOST}")
    print(f"- Port: {SERVER_PORT}")
    print("=" * 40)
    print(f"Server starting on http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"You can test with: curl -X POST http://localhost:{SERVER_PORT}/tool/search -H \"Content-Type: application/json\" -d '{{\"query\": \"*:*\"}}'")
    print(f"OpenAPI documentation available at: http://localhost:{SERVER_PORT}/docs")
    
    # Run the FastAPI app with uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)