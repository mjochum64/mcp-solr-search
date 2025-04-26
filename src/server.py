#!/usr/bin/env python3
"""
MCP-Server for Apache Solr document search.

This server exposes Apache Solr search functionality as MCP resources and tools,
allowing LLMs to search and retrieve documents from Solr collections.
"""
import os
import json
from typing import Dict, List, Optional, Tuple, Any
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

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
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, auth=auth)
            response.raise_for_status()
            return response.json()
            
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
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, auth=auth)
            response.raise_for_status()
            data = response.json()
            
            if data["response"]["numFound"] == 0:
                return {"error": f"Document with ID {doc_id} not found"}
                
            return data["response"]["docs"][0]


# Models for request/response validation
class SearchParams(BaseModel):
    """Parameters for a search query."""
    query: str
    filter_query: Optional[str] = None
    sort: Optional[str] = None
    rows: int = 10
    start: int = 0


class DocumentParams(BaseModel):
    """Parameters for document retrieval."""
    id: str
    fields: Optional[List[str]] = None


@asynccontextmanager
async def lifespan():
    """
    Lifespan context manager for the MCP server.
    
    Initializes resources when the server starts and cleans up when it stops.
    """
    # Initialize the Solr client
    solr_client = SolrClient(
        base_url=SOLR_BASE_URL,
        collection=SOLR_COLLECTION,
        username=SOLR_USERNAME,
        password=SOLR_PASSWORD
    )
    
    # Yield the initialized resources
    yield {"solr_client": solr_client}
    
    # Cleanup when server stops
    print("Server shutting down, performing cleanup...")


# Create the MCP server
mcp = FastMCP("Solr Search", lifespan=lifespan)


@mcp.resource("solr://search/{query}")
async def search_solr(ctx, query: str):
    """
    Resource for searching Solr documents.
    
    Args:
        ctx: The request context
        query (str): The search query
        
    Returns:
        str: JSON string with search results
    """
    solr_client = ctx.request_context.lifespan_context["solr_client"]
    results = await solr_client.search(query)
    return json.dumps(results, indent=2)


@mcp.tool()
async def search(ctx, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool for advanced document search with multiple parameters.
    
    Args:
        ctx: The request context
        params (Dict[str, Any]): Search parameters including query, filters, etc.
        
    Returns:
        Dict[str, Any]: Search results
    """
    search_params = SearchParams(**params)
    solr_client = ctx.request_context.lifespan_context["solr_client"]
    
    results = await solr_client.search(
        query=search_params.query,
        filter_query=search_params.filter_query,
        sort=search_params.sort,
        rows=search_params.rows,
        start=search_params.start
    )
    
    return results


@mcp.tool()
async def get_document(ctx, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool for retrieving a specific document by ID.
    
    Args:
        ctx: The request context
        params (Dict[str, Any]): Document parameters including ID and optional fields
        
    Returns:
        Dict[str, Any]: The requested document
    """
    doc_params = DocumentParams(**params)
    solr_client = ctx.request_context.lifespan_context["solr_client"]
    
    document = await solr_client.get_document(
        doc_id=doc_params.id,
        fields=doc_params.fields
    )
    
    return document


if __name__ == "__main__":
    mcp.run()