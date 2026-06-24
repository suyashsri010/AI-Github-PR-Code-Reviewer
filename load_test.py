"""
Load test script for /webhook/github endpoint.
Run locally: python3 load_test.py
Requires: pip install httpx --break-system-packages (or in a venv)
"""
import hashlib
import hmac
import json
import time
import statistics
import random
import httpx
import os

# ---- CONFIG: fill these in ----
GATEWAY_URL = "http://a6996ffb1100946239a5f8a18dc4b825-451310394.us-east-1.elb.amazonaws.com/webhook/github"
WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "PASTE_YOUR_SECRET_HERE")
NUM_REQUESTS = 50          # total requests to send
CONCURRENCY = 10           # how many at once
# --------------------------------

def make_payload(i: int) -> dict:
    """Each request gets a unique PR number + SHA so we don't trigger
    the duplicate-event idempotency check (real GitHub traffic wouldn't
    send identical PR+SHA concurrently either — this mirrors real usage)."""
    pr_number = 1000 + i
    sha = hashlib.sha1(f"sha-{i}-{random.random()}".encode()).hexdigest()
    return {
        "action": "opened",
        "number": pr_number,
        "pull_request": {
            "id": 1000000 + i,
            "number": pr_number,
            "title": f"Test PR #{pr_number} - retry logic",
            "state": "open",
            "diff_url": f"https://github.com/example/repo/pull/{pr_number}.diff",
            "user": {"login": "suyash"},
            "head": {"sha": sha, "ref": f"feature/test-{i}"},
            "base": {"sha": "def456", "ref": "main"},
            "additions": 45,
            "deletions": 12,
            "changed_files": 3,
        },
        "repository": {
            "id": 987654321,
            "full_name": "example/repo",
            "name": "repo",
        },
        "installation": {"id": 11111},
    }

def sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

def send_one(client: httpx.Client, i: int):
    body_bytes = json.dumps(make_payload(i)).encode()
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": sign(body_bytes, WEBHOOK_SECRET),
        "X-GitHub-Event": "pull_request",
    }
    start = time.perf_counter()
    try:
        resp = client.post(GATEWAY_URL, content=body_bytes, headers=headers, timeout=30)
        elapsed = (time.perf_counter() - start) * 1000  # ms
        return elapsed, resp.status_code
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed, f"ERROR: {e}"

def main():
    if WEBHOOK_SECRET == "PASTE_YOUR_SECRET_HERE":
        print("ERROR: Set GITHUB_WEBHOOK_SECRET env var or edit the script.")
        return

    print(f"Sending {NUM_REQUESTS} requests (unique PR per request), concurrency={CONCURRENCY}...")
    latencies = []
    statuses = {}

    import concurrent.futures
    with httpx.Client() as client:
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
            futures = [executor.submit(send_one, client, i) for i in range(NUM_REQUESTS)]
            for f in concurrent.futures.as_completed(futures):
                elapsed, status = f.result()
                latencies.append(elapsed)
                statuses[str(status)] = statuses.get(str(status), 0) + 1
                print(f"  {elapsed:.1f}ms -> {status}")

    latencies.sort()
    n = len(latencies)
    p50 = latencies[int(n * 0.50)]
    p95 = latencies[int(n * 0.95) if n > 1 else 0]
    p99 = latencies[int(n * 0.99) if n > 1 else 0]

    print("\n" + "="*40)
    print("RESULTS")
    print("="*40)
    print(f"Total requests : {n}")
    print(f"Status codes   : {statuses}")
    print(f"Min latency    : {min(latencies):.1f}ms")
    print(f"Max latency    : {max(latencies):.1f}ms")
    print(f"Mean latency   : {statistics.mean(latencies):.1f}ms")
    print(f"p50 latency    : {p50:.1f}ms")
    print(f"p95 latency    : {p95:.1f}ms")
    print(f"p99 latency    : {p99:.1f}ms")
    print("="*40)

if __name__ == "__main__":
    main()

    latencies.sort()
    n = len(latencies)
    p50 = latencies[int(n * 0.50)]
    p95 = latencies[int(n * 0.95) if n > 1 else 0]
    p99 = latencies[int(n * 0.99) if n > 1 else 0]

    print("\n" + "="*40)
    print("RESULTS")
    print("="*40)
    print(f"Total requests : {n}")
    print(f"Status codes   : {statuses}")
    print(f"Min latency    : {min(latencies):.1f}ms")
    print(f"Max latency    : {max(latencies):.1f}ms")
    print(f"Mean latency   : {statistics.mean(latencies):.1f}ms")
    print(f"p50 latency    : {p50:.1f}ms")
    print(f"p95 latency    : {p95:.1f}ms")
    print(f"p99 latency    : {p99:.1f}ms")
    print("="*40)

if __name__ == "__main__":
    main()
    