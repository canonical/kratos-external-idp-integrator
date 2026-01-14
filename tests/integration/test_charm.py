#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.


import logging
from pathlib import Path
from typing import Dict

import jubilant
import pytest
from integration.constants import APP_NAME
from integration.utils import any_error, is_blocked

logger = logging.getLogger(__name__)


@pytest.mark.setup
def test_build_and_deploy(juju: jubilant.Juju, config: Dict, local_charm: Path) -> None:
    """Build the charm-under-test and deploy it together with related charms.

    Assert on the unit status before any relations/configurations take place.
    """
    juju.deploy(str(local_charm), app=APP_NAME, config=config)

    juju.wait(
        ready=is_blocked(APP_NAME),
        error=any_error(APP_NAME),
        timeout=10 * 60,
    )


@pytest.mark.teardown
def test_remove_application(juju: jubilant.Juju) -> None:
    """Test removing the application."""
    juju.remove_application(APP_NAME, destroy_storage=True)
    juju.wait(lambda s: APP_NAME not in s.apps, timeout=10 * 60)
