"""
R_volution power switch entity.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes, switch
from ucapi_framework import SwitchEntity

from uc_intg_rvolution.config import DeviceConfig
from uc_intg_rvolution.device import RvolutionDevice

_LOG = logging.getLogger(__name__)


class RvolutionPowerSwitch(SwitchEntity):
    """Power switch entity for an R_volution device."""

    def __init__(self, device_config: DeviceConfig, device: RvolutionDevice) -> None:
        self._device = device
        entity_id = f"switch.{device_config.identifier}.power"
        super().__init__(
            entity_id,
            f"{device_config.name} Power",
            [switch.Features.ON_OFF, switch.Features.TOGGLE],
            {switch.Attributes.STATE: switch.States.UNKNOWN},
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        state = switch.States.OFF if self._device.state == "OFF" else switch.States.ON
        self.update({switch.Attributes.STATE: state})

    async def _handle_command(
        self, entity: Any, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        try:
            if cmd_id == switch.Commands.ON:
                ok = await self._device.power_on()
            elif cmd_id == switch.Commands.OFF:
                ok = await self._device.power_off()
            elif cmd_id == switch.Commands.TOGGLE:
                ok = await self._device.power_toggle()
            else:
                return StatusCodes.NOT_IMPLEMENTED
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
        except Exception as err:  # pylint: disable=broad-except
            _LOG.error("[%s] Command '%s' error: %s", self.id, cmd_id, err)
            return StatusCodes.SERVER_ERROR
