import json
import logging
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from controllers.book_controller import BookController
from models.book_repository import BookRepository


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"


class LibraryHandler(BaseHTTPRequestHandler):
    controller: BookController

    def do_GET(self):
        if urlsplit(self.path).path.startswith("/api/"):
            self._handle_api()
        else:
            self._serve_static()

    def do_POST(self):
        self._handle_api()

    def do_PUT(self):
        self._handle_api()

    def do_DELETE(self):
        self._handle_api()

    def _handle_api(self):
        parsed_url = urlsplit(self.path)
        payload = None

        if self.command in ("POST", "PUT"):
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                if content_length > 16_384:
                    self._send_json(413, {"error": "A solicitação excede o limite permitido."})
                    return
                if content_length < 0:
                    raise ValueError
                payload = json.loads(self.rfile.read(content_length))
            except (ValueError, json.JSONDecodeError):
                self._send_json(400, {"error": "Envie um corpo JSON válido."})
                return

        status, response = self.controller.handle(
            self.command, parsed_url.path, parsed_url.query, payload
        )
        self._send_json(status, response)

    def _serve_static(self):
        if self.command != "GET":
            self._send_json(405, {"error": "Método não permitido."})
            return

        requested_path = unquote(urlsplit(self.path).path)
        if requested_path == "/":
            requested_path = "/pagina-inicial.html"

        file_path = (STATIC_DIR / requested_path.lstrip("/")).resolve()
        if not file_path.is_relative_to(STATIC_DIR.resolve()) or not file_path.is_file():
            self.send_error(404)
            return

        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(file_path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, status, payload):
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(content)

    def _send_security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; base-uri 'none'; "
            "form-action 'self'; frame-ancestors 'none'",
        )

    def log_message(self, format_string, *args):
        logging.info("%s - %s", self.address_string(), format_string % args)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    database_path = Path(
        os.environ.get("BIBLIOTECA_DB_PATH", str(ROOT / "data" / "biblioteca.db"))
    )
    repository = BookRepository(database_path)
    handler = type(
        "ConfiguredLibraryHandler",
        (LibraryHandler,),
        {"controller": BookController(repository)},
    )

    host = os.environ.get("BIBLIOTECA_HOST", "127.0.0.1")
    port = int(os.environ.get("BIBLIOTECA_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), handler)
    logging.info("Biblioteca Virtual disponível em http://%s:%s", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Encerrando a Biblioteca Virtual.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
