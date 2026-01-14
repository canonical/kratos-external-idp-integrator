# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

import os
import secrets
import subprocess
from contextlib import suppress
from pathlib import Path
from typing import Generator

import jubilant
import pytest
from integration.utils import juju_model_factory


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command-line options for model management and deployment control."""
    parser.addoption(
        "--keep-models",
        "--no-teardown",
        action="store_true",
        dest="no_teardown",
        default=False,
        help="Keep the model after the test is finished.",
    )
    parser.addoption(
        "--model",
        action="store",
        dest="model",
        default=None,
        help="The model to run the tests on.",
    )
    parser.addoption(
        "--no-deploy",
        "--no-setup",
        action="store_true",
        dest="no_setup",
        default=False,
        help="Skip deployment of the charm.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers for test selection based on deployment and model management."""
    config.addinivalue_line("markers", "setup: tests that setup some parts of the environment")
    config.addinivalue_line(
        "markers", "teardown: tests that teardown some parts of the environment."
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Modify collected test items based on command-line options."""
    skip_setup = pytest.mark.skip(reason="no_setup provided")
    skip_teardown = pytest.mark.skip(reason="no_teardown provided")
    for item in items:
        if config.getoption("no_setup") and "setup" in item.keywords:
            item.add_marker(skip_setup)
        if config.getoption("no_teardown") and "teardown" in item.keywords:
            item.add_marker(skip_teardown)


@pytest.fixture(scope="module")
def juju(request: pytest.FixtureRequest) -> Generator[jubilant.Juju, None, None]:
    """Create a temporary Juju model for integration tests."""
    model_name = request.config.getoption("--model")
    if not model_name:
        model_name = f"test-kratos-integrator-{secrets.token_hex(4)}"

    juju_ = juju_model_factory(model_name)
    juju_.wait_timeout = 10 * 60

    try:
        yield juju_
    finally:
        breakpoint()
        if request.session.testsfailed:
            log = juju_.debug_log(limit=1000)
            print(log, end="")

        no_teardown = bool(request.config.getoption("--no-teardown"))
        keep_model = no_teardown or request.session.testsfailed > 0
        if not keep_model:
            with suppress(jubilant.CLIError):
                args = [
                    "destroy-model",
                    model_name,
                    "--no-prompt",
                    "--destroy-storage",
                    "--force",
                    "--timeout",
                    "600s",
                ]
                juju_.cli(*args, include_model=False)


@pytest.fixture(scope="session")
def local_charm() -> Path:
    """Get the path to the charm-under-test."""
    # in GitHub CI, charms are built with charmcraftcache and uploaded to $CHARM_PATH
    charm: str | Path | None = os.getenv("CHARM_PATH")
    if not charm:
        # fall back to build locally - required when run outside of GitHub CI
        subprocess.run(["charmcraft", "pack"], check=True)
        if not (charms := list(Path(".").glob("*.charm"))):
            raise RuntimeError("Charm not found and build failed")
        charm = charms[0].absolute()
    return Path(charm)


@pytest.fixture
def config() -> dict:
    return {
        "client_id": "client_id",
        "client_secret": "client_secret",
        "provider": "generic",
        "issuer_url": "http://example.com",
    }
