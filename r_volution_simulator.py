#!/usr/bin/env python3
"""
R_volution Device Simulator with Multi-Device Support.

Simulates both Amlogic and Player device types with their respective IR code APIs.

:copyright: (c) 2025 by Meir Miyara
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import json
import logging
import random
import socket
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from enum import Enum

from aiohttp import web
from aiohttp.web import Request, Response

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class DeviceType(Enum):
    AMLOGIC = "amlogic"
    PLAYER = "player"


def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


class RvolutionSimulator:
    
    def __init__(self, host: str = None, port: int = 8080, device_name: str = "R_volution-SIM", 
                 device_id: int = 1, device_type: DeviceType = DeviceType.AMLOGIC):
        self.host = host if host else get_local_ip()
        self.port = port
        self.device_name = device_name
        self.device_id = device_id
        self.device_type = device_type
        self.app = web.Application()
        
        # FIXED: Use simple string instead of method call during init
        self.device_state = {
            "power": "on",
            "volume": 50 + (device_id * 5),
            "max_volume": 100,
            "mute": False,
            "input": "hdmi1",  # FIXED: Simple default instead of method call
            "playback": "stop",
            "position": 0,
            "duration": 7200,
            "title": f"Demo Movie {device_id}",
            "subtitle_enabled": False,
            "audio_track": "main",
            "video_format": "4K",
            "repeat": False,
            # ENHANCED: Additional fields for enhanced testing (backward compatible)
            "artist": f"Demo Artist {device_id}",
            "album": f"Demo Album {device_id}",
            "cover_url": f"https://picsum.photos/300/300?random={device_id}"
        }
        
        # ENHANCED: Device info with more realistic data
        if device_type == DeviceType.AMLOGIC:
            self.device_info = {
                "model_name": f"PlayerOne-8K-SIM-{device_id}",
                "device_id": f"AMLOGIC{device_id:03d}",
                "device_type": "amlogic",
                "firmware_version": "2.1.5",
                "supported_formats": ["4K", "HDR", "DolbyVision"],
                "api_type": "amlogic_ir",
                "inputs": ["hdmi1", "hdmi2", "usb", "network", "sd_card"],
                "capabilities": ["repeat", "shuffle", "subtitle", "audio_track"]
            }
            self.ir_codes = self._get_amlogic_ir_codes()
        else:
            self.device_info = {
                "model_name": f"R_volution-Player-SIM-{device_id}",
                "device_id": f"PLAYER{device_id:03d}",
                "device_type": "player",
                "firmware_version": "1.8.2",
                "supported_formats": ["1080p", "4K", "HDR"],
                "api_type": "player_ir",
                "inputs": ["hdmi1", "hdmi2", "usb", "network", "optical"],
                "capabilities": ["repeat", "shuffle", "subtitle", "audio_track", "hdmi_audio_toggle"]
            }
            self.ir_codes = self._get_player_ir_codes()
        
        # ENHANCED: Media library for more realistic testing
        self.media_library = [
            {
                "title": "Inception",
                "artist": "Hans Zimmer",
                "album": "Inception Soundtrack",
                "duration": 8880,
                "cover_url": "https://picsum.photos/300/300?random=1"
            },
            {
                "title": "Interstellar",
                "artist": "Hans Zimmer", 
                "album": "Interstellar Soundtrack",
                "duration": 10320,
                "cover_url": "https://picsum.photos/300/300?random=2"
            },
            {
                "title": "The Dark Knight",
                "artist": "Hans Zimmer & James Newton Howard",
                "album": "The Dark Knight Soundtrack", 
                "duration": 9600,
                "cover_url": "https://picsum.photos/300/300?random=3"
            },
            {
                "title": "Live Stream Radio",
                "artist": "",
                "album": "",
                "duration": 0,  # Live content
                "cover_url": "https://picsum.photos/300/300?random=radio"
            }
        ]
        
        # FIXED: Simple initialization order like original
        self._setup_routes()
        self._position_task: Optional[asyncio.Task] = None
        
        # Set input based on device type AFTER initialization
        if device_type == DeviceType.AMLOGIC:
            self.device_state["input"] = "network" 
        else:
            self.device_state["input"] = "hdmi1"
            
        self._start_position_update()
        
    def _get_default_input(self) -> str:
        """Get default input based on device type."""
        if self.device_type == DeviceType.AMLOGIC:
            return "network"
        else:
            return "hdmi1"
    
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
        
    def _setup_routes(self):
        self.app.router.add_get('/', self.handle_root)
        self.app.router.add_get('/cgi-bin/do', self.handle_ir_command)
        self.app.router.add_get('/device/info', self.get_device_info)
        self.app.router.add_get('/device/status', self.get_device_status)
        # ENHANCED: Additional testing endpoints
        self.app.router.add_get('/device/sources', self.get_device_sources)
        self.app.router.add_get('/device/capabilities', self.get_device_capabilities)
        self.app.router.add_get('/debug/state', self.debug_state)
        self.app.router.add_get('/debug/reset', self.debug_reset)
        self.app.router.add_get('/debug/ir_codes', self.debug_ir_codes)
        self.app.router.add_get('/debug/media_library', self.debug_media_library)
        self.app.router.add_get('/health', self.health_check)
    
    async def handle_root(self, request: Request) -> Response:
        # FIXED: Keep exact same response format as original simulator for compatibility
        return web.json_response({
            "message": f"R_volution {self.device_type.value.title()} Simulator {self.device_id}",
            "device_id": self.device_info["device_id"],
            "model": self.device_info["model_name"],
            "device_name": self.device_name,
            "device_type": self.device_type.value,
            "firmware": self.device_info["firmware_version"],
            "supported_commands": list(self.ir_codes.keys()),
            "api_endpoint": "/cgi-bin/do?cmd=ir_code&ir_code=XXXX",
            "examples": [
                f"/cgi-bin/do?cmd=ir_code&ir_code={self.ir_codes['Power On']}",
                f"/cgi-bin/do?cmd=ir_code&ir_code={self.ir_codes['Play/Pause']}",
                f"/cgi-bin/do?cmd=ir_code&ir_code={self.ir_codes['Volume Up']}"
            ]
        })

    async def health_check(self, request: Request) -> Response:
        return web.json_response({
            "status": "healthy", 
            "device_id": self.device_info["device_id"],
            "device_name": self.device_name,
            "device_type": self.device_type.value
        })

    async def get_device_info(self, request: Request) -> Response:
        return web.json_response({
            "status": "ok",
            **self.device_info
        })

    async def get_device_status(self, request: Request) -> Response:
        # ENHANCED: More comprehensive status response
        status_response = {
            "status": "ok",
            **self.device_state,
            "device_info": self.device_info,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add live stream indicator for duration=0 content
        if self.device_state["duration"] == 0:
            status_response["live_stream"] = True
        
        return web.json_response(status_response)

    # ENHANCED: New endpoint for source testing
    async def get_device_sources(self, request: Request) -> Response:
        return web.json_response({
            "status": "ok",
            "current_input": self.device_state["input"],
            "available_inputs": self.device_info["inputs"],
            "device_functions": ["explorer", "info", "settings"]
        })

    # ENHANCED: New endpoint for capability testing  
    async def get_device_capabilities(self, request: Request) -> Response:
        return web.json_response({
            "status": "ok",
            "capabilities": self.device_info["capabilities"],
            "supported_formats": self.device_info["supported_formats"],
            "api_version": "1.0",
            "enhanced_features": True
        })

    async def handle_ir_command(self, request: Request) -> Response:
        # FIXED: Keep exact same logic as original simulator
        cmd = request.query.get('cmd')
        ir_code = request.query.get('ir_code')
        
        if cmd != 'ir_code':
            return web.json_response({"status": "error", "message": "Invalid command"}, status=400)
        
        if not ir_code:
            return web.json_response({"status": "error", "message": "Missing ir_code parameter"}, status=400)
        
        command_name = None
        for name, code in self.ir_codes.items():
            if code == ir_code:
                command_name = name
                break
        
        if not command_name:
            logger.warning(f"Device {self.device_id}: Unknown IR code received: {ir_code}")
            return web.json_response({"status": "error", "message": f"Unknown IR code: {ir_code}"}, status=404)
        
        # FIXED: Use simple command processing like original
        await self._process_command_simple(command_name)
        
        logger.info(f"Device {self.device_id}: Executed command '{command_name}' (IR: {ir_code})")
        return web.json_response({
            "status": "ok", 
            "command": command_name,
            "ir_code": ir_code,
            "device_id": self.device_info["device_id"]
        })

    async def _process_command_simple(self, command: str) -> None:
        """FIXED: Simple command processing like original simulator."""
        if command == "Power On":
            self.device_state["power"] = "on"
        elif command == "Power Off":
            self.device_state["power"] = "off"
            self.device_state["playback"] = "stop"
        elif command == "Power Toggle":
            self.device_state["power"] = "off" if self.device_state["power"] == "on" else "on"
            if self.device_state["power"] == "off":
                self.device_state["playback"] = "stop"
        
        elif command == "Play/Pause":
            if self.device_state["power"] == "on":
                if self.device_state["playback"] == "play":
                    self.device_state["playback"] = "pause"
                else:
                    self.device_state["playback"] = "play"
        
        elif command == "Stop":
            self.device_state["playback"] = "stop"
            self.device_state["position"] = 0
        
        elif command == "Next":
            await self._change_media()
        elif command == "Previous":
            await self._change_media()
        
        elif command == "Volume Up":
            self.device_state["volume"] = min(100, self.device_state["volume"] + 5)
        elif command == "Volume Down":
            self.device_state["volume"] = max(0, self.device_state["volume"] - 5)
        elif command == "Mute":
            self.device_state["mute"] = not self.device_state["mute"]
        
        # ENHANCED: Keep new functionality but ensure compatibility
        elif command == "Repeat":
            self.device_state["repeat"] = not self.device_state["repeat"]
        
        # Enhanced features for testing
        elif command in ["Function Red", "Function Green", "Function Blue", "Function Yellow"]:
            await self._handle_source_switch(command)

    async def _process_command(self, command: str) -> None:
        """ENHANCED: More comprehensive command processing."""
        # First do simple processing for compatibility
        await self._process_command_simple(command)
        
        # Then add enhanced features
        if command == "Fast Forward":
            self.device_state["position"] = min(self.device_state["duration"], 
                                              self.device_state["position"] + 30)
        elif command == "Fast Reverse":
            self.device_state["position"] = max(0, self.device_state["position"] - 30)
        elif command == "10 sec forward":
            self.device_state["position"] = min(self.device_state["duration"], 
                                              self.device_state["position"] + 10)
        elif command == "10 sec rewind":
            self.device_state["position"] = max(0, self.device_state["position"] - 10)
        elif command == "60 sec forward":
            self.device_state["position"] = min(self.device_state["duration"], 
                                              self.device_state["position"] + 60)
        elif command == "60 sec rewind":
            self.device_state["position"] = max(0, self.device_state["position"] - 60)
        
        elif command == "Subtitle":
            self.device_state["subtitle_enabled"] = not self.device_state["subtitle_enabled"]
        elif command == "Audio":
            tracks = ["main", "commentary", "alternate"]
            current_idx = tracks.index(self.device_state["audio_track"])
            self.device_state["audio_track"] = tracks[(current_idx + 1) % len(tracks)]
        
        elif command == "Explorer":
            self.device_state["input"] = "usb"
            await self._change_media("file_browser")
        # ENHANCED: More comprehensive command processing
        if command == "Power On":
            self.device_state["power"] = "on"
        elif command == "Power Off":
            self.device_state["power"] = "off"
            self.device_state["playback"] = "stop"
            self.device_state["position"] = 0
        elif command == "Power Toggle":
            self.device_state["power"] = "off" if self.device_state["power"] == "on" else "on"
            if self.device_state["power"] == "off":
                self.device_state["playback"] = "stop"
                self.device_state["position"] = 0
        
        elif command == "Play/Pause":
            if self.device_state["power"] == "on":
                if self.device_state["playback"] == "play":
                    self.device_state["playback"] = "pause"
                else:
                    self.device_state["playback"] = "play"
        
        elif command == "Stop":
            self.device_state["playback"] = "stop"
            self.device_state["position"] = 0
        
        elif command == "Next":
            await self._change_media()
        elif command == "Previous":
            await self._change_media()
        
        elif command == "Volume Up":
            self.device_state["volume"] = min(100, self.device_state["volume"] + 5)
        elif command == "Volume Down":
            self.device_state["volume"] = max(0, self.device_state["volume"] - 5)
        elif command == "Mute":
            self.device_state["mute"] = not self.device_state["mute"]
        
        elif command == "Fast Forward":
            self.device_state["position"] = min(self.device_state["duration"], 
                                              self.device_state["position"] + 30)
        elif command == "Fast Reverse":
            self.device_state["position"] = max(0, self.device_state["position"] - 30)
        elif command == "10 sec forward":
            self.device_state["position"] = min(self.device_state["duration"], 
                                              self.device_state["position"] + 10)
        elif command == "10 sec rewind":
            self.device_state["position"] = max(0, self.device_state["position"] - 10)
        elif command == "60 sec forward":
            self.device_state["position"] = min(self.device_state["duration"], 
                                              self.device_state["position"] + 60)
        elif command == "60 sec rewind":
            self.device_state["position"] = max(0, self.device_state["position"] - 60)
        
        elif command == "Subtitle":
            self.device_state["subtitle_enabled"] = not self.device_state["subtitle_enabled"]
        elif command == "Audio":
            tracks = ["main", "commentary", "alternate"]
            current_idx = tracks.index(self.device_state["audio_track"])
            self.device_state["audio_track"] = tracks[(current_idx + 1) % len(tracks)]
        elif command == "Repeat":
            self.device_state["repeat"] = not self.device_state["repeat"]
        
        elif command == "Explorer":
            self.device_state["input"] = "usb"
            await self._change_media("file_browser")
        elif command == "Info":
            # Simulate showing device info - no state change
            pass
        elif command == "Menu":
            # Simulate opening menu - no state change  
            pass

    # ENHANCED: Source switching simulation
    async def _handle_source_switch(self, command: str):
        """Simulate source switching based on color function commands."""
        source_map = {
            "Function Red": "hdmi1",
            "Function Green": "hdmi2", 
            "Function Blue": "usb",
            "Function Yellow": "network"
        }
        
        if self.device_type == DeviceType.PLAYER and command == "Function Yellow":
            source_map["Function Yellow"] = "optical"
        
        new_input = source_map.get(command)
        if new_input and new_input != self.device_state["input"]:
            logger.info(f"Device {self.device_id}: Switching from {self.device_state['input']} to {new_input}")
            self.device_state["input"] = new_input
            
            # Simulate clearing media info on source change
            self.device_state["playback"] = "stop"
            self.device_state["position"] = 0
            
            # Load appropriate content for new source
            await self._change_media(f"content_for_{new_input}")

    async def debug_state(self, request: Request) -> Response:
        return web.json_response({
            "device_state": self.device_state,
            "device_info": self.device_info,
            "device_id": self.device_id,
            "device_name": self.device_name,
            "device_type": self.device_type.value,
            "timestamp": datetime.now().isoformat()
        })

    async def debug_reset(self, request: Request) -> Response:
        self.device_state.update({
            "power": "on",
            "volume": 50 + (self.device_id * 5),
            "max_volume": 100,
            "mute": False,
            "input": self._get_default_input(),
            "playback": "stop",
            "position": 0,
            "duration": 7200,
            "title": f"Demo Movie {self.device_id}",
            "artist": f"Demo Artist {self.device_id}",
            "album": f"Demo Album {self.device_id}",
            "cover_url": f"https://picsum.photos/300/300?random={self.device_id}",
            "subtitle_enabled": False,
            "audio_track": "main",
            "video_format": "4K",
            "repeat": False
        })
        
        logger.info(f"Device {self.device_id}: Simulator state reset to defaults")
        return web.json_response({"message": "State reset to defaults", "status": "ok"})

    async def debug_ir_codes(self, request: Request) -> Response:
        return web.json_response({
            "device_type": self.device_type.value,
            "device_id": self.device_info["device_id"],
            "ir_codes": self.ir_codes,
            "total_commands": len(self.ir_codes)
        })

    # ENHANCED: Media library endpoint for testing
    async def debug_media_library(self, request: Request) -> Response:
        return web.json_response({
            "status": "ok",
            "media_library": self.media_library,
            "current_media_index": getattr(self, '_current_media_index', 0)
        })

    def _start_position_update(self):
        if self._position_task is None:
            self._position_task = asyncio.create_task(self._position_updater())
    
    async def _position_updater(self):
        while True:
            try:
                await asyncio.sleep(1)
                if (self.device_state["power"] == "on" and 
                    self.device_state["playback"] == "play" and
                    self.device_state["duration"] > 0):  # Don't update position for live streams
                    self.device_state["position"] += 1
                    if self.device_state["position"] >= self.device_state["duration"]:
                        if self.device_state["repeat"]:
                            self.device_state["position"] = 0
                        else:
                            self.device_state["playback"] = "stop"
                            self.device_state["position"] = 0
                            await self._change_media()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Device {self.device_id}: Position update error: {e}")

    async def _change_media(self, source_context: str = None) -> None:
        """ENHANCED: More realistic media changing with proper metadata."""
        if not hasattr(self, '_current_media_index'):
            self._current_media_index = 0
        
        # Select appropriate media based on context
        if source_context == "file_browser":
            # File browser content
            media = {
                "title": f"Local File {random.randint(1, 100)}.mkv",
                "artist": "",
                "album": "",
                "duration": random.randint(3600, 7200),
                "cover_url": ""
            }
        elif source_context and "hdmi" in source_context:
            # HDMI input - no metadata
            media = {
                "title": f"HDMI Input",
                "artist": "",
                "album": "",
                "duration": 0,  # Live input
                "cover_url": ""
            }
        elif source_context and "optical" in source_context:
            # Optical input - no metadata
            media = {
                "title": "Optical Audio Input",
                "artist": "",
                "album": "",
                "duration": 0,  # Live input
                "cover_url": ""
            }
        else:
            # Cycle through media library
            self._current_media_index = (self._current_media_index + 1) % len(self.media_library)
            media = self.media_library[self._current_media_index]
        
        self.device_state.update({
            "title": media["title"],
            "artist": media["artist"],
            "album": media["album"],
            "position": 0,
            "duration": media["duration"],
            "cover_url": media["cover_url"],
            "audio_track": "main",
            "subtitle_enabled": False
        })
        
        if self.device_state["playback"] != "stop":
            self.device_state["playback"] = "play"
        
        logger.info(f"Device {self.device_id}: Changed media to '{media['title']}'")

    async def start(self) -> None:
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"R_volution {self.device_type.value.title()} Simulator {self.device_id} started on {self.host}:{self.port}")
        logger.info(f"Device: {self.device_name} ({self.device_info['device_id']})")
        logger.info(f"Type: {self.device_type.value} - {len(self.ir_codes)} commands available")


class MultiDeviceSimulator:
    
    def __init__(self):
        self.simulators: List[RvolutionSimulator] = []
        self.base_port = 8080
        self.host = get_local_ip()
    
    async def create_simulators(self, amlogic_count: int = 2, player_count: int = 2) -> List[Dict[str, Any]]:
        device_configs = []
        device_id = 1
        
        for i in range(amlogic_count):
            port = self.base_port + device_id - 1
            device_name = f"PlayerOne-8K-{device_id}"
            
            simulator = RvolutionSimulator(
                host=self.host,
                port=port,
                device_name=device_name,
                device_id=device_id,
                device_type=DeviceType.AMLOGIC
            )
            
            self.simulators.append(simulator)
            
            device_configs.append({
                "device_id": device_id,
                "name": device_name,
                "model": "PlayerOne 8K",
                "device_type": "amlogic",
                "ip": self.host,
                "port": port,
                "url": f"http://{self.host}:{port}"
            })
            device_id += 1
        
        for i in range(player_count):
            port = self.base_port + device_id - 1
            device_name = f"R_volution-Player-{device_id}"
            
            simulator = RvolutionSimulator(
                host=self.host,
                port=port,
                device_name=device_name,
                device_id=device_id,
                device_type=DeviceType.PLAYER
            )
            
            self.simulators.append(simulator)
            
            device_configs.append({
                "device_id": device_id,
                "name": device_name,
                "model": "R_volution Player",
                "device_type": "player",
                "ip": self.host,
                "port": port,
                "url": f"http://{self.host}:{port}"
            })
            device_id += 1
        
        return device_configs
    
    async def start_all(self) -> None:
        logger.info(f"Starting {len(self.simulators)} R_volution device simulators...")
        
        start_tasks = [simulator.start() for simulator in self.simulators]
        await asyncio.gather(*start_tasks)
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("Enhanced Multi-Device R_volution Simulator Ready")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Use these addresses in the integration setup:")
        
        amlogic_devices = [s for s in self.simulators if s.device_type == DeviceType.AMLOGIC]
        player_devices = [s for s in self.simulators if s.device_type == DeviceType.PLAYER]
        
        if amlogic_devices:
            logger.info("\nAmlogic Devices (PlayerOne 8K, Pro 8K, Mini):")
            for sim in amlogic_devices:
                logger.info(f"  Device {sim.device_id}: {sim.host}:{sim.port} ({sim.device_name})")
        
        if player_devices:
            logger.info("\nR_volution Player Devices:")
            for sim in player_devices:
                logger.info(f"  Device {sim.device_id}: {sim.host}:{sim.port} ({sim.device_name})")
        
        logger.info("")
        logger.info("ENHANCED API endpoints for each device:")
        logger.info("  - IR Command: http://HOST:PORT/cgi-bin/do?cmd=ir_code&ir_code=XXXX")
        logger.info("  - Device info: http://HOST:PORT/device/info")
        logger.info("  - Status: http://HOST:PORT/device/status")
        logger.info("  - Sources: http://HOST:PORT/device/sources")
        logger.info("  - Capabilities: http://HOST:PORT/device/capabilities")
        logger.info("  - Media library: http://HOST:PORT/debug/media_library")
        logger.info("  - Debug state: http://HOST:PORT/debug/state")
        logger.info("  - IR codes: http://HOST:PORT/debug/ir_codes")
        logger.info("  - Health check: http://HOST:PORT/health")
        logger.info("")
        logger.info("Enhanced Testing Features:")
        logger.info("  - Source switching with Function Red/Green/Blue/Yellow")
        logger.info("  - Media metadata with artist, album, cover art")
        logger.info("  - Live stream simulation (duration=0)")
        logger.info("  - Repeat mode testing")
        logger.info("  - Input source detection")
        logger.info("  - Position/duration tracking")
        logger.info("")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced R_volution Multi-Device Simulator")
    parser.add_argument("--host", default=None, help="Host to bind to (default: auto-detect local IP)")
    parser.add_argument("--port", type=int, default=8080, help="Base port to bind to (default: 8080)")
    parser.add_argument("--amlogic", type=int, default=2, help="Number of Amlogic devices (default: 2)")
    parser.add_argument("--player", type=int, default=2, help="Number of Player devices (default: 2)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--single", action="store_true", help="Run single device simulator")
    parser.add_argument("--type", choices=['amlogic', 'player'], default='amlogic', help="Device type for single mode")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.single:
        host = args.host if args.host else get_local_ip()
        device_type = DeviceType.AMLOGIC if args.type == 'amlogic' else DeviceType.PLAYER
        simulator = RvolutionSimulator(host, args.port, f"R_volution-{args.type}-SIM", 1, device_type)
        await simulator.start()
        
        logger.info("")
        logger.info("Single Enhanced R_volution Simulator Started")
        logger.info("=" * 50)
        logger.info("")
        logger.info("Use this address in the integration setup:")
        logger.info(f"  {host}:{args.port} (Type: {args.type})")
        logger.info("")
        logger.info("Test commands:")
        logger.info(f"  curl http://{host}:{args.port}/device/info")
        logger.info(f"  curl http://{host}:{args.port}/device/status")
        logger.info(f"  curl http://{host}:{args.port}/device/sources")
        logger.info(f"  curl http://{host}:{args.port}/device/capabilities")
        logger.info(f"  curl 'http://{host}:{args.port}/cgi-bin/do?cmd=ir_code&ir_code={simulator.ir_codes['Power On']}'")
        logger.info(f"  curl 'http://{host}:{args.port}/cgi-bin/do?cmd=ir_code&ir_code={simulator.ir_codes['Play/Pause']}'")
        logger.info(f"  curl 'http://{host}:{args.port}/cgi-bin/do?cmd=ir_code&ir_code={simulator.ir_codes['Function Red']}'")
        logger.info("")
        logger.info("Enhanced Features:")
        logger.info("  - Media metadata with artist/album/cover")
        logger.info("  - Source switching simulation")
        logger.info("  - Live stream content (duration=0)")
        logger.info("  - Repeat mode functionality")
        logger.info("  - Position/duration tracking")
        logger.info("")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Enhanced R_volution Simulator stopped by user")
    else:
        multi_sim = MultiDeviceSimulator()
        multi_sim.host = args.host if args.host else get_local_ip()
        multi_sim.base_port = args.port
        
        device_configs = await multi_sim.create_simulators(args.amlogic, args.player)
        await multi_sim.start_all()
        
        logger.info("Test commands for devices:")
        for config in device_configs:
            logger.info(f"  {config['name']} ({config['device_type']}):")
            logger.info(f"    curl http://{config['ip']}:{config['port']}/device/info")
            logger.info(f"    curl http://{config['ip']}:{config['port']}/device/status")
            logger.info(f"    curl http://{config['ip']}:{config['port']}/device/sources")
            logger.info(f"    curl 'http://{config['ip']}:{config['port']}/cgi-bin/do?cmd=ir_code&ir_code=POWER_CODE'")
        logger.info("")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Enhanced Multi-Device R_volution Simulator stopped by user")


if __name__ == "__main__":
    print("Enhanced R_volution Multi-Device Simulator")
    print("=" * 50)
    print("This simulator provides web servers that mimic R_volution device APIs")
    print("for testing the Unfolded Circle integration without physical hardware.")
    print("")
    print("Supports two device types:")
    print("  - Amlogic: PlayerOne 8K, Pro 8K, Mini")
    print("  - Player:  R_volution Players")
    print("")
    print("Enhanced Features:")
    print("  - Rich media metadata (artist, album, cover art)")
    print("  - Source switching simulation")
    print("  - Live stream content support")
    print("  - Repeat mode functionality")
    print("  - Position/duration tracking")
    print("  - Enhanced API endpoints for testing")
    print("")
    print("Usage:")
    print("  Single device:   python r_volution_simulator.py --single --type amlogic")
    print("  Multi-device:    python r_volution_simulator.py --amlogic 2 --player 2")
    print("  Debug mode:      python r_volution_simulator.py --debug --amlogic 1 --player 1")
    print("")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEnhanced Simulator stopped by user")
    except Exception as e:
        print(f"\nSimulator error: {e}")
        logging.exception("Simulator crashed")