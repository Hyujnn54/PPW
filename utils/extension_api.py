"""
PPW Local Extension API
=======================
A tiny HTTP server that runs on localhost:27227 while the desktop app is open.
The browser extension talks to this server to read vault data.

Security model:
  - Binds to 127.0.0.1 ONLY — never reachable from the network
  - Requires a per-session token in every request header (X-PPW-Token)
  - Token is generated fresh each time the vault is unlocked
  - Vault must be unlocked (master password entered) for any data endpoint
  - /api/ping is the only endpoint that works without a token
"""

import threading
import secrets
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from typing import Optional, Callable

from controllers.account_controller import AccountController

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

PORT = 27227
BIND = "127.0.0.1"      # localhost only — never expose to the network


class ExtensionAPIState:
    """Holds the live session for the extension API."""
    _user_id:        Optional[str] = None
    _master_password: Optional[str] = None
    _token:          Optional[str] = None
    _unlocked:       bool          = False
    _on_focus:       Optional[Callable] = None   # callback to bring GUI to front

    @classmethod
    def unlock(cls, user_id: str, master_password: str) -> str:
        """Called when the user successfully logs in to the desktop app."""
        cls._user_id        = user_id
        cls._master_password = master_password
        cls._token          = secrets.token_urlsafe(32)
        cls._unlocked       = True
        logger.info("Extension API: vault unlocked")
        return cls._token

    @classmethod
    def lock(cls):
        """Called on logout / session timeout."""
        cls._user_id        = None
        cls._master_password = None
        cls._token          = None
        cls._unlocked       = False
        logger.info("Extension API: vault locked")

    @classmethod
    def is_valid_token(cls, token: str) -> bool:
        return cls._unlocked and cls._token and secrets.compare_digest(
            cls._token, token)


state = ExtensionAPIState


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass   # suppress request noise in console

    # ── Routing ───────────────────────────────────────────────────
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/ping":
            return self._ping()

        if not self._auth():
            return

        if path == "/api/ext/accounts":
            return self._accounts()

        if path.startswith("/api/ext/accounts/"):
            acc_id = path.split("/")[-1]
            return self._account_detail(acc_id)

        self._json({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/ext/lock":
            if not self._auth():
                return
            state.lock()
            return self._json({"status": "locked"})

        if path == "/api/ext/focus":
            if not self._auth():
                return
            if state._on_focus:
                state._on_focus()
            return self._json({"status": "ok"})

        self._json({"error": "not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    # ── Handlers ──────────────────────────────────────────────────
    def _ping(self):
        self._json({
            "status":   "ok",
            "unlocked": state._unlocked,
            "token":    state._token if state._unlocked else None,
        })

    def _accounts(self):
        accounts = AccountController.get_accounts(state._user_id)
        self._json(accounts)

    def _account_detail(self, account_id: str):
        detail = AccountController.get_account_details(
            user_id=state._user_id,
            account_id=account_id,
            include_password=True,
            master_password=state._master_password,
        )
        if detail:
            self._json(detail)
        else:
            self._json({"error": "not found"}, 404)

    # ── Helpers ───────────────────────────────────────────────────
    def _auth(self) -> bool:
        token = self.headers.get("X-PPW-Token", "")
        if not state.is_valid_token(token):
            self._json({"error": "unauthorised — vault locked or invalid token"}, 401)
            return False
        return True

    def _json(self, data, status: int = 200):
        body = json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type",  "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        # Only allow the Chrome extension origin
        self.send_header("Access-Control-Allow-Origin",  "chrome-extension://")
        self.send_header("Access-Control-Allow-Headers", "X-PPW-Token, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")


# ── Server lifecycle ──────────────────────────────────────────────────────────

_server: Optional[HTTPServer] = None
_thread: Optional[threading.Thread] = None


def start():
    """Start the local API server in a daemon thread. Safe to call multiple times."""
    global _server, _thread
    if _server is not None:
        return

    try:
        _server = HTTPServer((BIND, PORT), Handler)
        _thread = threading.Thread(target=_server.serve_forever, daemon=True)
        _thread.start()
        logger.info(f"Extension API running on http://{BIND}:{PORT}")
    except OSError as e:
        logger.warning(f"Extension API failed to start (port busy?): {e}")


def stop():
    """Gracefully stop the server."""
    global _server
    if _server:
        _server.shutdown()
        _server = None
        logger.info("Extension API stopped")




