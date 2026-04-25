"""Garmin Connect login — store credentials and authenticate."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.prompt import Prompt

from openactivity.auth.keyring import (
    has_garmin_credentials,
    store_garmin_credentials,
)

console = Console()

# Token cache — same path used by sync_cmd.
_TOKEN_STORE = "~/.garminconnect"


def garmin_login() -> None:
    """Log in to Garmin Connect.

    Prompts for email and password, stores them in the OS keychain,
    then authenticates with Garmin Connect to cache tokens. Supports
    MFA if your account requires it.

    Tokens are saved to ~/.garminconnect and auto-refresh on future
    sync calls — you only need to log in once.

    Examples:
        openactivity garmin login
    """
    from openactivity.auth.keyring import get_garmin_credentials

    if has_garmin_credentials():
        overwrite = Prompt.ask(
            "Garmin credentials already stored. Overwrite?",
            choices=["y", "n"],
            default="n",
        )
        if overwrite == "y":
            email = Prompt.ask("Garmin Connect email")
            password = Prompt.ask("Garmin Connect password", password=True)
            if not email or not password:
                console.print("[red]Email and password are required.[/red]")
                raise typer.Exit(code=1)
            store_garmin_credentials(email, password)
            console.print("[green]Credentials updated.[/green]")
        else:
            email, password = get_garmin_credentials()
    else:
        email = Prompt.ask("Garmin Connect email")
        password = Prompt.ask("Garmin Connect password", password=True)
        if not email or not password:
            console.print("[red]Email and password are required.[/red]")
            raise typer.Exit(code=1)
        store_garmin_credentials(email, password)
        console.print("[green]Credentials saved to OS keychain.[/green]")

    # Authenticate and cache tokens
    console.print("[dim]Authenticating with Garmin Connect...[/dim]")
    try:
        from garminconnect import Garmin

        client = Garmin(
            email,
            password,
            prompt_mfa=lambda: input("Enter MFA code: "),
        )
        client.login(_TOKEN_STORE)
    except Exception as exc:
        console.print(f"[yellow]Authentication failed:[/yellow] {exc}")
        console.print(
            "Credentials are saved — you can retry with "
            "'openactivity garmin sync' later when rate limits clear."
        )
        return

    console.print("[green]Logged in successfully. Tokens cached at ~/.garminconnect[/green]")
    console.print("Run 'openactivity garmin sync' to pull health data.")
