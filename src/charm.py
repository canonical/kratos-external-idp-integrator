#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""A Juju charm for integrating Ory Kratos with and external IdP."""

import logging

from charms.kratos_external_idp_integrator.v0.kratos_external_provider import ExternalIdpProvider
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, WaitingStatus

logger = logging.getLogger(__name__)


class KratosIdpIntegratorCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()
    _relation_name = "kratos-external-idp"

    def __init__(self, *args):
        super().__init__(*args)
        self.external_idp_provider = ExternalIdpProvider(self, self.config)

        # Charm events
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.update_status, self._on_update_status)

        # Library events
        self.framework.observe(
            self.external_idp_provider.on.redirect_uri_changed, self._on_redirect_uri_changed
        )
        self.framework.observe(
            self.external_idp_provider.on.invalid_client_config, self._on_invalid_client_config
        )

        # Action events
        self.framework.observe(self.on.get_redirect_uri_action, self._get_redirect_uri)
        self.framework.observe(self.on.enable_action, self._enable)
        self.framework.observe(self.on.disable_action, self._disable)

        self._stored.set_default(redirect_uri="")
        self._stored.set_default(enabled=True)

    @property
    def _relation(self):
        return self.model.get_relation(self._relation_name)

    def _on_config_changed(self, event):
        self.unit.status = WaitingStatus("Configuring the charm")
        self.external_idp_provider.update_client_config(self.config)
        self._configure_relation()
        self._on_update_status(event)

    def _on_update_status(self, event):
        """Set the unit status.

        - If unit is blocked, leave it that way (it means that mandatory config is missing)
        - If no relation exists, status is waiting
        - Else status is active
        """
        if not isinstance(self.unit.status, BlockedStatus):
            if not self._relation:
                self.unit.status = WaitingStatus("Waiting for relation with Kratos")
            elif not self._stored.redirect_uri and self._stored.enabled:
                self.unit.status = WaitingStatus("Waiting for Kratos to register provider")
            else:
                self.unit.status = ActiveStatus()

    def _on_redirect_uri_changed(self, event):
        self._stored.redirect_uri = event.redirect_uri
        self._on_update_status(event)

    def _on_invalid_client_config(self, event):
        # Can this be fired before the
        self.unit.status = BlockedStatus(event.error)

    def _get_redirect_uri(self, event):
        """Get the redirect_uri from the relation and return it to the user."""
        if redirect_uri := self._stored.redirect_uri:
            event.set_results({"redirect_uri": redirect_uri})
        else:
            # More descriptive message is needed?
            event.set_results("No redirect_uri found")

    def _enable(self, event):
        self._stored.enabled = True
        self._configure_relation()

    def _disable(self, event):
        self._stored.enabled = False
        self._configure_relation()

    def _configure_relation(self):
        """Create or remove the client."""
        if not self._relation or isinstance(self.unit.status, BlockedStatus):
            return

        if not self._stored.enabled:
            self.external_idp_provider.remove_client()
        else:
            self.external_idp_provider.create_client()


if __name__ == "__main__":
    main(KratosIdpIntegratorCharm)
