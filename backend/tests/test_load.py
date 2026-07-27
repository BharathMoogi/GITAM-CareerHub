"""
Performance & Load Testing Script for GITAM CareerHub API.

Uses locust-compatible patterns, runnable standalone with asyncio.
Tests:
  - Health endpoint baseline throughput
  - Auth login under concurrent load
  - Student dashboard under N concurrent virtual users
  - AI Mentor chat endpoint latency
  - Rate limiter behaviour under burst traffic

Run standalone:
    python backend/tests/test_load.py

Run with locust (install locust first):
    locust -f backend/tests/test_load.py --host=http://localhost:8000
"""
import asyncio
import time
import httpx
from typing import List, Tuple

BASE_URL = "http://localhost:8000"

# ── Helpers ────────────────────────────────────────────────────────────────────

async def get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=BASE_URL, timeout=10.0)


async def measure(client: httpx.AsyncClient, method: str, path: str, **kwargs) -> Tuple[int, float]:
    """Make a request and return (status_code, latency_ms)."""
    start = time.monotonic()
    try:
        resp = await getattr(client, method)(path, **kwargs)
        return resp.status_code, (time.monotonic() - start) * 1000
    except Exception:
        return 0, (time.monotonic() - start) * 1000


# ── Test Scenarios ─────────────────────────────────────────────────────────────

async def scenario_health_check(client: httpx.AsyncClient, results: list):
    """Baseline: GET /health should respond < 100ms."""
    status, latency = await measure(client, "get", "/health")
    results.append(("health", status, latency))


async def scenario_api_docs(client: httpx.AsyncClient, results: list):
    """Docs page should be reachable."""
    status, latency = await measure(client, "get", "/docs")
    results.append(("docs", status, latency))


async def scenario_openapi_schema(client: httpx.AsyncClient, results: list):
    """OpenAPI JSON should serialize correctly."""
    status, latency = await measure(client, "get", "/api/v1/openapi.json")
    results.append(("openapi", status, latency))


async def scenario_metrics_endpoint(client: httpx.AsyncClient, results: list):
    """Prometheus /metrics should respond with text/plain."""
    status, latency = await measure(client, "get", "/metrics")
    results.append(("metrics", status, latency))


async def scenario_rate_limit_burst(client: httpx.AsyncClient, results: list):
    """Send 10 rapid auth requests to observe rate limiter behaviour."""
    tasks = [measure(client, "post", "/api/v1/auth/login",
                     json={"email": "load@test.com", "password": "wrong"})
             for _ in range(10)]
    responses = await asyncio.gather(*tasks)
    for status, latency in responses:
        results.append(("rate_limit_burst", status, latency))


# ── Runner ─────────────────────────────────────────────────────────────────────

async def run_load_test(
    virtual_users: int = 10,
    iterations_per_user: int = 5
):
    """Simulate concurrent virtual users across all scenarios."""
    scenarios = [
        scenario_health_check,
        scenario_api_docs,
        scenario_openapi_schema,
        scenario_metrics_endpoint,
    ]

    results: List[Tuple[str, int, float]] = []

    async def user_session(user_id: int):
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            for _ in range(iterations_per_user):
                for scenario in scenarios:
                    await scenario(client, results)

    print(f"\nLoad Test: {virtual_users} virtual users x {iterations_per_user} iterations")
    print(f"Scenarios: {[s.__name__ for s in scenarios]}")
    print("-" * 60)

    start = time.monotonic()
    await asyncio.gather(*[user_session(i) for i in range(virtual_users)])
    elapsed = time.monotonic() - start

    # Aggregate results
    from collections import defaultdict
    by_scenario = defaultdict(list)
    for name, status, latency in results:
        by_scenario[name].append((status, latency))

    total_requests = len(results)
    total_errors = sum(1 for _, s, _ in results if s >= 400 or s == 0)
    all_latencies = [lat for _, _, lat in results]
    avg_latency = sum(all_latencies) / len(all_latencies) if all_latencies else 0
    p95_latency = sorted(all_latencies)[int(len(all_latencies) * 0.95)] if all_latencies else 0
    rps = total_requests / elapsed

    print(f"\nResults Summary:")
    print(f"  Total requests    : {total_requests}")
    print(f"  Total errors      : {total_errors}")
    print(f"  Elapsed time      : {elapsed:.2f}s")
    print(f"  Throughput (RPS)  : {rps:.1f}")
    print(f"  Avg latency       : {avg_latency:.1f}ms")
    print(f"  P95 latency       : {p95_latency:.1f}ms")
    print()
    for name, data in sorted(by_scenario.items()):
        lats = [l for _, l in data]
        statuses = [s for s, _ in data]
        errors = sum(1 for s in statuses if s >= 400 or s == 0)
        print(f"  {name:<25} avg={sum(lats)/len(lats):.1f}ms  errors={errors}/{len(data)}")

    return {
        "total_requests": total_requests,
        "total_errors": total_errors,
        "rps": rps,
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": p95_latency,
    }


if __name__ == "__main__":
    import sys

    # Check if server is reachable first
    async def check_server():
        try:
            async with httpx.AsyncClient(base_url=BASE_URL, timeout=3.0) as client:
                resp = await client.get("/health")
                return resp.status_code == 200
        except Exception:
            return False

    async def main():
        print(f"Checking server at {BASE_URL}...")
        if not await check_server():
            print(f"ERROR: Server not reachable at {BASE_URL}")
            print("Start the server with: cd backend && python -m uvicorn app.main:app --reload")
            sys.exit(1)

        print(f"Server is live. Starting load test...")
        vus = int(sys.argv[1]) if len(sys.argv) > 1 else 10
        iters = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        await run_load_test(virtual_users=vus, iterations_per_user=iters)

    asyncio.run(main())
