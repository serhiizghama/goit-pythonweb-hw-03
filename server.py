from datetime import datetime
import mimetypes
import os
import pathlib
import json
from typing import Dict
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from jinja2 import Template

BASE_DIR = Path(__file__).resolve().parent

FILE_PATH = BASE_DIR / "storage" / "data.json"


class Http_Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                self.send_html("./templates/index.html")
            case "/read":
                self.show_messages()
            case "/message":
                self.send_html("./templates/message.html")
            case _:
                file = pathlib.Path().joinpath(route.path[1:])
                if file.exists():
                    self.send_static()
                else:
                    self.send_html("./templates/error.html", 404)

    def do_POST(self) -> None:
        size = self.headers.get("Content-Length")
        data = self.rfile.read(int(size)).decode("utf-8")
        parse_data = urllib.parse.unquote_plus(data)
        data_dict = {
            item.split("=")[0]: item.split("=")[1] for item in parse_data.split("&")
        }

        self.save_message(data_dict)

        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def send_html(self, filename: str, status_code: int = 200) -> None:
        self.send_response(status_code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as file:
            self.wfile.write(file.read())

    def send_static(self) -> None:
        self.send_response(200)
        mime_type, *_ = mimetypes.guess_type(self.path)
        if mime_type:
            self.send_header("Content-type", mime_type)
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())

    def save_message(self, data: Dict[str, str]) -> None:
        create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, "r", encoding="utf-8") as file:
                try:
                    existing_data = json.load(file)
                    if not isinstance(existing_data, dict):
                        existing_data = {}
                except json.JSONDecodeError:
                    existing_data = {}
        else:
            existing_data = {}

        existing_data[create_date] = data
        print("existing_data", existing_data)
        with open(FILE_PATH, "w", encoding="utf-8") as file:
            json.dump(existing_data, file, ensure_ascii=False, indent=4)

    def show_messages(self) -> None:
        try:
            with open(FILE_PATH, "r") as f:
                messages = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            messages = {}

        with open("./templates/read.html", "r") as f:
            template = Template(f.read())

        rendered_html = template.render(messages=messages)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(rendered_html.encode("utf-8"))


def run(http_server=HTTPServer, http_handler=Http_Handler, host="0.0.0.0", port=3000):
    server_address = (host, port)
    http = http_server(server_address, http_handler)
    print(f"Starting server on {host}:{port}...")

    try:
        http.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        http.server_close()


if __name__ == "__main__":
    run()
