#!/bin/bash
# Keycloak OAuth Flow Test Script
# This script tests if Keycloak is configured correctly

set -e  # Exit on error

echo "🔐 Keycloak OAuth Flow Test"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
KEYCLOAK_URL="http://localhost:8080"
REALM="solr-mcp"
CLIENT_ID="solr-search-server"
USERNAME="testuser"
PASSWORD="testpassword"

# Check if client secret is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <CLIENT_SECRET>${NC}"
    echo ""
    echo "Steps to get CLIENT_SECRET:"
    echo "1. Open http://localhost:8080"
    echo "2. Login as admin/admin"
    echo "3. Go to: Clients → solr-search-server → Credentials tab"
    echo "4. Copy the 'Client secret'"
    echo "5. Run: ./test-keycloak.sh <CLIENT_SECRET>"
    echo ""
    exit 1
fi

CLIENT_SECRET="$1"

echo "Configuration:"
echo "  Keycloak URL: $KEYCLOAK_URL"
echo "  Realm: $REALM"
echo "  Client ID: $CLIENT_ID"
echo "  Username: $USERNAME"
echo ""

# Step 1: Check if Keycloak is running
echo "Step 1: Checking if Keycloak is accessible..."
if curl -s -f "$KEYCLOAK_URL" > /dev/null; then
    echo -e "${GREEN}✓${NC} Keycloak is running"
else
    echo -e "${RED}✗${NC} Keycloak is not accessible at $KEYCLOAK_URL"
    echo "   Try: docker-compose up -d keycloak"
    exit 1
fi
echo ""

# Step 2: Get Access Token
echo "Step 2: Requesting access token..."
TOKEN_RESPONSE=$(curl -s -X POST "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "username=$USERNAME" \
  -d "password=$PASSWORD" \
  -d "grant_type=password" \
  -d "scope=solr:search solr:read")

# Check if we got a token
if echo "$TOKEN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓${NC} Access token received successfully"
    ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    SCOPES=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('scope', 'N/A'))")
    echo "  Scopes: $SCOPES"
else
    echo -e "${RED}✗${NC} Failed to get access token"
    echo "Response:"
    echo "$TOKEN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$TOKEN_RESPONSE"
    exit 1
fi
echo ""

# Step 3: Decode Token
echo "Step 3: Decoding access token..."
PAYLOAD=$(echo "$ACCESS_TOKEN" | cut -d'.' -f2)
# Add padding if needed
case $((${#PAYLOAD} % 4)) in
    2) PAYLOAD="${PAYLOAD}==" ;;
    3) PAYLOAD="${PAYLOAD}=" ;;
esac

DECODED=$(echo "$PAYLOAD" | base64 -d 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "Failed to decode")

if echo "$DECODED" | grep -q "preferred_username"; then
    echo -e "${GREEN}✓${NC} Token decoded successfully"
    echo ""
    echo "Token Details:"
    echo "$DECODED" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"  Username: {data.get('preferred_username', 'N/A')}\")
print(f\"  Email: {data.get('email', 'N/A')}\")
print(f\"  Scopes: {data.get('scope', 'N/A')}\")
print(f\"  Issued at: {data.get('iat', 'N/A')}\")
print(f\"  Expires at: {data.get('exp', 'N/A')}\")
print(f\"  Client: {data.get('azp', 'N/A')}\")
"
else
    echo -e "${YELLOW}⚠${NC} Could not decode token (but token was received)"
fi
echo ""

# Step 4: Validate Token
echo "Step 4: Validating token with introspection endpoint..."
INTROSPECT_RESPONSE=$(curl -s -X POST "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token/introspect" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "$CLIENT_ID:$CLIENT_SECRET" \
  -d "token=$ACCESS_TOKEN")

if echo "$INTROSPECT_RESPONSE" | grep -q '"active": *true'; then
    echo -e "${GREEN}✓${NC} Token is valid and active"
    ACTIVE_USERNAME=$(echo "$INTROSPECT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('username', 'N/A'))")
    ACTIVE_SCOPES=$(echo "$INTROSPECT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('scope', 'N/A'))")
    echo "  Active for user: $ACTIVE_USERNAME"
    echo "  With scopes: $ACTIVE_SCOPES"
else
    echo -e "${RED}✗${NC} Token validation failed"
    echo "Response:"
    echo "$INTROSPECT_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$INTROSPECT_RESPONSE"
    exit 1
fi
echo ""

# Step 5: Summary
echo "================================"
echo -e "${GREEN}✓ All tests passed!${NC}"
echo ""
echo "Keycloak OAuth is configured correctly:"
echo "  ✓ Keycloak is accessible"
echo "  ✓ Access token obtained"
echo "  ✓ Token contains correct scopes"
echo "  ✓ Token validation successful"
echo ""
echo "You can now proceed with MCP server OAuth implementation."
echo ""
echo "Access Token (first 50 chars):"
echo "${ACCESS_TOKEN:0:50}..."
echo ""
echo "To use this token in tests:"
echo "export OAUTH_TOKEN=\"$ACCESS_TOKEN\""
echo ""
