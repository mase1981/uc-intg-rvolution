"""
R_volution quick-launch select entity.

Provides a dropdown of navigation shortcuts that map to IR commands. Because the
device cannot report its current screen over IR, this is an action select: the
chosen option is sent and reflected optimistically.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes, select
from ucapi_framework import SelectEntity

from uc_intg_rvolution.config import DeviceConfig
from uc_intg_rvolution.const import DEVICE_TYPE_PLAYER
from uc_intg_rvolution.device import RvolutionDevice

_LOG = logging.getLogger(__name__)


def _options_for(device_type: str) -> list[str]:
    options = ["Home", "Explorer", "Menu"]
    if device_type != DEVICE_TYPE_PLAYER:
        options.insert(2, "R_video")
    return options


class QuickLaunchSelect(SelectEntity):
    """Navigation shortcut select for an R_volution device."""

    def __init__(self, device_config: DeviceConfig, device: RvolutionDevice) -> None:
        self._device = device
        self._options = _options_for(device_config.device_type)
        entity_id = f"select.{device_config.identifier}.quick_launch"
        super().__init__(
            entity_id,
            f"{device_config.name} Quick Launch",
            {
                select.Attributes.STATE: select.States.UNKNOWN,
                select.Attributes.OPTIONS: [],
                select.Attributes.CURRENT_OPTION: "",
            },
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        state = select.States.UNAVAILABLE if self._device.state == "OFF" else select.States.ON
        self.update(
            {
                select.Attributes.STATE: state,
                select.Attributes.OPTIONS: self._options,
            }
        )

    async def _handle_command(
        self, entity: Any, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id != select.Commands.SELECT_OPTION:
            return StatusCodes.NOT_IMPLEMENTED
        option = (params or {}).get("option", "")
        if option not in self._options:
            return StatusCodes.BAD_REQUEST
        if await self._device.send_command(option):
            self.update({select.Attributes.CURRENT_OPTION: option})
            return StatusCodes.OK
        return StatusCodes.SERVER_ERROR
