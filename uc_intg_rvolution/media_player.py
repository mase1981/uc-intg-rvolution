"""
R_volution Media Player entity

:copyright: (c) 2025 by Meir Miyara
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any, Optional

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
        self._status_available = None  # Track if status endpoint works (None = unknown, True/False = known)
        self._polling_task: Optional[asyncio.Task] = None
        self._polling_interval = 5.0  # Poll every 5 seconds
        
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
            Attributes.MEDIA_IMAGE_URL: "",
            Attributes.MEDIA_TYPE: "",
            Attributes.MEDIA_DURATION: 0,
            Attributes.MEDIA_POSITION: 0
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

    def _start_polling(self):
        """Start background polling task for status updates."""
        if self._polling_task is None or self._polling_task.done():
            self._polling_task = asyncio.create_task(self._status_polling_loop())
            _LOG.info(f"Started status polling for media player {self.id}")

    def _stop_polling(self):
        """Stop background polling task."""
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
            _LOG.info(f"Stopped status polling for media player {self.id}")

    async def _status_polling_loop(self):
        """Background task for continuous status updates."""
        _LOG.debug(f"Status polling loop started for {self.id}")
        while True:
            try:
                await asyncio.sleep(self._polling_interval)
                
                # Only poll if status is available or unknown
                if self._status_available is not False:
                    await self._safe_update_status()
                    
            except asyncio.CancelledError:
                _LOG.debug(f"Status polling cancelled for {self.id}")
                break
            except Exception as e:
                _LOG.debug(f"Polling error for {self.id}: {e}")
                # Continue polling even on errors

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
                    # Trigger immediate status update
                    if self._status_available is not False:
                        await self._safe_update_status()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.STOP:
                success = await self._client.stop()
                if success:
                    await self._update_attributes({
                        Attributes.STATE: States.ON,
                        Attributes.MEDIA_POSITION: 0
                    })
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.NEXT:
                success = await self._client.next_track()
                if success and self._status_available is not False:
                    await self._safe_update_status()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.PREVIOUS:
                success = await self._client.previous_track()
                if success and self._status_available is not False:
                    await self._safe_update_status()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.VOLUME_UP:
                success = await self._client.volume_up()
                if success:
                    # Optimistically update volume (R_volution increments by 5)
                    current_volume = self.attributes.get(Attributes.VOLUME, 50)
                    new_volume = min(100, current_volume + 5)
                    await self._update_attributes({Attributes.VOLUME: new_volume})
                    _LOG.debug(f"Volume up: {current_volume} → {new_volume}")
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.VOLUME_DOWN:
                success = await self._client.volume_down()
                if success:
                    # Optimistically update volume (R_volution decrements by 5)
                    current_volume = self.attributes.get(Attributes.VOLUME, 50)
                    new_volume = max(0, current_volume - 5)
                    await self._update_attributes({Attributes.VOLUME: new_volume})
                    _LOG.debug(f"Volume down: {current_volume} → {new_volume}")
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.MUTE_TOGGLE or cmd_id == Commands.MUTE:
                success = await self._client.mute()
                if success:
                    # Toggle mute state
                    current_mute = self.attributes.get(Attributes.MUTED, False)
                    new_mute = not current_mute
                    await self._update_attributes({Attributes.MUTED: new_mute})
                    _LOG.debug(f"Mute toggle: {current_mute} → {new_mute}")
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.UNMUTE:
                success = await self._client.mute()
                if success:
                    await self._update_attributes({Attributes.MUTED: False})
                    _LOG.debug("Unmute")
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
        """
        Safely update status with R_video API integration.
        Provides rich media metadata when available, never affects entity availability.
        """
        # If we already know status doesn't work, skip completely
        if self._status_available is False:
            return
        
        try:
            # Get enhanced status from R_video API
            enhanced_status = await self._client.get_enhanced_status()
            
            # No status data - mark as unavailable and stop trying
            if not enhanced_status:
                if self._status_available is None:
                    _LOG.info(f"Device {self.id} does not provide R_video API - basic mode enabled")
                    self._status_available = False
                return
            
            # Status works! Mark as available and process data
            if self._status_available is None:
                _LOG.info(f"Device {self.id} R_video API available - enhanced media display enabled")
                self._status_available = True
            
            attributes_update = {}
            
            # Extract playback information
            playback_info = enhanced_status.get('playback_info', {})
            is_playing = enhanced_status.get('is_playing', False)
            
            # Update volume and mute from playback info
            if 'playback_volume' in playback_info:
                try:
                    volume = int(playback_info['playback_volume'])
                    attributes_update[Attributes.VOLUME] = volume
                except (ValueError, TypeError):
                    pass
            
            if 'playback_mute' in playback_info:
                try:
                    muted = int(playback_info['playback_mute']) == 1
                    attributes_update[Attributes.MUTED] = muted
                except (ValueError, TypeError):
                    pass
            
            # Update playback state
            playback_state = playback_info.get('playback_state', '')
            if playback_state == 'playing':
                attributes_update[Attributes.STATE] = States.PLAYING
            elif playback_state == 'paused':
                attributes_update[Attributes.STATE] = States.PAUSED
            elif playback_state == 'buffering':
                attributes_update[Attributes.STATE] = States.BUFFERING
            elif is_playing:
                # In file_playback mode but no explicit state
                attributes_update[Attributes.STATE] = States.PLAYING
            else:
                # Not playing, in navigator/menu
                attributes_update[Attributes.STATE] = States.ON
                # Clear media info when not playing
                attributes_update[Attributes.MEDIA_TITLE] = ""
                attributes_update[Attributes.MEDIA_ARTIST] = ""
                attributes_update[Attributes.MEDIA_ALBUM] = ""
                attributes_update[Attributes.MEDIA_IMAGE_URL] = ""
                attributes_update[Attributes.MEDIA_TYPE] = ""
                attributes_update[Attributes.MEDIA_DURATION] = 0
                attributes_update[Attributes.MEDIA_POSITION] = 0
            
            # If playing, extract rich media metadata
            if is_playing:
                media = enhanced_status.get('media')
                
                # Update duration and position
                if 'playback_duration' in playback_info:
                    try:
                        duration = int(playback_info['playback_duration'])
                        attributes_update[Attributes.MEDIA_DURATION] = duration
                    except (ValueError, TypeError):
                        pass
                
                if 'playback_position' in playback_info:
                    try:
                        position = int(playback_info['playback_position'])
                        attributes_update[Attributes.MEDIA_POSITION] = position
                    except (ValueError, TypeError):
                        pass
                
                # Process media metadata if available
                if media:
                    media_type = media.get('Type', '')
                    
                    if media_type == 'Movie':
                        # Movie: Show title and poster
                        title = media.get('Title', '')
                        poster_url = media.get('PosterUrl', '')
                        
                        attributes_update[Attributes.MEDIA_TITLE] = title
                        attributes_update[Attributes.MEDIA_TYPE] = "MOVIE"
                        attributes_update[Attributes.MEDIA_IMAGE_URL] = poster_url
                        
                        # Clear TV show fields
                        attributes_update[Attributes.MEDIA_ARTIST] = ""
                        attributes_update[Attributes.MEDIA_ALBUM] = ""
                        
                        _LOG.info(f"Updated movie: {title}")
                    
                    elif media_type == 'TVShowEpisode':
                        # TV Show: Show episode title, series name, season/episode, poster
                        episode_title = media.get('Title', '')
                        series_name = media.get('TvShowName', '')
                        season = media.get('Season', 0)
                        episode = media.get('Episode', 0)
                        poster_url = media.get('PosterUrl', '')
                        
                        # Format season/episode info
                        season_episode = f"Season {season} Episode {episode}" if season and episode else ""
                        
                        attributes_update[Attributes.MEDIA_TITLE] = episode_title
                        attributes_update[Attributes.MEDIA_ARTIST] = series_name
                        attributes_update[Attributes.MEDIA_ALBUM] = season_episode
                        attributes_update[Attributes.MEDIA_TYPE] = "TVSHOW"
                        attributes_update[Attributes.MEDIA_IMAGE_URL] = poster_url
                        
                        _LOG.info(f"Updated TV show: {series_name} - {episode_title} ({season_episode})")
                    
                    else:
                        # Unknown media type - show basic info
                        title = media.get('Title', '')
                        if title:
                            attributes_update[Attributes.MEDIA_TITLE] = title
                            attributes_update[Attributes.MEDIA_TYPE] = "VIDEO"
                        
                        _LOG.debug(f"Updated media: {title} (type: {media_type})")
            
            # Apply updates if we have any
            if attributes_update:
                await self._update_attributes(attributes_update)
                _LOG.debug(f"Updated {len(attributes_update)} attributes for {self.id}")
                
        except Exception as e:
            # Mark status as unavailable on first failure
            if self._status_available is None:
                _LOG.info(f"Device {self.id} status check failed - disabling status polling: {e}")
                self._status_available = False
            # Silently ignore all status update failures - they never affect availability

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
            
            _LOG.debug(f"Updated attributes for media player {self.id}: {list(attributes.keys())}")
            
        except Exception as e:
            _LOG.error(f"Failed to update attributes for media player {self.id}: {e}")

    async def test_connection(self) -> bool:
        """Test device connectivity - uses IR command test, never status endpoint."""
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
        """Update entity state and start polling."""
        _LOG.debug(f"Updating state for media player {self.id}")
        
        try:
            # Connection test uses IR command, not status endpoint
            connection_success = await self.test_connection()
            
            if connection_success:
                if self._client.connection_established:
                    await self._update_attributes({Attributes.STATE: States.ON})
                    self._attr_available = True
                    
                    # Try initial status update ONLY if not yet determined
                    if self._status_available is None:
                        await self._safe_update_status()
                    
                    # Start polling for continuous updates
                    self._start_polling()
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
        """Return entity availability - based only on IR command connectivity."""
        return self._attr_available and self._initialization_complete

    @property
    def device_config(self) -> DeviceConfig:
        """Get device configuration."""
        return self._device_config