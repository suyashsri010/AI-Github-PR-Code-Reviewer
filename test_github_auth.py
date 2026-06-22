"""
Standalone test: get a fresh GitHub App installation token and try
posting a review directly. Isolates whether the 403 is a token/timing
issue or something else, independent of the running K8s pods.

Run locally: python3 test_github_auth.py
Requires: pip install pyjwt httpx cryptography --break-system-packages
"""
import time
import jwt
import httpx

# ---- FILL THESE IN ----
GITHUB_APP_ID = "4076089"          # e.g. 4076089
INSTALLATION_ID = "141746133"     # the installation_id from your earlier secret/logs
PRIVATE_KEY_PATH = "/tmp/github_app.pem"   # save your private key to a local .pem file, or paste inline below
REPO_FULL_NAME = "suyashsri010/BhashaBlend-Heterogeneous-Audio-NLP-Summarization-Engine"
PR_NUMBER = 3  # use a NEW pr number you haven't tested yet, ideally one you just opened
# ------------------------

def get_private_key():
    with open(PRIVATE_KEY_PATH, "r") as f:
        return f.read()

def get_installation_token():
    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + 600, "iss": GITHUB_APP_ID}
    private_key = get_private_key()
    encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")

    resp = httpx.post(
        f"https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens",
        headers={
            "Authorization": f"Bearer {encoded_jwt}",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    print("Token request status:", resp.status_code)
    resp.raise_for_status()
    return resp.json()["token"]

def check_app_permissions(token):
    """Check what permissions GitHub actually granted this installation token."""
    resp = httpx.get(
        "https://api.github.com/installation/repositories",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    print("Installation repos check status:", resp.status_code)
    print(resp.json() if resp.status_code == 200 else resp.text)

def try_post_review(token):
    url = f"https://api.github.com/repos/{REPO_FULL_NAME}/pulls/{PR_NUMBER}/reviews"
    resp = httpx.post(
        url,
        json={"event": "COMMENT", "body": "Test comment from standalone debug script."},
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    print(f"\nReview POST to {url}")
    print("Status:", resp.status_code)
    print("Response:", resp.text[:1000])

if __name__ == "__main__":
    print("=== Step 1: Getting fresh installation token ===")
    token = get_installation_token()
    print("Got token (first 20 chars):", token[:20], "...")

    print("\n=== Step 2: Checking what repos/permissions this token sees ===")
    check_app_permissions(token)

    print("\n=== Step 3: Attempting to post a review comment ===")
    try_post_review(token)