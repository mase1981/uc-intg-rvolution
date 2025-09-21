"""
HTTP client for R_volution device communication.

:copyright: (c) 2025 by Meir Miyara
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from enum import Enum

import aiohttp

from uc_intg_rvolution.config import DeviceConfig, DeviceType

_LOG = logging.getLogger(__name__)


class RvolutionError(Exception):
    pass


class ConnectionError(RvolutionError):
    pass


class CommandError(RvolutionError):
    pass


class RvolutionClient:
    
    def __init__(self, device_config: DeviceConfig):
        self.device_config = device_config
        self._session: Optional[aiohttp.ClientSession] = None
        self._base_url = f"http://{device_config.ip_address}:{device_config.port}"
        
        self._ir_codes = self._get_ir_codes_for_device_type(device_config.device_type)
        
        _LOG.debug(f"Initialized client for {device_config.name} ({device_config.device_type.value}) at {self._base_url}")
    
    def _get_ir_codes_for_device_type(self, device_type: DeviceType) -> Dict[str, str]:
        if device_type == DeviceType.AMLOGIC:
            return self._get_amlogic_ir_codes()
        else:
            return self._get_player_ir_codes()
    
    def _get_amlogic_ir_codes(self) -> Dict[str, str]:
        return {
            "3D": "ED124040",
            "Audio": "E6194040",
            "Cursor Down": "F10E4040",
            "Cursor Enter": "F20D4040",
            "Cursor Left": "EF104040",
            "Cursor Right": "EE114040",
            "Cursor Up": "F40B4040",
            "Delete": "F30C4040",
            "Digit 0": "FF004040",
            "Digit 1": "FE014040",
            "Digit 2": "FD024040",
            "Digit 3": "FC034040",
            "Digit 4": "FB044040",
            "Digit 5": "FA054040",
            "Digit 6": "F9064040",
            "Digit 7": "F8074040",
            "Digit 8": "F7084040",
            "Digit 9": "F6094040",
            "Dimmer": "A45B4040",
            "Explorer": "EA164040",
            "Format Scroll": "EB144040",
            "Function Green": "F50A4040",
            "Function Yellow": "BE414040",
            "Function Red": "A68E4040",
            "Function Blue": "AB544040",
            "Home": "E51A4040",
            "Info": "BB444040",
            "Menu": "BA454040",
            "Mouse": "B98F4040",
            "Mute": "BC434040",
            "Page Down": "DB204040",
            "Page Up": "BF404040",
            "Play/Pause": "AC534040",
            "Power Toggle": "B24D4040",
            "Power Off": "4AB54040",
            "Power On": "4CB34040",
            "Repeat": "B9464040",
            "Return": "BD424040",
            "R_video": "EC134040",
            "Subtitle": "E41B4040",
            "Volume Down": "E8174040",
            "Volume Up": "E7184040",
            "Zoom": "E21D4040",
            "Next": "E11E4040",
            "Previous": "E01F4040",
            "Fast Forward": "E41BBF00",
            "Fast Reverse": "E31CBF00",
            "Stop": "BD424040",
            "60 sec forward": "EE114040",
            "60 sec rewind": "EF104040",
            "10 sec forward": "BF404040",
            "10 sec rewind": "DF204040"
        }
    
    def _get_player_ir_codes(self) -> Dict[str, str]:
        return {
            "3D": "EC124040",
            "Audio": "EC194040",
            "Cursor Down": "EC0E4040",
            "Cursor Enter": "EC0D4040",
            "Cursor Left": "EC104040",
            "Cursor Right": "EC114040",
            "Cursor Up": "EC0B4040",
            "Delete": "EC0C4040",
            "Digit 0": "EC004040",
            "Digit 1": "EC014040",
            "Digit 2": "EC024040",
            "Digit 3": "EC034040",
            "Digit 4": "EC044040",
            "Digit 5": "EC054040",
            "Digit 6": "EC064040",
            "Digit 7": "EC074040",
            "Digit 8": "EC084040",
            "Digit 9": "EC094040",
            "Dimmer": "EC5B4040",
            "Explorer": "EC164040",
            "Fast Forward": "E41BBF00",
            "Fast Reverse": "E31CBF00",
            "Format Scroll": "EC144040",
            "Function Green": "EC0A4040",
            "Function Yellow": "EC414040",
            "Function Red": "EC574040",
            "Function Blue": "EC544040",
            "Home": "EC1A4040",
            "Info": "EC444040",
            "Menu": "EC454040",
            "Mouse": "EC474040",
            "Mute": "EC434040",
            "Page Down": "EC204040",
            "Page Up": "EC404040",
            "Next": "EC1E4040",
            "Previous": "EC1F4040",
            "Play/Pause": "EC534040",
            "Power Toggle": "EC4D4040",
            "Power Off": "ECB54040",
            "Power On": "ECB34040",
            "Repeat": "EC464040",
            "Return": "EC424040",
            "R_video": "EC134040",
            "Subtitle": "EC1B4040",
            "Volume Down": "EC174040",
            "Volume Up": "EC184040",
            "Zoom": "EC1D4040",
            "Stop": "EC424040",
            "60 sec forward": "EC114040",
            "60 sec rewind": "EC104040",
            "10 sec forward": "EC404040",
            "10 sec rewind": "EC204040",
            "HDMI/XMOS Audio Toggle": "BA45BF00"
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.device_config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def test_connection(self) -> bool:
        try:
            session = await self._get_session()
            async with session.get(f"{self._base_url}/") as response:
                success = response.status == 200
                _LOG.debug(f"Connection test for {self.device_config.name}: {'success' if success else 'failed'}")
                return success
        except Exception as e:
            _LOG.debug(f"Connection test failed for {self.device_config.name}: {e}")
            return False
    
    async def get_device_info(self) -> Optional[Dict[str, Any]]:
        try:
            session = await self._get_session()
            async with session.get(f"{self._base_url}/device/info") as response:
                if response.status == 200:
                    data = await response.json()
                    _LOG.debug(f"Retrieved device info for {self.device_config.name}")
                    return data
                else:
                    _LOG.debug(f"Device info not available for {self.device_config.name} (status: {response.status})")
                    return None
        except Exception as e:
            _LOG.debug(f"Failed to get device info for {self.device_config.name}: {e}")
            return None
    
    async def get_device_status(self) -> Optional[Dict[str, Any]]:
        try:
            session = await self._get_session()
            async with session.get(f"{self._base_url}/device/status") as response:
                if response.status == 200:
                    data = await response.json()
                    _LOG.debug(f"Retrieved device status for {self.device_config.name}")
                    return data
                else:
                    _LOG.debug(f"Device status not available for {self.device_config.name} (status: {response.status})")
                    return None
        except Exception as e:
            _LOG.debug(f"Failed to get device status for {self.device_config.name}: {e}")
            return None
    
    async def send_ir_command(self, command: str) -> bool:
        if command not in self._ir_codes:
            raise CommandError(f"Unknown command: {command}")
        
        ir_code = self._ir_codes[command]
        url = f"{self._base_url}/cgi-bin/do"
        params = {
            "cmd": "ir_code",
            "ir_code": ir_code
        }
        
        try:
            session = await self._get_session()
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    _LOG.debug(f"Sent command '{command}' (IR: {ir_code}) to {self.device_config.name}")
                    return True
                else:
                    _LOG.warning(f"Command failed for {self.device_config.name}: HTTP {response.status}")
                    return False
        except asyncio.TimeoutError:
            _LOG.warning(f"Command timeout for {self.device_config.name}: {command}")
            raise ConnectionError(f"Timeout sending command to {self.device_config.name}")
        except Exception as e:
            _LOG.error(f"Command error for {self.device_config.name}: {e}")
            raise ConnectionError(f"Failed to send command to {self.device_config.name}: {e}")
    
    async def power_on(self) -> bool:
        return await self.send_ir_command("Power On")
    
    async def power_off(self) -> bool:
        return await self.send_ir_command("Power Off")
    
    async def power_toggle(self) -> bool:
        return await self.send_ir_command("Power Toggle")
    
    async def play_pause(self) -> bool:
        return await self.send_ir_command("Play/Pause")
    
    async def stop(self) -> bool:
        return await self.send_ir_command("Stop")
    
    async def next_track(self) -> bool:
        return await self.send_ir_command("Next")
    
    async def previous_track(self) -> bool:
        return await self.send_ir_command("Previous")
    
    async def volume_up(self) -> bool:
        return await self.send_ir_command("Volume Up")
    
    async def volume_down(self) -> bool:
        return await self.send_ir_command("Volume Down")
    
    async def mute(self) -> bool:
        return await self.send_ir_command("Mute")
    
    async def navigate_up(self) -> bool:
        return await self.send_ir_command("Cursor Up")
    
    async def navigate_down(self) -> bool:
        return await self.send_ir_command("Cursor Down")
    
    async def navigate_left(self) -> bool:
        return await self.send_ir_command("Cursor Left")
    
    async def navigate_right(self) -> bool:
        return await self.send_ir_command("Cursor Right")
    
    async def navigate_enter(self) -> bool:
        return await self.send_ir_command("Cursor Enter")
    
    async def go_home(self) -> bool:
        return await self.send_ir_command("Home")
    
    async def menu(self) -> bool:
        return await self.send_ir_command("Menu")
    
    async def back(self) -> bool:
        return await self.send_ir_command("Return")
    
    async def info(self) -> bool:
        return await self.send_ir_command("Info")
    
    async def send_digit(self, digit: int) -> bool:
        if not 0 <= digit <= 9:
            raise CommandError(f"Invalid digit: {digit}. Must be 0-9")
        return await self.send_ir_command(f"Digit {digit}")
    
    async def send_color_function(self, color: str) -> bool:
        color_commands = {
            "red": "Function Red",
            "green": "Function Green", 
            "yellow": "Function Yellow",
            "blue": "Function Blue"
        }
        
        if color.lower() not in color_commands:
            raise CommandError(f"Invalid color: {color}. Must be red, green, yellow, or blue")
        
        return await self.send_ir_command(color_commands[color.lower()])
    
    async def fast_forward(self) -> bool:
        return await self.send_ir_command("Fast Forward")
    
    async def fast_reverse(self) -> bool:
        return await self.send_ir_command("Fast Reverse")
    
    async def skip_forward_10s(self) -> bool:
        return await self.send_ir_command("10 sec forward")
    
    async def skip_reverse_10s(self) -> bool:
        return await self.send_ir_command("10 sec rewind")
    
    async def skip_forward_60s(self) -> bool:
        return await self.send_ir_command("60 sec forward")
    
    async def skip_reverse_60s(self) -> bool:
        return await self.send_ir_command("60 sec rewind")
    
    async def toggle_subtitles(self) -> bool:
        return await self.send_ir_command("Subtitle")
    
    async def toggle_audio_track(self) -> bool:
        return await self.send_ir_command("Audio")
    
    async def toggle_repeat(self) -> bool:
        return await self.send_ir_command("Repeat")
    
    async def zoom(self) -> bool:
        return await self.send_ir_command("Zoom")
    
    async def page_up(self) -> bool:
        return await self.send_ir_command("Page Up")
    
    async def page_down(self) -> bool:
        return await self.send_ir_command("Page Down")
    
    def get_available_commands(self) -> list[str]:
        return list(self._ir_codes.keys())
    
    def get_ir_code(self, command: str) -> Optional[str]:
        return self._ir_codes.get(command)
    
    @property
    def device_name(self) -> str:
        return self.device_config.name
    
    @property
    def device_id(self) -> str:
        return self.device_config.device_id
    
    @property
    def device_type(self) -> DeviceType:
        return self.device_config.device_type
    
    @property
    def base_url(self) -> str:
        return self._base_url