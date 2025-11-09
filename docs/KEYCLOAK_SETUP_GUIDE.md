# Keycloak Setup Testing Guide

This guide walks you through testing the Keycloak setup step by step.

## ✅ Prerequisites

- Docker and Docker Compose installed
- Keycloak container running (check with `docker-compose ps`)

## 🚀 Step-by-Step Setup

### Step 1: Access Keycloak Admin Console

1. **Open your browser** and navigate to:
   ```
   http://localhost:8080
   ```

2. **Login** with default credentials:
   ```
   Username: admin
   Password: admin
   ```

3. You should see the Keycloak Admin Console welcome screen.

---

### Step 2: Create Realm "solr-mcp"

1. **Click** on the dropdown in the top-left corner (currently shows "master")
2. **Click** "Create Realm"
3. **Enter** the following:
   - **Realm name**: `solr-mcp`
   - **Enabled**: ON (toggle switch)
4. **Click** "Create"

**Result:** You should now see "solr-mcp" in the realm dropdown.

---

### Step 3: Create Client "solr-search-server"

1. **Navigate** to: Clients (in left sidebar)
2. **Click** "Create client"
3. **General Settings:**
   - **Client type**: `OpenID Connect`
   - **Client ID**: `solr-search-server`
4. **Click** "Next"
5. **Capability config:**
   - **Client authentication**: `ON` (toggle switch)
   - **Authorization**: `OFF`
   - **Authentication flow**: Check all boxes
6. **Click** "Next"
7. **Login settings:**
   - **Root URL**: `http://localhost:8765`
   - **Home URL**: `http://localhost:8765`
   - **Valid redirect URIs**: `http://localhost:8765/*`
   - **Web origins**: `http://localhost:8765`
8. **Click** "Save"

**Result:** Client "solr-search-server" created successfully.

---

### Step 4: Get Client Secret

1. **Stay in** the "solr-search-server" client view
2. **Click** on the "Credentials" tab
3. **Copy** the "Client secret" value
4. **Save it** - you'll need this for `.env` file

Example:
```
Client Secret: xK7mP9nQ2wR5tY8uI1oP3sA6vB4cD0eF
```

---

### Step 5: Create Client Scopes

Now we'll create custom scopes for fine-grained permissions.

#### 5.1 Create "solr:search" scope

1. **Navigate** to: Client Scopes (in left sidebar)
2. **Click** "Create client scope"
3. **Enter:**
   - **Name**: `solr:search`
   - **Description**: `Permission to search in Solr`
   - **Type**: `Optional`
   - **Protocol**: `OpenID Connect`
4. **Click** "Save"

#### 5.2 Create "solr:read" scope

1. **Click** "Create client scope" again
2. **Enter:**
   - **Name**: `solr:read`
   - **Description**: `Permission to read Solr documents`
   - **Type**: `Optional`
   - **Protocol**: `OpenID Connect`
3. **Click** "Save"

#### 5.3 Create "solr:write" scope (optional, for future use)

1. **Click** "Create client scope" again
2. **Enter:**
   - **Name**: `solr:write`
   - **Description**: `Permission to write to Solr`
   - **Type**: `Optional`
   - **Protocol**: `OpenID Connect`
3. **Click** "Save"

#### 5.4 Create "solr:admin" scope (optional, for admin operations)

1. **Click** "Create client scope" again
2. **Enter:**
   - **Name**: `solr:admin`
   - **Description**: `Administrative access to Solr MCP server`
   - **Type**: `Optional`
   - **Protocol**: `OpenID Connect`
3. **Click** "Save"

**Result:** Four client scopes created.

---

### Step 6: Assign Scopes to Client

1. **Navigate** to: Clients → solr-search-server
2. **Click** on the "Client scopes" tab
3. **Click** "Add client scope"
4. **Select** the following scopes:
   - `solr:search`
   - `solr:read`
   - `solr:write` (optional)
   - `solr:admin` (optional)
5. **Choose** "Optional" (not "Default")
6. **Click** "Add"

**Result:** Scopes are now available for this client.

---

### Step 7: Create Test User

1. **Navigate** to: Users (in left sidebar)
2. **Click** "Add user"
3. **Enter:**
   - **Username**: `testuser`
   - **Email**: `testuser@example.com`
   - **Email verified**: `ON` (toggle)
   - **First name**: `Test`
   - **Last name**: `User`
   - **Enabled**: `ON` (toggle)
4. **Click** "Create"

**Result:** User "testuser" created.

---

### Step 8: Set User Password

1. **Stay in** the testuser view
2. **Click** on the "Credentials" tab
3. **Click** "Set password"
4. **Enter:**
   - **Password**: `testpassword`
   - **Password confirmation**: `testpassword`
   - **Temporary**: `OFF` (toggle - so user doesn't need to change password)
5. **Click** "Save"
6. **Confirm** the warning dialog

**Result:** Password set for testuser.

---

### Step 9: Assign Scopes to User

1. **Stay in** the testuser view
2. **Click** on the "Role mapping" tab
3. This step is for role-based access. For now, we'll use scopes directly in token requests.

**Note:** Scopes will be requested during OAuth flow, not assigned to users directly.

---

### Step 10: Test OAuth Flow (Manual)

Now let's test if the OAuth setup works!

#### 10.1 Get Token via curl

Open a terminal and run:

```bash
# Replace CLIENT_SECRET with your actual client secret from Step 4
CLIENT_SECRET="your-client-secret-here"

curl -X POST "http://localhost:8080/realms/solr-mcp/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=solr-search-server" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "username=testuser" \
  -d "password=testpassword" \
  -d "grant_type=password" \
  -d "scope=solr:search solr:read" \
  | python -m json.tool
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300,
  "refresh_expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "not-before-policy": 0,
  "session_state": "...",
  "scope": "solr:read solr:search"
}
```

✅ **Success!** You received an access token!

---

#### 10.2 Decode Token

Let's verify the token contains our scopes:

```bash
# Copy the access_token from the previous response
TOKEN="paste-your-access-token-here"

# Decode JWT (splits on '.' and base64 decodes the payload)
echo $TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | python -m json.tool
```

**Expected Output:**
```json
{
  "exp": 1699462800,
  "iat": 1699462500,
  "jti": "...",
  "iss": "http://localhost:8080/realms/solr-mcp",
  "aud": "account",
  "sub": "...",
  "typ": "Bearer",
  "azp": "solr-search-server",
  "scope": "solr:read solr:search",
  "preferred_username": "testuser",
  "email": "testuser@example.com"
}
```

✅ **Success!** Token contains correct scopes and user info!

---

#### 10.3 Validate Token

Test if Keycloak can validate the token:

```bash
curl -X POST "http://localhost:8080/realms/solr-mcp/protocol/openid-connect/token/introspect" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "solr-search-server:$CLIENT_SECRET" \
  -d "token=$TOKEN" \
  | python -m json.tool
```

**Expected Response:**
```json
{
  "exp": 1699462800,
  "iat": 1699462500,
  "jti": "...",
  "iss": "http://localhost:8080/realms/solr-mcp",
  "aud": "account",
  "sub": "...",
  "typ": "Bearer",
  "azp": "solr-search-server",
  "preferred_username": "testuser",
  "email_verified": true,
  "scope": "solr:read solr:search",
  "client_id": "solr-search-server",
  "username": "testuser",
  "active": true
}
```

✅ **Success!** Token is valid and active!

---

## ✅ Verification Checklist

Mark each item as completed:

- [ ] Accessed Keycloak Admin Console (http://localhost:8080)
- [ ] Logged in with admin/admin
- [ ] Created realm "solr-mcp"
- [ ] Created client "solr-search-server"
- [ ] Copied client secret
- [ ] Created client scopes (solr:search, solr:read)
- [ ] Assigned scopes to client
- [ ] Created test user "testuser"
- [ ] Set password "testpassword"
- [ ] Got access token via curl
- [ ] Decoded token and verified scopes
- [ ] Validated token successfully

---

## 🔧 Update .env File

Now update your `.env` file with the real values:

```bash
# Copy .env.example to .env if not exists
cp .env.example .env

# Edit .env and set:
ENABLE_OAUTH=false  # Set to 'true' when OAuth code is implemented
OAUTH_PROVIDER=keycloak
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=solr-mcp
KEYCLOAK_CLIENT_ID=solr-search-server
KEYCLOAK_CLIENT_SECRET=<paste-your-client-secret-from-step-4>
OAUTH_SCOPES=solr:search,solr:read
```

---

## 🧹 Cleanup (Optional)

To stop and remove Keycloak:

```bash
# Stop containers but keep data
docker-compose stop keycloak postgres

# Stop and remove containers (keeps volumes)
docker-compose down

# Remove everything including volumes (complete reset)
docker-compose down -v
```

---

## 🐛 Troubleshooting

### Keycloak won't start

```bash
# Check logs
docker-compose logs keycloak

# Restart
docker-compose restart keycloak
```

### Can't access http://localhost:8080

```bash
# Check if port is in use
lsof -i :8080

# Check container status
docker-compose ps
```

### Token request fails

```bash
# Verify client secret is correct
# Check username/password are correct
# Ensure scopes exist in Keycloak
```

---

## 📚 Next Steps

Once Keycloak is working:

1. ✅ Keycloak setup complete
2. ⏭️ Implement OAuth in MCP server code
3. ⏭️ Test OAuth with MCP server
4. ⏭️ Integrate with Claude Desktop

See `docs/OAUTH_GUIDE.md` for implementation details.

---

**Last Updated:** November 8, 2025
**Keycloak Version:** 23.0
**Author:** Claude Code

🤖 Generated with [Claude Code](https://claude.com/claude-code)
