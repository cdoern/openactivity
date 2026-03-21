"""Strava OAuth2 flow implementation."""

from __future__ import annotations

import http.server
import os
import threading
import time
import webbrowser
from urllib.parse import parse_qs, urlparse

# Silence stravalib warnings about missing env vars — we use keyring instead
os.environ.setdefault("SILENCE_TOKEN_WARNINGS", "true")

from stravalib import Client  # noqa: E402

from openactivity.auth.keyring import (
    get_client_credentials,
    get_tokens,
    store_tokens,
)

REDIRECT_PORT = 8339
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"
SCOPES = ["activity:read_all", "profile:read_all"]


class _OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that captures the OAuth callback code."""

    authorization_code: str | None = None

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/callback":
            params = parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            if code:
                _OAuthCallbackHandler.authorization_code = code
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h2>Authorization successful!</h2>"
                    b"<p>You can close this window and return to the terminal.</p>"
                    b"</body></html>"
                )
            else:
                error = params.get("error", ["unknown"])[0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    f"<html><body><h2>Authorization failed: {error}</h2></body></html>".encode()
                )
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        # Suppress default HTTP server logging
        pass


def get_authorization_url() -> str:
    """Build the Strava OAuth authorization URL."""
    client_id, _ = get_client_credentials()
    if not client_id:
        msg = "No client ID found. Run 'openactivity strava auth' first."
        raise RuntimeError(msg)

    client = Client()
    return client.authorization_url(
        client_id=int(client_id),
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
    )


def run_oauth_flow() -> dict:
    """Run the full OAuth2 authorization flow.

    Opens the browser for authorization, listens for the callback,
    exchanges the code for tokens, and stores them.

    Returns:
        Dict with athlete info from the token exchange response.
    """
    client_id, client_secret = get_client_credentials()
    if not client_id or not client_secret:
        msg = "Client credentials not configured. Run 'openactivity strava auth' first."
        raise RuntimeError(msg)

    # Reset any previous code
    _OAuthCallbackHandler.authorization_code = None

    # Start local server for callback
    server = http.server.HTTPServer(("localhost", REDIRECT_PORT), _OAuthCallbackHandler)
    server_thread = threading.Thread(target=server.handle_request, daemon=True)
    server_thread.start()

    # Open browser for authorization
    auth_url = get_authorization_url()
    webbrowser.open(auth_url)

    # Wait for callback (up to 120 seconds)
    deadline = time.monotonic() + 120
    while _OAuthCallbackHandler.authorization_code is None:
        if time.monotonic() > deadline:
            server.server_close()
            msg = "OAuth authorization timed out after 120 seconds."
            raise TimeoutError(msg)
        time.sleep(0.1)

    server.server_close()

    code = _OAuthCallbackHandler.authorization_code

    # Exchange code for tokens (return_athlete=True gives us a tuple)
    client = Client()
    token_info, athlete = client.exchange_code_for_token(
        client_id=int(client_id),
        client_secret=client_secret,
        code=code,
        return_athlete=True,
    )

    # Store tokens
    store_tokens(
        access_token=token_info["access_token"],
        refresh_token=token_info["refresh_token"],
        expires_at=token_info["expires_at"],
    )

    # Build result with token info + athlete data
    result = dict(token_info)
    if athlete:
        result["athlete"] = {
            "id": athlete.id,
            "firstname": athlete.firstname or "",
            "lastname": athlete.lastname or "",
        }

    return result


def refresh_access_token() -> dict:
    """Refresh the access token using the stored refresh token.

    Returns:
        Dict with new token info.
    """
    client_id, client_secret = get_client_credentials()
    _, refresh_token, _ = get_tokens()

    if not client_id or not client_secret or not refresh_token:
        msg = "Missing credentials for token refresh. Run 'openactivity strava auth'."
        raise RuntimeError(msg)

    client = Client()
    token_response = client.refresh_access_token(
        client_id=int(client_id),
        client_secret=client_secret,
        refresh_token=refresh_token,
    )

    store_tokens(
        access_token=token_response["access_token"],
        refresh_token=token_response["refresh_token"],
        expires_at=token_response["expires_at"],
    )

    return token_response


def is_token_expired() -> bool:
    """Check if the stored access token is expired."""
    _, _, expires_at = get_tokens()
    if expires_at is None:
        return True
    return time.time() >= expires_at
