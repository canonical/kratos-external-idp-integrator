# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import json
from textwrap import dedent
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
        "label": "Some Provider",
        "issuer_url": "http://example.com",
        "secret_backend": "relation",
        "scope": "profile email address phone",
    }


@pytest.fixture
def generic_databag(config: Dict) -> Dict:
    return {
        "providers": [
            {
                "client_id": config["client_id"],
                "provider": config["provider"],
                "label": config["label"],
                "secret_backend": config["secret_backend"],
                "client_secret": config["client_secret"],
                "issuer_url": config["issuer_url"],
                "scope": config["scope"],
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
        "label": config["label"],
        "client_secret": config["client_secret"],
        "issuer_url": config["issuer_url"],
        "scope": config["scope"].split(" "),
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
def github_config() -> Dict:
    return {
        "client_id": "client_id",
        "client_secret": "client_secret",
        "provider": "github",
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


@pytest.fixture
def jsonnet() -> str:
    return dedent(
        """
        local claims = {
            email_verified: false,
        } + std.extVar('claims');

        {
            identity: {
                traits: {
                    [if 'email' in claims && claims.email_verified then 'email' else null]: claims.email,
                    [if 'name' in claims then 'name' else null]: claims.name,
                    [if 'given_name' in claims then 'given_name' else null]: claims.given_name,
                    [if 'family_name' in claims then 'family_name' else null]: claims.family_name,
                },
            },
        }"""
    )
