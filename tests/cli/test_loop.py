import httpx
import pytest

from tests.cli import interfaces
from tests.marks import skip_windows


@pytest.fixture()
def app_code() -> str:
    return """
    import asyncio

    from faststream.asgi import AsgiFastStream, AsgiResponse, get
    from faststream.asgi.types import Scope
    from faststream.nats import NatsBroker


    @get
    async def loop_handler(scope: Scope) -> AsgiResponse:
        loop = asyncio.get_event_loop()
        return AsgiResponse(
            body=f"{loop.__module__}:{loop.__class__.__name__}".encode(),
            status_code=200,
        )


    broker = NatsBroker()

    app = AsgiFastStream(
        broker,
        asgi_routes=[
            ("/loop", loop_handler),
        ],
    )
    """


@pytest.mark.slow()
@skip_windows
@pytest.mark.parametrize(
    ("loop_param", "expected_loop"),
    (
        pytest.param(
            "asyncio:new_event_loop",
            "asyncio.unix_events:_UnixSelectorEventLoop",
            id="asyncio",
        ),
        pytest.param(
            "uvloop:new_event_loop",
            "uvloop:Loop",
            id="uvloop",
        ),
    ),
)
def test_loop(
    loop_param: str,
    expected_loop: str,
    generate_template: interfaces.GenerateTemplateFactory,
    faststream_cli: interfaces.FastStreamCLIFactory,
    app_code: str,
) -> None:
    with (
        generate_template(app_code) as app_path,
        faststream_cli(
            "faststream",
            "run",
            "--loop",
            loop_param,
            f"{app_path.stem}:app",
        ),
    ):
        response = httpx.get("http://127.0.0.1:8000/loop")
        assert response.text == expected_loop
        assert response.status_code == 200


@pytest.mark.slow()
@skip_windows
def test_loop_not_found(
    generate_template: interfaces.GenerateTemplateFactory,
    faststream_cli: interfaces.FastStreamCLIFactory,
    app_code: str,
) -> None:
    with (
        generate_template(app_code) as app_path,
        faststream_cli(
            "faststream",
            "run",
            "--loop",
            "loop:not_found",
            f"{app_path.stem}:app",
        ) as cli,
    ):
        cli.signint()
        cli.wait(3.0)

    assert cli.process.returncode == -2
