# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import dataclasses
import json
from typing import Any

import pytest
import yaml
from charms.kratos_external_idp_integrator.v0.kratos_external_provider import (
    ExternalIdpRequirer,
)
from ops.charm import ActionEvent, CharmBase
from ops.testing import Context, Relation, RelationBase, State

EXTERNAL_IDP_RELATION = "kratos-external-idp"

KRATOS_META = f"""
name: kratos-tester
requires:
  {EXTERNAL_IDP_RELATION}:
    interface: external_provider
"""

KRATOS_ACTIONS = """
get-providers:
  params:
    provider-id:
      type: string
  description: Get providers
set-provider:
  params:
    provider-id:
      type: string
      description: Provider ID
    redirect-uri:
      type: string
      description: Redirect URI
  description: Set provider
remove-provider:
  params:
    provider-id:
      type: string
      description: Provider ID
  description: Remove provider
"""

KRATOS_CONFIG = """
options:
  operation:
    type: string
    default: ""
  provider-id:
    type: string
    default: ""
  redirect-uri:
    type: string
    default: ""
"""


class EndpointAggregatorCharm(CharmBase):
    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        self.external_idp_requirer = ExternalIdpRequirer(self, relation_name=EXTERNAL_IDP_RELATION)
        self.framework.observe(self.on.get_providers_action, self._on_get_providers)
        self.framework.observe(self.on.update_status, self._on_update_status)

    def _on_get_providers(self, event: ActionEvent):
        pid = event.params.get("provider-id")
        providers = self.external_idp_requirer.get_providers()

        if pid:
            providers = [
                p for p in providers if getattr(p, "provider_id", getattr(p, "id", None)) == pid
            ]

        providers_dicts = []
        for p in providers:
            pd = {k: v for k, v in vars(p).items() if not k.startswith("_")}
            providers_dicts.append(pd)

        event.set_results({"providers": json.dumps(providers_dicts)})

    def _on_update_status(self, _):
        op = self.config.get("operation")
        if not op:
            return

        pid = str(self.config.get("provider-id"))
        uri = str(self.config.get("redirect-uri"))

        if (
            EXTERNAL_IDP_RELATION in self.model.relations
            and self.model.relations[EXTERNAL_IDP_RELATION]
        ):
            rel = self.model.relations[EXTERNAL_IDP_RELATION][0]

            if op == "set":
                self.external_idp_requirer.set_relation_registered_provider(
                    redirect_uri=uri, provider_id=pid, relation_id=rel.id
                )
            elif op == "remove":
                self.external_idp_requirer.remove_relation_registered_provider(relation_id=rel.id)


@pytest.fixture
def context() -> Context:
    return Context(
        EndpointAggregatorCharm,
        meta=yaml.safe_load(KRATOS_META),
        actions=yaml.safe_load(KRATOS_ACTIONS),
        config=yaml.safe_load(KRATOS_CONFIG),
    )


@pytest.fixture
def external_idp_relation() -> Relation:
    return Relation(EXTERNAL_IDP_RELATION, remote_app_name="kratos-external-provider")


@pytest.fixture
def external_idp_relation_with_data(
    external_idp_relation: Relation, generic_databag: dict[str, Any]
) -> Relation:
    remote_data = dict(generic_databag)
    remote_data["providers"] = json.dumps(generic_databag["providers"])
    return dataclasses.replace(external_idp_relation, remote_app_data=remote_data)


def create_state(
    config: dict[str, Any] | None = None,
    relations: list[RelationBase] | None = None,
    leader: bool = True,
) -> State:
    return State(config=config or {}, relations=relations or [], leader=leader)


class TestExternalIdpRequirer:
    def test_get_providers(
        self,
        context: Context,
        external_idp_relation_with_data: Relation,
        generic_databag: dict[str, Any],
    ):
        state = create_state(relations=[external_idp_relation_with_data])

        context.run(context.on.action("get-providers"), state)

        assert context.action_results is not None
        providers = json.loads(context.action_results["providers"])

        assert len(providers) == 1
        expected = generic_databag["providers"][0]
        assert providers[0]["provider"] == expected["provider"]
        assert providers[0]["client_id"] == expected["client_id"]

    def test_get_providers_with_provider_id(
        self,
        context: Context,
        generic_databag: dict[str, Any],
        external_idp_relation: Relation,
    ):
        remote_data = dict(generic_databag)
        providers_list = [p.copy() for p in generic_databag["providers"]]
        providers_list[0]["provider_id"] = "generic"
        remote_data["providers"] = json.dumps(providers_list)

        relation = dataclasses.replace(external_idp_relation, remote_app_data=remote_data)
        state = create_state(relations=[relation])

        context.run(context.on.action("get-providers", params={"provider-id": "generic"}), state)
        assert context.action_results is not None
        providers = json.loads(context.action_results["providers"])
        assert len(providers) == 1

        context.run(context.on.action("get-providers", params={"provider-id": "invalid"}), state)
        assert context.action_results is not None
        providers_wrong = json.loads(context.action_results["providers"])
        assert len(providers_wrong) == 0

    def test_get_providers_with_jsonnet(
        self,
        context: Context,
        generic_databag: dict[str, Any],
        jsonnet: str,
        external_idp_relation: Relation,
    ):
        remote_data = dict(generic_databag)
        provider_cfg = generic_databag["providers"][0].copy()
        provider_cfg["jsonnet_mapper"] = jsonnet
        remote_data["providers"] = json.dumps([provider_cfg])

        relation = dataclasses.replace(external_idp_relation, remote_app_data=remote_data)
        state = create_state(relations=[relation])

        context.run(context.on.action("get-providers"), state)
        assert context.action_results is not None
        providers = json.loads(context.action_results["providers"])

        assert len(providers) == 1
        assert providers[0]["jsonnet_mapper"] == jsonnet

    def test_set_relation_registered_provider(
        self, context: Context, external_idp_relation: Relation
    ):
        config: dict[str, Any] = {
            "operation": "set",
            "provider-id": "1",
            "redirect-uri": "http://example.com",
        }
        state = create_state(config=config, relations=[external_idp_relation])

        state_out = context.run(context.on.update_status(), state)

        relations = list(state_out.relations)
        assert relations[0].local_app_data
        data = relations[0].local_app_data
        assert "providers" in data

        providers = json.loads(data["providers"])
        assert len(providers) == 1
        assert providers[0]["provider_id"] == "1"
        assert providers[0]["redirect_uri"] == "http://example.com"

    def test_set_and_remove_relation_registered_provider(
        self, context: Context, external_idp_relation: Relation
    ):
        config_set: dict[str, Any] = {
            "operation": "set",
            "provider-id": "1",
            "redirect-uri": "http://example.com",
        }
        state = create_state(config=config_set, relations=[external_idp_relation])
        state_after_set = context.run(context.on.update_status(), state)

        config_remove: dict[str, Any] = {
            "operation": "remove",
            "provider-id": "1",
        }

        relations = list(state_after_set.relations) or None

        state_to_remove = create_state(config=config_remove, relations=relations)
        state_after_remove = context.run(context.on.update_status(), state_to_remove)

        relations_after = list(state_after_remove.relations)
        data = relations_after[0].local_app_data
        assert data == {}
