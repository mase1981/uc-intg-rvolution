"""
R_volution Device Client Implementation

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
import time
import socket
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
        self._min_request_interval = 1.0  # Increased for device stability
        self._max_retries = 1  # Reduced to avoid device overload
        self._base_timeout = 10  # Increased timeout
        self.connection_established = False
        self._last_successful_request = 0
        
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

    async def _diagnostic_ping(self) -> bool:
        """Diagnostic: Test raw TCP connectivity."""
        try:
            _LOG.info(f"🔍 DIAGNOSTIC: Testing TCP connectivity to {self._device_config.ip_address}:80")
            
            # Test basic TCP connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._device_config.ip_address, 80),
                timeout=5.0
            )
            writer.close()
            await writer.wait_closed()
            
            _LOG.info(f"✅ DIAGNOSTIC: TCP connection successful to {self._device_config.ip_address}")
            return True
            
        except asyncio.TimeoutError:
            _LOG.error(f"❌ DIAGNOSTIC: TCP timeout to {self._device_config.ip_address}")
            return False
        except Exception as e:
            _LOG.error(f"❌ DIAGNOSTIC: TCP connection failed to {self._device_config.ip_address}: {e}")
            return False

    async def _ensure_session(self):
        """Ensure HTTP session with conservative settings for device stability."""
        if self._session is None or self._session.closed:
            _LOG.info(f"🔄 Creating new HTTP session for {self._device_config.ip_address}")
            
            connector = aiohttp.TCPConnector(
                limit=1,              # Only 1 connection total
                limit_per_host=1,     # Only 1 connection per host
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True,
                force_close=True      # Close after each request
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
                    'User-Agent': 'UC-Integration-RVolution/1.0.11-DIAGNOSTIC',
                    'Accept': '*/*',
                    'Connection': 'close'  # Force connection close
                }
            )
            
            _LOG.debug(f"📡 HTTP session created for {self._device_config.ip_address}")

    async def close(self):
        """Close HTTP session with proper cleanup."""
        if self._session and not self._session.closed:
            _LOG.debug(f"🔒 Closing HTTP session for {self._device_config.ip_address}")
            await self._session.close()
            await asyncio.sleep(0.25)  # Extended cleanup time

    async def _throttled_request(self, url: str, retry_count: int = 0) -> Optional[str]:
        """Make throttled HTTP request with extensive diagnostics."""
        await self._ensure_session()
        
        # throttling for device stability
        time_since_last = time.time() - self._last_request_time
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            _LOG.debug(f"⏳ Throttling: sleeping {sleep_time:.2f}s for device stability")
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = time.time()
        
        # Step 1: Test TCP connectivity first
        tcp_ok = await self._diagnostic_ping()
        if not tcp_ok:
            _LOG.error(f"❌ TCP connectivity failed, aborting HTTP request to {url}")
            raise ConnectionError("TCP connectivity test failed")
        
        try:
            _LOG.info(f"📡 HTTP Request attempt {retry_count + 1}: {url}")
            
            # Step 2: Make HTTP request with detailed logging
            async with self._session.get(url, ssl=False) as response:
                content = await response.text()
                
                _LOG.info(f"📨 HTTP Response: Status={response.status}, Length={len(content)}, Content-Type={response.headers.get('content-type', 'unknown')}")
                _LOG.debug(f"📄 Response content (first 200 chars): {content[:200]}")
                
                if response.status == 200:
                    self.connection_established = True
                    self._last_successful_request = time.time()
                    _LOG.info(f"✅ HTTP request successful to {self._device_config.ip_address}")
                    return content
                else:
                    _LOG.warning(f"⚠️ HTTP {response.status} from {self._device_config.ip_address}")
                    if retry_count < self._max_retries:
                        await asyncio.sleep(2.0)
                        return await self._throttled_request(url, retry_count + 1)
                    return None
                    
        except aiohttp.ClientConnectorError as e:
            error_msg = str(e)
            _LOG.error(f"🔌 Connection error to {self._device_config.ip_address}: {error_msg}")
            self.connection_established = False
            
            # Detailed diagnosis
            if "Connect call failed" in error_msg:
                _LOG.error(f"🔍 DIAGNOSIS: Device {self._device_config.ip_address} is not accepting connections")
                _LOG.error(f"🔍 DIAGNOSIS: Possible causes:")
                _LOG.error(f"   - Device is in standby/sleep mode")
                _LOG.error(f"   - Device network interface reset after IR command")
                _LOG.error(f"   - Device firewall blocking connections")
                _LOG.error(f"   - Device overload from previous requests")
            
            # Wait longer before retry for device recovery
            if retry_count < self._max_retries:
                recovery_time = 5.0  # Extended recovery time
                _LOG.info(f"⏰ Waiting {recovery_time}s for device recovery before retry...")
                await asyncio.sleep(recovery_time)
                
                # Close and recreate session for clean retry
                await self.close()
                await self._ensure_session()
                return await self._throttled_request(url, retry_count + 1)
            else:
                raise ConnectionError(f"Failed to connect after {self._max_retries + 1} attempts: {error_msg}")
                
        except asyncio.TimeoutError:
            _LOG.warning(f"⏱️ Request timeout to {self._device_config.ip_address}")
            self.connection_established = False
            
            if retry_count < self._max_retries:
                await asyncio.sleep(3.0)
                return await self._throttled_request(url, retry_count + 1)
            else:
                raise ConnectionError(f"Request timeout after {self._max_retries + 1} attempts")
                
        except Exception as e:
            _LOG.error(f"💥 Unexpected error requesting {url}: {e}")
            self.connection_established = False
            raise ConnectionError(f"Unexpected error: {e}")

    def _build_url(self, endpoint: str) -> str:
        port = getattr(self._device_config, 'port', 80)
        return f"http://{self._device_config.ip_address}:{port}{endpoint}"

    async def test_connection(self) -> bool:
        """Test connection with comprehensive diagnostics."""
        try:
            _LOG.info(f"🧪 TESTING CONNECTION to {self._device_config.name} ({self._device_config.ip_address})")
            
            # Step 1: Basic device info
            time_since_last_success = time.time() - self._last_successful_request if self._last_successful_request > 0 else "never"
            _LOG.info(f"📊 Device info: Type={self._device_config.device_type.value}, Last success={time_since_last_success}")
            
            # Step 2: Select test command (use gentler command than Power Toggle)
            if self._device_config.device_type == DeviceType.AMLOGIC:
                test_ir_code = self._amlogic_commands["Info"]  # Less disruptive than Power Toggle
                test_command = "Info"
            else:
                test_ir_code = self._player_commands["Info"]
                test_command = "Info"
            
            url = self._build_url(f"/cgi-bin/do?cmd=ir_code&ir_code={test_ir_code}")
            
            _LOG.info(f"🎯 Testing with command: {test_command} (IR: {test_ir_code})")
            _LOG.info(f"🌐 Test URL: {url}")
            
            # Step 3: Execute test request
            response = await self._throttled_request(url)
            
            if response is not None:
                # Step 4: Analyze response
                success_indicators = [
                    'command_status" value="ok"',
                    'command_status" value="failed"',  # Device responds but rejects command
                    '<r>',
                    'status=',
                    'result='
                ]
                
                has_valid_response = any(indicator in response for indicator in success_indicators)
                
                if has_valid_response:
                    _LOG.info(f"✅ CONNECTION TEST PASSED for {self._device_config.name}")
                    _LOG.info(f"📈 Response analysis: Valid R_volution response detected")
                    self.connection_established = True
                    return True
                else:
                    _LOG.warning(f"⚠️ CONNECTION TEST INCONCLUSIVE for {self._device_config.name}")
                    _LOG.warning(f"📝 Response doesn't match expected R_volution format")
                    _LOG.warning(f"🔍 Raw response: {response[:500]}")
                    return False
            else:
                _LOG.error(f"❌ CONNECTION TEST FAILED - No response from {self._device_config.name}")
                return False
                
        except ConnectionError as e:
            _LOG.error(f"❌ CONNECTION TEST FAILED for {self._device_config.name}: {e}")
            self.connection_established = False
            return False
        except Exception as e:
            _LOG.error(f"💥 CONNECTION TEST ERROR for {self._device_config.name}: {e}")
            self.connection_established = False
            return False

    async def send_ir_command(self, command: str) -> bool:
        """Send IR command with extensive diagnostics."""
        try:
            _LOG.info(f"🎮 SENDING IR COMMAND: '{command}' to {self._device_config.name}")
            
            if self._device_config.device_type == DeviceType.AMLOGIC:
                command_set = self._amlogic_commands
            else:
                command_set = self._player_commands
            
            if command not in command_set:
                _LOG.error(f"❌ Unknown command '{command}' for device type {self._device_config.device_type}")
                return False
            
            ir_code = command_set[command]
            url = self._build_url(f"/cgi-bin/do?cmd=ir_code&ir_code={ir_code}")
            
            _LOG.info(f"📡 IR Command details: {command} → {ir_code}")
            _LOG.debug(f"🌐 Command URL: {url}")
            
            response = await self._throttled_request(url)
            
            if response is not None:
                # Analyze command response
                success_indicators = [
                    'command_status" value="ok"',
                    '<r>ok</r>',
                    'status=ok'
                ]
                
                failure_indicators = [
                    'command_status" value="failed"',
                    '<r>failed</r>',
                    'status=failed'
                ]
                
                has_success = any(indicator in response for indicator in success_indicators)
                has_failure = any(indicator in response for indicator in failure_indicators)
                
                if has_success:
                    _LOG.info(f"✅ IR COMMAND SUCCESS: '{command}' executed on {self._device_config.name}")
                    return True
                elif has_failure:
                    _LOG.warning(f"⚠️ IR COMMAND REJECTED: '{command}' by {self._device_config.name}")
                    _LOG.warning(f"📝 Device rejected the command but is responding")
                    return True  # Device is responding, command format is correct
                else:
                    _LOG.warning(f"❓ IR COMMAND UNCERTAIN: '{command}' response unclear")
                    _LOG.debug(f"📄 Response: {response[:200]}")
                    return True  # Any response indicates device is working
            else:
                _LOG.error(f"❌ IR COMMAND FAILED: No response for '{command}'")
                return False
                
        except ConnectionError as e:
            _LOG.error(f"🔌 IR COMMAND CONNECTION ERROR for '{command}': {e}")
            return False
        except Exception as e:
            _LOG.error(f"💥 IR COMMAND ERROR for '{command}': {e}")
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
        """Get device status information with diagnostics."""
        try:
            _LOG.debug(f"🔍 Checking device status for {self._device_config.name}")
            
            status_urls = [
                self._build_url("/device/status"),
                self._build_url("/device/info"),
                self._build_url("/as/system/information")
            ]
            
            for url in status_urls:
                try:
                    response = await self._throttled_request(url)
                    if response and response.strip().startswith('{'):
                        import json
                        status_data = json.loads(response)
                        _LOG.info(f"📊 Device status retrieved from {url}")
                        return status_data
                except Exception as e:
                    _LOG.debug(f"🔍 Status URL {url} failed: {e}")
                    continue
            
            _LOG.debug(f"📊 No status information available for {self._device_config.name}")
            return None
            
        except Exception as e:
            _LOG.debug(f"📊 Status check error: {e}")
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