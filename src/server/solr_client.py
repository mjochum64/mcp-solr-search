#!/usr/bin/env python3
"""
SolrClient für die Kommunikation mit Apache Solr.

Diese Klasse bietet asynchrone Methoden für Suche und Dokumentenabruf von Solr-Servern.
"""
import logging
import traceback
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import inspect

import httpx

# Logger für diese Datei konfigurieren
logger = logging.getLogger("solr-client")

@dataclass
class SolrClient:
    """Client für die Kommunikation mit Apache Solr.
    
    Diese Klasse kapselt alle Operationen, die mit dem Solr-Server durchgeführt werden,
    einschließlich Suche und Dokumentenabruf.
    
    Attributes:
        base_url (str): Basis-URL des Solr-Servers (z.B. "http://localhost:8983/solr")
        collection (str): Name der Solr-Kollektion für Suchabfragen
        username (Optional[str]): Benutzername für die Solr-Authentifizierung
        password (Optional[str]): Passwort für die Solr-Authentifizierung
    """
    
    base_url: str
    collection: str
    username: Optional[str] = None
    password: Optional[str] = None
    
    async def search(self, query: str = "*:*", filter_query: Optional[str] = None, 
                    sort: Optional[str] = None, rows: int = 10, 
                    start: int = 0) -> Dict[str, Any]:
        """
        Führt eine Suchanfrage an Solr aus.
        
        Args:
            query (str): Die Suchanfrage (q-Parameter)
            filter_query (Optional[str]): Optionale Filterabfrage (fq-Parameter)
            sort (Optional[str]): Optionale Sortierparameter (z.B. "id asc")
            rows (int): Anzahl der zurückgegebenen Dokumente (Standard: 10)
            start (int): Offset für Paginierung (Standard: 0)
            
        Returns:
            Dict[str, Any]: Die Suchergebnisse von Solr
        """
        params = {
            "q": query or "*:*",
            "wt": "json",
            "rows": rows,
            "start": start,
        }
        
        # Füge optionale Parameter hinzu, wenn sie vorhanden sind
        if filter_query:
            params["fq"] = filter_query
        
        if sort:
            params["sort"] = sort
            
        auth = None
        if self.username and self.password:
            auth = (self.username, self.password)
            
        url = f"{self.base_url}/{self.collection}/select"
        
        try:
            logger.info(f"Sende Solr-Suchanfrage an {url} mit Query: {query}")
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, auth=auth)
                if inspect.iscoroutinefunction(response.raise_for_status):
                    await response.raise_for_status()
                else:
                    response.raise_for_status()
                if inspect.iscoroutinefunction(response.json):
                    return await response.json()
                else:
                    return response.json()
        except httpx.HTTPStatusError:
            # Fehler nicht abfangen, sondern durchreichen
            raise
        except Exception as e:
            logger.error(f"Fehler bei der Solr-Suche: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"Fehler bei der Suche: {str(e)}"}
    
    async def get_document(self, doc_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Ruft ein spezifisches Dokument anhand seiner ID ab.
        
        Args:
            doc_id (str): Die ID des abzurufenden Dokuments
            fields (Optional[List[str]]): Optionale Liste von Feldern, die zurückgegeben werden sollen
            
        Returns:
            Dict[str, Any]: Das abgerufene Dokument oder eine Fehlermeldung
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
            logger.info(f"Rufe Dokument mit ID {doc_id} von {url} ab")
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, auth=auth)
                if inspect.iscoroutinefunction(response.raise_for_status):
                    await response.raise_for_status()
                else:
                    response.raise_for_status()
                if inspect.iscoroutinefunction(response.json):
                    result = await response.json()
                else:
                    result = response.json()
                if result["response"]["numFound"] == 0:
                    return {"error": f"Dokument mit ID {doc_id} nicht gefunden"}
                return result["response"]["docs"][0]
        except httpx.HTTPStatusError:
            # Fehler nicht abfangen, sondern durchreichen
            raise
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Dokuments: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"Fehler beim Abrufen des Dokuments: {str(e)}"}