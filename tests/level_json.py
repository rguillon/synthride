# Copyright (c) 2026 Renaud Guillon
# SPDX-License-Identifier: MIT

"""Builds level file text for tests."""

import json


def level_json(*rows: object, **settings: object) -> str:
    """Return a level file with the given settings (``name``, ``oxygen``...) and track entries."""
    return json.dumps({**settings, "track": list(rows)})
