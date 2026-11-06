#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""A Juju charm for integrating an identity broker with an external IdP."""

import logging
from typing import Any, Union

from charms.kratos_external_idp_integrator.v1.kratos_external_provider import (
    ExternalIdpProvider,
    RedirectURIChangedEvent,
)
from ops import (
    ActionEvent,
    ActiveStatus,
    BlockedStatus,
    CharmBase,
    CollectStatusEvent,
    EventBase,
    MaintenanceStatus,
    ModelError,
    SecretNotFoundError,
    WaitingStatus,
    main,
)

logger = logging.getLogger(__name__)

KRATOS_EXTERNAL_IDP_INTEGRATION_NAME = "kratos-external-idp"
CLIENT_SECRET_OPTION = "client_secret_uri"
CLIENT_SECRET_KEY = "client-secret"


class KratosIdpIntegratorCharm(CharmBase):
    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        self.external_idp_provider = ExternalIdpProvider(self)

        # Lifecycle events
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.secret_changed, self._on_config_changed)
        # Granting a secret to the application fires no hook, so a grant made
        # after client_secret_uri is set is picked up here.
        self.framework.observe(self.on.update_status, self._on_config_changed)
        self.framework.observe(self.on.collect_unit_status, self._on_collect_status)

        # External IdP provider
        self.framework.observe(
            self.external_idp_provider.on.ready,
            self._on_config_changed,
        )
        self.framework.observe(
            self.external_idp_provider.on.redirect_uri_changed,
            self._on_redirect_uri_changed,
        )

        # Action events
        self.framework.observe(
            self.on.get_redirect_uri_action,
            self._on_get_redirect_uri,
        )

    def _provider_config(self) -> Union[dict[str, Any], str]:
        """The provider configuration, or why it cannot be built.

        The client secret is read from the Juju secret named by
        client_secret_uri when that option is set.
        """
        config = dict(self.config)
        if not (secret_id := config.pop(CLIENT_SECRET_OPTION, None)):
            return config

        if config.get("client_secret"):
            return f"Set either client_secret or {CLIENT_SECRET_OPTION}, not both"

        try:
            content = self.model.get_secret(id=secret_id).get_content(refresh=True)
        except (SecretNotFoundError, ModelError):
            return f"Grant the {CLIENT_SECRET_OPTION} secret to this application"

        if not (client_secret := content.get(CLIENT_SECRET_KEY)):
            return f"The {CLIENT_SECRET_OPTION} secret needs a {CLIENT_SECRET_KEY} key"

        config["client_secret"] = client_secret
        return config

    def _on_config_changed(self, event: EventBase) -> None:
        if isinstance(config := self._provider_config(), str):
            return

        if not (providers := self.external_idp_provider.validate_provider_config([config])):
            return

        self.unit.status = MaintenanceStatus("Configuring the charm")

        if not self.external_idp_provider.is_ready():
            return

        if not self.config["enabled"]:
            self.external_idp_provider.remove_provider()
            return

        self.external_idp_provider.create_providers(providers)

    def _on_redirect_uri_changed(self, event: RedirectURIChangedEvent) -> None:
        logger.info(f"The client's redirect_uri changed to {event.redirect_uri}")

    def _on_collect_status(self, event: CollectStatusEvent) -> None:
        if isinstance(config := self._provider_config(), str):
            event.add_status(BlockedStatus(config))
        elif not self.external_idp_provider.validate_provider_config([config]):
            event.add_status(BlockedStatus("Invalid OIDC provider configuration"))

        if not self.external_idp_provider.is_ready():
            event.add_status(
                BlockedStatus(f"Missing integration {KRATOS_EXTERNAL_IDP_INTEGRATION_NAME}")
            )

        if not self.external_idp_provider.get_redirect_uri() and self.config["enabled"]:
            event.add_status(
                WaitingStatus("Waiting for the requirer charm to register the OIDC provider")
            )

        if not self.config["enabled"]:
            event.add_status(ActiveStatus("The OIDC provider is disabled"))

        event.add_status(ActiveStatus("The OIDC provider is ready"))

    def _on_get_redirect_uri(self, event: ActionEvent) -> None:
        if not (redirect_uri := self.external_idp_provider.get_redirect_uri()):
            event.fail("No redirect uri is found")
            return

        event.set_results({"redirect-uri": redirect_uri})


if __name__ == "__main__":
    main(KratosIdpIntegratorCharm)
