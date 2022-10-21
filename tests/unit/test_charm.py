# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

from unittest.mock import MagicMock

import ops
import pytest
from ops.testing import Harness
from ops.model import ActiveStatus, BlockedStatus, WaitingStatus

from charm import KratosIdpIntegratorCharm

ops.testing.SIMULATE_CAN_CONNECT = True


@pytest.fixture
def config():
    return {
        "client_id": "client_id",
        "client_secret": "client_secret",
        "provider": "generic",
        "issuer_url": "http://example.com",
    }


@pytest.fixture
def microsoft_config():
    return {
        "client_id": "client_id",
        "client_secret": "client_secret",
        "provider": "microsoft",
        "microsoft_tenant_id": "some-tenant-id",
    }


@pytest.fixture
def apple_config():
    return {
        "client_id": "client_id",
        "client_secret": "client_secret",
        "provider": "apple",
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
    }


@pytest.fixture
def mock_event():
    event = MagicMock()
    event.set_results = MagicMock()
    return event


@pytest.fixture
def relation_data():
    return {"redirect_uri": "https://example.com/callback"}


@pytest.fixture
def harness():
    harness = Harness(KratosIdpIntegratorCharm)
    harness.set_leader(True)
    harness.begin_with_initial_hooks()
    yield harness
    harness.cleanup()


def test_relation(harness, config, relation_data):
    harness.update_config(config)
    relation_id = harness.add_relation("provider-endpoint", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    unit_data = harness.get_relation_data(relation_id, harness.charm.unit)
    app_data = harness.get_relation_data(relation_id, harness.charm.app)

    assert isinstance(harness.charm.unit.status, ActiveStatus)
    assert unit_data == {}
    assert app_data == config


def test_invalid_config(harness, invalid_provider_config, relation_data):
    harness.update_config(invalid_provider_config, relation_data)
    relation_id = harness.add_relation("provider-endpoint", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    unit_data = harness.get_relation_data(relation_id, harness.charm.unit)
    app_data = harness.get_relation_data(relation_id, harness.charm.app)
    assert isinstance(harness.charm.unit.status, BlockedStatus)
    assert unit_data == {}
    assert app_data == {}


def test_microsoft_config(harness, microsoft_config, relation_data):
    harness.update_config(microsoft_config)
    relation_id = harness.add_relation("provider-endpoint", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)
    assert app_data == microsoft_config


def test_microsoft_invalid_config(harness, config, relation_data):
    config["provider"] = "microsoft"
    harness.update_config(config)
    relation_id = harness.add_relation("provider-endpoint", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)
    assert app_data == {}


def test_apple_config(harness, apple_config, relation_data):
    harness.update_config(apple_config)
    relation_id = harness.add_relation("provider-endpoint", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)
    assert app_data == apple_config


def test_apple_invalid_config(harness, config, relation_data):
    config["provider"] = "apple"
    harness.update_config(config)
    relation_id = harness.add_relation("provider-endpoint", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)
    assert app_data == {}


def test_get_redirect_uri(harness, config, mock_event, relation_data):
    harness.update_config(config)
    relation_id = harness.add_relation("provider-endpoint", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    harness.charm._get_redirect_uri(mock_event)

    mock_event.set_results.assert_called_once()
    assert mock_event.set_results.mock_calls[0].args == (relation_data,)
