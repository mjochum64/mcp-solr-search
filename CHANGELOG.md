# Changelog

Dieses Dokument dokumentiert alle wichtigen Änderungen am MCP-Server für Apache Solr.

## [1.3.1] - 2025-11-08

### Geändert
- **MCP Specification Update**: Dokumentation aktualisiert auf MCP Spec 2025-06-18 (neueste Version)
- CLAUDE.md, README.md, TASK.md auf 2025-06-18 Spec aktualisiert
- "Next Steps" erweitert um OAuth 2.1 und Resource Indicators (nun mandatory für Production)

### Technische Details
- MCP SDK 1.21.0 unterstützt bereits vollständig 2025-06-18 Spec ✅
- Keine Code-Änderungen notwendig - nur Dokumentations-Update
- Backward-kompatibel mit 2025-03-26 und 2024-11-05

## [1.3.0] - 2025-11-08

### Hinzugefügt
- **Highlighting Support**: Neuer `highlight_fields` Parameter für das `search` Tool
- Highlighting zeigt mit `<em>` Tags, wo Suchbegriffe in Ergebnissen vorkommen
- Highlighting-Unterstützung in SolrClient.search() Methode
- Zwei neue Unit Tests für Highlighting-Funktionalität
- Zwei neue Integration Tests mit echtem Solr für Highlighting
- Dokumentation und Beispiele für Highlighting in README.md

### Geändert
- `search` Tool erweitert um optionalen `highlight_fields` Parameter
- Tool-Beschreibung aktualisiert: "Advanced search with filtering, sorting, pagination, faceting, and highlighting"
- README Features-Liste um "Highlighting" erweitert
- MCP Inspector Anleitung um Highlighting-Beispiele erweitert

### Technische Details
- Response enthält jetzt `highlighting` Section wenn `highlight_fields` angegeben
- Automatisches Setzen von `hl=true`, `hl.fl`, `hl.snippets=3` und `hl.fragsize=150` in Solr Query
- Alle 11 Unit Tests passing (9 bestehende + 2 neue) ✅
- Alle 7 Integration Tests passing (5 bestehende + 2 neue) ✅

## [1.2.0] - 2025-11-08

### Hinzugefügt
- **Faceted Search Support**: Neuer `facet_fields` Parameter für das `search` Tool
- Automatische Aggregation von Feldwerten mit Counts
- Facet-Unterstützung in SolrClient.search() Methode
- Zwei neue Unit Tests für Faceted Search Funktionalität
- Dokumentation und Beispiele für Faceted Search in README.md

### Geändert
- `search` Tool erweitert um optionalen `facet_fields` Parameter
- Tool-Beschreibung aktualisiert: "Advanced search with filtering, sorting, pagination, and faceting"
- README Features-Liste um "Faceted Search" erweitert
- MCP Inspector Anleitung um Faceted Search Beispiele erweitert

### Technische Details
- Response enthält jetzt `facet_counts.facet_fields` wenn `facet_fields` angegeben
- Automatisches Setzen von `facet=true` und `facet.mincount=1` in Solr Query
- Alle 7 Unit Tests passing ✅

## [1.1.0] - 2025-11-08

### Hinzugefügt
- **MCP 1.21.0 Modernisierung**: Vollständige Unterstützung der 2025-03-26 Spezifikation
- Lifespan Context Manager mit typsicherer `AppContext` Dataclass
- Tool Annotations (readOnlyHint, title, description)
- Context-basierte Logging-Methoden (ctx.info/debug/warning/error)
- Modern FastMCP Decorator Pattern (@app.tool, @app.resource)
- Native Streamable HTTP Transport Support

### Geändert
- Upgrade von MCP 1.12.3 auf MCP 1.21.0
- Ersetzen globaler Variablen durch Lifespan Context Pattern
- Funktion-Signaturen modernisiert (Parameter first, ctx last)
- Enhanced Logging mit direkter Client-Kommunikation
- Alle Unit Tests für neue Patterns aktualisiert

### Entfernt
- MCP 1.6.0 Kompatibilitäts-Workarounds
- FastAPI HTTP Server Workaround (ersetzt durch native Streamable HTTP)
- Globale Variablen für State Management

### Behoben
- TaskGroup-Fehler durch modernen Lifespan Context Manager
- Claude Desktop Integration mit absoluten Pfaden
- Dokumentationsinkonsistenzen in README.md

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