#!/usr/bin/env python3
"""
Convenience-Skript zum Starten des Solr-Servers.

Dieses Skript dient als einfacher Einstiegspunkt für das Projekt
und leitet die Ausführung an src/main.py weiter.
"""
import os
import sys
from pathlib import Path

# Füge das src-Verzeichnis zum Modul-Suchpfad hinzu
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # Importiere und führe die main-Funktion aus
    from src.main import parse_arguments, print_help, start_mcp_server, start_http_server
    
    args = parse_arguments()
    
    if args.mode == "help":
        print_help()
    elif args.mode == "mcp":
        start_mcp_server(args.port)
    elif args.mode == "http":
        start_http_server(args.port)