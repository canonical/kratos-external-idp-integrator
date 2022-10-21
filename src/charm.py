#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""A Juju charm for integrating Ory Kratos with and external IdP."""

import logging

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, WaitingStatus

logger = logging.getLogger(__name__)


class InvalidConfigError(Exception):
    """Internal exception that is raised if the charm config is not valid."""

    pass


class KratosIdpIntegratorCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()
    _relation_name = "provider-endpoint"
    _allowed_providers = [
        "generic",
        "google",
        "facebook",
        "microsoft",
        "github",
        "apple",
        "gitlab",
        "auth0",
        "slack",
        "spotify",
        "discord",
        "twitch",
        "netid",
        "yandex",
        "vkontakte",
        "dingtalk",
    ]
    provider_extra_config = {
        "microsoft": ["microsoft_tenant_id"],
        "apple": ["apple_team_id", "apple_private_key_id", "apple_private_key"],
    }
    optional_config = ["requested_claims", "issuer_url"]

    def __init__(self, *args):
        super().__init__(*args)

        # Charm events
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.update_status, self._on_update_status)

        # Relation events
        self.framework.observe(
            self.on.provider_endpoint_relation_created, self._on_relation_created
        )
        self.framework.observe(self.on.provider_endpoint_relation_changed, self._on_relation_changed)

        # Action events
        self.framework.observe(self.on.get_redirect_uri_action, self._get_redirect_uri)
        self.framework.observe(self.on.get_logo_action, self._get_logo)
        self.framework.observe(self.on.set_logo_action, self._set_logo)
        self.framework.observe(self.on.get_identity_schema_action, self._get_identity_schema)
        self.framework.observe(self.on.set_identity_schema_action, self._set_identity_schema)
        self.framework.observe(self.on.get_scopes_action, self._get_scopes)
        self.framework.observe(self.on.set_scopes_action, self._set_scopes)
        self.framework.observe(self.on.get_provider_name_action, self._get_provider_name)
        self.framework.observe(self.on.set_provider_name_action, self._set_provider_name)
        self.framework.observe(self.on.enable_action, self._enable)
        self.framework.observe(self.on.disable_action, self._disable)

        self._stored.set_default(redirect_uri="")

    @property
    def _relation(self):
        try:
            _relation = self.model.get_relation(self._relation_name)
        except KeyError:
            return None
        return _relation

    def _validate_provider_extra_fields(self):
        provider = self.config["provider"]
        for field in self.provider_extra_config.get(provider, []):
            if not self.config.get(field):
                raise InvalidConfigError(
                    f"Missing required configuration for {provider}: '{field}'"
                )

    def _get_provider_extra_fields(self):
        return {
            field: self.config[field]
            for field in self.provider_extra_config.get(self.config["provider"], [])
        }

    def _validate_config(self):
        """Validate the charm config.

        Validates that:
        - client_id exists and it is not None
        - client_secret exists and it is not None
        - provider is valid
        - provider specific configurations are set
        """
        if not self.config.get("client_id"):
            raise InvalidConfigError("Missing required configuration: 'client_id'")
        elif not self.config.get("client_secret"):
            raise InvalidConfigError("Missing required configuration: 'client_secret'")
        elif self.config["provider"] not in self._allowed_providers:
            raise InvalidConfigError(
                "Required configuration 'provider' MUST be one of the following: "
                ", ".join(self._allowed_providers)
            )
        elif self.config["provider"] in ["generic", "auth0"] and "issuer_url" not in self.config:
            raise InvalidConfigError(
                "issuer_url MUST be provided for 'generic' and 'auth0' providers"
            )

        # Should we also validate that the user didn't provide any unused config?
        # E.g. microsoft_tenant_id with provider=google

        self._validate_provider_extra_fields()

    def _get_optional_config(self):
        return {
            field: self.config[field] for field in self.optional_config if self.config.get(field)
        }

    def _configure_relation(self, relation):
        """Validate that the config is valid and pass it to the relation."""
        if not relation or isinstance(self.unit.status, BlockedStatus):
            return

        data = {
            "client_id": self.config["client_id"],
            # TODO: Use juju secret to transmit client_secret once the ops library supports it.
            # Relevant PR: https://github.com/canonical/operator/pull/840
            # TODO: Use vault
            "client_secret": self.config["client_secret"],
            "provider": self.config["provider"],
            **self._get_optional_config(),
            **self._get_provider_extra_fields(),
        }

        relation.data[self.app].update(data)

    def _on_relation_created(self, event):
        relation = event.relation
        self._configure_relation(relation)
        self._on_update_status(event)

    def _on_relation_changed(self, event):
        relation = event.relation
        self._stored.redirect_uri = relation.data[event.app].get("redirect_uri")
        self._on_update_status(event)

    def _on_config_changed(self, event):
        self.unit.status = WaitingStatus("Configuring the charm")
        try:
            self._validate_config()
        except InvalidConfigError as e:
            self.unit.status = BlockedStatus(e.args[0])
            # How should we handle invalid config?
            # if self.relation:
            #     self.relation.data[self.app].clear()
            return
        self._configure_relation(self._relation)
        self._on_update_status(event)

    def _on_update_status(self, event):
        """Set the unit status
        - If unit is blocked, leave it that way (it means that mandatory config is missing)
        - If no relation exists, status is waiting
        - Else status is active
        """
        if not isinstance(self.unit.status, BlockedStatus):
            if not self._relation:
                self.unit.status = WaitingStatus("Waiting for relation with Kratos")
            elif not self._stored.redirect_uri:
                self.unit.status = WaitingStatus("Waiting for Kratos to register provider")
            else:
                self.unit.status = ActiveStatus()

    def _get_redirect_uri(self, event):
        """Get the redirect_uri from the relation and return it to the user."""
        redirect_uri = self._stored.redirect_uri
        if not redirect_uri:
            # Perhaps a more descriptive message is needed here?
            event.set_results("No redirect_uri found")
        else:
            event.set_results({"redirect_uri": self._stored.redirect_uri})

    def _get_logo(self, event):
        # TODO: Implement once we agree on a provider management API
        raise NotImplementedError()

    def _set_logo(self, event):
        # TODO: Implement once we agree on a provider management API
        raise NotImplementedError()

    def _get_identity_schema(self, event):
        # TODO: Implement once we agree on a provider management API
        raise NotImplementedError()

    def _set_identity_schema(self, event):
        # TODO: Implement once we agree on a provider management API
        raise NotImplementedError()

    def _get_scopes(self, event):
        # TODO: Implement once we agree on a provider management API
        raise NotImplementedError()

    def _set_scopes(self, event):
        # TODO: Implement once we agree on a provider management API
        raise NotImplementedError()

    def _get_provider_name(self, event):
        # TODO: Implement once we agree on a provider management API
        raise NotImplementedError()

    def _set_provider_name(self, event):
        # TODO: Implement once we agree on a provider management API
        raise NotImplementedError()

    def _enable(self, event):
        # TODO: Implement once we agree on a provider management API
        raise NotImplementedError()

    def _disable(self, event):
        # TODO: Implement once we agree on a provider management API
        raise NotImplementedError()


if __name__ == "__main__":
    main(KratosIdpIntegratorCharm)
