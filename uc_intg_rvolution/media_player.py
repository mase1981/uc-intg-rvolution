"""
R_volution Media Player entity implementation.

:copyright: (c) 2025 by Meir Miyara
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any

import ucapi
from ucapi import StatusCodes
from ucapi.media_player import Attributes, Commands, DeviceClasses, Features, MediaType, States

from uc_intg_rvolution.client import RvolutionClient, ConnectionError, CommandError
from uc_intg_rvolution.config import DeviceConfig

_LOG = logging.getLogger(__name__)


class RvolutionMediaPlayer(ucapi.MediaPlayer):

    def __init__(self, client: RvolutionClient, device_config: DeviceConfig, api: ucapi.IntegrationAPI):
        self._client = client
        self._device_config = device_config
        self._api = api
        self._attr_available = True
        
        entity_id = f"mp_{device_config.device_id}"
        
        device_type_name = "Amlogic Player" if device_config.device_type.value == "amlogic" else "R_volution Player"
        entity_name = f"{device_config.name} ({device_type_name})"
        
        attributes = {
            Attributes.STATE: States.UNKNOWN,
            Attributes.VOLUME: 50,
            Attributes.MUTED: False,
            Attributes.MEDIA_TYPE: MediaType.VIDEO,
            Attributes.MEDIA_TITLE: "R_volution Player"
        }
        
        features = [
            Features.ON_OFF,
            Features.TOGGLE,
            Features.PLAY_PAUSE,
            Features.STOP,
            Features.NEXT,
            Features.PREVIOUS,
            Features.VOLUME_UP_DOWN,
            Features.MUTE_TOGGLE,
            Features.FAST_FORWARD,
            Features.REWIND
        ]
        
        super().__init__(
            identifier=entity_id,
            name=entity_name,
            features=features,
            attributes=attributes,
            device_class=DeviceClasses.TV,
            cmd_handler=self._cmd_handler
        )
        
        _LOG.info(f"Created media player entity: {entity_id} for {device_config.name}")

    async def _cmd_handler(self, entity: ucapi.Entity, cmd_id: str, params: dict[str, Any] | None) -> StatusCodes:
        _LOG.debug(f"Media player {self.id} received command: {cmd_id} with params: {params}")
        
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
            
            elif cmd_id == Commands.PLAY_PAUSE:
                success = await self._client.play_pause()
                if success:
                    current_state = self.attributes.get(Attributes.STATE, States.UNKNOWN)
                    if current_state == States.PLAYING:
                        new_state = States.PAUSED
                    elif current_state in [States.PAUSED, States.ON]:
                        new_state = States.PLAYING
                    else:
                        new_state = States.PLAYING
                    await self._update_attributes({Attributes.STATE: new_state})
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.STOP:
                success = await self._client.stop()
                if success:
                    await self._update_attributes({Attributes.STATE: States.ON})
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.NEXT:
                success = await self._client.next_track()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.PREVIOUS:
                success = await self._client.previous_track()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.VOLUME_UP:
                success = await self._client.volume_up()
                if success:
                    current_volume = self.attributes.get(Attributes.VOLUME, 50)
                    new_volume = min(100, current_volume + 5)
                    await self._update_attributes({Attributes.VOLUME: new_volume})
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.VOLUME_DOWN:
                success = await self._client.volume_down()
                if success:
                    current_volume = self.attributes.get(Attributes.VOLUME, 50)
                    new_volume = max(0, current_volume - 5)
                    await self._update_attributes({Attributes.VOLUME: new_volume})
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.MUTE_TOGGLE:
                success = await self._client.mute()
                if success:
                    current_muted = self.attributes.get(Attributes.MUTED, False)
                    await self._update_attributes({Attributes.MUTED: not current_muted})
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.FAST_FORWARD:
                success = await self._client.fast_forward()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.REWIND:
                success = await self._client.fast_reverse()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            else:
                _LOG.warning(f"Unknown command for media player {self.id}: {cmd_id}")
                return StatusCodes.NOT_IMPLEMENTED
                
        except ConnectionError as e:
            _LOG.error(f"Connection error for media player {self.id}: {e}")
            await self._update_attributes({Attributes.STATE: States.UNAVAILABLE})
            return StatusCodes.SERVICE_UNAVAILABLE
        
        except CommandError as e:
            _LOG.error(f"Command error for media player {self.id}: {e}")
            return StatusCodes.BAD_REQUEST
        
        except Exception as e:
            _LOG.error(f"Unexpected error for media player {self.id}: {e}")
            return StatusCodes.SERVER_ERROR

    async def _update_attributes(self, attributes: dict[str, Any]) -> None:
        try:
            for key, value in attributes.items():
                self.attributes[key] = value
            
            if self._api and self._api.configured_entities:
                self._api.configured_entities.update_attributes(self.id, attributes)
            
            _LOG.debug(f"Updated attributes for media player {self.id}: {attributes}")
        except Exception as e:
            _LOG.error(f"Failed to update attributes for media player {self.id}: {e}")

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
            _LOG.error(f"Connection test failed for media player {self.id}: {e}")
            await self._update_attributes({Attributes.STATE: States.UNAVAILABLE})
            self._attr_available = False
            return False

    async def update_status(self) -> None:
        try:
            status = await self._client.get_device_status()
            if status:
                updates = {}
                
                if "power" in status:
                    power_state = status["power"]
                    if power_state == "on":
                        playback = status.get("playback", "stop")
                        if playback == "play":
                            updates[Attributes.STATE] = States.PLAYING
                        elif playback == "pause":
                            updates[Attributes.STATE] = States.PAUSED
                        else:
                            updates[Attributes.STATE] = States.ON
                    else:
                        updates[Attributes.STATE] = States.OFF
                
                if "volume" in status:
                    updates[Attributes.VOLUME] = status["volume"]
                
                if "mute" in status:
                    updates[Attributes.MUTED] = status["mute"]
                
                if "title" in status:
                    updates[Attributes.MEDIA_TITLE] = status["title"]
                
                if updates:
                    await self._update_attributes(updates)
                    
        except Exception as e:
            _LOG.debug(f"Status update failed for media player {self.id}: {e}")

    async def push_update(self) -> None:
        _LOG.debug(f"Pushing update for media player {self.id}")
        await self.test_connection()
        await self.update_status()

    @property
    def available(self) -> bool:
        return self._attr_available

    @property
    def device_config(self) -> DeviceConfig:
        return self._device_config