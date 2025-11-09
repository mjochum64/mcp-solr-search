#!/bin/bash
# Quick script to get an OAuth access token from Keycloak for testing

KEYCLOAK_URL="http://localhost:8080"
REALM="solr-mcp"
CLIENT_ID="solr-search-server"
CLIENT_SECRET="w9ynv6VG4yfM86x6XTwjB1RBrrpkEt6b"
USERNAME="testuser"
PASSWORD="testpassword"

echo "🔑 Getting OAuth access token from Keycloak..."
echo ""

# Get token
RESPONSE=$(curl -s -X POST \
  "${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "username=${USERNAME}" \
  -d "password=${PASSWORD}" \
  -d "grant_type=password" \
  -d "scope=solr:search solr:read")

# Extract access token
ACCESS_TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ Error: Could not get access token"
  echo "Response: $RESPONSE"
  exit 1
fi

echo "✅ Access token received!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Token (copy this):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "$ACCESS_TOKEN"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Use this token in Claude Desktop:"
echo "   \"Suche nach 'python' in Solr mit diesem Token: $ACCESS_TOKEN\""
echo ""
echo "⏱  Token expires in: $(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['expires_in'])" 2>/dev/null) seconds"
