"""
Tests for the Solr MCP Server functionality.
"""
import json
import os
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
from mcp.server.fastmcp import FastMCP

# Add the src directory to the path so we can import from it
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# Import the server module
import server


@pytest.fixture
def mock_solr_client():
    """Create a mock Solr client for testing"""
    client = AsyncMock()
    
    # Mock search method
    search_result = {
        "responseHeader": {"status": 0},
        "response": {
            "numFound": 1,
            "start": 0,
            "docs": [{"id": "doc1", "title": "Test Document"}]
        }
    }
    client.search.return_value = search_result
    
    # Mock get_document method
    doc_result = {"id": "doc1", "title": "Test Document"}
    client.get_document.return_value = doc_result
    
    return client


@pytest.fixture
def mock_context(mock_solr_client):
    """Create a mock context with the solr client"""
    context = MagicMock()
    context.request_context.lifespan_context = {"solr_client": mock_solr_client}
    return context


@pytest.mark.asyncio
async def test_search_solr_resource(mock_context):
    """Test the solr://search/{query} resource"""
    # Call the resource function
    result = await server.search_solr(mock_context, "test query")
    
    # Verify solr client was called with the right parameters
    mock_context.request_context.lifespan_context["solr_client"].search.assert_called_once_with("test query")
    
    # Verify the result is properly formatted
    parsed_result = json.loads(result)
    assert parsed_result["response"]["numFound"] == 1
    assert parsed_result["response"]["docs"][0]["id"] == "doc1"


@pytest.mark.asyncio
async def test_search_tool(mock_context):
    """Test the search tool with parameters"""
    # Prepare parameters
    params = {
        "query": "test query",
        "filter_query": "field:value",
        "sort": "score desc",
        "rows": 5,
        "start": 10
    }
    
    # Call the tool function
    result = await server.search(mock_context, params)
    
    # Verify solr client was called with the right parameters
    mock_context.request_context.lifespan_context["solr_client"].search.assert_called_once_with(
        query="test query",
        filter_query="field:value",
        sort="score desc",
        rows=5,
        start=10
    )
    
    # Check the result
    assert result["response"]["docs"][0]["id"] == "doc1"


@pytest.mark.asyncio
async def test_get_document_tool(mock_context):
    """Test the get_document tool"""
    # Prepare parameters
    params = {
        "id": "doc1",
        "fields": ["id", "title"]
    }
    
    # Call the tool function
    result = await server.get_document(mock_context, params)
    
    # Verify solr client was called with the right parameters
    mock_context.request_context.lifespan_context["solr_client"].get_document.assert_called_once_with(
        doc_id="doc1",
        fields=["id", "title"]
    )
    
    # Check the result
    assert result["id"] == "doc1"
    assert result["title"] == "Test Document"


@pytest.mark.asyncio
async def test_solr_client_search():
    """Test the SolrClient search method with a mocked httpx response"""
    # Create a mock response
    mock_response = AsyncMock()
    mock_response.raise_for_status = AsyncMock()
    mock_response.json.return_value = {
        "responseHeader": {"status": 0},
        "response": {
            "numFound": 2,
            "start": 0,
            "docs": [
                {"id": "doc1", "title": "First Document"},
                {"id": "doc2", "title": "Second Document"}
            ]
        }
    }
    
    # Create a mock httpx client
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.get.return_value = mock_response
    
    # Patch the httpx.AsyncClient to return our mock
    with patch("httpx.AsyncClient", return_value=mock_client):
        # Create a SolrClient instance
        client = server.SolrClient(
            base_url="http://example.com/solr",
            collection="test_collection"
        )
        
        # Call the search method
        result = await client.search(
            query="test",
            filter_query="field:value",
            sort="score desc",
            rows=10,
            start=0
        )
        
        # Verify the result
        assert result["response"]["numFound"] == 2
        assert len(result["response"]["docs"]) == 2
        assert result["response"]["docs"][0]["id"] == "doc1"
        assert result["response"]["docs"][1]["id"] == "doc2"


@pytest.mark.asyncio
async def test_solr_client_get_document():
    """Test the SolrClient get_document method with a mocked httpx response"""
    # Create a mock response for a successful document retrieval
    mock_response = AsyncMock()
    mock_response.raise_for_status = AsyncMock()
    mock_response.json.return_value = {
        "responseHeader": {"status": 0},
        "response": {
            "numFound": 1,
            "start": 0,
            "docs": [
                {"id": "doc1", "title": "Test Document", "content": "This is a test"}
            ]
        }
    }
    
    # Create a mock httpx client
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.get.return_value = mock_response
    
    # Patch the httpx.AsyncClient to return our mock
    with patch("httpx.AsyncClient", return_value=mock_client):
        # Create a SolrClient instance
        client = server.SolrClient(
            base_url="http://example.com/solr",
            collection="test_collection"
        )
        
        # Call the get_document method
        result = await client.get_document(doc_id="doc1", fields=["id", "title"])
        
        # Verify the result
        assert result["id"] == "doc1"
        assert result["title"] == "Test Document"
        assert "content" in result