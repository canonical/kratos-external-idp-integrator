# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import json
from typing import Dict
from unittest.mock import MagicMock

import pytest
from ops.model import ActiveStatus, BlockedStatus, WaitingStatus
from ops.testing import Harness
from utils import parse_databag  # type: ignore


def test_relation(
    harness: Harness, config: Dict, relation_data: Dict, generic_databag: Dict
) -> None:
    harness.update_config(config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos")
    harness.add_relation_unit(relation_id, "kratos/0")

    unit_data = harness.get_relation_data(relation_id, harness.charm.unit)
    app_data = harness.get_relation_data(relation_id, harness.charm.app)

    assert isinstance(harness.charm.unit.status, WaitingStatus)
    assert unit_data == {}
    assert parse_databag(app_data) == generic_databag

    harness.update_relation_data(relation_id, "kratos", relation_data)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)

    assert isinstance(harness.charm.unit.status, ActiveStatus)
    assert parse_databag(app_data) == generic_databag


def test_provider_id_config(
    harness: Harness, config: Dict, relation_data: Dict, generic_databag: Dict
) -> None:
    harness.update_config(dict(provider_id="id", **config))
    generic_databag["providers"][0]["provider_id"] = "id"
    relation_id = harness.add_relation("kratos-external-idp", "kratos")
    harness.add_relation_unit(relation_id, "kratos/0")

    unit_data = harness.get_relation_data(relation_id, harness.charm.unit)
    app_data = harness.get_relation_data(relation_id, harness.charm.app)

    assert unit_data == {}
    assert parse_databag(app_data) == generic_databag


def test_jsonnet_config(
    harness: Harness, config: Dict, relation_data: Dict, generic_databag: Dict, jsonnet: str
) -> None:
    harness.update_config(dict(jsonnet=jsonnet, **config))
    generic_databag["providers"][0]["jsonnet"] = jsonnet
    relation_id = harness.add_relation("kratos-external-idp", "kratos")
    harness.add_relation_unit(relation_id, "kratos/0")

    unit_data = harness.get_relation_data(relation_id, harness.charm.unit)
    app_data = harness.get_relation_data(relation_id, harness.charm.app)

    assert unit_data == {}
    assert parse_databag(app_data) == generic_databag


def test_extra_config(
    harness: Harness,
    config: Dict,
    relation_data: Dict,
    generic_databag: Dict,
    caplog: pytest.LogCaptureFixture,
) -> None:
    config["microsoft_tenant_id"] = "4242424242"

    harness.update_config(config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos")
    harness.add_relation_unit(relation_id, "kratos/0")
    harness.update_relation_data(relation_id, "kratos", relation_data)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)

    assert isinstance(harness.charm.unit.status, ActiveStatus)
    assert (
        caplog.records[0].message
        == "Invalid config 'microsoft_tenant_id' for provider 'generic' will be ignored"
    )
    assert parse_databag(app_data) == generic_databag


def test_config_no_relation(harness: Harness, config: Dict) -> None:
    harness.update_config(config)
    assert isinstance(harness.charm.unit.status, BlockedStatus)


def test_invalid_config(
    harness: Harness,
    invalid_provider_config: Dict,
    config: Dict,
    generic_databag: Dict,
    relation_data: Dict,
) -> None:
    harness.update_config(invalid_provider_config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos-app")

    unit_data = harness.get_relation_data(relation_id, harness.charm.unit)
    app_data = harness.get_relation_data(relation_id, harness.charm.app)
    assert isinstance(harness.charm.unit.status, BlockedStatus)
    assert unit_data == {}
    assert app_data == {}

    harness.update_config(config)
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)

    assert isinstance(harness.charm.unit.status, ActiveStatus)
    assert parse_databag(app_data) == generic_databag


def test_invalid_provider(harness: Harness, config: Dict) -> None:
    config["provider"] = "error"
    harness.update_config(config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos-app")
    # harness.update_relation_data(relation_id, "kratos-app", relation_data)

    unit_data = harness.get_relation_data(relation_id, harness.charm.unit)
    app_data = harness.get_relation_data(relation_id, harness.charm.app)
    assert isinstance(harness.charm.unit.status, BlockedStatus)
    assert unit_data == {}
    assert app_data == {}


def test_microsoft_config(harness: Harness, microsoft_config: Dict, relation_data: Dict) -> None:
    expected_databag = {
        "providers": [
            {
                "client_id": microsoft_config["client_id"],
                "provider": microsoft_config["provider"],
                "secret_backend": microsoft_config["secret_backend"],
                "tenant_id": microsoft_config["microsoft_tenant_id"],
                "client_secret": microsoft_config["client_secret"],
                "scope": "profile email address phone",
            }
        ]
    }

    harness.update_config(microsoft_config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos")
    harness.add_relation_unit(relation_id, "kratos/0")
    harness.update_relation_data(relation_id, "kratos", relation_data)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)

    assert isinstance(harness.charm.unit.status, ActiveStatus)
    assert parse_databag(app_data) == expected_databag


def test_microsoft_invalid_config(harness: Harness, config: Dict, relation_data: Dict) -> None:
    config["provider"] = "microsoft"
    harness.update_config(config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)
    assert isinstance(harness.charm.unit.status, BlockedStatus)
    assert app_data == {}


def test_apple_config(harness: Harness, apple_config: Dict, relation_data: Dict) -> None:
    expected_databag = {
        "providers": [
            {
                "client_id": "client_id",
                "provider": "apple",
                "secret_backend": "relation",
                "team_id": "apple_team_id",
                "private_key_id": "apple_private_key_id",
                "private_key": "apple_private_key",
                "scope": "profile email address phone",
            }
        ]
    }

    harness.update_config(apple_config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos")
    harness.add_relation_unit(relation_id, "kratos/0")
    harness.update_relation_data(relation_id, "kratos", relation_data)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)

    assert isinstance(harness.charm.unit.status, ActiveStatus)
    assert parse_databag(app_data) == expected_databag


def test_apple_invalid_config(harness: Harness, config: Dict, relation_data: Dict) -> None:
    config["provider"] = "apple"
    harness.update_config(config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)
    assert isinstance(harness.charm.unit.status, BlockedStatus)
    assert app_data == {}


def test_get_redirect_uri(
    harness: Harness, config: Dict, mock_event: MagicMock, relation_data: Dict
) -> None:
    redirect_uri = json.loads(relation_data["providers"])[0]["redirect_uri"]

    harness.update_config(config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    harness.charm._get_redirect_uri(mock_event)

    mock_event.set_results.assert_called_once()
    assert isinstance(harness.charm.unit.status, ActiveStatus)
    assert mock_event.set_results.mock_calls[0].args == ({"redirect-uri": redirect_uri},)


def test_get_no_redirect_uri(harness: Harness, config: Dict, mock_event: MagicMock) -> None:
    harness.update_config(config)

    harness.charm._get_redirect_uri(mock_event)

    mock_event.fail.assert_called_once_with("No redirect_uri found")


def test_disable(
    harness: Harness,
    config: Dict,
    generic_databag: Dict,
    relation_data: Dict,
    mock_event: MagicMock,
) -> None:
    harness.update_config(config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    harness.charm._disable(mock_event)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)
    assert isinstance(harness.charm.unit.status, ActiveStatus)
    assert app_data == {}

    harness.charm._enable(mock_event)

    assert isinstance(harness.charm.unit.status, ActiveStatus)
    assert parse_databag(app_data) == generic_databag
