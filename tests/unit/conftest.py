# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

from unittest.mock import MagicMock

import pytest
from ops.testing import Harness

from charm import KratosIdpIntegratorCharm


@pytest.fixture
def config():
    return {
        "client_id": "client_id",
        "client_secret": "client_secret",
        "provider": "generic",
        "issuer_url": "http://example.com",
        "secret_backend": "plain",
    }


@pytest.fixture
def generic_databag(config):
    return {
        "client_id": config["client_id"],
        "provider": config["provider"],
        "secret_backend": config["secret_backend"],
        config["provider"]: {
            "client_secret": config["client_secret"],
            "issuer_url": config["issuer_url"],
        },
    }


@pytest.fixture
def microsoft_config():
    return {
        "client_id": "client_id",
        "client_secret": "client_secret",
        "provider": "microsoft",
        "microsoft_tenant_id": "some-tenant-id",
        "secret_backend": "plain",
    }


@pytest.fixture
def apple_config():
    return {
        "client_id": "client_id",
        "provider": "apple",
        "secret_backend": "plain",
        "apple_team_id": "apple_team_id",
        "apple_private_key_id": "apple_private_key_id",
        "apple_private_key": "apple_private_key",
    }


@pytest.fixture
def invalid_provider_config():
    return {
        "client_id": "client_id",
        "client_secret": "client_secret",
        "provider": "go0gle",
        "secret_backend": "plain",
    }


@pytest.fixture
def mock_event():
    event = MagicMock()
    event.set_results = MagicMock()
    return event


@pytest.fixture
def relation_data():
    return {
        "redirect_uri": "https://example.com/callback",
        "provider_id": "provider",
    }


@pytest.fixture
def harness():
    harness = Harness(KratosIdpIntegratorCharm)
    harness.set_leader(True)
    harness.begin_with_initial_hooks()
    yield harness
    harness.cleanup()