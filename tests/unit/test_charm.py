# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

from unittest.mock import MagicMock

import ops
import pytest
from ops.testing import Harness

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
def harness(config):
    harness = Harness(KratosIdpIntegratorCharm)
    harness.update_config(config)
    harness.set_leader(True)
    harness.begin()
    yield harness
    harness.cleanup()


def test_relation(harness, config):
    relation_id = harness.add_relation("provider_endpoint", "kratos-app")
    unit_data = harness.get_relation_data(relation_id, harness.charm.unit)
    app_data = harness.get_relation_data(relation_id, harness.charm.app)
    assert unit_data == {}
    assert app_data == config


def test_invalid_config(harness, invalid_provider_config):
    harness.update_config(invalid_provider_config)
    relation_id = harness.add_relation("provider_endpoint", "kratos-app")
    unit_data = harness.get_relation_data(relation_id, harness.charm.unit)
    app_data = harness.get_relation_data(relation_id, harness.charm.app)
    assert unit_data == {}
    assert app_data == {}


def test_get_redirect_uri(harness, config, mock_event):
    redirect_uri = "https://example.com/callback"
    relation_id = harness.add_relation("provider_endpoint", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", {"redirect_uri": redirect_uri})
    harness.charm._get_redirect_uri(mock_event)

    mock_event.set_results.assert_called_once()
    assert mock_event.set_results.mock_calls[0].args == ({"redirect_uri": redirect_uri},)
