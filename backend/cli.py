"""CLI for Jakebot Dashboard"""
import click
import uvicorn


@click.group()
def cli():
    """Jakebot Labs Dashboard"""
    pass


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=7842, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def start(host, port, reload):
    """Start the dashboard server"""
    click.echo(f"🚀 Starting Jakebot Labs Dashboard on {host}:{port}")
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    cli()
