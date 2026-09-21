# Copyright 2026 Red Hat, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Prefix Ansible display output (including PLAY/TASK banners) with UTC time."""

from datetime import datetime, timezone

from ansible.plugins.callback import CallbackBase
from ansible.utils.display import Display

DOCUMENTATION = r"""
name: utc_timestamp
type: aggregate
short_description: Prefix Ansible display lines with UTC timestamps
description:
  - Wraps Ansible's Display.display so PLAY/TASK banners, task results,
    and profile_tasks lines get a ``[YYYY-MM-DD HH:MM:SS.mmm UTC]`` prefix.
  - Use this to correlate adoption playbook output with ping drop windows.
"""


def _utc_prefix():
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return f"[{stamp} UTC] "


_ORIG_DISPLAY = Display.display


def _timestamped_display(self, msg, *args, **kwargs):
    if msg:
        text = str(msg)
        prefix = _utc_prefix()
        if text.startswith("\n"):
            text = "\n" + prefix + text.lstrip("\n")
        else:
            text = prefix + text
        msg = text
    return _ORIG_DISPLAY(self, msg, *args, **kwargs)


class CallbackModule(CallbackBase):
    """Stamp every Ansible display line with UTC time."""

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "aggregate"
    CALLBACK_NAME = "utc_timestamp"
    CALLBACK_NEEDS_WHITELIST = True
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self):
        super().__init__()
        Display.display = _timestamped_display
