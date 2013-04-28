#!/usr/bin/env python

import os
import json
from io import BytesIO


def _get_path(base_dir):
    return os.path.join(base_dir, "manifest.json")


def load(base_dir):
    with open(_get_path(base_dir)) as f:
        return json.load(f)


def format_json(base_dir):
    path = _get_path(base_dir)

    with open(path, "rb") as in_file:
        data = json.load(in_file)

    with open(path, "wb") as out_file:
        out_buffer = BytesIO()
        json.dump(data, out_buffer, sort_keys=True, indent=4)

        out_buffer.seek(0)
        for line in out_buffer.readlines():
            out_file.write(line.rstrip() + "\n")
