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
        
        # ENHANCED: Build attributes dynamically based on device capabilities
        attributes = self._build_device_attributes(device_config)
        
        # ENHANCED: Build features dynamically based on device type
        features = self._build_device_features(device_config)
        
        super().__init__(
            identifier=entity_id,
            name=entity_name,
            features=features,
            attributes=attributes,
            device_class=DeviceClasses.TV,
            cmd_handler=self._cmd_handler
        )
        
        _LOG.info(f"Created media player entity: {entity_id} for {device_config.name}")

    def _build_device_attributes(self, device_config: DeviceConfig) -> dict[str, Any]:
        """Build initial attributes dynamically based on device capabilities."""
        # Base attributes that all R_volution devices support
        base_attributes = {
            Attributes.STATE: States.UNKNOWN,
            Attributes.VOLUME: 50,
            Attributes.MUTED: False,
            Attributes.MEDIA_TYPE: MediaType.VIDEO,
            Attributes.MEDIA_TITLE: "R_volution Player"
        }
        
        # ENHANCED: Add enhanced media attributes for devices that support them
        enhanced_attributes = {
            Attributes.MEDIA_ARTIST: "",
            Attributes.MEDIA_ALBUM: "",
            Attributes.MEDIA_IMAGE_URL: "",
            Attributes.REPEAT: "off",
        }
        
        # ENHANCED: Build source list dynamically based on device type
        source_list = self._build_source_list(device_config)
        if source_list:
            base_attributes[Attributes.SOURCE_LIST] = source_list
            base_attributes[Attributes.SOURCE] = None
        
        # Merge enhanced attributes
        base_attributes.update(enhanced_attributes)
        
        return base_attributes

    def _build_device_features(self, device_config: DeviceConfig) -> list[Features]:
        """Build features list dynamically based on device capabilities."""
        # Base features that all R_volution devices support (KEEP EXISTING)
        base_features = [
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
        
        # ENHANCED: Add enhanced features for supported capabilities
        enhanced_features = [
            Features.VOLUME,           # Direct volume setting
            Features.MUTE,            # Explicit mute
            Features.UNMUTE,          # Explicit unmute
            Features.REPEAT,          # Repeat toggle
            Features.MEDIA_DURATION,  # Duration display
            Features.MEDIA_POSITION,  # Position display
            Features.MEDIA_TITLE,     # Title display
            Features.MEDIA_ARTIST,    # Artist display (when available)
            Features.MEDIA_ALBUM,     # Album display (when available)
            Features.MEDIA_IMAGE_URL, # Cover art (when available)
            Features.MEDIA_TYPE,      # Media type indication
        ]
        
        # Add source selection if device supports multiple inputs
        source_list = self._build_source_list(device_config)
        if source_list:
            enhanced_features.append(Features.SELECT_SOURCE)
        
        return base_features + enhanced_features

    def _build_source_list(self, device_config: DeviceConfig) -> list[str]:
        """Build source list dynamically based on device type and capabilities."""
        sources = []
        
        # Base input sources that most R_volution devices support
        if device_config.device_type.value == "amlogic":
            # Amlogic devices (PlayerOne series) typically support
            sources = [
                "hdmi1", "hdmi2", "usb", "network", "sd_card"
            ]
        else:
            # R_volution Player devices typically support
            sources = [
                "hdmi1", "hdmi2", "usb", "network", "optical"
            ]
        
        # Add device-specific functions
        device_functions = [
            "explorer",     # File browser
            "info",         # Device info
            "settings"      # Settings menu
        ]
        
        return sources + device_functions

    async def _cmd_handler(self, entity: ucapi.Entity, cmd_id: str, params: dict[str, Any] | None) -> StatusCodes:
        """Handle media player commands - ENHANCED while preserving existing functionality."""
        _LOG.debug(f"Media player {self.id} received command: {cmd_id} with params: {params}")
        
        try:
            # EXISTING COMMANDS (preserve exact functionality)
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
                    # ENHANCED: Clear media info when stopping
                    await self._clear_media_info()
                    await self._update_attributes({Attributes.STATE: States.ON})
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.NEXT:
                success = await self._client.next_track()
                if success:
                    # ENHANCED: Trigger status update for new media
                    asyncio.create_task(self._deferred_status_update())
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == Commands.PREVIOUS:
                success = await self._client.previous_track()
                if success:
                    # ENHANCED: Trigger status update for new media
                    asyncio.create_task(self._deferred_status_update())
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
            
            # ENHANCED COMMANDS (new functionality)
            elif cmd_id == Commands.VOLUME and params and 'volume' in params:
                # Direct volume setting - use multiple volume up/down commands
                target_volume = int(params['volume'])
                success = await self._set_volume_level(target_volume)
                if success:
                    await self._update_attributes({Attributes.VOLUME: target_volume})
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.MUTE:
                if not self.attributes.get(Attributes.MUTED, False):
                    success = await self._client.mute()
                    if success:
                        await self._update_attributes({Attributes.MUTED: True})
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                return StatusCodes.OK

            elif cmd_id == Commands.UNMUTE:
                if self.attributes.get(Attributes.MUTED, False):
                    success = await self._client.mute()
                    if success:
                        await self._update_attributes({Attributes.MUTED: False})
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                return StatusCodes.OK

            elif cmd_id == Commands.REPEAT:
                success = await self._client.toggle_repeat()
                if success:
                    current_repeat = self.attributes.get(Attributes.REPEAT, "off")
                    new_repeat = "one" if current_repeat == "off" else "off"
                    await self._update_attributes({Attributes.REPEAT: new_repeat})
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.SELECT_SOURCE and params and 'source' in params:
                source = params['source']
                success = await self._handle_source_selection(source)
                if success:
                    await self._update_attributes({Attributes.SOURCE: source})
                    # Clear media info and trigger update after source change
                    await self._clear_media_info()
                    asyncio.create_task(self._deferred_status_update())
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

    async def _set_volume_level(self, target_volume: int) -> bool:
        """Set volume to specific level using volume up/down commands."""
        try:
            current_volume = self.attributes.get(Attributes.VOLUME, 50)
            difference = target_volume - current_volume
            
            if difference == 0:
                return True
            
            # Use volume up/down commands to reach target
            command = self._client.volume_up if difference > 0 else self._client.volume_down
            steps = abs(difference) // 5  # R_volution typically changes volume by 5
            
            for _ in range(min(steps, 20)):  # Limit to prevent excessive commands
                await command()
                await asyncio.sleep(0.1)  # Small delay between commands
            
            return True
        except Exception as e:
            _LOG.error(f"Error setting volume level: {e}")
            return False

    async def _handle_source_selection(self, source: str) -> bool:
        """Handle source selection with device-specific mapping."""
        try:
            # Map sources to R_volution IR commands based on device type
            if self._device_config.device_type.value == "amlogic":
                source_commands = {
                    "hdmi1": "Function Red",
                    "hdmi2": "Function Green", 
                    "usb": "Function Blue",
                    "network": "Function Yellow",
                    "sd_card": "Explorer",
                    "explorer": "Explorer",
                    "info": "Info",
                    "settings": "Menu"
                }
            else:  # R_volution Player
                source_commands = {
                    "hdmi1": "Function Red",
                    "hdmi2": "Function Green",
                    "usb": "Function Blue", 
                    "network": "Function Yellow",
                    "optical": "Audio",
                    "explorer": "Explorer",
                    "info": "Info",
                    "settings": "Menu"
                }
            
            if source in source_commands:
                ir_command = source_commands[source]
                return await self._client.send_ir_command(ir_command)
            else:
                _LOG.warning(f"Unsupported source: {source}")
                return False
                
        except Exception as e:
            _LOG.error(f"Error handling source selection: {e}")
            return False

    async def _update_attributes(self, attributes: dict[str, Any]) -> None:
        """Update attributes and notify integration API."""
        try:
            for key, value in attributes.items():
                self.attributes[key] = value
            
            if self._api and self._api.configured_entities:
                self._api.configured_entities.update_attributes(self.id, attributes)
            
            _LOG.debug(f"Updated attributes for media player {self.id}: {attributes}")
        except Exception as e:
            _LOG.error(f"Failed to update attributes for media player {self.id}: {e}")

    async def update_status(self) -> None:
        """Update status with ENHANCED media information support while preserving existing functionality."""
        try:
            status = await self._client.get_device_status()
            if not status:
                self._handle_state_update(States.UNAVAILABLE)
                return

            updates = {}
            
            # EXISTING STATUS HANDLING (preserve exact logic)
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
            
            # ENHANCED STATUS HANDLING (new functionality)
            if "position" in status:
                updates[Attributes.MEDIA_POSITION] = status["position"]
            
            if "duration" in status and status["duration"] > 0:
                updates[Attributes.MEDIA_DURATION] = status["duration"]
            elif "duration" in status and status["duration"] == 0:
                # Remove duration for live/streaming content
                if Attributes.MEDIA_DURATION in self.attributes:
                    del self.attributes[Attributes.MEDIA_DURATION]
            
            if "repeat" in status:
                updates[Attributes.REPEAT] = "one" if status["repeat"] else "off"
            
            # Enhanced media metadata (when available)
            if "artist" in status and status["artist"]:
                updates[Attributes.MEDIA_ARTIST] = status["artist"]
            
            if "album" in status and status["album"]:
                updates[Attributes.MEDIA_ALBUM] = status["album"]
            
            if "cover_url" in status and status["cover_url"]:
                updates[Attributes.MEDIA_IMAGE_URL] = status["cover_url"]
            
            # Current input detection
            if "input" in status:
                updates[Attributes.SOURCE] = status["input"]
            
            if updates:
                await self._update_attributes(updates)
                
        except Exception as e:
            _LOG.debug(f"Status update failed for media player {self.id}: {e}")

    async def _clear_media_info(self) -> None:
        """Clear media information attributes."""
        clear_attributes = {
            Attributes.MEDIA_TITLE: "",
            Attributes.MEDIA_ARTIST: "",
            Attributes.MEDIA_ALBUM: "", 
            Attributes.MEDIA_IMAGE_URL: "",
        }
        
        # Remove position/duration
        if Attributes.MEDIA_POSITION in self.attributes:
            del self.attributes[Attributes.MEDIA_POSITION]
        if Attributes.MEDIA_DURATION in self.attributes:
            del self.attributes[Attributes.MEDIA_DURATION]
            
        await self._update_attributes(clear_attributes)

    async def _deferred_status_update(self) -> None:
        """Update status after a short delay."""
        await asyncio.sleep(1.0)
        await self.update_status()

    def _handle_state_update(self, new_state: States):
        """Update state and notify integration API."""
        if new_state != self.attributes.get(Attributes.STATE):
            self.attributes[Attributes.STATE] = new_state
            _LOG.debug(f"Media player state changed to: {new_state}")

    # EXISTING METHODS (preserve exactly)
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