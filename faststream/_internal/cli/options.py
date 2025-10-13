import typer

from faststream._internal.cli.utils.imports import import_from_string


def check_loop(value: str) -> str:
    if value != "auto":
        import_from_string(value)
    return value


FACTORY_OPTION = typer.Option(
    False,
    "-f",
    "--factory",
    help="Treat APP as an application factory.",
)

RELOAD_FLAG = typer.Option(
    False,
    "-r",
    "--reload",
    is_flag=True,
    help="Restart app at directory files changes.",
)

APP_DIR_OPTION = typer.Option(
    ".",
    "--app-dir",
    help=("Look for APP in the specified directory, by adding this to the PYTHONPATH."),
    envvar="FASTSTREAM_APP_DIR",
)

RELOAD_EXTENSIONS_OPTION = typer.Option(
    (),
    "--extension",
    "--ext",
    "--reload-extension",
    "--reload-ext",
    help="List of file extensions to watch by.",
)

LOOP_OPTION = typer.Option(
    "auto",
    "--loop",
    callback=check_loop,
    help=("Event loop factory implementation."),
    envvar="FASTSTREAM_LOOP",
)

APP_ARGUMENT = typer.Argument(
    ...,
    help="[python_module:FastStream] - path to your application.",
    show_default=False,
)
