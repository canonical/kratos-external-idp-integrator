# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import json
from typing import Dict, Generator
from unittest.mock import MagicMock

import pytest
from ops.testing import Harness

from charm import KratosIdpIntegratorCharm


@pytest.fixture
def config() -> Dict:
    return {
        "client_id": "client_id",
        "client_secret": "client_secret",
        "provider": "generic",
        "issuer_url": "http://example.com",
        "secret_backend": "relation",
    }


@pytest.fixture
def generic_databag(config: Dict) -> Dict:
    return {
        "providers": [
            {
                "client_id": config["client_id"],
                "provider": config["provider"],
                "secret_backend": config["secret_backend"],
                "client_secret": config["client_secret"],
                "issuer_url": config["issuer_url"],
            }
        ]
    }


@pytest.fixture
def relation_data() -> Dict:
    return {
        "providers": json.dumps(
            [
                {
                    "redirect_uri": "https://example.com/callback",
                    "provider_id": "provider",
                }
            ]
        )
    }


@pytest.fixture
def generic_kratos_config(config: Dict) -> Dict:
    return {
        "id": "generic_c1b858ba120b6a62d17865256fab2617b727ab27",
        "client_id": config["client_id"],
        "provider": config["provider"],
        "client_secret": config["client_secret"],
        "issuer_url": config["issuer_url"],
    }


@pytest.fixture
def microsoft_config() -> Dict:
    return {
        "client_id": "client_id",
        "client_secret": "client_secret",
        "provider": "microsoft",
        "microsoft_tenant_id": "some-tenant-id",
        "secret_backend": "relation",
    }


@pytest.fixture
def apple_config() -> Dict:
    return {
        "client_id": "client_id",
        "provider": "apple",
        "secret_backend": "relation",
        "apple_team_id": "apple_team_id",
        "apple_private_key_id": "apple_private_key_id",
        "apple_private_key": "apple_private_key",
    }


@pytest.fixture
def invalid_provider_config() -> Dict:
    return {
        "client_id": "client_id",
        "client_secret": "client_secret",
        "provider": "go0gle",
        "secret_backend": "relation",
    }


@pytest.fixture
def mock_event() -> MagicMock:
    event = MagicMock()
    event.set_results = MagicMock()
    return event


@pytest.fixture
def harness() -> Generator[Harness, None, None]:
    harness = Harness(KratosIdpIntegratorCharm)
    harness.set_leader(True)
    harness.begin_with_initial_hooks()
    yield harness
    harness.cleanup()
