"""Garmin authentication CLI command with MFA support."""

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

    Supports two-factor authentication (MFA). You will be prompted for your
    MFA code if you have it enabled on your Garmin account.

    Authentication tokens are saved and reused, so you only need to
    authenticate once (unless tokens expire).
    """
    # Check status only
    if status:
        if auth.is_authenticated():
            username, _ = keyring.get_garmin_credentials()
            console.print("[green]✓ Garmin Connect: Authenticated[/green]")
            if username and username != "TOKEN_BASED_AUTH":
                console.print(f"Username: {username}")
            console.print("\n[dim]Using saved OAuth tokens (supports MFA)[/dim]")
        else:
            console.print("[yellow]Garmin Connect: Not authenticated[/yellow]")
            console.print("Run 'openactivity garmin auth' to authenticate.")
        return

    # Interactive authentication
    console.print("[bold]Garmin Connect Authentication[/bold]")
    console.print("[dim]Supports MFA - you'll be prompted for your code if enabled[/dim]\n")

    # Check if already authenticated
    if auth.is_authenticated():
        console.print("[yellow]⚠ You are already authenticated[/yellow]")
        overwrite = typer.confirm("Re-authenticate anyway?")
        if not overwrite:
            console.print("Authentication cancelled")
            return
        console.print()

    # Prompt for credentials
    username = typer.prompt("Garmin email")
    password = typer.prompt("Password", hide_input=True)

    console.print("\n[bold]Authenticating with Garmin Connect...[/bold]")
    console.print("[dim]If you have MFA enabled, you'll be prompted for your code...[/dim]\n")

    # Attempt authentication (garth will handle MFA prompt)
    success, error = auth.authenticate(username, password)

    if success:
        console.print("\n[green]✓ Authentication successful![/green]")
        console.print("OAuth tokens saved - you won't need to re-authenticate for weeks/months")
        console.print("\n[dim]Tokens are stored in: ~/.local/share/openactivity/garmin/[/dim]")
    else:
        console.print("\n[red]✗ Authentication failed[/red]")

        # Provide specific error messages
        if error == "rate_limit":
            console.print("\n[yellow]⚠ Rate Limit Exceeded[/yellow]")
            console.print(
                "Garmin is temporarily blocking login attempts from your IP address."
            )
            console.print("\n[bold]What to do:[/bold]")
            console.print("  1. Wait 15-30 minutes before trying again")
            console.print("  2. Ensure your username and password are correct")
            console.print(
                "  3. Try logging into https://connect.garmin.com in a browser first"
            )
        elif error == "invalid_credentials":
            console.print("\n[bold]Invalid username or password[/bold]")
            console.print("Double-check your Garmin Connect credentials.")
        elif error == "mfa_required":
            console.print("\n[bold]MFA code required but not provided[/bold]")
            console.print("The authentication library should have prompted for your MFA code.")
            console.print("If you didn't see a prompt, please report this issue.")
        else:
            console.print(f"\n[bold]Error details:[/bold] {error}")

        raise typer.Exit(1)
