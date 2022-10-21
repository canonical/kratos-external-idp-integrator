#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import BlockedStatus, WaitingStatus

logger = logging.getLogger(__name__)


class InvalidConfigError(Exception):
    pass


class KratosIdpIntegratorCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()
    _RELATION_NAME = "provider_endpoint"
    _ALLOWED_PROVIDERS = [
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

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._configure_relation)
        self.framework.observe(
            self.on.provider_endpoint_relation_created, self._configure_relation
        )
        self.framework.observe(
            self.on.provider_endpoint_relation_created, self._configure_relation
        )
        self.framework.observe(self.on.provider_endpoint_relation_changed, self._relation_changed)

        # Actions
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
    def relation(self):
        try:
            _relation = self.model.get_relation(self._RELATION_NAME)
        except KeyError:
            self.unit.status = WaitingStatus(f"Relation '{self._RELATION_NAME}' does not exist")
            return None
        return _relation

    def _validate_config(self):
        if not self.config.get("client_id"):
            raise InvalidConfigError("Missing required configuration: 'client_id'")
        elif not self.config.get("client_secret"):
            raise InvalidConfigError("Missing required configuration: 'client_secret'")
        elif self.config["provider"] not in self._ALLOWED_PROVIDERS:
            raise InvalidConfigError(
                "Required configuration 'provider' MUST be one of the following: "
                ", ".join(self._ALLOWED_PROVIDERS)
            )
        elif self.config["provider"] == "generic" and not self.config["issuer_url"]:
            raise InvalidConfigError("issuer_url MUST be provided for 'generic' providers")

        if self.config["provider"] != "generic" and self.config["issuer_url"] is not None:
            # Should we raise here?
            logger.warn(
                "'issuer_url' is provided, but provider is not 'generic'. "
                "'issuer_url' will be ignored"
            )

    def _configure_relation(self, event):
        relation = getattr(event, "relation", None) or self.relation

        # We validate the config first as we don't
        try:
            self._validate_config()
        except InvalidConfigError as e:
            self.unit.status = BlockedStatus(e.args[0])
            # How should we handle invalid config?
            if relation:
                relation.data[self.app].clear()
            return

        if not relation:
            return

        data = {
            "client_id": self.config["client_id"],
            # TODO: Use juju secret to transmit this once the ops library supports it.
            # Relevant PR: https://github.com/canonical/operator/pull/840
            "client_secret": self.config["client_secret"],
            "provider": self.config["provider"],
            "issuer_url": self.config["issuer_url"],
        }

        relation.data[self.app].update(data)


    def _relation_changed(self, event):
        relation = event.relation
        self._stored.redirect_uri = relation.data[event.app].get("redirect_uri")
        self._configure_relation(event)

    def _get_redirect_uri(self, event):
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
