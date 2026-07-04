# Copyright 2024, OpenVoiceOS
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""End-to-end tests for ovos-PHAL-plugin-ipgeo.

Tests that the plugin emits ``configuration.updated`` after a successful
geolocation lookup, using a mocked ``get_ip_geolocation`` to avoid real
network calls and a mocked ``update_mycroft_config`` to avoid writing to disk.
"""
from __future__ import annotations

import time
from unittest import TestCase
from unittest.mock import patch

from ovos_bus_client.message import Message
from ovos_utils.fakebus import FakeBus
from ovos_utils.log import LOG

_MOCK_LOCATION = {
    "city": {
        "code": "EN",
        "name": "Test City",
        "state": {
            "code": "TS",
            "name": "Test State",
            "country": {"code": "US", "name": "United States"},
        },
    },
    "coordinate": {"latitude": 37.7749, "longitude": -122.4194},
    "timezone": {"code": "America/Los_Angeles", "name": "Pacific Standard Time"},
}


class TestIPGeoPlugin(TestCase):
    """Tests for IPGeoPlugin geolocation update messages."""

    def setUp(self) -> None:
        LOG.set_level("WARNING")
        self.bus = FakeBus()

    def _make_plugin(self) -> object:
        """Create an IPGeoPlugin with mocked config and geolocation."""
        from ovos_phal_plugin_ipgeo import IPGeoPlugin

        with patch("ovos_phal_plugin_ipgeo.update_mycroft_config"), \
             patch("ovos_phal_plugin_ipgeo.get_ip_geolocation", return_value=_MOCK_LOCATION):
            plugin = IPGeoPlugin(bus=self.bus)
        return plugin

    def test_on_reset_emits_configuration_updated(self) -> None:
        """on_reset with valid geolocation emits configuration.updated."""
        plugin = self._make_plugin()
        captured: list = []
        self.bus.on("message", lambda m: captured.append(
            Message.deserialize(m) if isinstance(m, str) else m
        ))

        with patch("ovos_phal_plugin_ipgeo.update_mycroft_config"), \
             patch("ovos_phal_plugin_ipgeo.get_ip_geolocation", return_value=_MOCK_LOCATION):
            plugin.on_reset(Message("mycroft.internet.connected"))
        time.sleep(0.1)

        types = [m.msg_type for m in captured]
        assert "configuration.updated" in types, f"Expected configuration.updated, got: {types}"

    def test_on_reset_via_update_request(self) -> None:
        """ovos.ipgeo.update trigger also emits configuration.updated."""
        plugin = self._make_plugin()
        captured: list = []
        self.bus.on("message", lambda m: captured.append(
            Message.deserialize(m) if isinstance(m, str) else m
        ))

        with patch("ovos_phal_plugin_ipgeo.update_mycroft_config"), \
             patch("ovos_phal_plugin_ipgeo.get_ip_geolocation", return_value=_MOCK_LOCATION):
            plugin.on_reset(Message("ovos.ipgeo.update"))
        time.sleep(0.1)

        types = [m.msg_type for m in captured]
        assert "configuration.updated" in types, f"Expected configuration.updated, got: {types}"

    def test_on_reset_network_error_no_crash(self) -> None:
        """ConnectionError in geolocation lookup → no crash, no configuration.updated."""
        plugin = self._make_plugin()
        captured: list = []
        self.bus.on("message", lambda m: captured.append(
            Message.deserialize(m) if isinstance(m, str) else m
        ))

        with patch("ovos_phal_plugin_ipgeo.get_ip_geolocation", side_effect=ConnectionError("timeout")):
            plugin.on_reset(Message("mycroft.internet.connected"))
        time.sleep(0.1)

        types = [m.msg_type for m in captured]
        assert "configuration.updated" not in types, (
            f"Should not emit configuration.updated on error, got: {types}"
        )
