# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import json
from typing import Dict


def parse_databag(data: Dict) -> Dict:
    data = dict(data)
    data["providers"] = json.loads(data["providers"])
    return data
