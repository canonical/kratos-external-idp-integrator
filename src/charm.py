#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""A Juju charm for integrating an identity broker with an external IdP."""

import logging
from typing import Any

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
    ConfigChangedEvent,
    MaintenanceStatus,
    WaitingStatus,
    main,
)

logger = logging.getLogger(__name__)

KRATOS_EXTERNAL_IDP_INTEGRATION_NAME = "kratos-external-idp"


class KratosIdpIntegratorCharm(CharmBase):
    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        self.external_idp_provider = ExternalIdpProvider(self)

        # Lifecycle events
        self.framework.observe(self.on.config_changed, self._on_config_changed)
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

    def _on_config_changed(self, event: ConfigChangedEvent) -> None:
        if not (providers := self.external_idp_provider.validate_provider_config([self.config])):
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
        if not self.external_idp_provider.validate_provider_config([self.config]):
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
