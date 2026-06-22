"""
Check what permissions the GitHub App ITSELF is configured with,
bypassing any installation-level caching/confusion.

Run locally: python3 check_app_permissions.py
Requires: pip install pyjwt httpx --break-system-packages
"""
import jwt
import httpx
import time

# ---- FILL THESE IN ----
GITHUB_APP_ID = "4076089"          # same as before, e.g. 4076089
PRIVATE_KEY_PATH = "/tmp/github_app.pem"      # same pem file you saved earlier
# ------------------------

with open(PRIVATE_KEY_PATH) as f:
    private_key = f.read()

now = int(time.time())
payload = {"iat": now - 60, "exp": now + 600, "iss": GITHUB_APP_ID}
encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")

resp = httpx.get(
    "https://api.github.com/app",
    headers={"Authorization": f"Bearer {encoded_jwt}", "Accept": "application/vnd.github.v3+json"},
)
print("Status:", resp.status_code)
print()
data = resp.json()
print("App name:", data.get("name"))
print("App slug:", data.get("slug"))
print()
print("Permissions configured on this App:")
for k, v in (data.get("permissions") or {}).items():
    print(f"  {k}: {v}")