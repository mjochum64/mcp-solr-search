# Changelog

Dieses Dokument dokumentiert alle wichtigen Änderungen am MCP-Server für Apache Solr.

## [1.0.0] - 2025-04-26

### Hinzugefügt
- Initiale Projektstruktur mit MCP Python SDK-Integration
- Implementierung eines MCP-Servers mit Solr-Integration
- Docker Compose-basierte Entwicklungs- und Testumgebung für Apache Solr
- Basis-Search-Resource (`solr://search/{query}`)
- Erweiterte Such-Tools mit Filterung und Sortierung
- Dokumenten-Abruf-Tool
- Umfangreiche Test-Suite (Unit- und Integrationstests)
- Testdatengenerator für Apache Solr
- Schema- und Konfigurationsdateien für Apache Solr
- FastAPI-basierter Server für direkten HTTP-Zugriff auf Solr-Suchfunktionen

### Geändert
- Umstellung von ursprünglichem FastAPI-Konzept auf MCP SDK
- Entfernung des lifespan-Kontextmanagers für MCP 1.6.0 Kompatibilität
- Ersetzen der `app.state` Zustandsverwaltung durch globale Variablen für MCP 1.6.0 Kompatibilität
- Hinzufügung eines FastAPI-basierten Servers als Workaround für direkte HTTP-Zugriffe, da MCP 1.6.0 keinen HTTP-Transport unterstützt

### Behoben
- TaskGroup-Fehler in MCP 1.6.0 durch Entfernung des lifespan-Kontextmanagers
- Kompatibilitätsprobleme mit MCP 1.6.0 API durch Anpassung des Codes an die aktuelle API-Version
- Direkter HTTP-Zugriff auf den Server durch Implementierung eines FastAPI-basierten Alternativservers
- Import-Probleme bei verschiedenen Ausführungsmethoden durch Hinzufügen einer Systempfad-Anpassung in MCP- und HTTP-Server

## [0.1.0] - 2025-04-26

### Hinzugefügt
- Initiale Projektstruktur
- Grundlegende MCP-Server-Implementierung in `src/server.py`
- Solr-Integration mit Unterstützung für grundlegende Suche und Dokumentenabruf
- Docker Compose-Setup für Apache Solr
- Integration-Tests für die Solr-Verbindung
- Beispieldatenloader für Apache Solr

### Geändert
- README.md aktualisiert mit detaillierten Informationen zum Projekt
- PLANNING.md und TASK.md auf den aktuellen Stand gebracht

### Behoben
- N/A

## Format der Änderungseinträge

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Jeder Abschnitt sollte eine der folgenden Kategorien enthalten (falls zutreffend):

- **Hinzugefügt** für neue Features
- **Geändert** für Änderungen an bestehender Funktionalität
- **Veraltet** für Features, die in zukünftigen Versionen entfernt werden
- **Entfernt** für Features, die in dieser Version entfernt wurden
- **Behoben** für Bugfixes
- **Sicherheit** für Sicherheitsverbesserungen