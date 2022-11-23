#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""# Interface library for Kratos external OIDC providers.

This library wraps relation endpoints using the `kratos-external-idp` interface
and provides a Python API for both requesting Kratos to register the a client for
communicating with an external provider.

## Getting Started

To get started using the library, you just need to fetch the library using `charmcraft`.

```shell
cd some-charm
charmcraft fetch-lib charms.kratos_external_idp_integrator.v0.kratos_external_provider
```

In the `metadata.yaml` of the charm, add the following:

```yaml
provides:
    kratos-external-idp:
        interface: external_provider
        limit: 1
```

Then, to initialise the library:

```python
from charms.kratos_external_idp_integrator.v0.kratos_external_provider import (
    ExternalIdpProvider, InvalidConfigError
)
from ops.model import BlockedStatus

class SomeCharm(CharmBase):
  def __init__(self, *args):
    # ...
    self.external_idp_provider = ExternalIdpProvider(self, self.config)

    self.framework.observe(self.external_idp_provider.on.ready, self._on_ready)
    self.framework.observe(
        self.external_idp_provider.on.redirect_uri_changed, self._on_redirect_uri_changed
    )

    def _on_config_changed(self, event):
        # ...
        try:
            self.external_idp_provider.validate_client_config(self.config)
        except InvalidConfigError as e:
            self.unit.status = BlockedStatus(f"Invalid configuration: {e.args[0]}")

        # ...

    def _on_redirect_uri_changed(self, event):
        logger.info(f"The client's redirect_uri changed to {event.redirect_uri}")
        self._stored.redirect_uri = event.redirect_uri
        self._on_update_status(event)

    def _on_ready(self, event):
        if not isinstance(self.unit.status, BlockedStatus):
            self.external_idp_provider.create_client(self.config)
```
"""

import json
import logging

from ops.framework import EventBase, EventSource, Object, ObjectEvents

# The unique Charmhub library identifier, never change it
LIBID = "33040051de7f43a8bb43349f2b037dfc"

# Increment this major API version when introducing breaking changes
LIBAPI = 0

# Increment this PATCH version before using `charmcraft publish-lib` or reset
# to 0 if you are raising the major API version
LIBPATCH = 1

DEFAULT_RELATION_NAME = "kratos-external-idp"
logger = logging.getLogger(__name__)


class InvalidConfigError(Exception):
    """Internal exception that is raised if the charm config is not valid."""

    pass


class BaseProviderConfigHandler:
    """The base class for parsing a provider's config."""

    mandatory_fields = {"provider", "client_id", "secret_backend"}
    providers = []

    @classmethod
    def validate_config(cls, config):
        """Validate and sanitize the user provided config."""
        config_keys = set(config.keys())
        provider = config["provider"]
        if provider not in cls.providers:
            raise ValueError(f"Invalid provider, allowed providers are: {cls.providers}")

        for key in cls.mandatory_fields:
            if not config.get(key, None):
                raise InvalidConfigError(
                    f"Missing required configuration '{key}' for provider '{config['provider']}'"
                )
            config_keys.remove(key)

        if config["secret_backend"] not in ["relation", "secret", "vault"]:
            raise InvalidConfigError(
                f"Invalid value {config['secret_backend']} for `secret_backend` "
                "allowed values are: ['relation', 'secret', 'vault']"
            )

        for key in config_keys:
            logger.warn(f"Invalid config '{key}' for provider '{provider}' will be ignored")

        return {key: value for key, value in config.items() if key not in config_keys}

    @classmethod
    def handle_config(cls, config):
        """Validate the config and transform it in the relation databag expected format."""
        config = cls.validate_config(config)
        return cls.parse_config(config)

    @classmethod
    def parse_config(cls, config):
        """Parse the user provided config into the relation databag expected format."""
        return [
            {
                "client_id": config["client_id"],
                "provider": config["provider"],
                "secret_backend": config["secret_backend"],
                **cls._parse_provider_config(config),
            }
        ]

    @classmethod
    def _parse_provider_config(cls, config):
        """Create the provider specific config."""
        raise NotImplementedError()


class GenericConfigHandler(BaseProviderConfigHandler):
    """The class for parsing a 'generic' provider's config."""

    mandatory_fields = BaseProviderConfigHandler.mandatory_fields | {"client_secret", "issuer_url"}
    providers = ["generic", "auth0"]

    @classmethod
    def _parse_provider_config(cls, config):
        return {
            "client_secret": config["client_secret"],
            "issuer_url": config["issuer_url"],
        }


class SocialConfigHandler(BaseProviderConfigHandler):
    """The class for parsing a social provider's config."""

    mandatory_fields = BaseProviderConfigHandler.mandatory_fields | {"client_secret"}
    providers = [
        "google",
        "facebook",
        "github",
        "gitlab",
        "slack",
        "spotify",
        "discord",
        "twitch",
        "netid",
        "yander",
        "vk",
        "dingtalk",
    ]

    @classmethod
    def _parse_provider_config(cls, config):
        return {
            "client_secret": config["client_secret"],
        }


class MicrosoftConfigHandler(SocialConfigHandler):
    """The class for parsing a 'microsoft' provider's config."""

    mandatory_fields = SocialConfigHandler.mandatory_fields | {
        "microsoft_tenant_id",
    }
    providers = ["microsoft"]

    @classmethod
    def _parse_provider_config(cls, config):
        return {
            "client_secret": config["client_secret"],
            "tenant_id": config["microsoft_tenant_id"],
        }

    @classmethod
    def _parse_relation_data(cls, data):
        return {
            "client_secret": data["client_secret"],
            "tenant_id": data["tenant_id"],
        }


class AppleConfigHandler(BaseProviderConfigHandler):
    """The class for parsing an 'apple' provider's config."""

    mandatory_fields = BaseProviderConfigHandler.mandatory_fields | {
        "apple_team_id",
        "apple_private_key_id",
        "apple_private_key",
    }
    _secret_fields = ["private_key"]
    providers = ["apple"]

    @classmethod
    def _parse_provider_config(cls, config):
        return {
            "team_id": config["apple_team_id"],
            "private_key_id": config["apple_private_key_id"],
            "private_key": config["apple_private_key"],
        }


_config_handlers = [
    GenericConfigHandler,
    SocialConfigHandler,
    MicrosoftConfigHandler,
    AppleConfigHandler,
]
allowed_providers = {
    provider: handler for handler in _config_handlers for provider in handler.providers
}


def get_provider_config_handler(config):
    """Get the config handler for this provider."""
    provider = config.get("provider")
    if provider not in allowed_providers:
        raise InvalidConfigError(
            "Required configuration 'provider' MUST be one of the following: "
            + ", ".join(allowed_providers)
        )
    return allowed_providers[provider]


class RelationReadyEvent(EventBase):
    """Event to notify the charm that the relation is ready."""

    def snapshot(self):
        """Save event."""
        return {}

    def restore(self, snapshot):
        """Restore event."""
        pass


class RedirectURIChangedEvent(EventBase):
    """Event to notify the charm that the redirect_uri changed."""

    def __init__(self, handle, redirect_uri):
        super().__init__(handle)
        self.redirect_uri = redirect_uri

    def snapshot(self):
        """Save redirect_uri."""
        return {"redirect_uri": self.redirect_uri}

    def restore(self, snapshot):
        """Restore redirect_uri."""
        self.redirect_uri = snapshot["redirect_uri"]


class ExternalIdpProviderEvents(ObjectEvents):
    """Event descriptor for events raised by `ExternalIdpProvider`."""

    ready = EventSource(RelationReadyEvent)
    redirect_uri_changed = EventSource(RedirectURIChangedEvent)


class ExternalIdpProvider(Object):
    """Forward client configurations to Identity Broker."""

    on = ExternalIdpProviderEvents()

    def __init__(self, charm, relation_name=DEFAULT_RELATION_NAME):
        super().__init__(charm, relation_name)
        self._charm = charm
        self._relation_name = relation_name

        events = self._charm.on[relation_name]
        self.framework.observe(events.relation_joined, self._on_provider_endpoint_relation_joined)
        self.framework.observe(
            events.relation_changed, self._on_provider_endpoint_relation_changed
        )
        self.framework.observe(
            events.relation_departed, self._on_provider_endpoint_relation_departed
        )

    def _on_provider_endpoint_relation_joined(self, event):
        self.on.ready.emit()

    def _on_provider_endpoint_relation_changed(self, event):
        data = json.loads(event.relation.data[event.app]["providers"])
        if len(data) == 0:
            return
        redirect_uri = data[0].get("redirect_uri")
        self.on.redirect_uri_changed.emit(redirect_uri=redirect_uri)

    def _on_provider_endpoint_relation_departed(self, event):
        self.on.redirect_uri_changed.emit(redirect_uri="")

    def is_ready(self):
        """Checks if the relation is ready."""
        return self._charm.model.get_relation(self._relation_name)

    def create_client(self, config):
        """Use the configuration to create the relation databag."""
        if not self._charm.unit.is_leader():
            return

        config = self._handle_config(config)
        return self._set_client_data(config)

    def remove_client(self):
        """Remove the client config to the relation databag."""
        if not self._charm.unit.is_leader():
            return

        # Do we need to iterate on the relations? There should never be more
        # than one
        for relation in self._charm.model.relations[self._relation_name]:
            relation.data[self._charm.app].clear()

    def validate_client_config(self, config):
        """Validate the client config.

        Raises InvalidConfigError is config is invalid.
        """
        self._validate_config(config)

    def _handle_config(self, config):
        handler = get_provider_config_handler(config)
        return handler.handle_config(config)

    def _validate_config(self, config):
        handler = get_provider_config_handler(config)
        handler.validate_config(config)

    def _set_client_data(self, client_config):
        self._create_secrets(client_config)
        # Do we need to iterate on the relations? There should never be more
        # than one
        for relation in self._charm.model.relations[self._relation_name]:
            relation.data[self._charm.app].update(providers=json.dumps(client_config))

    def _create_secrets(self, client_config):
        for conf in client_config:
            backend = conf["secret_backend"]

            if backend == "relation":
                pass
            elif backend == "secret":
                raise NotImplementedError()
            elif backend == "vault":
                raise NotImplementedError()
            else:
                raise ValueError(f"Invalid backend: {backend}")
