# OAuth Auto-Refresh Testing Guide

## 🎯 Was ist neu?

Der MCP Server kann jetzt **automatisch** OAuth-Tokens von Keycloak holen und refreshen!

**Vorher:**
```
❌ Du musst: ./get-oauth-token.sh
❌ Token kopieren
❌ "Suche mit access_token: eyJh..."
```

**Jetzt:**
```
✅ Einfach: "Suche nach python"
✅ Server holt Token automatisch
✅ Kein manuelles Token-Handling!
```

---

## ✅ Voraussetzungen

1. **Keycloak läuft:**
   ```bash
   docker-compose ps | grep keycloak
   # Should show: mcp_keycloak   Up
   ```

2. **OAuth aktiviert in `.env`:**
   ```bash
   grep -E "ENABLE_OAUTH|OAUTH_AUTO_REFRESH" .env
   ```

   **Sollte zeigen:**
   ```
   ENABLE_OAUTH=true
   OAUTH_AUTO_REFRESH=true
   OAUTH_USERNAME=testuser
   OAUTH_PASSWORD=testpassword
   ```

3. **Claude Desktop neu gestartet:**
   ```bash
   pkill -f "Claude"
   claude-desktop
   ```

---

## 🚀 Test 1: Automatischer Token (NEU!)

### In Claude Desktop eingeben:

```
Suche nach "machine learning" in Solr
```

**Erwartetes Ergebnis:**
```
✅ Gefunden: 1 Dokument
- ID: doc2
- Title: Machine Learning Basics
```

**Was im Hintergrund passiert:**
1. MCP Server startet
2. Server holt OAuth Token von Keycloak (mit testuser/testpassword)
3. Server refresht Token automatisch alle 4 Minuten
4. Suche verwendet den Server-Token
5. **Du musst NICHTS tun!** 🎉

---

## 🧪 Test 2: Weitere Suchen (alle funktionieren automatisch)

```
Suche nach "python" in Solr
```

```
Suche nach "solr" in Solr
```

```
Hole das Dokument mit ID "doc1" aus Solr
```

**Alle sollten funktionieren ohne access_token Parameter!**

---

## 🔍 Test 3: Logs prüfen (optional)

**Claude Desktop Logs:**
```bash
tail -50 ~/.config/Claude/logs/mcp-server-solr-search.log
```

**Erwartete Log-Einträge:**
```
INFO - OAuth 2.1 enabled with provider: keycloak (realm: solr-mcp)
INFO - OAuth auto-refresh enabled for user: testuser
INFO - Retrieving initial OAuth token for server-side authentication...
INFO - ✅ Initial OAuth token retrieved successfully (expires in 300 seconds)
INFO - Token refresh background task started
INFO - Token refresh task started (interval: 240 seconds)
```

**Nach 4 Minuten solltest du sehen:**
```
INFO - Refreshing OAuth token...
INFO - ✅ OAuth token refreshed successfully (expires in 300 seconds)
```

---

## 🛠️ Test 4: Token-Refresh testen

1. **Starte Claude Desktop**
2. **Mache eine Suche:**
   ```
   Suche nach "machine learning"
   ```
   → ✅ Funktioniert

3. **Warte 5 Minuten** (oder nutze die Zeit für Kaffee ☕)

4. **Mache noch eine Suche:**
   ```
   Suche nach "python"
   ```
   → ✅ Sollte immer noch funktionieren!

   **Warum?** Der Background-Task hat den Token nach 4 Minuten refresht.

---

## 🔄 Test 5: Manueller Token überschreibt Auto-Token

Du kannst **immer noch** manuelle Tokens übergeben:

```bash
# Hole manuellen Token
./get-oauth-token.sh
```

Dann in Claude Desktop:
```
Suche mit access_token: eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldU...
```

**Ergebnis:** Verwendet den manuellen Token (nicht den Server-Token)

---

## ❌ Test 6: OAuth deaktivieren

**In `.env` ändern:**
```bash
OAUTH_AUTO_REFRESH=false
```

**Claude Desktop neu starten**

**Dann in Claude Desktop:**
```
Suche nach "python" in Solr
```

**Erwartetes Ergebnis:**
```
❌ Fehler: OAuth is enabled but no access token provided.
Either provide access_token parameter or enable OAUTH_AUTO_REFRESH in .env
```

**Wieder aktivieren:**
```bash
# In .env ändern
OAUTH_AUTO_REFRESH=true

# Claude Desktop neu starten
pkill -f "Claude"
claude-desktop
```

---

## 📊 Vergleich: Vorher vs. Nachher

### Vorher (Manuell)

**Schritt 1:**
```bash
./get-oauth-token.sh
```

**Schritt 2:** Token kopieren

**Schritt 3:**
```
Suche mit access_token: eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldU...
```

**Schritt 4:** Nach 5 Minuten: Token abgelaufen, zurück zu Schritt 1

---

### Nachher (Automatisch)

**Schritt 1:**
```
Suche nach "python"
```

**Done! 🎉**

- ✅ Token wird automatisch geholt
- ✅ Token wird automatisch refresht
- ✅ Läuft unbegrenzt

---

## 🔧 Troubleshooting

### Problem: "Keycloak not accessible"

**Lösung:**
```bash
# Prüfe ob Keycloak läuft
curl http://localhost:8080/health/ready

# Falls nicht
docker-compose restart keycloak
```

### Problem: "Failed to retrieve OAuth token"

**Lösung:**
```bash
# Prüfe Credentials in .env
grep -E "OAUTH_USERNAME|OAUTH_PASSWORD" .env

# Sollte sein:
OAUTH_USERNAME=testuser
OAUTH_PASSWORD=testpassword

# Falls falsch, korrigiere und starte Claude Desktop neu
```

### Problem: "Token keeps expiring"

**Ursache:** Background-Task läuft nicht

**Lösung:**
```bash
# Prüfe Claude Desktop Logs
tail -100 ~/.config/Claude/logs/mcp-server-solr-search.log | grep "refresh"

# Sollte zeigen:
# "Token refresh background task started"
# "Token refresh task started (interval: 240 seconds)"
```

---

## ✨ Zusammenfassung

**Jetzt NEU:**
- ✅ Automatisches OAuth Token Management
- ✅ Kein manuelles Token-Handling
- ✅ Token läuft nie ab (auto-refresh)
- ✅ Perfekt für Single-User / Development
- ✅ Einfach: "Suche nach python" - Done!

**Geeignet für:**
- ✅ Lokale Entwicklung
- ✅ Testing
- ✅ Single-User Szenarien
- ✅ Demos

**Nicht geeignet für:**
- ❌ Multi-User mit unterschiedlichen Permissions
- ❌ Production mit vielen Nutzern

Für Production: Warte auf MCP Client OAuth Support (Claude Desktop Feature Request)

---

## 🎯 Nächste Schritte

1. **Teste die automatische Suche** (Test 1)
2. **Prüfe die Logs** (Test 3)
3. **Warte 5 Minuten und teste nochmal** (Test 4)
4. **Genieße die Bequemlichkeit!** 🎉

Viel Erfolg! 🚀
