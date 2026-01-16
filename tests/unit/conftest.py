# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import dataclasses
import json
from textwrap import dedent
from typing import Any
from unittest.mock import MagicMock

import pytest
from ops.testing import Context, Relation, State

from charm import KRATOS_EXTERNAL_IDP_INTEGRATION_NAME, KratosIdpIntegratorCharm


@pytest.fixture
def kratos_relation() -> Relation:
    return Relation(KRATOS_EXTERNAL_IDP_INTEGRATION_NAME, remote_app_name="kratos")


@pytest.fixture
def kratos_relation_with_data(
    kratos_relation: Relation, relation_data: dict[str, Any]
) -> Relation:
    return dataclasses.replace(kratos_relation, remote_app_data=relation_data)


@pytest.fixture
def config() -> dict[str, Any]:
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
def generic_databag(config: dict[str, Any]) -> dict[str, Any]:
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
def generic_databag_v1(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "providers": [
            {
                "client_id": config["client_id"],
                "provider": config["provider"],
                "label": config["label"],
                "client_secret": config["client_secret"],
                "issuer_url": config["issuer_url"],
                "scope": config["scope"],
                "id": "generic_c1b858ba120b6a62d17865256fab2617b727ab27",
                "jsonnet_mapper": None,
                "mapper_url": None,
            }
        ]
    }


@pytest.fixture
def relation_data() -> dict[str, Any]:
    return {
        "providers": json.dumps([
            {
                "redirect_uri": "https://example.com/callback",
                "provider_id": "provider",
            }
        ])
    }


@pytest.fixture
def generic_kratos_config(config: dict[str, Any]) -> dict[str, Any]:
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
def microsoft_config() -> dict[str, Any]:
    return {
        "client_id": "client_id",
        "client_secret": "client_secret",
        "provider": "microsoft",
        "microsoft_tenant_id": "some-tenant-id",
        "secret_backend": "relation",
    }


@pytest.fixture
def github_config() -> dict[str, Any]:
    return {
        "client_id": "client_id",
        "client_secret": "client_secret",
        "provider": "github",
        "secret_backend": "relation",
    }


@pytest.fixture
def apple_config() -> dict[str, Any]:
    return {
        "client_id": "client_id",
        "provider": "apple",
        "secret_backend": "relation",
        "apple_team_id": "apple_team_id",
        "apple_private_key_id": "apple_private_key_id",
        "apple_private_key": "apple_private_key",
    }


@pytest.fixture
def invalid_provider_config() -> dict[str, Any]:
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
def context() -> Context:
    return Context(KratosIdpIntegratorCharm)


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


def create_state(
    config: dict[str, Any], relations: list[Relation] | None = None, leader: bool = True
) -> State:
    return State(config=config, relations=relations or [], leader=leader)
