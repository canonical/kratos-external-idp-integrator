# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import json


def parse_databag(data):
    data = dict(data)
    data["providers"] = json.loads(data["providers"])
    return data
