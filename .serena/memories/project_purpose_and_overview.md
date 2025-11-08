# Project Purpose and Overview

## What is this project?
This is an **MCP (Model Context Protocol) Server for Apache Solr Document Search**. It provides a bridge between Large Language Models (LLMs) and Apache Solr search capabilities through the standardized MCP protocol.

## Key Features
- MCP Resources for searching Solr documents (`solr://search/{query}`)
- MCP Tools for advanced search and document retrieval
- Asynchronous communication with Solr using httpx
- Type-safe interfaces with Pydantic models
- Authentication support (JWT)
- Docker-based Solr development environment
- FastAPI HTTP server as fallback for MCP 1.6.0 limitations

## Current Status
- **Version**: 1.0.0
- **MCP Version**: Currently on MCP 1.6.0, planned migration to MCP 2025-03-26
- **Status**: Production-ready with known MCP 1.6.0 compatibility workarounds

## Architecture
The project implements both:
1. **MCP Server** - For integration with LLM applications and Claude Desktop
2. **HTTP Server** - FastAPI-based workaround for direct HTTP access (due to MCP 1.6.0 limitations)

## Target Users
- Developers integrating Solr search into LLM applications
- Users wanting to provide Claude Desktop access to Solr document collections
- Teams building AI-powered search and document retrieval systems