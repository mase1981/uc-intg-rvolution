"""
R_volution Device Client Implementation.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
import ssl
import time
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
    """Client for interacting with R_volution devices via HTTP API."""

    def __init__(self, device_config: DeviceConfig):
        """Initialize R_volution client with complete SSL fix."""
        self._device_config = device_config
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time = 0
        self._min_request_interval = 0.3  # Reduced to 300ms for better responsiveness
        self._max_retries = 2
        self._base_timeout = 8  # Reduced timeout for faster feedback
        self._connection_established = False
        
        # Device-specific command sets (unchanged)
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
        """Ensure HTTP session with COMPLETE SSL fix."""
        if self._session is None or self._session.closed:
            # Create explicit SSL context that disables SSL entirely
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(
                limit=1,
                limit_per_host=1,
                force_close=True,
                enable_cleanup_closed=True,
                ssl=None,  # Changed from False to None for complete SSL disable
                use_dns_cache=False,  # Disable DNS caching for better reliability
                ttl_dns_cache=0
            )
            
            timeout = aiohttp.ClientTimeout(
                total=self._base_timeout,
                connect=3,
                sock_read=5
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'UC-Integration-RVolution/1.0.8',
                    'Connection': 'close',
                    'Accept': '*/*'
                }
            )
            _LOG.debug("HTTP session created with SSL completely disabled")

    async def close(self):
        """Close HTTP session and cleanup resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            await asyncio.sleep(0.1)
            self._session = None
        self._connection_established = False

    async def _throttled_request(self, url: str, retry_count: int = 0) -> Optional[str]:
        """Make throttled HTTP request with complete SSL fix."""
        await self._ensure_session()
        
        # Enforce minimum time between requests
        time_since_last = time.time() - self._last_request_time
        if time_since_last < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - time_since_last)
        
        self._last_request_time = time.time()
        
        try:
            _LOG.debug(f"Making HTTP request to: {url}")
            
            if url.startswith('https://'):
                url = url.replace('https://', 'http://')
                _LOG.warning("Forced HTTPS to HTTP conversion")
            
            async with self._session.get(url) as response:
                content = await response.text()
                
                if response.status == 200:
                    self._connection_established = True
                    _LOG.debug(f"Request successful: {response.status}")
                    return content
                else:
                    _LOG.warning(f"HTTP {response.status} from {self._device_config.ip_address}")
                    if retry_count < self._max_retries:
                        await asyncio.sleep(0.5)
                        return await self._throttled_request(url, retry_count + 1)
                    return None
                    
        except (aiohttp.ClientConnectorError, aiohttp.ClientError, aiohttp.ClientSSLError) as e:
            error_msg = str(e)
            _LOG.error(f"Connection error to {self._device_config.ip_address}: {error_msg}")
            
            # Force session recreation on any SSL or connection error
            if 'ssl' in error_msg.lower() or 'certificate' in error_msg.lower():
                _LOG.warning("SSL-related error detected, forcing session recreation")
                await self.close()
                await self._ensure_session()
            
            if retry_count < self._max_retries:
                await asyncio.sleep(1.0)
                return await self._throttled_request(url, retry_count + 1)
            else:
                raise ConnectionError(f"Failed to connect after retries: {error_msg}")
                
        except asyncio.TimeoutError:
            _LOG.warning(f"Request timeout to {self._device_config.ip_address}")
            if retry_count < self._max_retries:
                await asyncio.sleep(1.0)
                return await self._throttled_request(url, retry_count + 1)
            else:
                raise ConnectionError("Request timeout after retries")
                
        except Exception as e:
            _LOG.error(f"Unexpected error requesting {url}: {type(e).__name__}: {e}")
            raise ConnectionError(f"Unexpected error: {e}")

    async def test_connection(self) -> bool:
        """Test connection using single lightweight command with race condition prevention."""
        try:
            _LOG.info(f"Testing connection to {self._device_config.name} at {self._device_config.ip_address}")
            
            # Use Power Toggle as the test command - most reliable
            if self._device_config.device_type == DeviceType.AMLOGIC:
                test_ir_code = self._amlogic_commands["Power Toggle"]
            else:
                test_ir_code = self._player_commands["Power Toggle"]
            
            url = f"http://{self._device_config.ip_address}:{self._device_config.port}/cgi-bin/do?cmd=ir_code&ir_code={test_ir_code}"
            
            response = await self._throttled_request(url)
            
            if response and ('command_status" value="ok"' in response or 'command_status" value="failed"' in response):
                self._connection_established = True
                _LOG.info(f"Connection test successful for {self._device_config.name}")
                return True
            else:
                _LOG.warning(f"Connection test failed for {self._device_config.name} - no valid response")
                return False
                
        except ConnectionError as e:
            _LOG.error(f"Connection test failed for {self._device_config.name}: {e}")
            return False
        except Exception as e:
            _LOG.error(f"Unexpected error testing connection to {self._device_config.name}: {e}")
            return False

    async def send_ir_command(self, command: str) -> bool:
        """Send IR command with complete SSL fix and connection state tracking."""
        try:
            if self._device_config.device_type == DeviceType.AMLOGIC:
                command_set = self._amlogic_commands
            else:
                command_set = self._player_commands
            
            if command not in command_set:
                _LOG.warning(f"Unknown command '{command}' for {self._device_config.device_type.value} device")
                return False
            
            ir_code = command_set[command]
            url = f"http://{self._device_config.ip_address}:{self._device_config.port}/cgi-bin/do?cmd=ir_code&ir_code={ir_code}"
            
            _LOG.debug(f"Sending IR command '{command}' ({ir_code}) to {self._device_config.name}")
            
            response = await self._throttled_request(url)
            
            if response and 'command_status" value="ok"' in response:
                _LOG.debug(f"IR command '{command}' successful")
                return True
            elif response and 'command_status" value="failed"' in response:
                _LOG.debug(f"IR command '{command}' failed (device reported failure)")
                return False
            else:
                _LOG.warning(f"IR command '{command}' - unexpected or no response")
                return False
                
        except ConnectionError as e:
            _LOG.error(f"Connection error sending command '{command}': {e}")
            return False
        except Exception as e:
            _LOG.error(f"Unexpected error sending command '{command}': {e}")
            return False

    @property
    def connection_established(self) -> bool:
        """Check if connection has been successfully established."""
        return self._connection_established

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
        """Get device status information (limited availability)."""
        try:
            status_urls = [
                f"http://{self._device_config.ip_address}:{self._device_config.port}/device/status",
                f"http://{self._device_config.ip_address}:{self._device_config.port}/as/system/information"
            ]
            
            for url in status_urls:
                try:
                    response = await self._throttled_request(url)
                    if response and response.startswith('{'):
                        import json
                        return json.loads(response)
                except:
                    continue
            
            return None
            
        except Exception as e:
            _LOG.debug(f"Status request failed for {self._device_config.name}: {e}")
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