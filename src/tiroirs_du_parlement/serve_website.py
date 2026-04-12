import shutil
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from tiroirs_du_parlement.config import IS_CI_ENV, OUTPUT_PATH, SERVER_PORT, WEB_PATH


class _HTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, directory=WEB_PATH, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def serve_website():
    if IS_CI_ENV:
        raise RuntimeError("Serving the website is not supported in CI environments.")
    if not OUTPUT_PATH.is_file():
        raise FileNotFoundError(
            f"You must generate the `{OUTPUT_PATH}` file before serving the website."
        )

    shutil.copy(OUTPUT_PATH, WEB_PATH / OUTPUT_PATH.name)

    with ThreadingHTTPServer(("localhost", SERVER_PORT), _HTTPRequestHandler) as httpd:
        print(
            f"Serving the website at http://{httpd.server_address[0]}:{httpd.server_address[1]}/"
        )
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.shutdown()


if __name__ == "__main__":
    serve_website()
