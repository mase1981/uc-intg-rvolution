"""
R_volution Media Player entity

:copyright: (c) 2025 by Meir Miyara
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any

import ucapi
from ucapi import StatusCodes
from ucapi.media_player import Attributes, Commands, DeviceClasses, Features, MediaPlayer, States

from uc_intg_rvolution.client import RvolutionClient, ConnectionError, CommandError
from uc_intg_rvolution.config import DeviceConfig

_LOG = logging.getLogger(__name__)


class RvolutionMediaPlayer(MediaPlayer):

    def __init__(self, client: RvolutionClient, device_config: DeviceConfig, api: ucapi.IntegrationAPI):
        self._client = client
        self._device_config = device_config
        self._api = api
        self._attr_available = True
        self._initialization_complete = False
        
        entity_id = f"mp_{device_config.device_id}"
        
        device_type_name = "Amlogic Player" if device_config.device_type.value == "amlogic" else "R_volution Player"
        entity_name = f"{device_config.name} ({device_type_name})"
        
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
            Features.REWIND,
            Features.VOLUME,
            Features.MUTE,
            Features.UNMUTE,
            Features.REPEAT,
            Features.MEDIA_DURATION,
            Features.MEDIA_POSITION,
            Features.MEDIA_TITLE,
            Features.MEDIA_ARTIST,
            Features.MEDIA_ALBUM,
            Features.MEDIA_IMAGE_URL,
            Features.MEDIA_TYPE,
            Features.SELECT_SOURCE
        ]
        
        attributes = {
            Attributes.STATE: States.UNKNOWN,
            Attributes.VOLUME: 50,
            Attributes.MUTED: False,
            Attributes.MEDIA_TITLE: "",
            Attributes.MEDIA_ARTIST: "",
            Attributes.MEDIA_ALBUM: "",
        }
        
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
        _LOG.debug(f"Media player {self.id} received command: {cmd_id}")
        
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
                    # Try to update status after play/pause command
                    await self._safe_update_status()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.STOP:
                success = await self._client.stop()
                if success:
                    await self._update_attributes({Attributes.STATE: States.ON})
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.NEXT:
                success = await self._client.next_track()
                if success:
                    await self._safe_update_status()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.PREVIOUS:
                success = await self._client.previous_track()
                if success:
                    await self._safe_update_status()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.VOLUME_UP:
                success = await self._client.volume_up()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.VOLUME_DOWN:
                success = await self._client.volume_down()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.MUTE_TOGGLE or cmd_id == Commands.MUTE:
                success = await self._client.mute()
                if success:
                    await self._update_attributes({Attributes.MUTED: True})
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.UNMUTE:
                success = await self._client.mute()
                if success:
                    await self._update_attributes({Attributes.MUTED: False})
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.VOLUME and params and "volume" in params:
                return StatusCodes.NOT_IMPLEMENTED
            
            else:
                _LOG.warning(f"Unknown command for media player {self.id}: {cmd_id}")
                return StatusCodes.NOT_IMPLEMENTED
                
        except ConnectionError as e:
            _LOG.error(f"Connection error for media player {self.id}: {e}")
            await self._update_attributes({Attributes.STATE: States.UNAVAILABLE})
            self._attr_available = False
            return StatusCodes.SERVICE_UNAVAILABLE
        
        except CommandError as e:
            _LOG.error(f"Command error for media player {self.id}: {e}")
            return StatusCodes.BAD_REQUEST
        
        except Exception as e:
            _LOG.error(f"Unexpected error for media player {self.id}: {e}", exc_info=True)
            return StatusCodes.SERVER_ERROR

    async def _safe_update_status(self):
        """Safely update status using skyrahfall approach - never throws errors."""
        try:
            status = await self._client.get_device_status()
            if not status:
                return
            
            attributes_update = {}
            
            # Map skyrahfall-style JSON response to attributes
            # Based on skyrahfall repository structure
            
            # Title from JSON response
            if 'title' in status and status['title']:
                attributes_update[Attributes.MEDIA_TITLE] = status['title']
            
            # Artist from JSON response
            if 'artist' in status and status['artist']:
                attributes_update[Attributes.MEDIA_ARTIST] = status['artist']
            
            # Album from JSON response
            if 'album' in status and status['album']:
                attributes_update[Attributes.MEDIA_ALBUM] = status['album']
            
            # Duration from JSON response
            if 'duration' in status:
                duration = status['duration']
                if isinstance(duration, (int, float)) and duration > 0:
                    attributes_update[Attributes.MEDIA_DURATION] = int(duration)
            
            # Position from JSON response
            if 'position' in status:
                position = status['position']
                if isinstance(position, (int, float)) and position >= 0:
                    attributes_update[Attributes.MEDIA_POSITION] = int(position)
            
            # State from JSON response
            if 'state' in status:
                state_str = str(status['state']).lower()
                if state_str == 'playing':
                    attributes_update[Attributes.STATE] = States.PLAYING
                elif state_str == 'paused':
                    attributes_update[Attributes.STATE] = States.PAUSED
                elif state_str == 'stopped':
                    attributes_update[Attributes.STATE] = States.ON
            
            # Volume from JSON response
            if 'volume' in status:
                volume = status['volume']
                if isinstance(volume, (int, float)):
                    attributes_update[Attributes.VOLUME] = int(volume)
            
            # Mute from JSON response
            if 'muted' in status:
                muted = status['muted']
                if isinstance(muted, bool):
                    attributes_update[Attributes.MUTED] = muted
            
            # Apply updates if we have any
            if attributes_update:
                await self._update_attributes(attributes_update)
                _LOG.debug(f"Updated media status for {self.id}: {len(attributes_update)} attributes")
                
        except Exception as e:
            _LOG.debug(f"Status update failed for {self.id}: {e}")
            # Never propagate errors from status updates

    async def _update_attributes(self, attributes: dict[str, Any]) -> None:
        """Update entity attributes."""
        try:
            for key, value in attributes.items():
                self.attributes[key] = value
            
            if self._api and hasattr(self._api, 'configured_entities') and self._api.configured_entities:
                try:
                    self._api.configured_entities.update_attributes(self.id, attributes)
                except Exception as update_error:
                    _LOG.debug(f"Could not update integration API: {update_error}")
            
            _LOG.debug(f"Updated attributes for media player {self.id}: {attributes}")
            
        except Exception as e:
            _LOG.error(f"Failed to update attributes for media player {self.id}: {e}")

    async def test_connection(self) -> bool:
        """Test device connectivity."""
        try:
            success = await self._client.test_connection()
            
            if success:
                await self._update_attributes({Attributes.STATE: States.ON})
                self._attr_available = True
                _LOG.debug(f"Media player {self.id} connection test successful")
            else:
                await self._update_attributes({Attributes.STATE: States.UNAVAILABLE})
                self._attr_available = False
                _LOG.warning(f"Media player {self.id} connection test failed")
            
            return success
            
        except Exception as e:
            _LOG.error(f"Connection test failed for media player {self.id}: {e}")
            await self._update_attributes({Attributes.STATE: States.UNAVAILABLE})
            self._attr_available = False
            return False

    async def push_update(self) -> None:
        """Update entity state to prevent race conditions."""
        _LOG.debug(f"Updating state for media player {self.id}")
        
        try:
            connection_success = await self.test_connection()
            
            if connection_success:
                if self._client.connection_established:
                    await self._update_attributes({Attributes.STATE: States.ON})
                    self._attr_available = True
                    
                    # Try initial status update using skyrahfall approach
                    try:
                        await self._safe_update_status()
                    except Exception as e:
                        _LOG.debug(f"Initial status update failed for {self.id}: {e}")
                        
                else:
                    await self._update_attributes({Attributes.STATE: States.UNKNOWN})
                    self._attr_available = True
            else:
                await self._update_attributes({Attributes.STATE: States.UNAVAILABLE})
                self._attr_available = False
            
            self._initialization_complete = True
            _LOG.info(f"Media player {self.id} state update completed - Available: {self._attr_available}")
            
        except Exception as e:
            _LOG.error(f"Failed to push update for media player {self.id}: {e}")
            self._attr_available = False

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self._attr_available and self._initialization_complete

    @property
    def device_config(self) -> DeviceConfig:
        """Get device configuration."""
        return self._device_config