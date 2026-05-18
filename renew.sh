#!/usr/bin/env bash
# ACLClouds Auto-Renew Script
# Renews all free servers on dash.aclclouds.com

set -euo pipefail

EMAIL="${ACL_EMAIL:?Missing ACL_EMAIL}"
PASSWORD="${ACL_PASSWORD:?Missing ACL_PASSWORD}"
BASE_URL="https://dash.aclclouds.com"
COOKIE_JAR=$(mktemp)
trap "rm -f $COOKIE_JAR" EXIT

echo "=== ACLClouds Auto-Renew ==="
echo "Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

# Step 1: Get login page for CSRF token
echo "[1] Getting CSRF token..."
LOGIN_PAGE=$(curl -s -c "$COOKIE_JAR" "$BASE_URL/auth/login" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")

XSRF_TOKEN=$(grep XSRF-TOKEN "$COOKIE_JAR" | awk '{print $NF}')
XSRF_DECODED=$(python3 -c "import urllib.parse; print(urllib.parse.unquote('$XSRF_TOKEN'))")

# Step 2: Login
echo "[2] Logging in as $EMAIL..."
LOGIN_RESP=$(curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  "$BASE_URL/auth/login" \
  -X POST \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Requested-With: XMLHttpRequest" \
  -H "X-XSRF-TOKEN: $XSRF_DECODED" \
  -H "Referer: $BASE_URL/auth/login" \
  -H "Origin: $BASE_URL" \
  -d "email=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$EMAIL'))")&password=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$PASSWORD'))")")

# Refresh XSRF after login
XSRF_TOKEN=$(grep XSRF-TOKEN "$COOKIE_JAR" | awk '{print $NF}')
XSRF_DECODED=$(python3 -c "import urllib.parse; print(urllib.parse.unquote('$XSRF_TOKEN'))")

# Step 3: Get server list
echo "[3] Fetching server list..."
SERVERS=$(curl -s -b "$COOKIE_JAR" \
  "$BASE_URL/api/client" \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -H "X-XSRF-TOKEN: $XSRF_DECODED")

# Check auth
if echo "$SERVERS" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'errors' not in d or d['errors'][0]['code'] != 'AuthenticationException'" 2>/dev/null; then
  echo "[OK] Authenticated successfully"
else
  echo "[FAIL] Authentication failed!"
  echo "$SERVERS"
  exit 1
fi

# Step 4: Renew each server
SERVER_COUNT=$(echo "$SERVERS" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['data']))")
echo "[4] Found $SERVER_COUNT server(s)"

RESULT=""
for i in $(seq 0 $((SERVER_COUNT - 1))); do
  UUID=$(echo "$SERVERS" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'][$i]['attributes']['uuid'])")
  NAME=$(echo "$SERVERS" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'][$i]['attributes']['name'])")
  CAN_RENEW=$(echo "$SERVERS" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'][$i]['attributes']['can_renew'])")
  EXPIRES=$(echo "$SERVERS" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'][$i]['attributes']['expires_at'])")

  echo ""
  echo "--- Server: $NAME (UUID: $UUID) ---"
  echo "  Expires: $EXPIRES"
  echo "  Can renew: $CAN_RENEW"

  if [ "$CAN_RENEW" = "True" ] || [ "$CAN_RENEW" = "true" ]; then
    echo "  [RENEWING]..."
    RENEW_RESP=$(curl -s -b "$COOKIE_JAR" \
      "$BASE_URL/api/client/servers/$UUID/upgrade/renew" \
      -X POST \
      -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
      -H "Accept: application/json" \
      -H "Content-Type: application/json" \
      -H "X-Requested-With: XMLHttpRequest" \
      -H "X-XSRF-TOKEN: $XSRF_DECODED" \
      -H "Origin: $BASE_URL" \
      -H "Referer: $BASE_URL/")
    
    echo "  Response: $RENEW_RESP"
    
    if echo "$RENEW_RESP" | grep -q "requires_payment"; then
      RESULT="$RESULT\n✅ $NAME: Renewal requires payment"
    elif echo "$RENEW_RESP" | grep -q "error"; then
      ERROR=$(echo "$RENEW_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('error','unknown'))" 2>/dev/null || echo "unknown")
      RESULT="$RESULT\n⚠️ $NAME: $ERROR"
    else
      RESULT="$RESULT\n✅ $NAME: Renewed successfully!"
    fi
  else
    DAYS=$(echo "$SERVERS" | python3 -c "import sys,json; d=json.load(sys.stdin)['data'][$i]['attributes']; from datetime import datetime; exp=d.get('expires_at',''); print('N/A')" 2>/dev/null)
    RESULT="$RESULT\n⏳ $NAME: Not available yet (expires: $EXPIRES)"
  fi
done

echo ""
echo "=== Summary ==="
echo -e "$RESULT"
echo ""
echo "Done at $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
