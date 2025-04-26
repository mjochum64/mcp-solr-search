#!/usr/bin/env python3
"""
Pydantic-Modelle für die Solr-MCP-Server-Kommunikation.

Diese Modelle definieren die Struktur von Anfragen und Antworten für die MCP-Endpoints.
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class SearchParams(BaseModel):
    """Parameter für eine Suchanfrage.
    
    Diese Klasse definiert die erwartete Struktur der Parameter für das Suchtool.
    
    Attributes:
        query (str): Die Suchabfrage
        filter_query (Optional[str]): Optionaler Filterausdruck für die Suche
        sort (Optional[str]): Optionale Sortierparameter (z.B. "id asc")
        rows (int): Anzahl der zurückzugebenden Dokumente (Standard: 10)
        start (int): Offset für Paginierung (Standard: 0)
    """
    query: str = Field(description="Die Suchabfrage")
    filter_query: Optional[str] = Field(None, description="Optionaler Filterausdruck für die Suche")
    sort: Optional[str] = Field(None, description="Optionaler Sortierparameter (z.B. 'id asc')")
    rows: int = Field(10, description="Anzahl der zurückzugebenden Dokumente")
    start: int = Field(0, description="Offset für Paginierung")


class GetDocumentParams(BaseModel):
    """Parameter für den Dokumentenabruf.
    
    Diese Klasse definiert die erwartete Struktur der Parameter für das Dokumentenabruf-Tool.
    
    Attributes:
        id (str): Die ID des abzurufenden Dokuments
        fields (Optional[List[str]]): Optionale Liste von Feldern, die zurückgegeben werden sollen
    """
    id: str = Field(description="Die ID des abzurufenden Dokuments")
    fields: Optional[List[str]] = Field(None, description="Optionale Liste von Feldern, die zurückgegeben werden sollen")


class ErrorResponse(BaseModel):
    """Modell für eine Fehlerantwort.
    
    Attributes:
        error (str): Die Fehlermeldung
        detail (Optional[str]): Optionale detaillierte Beschreibung des Fehlers
    """
    error: str = Field(description="Die Fehlermeldung")
    detail: Optional[str] = Field(None, description="Optionale detaillierte Beschreibung des Fehlers")