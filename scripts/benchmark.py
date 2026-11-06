"""
Benchmarking harness for VLM Document Extraction API.
Measures P50, P95, P99 latency, throughput (req/s), and error rates.
"""

import asyncio
import time
import statistics
import httpx


API_URL = "http://localhost:8000/api/v1/extract"
SAMPLE_FILE = "sample_invoice.png"
NUM_REQUESTS = 30
CONCURRENCY = 5


async def send_extraction_request(client: httpx.AsyncClient, file_bytes: bytes, sem: asyncio.Semaphore):
    async with sem:
        t0 = time.perf_counter()
        files = {"file": ("invoice.png", file_bytes, "image/png")}
        data = {"provider": "mock"}
        try:
            resp = await client.post(API_URL, files=files, data=data, timeout=30.0)
            elapsed = (time.perf_counter() - t0) * 1000.0
            return resp.status_code == 200, elapsed, resp.json()
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000.0
            return False, elapsed, str(e)


async def run_benchmark():
    print(f"[*] Starting benchmark on {API_URL}")
    print(f"[*] Total Requests: {NUM_REQUESTS} | Concurrency: {CONCURRENCY}")

    try:
        with open(SAMPLE_FILE, "rb") as f:
            file_bytes = f.read()
    except FileNotFoundError:
        # Fallback dummy payload
        file_bytes = b"dummy-image-content"

    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient() as client:
        start_wall = time.perf_counter()
        tasks = [send_extraction_request(client, file_bytes, sem) for _ in range(NUM_REQUESTS)]
        results = await asyncio.gather(*tasks)
        total_wall = time.perf_counter() - start_wall

    successes = [r for r in results if r[0]]
    latencies = [r[1] for r in successes]

    print("\n" + "=" * 50)
    print("           BENCHMARK RESULTS")
    print("=" * 50)
    print(f"Success Rate:         {len(successes)}/{NUM_REQUESTS} ({len(successes)/NUM_REQUESTS*100:.1f}%)")
    print(f"Total Wall Clock:     {total_wall:.2f} seconds")
    print(f"Throughput:           {len(successes)/total_wall:.2f} req/sec")

    if latencies:
        print(f"P50 (Median) Latency: {statistics.median(latencies):.2f} ms")
        sorted_lat = sorted(latencies)
        p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
        p99 = sorted_lat[min(int(len(sorted_lat) * 0.99), len(sorted_lat) - 1)]
        print(f"P95 Latency:          {p95:.2f} ms")
        print(f"P99 Latency:          {p99:.2f} ms")
        print(f"Min / Max:            {min(latencies):.2f} ms / {max(latencies):.2f} ms")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
