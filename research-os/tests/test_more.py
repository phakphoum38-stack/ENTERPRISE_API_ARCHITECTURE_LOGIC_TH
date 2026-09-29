import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request


def find_free_port():
    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def start_server(port):
    env = os.environ.copy()
    env["RESEARCH_OS_PORT"] = str(port)
    proc = subprocess.Popen([sys.executable, "research-os/app/main.py"], env=env)
    return proc


def wait_for_http(url, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                return r.read()
        except Exception:
            time.sleep(0.1)
    raise TimeoutError(f"{url} not responsive after {timeout}s")


def test_404():
    port = find_free_port()
    proc = start_server(port)
    try:
        # Wait for server to be ready, then request a missing path
        wait_for_http(f"http://127.0.0.1:{port}/health", timeout=5)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/does-not-exist") as r:
                body = r.read()
                # Should not reach here
                assert False, "expected 404 response"
        except urllib.error.HTTPError as e:
            # urllib raises HTTPError for non-200 responses
            assert e.code == 404
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


def test_concurrent_requests():
    port = find_free_port()
    proc = start_server(port)
    try:
        time.sleep(0.2)
        results = []

        def worker():
            try:
                body = wait_for_http(f"http://127.0.0.1:{port}/health", timeout=5)
                d = json.loads(body)
                results.append(d.get("status"))
            except Exception:
                results.append(None)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(r == "healthy" for r in results)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
