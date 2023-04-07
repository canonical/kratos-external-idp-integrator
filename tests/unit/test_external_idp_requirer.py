# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import json
from typing import Any, Dict, Generator

import pytest
from charms.kratos_external_idp_integrator.v0.kratos_external_provider import ExternalIdpRequirer
from ops.charm import CharmBase
from ops.testing import Harness
from utils import parse_databag  # type: ignore

EXTERNAL_IDP_RELATION = "kratos-external-idp"
KRATOS_META = f"""
name: kratos-tester
containers:
  kratos-tester:
requires:
  {EXTERNAL_IDP_RELATION}:
    interface: external_provider
"""


class EndpointAggregatorCharm(CharmBase):
    def __init__(self, *args: Any) -> None:
        super().__init__(*args)

        self.external_idp_requirer = ExternalIdpRequirer(self, relation_name=EXTERNAL_IDP_RELATION)


@pytest.fixture
def harness() -> Generator[Harness, None, None]:
    harness = Harness(EndpointAggregatorCharm, meta=KRATOS_META)
    harness.set_leader(True)
    harness.begin_with_initial_hooks()
    yield harness
    harness.cleanup()


def test_get_providers(
    harness: Harness, generic_databag: Dict, generic_kratos_config: Dict
) -> None:
    relation_id = harness.add_relation("kratos-external-idp", "kratos-external-provider")
    harness.add_relation_unit(relation_id, "kratos-external-provider/0")
    generic_databag["providers"] = json.dumps(generic_databag["providers"])
    harness.update_relation_data(relation_id, "kratos-external-provider", generic_databag)

    providers = harness.charm.external_idp_requirer.get_providers()
    provider = providers[0]

    assert provider.relation_id == relation_id
    assert provider.config() == generic_kratos_config


def test_set_relation_registered_provider(harness: Harness, generic_databag: Dict) -> None:
    redirect_uri = "redirect_uri"
    provider_id = "provider_id"
    expected_data = {"providers": [{"redirect_uri": redirect_uri, "provider_id": provider_id}]}

    relation_id = harness.add_relation("kratos-external-idp", "kratos-external-provider")
    harness.add_relation_unit(relation_id, "kratos-external-provider/0")
    generic_databag["providers"] = json.dumps(generic_databag["providers"])
    harness.update_relation_data(relation_id, "kratos-external-provider", generic_databag)

    harness.charm.external_idp_requirer.set_relation_registered_provider(
        redirect_uri, provider_id, relation_id
    )

    app_data = harness.get_relation_data(relation_id, harness.charm.app)

    assert parse_databag(app_data) == expected_data
