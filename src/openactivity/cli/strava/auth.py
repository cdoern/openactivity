"""Strava authentication commands."""

from __future__ import annotations

from datetime import UTC, datetime

import typer
from rich.console import Console

from openactivity.auth.keyring import (
    delete_all_credentials,
    has_client_credentials,
    has_tokens,
    store_client_credentials,
)
from openactivity.cli.root import get_global_state
from openactivity.output.errors import exit_with_error
from openactivity.output.json import print_json
from openactivity.providers.strava.oauth import run_oauth_flow

console = Console()

app = typer.Typer(
    name="auth",
    help=(
        "Authenticate with Strava via OAuth.\n\n"
        "Examples:\n\n"
        "  # First-time setup — prompts for API credentials and opens browser\n"
        "  openactivity strava auth\n\n"
        "  # Re-authorize (refresh OAuth tokens)\n"
        "  openactivity strava auth\n\n"
        "  # Remove all stored credentials\n"
        "  openactivity strava auth revoke\n\n"
        "Register your Strava API application at:\n"
        "  https://www.strava.com/settings/api\n"
        "Set the 'Authorization Callback Domain' to 'localhost'."
    ),
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def auth(ctx: typer.Context) -> None:
    """Authenticate with Strava via OAuth.

    On first run, prompts for your Strava API client ID and client secret,
    then opens a browser for OAuth authorization. Credentials are stored
    securely in your OS keychain.

    On subsequent runs, re-authorizes and refreshes OAuth tokens.

    Examples:
        openactivity strava auth
    """
    if ctx.invoked_subcommand is not None:
        return

    state = get_global_state()
    use_json = state.get("json", False)

    # Prompt for client credentials if not stored
    if not has_client_credentials():
        console.print(
            "\n[bold]Strava API Setup[/bold]\n"
            "\nTo use openactivity with Strava, you need to register a Strava API application.\n"
            "\n1. Go to [link=https://www.strava.com/settings/api]https://www.strava.com/settings/api[/link]"
            "\n2. Create an application (set Callback Domain to [bold]localhost[/bold])"
            "\n3. Copy your Client ID and Client Secret below\n"
        )
        client_id = typer.prompt("Client ID")
        client_secret = typer.prompt("Client Secret")

        if not client_id or not client_secret:
            exit_with_error(
                "invalid_credentials",
                "Client ID and Client Secret are required.",
                "Register your app at https://www.strava.com/settings/api",
                use_json=use_json,
            )

        store_client_credentials(client_id.strip(), client_secret.strip())
        console.print("\n[green]✓[/green] Client credentials stored in OS keychain.")

    # Run OAuth flow
    console.print("\n[bold]Opening browser for Strava authorization...[/bold]")
    console.print("If the browser doesn't open, copy and paste the URL shown above.\n")

    try:
        token_response = run_oauth_flow()
    except TimeoutError:
        exit_with_error(
            "oauth_timeout",
            "OAuth authorization timed out.",
            "Try again with 'openactivity strava auth'. Complete authorization in the browser.",
            use_json=use_json,
        )
    except Exception as e:
        exit_with_error(
            "oauth_error",
            f"OAuth authorization failed: {e}",
            "Check your client credentials and try again with 'openactivity strava auth'.",
            use_json=use_json,
        )

    athlete = token_response.get("athlete", {})
    athlete_id = athlete.get("id")
    firstname = athlete.get("firstname", "")
    lastname = athlete.get("lastname", "")
    expires_at = token_response.get("expires_at", 0)
    expires_dt = datetime.fromtimestamp(expires_at, tz=UTC)
    name = f"{firstname} {lastname}".strip() or "Unknown"

    if use_json:
        print_json(
            {
                "athlete_id": athlete_id,
                "name": name,
                "token_expires_at": expires_dt.isoformat(),
                "scopes": ["activity:read_all", "profile:read_all"],
            }
        )
    else:
        console.print(f"\n[green]✓[/green] Authenticated as [bold]{name}[/bold]")
        console.print(f"  Token expires: {expires_dt.isoformat()}")


@app.command()
def revoke() -> None:
    """Remove all stored Strava credentials from the OS keychain.

    This deletes your client ID, client secret, access token, and refresh token.
    You will need to re-run 'openactivity strava auth' to use Strava commands again.

    Examples:
        openactivity strava auth revoke
    """
    state = get_global_state()
    use_json = state.get("json", False)

    if not has_client_credentials() and not has_tokens():
        if use_json:
            print_json({"status": "no_credentials", "message": "No stored credentials found."})
        else:
            console.print("No stored credentials found.")
        return

    delete_all_credentials()

    if use_json:
        print_json({"status": "revoked", "message": "All Strava credentials removed."})
    else:
        console.print("[green]✓[/green] All Strava credentials removed from OS keychain.")
