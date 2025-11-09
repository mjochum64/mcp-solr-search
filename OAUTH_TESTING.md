# OAuth 2.1 Testing Guide für Claude Desktop

## Voraussetzungen

✅ Keycloak läuft (`docker-compose up -d`)
✅ OAuth aktiviert in `.env` (`ENABLE_OAUTH=true`)
✅ Claude Desktop neu gestartet

---

## Test 1: Suche MIT OAuth Token (sollte funktionieren ✅)

### Schritt 1: Token holen

Im Terminal:
```bash
cd /home/mjochum/projekte/mcp-solr-search
./get-oauth-token.sh
```

**Output:**
```
✅ Access token received!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Token (copy this):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJSZ...
```

**→ Kopiere den Token!**

### Schritt 2: In Claude Desktop eingeben

**Variante A - Explizit mit Parameter:**
```
Nutze das search Tool mit folgenden Parametern:
- query: "machine learning"
- access_token: "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJSZ..."
```

**Variante B - Natürlichsprachlich:**
```
Suche nach "machine learning" in Solr. Verwende dabei diesen access_token:
eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJSZ...
```

**Erwartetes Ergebnis:**
```
✅ Suche erfolgreich!
Gefunden: 1 Dokument
- ID: doc2
- Title: Machine Learning Basics
```

---

## Test 2: Suche OHNE OAuth Token (sollte fehlschlagen ❌)

### In Claude Desktop eingeben:

```
Suche nach "python" in Solr
```

**Erwartetes Ergebnis:**
```
❌ Fehler: Authentication failed: No access token provided
```

Oder in der MCP-Antwort:
```json
{
  "error": "Authentication failed: No access token provided"
}
```

---

## Test 3: Suche mit UNGÜLTIGEM Token (sollte fehlschlagen ❌)

### In Claude Desktop eingeben:

```
Nutze das search Tool mit:
- query: "python"
- access_token: "invalid-token-12345"
```

**Erwartetes Ergebnis:**
```
❌ Fehler: Authentication failed: Token invalid or expired
```

---

## Test 4: get_document mit OAuth

### Schritt 1: Token holen (wie in Test 1)

### Schritt 2: In Claude Desktop

```
Hole das Dokument mit ID "doc1" aus Solr mit diesem access_token:
eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJSZ...
```

**Erwartetes Ergebnis:**
```
✅ Dokument gefunden:
- ID: doc1
- Title: Introduction to Apache Solr
```

---

## Test 5: Token-Ablauf testen (optional)

### Schritt 1: Token holen

```bash
./get-oauth-token.sh
```

### Schritt 2: 6 Minuten warten

```bash
sleep 360  # 6 Minuten = 360 Sekunden
```

### Schritt 3: Verwende den ALTEN Token in Claude Desktop

```
Suche nach "python" in Solr mit diesem access_token:
[DEIN ALTER TOKEN]
```

**Erwartetes Ergebnis:**
```
❌ Fehler: Authentication failed: Token expired
```

---

## Troubleshooting

### Problem: "MCP Tool nicht gefunden"

**Lösung:**
- Claude Desktop neu starten: `pkill -f "Claude" && claude-desktop`
- Prüfe ~/.config/Claude/claude_desktop_config.json

### Problem: "Keycloak antwortet nicht"

**Lösung:**
```bash
# Prüfe ob Keycloak läuft
curl http://localhost:8080/health/ready

# Falls nicht, starte neu
docker-compose restart keycloak
```

### Problem: "Token kann nicht abgerufen werden"

**Lösung:**
```bash
# Prüfe Keycloak-Setup
./setup-keycloak.sh

# Test mit dem Test-Script
./test-keycloak.sh w9ynv6VG4yfM86x6XTwjB1RBrrpkEt6b
```

### Problem: "Suche funktioniert auch ohne Token"

**Ursache:** OAuth ist nicht aktiviert

**Lösung:**
```bash
# Prüfe .env
grep ENABLE_OAUTH .env

# Sollte sein: ENABLE_OAUTH=true
# Falls nicht, ändere und starte Claude Desktop neu
```

---

## MCP Server Logs prüfen

**Claude Desktop Logs:**
```bash
# Liste alle MCP Logs
ls -lah ~/.config/Claude/logs/mcp*.log

# Zeige letzten Log-Eintrag
tail -100 ~/.config/Claude/logs/mcp-server-solr-search.log
```

**Wichtige Log-Zeilen bei OAuth:**
```
INFO: OAuth is enabled, token validation required
INFO: Validating OAuth token...
INFO: Token validated successfully, scopes: ['solr:search', 'solr:read']
```

Oder bei Fehlern:
```
ERROR: Authentication failed: No access token provided
ERROR: Authentication failed: Token invalid or expired
ERROR: Authentication failed: Insufficient scopes
```

---

## OAuth deaktivieren (zurück zu vorher)

```bash
# In .env ändern
sed -i 's/ENABLE_OAUTH=true/ENABLE_OAUTH=false/' .env

# Claude Desktop neu starten
pkill -f "Claude"
claude-desktop
```

Dann funktionieren Suchen wieder ohne Token.

---

## Token-Details verstehen

Ein OAuth Access Token von Keycloak enthält:

- **Gültigkeit:** 300 Sekunden (5 Minuten)
- **Scopes:** `solr:search`, `solr:read`
- **User:** testuser
- **Client:** solr-search-server

Du kannst den Token dekodieren auf: https://jwt.io

**Beispiel-Payload:**
```json
{
  "exp": 1762682323,
  "iat": 1762682023,
  "scope": "profile solr:search email solr:read",
  "preferred_username": "testuser",
  "email": "testuser@example.com"
}
```

Der MCP Server prüft:
1. ✅ Token ist gültig (nicht abgelaufen)
2. ✅ Token kommt von Keycloak (JWKS-Signatur)
3. ✅ Scopes enthalten `solr:search` und `solr:read`

Wenn alles OK → Suche wird durchgeführt
Wenn nicht OK → Fehler wird zurückgegeben
