import json
import os
import socket
import subprocess
import sys
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
    # Start the example app as a subprocess
    proc = subprocess.Popen([sys.executable, "research-os/app/main.py"], env=env)
    return proc


def wait_for_http(url, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                return r.read()
        except Exception:
            time.sleep(0.2)
    raise TimeoutError(f"{url} not responsive after {timeout}s")


def test_health_endpoint():
    port = find_free_port()
    proc = start_server(port)
    try:
        body = wait_for_http(f"http://127.0.0.1:{port}/health", timeout=10)
        data = json.loads(body)
        assert data.get("status") == "healthy"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


def test_root_endpoint():
    port = find_free_port()
    proc = start_server(port)
    try:
        body = wait_for_http(f"http://127.0.0.1:{port}/")
        data = json.loads(body)
        assert data.get("status") == "ok"
        assert data.get("name") == "research-os"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
