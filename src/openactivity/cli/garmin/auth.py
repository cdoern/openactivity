"""Garmin authentication CLI command."""

from __future__ import annotations

import typer
from rich.console import Console

from openactivity.auth import keyring
from openactivity.providers.garmin import auth

console = Console()


def garmin_auth(
    status: bool = typer.Option(False, "--status", help="Show authentication status"),
) -> None:
    """Authenticate with Garmin Connect.

    Interactive authentication that prompts for username and password,
    then stores credentials securely in the system keyring.
    """
    # Check status only
    if status:
        if auth.is_authenticated():
            username, _ = keyring.get_garmin_credentials()
            console.print("[green]Garmin Connect: Authenticated[/green]")
            console.print(f"Username: {username}")
        else:
            console.print("[yellow]Garmin Connect: Not authenticated[/yellow]")
        return

    # Interactive authentication
    console.print("[bold]Garmin Connect Authentication[/bold]\n")

    # Check if already authenticated
    if auth.is_authenticated():
        username, _ = keyring.get_garmin_credentials()
        console.print(f"[yellow]Warning: Garmin credentials already stored[/yellow]")
        console.print(f"Current username: {username}")
        overwrite = typer.confirm("Overwrite existing credentials?")
        if not overwrite:
            console.print("Authentication cancelled")
            return

    # Prompt for credentials
    username = typer.prompt("Username")
    password = typer.prompt("Password", hide_input=True)

    console.print("\nAuthenticating with Garmin Connect...")

    # Attempt authentication
    if auth.authenticate(username, password):
        console.print("[green]✓ Authentication successful[/green]")
        console.print("Credentials stored securely in system keyring")
        console.print(
            "\n[dim]Note: Two-factor authentication (MFA) is not fully supported.[/dim]"
        )
        console.print(
            "[dim]If you have MFA enabled, you may need to use an app-specific password."
            "[/dim]"
        )
    else:
        console.print("[red]Error: Authentication failed[/red]")
        console.print("Invalid username or password. Please try again.")
        raise typer.Exit(1)
