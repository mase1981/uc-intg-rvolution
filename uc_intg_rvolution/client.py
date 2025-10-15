"""
R_volution Device Client Implementation

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import json
import logging
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

import aiohttp

from uc_intg_rvolution.config import DeviceConfig, DeviceType

_LOG = logging.getLogger(__name__)


class ConnectionError(Exception):
    """Connection-related error."""
    pass


class CommandError(Exception):
    """Command execution error."""
    pass


class RvolutionClient:

    def __init__(self, device_config: DeviceConfig):
        """Initialize R_volution client."""
        self._device_config = device_config
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time = 0
        self._min_request_interval = 1.0
        self._max_retries = 1
        self._base_timeout = 10
        self.connection_established = False
        self._last_successful_request = 0
        self._rvideo_available = None  # Track R_video API availability
        
        # Device-specific command sets
        self._amlogic_commands = {
            "Power On": "4CB34040",
            "Power Off": "4AB54040", 
            "Power Toggle": "B24D4040",
            "Play/Pause": "AC534040",
            "Stop": "BD424040",
            "Next": "E11E4040",
            "Previous": "E01F4040",
            "Fast Forward": "E41BBF00",
            "Fast Reverse": "E31CBF00",
            "Volume Up": "E7184040",
            "Volume Down": "E8174040",
            "Mute": "BC434040",
            "Cursor Up": "F40B4040",
            "Cursor Down": "F10E4040",
            "Cursor Left": "EF104040", 
            "Cursor Right": "EE114040",
            "Cursor Enter": "F20D4040",
            "Home": "E51A4040",
            "Menu": "BA454040",
            "Return": "BD424040",
            "Info": "BB444040",
            "10 sec forward": "BF404040",
            "10 sec rewind": "DF204040",
            "60 sec forward": "EE114040",
            "60 sec rewind": "EF104040",
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
            "Function Red": "A68E4040",
            "Function Green": "F50A4040",
            "Function Yellow": "BE414040",
            "Function Blue": "AB544040",
            "3D": "ED124040",
            "Audio": "E6194040",
            "Subtitle": "E41B4040",
            "Zoom": "E21D4040",
            "Repeat": "B9464040",
            "Page Up": "BF404040",
            "Page Down": "DB204040",
            "Delete": "F30C4040",
            "Dimmer": "A45B4040",
            "Explorer": "EA164040",
            "Format Scroll": "EB144040",
            "R_video": "EC134040"
        }
        
        self._player_commands = {
            "Power On": "ECB34040",
            "Power Off": "ECB54040",
            "Power Toggle": "EC4D4040", 
            "Play/Pause": "EC534040",
            "Stop": "EC424040",
            "Next": "EC1E4040",
            "Previous": "EC1F4040",
            "Fast Forward": "E41BBF00",
            "Fast Reverse": "E31CBF00",
            "Volume Up": "EC184040",
            "Volume Down": "EC174040",
            "Mute": "EC434040",
            "Cursor Up": "EC0B4040",
            "Cursor Down": "EC0E4040",
            "Cursor Left": "EC104040",
            "Cursor Right": "EC114040", 
            "Cursor Enter": "EC0D4040",
            "Home": "EC1A4040",
            "Menu": "EC454040",
            "Return": "EC424040",
            "Info": "EC444040",
            "10 sec forward": "EC404040",
            "10 sec rewind": "EC204040",
            "60 sec forward": "EC114040",
            "60 sec rewind": "EC104040",
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
            "Function Red": "EC574040",
            "Function Green": "EC0A4040",
            "Function Yellow": "EC414040",
            "Function Blue": "EC544040",
            "3D": "EC124040",
            "Audio": "EC194040",
            "Subtitle": "EC1B4040",
            "Zoom": "EC1D4040",
            "Repeat": "EC464040",
            "Page Up": "EC404040",
            "Page Down": "EC204040",
            "Delete": "EC0C4040",
            "Dimmer": "EC5B4040",
            "Explorer": "EC164040",
            "Format Scroll": "EC144040",
            "Mouse": "EC474040",
            "HDMI/XMOS Audio Toggle": "BA45BF00"
        }

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self):
        """Ensure HTTP session with device-friendly settings."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=1,
                limit_per_host=1,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True,
                force_close=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=self._base_timeout,
                connect=5,
                sock_read=8
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'UC-Integration-RVolution/1.0.12',
                    'Accept': '*/*',
                    'Connection': 'close'
                }
            )

    async def close(self):
        """Close HTTP session with proper cleanup."""
        if self._session and not self._session.closed:
            await self._session.close()
            await asyncio.sleep(0.25)

    async def _http_request(self, url: str, method: str = "GET", retry_count: int = 0) -> Optional[str]:
        await self._ensure_session()
        
        # Rate limiting for device stability
        time_since_last = time.time() - self._last_request_time
        if time_since_last < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - time_since_last)
        
        self._last_request_time = time.time()
        
        try:
            # Use appropriate HTTP method
            if method.upper() == "POST":
                request = self._session.post(url, ssl=False)
            else:
                request = self._session.get(url, ssl=False)
            
            async with request as response:
                content = await response.text()
                
                if response.status == 200:
                    self.connection_established = True
                    self._last_successful_request = time.time()
                    return content
                else:
                    _LOG.warning(f"HTTP {response.status} from {self._device_config.ip_address}")
                    if retry_count < self._max_retries:
                        await asyncio.sleep(2.0)
                        return await self._http_request(url, method, retry_count + 1)
                    return None
                    
        except aiohttp.ClientConnectorError as e:
            _LOG.error(f"Connection failed to {self._device_config.ip_address}: {e}")
            self.connection_established = False
            
            if retry_count < self._max_retries:
                _LOG.info(f"Retrying connection after device recovery delay...")
                await asyncio.sleep(5.0)
                await self.close()
                await self._ensure_session()
                return await self._http_request(url, method, retry_count + 1)
            else:
                raise ConnectionError(f"Failed to connect after {self._max_retries + 1} attempts")
                
        except asyncio.TimeoutError:
            _LOG.warning(f"Request timeout to {self._device_config.ip_address}")
            self.connection_established = False
            
            if retry_count < self._max_retries:
                await asyncio.sleep(3.0)
                return await self._http_request(url, method, retry_count + 1)
            else:
                raise ConnectionError(f"Request timeout after {self._max_retries + 1} attempts")
                
        except Exception as e:
            _LOG.error(f"Unexpected error requesting {url}: {e}")
            self.connection_established = False
            raise ConnectionError(f"Unexpected error: {e}")

    def _build_ir_url(self, endpoint: str) -> str:
        """Build URL for IR commands (port 80 or configured port)."""
        port = getattr(self._device_config, 'port', 80)
        return f"http://{self._device_config.ip_address}:{port}{endpoint}"

    def _build_rvideo_url(self, endpoint: str) -> str:
        """Build URL for R_video API (always port 8990)."""
        return f"http://{self._device_config.ip_address}:8990{endpoint}"

    async def test_connection(self) -> bool:
        """Test device connectivity using non-disruptive Info command."""
        try:
            _LOG.info(f"Testing connection to {self._device_config.name}")
            
            # Use Info command for testing - non-disruptive and reliable
            if self._device_config.device_type == DeviceType.AMLOGIC:
                test_ir_code = self._amlogic_commands["Info"]
            else:
                test_ir_code = self._player_commands["Info"]
            
            url = self._build_ir_url(f"/cgi-bin/do?cmd=ir_code&ir_code={test_ir_code}")
            response = await self._http_request(url, method="GET")
            
            if response is not None:
                # Check for valid R_volution response indicators
                success_indicators = [
                    'command_status" value="ok"',
                    'command_status" value="failed"',
                    '<r>',
                    'status=',
                    'result='
                ]
                
                has_valid_response = any(indicator in response for indicator in success_indicators)
                
                if has_valid_response:
                    _LOG.info(f"Connection test passed for {self._device_config.name}")
                    self.connection_established = True
                    return True
                else:
                    _LOG.warning(f"Connection test inconclusive for {self._device_config.name}")
                    return False
            else:
                _LOG.warning(f"Connection test failed for {self._device_config.name}")
                return False
                
        except ConnectionError as e:
            _LOG.error(f"Connection test failed for {self._device_config.name}: {e}")
            self.connection_established = False
            return False
        except Exception as e:
            _LOG.error(f"Connection test error for {self._device_config.name}: {e}")
            self.connection_established = False
            return False

    async def get_playback_information(self) -> Optional[Dict[str, Any]]:
        try:
            url = self._build_rvideo_url("/PlaybackInformation")
            _LOG.debug(f"Requesting playback info via POST: {url}")
            response = await self._http_request(url, method="POST")
            
            if not response:
                return None
            
            # Parse JSON wrapper
            json_data = json.loads(response)
            xml_content = json_data.get('XmlContent', '')
            
            if not xml_content:
                _LOG.debug("No XML content in PlaybackInformation response")
                return None
            
            # Parse XML (JSON automatically unescapes \u003C to <)
            root = ET.fromstring(xml_content)
            
            # Extract all params into dictionary
            playback_info = {}
            for param in root.findall('.//param'):
                name = param.get('name')
                value = param.get('value')
                if name and value:
                    playback_info[name] = value
            
            _LOG.debug(f"Playback info retrieved: player_state={playback_info.get('player_state')}, "
                      f"playback_state={playback_info.get('playback_state')}")
            
            return playback_info
            
        except json.JSONDecodeError as e:
            _LOG.debug(f"Failed to parse PlaybackInformation JSON: {e}")
            return None
        except ET.ParseError as e:
            _LOG.debug(f"Failed to parse PlaybackInformation XML: {e}")
            return None
        except Exception as e:
            _LOG.debug(f"Error getting playback information: {e}")
            return None

    async def get_last_media(self) -> Optional[Dict[str, Any]]:
        try:
            url = self._build_rvideo_url("/LastMedia")
            _LOG.debug(f"Requesting last media via POST: {url}")
            response = await self._http_request(url, method="POST")
            
            if not response:
                return None
            
            # Parse JSON
            media_data = json.loads(response)
            
            # Check for error
            if media_data.get('ErrorCode') != 'None':
                _LOG.debug(f"LastMedia returned error: {media_data.get('ErrorCode')}")
                return None
            
            # Extract media info
            media = media_data.get('Media')
            if not media:
                _LOG.debug("No media data in LastMedia response")
                return None
            
            _LOG.debug(f"Media info retrieved: Title={media.get('Title')}, "
                      f"Type={media.get('Type')}, "
                      f"TvShowName={media.get('TvShowName')}")
            
            return media
            
        except json.JSONDecodeError as e:
            _LOG.debug(f"Failed to parse LastMedia JSON: {e}")
            return None
        except Exception as e:
            _LOG.debug(f"Error getting last media: {e}")
            return None

    async def get_enhanced_status(self) -> Optional[Dict[str, Any]]:
        if self._rvideo_available is None:
            _LOG.info(f"Testing R_video API availability for {self._device_config.name}...")
            playback_test = await self.get_playback_information()
            if playback_test is None:
                _LOG.info(f"R_video API not available for {self._device_config.name} - enhanced status disabled")
                self._rvideo_available = False
                return None
            else:
                _LOG.info(f"R_video API available for {self._device_config.name} - enhanced status enabled")
                self._rvideo_available = True
        
        if self._rvideo_available is False:
            return None
        
        try:
            # Get both playback info and media metadata
            playback_info = await self.get_playback_information()
            
            if not playback_info:
                return None
            
            # Check if currently playing media
            player_state = playback_info.get('player_state', '')
            is_playing = player_state == 'file_playback'
            
            # Only get media metadata if actually playing
            media = None
            if is_playing:
                media = await self.get_last_media()
            
            enhanced_status = {
                'playback_info': playback_info,
                'media': media,
                'is_playing': is_playing,
                'player_state': player_state
            }
            
            return enhanced_status
            
        except Exception as e:
            _LOG.debug(f"Error getting enhanced status: {e}")
            return None

    async def send_ir_command(self, command: str) -> bool:
        """Send IR command to device."""
        try:
            if self._device_config.device_type == DeviceType.AMLOGIC:
                command_set = self._amlogic_commands
            else:
                command_set = self._player_commands
            
            if command not in command_set:
                _LOG.error(f"Unknown command '{command}' for device type {self._device_config.device_type}")
                return False
            
            ir_code = command_set[command]
            url = self._build_ir_url(f"/cgi-bin/do?cmd=ir_code&ir_code={ir_code}")
            
            _LOG.debug(f"Sending IR command '{command}' to {self._device_config.name}")
            
            response = await self._http_request(url, method="GET")
            
            if response is not None:
                # Check for success indicators in response
                success_indicators = [
                    'command_status" value="ok"',
                    '<r>ok</r>',
                    'status=ok'
                ]
                
                has_success = any(indicator in response for indicator in success_indicators)
                
                if has_success:
                    _LOG.debug(f"IR command '{command}' successful")
                    return True
                else:
                    _LOG.debug(f"IR command '{command}' executed (device responded)")
                    return True  # Device responded, assume success
            else:
                _LOG.error(f"No response for IR command '{command}'")
                return False
                
        except ConnectionError as e:
            _LOG.error(f"Connection error for command '{command}': {e}")
            return False
        except Exception as e:
            _LOG.error(f"Error sending command '{command}': {e}")
            return False

    async def power_on(self) -> bool:
        """Send power on command."""
        return await self.send_ir_command("Power On")

    async def power_off(self) -> bool:
        """Send power off command."""
        return await self.send_ir_command("Power Off")

    async def power_toggle(self) -> bool:
        """Send power toggle command."""
        return await self.send_ir_command("Power Toggle")

    async def play_pause(self) -> bool:
        """Send play/pause command."""
        return await self.send_ir_command("Play/Pause")

    async def stop(self) -> bool:
        """Send stop command."""
        return await self.send_ir_command("Stop")

    async def next_track(self) -> bool:
        """Send next track command."""
        return await self.send_ir_command("Next")

    async def previous_track(self) -> bool:
        """Send previous track command."""
        return await self.send_ir_command("Previous")

    async def volume_up(self) -> bool:
        """Send volume up command."""
        return await self.send_ir_command("Volume Up")

    async def volume_down(self) -> bool:
        """Send volume down command."""
        return await self.send_ir_command("Volume Down")

    async def mute(self) -> bool:
        """Send mute command."""
        return await self.send_ir_command("Mute")

    async def get_device_status(self) -> Optional[Dict[str, Any]]:
        try:
            # Try enhanced status first (R_video API)
            enhanced = await self.get_enhanced_status()
            if enhanced:
                return enhanced
            
            # Fallback to basic status endpoints
            status_urls = [
                self._build_ir_url("/device/status"),
                self._build_ir_url("/device/info"),
                self._build_ir_url("/as/system/information")
            ]
            
            for url in status_urls:
                try:
                    response = await self._http_request(url, method="GET")
                    if response and response.strip().startswith('{'):
                        status_data = json.loads(response)
                        _LOG.debug(f"Device status retrieved from {url}")
                        return status_data
                except Exception as e:
                    _LOG.debug(f"Status URL {url} failed: {e}")
                    continue
            
            _LOG.debug(f"No status information available for {self._device_config.name}")
            return None
            
        except Exception as e:
            _LOG.debug(f"Status check error: {e}")
            return None

    def get_available_commands(self) -> List[str]:
        """Get list of available commands for this device type."""
        if self._device_config.device_type == DeviceType.AMLOGIC:
            return list(self._amlogic_commands.keys())
        else:
            return list(self._player_commands.keys())

    @property
    def device_config(self) -> DeviceConfig:
        """Get device configuration."""
        return self._device_config

    @property
    def device_name(self) -> str:
        """Get device name."""
        return self._device_config.name

    @property
    def device_ip(self) -> str:
        """Get device IP address."""
        return self._device_config.ip_address