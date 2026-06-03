from copado_hx._app import app, __version__
from copado_hx.utils.output import print_success


@app.command()
def version() -> None:
    """Show copado-hx version"""
    print_success(f"copado-hx version {__version__}")
