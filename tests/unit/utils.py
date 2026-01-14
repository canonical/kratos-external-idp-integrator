# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import json
from typing import Any, Mapping


def parse_databag(data: Mapping[str, Any]) -> dict[str, Any]:
    output = dict(data)
    if "providers" in output:
        output["providers"] = json.loads(output["providers"])
    return output
