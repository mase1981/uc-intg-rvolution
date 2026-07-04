"""
Setup flow for the R_volution integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import IntegrationSetupError, RequestUserInput, SetupError
from ucapi_framework import BaseSetupFlow

from uc_intg_rvolution.client import RvolutionClient
from uc_intg_rvolution.config import DeviceConfig
from uc_intg_rvolution.const import DEVICE_TYPE_AMLOGIC, DEVICE_TYPE_PLAYER

_LOG = logging.getLogger(__name__)


class RvolutionSetupFlow(BaseSetupFlow[DeviceConfig]):
    """Manual-entry setup flow for R_volution devices."""

    def get_manual_entry_form(self) -> RequestUserInput:
        return RequestUserInput(
            {"en": "R_volution Device"},
            [
                {
                    "id": "name",
                    "label": {"en": "Device Name"},
                    "field": {"text": {"value": "R_volution Player"}},
                },
                {
                    "id": "host",
                    "label": {"en": "IP Address"},
                    "field": {"text": {"value": ""}},
                },
                {
                    "id": "device_type",
                    "label": {"en": "Device Type"},
                    "field": {
                        "dropdown": {
                            "value": DEVICE_TYPE_AMLOGIC,
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
        host = input_values.get("host", "").strip()
        if not host:
            return SetupError(error_type=IntegrationSetupError.OTHER)

        device_type = input_values.get("device_type", DEVICE_TYPE_AMLOGIC)
        name = input_values.get("name", "").strip() or f"R_volution ({host})"

        client = RvolutionClient(host, device_type)
        try:
            reachable = await client.is_reachable(timeout=5.0)
        finally:
            await client.close()

        if not reachable:
            _LOG.error("Cannot reach R_volution device at %s", host)
            return SetupError(error_type=IntegrationSetupError.CONNECTION_REFUSED)

        identifier = f"rvolution_{host.replace('.', '_')}"
        _LOG.info("Configured R_volution device %s (%s) at %s", name, device_type, host)
        return DeviceConfig(
            identifier=identifier,
            name=name,
            host=host,
            device_type=device_type,
        )
