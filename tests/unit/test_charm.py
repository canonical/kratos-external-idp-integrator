# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import ops
from ops.model import ActiveStatus, BlockedStatus, WaitingStatus

ops.testing.SIMULATE_CAN_CONNECT = True


def test_relation(harness, config, relation_data, generic_databag):
    harness.update_config(config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    unit_data = harness.get_relation_data(relation_id, harness.charm.unit)
    app_data = harness.get_relation_data(relation_id, harness.charm.app)

    assert isinstance(harness.charm.unit.status, ActiveStatus)
    assert unit_data == {}
    assert app_data == generic_databag


def test_extra_config(harness, config, relation_data, generic_databag, caplog):
    config["microsoft_tenant_id"] = "4242424242"

    harness.update_config(config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)

    assert isinstance(harness.charm.unit.status, ActiveStatus)
    assert (
        caplog.records[0].message
        == "Invalid config 'microsoft_tenant_id' for provider 'generic' will be ignored"
    )
    assert app_data == generic_databag


def test_config_no_relation(harness, config, relation_data):
    harness.update_config(config)
    assert isinstance(harness.charm.unit.status, WaitingStatus)


def test_invalid_config(harness, invalid_provider_config, config, generic_databag, relation_data):
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
    assert app_data == generic_databag


def test_invalid_provider(harness, config, relation_data):
    config["provider"] = "error"
    harness.update_config(config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos-app")
    # harness.update_relation_data(relation_id, "kratos-app", relation_data)

    unit_data = harness.get_relation_data(relation_id, harness.charm.unit)
    app_data = harness.get_relation_data(relation_id, harness.charm.app)
    assert isinstance(harness.charm.unit.status, BlockedStatus)
    assert unit_data == {}
    assert app_data == {}


def test_microsoft_config(harness, microsoft_config, relation_data):
    expected_databag = {
        "client_id": microsoft_config["client_id"],
        "provider": microsoft_config["provider"],
        "secret_backend": microsoft_config["secret_backend"],
        "tenant_id": microsoft_config["microsoft_tenant_id"],
        "client_secret": microsoft_config["client_secret"],
    }

    harness.update_config(microsoft_config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)

    assert isinstance(harness.charm.unit.status, ActiveStatus)
    assert app_data == expected_databag


def test_microsoft_invalid_config(harness, config, relation_data):
    config["provider"] = "microsoft"
    harness.update_config(config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)
    assert isinstance(harness.charm.unit.status, BlockedStatus)
    assert app_data == {}


def test_apple_config(harness, apple_config, relation_data):
    expected_databag = {
        "client_id": "client_id",
        "provider": "apple",
        "secret_backend": "plain",
        "team_id": "apple_team_id",
        "private_key_id": "apple_private_key_id",
        "private_key": "apple_private_key",
    }

    harness.update_config(apple_config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)

    assert isinstance(harness.charm.unit.status, ActiveStatus)
    assert app_data == expected_databag


def test_apple_invalid_config(harness, config, relation_data):
    config["provider"] = "apple"
    harness.update_config(config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)
    assert isinstance(harness.charm.unit.status, BlockedStatus)
    assert app_data == {}


def test_get_redirect_uri(harness, config, mock_event, relation_data):
    harness.update_config(config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    harness.charm._get_redirect_uri(mock_event)

    mock_event.set_results.assert_called_once()
    assert isinstance(harness.charm.unit.status, ActiveStatus)
    assert mock_event.set_results.mock_calls[0].args == (
        dict(redirect_uri=relation_data["redirect_uri"]),
    )


def test_get_no_redirect_uri(harness, config, mock_event, relation_data):
    harness.update_config(config)

    harness.charm._get_redirect_uri(mock_event)

    mock_event.set_results.assert_called_once()
    assert mock_event.set_results.mock_calls[0].args == ("No redirect_uri found",)


def test_disable(harness, config, generic_databag, relation_data, mock_event):
    harness.update_config(config)
    relation_id = harness.add_relation("kratos-external-idp", "kratos-app")
    harness.update_relation_data(relation_id, "kratos-app", relation_data)

    harness.charm._disable(mock_event)

    app_data = harness.get_relation_data(relation_id, harness.charm.app)
    assert isinstance(harness.charm.unit.status, ActiveStatus)
    assert app_data == {}

    harness.charm._enable(mock_event)

    assert isinstance(harness.charm.unit.status, ActiveStatus)
    assert app_data == generic_databag
