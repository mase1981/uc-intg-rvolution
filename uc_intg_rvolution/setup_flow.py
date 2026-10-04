"""
Setup flow for the R_volution integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import RequestUserInput, SetupError
from ucapi_framework import BaseSetupFlow

from uc_intg_rvolution.client import RvolutionClient
from uc_intg_rvolution.config import DeviceConfig
from uc_intg_rvolution.const import DEVICE_TYPE_AMLOGIC, DEVICE_TYPE_PLAYER

_LOG = logging.getLogger(__name__)


class RvolutionSetupFlow(BaseSetupFlow[DeviceConfig]):
    """Manual-entry setup flow for R_volution devices.

    Problems are shown on the form with the typed values kept. Update starts from the
    saved values and keeps the device ID, so entity IDs and activities stay intact.
    """

    def get_manual_entry_form(self, error: str = "", values: dict[str, Any] | None = None) -> RequestUserInput:
        saved = self.selected_config_entry
        values = values or {}

        def pick(key: str, default: Any) -> Any:
            if values.get(key) not in (None, ""):
                return values[key]
            return getattr(saved, key, default) if saved else default

        problem = [{
            "id": "error",
            "label": {"en": "Problem"},
            "field": {"label": {"value": {"en": error}}},
        }] if error else []
        return RequestUserInput(
            {"en": "R_volution Device"},
            problem + [
                {
                    "id": "name",
                    "label": {"en": "Device Name"},
                    "field": {"text": {"value": pick("name", "R_volution Player")}},
                },
                {
                    "id": "host",
                    "label": {"en": "IP Address"},
                    "field": {"text": {"value": pick("host", "")}},
                },
                {
                    "id": "device_type",
                    "label": {"en": "Device Type"},
                    "field": {
                        "dropdown": {
                            "value": pick("device_type", DEVICE_TYPE_AMLOGIC),
                            "items": [
                                {
                                    "id": DEVICE_TYPE_AMLOGIC,
                                    "label": {"en": "Amlogic (PlayerOne 8K, Pro 8K, Mini)"},
                                },
                                {
                                    "id": DEVICE_TYPE_PLAYER,
                                    "label": {"en": "R_volution Player"},
                                },
                            ],
                        }
                    },
                },
            ],
        )

    async def query_device(
        self, input_values: dict[str, Any]
    ) -> DeviceConfig | SetupError | RequestUserInput:
        saved = self.selected_config_entry
        host = "".join(str(input_values.get("host") or "").split())
        values = {**input_values, "host": host}
        if not host:
            return self.get_manual_entry_form("Enter the player's IP address.", values)

        device_type = input_values.get("device_type") or DEVICE_TYPE_AMLOGIC
        name = str(input_values.get("name") or "").strip() or f"R_volution ({host})"

        client = RvolutionClient(host, device_type)
        try:
            reachable = await client.is_reachable(timeout=5.0)
        finally:
            await client.close()

        if not reachable:
            _LOG.error("Cannot reach R_volution device at %s", host)
            return self.get_manual_entry_form(
                f"No answer from {host}. Check the IP address and that the player is switched "
                "on and on the same network as the Remote.",
                values,
            )

        # Updating keeps the device ID so entity IDs and activities stay intact.
        identifier = saved.identifier if saved else f"rvolution_{host.replace('.', '_')}"
        _LOG.info("Configured R_volution device %s (%s) at %s", name, device_type, host)
        return DeviceConfig(
            identifier=identifier,
            name=name,
            host=host,
            device_type=device_type,
        )
