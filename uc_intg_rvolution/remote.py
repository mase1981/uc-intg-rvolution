"""
R_volution Remote entity implementation with comprehensive button support.

:copyright: (c) 2025 by Meir Miyara
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

import ucapi
from ucapi import StatusCodes
from ucapi.remote import Attributes, Commands, Features, States
from ucapi.ui import DeviceButtonMapping, EntityCommand, UiPage, create_ui_text, create_ui_icon, Size

from uc_intg_rvolution.client import RvolutionClient, ConnectionError, CommandError
from uc_intg_rvolution.config import DeviceConfig, DeviceType

_LOG = logging.getLogger(__name__)


class RvolutionRemote(ucapi.Remote):

    def __init__(self, client: RvolutionClient, device_config: DeviceConfig, api: ucapi.IntegrationAPI):
        self._client = client
        self._device_config = device_config
        self._api = api
        self._attr_available = True
        
        entity_id = f"remote_{device_config.device_id}"
        
        device_type_name = "Amlogic Remote" if device_config.device_type.value == "amlogic" else "R_volution Remote"
        entity_name = f"{device_config.name} Remote ({device_type_name})"
        
        available_commands = client.get_available_commands()
        
        simple_commands = [cmd for cmd in available_commands if cmd not in [
            "Power On", "Power Off"
        ]]
        
        attributes = {
            Attributes.STATE: States.UNKNOWN
        }
        
        features = [
            Features.ON_OFF,
            Features.TOGGLE,
            Features.SEND_CMD
        ]
        
        ui_pages = self._create_ui_pages(device_config.device_type)
        
        super().__init__(
            identifier=entity_id,
            name=entity_name,
            features=features,
            attributes=attributes,
            simple_commands=simple_commands,
            ui_pages=ui_pages,
            cmd_handler=self._cmd_handler
        )
        
        _LOG.info(f"Created remote entity: {entity_id} for {device_config.name} with {len(simple_commands)} commands")

    def _create_ui_pages(self, device_type: DeviceType) -> list[UiPage]:
        pages = []
        
        main_page = UiPage("main", "Main Controls", grid=Size(4, 6))
        
        main_page.add(create_ui_text("Power", 0, 0, cmd="Power On"))
        main_page.add(create_ui_text("Info", 1, 0, cmd="Info"))
        main_page.add(create_ui_text("Menu", 2, 0, cmd="Menu"))
        main_page.add(create_ui_text("Home", 3, 0, cmd="Home"))

        main_page.add(create_ui_icon("uc:up", 1, 1, cmd="Cursor Up"))
        main_page.add(create_ui_icon("uc:left", 0, 2, cmd="Cursor Left"))
        main_page.add(create_ui_text("OK", 1, 2, cmd="Cursor Enter"))
        main_page.add(create_ui_icon("uc:right", 2, 2, cmd="Cursor Right"))
        main_page.add(create_ui_icon("uc:down", 1, 3, cmd="Cursor Down"))
        main_page.add(create_ui_text("Back", 3, 2, cmd="Return"))

        main_page.add(create_ui_text("Play", 0, 4, cmd="Play/Pause"))
        main_page.add(create_ui_text("Stop", 1, 4, cmd="Stop"))
        main_page.add(create_ui_text("Next", 2, 4, cmd="Next"))
        main_page.add(create_ui_text("Prev", 3, 4, cmd="Previous"))

        main_page.add(create_ui_text("Vol+", 0, 5, cmd="Volume Up"))
        main_page.add(create_ui_text("Vol-", 1, 5, cmd="Volume Down"))
        main_page.add(create_ui_text("Mute", 2, 5, cmd="Mute"))
        main_page.add(create_ui_text("FF", 3, 5, cmd="Fast Forward"))

        pages.append(main_page)

        numbers_page = UiPage("numbers", "Numbers & Functions", grid=Size(4, 6))
        
        numbers = [
            ("1", 0, 0), ("2", 1, 0), ("3", 2, 0),
            ("4", 0, 1), ("5", 1, 1), ("6", 2, 1),
            ("7", 0, 2), ("8", 1, 2), ("9", 2, 2),
            ("0", 1, 3)
        ]

        for num, x, y in numbers:
            numbers_page.add(create_ui_text(num, x, y, cmd=f"Digit {num}"))

        colors = [
            ("Red", "Function Red"),
            ("Green", "Function Green"),
            ("Yellow", "Function Yellow"),
            ("Blue", "Function Blue")
        ]
        
        for col_idx, (label, cmd) in enumerate(colors):
            numbers_page.add(create_ui_text(label, col_idx, 3, cmd=cmd))
        
        numbers_page.add(create_ui_text("Page↑", 0, 4, cmd="Page Up"))
        numbers_page.add(create_ui_text("Page↓", 1, 4, cmd="Page Down"))
        numbers_page.add(create_ui_text("Delete", 2, 4, cmd="Delete"))
        numbers_page.add(create_ui_text("3D", 3, 4, cmd="3D"))
        
        numbers_page.add(create_ui_text("Explorer", 0, 5, cmd="Explorer"))
        numbers_page.add(create_ui_text("Format", 1, 5, cmd="Format Scroll"))
        numbers_page.add(create_ui_text("Dimmer", 2, 5, cmd="Dimmer"))
        if device_type == DeviceType.PLAYER:
            numbers_page.add(create_ui_text("Mouse", 3, 5, cmd="Mouse"))
        else:
            numbers_page.add(create_ui_text("R_video", 3, 5, cmd="R_video"))
        
        pages.append(numbers_page)
        
        advanced_page = UiPage("advanced", "Advanced Controls", grid=Size(4, 6))
        
        advanced_page.add(create_ui_text("FF", 0, 0, cmd="Fast Forward"))
        advanced_page.add(create_ui_text("REW", 1, 0, cmd="Fast Reverse"))
        advanced_page.add(create_ui_text("+10s", 2, 0, cmd="10 sec forward"))
        advanced_page.add(create_ui_text("-10s", 3, 0, cmd="10 sec rewind"))
        
        advanced_page.add(create_ui_text("+60s", 0, 1, cmd="60 sec forward"))
        advanced_page.add(create_ui_text("-60s", 1, 1, cmd="60 sec rewind"))
        advanced_page.add(create_ui_text("Audio", 2, 1, cmd="Audio"))
        advanced_page.add(create_ui_text("Subtitle", 3, 1, cmd="Subtitle"))
        
        advanced_page.add(create_ui_text("Repeat", 0, 2, cmd="Repeat"))
        advanced_page.add(create_ui_text("Zoom", 1, 2, cmd="Zoom"))
        advanced_page.add(create_ui_text("Toggle", 2, 2, cmd="Power Toggle"))
        
        if device_type == DeviceType.PLAYER and "HDMI/XMOS Audio Toggle" in self._client.get_available_commands():
            advanced_page.add(create_ui_text("HDMI/XMOS", 3, 2, cmd="HDMI/XMOS Audio Toggle"))
        
        pages.append(advanced_page)
        
        return pages

    async def _cmd_handler(self, entity: ucapi.Entity, cmd_id: str, params: dict[str, Any] | None) -> StatusCodes:
        _LOG.debug(f"Remote {self.id} received command: {cmd_id} with params: {params}")
        
        try:
            if cmd_id == Commands.ON:
                success = await self._client.power_on()
                if success:
                    await self._update_attributes({Attributes.STATE: States.ON})
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.OFF:
                success = await self._client.power_off()
                if success:
                    await self._update_attributes({Attributes.STATE: States.OFF})
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.TOGGLE:
                success = await self._client.power_toggle()
                if success:
                    current_state = self.attributes.get(Attributes.STATE, States.UNKNOWN)
                    new_state = States.OFF if current_state == States.ON else States.ON
                    await self._update_attributes({Attributes.STATE: new_state})
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.SEND_CMD:
                if not params or "command" not in params:
                    _LOG.warning(f"SEND_CMD missing command parameter for remote {self.id}")
                    return StatusCodes.BAD_REQUEST
                
                command = params["command"]
                success = await self._client.send_ir_command(command)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id in self._client.get_available_commands():
                success = await self._client.send_ir_command(cmd_id)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            else:
                _LOG.warning(f"Unknown command for remote {self.id}: {cmd_id}")
                return StatusCodes.NOT_IMPLEMENTED
                
        except ConnectionError as e:
            _LOG.error(f"Connection error for remote {self.id}: {e}")
            await self._update_attributes({Attributes.STATE: States.UNAVAILABLE})
            return StatusCodes.SERVICE_UNAVAILABLE
        
        except CommandError as e:
            _LOG.error(f"Command error for remote {self.id}: {e}")
            return StatusCodes.BAD_REQUEST
        
        except Exception as e:
            _LOG.error(f"Unexpected error for remote {self.id}: {e}")
            return StatusCodes.SERVER_ERROR

    async def _update_attributes(self, attributes: dict[str, Any]) -> None:
        try:
            for key, value in attributes.items():
                self.attributes[key] = value
            
            if self._api and self._api.configured_entities:
                self._api.configured_entities.update_attributes(self.id, attributes)
            
            _LOG.debug(f"Updated attributes for remote {self.id}: {attributes}")
        except Exception as e:
            _LOG.error(f"Failed to update attributes for remote {self.id}: {e}")

    async def test_connection(self) -> bool:
        try:
            success = await self._client.test_connection()
            if success:
                await self._update_attributes({Attributes.STATE: States.ON})
                self._attr_available = True
            else:
                await self._update_attributes({Attributes.STATE: States.UNAVAILABLE})
                self._attr_available = False
            return success
        except Exception as e:
            _LOG.error(f"Connection test failed for remote {self.id}: {e}")
            await self._update_attributes({Attributes.STATE: States.UNAVAILABLE})
            self._attr_available = False
            return False

    async def push_update(self) -> None:
        _LOG.debug(f"Pushing update for remote {self.id}")
        await self.test_connection()

    @property
    def available(self) -> bool:
        return self._attr_available

    @property
    def device_config(self) -> DeviceConfig:
        return self._device_config