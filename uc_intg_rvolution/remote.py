"""
R_volution remote entity.

Exposes the full IR command set as simple commands plus a physical-button mapping
and on-screen UI pages.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes, remote
from ucapi.ui import Buttons, Size, UiPage, create_btn_mapping, create_ui_icon, create_ui_text
from ucapi_framework import RemoteEntity

from uc_intg_rvolution.config import DeviceConfig
from uc_intg_rvolution.const import DEVICE_TYPE_PLAYER, commands_for
from uc_intg_rvolution.device import RvolutionDevice

_LOG = logging.getLogger(__name__)


class RvolutionRemote(RemoteEntity):
    """Remote entity for an R_volution device."""

    def __init__(self, device_config: DeviceConfig, device: RvolutionDevice) -> None:
        self._device = device
        entity_id = f"remote.{device_config.identifier}"
        simple_commands = list(commands_for(device_config.device_type).keys())

        super().__init__(
            entity_id,
            device_config.name,
            [remote.Features.ON_OFF, remote.Features.TOGGLE, remote.Features.SEND_CMD],
            {remote.Attributes.STATE: remote.States.UNKNOWN},
            simple_commands=simple_commands,
            button_mapping=self._button_mapping(),
            ui_pages=self._ui_pages(device_config.device_type),
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "OFF":
            self.update({remote.Attributes.STATE: remote.States.OFF})
        else:
            self.update({remote.Attributes.STATE: remote.States.ON})

    async def _handle_command(
        self, entity: Any, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        try:
            if cmd_id == remote.Commands.ON:
                ok = await self._device.power_on()
            elif cmd_id == remote.Commands.OFF:
                ok = await self._device.power_off()
            elif cmd_id == remote.Commands.TOGGLE:
                ok = await self._device.power_toggle()
            elif cmd_id == remote.Commands.SEND_CMD:
                command = (params or {}).get("command", "")
                ok = await self._device.send_command(command)
            elif self._device.client and self._device.client.has_command(cmd_id):
                ok = await self._device.send_command(cmd_id)
            else:
                return StatusCodes.NOT_IMPLEMENTED
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
        except Exception as err:  # pylint: disable=broad-except
            _LOG.error("[%s] Command '%s' error: %s", self.id, cmd_id, err)
            return StatusCodes.SERVER_ERROR

    @staticmethod
    def _button_mapping() -> list:
        return [
            create_btn_mapping(Buttons.POWER, short="Power Toggle"),
            create_btn_mapping(Buttons.HOME, short="Home"),
            create_btn_mapping(Buttons.BACK, short="Return"),
            create_btn_mapping(Buttons.MENU, short="Menu"),
            create_btn_mapping(Buttons.DPAD_UP, short="Cursor Up"),
            create_btn_mapping(Buttons.DPAD_DOWN, short="Cursor Down"),
            create_btn_mapping(Buttons.DPAD_LEFT, short="Cursor Left"),
            create_btn_mapping(Buttons.DPAD_RIGHT, short="Cursor Right"),
            create_btn_mapping(Buttons.DPAD_MIDDLE, short="Cursor Enter"),
            create_btn_mapping(Buttons.VOLUME_UP, short="Volume Up"),
            create_btn_mapping(Buttons.VOLUME_DOWN, short="Volume Down"),
            create_btn_mapping(Buttons.MUTE, short="Mute"),
            create_btn_mapping(Buttons.CHANNEL_UP, short="Page Up"),
            create_btn_mapping(Buttons.CHANNEL_DOWN, short="Page Down"),
            create_btn_mapping(Buttons.PREV, short="Previous"),
            create_btn_mapping(Buttons.NEXT, short="Next"),
            create_btn_mapping(Buttons.PLAY, short="Play/Pause"),
            create_btn_mapping(Buttons.STOP, short="Stop"),
        ]

    @staticmethod
    def _ui_pages(device_type: str) -> list[UiPage]:
        main = UiPage("main", "Main Controls", grid=Size(4, 6))
        main.add(create_ui_text("Power", 0, 0, cmd="Power Toggle"))
        main.add(create_ui_text("Info", 1, 0, cmd="Info"))
        main.add(create_ui_text("Menu", 2, 0, cmd="Menu"))
        main.add(create_ui_text("Home", 3, 0, cmd="Home"))
        main.add(create_ui_icon("uc:up", 1, 1, cmd="Cursor Up"))
        main.add(create_ui_icon("uc:left", 0, 2, cmd="Cursor Left"))
        main.add(create_ui_text("OK", 1, 2, cmd="Cursor Enter"))
        main.add(create_ui_icon("uc:right", 2, 2, cmd="Cursor Right"))
        main.add(create_ui_icon("uc:down", 1, 3, cmd="Cursor Down"))
        main.add(create_ui_text("Back", 3, 2, cmd="Return"))
        main.add(create_ui_text("Play", 0, 4, cmd="Play/Pause"))
        main.add(create_ui_text("Stop", 1, 4, cmd="Stop"))
        main.add(create_ui_text("Prev", 2, 4, cmd="Previous"))
        main.add(create_ui_text("Next", 3, 4, cmd="Next"))
        main.add(create_ui_text("Vol+", 0, 5, cmd="Volume Up"))
        main.add(create_ui_text("Vol-", 1, 5, cmd="Volume Down"))
        main.add(create_ui_text("Mute", 2, 5, cmd="Mute"))
        main.add(create_ui_text("FF", 3, 5, cmd="Fast Forward"))

        numbers = UiPage("numbers", "Numbers & Functions", grid=Size(4, 6))
        for num, x, y in [
            ("1", 0, 0), ("2", 1, 0), ("3", 2, 0),
            ("4", 0, 1), ("5", 1, 1), ("6", 2, 1),
            ("7", 0, 2), ("8", 1, 2), ("9", 2, 2),
            ("0", 1, 3),
        ]:
            numbers.add(create_ui_text(num, x, y, cmd=f"Digit {num}"))
        for row, (label, cmd) in enumerate(
            [("Red", "Function Red"), ("Green", "Function Green"),
             ("Yellow", "Function Yellow"), ("Blue", "Function Blue")]
        ):
            numbers.add(create_ui_text(label, 3, row, cmd=cmd))
        numbers.add(create_ui_text("Page+", 0, 4, cmd="Page Up"))
        numbers.add(create_ui_text("Page-", 1, 4, cmd="Page Down"))
        numbers.add(create_ui_text("Delete", 2, 4, cmd="Delete"))
        numbers.add(create_ui_text("3D", 3, 4, cmd="3D"))
        numbers.add(create_ui_text("Explorer", 0, 5, cmd="Explorer"))
        numbers.add(create_ui_text("Format", 1, 5, cmd="Format Scroll"))
        numbers.add(create_ui_text("Dimmer", 2, 5, cmd="Dimmer"))
        if device_type == DEVICE_TYPE_PLAYER:
            numbers.add(create_ui_text("Mouse", 3, 5, cmd="Mouse"))
        else:
            numbers.add(create_ui_text("R_video", 3, 5, cmd="R_video"))

        advanced = UiPage("advanced", "Advanced Controls", grid=Size(4, 6))
        advanced.add(create_ui_text("FF", 0, 0, cmd="Fast Forward"))
        advanced.add(create_ui_text("REW", 1, 0, cmd="Fast Reverse"))
        advanced.add(create_ui_text("+10s", 2, 0, cmd="10 sec forward"))
        advanced.add(create_ui_text("-10s", 3, 0, cmd="10 sec rewind"))
        advanced.add(create_ui_text("+60s", 0, 1, cmd="60 sec forward"))
        advanced.add(create_ui_text("-60s", 1, 1, cmd="60 sec rewind"))
        advanced.add(create_ui_text("Audio", 2, 1, cmd="Audio"))
        advanced.add(create_ui_text("Subtitle", 3, 1, cmd="Subtitle"))
        advanced.add(create_ui_text("Repeat", 0, 2, cmd="Repeat"))
        advanced.add(create_ui_text("Zoom", 1, 2, cmd="Zoom"))
        advanced.add(create_ui_text("On", 2, 2, cmd="Power On"))
        advanced.add(create_ui_text("Off", 3, 2, cmd="Power Off"))
        if device_type == DEVICE_TYPE_PLAYER:
            advanced.add(create_ui_text("HDMI/XMOS", 0, 3, cmd="HDMI/XMOS Audio Toggle"))

        return [main, numbers, advanced]
