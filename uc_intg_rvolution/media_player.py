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
        self._status_update_task = None
        
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
            Features.SELECT_SOURCE,
            Features.SEEK
        ]
        
        attributes = {
            Attributes.STATE: States.UNKNOWN,
            Attributes.VOLUME: 50,
            Attributes.MUTED: False,
            Attributes.MEDIA_TITLE: "",
            Attributes.MEDIA_ARTIST: "",
            Attributes.MEDIA_ALBUM: "",
            Attributes.MEDIA_DURATION: 0,
            Attributes.MEDIA_POSITION: 0,
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
                    self._start_status_updates()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.OFF:
                success = await self._client.power_off()
                if success:
                    await self._update_attributes({Attributes.STATE: States.OFF})
                    self._stop_status_updates()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.TOGGLE:
                success = await self._client.power_toggle()
                if success:
                    current_state = self.attributes.get(Attributes.STATE, States.UNKNOWN)
                    new_state = States.OFF if current_state == States.ON else States.ON
                    await self._update_attributes({Attributes.STATE: new_state})
                    if new_state == States.ON:
                        self._start_status_updates()
                    else:
                        self._stop_status_updates()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.PLAY_PAUSE:
                success = await self._client.play_pause()
                if success:
                    self._start_status_updates()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.STOP:
                success = await self._client.stop()
                if success:
                    await self._update_attributes({Attributes.MEDIA_POSITION: 0})
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.NEXT:
                success = await self._client.next_track()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.PREVIOUS:
                success = await self._client.previous_track()
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
            
            elif cmd_id == Commands.SEEK and params and "media_position" in params:
                position = int(params["media_position"])
                success = await self._client.seek_to_position(position)
                if success:
                    await self._update_attributes({Attributes.MEDIA_POSITION: position})
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            else:
                _LOG.warning(f"Unknown command for media player {self.id}: {cmd_id}")
                return StatusCodes.NOT_IMPLEMENTED
                
        except ConnectionError as e:
            _LOG.error(f"Connection error for media player {self.id}: {e}")
            await self._update_attributes({Attributes.STATE: States.UNAVAILABLE})
            self._attr_available = False
            self._stop_status_updates()
            return StatusCodes.SERVICE_UNAVAILABLE
        
        except CommandError as e:
            _LOG.error(f"Command error for media player {self.id}: {e}")
            return StatusCodes.BAD_REQUEST
        
        except Exception as e:
            _LOG.error(f"Unexpected error for media player {self.id}: {e}", exc_info=True)
            return StatusCodes.SERVER_ERROR

    def _start_status_updates(self):
        """Start periodic status updates."""
        if self._status_update_task is None or self._status_update_task.done():
            self._status_update_task = asyncio.create_task(self._status_update_loop())

    def _stop_status_updates(self):
        """Stop periodic status updates."""
        if self._status_update_task and not self._status_update_task.done():
            self._status_update_task.cancel()
            self._status_update_task = None

    async def _status_update_loop(self):
        """Periodic status update loop."""
        try:
            while True:
                await asyncio.sleep(5.0)
                
                current_state = self.attributes.get(Attributes.STATE, States.UNKNOWN)
                if current_state in [States.OFF, States.UNAVAILABLE]:
                    break
                
                try:
                    await self._update_device_status()
                except Exception:
                    pass
                    
        except asyncio.CancelledError:
            pass

    async def _update_device_status(self):
        """Update device status from API."""
        try:
            status = await self._client.get_device_status()
            if not status:
                return
            
            attributes_update = {}
            
            # Player state
            player_state = status.get('player_state', '')
            playback_state = status.get('playback_state', '')
            
            if player_state == 'file_playback':
                if playback_state == 'playing':
                    attributes_update[Attributes.STATE] = States.PLAYING
                elif playback_state in ['paused', 'pause']:
                    attributes_update[Attributes.STATE] = States.PAUSED
                else:
                    attributes_update[Attributes.STATE] = States.ON
            elif player_state in ['standby']:
                attributes_update[Attributes.STATE] = States.OFF
            else:
                attributes_update[Attributes.STATE] = States.ON
            
            # Media title
            playback_caption = status.get('playback_caption', '')
            if playback_caption:
                if '/' in playback_caption:
                    title = playback_caption.split('/')[-1]
                else:
                    title = playback_caption
                title = title.split('.mkv')[0].split('.mp4')[0].split('.avi')[0]
                attributes_update[Attributes.MEDIA_TITLE] = title
            
            # Chapter as artist
            playback_extra_caption = status.get('playback_extra_caption', '')
            if playback_extra_caption:
                attributes_update[Attributes.MEDIA_ARTIST] = playback_extra_caption
            
            # Duration and position
            playback_duration = status.get('playback_duration', 0)
            if isinstance(playback_duration, (int, float)) and playback_duration > 0:
                attributes_update[Attributes.MEDIA_DURATION] = int(playback_duration)
            
            playback_position = status.get('playback_position', 0)
            if isinstance(playback_position, (int, float)) and playback_position >= 0:
                attributes_update[Attributes.MEDIA_POSITION] = int(playback_position)
            
            # Volume and mute
            playback_volume = status.get('playback_volume', None)
            if isinstance(playback_volume, (int, float)):
                attributes_update[Attributes.VOLUME] = int(playback_volume)
            
            playback_mute = status.get('playback_mute', None)
            if isinstance(playback_mute, (int, bool)):
                attributes_update[Attributes.MUTED] = bool(int(playback_mute))
            
            # Resolution as album
            video_width = status.get('playback_video_width', 0)
            if video_width:
                if video_width >= 3840:
                    resolution = "4K UHD"
                elif video_width >= 1920:
                    resolution = "Full HD"
                elif video_width >= 1280:
                    resolution = "HD"
                else:
                    resolution = f"{video_width}x{status.get('playback_video_height', 0)}"
                attributes_update[Attributes.MEDIA_ALBUM] = resolution
            
            if attributes_update:
                await self._update_attributes(attributes_update)
                
        except Exception:
            pass

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
            
        except Exception as e:
            _LOG.error(f"Failed to update attributes for media player {self.id}: {e}")

    async def test_connection(self) -> bool:
        """Test device connectivity."""
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

    async def push_update(self) -> None:
        """Update entity state to prevent race conditions."""
        try:
            connection_success = await self.test_connection()
            
            if connection_success:
                if self._client.connection_established:
                    await self._update_attributes({Attributes.STATE: States.ON})
                    self._attr_available = True
                    
                    try:
                        await self._update_device_status()
                    except Exception:
                        pass
                        
                else:
                    await self._update_attributes({Attributes.STATE: States.UNKNOWN})
                    self._attr_available = True
            else:
                await self._update_attributes({Attributes.STATE: States.UNAVAILABLE})
                self._attr_available = False
            
            self._initialization_complete = True
            
        except Exception as e:
            _LOG.error(f"Failed to push update for media player {self.id}: {e}")
            self._attr_available = False

    def cleanup(self):
        """Cleanup resources when entity is removed."""
        self._stop_status_updates()

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return self._attr_available and self._initialization_complete

    @property
    def device_config(self) -> DeviceConfig:
        """Get device configuration."""
        return self._device_config