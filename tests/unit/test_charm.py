# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import base64
import dataclasses
import json
from typing import Any

import pytest
from ops.model import ActiveStatus, BlockedStatus, WaitingStatus
from ops.testing import ActionFailed, Context, Relation, Secret
from unit.conftest import create_state
from utils import parse_databag

from charm import KRATOS_EXTERNAL_IDP_INTEGRATION_NAME


class TestCharmConfig:
    def test_relation(
        self,
        context: Context,
        config: dict[str, Any],
        kratos_relation: Relation,
        relation_data: dict[str, Any],
        generic_databag_v1: dict[str, Any],
    ) -> None:
        state = create_state(config=config, relations=[kratos_relation])

        state_out = context.run(context.on.config_changed(), state)

        relations = list(state_out.relations)
        assert len(relations) == 1
        assert parse_databag(relations[0].local_app_data) == generic_databag_v1

        state_status = context.run(context.on.collect_unit_status(), state_out)
        assert state_status.unit_status == WaitingStatus(
            "Waiting for the requirer charm to register the OIDC provider"
        )

        relation_updated = dataclasses.replace(relations[0], remote_app_data=relation_data)
        state_with_data = dataclasses.replace(state_out, relations=[relation_updated])

        state_active = context.run(context.on.collect_unit_status(), state_with_data)
        assert state_active.unit_status == ActiveStatus("The OIDC provider is ready")
        assert parse_databag(list(state_active.relations)[0].local_app_data) == generic_databag_v1

    def test_jsonnet_config(
        self,
        context: Context,
        config: dict[str, Any],
        jsonnet: str,
        kratos_relation: Relation,
        generic_databag_v1: dict[str, Any],
    ) -> None:
        generic_databag_v1["providers"][0].update({
            "id": "generic_c1b858ba120b6a62d17865256fab2617b727ab27",
            "jsonnet_mapper": jsonnet,
            "mapper_url": f"base64://{base64.b64encode(jsonnet.encode()).decode()}",
        })

        new_config: dict[str, Any] = dict(jsonnet_mapper=jsonnet, **config)

        state = create_state(config=new_config, relations=[kratos_relation])

        state_out = context.run(context.on.config_changed(), state)

        relations = list(state_out.relations)
        assert relations[0].local_app_data
        assert parse_databag(relations[0].local_app_data) == generic_databag_v1

    def test_extra_config(
        self,
        context: Context,
        config: dict[str, Any],
        kratos_relation_with_data: Relation,
        generic_databag_v1: dict[str, Any],
    ) -> None:
        config["microsoft_tenant_id"] = "4242424242"

        state = create_state(config=config, relations=[kratos_relation_with_data])

        state_out = context.run(context.on.config_changed(), state)

        relations = list(state_out.relations)
        assert parse_databag(relations[0].local_app_data) == generic_databag_v1

        state_status = context.run(context.on.collect_unit_status(), state_out)
        assert state_status.unit_status == ActiveStatus("The OIDC provider is ready")

    def test_config_no_relation(self, context: Context, config: dict[str, Any]) -> None:
        state = create_state(config=config)

        state_status = context.run(context.on.collect_unit_status(), state)

        assert state_status.unit_status == BlockedStatus(
            f"Missing integration {KRATOS_EXTERNAL_IDP_INTEGRATION_NAME}"
        )


class TestProviderConfig:
    def test_invalid_config(
        self,
        context: Context,
        invalid_provider_config: dict[str, Any],
        config: dict[str, Any],
        kratos_relation: Relation,
        kratos_relation_with_data: Relation,
        generic_databag_v1: dict[str, Any],
    ) -> None:
        state_invalid = create_state(config=invalid_provider_config, relations=[kratos_relation])

        state_out_invalid = context.run(context.on.collect_unit_status(), state_invalid)
        assert state_out_invalid.unit_status == BlockedStatus(
            "Invalid OIDC provider configuration"
        )

        state_out_invalid_event = context.run(context.on.config_changed(), state_invalid)
        assert list(state_out_invalid_event.relations)[0].local_app_data == {}

        state_valid = create_state(config=config, relations=[kratos_relation_with_data])

        state_out_valid = context.run(context.on.config_changed(), state_valid)
        assert (
            parse_databag(list(state_out_valid.relations)[0].local_app_data) == generic_databag_v1
        )

        state_status_valid = context.run(context.on.collect_unit_status(), state_out_valid)
        assert state_status_valid.unit_status == ActiveStatus("The OIDC provider is ready")

    def test_invalid_provider(
        self, context: Context, config: dict[str, Any], kratos_relation: Relation
    ) -> None:
        config["provider"] = "error"
        state = create_state(config=config, relations=[kratos_relation])

        state_status = context.run(context.on.collect_unit_status(), state)
        assert state_status.unit_status == BlockedStatus("Invalid OIDC provider configuration")

        state_out = context.run(context.on.config_changed(), state)
        assert list(state_out.relations)[0].local_app_data == {}

    def test_microsoft_config(
        self,
        context: Context,
        microsoft_config: dict[str, Any],
        kratos_relation_with_data: Relation,
    ) -> None:
        expected_databag = {
            "providers": [
                {
                    "client_id": microsoft_config["client_id"],
                    "provider": microsoft_config["provider"],
                    "microsoft_tenant": microsoft_config["microsoft_tenant_id"],
                    "client_secret": microsoft_config["client_secret"],
                    "scope": "profile email address phone",
                    "id": "microsoft_6e1ce1792c6e3594dfc2f2e9f53d386fcfab4d36",
                    "label": "microsoft",
                    "jsonnet_mapper": None,
                    "mapper_url": None,
                }
            ]
        }

        state = create_state(config=microsoft_config, relations=[kratos_relation_with_data])

        state_out = context.run(context.on.config_changed(), state)

        assert parse_databag(list(state_out.relations)[0].local_app_data) == expected_databag

        state_status = context.run(context.on.collect_unit_status(), state_out)
        assert state_status.unit_status == ActiveStatus("The OIDC provider is ready")

    def test_microsoft_invalid_config(
        self, context: Context, config: dict[str, Any], kratos_relation_with_data: Relation
    ) -> None:
        config["provider"] = "microsoft"

        state = create_state(config=config, relations=[kratos_relation_with_data])

        state_status = context.run(context.on.collect_unit_status(), state)
        assert state_status.unit_status == BlockedStatus("Invalid OIDC provider configuration")

        state_out = context.run(context.on.config_changed(), state)
        assert list(state_out.relations)[0].local_app_data == {}

    def test_github_config(
        self,
        context: Context,
        github_config: dict[str, Any],
        kratos_relation_with_data: Relation,
    ) -> None:
        expected_databag = {
            "providers": [
                {
                    "client_id": github_config["client_id"],
                    "provider": github_config["provider"],
                    "client_secret": github_config["client_secret"],
                    "scope": "user:email",
                    "id": "github_96da49381769303a6515a8785c7f19c383db376a",
                    "label": "github",
                    "jsonnet_mapper": None,
                    "mapper_url": None,
                }
            ]
        }

        state = create_state(config=github_config, relations=[kratos_relation_with_data])

        state_out = context.run(context.on.config_changed(), state)

        assert parse_databag(list(state_out.relations)[0].local_app_data) == expected_databag

        state_status = context.run(context.on.collect_unit_status(), state_out)
        assert state_status.unit_status == ActiveStatus("The OIDC provider is ready")

    def test_apple_config(
        self,
        context: Context,
        apple_config: dict[str, Any],
        kratos_relation_with_data: Relation,
    ) -> None:
        expected_databag = {
            "providers": [
                {
                    "client_id": "client_id",
                    "provider": "apple",
                    "apple_team_id": "apple_team_id",
                    "apple_private_key_id": "apple_private_key_id",
                    "apple_private_key": "apple_private_key",
                    "scope": "profile email address phone",
                    "id": "apple_96da49381769303a6515a8785c7f19c383db376a",
                    "label": "apple",
                    "jsonnet_mapper": None,
                    "mapper_url": None,
                }
            ]
        }

        state = create_state(config=apple_config, relations=[kratos_relation_with_data])

        state_out = context.run(context.on.config_changed(), state)

        assert parse_databag(list(state_out.relations)[0].local_app_data) == expected_databag

        state_status = context.run(context.on.collect_unit_status(), state_out)
        assert state_status.unit_status == ActiveStatus("The OIDC provider is ready")

    def test_apple_invalid_config(
        self, context: Context, config: dict[str, Any], kratos_relation_with_data: Relation
    ) -> None:
        config["provider"] = "apple"

        state = create_state(config=config, relations=[kratos_relation_with_data])

        state_status = context.run(context.on.collect_unit_status(), state)
        assert state_status.unit_status == BlockedStatus("Invalid OIDC provider configuration")

        state_out = context.run(context.on.config_changed(), state)
        assert list(state_out.relations)[0].local_app_data == {}

    def test_disable(
        self,
        context: Context,
        config: dict[str, Any],
        generic_databag_v1: dict[str, Any],
        kratos_relation_with_data: Relation,
    ) -> None:
        disabled_config: dict[str, Any] = dict(enabled=False, **config)
        state_disabled = create_state(
            config=disabled_config, relations=[kratos_relation_with_data]
        )

        state_out_disabled = context.run(context.on.config_changed(), state_disabled)

        state_status_disabled = context.run(context.on.collect_unit_status(), state_out_disabled)
        assert state_status_disabled.unit_status == ActiveStatus("The OIDC provider is disabled")

        assert list(state_out_disabled.relations)[0].local_app_data == {}

        state_enabled = dataclasses.replace(state_out_disabled, config=config)
        state_out_enabled = context.run(context.on.config_changed(), state_enabled)

        state_status_enabled = context.run(context.on.collect_unit_status(), state_out_enabled)
        assert state_status_enabled.unit_status == ActiveStatus("The OIDC provider is ready")
        assert (
            parse_databag(list(state_out_enabled.relations)[0].local_app_data)
            == generic_databag_v1
        )


class TestActions:
    def test_get_redirect_uri(
        self,
        context: Context,
        config: dict[str, Any],
        relation_data: dict[str, Any],
        kratos_relation_with_data: Relation,
    ) -> None:
        redirect_uri = json.loads(relation_data["providers"])[0]["redirect_uri"]

        state = create_state(config=config, relations=[kratos_relation_with_data])

        context.run(context.on.action("get-redirect-uri"), state)

        assert context.action_results == {"redirect-uri": redirect_uri}

        state_status = context.run(context.on.collect_unit_status(), state)
        assert state_status.unit_status == ActiveStatus("The OIDC provider is ready")

    def test_get_redirect_uri_without_relation(
        self, context: Context, config: dict[str, Any]
    ) -> None:
        state = create_state(config=config)

        with pytest.raises(ActionFailed) as exc_info:
            context.run(context.on.action("get-redirect-uri"), state)

        assert exc_info.value.message == "No redirect uri is found"

    def test_get_redirect_uri_without_relation_data(
        self, context: Context, config: dict[str, Any], kratos_relation: Relation
    ) -> None:
        state = create_state(config=config, relations=[kratos_relation])

        with pytest.raises(ActionFailed) as exc_info:
            context.run(context.on.action("get-redirect-uri"), state)

        assert exc_info.value.message == "No redirect uri is found"

    def test_get_redirect_uri_without_leadership(
        self,
        context: Context,
        config: dict[str, Any],
        kratos_relation_with_data: Relation,
    ) -> None:
        state = create_state(config=config, relations=[kratos_relation_with_data], leader=False)

        with pytest.raises(ActionFailed) as exc_info:
            context.run(context.on.action("get-redirect-uri"), state)

        assert exc_info.value.message == "No redirect uri is found"


class TestClientSecretUri:
    @staticmethod
    def _secret_config(config: dict[str, Any], secret: Secret) -> dict[str, Any]:
        new_config = {k: v for k, v in config.items() if k != "client_secret"}
        new_config["client_secret_uri"] = secret.id
        return new_config

    def test_client_secret_is_read_from_the_secret(
        self,
        context: Context,
        config: dict[str, Any],
        kratos_relation: Relation,
        generic_databag_v1: dict[str, Any],
    ) -> None:
        secret = Secret(tracked_content={"client-secret": config["client_secret"]})
        state = dataclasses.replace(
            create_state(config=self._secret_config(config, secret), relations=[kratos_relation]),
            secrets=[secret],
        )

        state_out = context.run(context.on.config_changed(), state)

        relation = list(state_out.relations)[0]
        assert parse_databag(relation.local_app_data) == generic_databag_v1

    def test_plain_client_secret_still_works(
        self,
        context: Context,
        config: dict[str, Any],
        kratos_relation: Relation,
        generic_databag_v1: dict[str, Any],
    ) -> None:
        state = create_state(config=config, relations=[kratos_relation])

        state_out = context.run(context.on.config_changed(), state)

        relation = list(state_out.relations)[0]
        assert parse_databag(relation.local_app_data) == generic_databag_v1

    def test_both_set_blocks(
        self,
        context: Context,
        config: dict[str, Any],
        kratos_relation: Relation,
    ) -> None:
        secret = Secret(tracked_content={"client-secret": "from-the-secret"})
        both = dict(config, client_secret_uri=secret.id)
        state = dataclasses.replace(
            create_state(config=both, relations=[kratos_relation]), secrets=[secret]
        )

        state_out = context.run(context.on.config_changed(), state)
        assert not list(state_out.relations)[0].local_app_data

        state_status = context.run(context.on.collect_unit_status(), state_out)
        assert state_status.unit_status == BlockedStatus(
            "Set either client_secret or client_secret_uri, not both"
        )

    def test_secret_not_granted_blocks(
        self,
        context: Context,
        config: dict[str, Any],
        kratos_relation: Relation,
    ) -> None:
        secret = Secret(tracked_content={"client-secret": "from-the-secret"})
        # The secret is not in the state, so the charm cannot read it.
        state = create_state(
            config=self._secret_config(config, secret), relations=[kratos_relation]
        )

        state_out = context.run(context.on.config_changed(), state)
        assert not list(state_out.relations)[0].local_app_data

        state_status = context.run(context.on.collect_unit_status(), state_out)
        assert state_status.unit_status == BlockedStatus(
            "Grant the client_secret_uri secret to this application"
        )

    def test_grant_after_configuration_is_picked_up_on_update_status(
        self,
        context: Context,
        config: dict[str, Any],
        kratos_relation: Relation,
        generic_databag_v1: dict[str, Any],
    ) -> None:
        secret = Secret(tracked_content={"client-secret": config["client_secret"]})
        state = dataclasses.replace(
            create_state(config=self._secret_config(config, secret), relations=[kratos_relation]),
            secrets=[secret],
        )

        state_out = context.run(context.on.update_status(), state)

        relation = list(state_out.relations)[0]
        assert parse_databag(relation.local_app_data) == generic_databag_v1

    def test_secret_without_the_key_blocks(
        self,
        context: Context,
        config: dict[str, Any],
        kratos_relation: Relation,
    ) -> None:
        secret = Secret(tracked_content={"other-key": "value"})
        state = dataclasses.replace(
            create_state(config=self._secret_config(config, secret), relations=[kratos_relation]),
            secrets=[secret],
        )

        state_out = context.run(context.on.config_changed(), state)
        assert not list(state_out.relations)[0].local_app_data

        state_status = context.run(context.on.collect_unit_status(), state_out)
        assert state_status.unit_status == BlockedStatus(
            "The client_secret_uri secret needs a client-secret key"
        )

    def test_a_new_secret_revision_updates_the_relation(
        self,
        context: Context,
        config: dict[str, Any],
        kratos_relation: Relation,
        generic_databag_v1: dict[str, Any],
    ) -> None:
        secret = Secret(
            tracked_content={"client-secret": config["client_secret"]},
            latest_content={"client-secret": "rotated"},
        )
        state = dataclasses.replace(
            create_state(config=self._secret_config(config, secret), relations=[kratos_relation]),
            secrets=[secret],
        )

        state_out = context.run(context.on.secret_changed(secret), state)

        generic_databag_v1["providers"][0]["client_secret"] = "rotated"
        relation = list(state_out.relations)[0]
        assert parse_databag(relation.local_app_data) == generic_databag_v1

    @pytest.mark.parametrize("failure", ["revoked", "missing-key", "conflicting-options"])
    def test_disable_removes_provider_with_invalid_credentials(
        self,
        context: Context,
        config: dict[str, Any],
        kratos_relation: Relation,
        failure: str,
    ) -> None:
        secret = Secret(tracked_content={"client-secret": config["client_secret"]})
        secret_config = self._secret_config(config, secret)
        state = dataclasses.replace(
            create_state(config=secret_config, relations=[kratos_relation]), secrets=[secret]
        )
        configured = context.run(context.on.config_changed(), state)
        assert next(iter(configured.relations)).local_app_data

        disabled_config = dict(secret_config, enabled=False)
        secrets = [secret]
        if failure == "revoked":
            secrets = []
        elif failure == "missing-key":
            secrets = [Secret(id=secret.id, tracked_content={"other-key": "value"})]
        else:
            disabled_config["client_secret"] = "conflicting-value"
        disabled = dataclasses.replace(configured, config=disabled_config, secrets=secrets)

        state_out = context.run(context.on.config_changed(), disabled)

        assert not next(iter(state_out.relations)).local_app_data
        assert state_out.unit_status == ActiveStatus("The OIDC provider is disabled")

    @pytest.mark.parametrize("use_secret", [True, False])
    def test_invalid_provider_does_not_log_credentials(
        self,
        context: Context,
        config: dict[str, Any],
        kratos_relation: Relation,
        caplog: pytest.LogCaptureFixture,
        use_secret: bool,
    ) -> None:
        credential = "review-canary-value"
        secret = Secret(tracked_content={"client-secret": credential})
        invalid_config = dict(config, provider="typo", client_secret=credential)
        if use_secret:
            invalid_config = self._secret_config(invalid_config, secret)
        state = dataclasses.replace(
            create_state(config=invalid_config, relations=[kratos_relation]),
            secrets=[secret] if use_secret else [],
        )

        state_out = context.run(context.on.config_changed(), state)

        assert state_out.unit_status == BlockedStatus("Invalid OIDC provider configuration")
        assert "External IdP provider configuration invalid" in caplog.text
        assert "union_tag_invalid" in caplog.text
        assert credential not in caplog.text
