#!/bin/bash
# Automated Keycloak Setup Script
# This script configures Keycloak via Admin REST API

set -e  # Exit on error

echo "🔧 Automated Keycloak Setup"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
KEYCLOAK_URL="http://localhost:8080"
ADMIN_USER="admin"
ADMIN_PASSWORD="admin"
REALM="solr-mcp"
CLIENT_ID="solr-search-server"
USERNAME="testuser"
USER_PASSWORD="testpassword"
USER_EMAIL="testuser@example.com"

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

# Step 2: Get admin access token
echo "Step 2: Getting admin access token..."
ADMIN_TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASSWORD" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$ADMIN_TOKEN" ]; then
    echo -e "${RED}✗${NC} Failed to get admin token"
    exit 1
fi
echo -e "${GREEN}✓${NC} Admin token received"
echo ""

# Step 3: Create realm
echo "Step 3: Creating realm '$REALM'..."
REALM_EXISTS=$(curl -s -o /dev/null -w "%{http_code}" \
  "$KEYCLOAK_URL/admin/realms/$REALM" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

if [ "$REALM_EXISTS" = "200" ]; then
    echo -e "${YELLOW}⚠${NC} Realm '$REALM' already exists, skipping..."
else
    curl -s -X POST "$KEYCLOAK_URL/admin/realms" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"realm\": \"$REALM\",
        \"enabled\": true
      }" > /dev/null
    echo -e "${GREEN}✓${NC} Realm '$REALM' created"
fi
echo ""

# Step 4: Create client scopes
echo "Step 4: Creating client scopes..."
for SCOPE in "solr:search:Permission to search in Solr" \
             "solr:read:Permission to read Solr documents" \
             "solr:write:Permission to write to Solr" \
             "solr:admin:Administrative access to Solr MCP server"; do

    SCOPE_NAME=$(echo $SCOPE | cut -d: -f1,2)
    SCOPE_DESC=$(echo $SCOPE | cut -d: -f3)

    # Check if scope exists
    SCOPE_ID=$(curl -s "$KEYCLOAK_URL/admin/realms/$REALM/client-scopes" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      | python3 -c "import sys, json; scopes = json.load(sys.stdin); print(next((s['id'] for s in scopes if s['name'] == '$SCOPE_NAME'), ''))" 2>/dev/null)

    if [ -n "$SCOPE_ID" ]; then
        echo -e "${YELLOW}⚠${NC} Scope '$SCOPE_NAME' already exists, skipping..."
    else
        curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM/client-scopes" \
          -H "Authorization: Bearer $ADMIN_TOKEN" \
          -H "Content-Type: application/json" \
          -d "{
            \"name\": \"$SCOPE_NAME\",
            \"description\": \"$SCOPE_DESC\",
            \"protocol\": \"openid-connect\",
            \"attributes\": {
              \"include.in.token.scope\": \"true\",
              \"display.on.consent.screen\": \"true\"
            }
          }" > /dev/null
        echo -e "${GREEN}✓${NC} Scope '$SCOPE_NAME' created"
    fi
done
echo ""

# Step 5: Create client
echo "Step 5: Creating client '$CLIENT_ID'..."
CLIENT_UUID=$(curl -s "$KEYCLOAK_URL/admin/realms/$REALM/clients" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | python3 -c "import sys, json; clients = json.load(sys.stdin); print(next((c['id'] for c in clients if c['clientId'] == '$CLIENT_ID'), ''))" 2>/dev/null)

if [ -n "$CLIENT_UUID" ]; then
    echo -e "${YELLOW}⚠${NC} Client '$CLIENT_ID' already exists, skipping creation..."
else
    curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM/clients" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"clientId\": \"$CLIENT_ID\",
        \"enabled\": true,
        \"protocol\": \"openid-connect\",
        \"publicClient\": false,
        \"serviceAccountsEnabled\": true,
        \"authorizationServicesEnabled\": false,
        \"directAccessGrantsEnabled\": true,
        \"standardFlowEnabled\": true,
        \"implicitFlowEnabled\": false,
        \"redirectUris\": [\"http://localhost:8765/*\"],
        \"webOrigins\": [\"http://localhost:8765\"],
        \"attributes\": {
          \"oauth2.device.authorization.grant.enabled\": \"false\",
          \"oidc.ciba.grant.enabled\": \"false\"
        }
      }" > /dev/null
    echo -e "${GREEN}✓${NC} Client '$CLIENT_ID' created"
fi
echo ""

# Get client UUID
CLIENT_UUID=$(curl -s "$KEYCLOAK_URL/admin/realms/$REALM/clients" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | python3 -c "import sys, json; clients = json.load(sys.stdin); print(next((c['id'] for c in clients if c['clientId'] == '$CLIENT_ID'), ''))")

if [ -z "$CLIENT_UUID" ]; then
    echo -e "${RED}✗${NC} Failed to get client UUID"
    exit 1
fi

# Step 6: Get client secret
echo "Step 6: Getting client secret..."
CLIENT_SECRET=$(curl -s "$KEYCLOAK_URL/admin/realms/$REALM/clients/$CLIENT_UUID/client-secret" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['value'])")

if [ -z "$CLIENT_SECRET" ]; then
    echo -e "${RED}✗${NC} Failed to get client secret"
    exit 1
fi
echo -e "${GREEN}✓${NC} Client secret retrieved"
echo ""

# Step 7: Assign scopes to client
echo "Step 7: Assigning scopes to client..."
for SCOPE_NAME in "solr:search" "solr:read" "solr:write" "solr:admin"; do
    # Get scope ID
    SCOPE_ID=$(curl -s "$KEYCLOAK_URL/admin/realms/$REALM/client-scopes" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      | python3 -c "import sys, json; scopes = json.load(sys.stdin); print(next((s['id'] for s in scopes if s['name'] == '$SCOPE_NAME'), ''))")

    if [ -n "$SCOPE_ID" ]; then
        # Add scope to client (optional scope)
        curl -s -X PUT "$KEYCLOAK_URL/admin/realms/$REALM/clients/$CLIENT_UUID/optional-client-scopes/$SCOPE_ID" \
          -H "Authorization: Bearer $ADMIN_TOKEN" > /dev/null
        echo -e "${GREEN}✓${NC} Assigned scope '$SCOPE_NAME' to client"
    fi
done
echo ""

# Step 8: Create test user
echo "Step 8: Creating test user '$USERNAME'..."
USER_ID=$(curl -s "$KEYCLOAK_URL/admin/realms/$REALM/users?username=$USERNAME" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | python3 -c "import sys, json; users = json.load(sys.stdin); print(users[0]['id'] if users else '')" 2>/dev/null)

if [ -n "$USER_ID" ]; then
    echo -e "${YELLOW}⚠${NC} User '$USERNAME' already exists, skipping creation..."
else
    curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM/users" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"username\": \"$USERNAME\",
        \"email\": \"$USER_EMAIL\",
        \"emailVerified\": true,
        \"firstName\": \"Test\",
        \"lastName\": \"User\",
        \"enabled\": true,
        \"credentials\": [{
          \"type\": \"password\",
          \"value\": \"$USER_PASSWORD\",
          \"temporary\": false
        }]
      }" > /dev/null
    echo -e "${GREEN}✓${NC} User '$USERNAME' created"
fi
echo ""

# Get user ID
USER_ID=$(curl -s "$KEYCLOAK_URL/admin/realms/$REALM/users?username=$USERNAME" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | python3 -c "import sys, json; users = json.load(sys.stdin); print(users[0]['id'])")

if [ -z "$USER_ID" ]; then
    echo -e "${RED}✗${NC} Failed to get user ID"
    exit 1
fi

# Step 9: Summary
echo "================================"
echo -e "${GREEN}✓ Keycloak setup complete!${NC}"
echo ""
echo "Configuration:"
echo "  Keycloak URL: $KEYCLOAK_URL"
echo "  Realm: $REALM"
echo "  Client ID: $CLIENT_ID"
echo "  Client Secret: $CLIENT_SECRET"
echo "  Username: $USERNAME"
echo "  Password: $USER_PASSWORD"
echo ""
echo "Scopes created:"
echo "  ✓ solr:search"
echo "  ✓ solr:read"
echo "  ✓ solr:write"
echo "  ✓ solr:admin"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Test OAuth flow with:"
echo "   ${YELLOW}./test-keycloak.sh $CLIENT_SECRET${NC}"
echo ""
echo "2. Update .env file with:"
echo "   ENABLE_OAUTH=false  # Set to 'true' when OAuth code is implemented"
echo "   OAUTH_PROVIDER=keycloak"
echo "   KEYCLOAK_URL=$KEYCLOAK_URL"
echo "   KEYCLOAK_REALM=$REALM"
echo "   KEYCLOAK_CLIENT_ID=$CLIENT_ID"
echo "   KEYCLOAK_CLIENT_SECRET=$CLIENT_SECRET"
echo "   OAUTH_SCOPES=solr:search,solr:read"
echo ""
echo -e "${GREEN}Ready to implement OAuth in MCP server!${NC}"
echo ""
