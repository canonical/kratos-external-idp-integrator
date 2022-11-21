# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import json

import pytest
from charms.kratos_external_idp_integrator.v0.kratos_external_provider import ExternalIdpRequirer
from ops.charm import CharmBase
from ops.testing import Harness

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        self.external_idp_requirer = ExternalIdpRequirer(self, relation_name=EXTERNAL_IDP_RELATION)


@pytest.fixture
def harness():
    harness = Harness(EndpointAggregatorCharm, meta=KRATOS_META)
    harness.set_leader(True)
    harness.begin_with_initial_hooks()
    yield harness
    harness.cleanup()


def test_get_providers(harness, generic_databag, generic_kratos_config):
    relation_id = harness.add_relation("kratos-external-idp", "kratos-external-provider")
    harness.add_relation_unit(relation_id, "kratos-external-provider/0")
    generic_databag["providers"] = json.dumps(generic_databag["providers"])
    harness.update_relation_data(relation_id, "kratos-external-provider", generic_databag)

    providers = harness.charm.external_idp_requirer.get_providers()

    assert providers == generic_kratos_config


def test_set_relation_registered_provider(harness, generic_databag, generic_kratos_config):
    expected_data = {"redirect_uri": "redirect_uri", "provider_id": "provider_id"}
    relation_id = harness.add_relation("kratos-external-idp", "kratos-external-provider")
    harness.add_relation_unit(relation_id, "kratos-external-provider/0")
    generic_databag["providers"] = json.dumps(generic_databag["providers"])
    harness.update_relation_data(relation_id, "kratos-external-provider", generic_databag)

    harness.charm.external_idp_requirer.set_relation_registered_provider(
        expected_data["redirect_uri"], expected_data["provider_id"], relation_id
    )

    app_data = harness.get_relation_data(relation_id, harness.charm.app)

    assert app_data == expected_data
