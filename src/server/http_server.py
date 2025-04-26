#!/usr/bin/env python3
"""
FastAPI-Server für direkten HTTP-Zugriff auf Apache Solr.

Diese Implementierung nutzt FastAPI anstelle des MCP-Protokolls, um direkten HTTP-Zugriff 
auf die Solr-Suchfunktionen zu ermöglichen. Dies ist ein Workaround für die Einschränkung in 
MCP 1.6.0, dass die FastMCP.run()-Methode keinen HTTP-Transport unterstützt.
"""
import os
import sys
import logging
import traceback
from typing import Dict, List, Optional, Any
from pathlib import Path

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import Field

# Projektpfad zum System-Pfad hinzufügen, um absolute Imports zu ermöglichen
# Dadurch können wir den Server mit verschiedenen Methoden starten
project_dir = str(Path(__file__).parents[2])  # Zwei Ebenen nach oben: src/server -> src -> Projektwurzel
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
    print(f"Added {project_dir} to system path")

# Importiere lokale Module
from src.server.models import SearchParams, GetDocumentParams, ErrorResponse
from src.server.solr_client import SolrClient

# Logger für diese Datei konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("http-server")

# Umgebungsvariablen laden
load_dotenv()

# Server-Konfiguration
SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8765"))
SERVER_HOST = "0.0.0.0"  # Explizit an alle Schnittstellen binden

# Solr-Verbindungskonfiguration
SOLR_BASE_URL = os.getenv("SOLR_BASE_URL", "http://localhost:8983/solr")
SOLR_COLLECTION = os.getenv("SOLR_COLLECTION", "documents")
SOLR_USERNAME = os.getenv("SOLR_USERNAME", "")
SOLR_PASSWORD = os.getenv("SOLR_PASSWORD", "")

# FastAPI-App initialisieren
app = FastAPI(
    title="Solr Search API",
    description="API für die Suche in Apache Solr-Dokumenten",
    version="1.0.0"
)

# Solr-Client initialisieren
solr_client = SolrClient(
    base_url=SOLR_BASE_URL,
    collection=SOLR_COLLECTION,
    username=SOLR_USERNAME,
    password=SOLR_PASSWORD
)


@app.on_event("startup")
async def startup_event():
    """Führt Startup-Aufgaben aus."""
    logger.info("Starte FastAPI Solr Search Server")
    
    # Teste die Solr-Verbindung
    try:
        logger.info("Teste Solr-Verbindung...")
        async with httpx.AsyncClient() as client:
            ping_url = f"{SOLR_BASE_URL}/{SOLR_COLLECTION}/admin/ping"
            response = await client.get(ping_url)
            response.raise_for_status()
            logger.info("Solr-Verbindung erfolgreich")
    except Exception as e:
        logger.warning(f"Solr-Verbindungstest fehlgeschlagen: {e}")
        logger.warning("Server wird gestartet, aber Solr-Suchen könnten fehlschlagen")


# Server-Info-Endpunkt (imitiert den MCP-Server-Info-Endpunkt)
@app.get("/server_info")
async def server_info():
    """Gibt Server-Informationen zurück (imitiert den MCP-Server-Info-Endpunkt)."""
    return {
        "name": "Solr Search API",
        "version": "1.0.0",
        "tools": ["search", "get_document"],
        "resources": ["solr://search/{query}"]
    }


# Tool-Endpunkt für die Suche (imitiert den MCP-Tool-Endpunkt)
@app.post("/tool/search", response_model=Dict[str, Any])
async def tool_search(params: SearchParams):
    """
    Such-Endpunkt, der die MCP-Tool-Schnittstelle imitiert.
    
    Args:
        params (SearchParams): Suchparameter
        
    Returns:
        Dict[str, Any]: Suchergebnisse von Solr
    """
    try:
        logger.info(f"Verarbeite Such-Tool-Anfrage mit Parametern: {params}")
        results = await solr_client.search(
            query=params.query,
            filter_query=params.filter_query,
            sort=params.sort,
            rows=params.rows,
            start=params.start
        )
        return results
    except Exception as e:
        logger.error(f"Fehler im Such-Tool: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Fehler bei der Verarbeitung der Suche: {str(e)}")


# Tool-Endpunkt für den Dokumentenabruf (imitiert den MCP-Tool-Endpunkt)
@app.post("/tool/get_document", response_model=Dict[str, Any])
async def tool_get_document(params: GetDocumentParams):
    """
    Dokumentenabruf-Endpunkt, der die MCP-Tool-Schnittstelle imitiert.
    
    Args:
        params (GetDocumentParams): Dokumentenabrufparameter
        
    Returns:
        Dict[str, Any]: Das abgerufene Dokument oder eine Fehlermeldung
    """
    try:
        logger.info(f"Verarbeite Dokumentenabruf-Anfrage mit Parametern: {params}")
        document = await solr_client.get_document(
            doc_id=params.id,
            fields=params.fields
        )
        
        # Prüfe auf Fehler in der Antwort
        if "error" in document:
            raise HTTPException(status_code=404, detail=document["error"])
            
        return document
    except HTTPException:
        # Bereits formatierte HTTPException weiterleiten
        raise
    except Exception as e:
        logger.error(f"Fehler beim Dokumentenabruf: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen des Dokuments: {str(e)}")


# Resource-Endpunkt für die Suche (imitiert den MCP-Resource-Endpunkt)
@app.get("/resource/solr://search/{query}")
async def resource_search(query: str):
    """
    Resource-Endpunkt, der die MCP-Resource-Schnittstelle imitiert.
    
    Args:
        query (str): Die Suchanfrage
        
    Returns:
        Dict[str, Any]: Suchergebnisse
    """
    try:
        logger.info(f"Verarbeite Such-Resource-Anfrage mit Query: {query}")
        results = await solr_client.search(query=query)
        return results
    except Exception as e:
        logger.error(f"Fehler in der Such-Resource: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Fehler bei der Verarbeitung der Suche: {str(e)}")


# Fallback für URL-kodierte Resource-URLs
@app.get("/resource/{path:path}")
async def resource_fallback(path: str, request: Request):
    """Fallback-Handler für URL-kodierte Resource-Pfade."""
    try:
        # Behandle URL-kodierte Pfade wie "solr%3A%2F%2Fsearch%2F%2A%3A%2A"
        if path.startswith("solr://search/") or path.startswith("solr%3A%2F%2Fsearch%2F"):
            # Extrahiere den Query-Teil
            query = path.split("/")[-1]
            logger.info(f"Fallback-Resource-Handler verarbeitet Query: {query}")
            results = await solr_client.search(query=query)
            return results
        else:
            return {"error": f"Nicht unterstützter Resource-Pfad: {path}"}
    except Exception as e:
        logger.error(f"Fehler im Resource-Fallback: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Fehler bei der Verarbeitung der Resource: {str(e)}")


if __name__ == "__main__":
    # Startup-Informationen ausgeben
    print("=" * 40)
    print(f"FastAPI Solr Search Server")
    print(f"- Host: {SERVER_HOST}")
    print(f"- Port: {SERVER_PORT}")
    print("=" * 40)
    print(f"Server startet auf http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"Sie können testen mit: curl -X POST http://localhost:{SERVER_PORT}/tool/search -H \"Content-Type: application/json\" -d '{{\"query\": \"*:*\"}}'")
    print(f"OpenAPI-Dokumentation verfügbar unter: http://localhost:{SERVER_PORT}/docs")
    
    # FastAPI-App mit uvicorn starten
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)