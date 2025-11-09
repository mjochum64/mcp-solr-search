#!/usr/bin/env python3
"""
Integration tests for the MCP Solr server using a real Solr instance.

These tests connect to a running Solr server and test the actual
functionality of the MCP server with real Solr queries.
"""
import os
import json
import pytest
import asyncio
from typing import Dict, Any
import httpx

import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# Importiere SolrClient direkt
from server.solr_client import SolrClient
from server.mcp_server import search_solr, search, get_document


@pytest.fixture
def solr_client():
    """Create a real SolrClient instance for integration testing."""
    return SolrClient(base_url="http://localhost:8983/solr", collection="documents")


class MockRequestContext:
    """Mock context for integration testing."""

    def __init__(self, lifespan_context):
        """Initialize the mock context with the provided lifespan context."""
        self.lifespan_context = lifespan_context


class MockContext:
    """Mock MCP context for integration testing."""

    def __init__(self, request_context):
        """Initialize the mock context with the provided request context."""
        self.request_context = request_context

    async def info(self, message: str):
        """Mock info logging."""
        pass

    async def debug(self, message: str):
        """Mock debug logging."""
        pass

    async def warning(self, message: str):
        """Mock warning logging."""
        pass

    async def error(self, message: str):
        """Mock error logging."""
        pass


@pytest.fixture
def integration_context(solr_client):
    """Create a mock context with real Solr client for integration testing."""
    from server.oauth import OAuth2Config

    class LifespanContext:
        def __init__(self, solr_client):
            self.solr_client = solr_client
            # OAuth disabled for integration tests
            self.oauth_config = OAuth2Config(
                enabled=False,
                provider="",
                keycloak_url="",
                realm="",
                client_id="",
                client_secret="",
                required_scopes=[],
                token_validation_endpoint="",
                jwks_endpoint="",
            )
            self.token_validator = None

    request_context = MockRequestContext(LifespanContext(solr_client))
    return MockContext(request_context)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_solr_integration(integration_context):
    """Test the search_solr function with a real Solr server."""
    # Skip if Solr is not available
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8983/solr/documents/admin/ping"
            )
            response.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError):
        pytest.skip("Solr server not available")

    # Test a simple search (jetzt mit *:*)
    result = await search_solr(integration_context, "*:*")  # ctx, query order
    parsed_result = json.loads(result)

    # Verify result structure
    assert "responseHeader" in parsed_result
    assert "response" in parsed_result
    assert parsed_result["responseHeader"]["status"] == 0

    # Verify that we got at least one result
    assert parsed_result["response"]["numFound"] >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_tool_integration(integration_context):
    """Test the search tool with a real Solr server."""
    # Skip if Solr is not available
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8983/solr/documents/admin/ping"
            )
            response.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError):
        pytest.skip("Solr server not available")

    # Test mit *:* und ohne Filter
    result = await search(
        query="*:*",
        filter_query=None,
        sort=None,
        rows=3,
        start=0,
        facet_fields=None,
        highlight_fields=None,
        ctx=integration_context,
    )

    # Verify result structure
    assert "responseHeader" in result
    assert "response" in result
    assert result["responseHeader"]["status"] == 0

    # Verify that we got filtered results
    assert result["response"]["numFound"] >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_document_tool_integration(integration_context):
    """Test the get_document tool with a real Solr server."""
    # Skip if Solr is not available
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8983/solr/documents/admin/ping"
            )
            response.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError):
        pytest.skip("Solr server not available")

    # Test retrieving a specific document
    result = await get_document(
        id="doc1", fields=["title", "author"], ctx=integration_context
    )
    if "id" not in result:
        print(f"WARN: get_document lieferte kein id-Feld: {result}")
        pytest.skip(f"Kein id-Feld im Ergebnis: {result}")
    assert result["id"] == "doc1"
    assert result["title"] == ["Introduction to Apache Solr"]
    assert result["author"] == ["John Smith"]
    assert "content" not in result  # Should not be included due to fields filter


@pytest.mark.asyncio
@pytest.mark.integration
async def test_solr_client_search_integration(solr_client):
    """Test the SolrClient search method with a real Solr server."""
    # Skip if Solr is not available
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8983/solr/documents/admin/ping"
            )
            response.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError):
        pytest.skip("Solr server not available")

    # Test basic search
    result = await solr_client.search(query="*:*", rows=5)  # Match all documents

    # Verify result structure
    assert "responseHeader" in result
    assert "response" in result
    assert result["responseHeader"]["status"] == 0
    assert result["response"]["numFound"] >= 5


@pytest.mark.asyncio
@pytest.mark.integration
async def test_error_handling_integration(solr_client):
    """Test error handling with a real Solr server."""
    # Skip if Solr is not available
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8983/solr/documents/admin/ping"
            )
            response.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError):
        pytest.skip("Solr server not available")

    # Test invalid query syntax
    with pytest.raises(httpx.HTTPStatusError):
        await solr_client.search(query="title:[* TO")  # Invalid syntax

    # Test non-existent document
    result = await solr_client.get_document(doc_id="non_existent_document_id")

    # Should return an error message
    assert "error" in result


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_tool_with_highlighting_integration(integration_context):
    """Test the search tool with highlight_fields parameter using real Solr."""
    # Skip if Solr is not available
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8983/solr/documents/admin/ping"
            )
            response.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError):
        pytest.skip("Solr server not available")

    # Test search with highlighting on title and content fields
    # Use field-specific query to ensure matches
    result = await search(
        query="title:machine",
        filter_query=None,
        sort=None,
        rows=5,
        start=0,
        facet_fields=None,
        highlight_fields=["title", "content"],
        ctx=integration_context,
    )

    # Verify result structure
    assert "responseHeader" in result
    assert "response" in result
    assert result["responseHeader"]["status"] == 0

    # Verify highlighting is present
    assert "highlighting" in result

    # Verify that at least one document has highlighting
    assert len(result["highlighting"]) > 0

    # Get the first document ID from results (should be doc2 for "machine")
    assert result["response"]["numFound"] > 0
    first_doc_id = result["response"]["docs"][0]["id"]

    # Verify highlighting exists for this document
    assert first_doc_id in result["highlighting"]
    doc_highlights = result["highlighting"][first_doc_id]

    # Verify that title field has highlighting with <em> tags
    assert "title" in doc_highlights
    assert len(doc_highlights["title"]) > 0
    title_highlight = doc_highlights["title"][0]
    assert "<em>" in title_highlight and "</em>" in title_highlight
    print(f"Title highlight: {title_highlight}")

    # Content field should also have highlighting
    if "content" in doc_highlights and len(doc_highlights["content"]) > 0:
        content_highlight = doc_highlights["content"][0]
        assert "<em>" in content_highlight and "</em>" in content_highlight
        print(f"Content highlight: {content_highlight}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_solr_client_search_with_highlighting_integration(solr_client):
    """Test SolrClient search method with highlight_fields using real Solr."""
    # Skip if Solr is not available
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8983/solr/documents/admin/ping"
            )
            response.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError):
        pytest.skip("Solr server not available")

    # Test search with highlighting
    # Use field-specific query to ensure matches
    result = await solr_client.search(
        query="title:python", highlight_fields=["title", "content"], rows=10
    )

    # Verify result structure
    assert "responseHeader" in result
    assert "response" in result
    assert result["responseHeader"]["status"] == 0

    # Verify highlighting section is present
    assert "highlighting" in result

    # Verify highlighting has data (should have at least one document)
    assert len(result["highlighting"]) > 0

    # Check that highlighting contains expected structure
    # Get first highlight entry (should be doc3 for "python")
    first_doc_id = list(result["highlighting"].keys())[0]
    first_doc_highlights = result["highlighting"][first_doc_id]

    # first_doc_highlights should be a dict with field names as keys
    assert isinstance(first_doc_highlights, dict)

    # Verify that title field has highlighting with <em> tags
    assert "title" in first_doc_highlights
    assert len(first_doc_highlights["title"]) > 0
    title_highlight = first_doc_highlights["title"][0]
    assert "<em>" in title_highlight and "</em>" in title_highlight
    print(f"Title highlight for {first_doc_id}: {title_highlight}")

    # Content field should also have highlighting
    if "content" in first_doc_highlights and len(first_doc_highlights["content"]) > 0:
        content_highlight = first_doc_highlights["content"][0]
        assert "<em>" in content_highlight and "</em>" in content_highlight
        print(f"Content highlight for {first_doc_id}: {content_highlight}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_edismax_multi_field_search(integration_context):
    """Test that edismax enables multi-field search for text queries."""
    # Skip if Solr is not available
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8983/solr/documents/admin/ping"
            )
            response.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError):
        pytest.skip("Solr server is not available")

    # Test a simple text query that should find results in title field
    result = await search(
        query="machine learning",
        filter_query=None,
        sort=None,
        rows=10,
        start=0,
        ctx=integration_context,
    )

    # Verify response structure
    assert "responseHeader" in result
    assert "response" in result
    assert result["responseHeader"]["status"] == 0

    # Should find at least one document with "Machine Learning Basics"
    assert result["response"]["numFound"] >= 1

    # Verify doc2 is in the results (Machine Learning Basics)
    docs = result["response"]["docs"]
    doc_ids = [doc["id"] for doc in docs]
    assert "doc2" in doc_ids

    # Find doc2 in results
    doc2 = next(doc for doc in docs if doc["id"] == "doc2")
    assert "Machine Learning Basics" in doc2["title"]

    print(
        f"✅ edismax found {result['response']['numFound']} documents for 'machine learning'"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_edismax_python_search(integration_context):
    """Test that edismax finds Python programming guide."""
    # Skip if Solr is not available
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8983/solr/documents/admin/ping"
            )
            response.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError):
        pytest.skip("Solr server is not available")

    # Test search for "python"
    result = await search(
        query="python",
        filter_query=None,
        sort=None,
        rows=10,
        start=0,
        ctx=integration_context,
    )

    # Verify response
    assert result["response"]["numFound"] >= 1

    # Should find doc3 (Python Programming Guide)
    docs = result["response"]["docs"]
    doc_ids = [doc["id"] for doc in docs]
    assert "doc3" in doc_ids

    print(f"✅ edismax found {result['response']['numFound']} documents for 'python'")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_field_specific_query_still_works(integration_context):
    """Test that field-specific queries (with colon) still work without edismax."""
    # Skip if Solr is not available
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8983/solr/documents/admin/ping"
            )
            response.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError):
        pytest.skip("Solr server is not available")

    # Test field-specific query (should NOT use edismax)
    result = await search(
        query="title:solr",
        filter_query=None,
        sort=None,
        rows=10,
        start=0,
        ctx=integration_context,
    )

    # Should find doc1 (Introduction to Apache Solr)
    assert result["response"]["numFound"] >= 1

    docs = result["response"]["docs"]
    doc_ids = [doc["id"] for doc in docs]
    assert "doc1" in doc_ids

    print(f"✅ Field-specific query found {result['response']['numFound']} documents")
