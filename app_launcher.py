"""Windows launcher for the OpenSeismo desktop executable."""

from __future__ import annotations

import logging
import signal
import socket
import threading
import time
import webbrowser

import flask.cli as flask_cli

from openseismo.app import create_app


browser_opened = False
browser_open_lock = threading.Lock()


def suppress_logs(app):
    """Keep Flask/Werkzeug output quiet for desktop use."""
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    logging.getLogger("werkzeug").disabled = True
    logging.getLogger("werkzeug").propagate = False
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    app.logger.disabled = True
    flask_cli.show_server_banner = lambda *args, **kwargs: None


def wait_for_server(host, port, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.25):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def open_browser_once():
    global browser_opened

    with browser_open_lock:
        if browser_opened:
            return
        browser_opened = True

    webbrowser.open("http://127.0.0.1:5000", new=1, autoraise=True)


def run_flask(app):
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


def run():
    app = create_app()
    suppress_logs(app)

    server_thread = threading.Thread(target=run_flask, args=(app,), daemon=True)
    server_thread.start()

    if wait_for_server("127.0.0.1", 5000):
        open_browser_once()

    stop_event = threading.Event()

    def stop(*_args):
        stop_event.set()

    try:
        signal.signal(signal.SIGINT, stop)
        signal.signal(signal.SIGTERM, stop)
    except ValueError:
        pass

    try:
        while not stop_event.is_set() and server_thread.is_alive():
            server_thread.join(timeout=0.5)
    finally:
        stop_event.set()


if __name__ == "__main__":
    run()