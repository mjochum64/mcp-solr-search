#!/usr/bin/env python3
"""
MCP-Server for Apache Solr document search.

This server exposes Apache Solr search functionality as MCP resources and tools,
allowing LLMs to search and retrieve documents from Solr collections.
"""
import os
import sys
import json
import logging
import traceback
import socket
import threading
import time
from typing import Dict, List, Optional, Tuple, Any
import asyncio
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
logger = logging.getLogger("solr-mcp-server")

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
    
    async def search(self, query: str, filter_query: Optional[str] = None, 
                    sort: Optional[str] = None, rows: int = 10, 
                    start: int = 0) -> Dict[str, Any]:
        """
        Execute a search query against Solr.
        
        Args:
            query (str): The search query (q parameter)
            filter_query (Optional[str]): Filter query (fq parameter)
            sort (Optional[str]): Sort criteria (e.g., "id asc")
            rows (int): Number of results to return
            start (int): Starting offset for results
            
        Returns:
            Dict[str, Any]: The search results from Solr
        """
        params = {
            "q": query,
            "wt": "json",
            "rows": rows,
            "start": start,
        }
        
        if filter_query:
            params["fq"] = filter_query
        
        if sort:
            params["sort"] = sort
        
        auth = None
        if self.username and self.password:
            auth = (self.username, self.password)
            
        url = f"{self.base_url}/{self.collection}/select"
        
        try:
            logger.info(f"Sending Solr search request to {url} with params: {params}")
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, auth=auth)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Solr HTTP error: {e}, Response: {e.response.text}")
            return {"error": f"Solr search error: {str(e)}", "status_code": e.response.status_code}
        except httpx.RequestError as e:
            logger.error(f"Solr request error: {e}")
            return {"error": f"Solr connection error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error in search: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"Unexpected error: {str(e)}"}
            
    async def get_document(self, doc_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Retrieve a specific document by ID.
        
        Args:
            doc_id (str): Document identifier
            fields (Optional[List[str]]): Specific fields to return
            
        Returns:
            Dict[str, Any]: The document data
        """
        params = {
            "q": f"id:{doc_id}",
            "wt": "json",
        }
        
        if fields:
            params["fl"] = ",".join(fields)
            
        auth = None
        if self.username and self.password:
            auth = (self.username, self.password)
            
        url = f"{self.base_url}/{self.collection}/select"
        
        try:
            logger.info(f"Sending Solr document request to {url} with id: {doc_id}")
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, auth=auth)
                response.raise_for_status()
                data = response.json()
                
                if data["response"]["numFound"] == 0:
                    logger.warning(f"Document with ID {doc_id} not found")
                    return {"error": f"Document with ID {doc_id} not found"}
                    
                return data["response"]["docs"][0]
        except httpx.HTTPStatusError as e:
            logger.error(f"Solr HTTP error: {e}, Response: {e.response.text}")
            return {"error": f"Solr document retrieval error: {str(e)}", "status_code": e.response.status_code}
        except httpx.RequestError as e:
            logger.error(f"Solr request error: {e}")
            return {"error": f"Solr connection error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error in get_document: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"Unexpected error: {str(e)}"}


# Models for request/response validation
class SearchParams(BaseModel):
    """Parameters for a search query."""
    query: str = Field(description="The search query")
    filter_query: Optional[str] = Field(None, description="Filter query to narrow results")
    sort: Optional[str] = Field(None, description="Sort criteria (e.g. 'id asc')")
    rows: int = Field(10, description="Number of results to return")
    start: int = Field(0, description="Starting offset for results")


class DocumentParams(BaseModel):
    """Parameters for document retrieval."""
    id: str = Field(description="Document ID to retrieve")
    fields: Optional[List[str]] = Field(None, description="Specific fields to return")


# Create the MCP server (removed lifespan)
app = FastMCP("Solr Search")

# Initialize the Solr client as a global variable
# Reason: In MCP 1.6.0, FastMCP doesn't have a state attribute
solr_client = SolrClient(
    base_url=SOLR_BASE_URL,
    collection=SOLR_COLLECTION,
    username=SOLR_USERNAME,
    password=SOLR_PASSWORD
)

# Test Solr connection at startup (moved from lifespan)
async def test_solr_connection():
    """Test the Solr connection at startup."""
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


@app.resource("solr://search/{query}")
async def search_solr(query: str):
    """
    Resource for searching Solr documents.
    
    Args:
        query (str): The search query
        
    Returns:
        str: JSON string with search results
    """
    try:
        logger.info(f"Processing search resource request with query: {query}")
        # Use global solr_client instead of app.state
        results = await solr_client.search(query)
        return json.dumps(results, indent=2)
    except Exception as e:
        logger.error(f"Error in search_solr resource: {e}")
        logger.error(traceback.format_exc())
        return json.dumps({"error": f"Error processing search: {str(e)}"}, indent=2)


@app.tool()
async def search(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool for advanced document search with multiple parameters.
    
    Args:
        params (Dict[str, Any]): Search parameters including query, filters, etc.
        
    Returns:
        Dict[str, Any]: Search results
    """
    try:
        logger.info(f"Processing search tool request with params: {params}")
        search_params = SearchParams(**params)
        # Use global solr_client instead of app.state
        
        results = await solr_client.search(
            query=search_params.query,
            filter_query=search_params.filter_query,
            sort=search_params.sort,
            rows=search_params.rows,
            start=search_params.start
        )
        
        return results
    except Exception as e:
        logger.error(f"Error in search tool: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Error processing search: {str(e)}"}


@app.tool()
async def get_document(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool for retrieving a specific document by ID.
    
    Args:
        params (Dict[str, Any]): Document parameters including ID and optional fields
        
    Returns:
        Dict[str, Any]: The requested document
    """
    try:
        logger.info(f"Processing get_document tool request with params: {params}")
        doc_params = DocumentParams(**params)
        # Use global solr_client instead of app.state
        
        document = await solr_client.get_document(
            doc_id=doc_params.id,
            fields=doc_params.fields
        )
        
        return document
    except Exception as e:
        logger.error(f"Error in get_document tool: {e}")
        logger.error(traceback.format_exc())
        return {"error": f"Error retrieving document: {str(e)}"}


def check_port_availability(host: str, port: int) -> bool:
    """
    Check if a port is available on the specified host.
    
    Args:
        host (str): The host to check.
        port (int): The port to check.
        
    Returns:
        bool: True if the port is available, False otherwise.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except socket.error:
            return False


def run_server_with_mcp_cli():
    """
    Run the MCP server using the MCP CLI.
    This is the method that should be used when executing the script directly.
    
    The function will detect whether the script is being run directly with Python
    or through the MCP CLI and adapt accordingly.
    """
    # Check if we're running through the MCP CLI
    is_mcp_cli = any('mcp' in arg for arg in sys.argv)
    
    if is_mcp_cli:
        # If we're running through the MCP CLI, we don't need to do anything
        # The MCP CLI will handle the server startup process
        logger.info("Detected execution through MCP CLI - letting MCP handle the server startup")
    else:
        # We're running directly with Python - set up the environment and call app.run()
        print(f"Starting MCP server on http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}...")
        
        # Check if port is available before starting
        port_available = check_port_availability(MCP_SERVER_HOST, MCP_SERVER_PORT)
        if not port_available:
            logger.error(f"Port {MCP_SERVER_PORT} is already in use on host {MCP_SERVER_HOST}!")
            sys.exit(1)
        else:
            logger.info(f"Port {MCP_SERVER_PORT} is available on host {MCP_SERVER_HOST}")
            
        # Set environment variables for the MCP server
        os.environ["MCP_PORT"] = str(MCP_SERVER_PORT)
        os.environ["HOST"] = MCP_SERVER_HOST
        
        # Test Solr connection before starting the server
        asyncio.run(test_solr_connection())
        
        try:
            # Start the MCP server
            logger.info("Starting MCP server directly...")
            app.run()
        except Exception as e:
            logger.error(f"Error starting MCP server: {e}")
            logger.error(traceback.format_exc())
            sys.exit(1)


if __name__ == "__main__":
    # Run the server with the appropriate method based on how the script was invoked
    run_server_with_mcp_cli()