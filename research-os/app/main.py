"""Research OS example application entrypoint with health endpoint and logging."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import json
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("research-os")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path or "/"
        if path == "/health":
            payload = {"status": "healthy"}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode())
            logger.info("/health checked")
            return

        # default root
        if path == "/" or path == "":
            payload = {"status": "ok", "name": "research-os"}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode())
            logger.info("/ served")
            return

        # not found
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": "not found"}).encode())


def run(server_class=HTTPServer, handler_class=Handler):
    port = int(os.environ.get("RESEARCH_OS_PORT", "8080"))
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    logger.info(f"Research OS running on port {port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down")
        httpd.server_close()


if __name__ == "__main__":
    run()
