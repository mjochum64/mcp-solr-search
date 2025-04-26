#!/usr/bin/env python3
"""
Hauptstartpunkt für die Solr-Server (MCP und HTTP).

Diese Datei bietet eine einfache Benutzeroberfläche zum Auswählen und Starten
der verschiedenen Server-Implementierungen.
"""
import os
import sys
import argparse


def parse_arguments():
    """Parst die Kommandozeilenargumente."""
    parser = argparse.ArgumentParser(
        description="Solr-Server (MCP und HTTP)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--mode",
        choices=["mcp", "http", "help"],
        default="help",
        help="Server-Modus (mcp: MCP-Protokoll, http: HTTP-API)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_SERVER_PORT", "8765")),
        help="Port, auf dem der Server laufen soll"
    )
    
    return parser.parse_args()


def print_help():
    """Gibt Hilfsinformationen zu den Server-Modi aus."""
    print("\n=== Solr-Server Starter ===\n")
    print("Verwendung:")
    print("  python src/main.py --mode [mcp|http] [--port PORT]\n")
    print("Modi:")
    print("  mcp   - MCP-Protokoll-Server für LLM-Integration")
    print("          Nutzbar mit MCP-Client oder mcp dev-Tool")
    print("  http  - HTTP-API-Server für direkten HTTP-Zugriff")
    print("          Bietet REST API und OpenAPI-Dokumentation\n")
    print("Beispiele:")
    print("  MCP-Server starten:")
    print("    python src/main.py --mode mcp")
    print("  HTTP-Server starten:")
    print("    python src/main.py --mode http")
    print("  Server auf spezifischem Port starten:")
    print("    python src/main.py --mode http --port 9000\n")


def start_mcp_server(port):
    """Startet den MCP-Protokoll-Server."""
    print(f"\nStarte MCP-Protokoll-Server auf Port {port}...")
    os.environ["MCP_PORT"] = str(port)
    
    try:
        from src.server.mcp_server import app
        print("\nMCP-Server wird gestartet...")
        print("Für die MCP-Inspector-GUI starten Sie: mcp dev src/server/mcp_server.py")
        app.run()
    except Exception as e:
        print(f"Fehler beim Starten des MCP-Servers: {e}")
        sys.exit(1)


def start_http_server(port):
    """Startet den HTTP-API-Server."""
    print(f"\nStarte HTTP-API-Server auf Port {port}...")
    os.environ["MCP_SERVER_PORT"] = str(port)
    
    try:
        # Wir importieren hier, um Uvicorn in der Funktion zu starten
        import uvicorn
        from src.server.http_server import app
        
        print(f"\nHTTP-Server startet auf http://localhost:{port}")
        print(f"OpenAPI-Dokumentation: http://localhost:{port}/docs")
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        print(f"Fehler beim Starten des HTTP-Servers: {e}")
        sys.exit(1)


if __name__ == "__main__":
    args = parse_arguments()
    
    if args.mode == "help":
        print_help()
    elif args.mode == "mcp":
        start_mcp_server(args.port)
    elif args.mode == "http":
        start_http_server(args.port)