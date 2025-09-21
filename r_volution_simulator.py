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
    """R_volution device types."""
    AMLOGIC = "amlogic"  # PlayerOne 8K, Pro 8K, Mini
    PLAYER = "player"    # R_volution Players


def get_local_ip() -> str:
    """Get the local IP address of the machine."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


class RvolutionSimulator:
    """Simulates an R_volution media player device."""
    
    def __init__(self, host: str = None, port: int = 8080, device_name: str = "R_volution-SIM", 
                 device_id: int = 1, device_type: DeviceType = DeviceType.AMLOGIC):
        """Initialize the simulator."""
        self.host = host if host else get_local_ip()
        self.port = port
        self.device_name = device_name
        self.device_id = device_id
        self.device_type = device_type
        self.app = web.Application()
        
        # Device state
        self.device_state = {
            "power": "on",
            "volume": 50 + (device_id * 5),
            "max_volume": 100,
            "mute": False,
            "input": "hdmi1",
            "playback": "stop",
            "position": 0,
            "duration": 7200,  # 2 hours in seconds
            "title": f"Demo Movie {device_id}",
            "subtitle_enabled": False,
            "audio_track": "main",
            "video_format": "4K",
            "repeat": False
        }
        
        # Device info based on type
        if device_type == DeviceType.AMLOGIC:
            self.device_info = {
                "model_name": f"PlayerOne-8K-SIM-{device_id}",
                "device_id": f"AMLOGIC{device_id:03d}",
                "device_type": "amlogic",
                "firmware_version": "2.1.5",
                "supported_formats": ["4K", "HDR", "DolbyVision"],
                "api_type": "amlogic_ir"
            }
            self.ir_codes = self._get_amlogic_ir_codes()
        else:
            self.device_info = {
                "model_name": f"R_volution-Player-SIM-{device_id}",
                "device_id": f"PLAYER{device_id:03d}",
                "device_type": "player",
                "firmware_version": "1.8.2",
                "supported_formats": ["1080p", "4K", "HDR"],
                "api_type": "player_ir"
            }
            self.ir_codes = self._get_player_ir_codes()
        
        self._setup_routes()
        self._position_task: Optional[asyncio.Task] = None
        self._start_position_update()
        
    def _get_amlogic_ir_codes(self) -> Dict[str, str]:
        """Get IR codes for Amlogic devices."""
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
        """Get IR codes for R_volution Player devices."""
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
        """Set up HTTP routes for R_volution API."""
        # Root endpoint
        self.app.router.add_get('/', self.handle_root)
        
        # Main IR control endpoint - matches R_volution API
        self.app.router.add_get('/cgi-bin/do', self.handle_ir_command)
        
        # Device info endpoints
        self.app.router.add_get('/device/info', self.get_device_info)
        self.app.router.add_get('/device/status', self.get_device_status)
        
        # Debug endpoints
        self.app.router.add_get('/debug/state', self.debug_state)
        self.app.router.add_get('/debug/reset', self.debug_reset)
        self.app.router.add_get('/debug/ir_codes', self.debug_ir_codes)
        
        # Health check
        self.app.router.add_get('/health', self.health_check)
    
    async def handle_root(self, request: Request) -> Response:
        """Handle root endpoint."""
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
        """Health check endpoint."""
        return web.json_response({
            "status": "healthy", 
            "device_id": self.device_info["device_id"],
            "device_name": self.device_name,
            "device_type": self.device_type.value
        })

    async def get_device_info(self, request: Request) -> Response:
        """Get device information."""
        return web.json_response({
            "status": "ok",
            **self.device_info
        })

    async def get_device_status(self, request: Request) -> Response:
        """Get current device status."""
        return web.json_response({
            "status": "ok",
            **self.device_state,
            "device_info": self.device_info
        })

    async def handle_ir_command(self, request: Request) -> Response:
        """Handle IR command requests - main API endpoint."""
        cmd = request.query.get('cmd')
        ir_code = request.query.get('ir_code')
        
        if cmd != 'ir_code':
            return web.json_response({"status": "error", "message": "Invalid command"}, status=400)
        
        if not ir_code:
            return web.json_response({"status": "error", "message": "Missing ir_code parameter"}, status=400)
        
        # Find command name from IR code
        command_name = None
        for name, code in self.ir_codes.items():
            if code == ir_code:
                command_name = name
                break
        
        if not command_name:
            logger.warning(f"Device {self.device_id}: Unknown IR code received: {ir_code}")
            return web.json_response({"status": "error", "message": f"Unknown IR code: {ir_code}"}, status=404)
        
        # Process the command
        await self._process_command(command_name)
        
        logger.info(f"Device {self.device_id}: Executed command '{command_name}' (IR: {ir_code})")
        return web.json_response({
            "status": "ok", 
            "command": command_name,
            "ir_code": ir_code,
            "device_id": self.device_info["device_id"]
        })

    async def _process_command(self, command: str) -> None:
        """Process IR command and update device state."""
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

    async def debug_state(self, request: Request) -> Response:
        """Get current simulator state for debugging."""
        return web.json_response({
            "device_state": self.device_state,
            "device_info": self.device_info,
            "device_id": self.device_id,
            "device_name": self.device_name,
            "device_type": self.device_type.value,
            "timestamp": datetime.now().isoformat()
        })

    async def debug_reset(self, request: Request) -> Response:
        """Reset simulator to initial state."""
        self.device_state.update({
            "power": "on",
            "volume": 50 + (self.device_id * 5),
            "max_volume": 100,
            "mute": False,
            "input": "hdmi1",
            "playback": "stop",
            "position": 0,
            "duration": 7200,
            "title": f"Demo Movie {self.device_id}",
            "subtitle_enabled": False,
            "audio_track": "main",
            "video_format": "4K",
            "repeat": False
        })
        
        logger.info(f"Device {self.device_id}: Simulator state reset to defaults")
        return web.json_response({"message": "State reset to defaults", "status": "ok"})

    async def debug_ir_codes(self, request: Request) -> Response:
        """Get all available IR codes for this device type."""
        return web.json_response({
            "device_type": self.device_type.value,
            "device_id": self.device_info["device_id"],
            "ir_codes": self.ir_codes,
            "total_commands": len(self.ir_codes)
        })

    def _start_position_update(self):
        """Start position update task."""
        if self._position_task is None:
            self._position_task = asyncio.create_task(self._position_updater())
    
    async def _position_updater(self):
        """Update position when playing."""
        while True:
            try:
                await asyncio.sleep(1)
                if (self.device_state["power"] == "on" and 
                    self.device_state["playback"] == "play"):
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

    async def _change_media(self) -> None:
        """Change to new media content."""
        movie_num = random.randint(1, 20)
        duration = random.randint(3600, 9000)  # 1-2.5 hours
        
        self.device_state.update({
            "title": f"Movie {movie_num} - Device {self.device_id}",
            "position": 0,
            "duration": duration,
            "audio_track": "main",
            "subtitle_enabled": False
        })
        
        if self.device_state["playback"] != "stop":
            self.device_state["playback"] = "play"

    async def start(self) -> None:
        """Start the simulator server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"R_volution {self.device_type.value.title()} Simulator {self.device_id} started on {self.host}:{self.port}")
        logger.info(f"Device: {self.device_name} ({self.device_info['device_id']})")
        logger.info(f"Type: {self.device_type.value} - {len(self.ir_codes)} commands available")


class MultiDeviceSimulator:
    """Manages multiple R_volution device simulators."""
    
    def __init__(self):
        self.simulators: List[RvolutionSimulator] = []
        self.base_port = 8080
        self.host = get_local_ip()
    
    async def create_simulators(self, amlogic_count: int = 2, player_count: int = 2) -> List[Dict[str, Any]]:
        """Create multiple device simulators."""
        device_configs = []
        device_id = 1
        
        # Create Amlogic devices
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
        
        # Create Player devices
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
        """Start all simulators."""
        logger.info(f"Starting {len(self.simulators)} R_volution device simulators...")
        
        start_tasks = [simulator.start() for simulator in self.simulators]
        await asyncio.gather(*start_tasks)
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("🎬 Multi-Device R_volution Simulator Ready")
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
        logger.info("API endpoints for each device:")
        logger.info("  - IR Command: http://HOST:PORT/cgi-bin/do?cmd=ir_code&ir_code=XXXX")
        logger.info("  - Device info: http://HOST:PORT/device/info")
        logger.info("  - Status: http://HOST:PORT/device/status")
        logger.info("  - Debug state: http://HOST:PORT/debug/state")
        logger.info("  - IR codes: http://HOST:PORT/debug/ir_codes")
        logger.info("  - Health check: http://HOST:PORT/health")
        logger.info("")


async def main():
    """Main entry point for the multi-device simulator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="R_volution Multi-Device Simulator")
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
        # Single device mode
        host = args.host if args.host else get_local_ip()
        device_type = DeviceType.AMLOGIC if args.type == 'amlogic' else DeviceType.PLAYER
        simulator = RvolutionSimulator(host, args.port, f"R_volution-{args.type}-SIM", 1, device_type)
        await simulator.start()
        
        logger.info("")
        logger.info("🎬 Single R_volution Simulator Started")
        logger.info("=" * 50)
        logger.info("")
        logger.info("Use this address in the integration setup:")
        logger.info(f"  {host}:{args.port} (Type: {args.type})")
        logger.info("")
        logger.info("Test commands:")
        logger.info(f"  curl http://{host}:{args.port}/device/info")
        logger.info(f"  curl http://{host}:{args.port}/device/status")
        logger.info(f"  curl 'http://{host}:{args.port}/cgi-bin/do?cmd=ir_code&ir_code={simulator.ir_codes['Power On']}'")
        logger.info(f"  curl 'http://{host}:{args.port}/cgi-bin/do?cmd=ir_code&ir_code={simulator.ir_codes['Play/Pause']}'")
        logger.info("")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("R_volution Simulator stopped by user")
    else:
        # Multi-device mode
        multi_sim = MultiDeviceSimulator()
        multi_sim.host = args.host if args.host else get_local_ip()
        multi_sim.base_port = args.port
        
        device_configs = await multi_sim.create_simulators(args.amlogic, args.player)
        await multi_sim.start_all()
        
        # Show test commands
        logger.info("Test commands for devices:")
        for config in device_configs:
            logger.info(f"  {config['name']} ({config['device_type']}):")
            logger.info(f"    curl http://{config['ip']}:{config['port']}/device/info")
            logger.info(f"    curl 'http://{config['ip']}:{config['port']}/cgi-bin/do?cmd=ir_code&ir_code=POWER_CODE'")
        logger.info("")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Multi-Device R_volution Simulator stopped by user")


if __name__ == "__main__":
    print("🎬 R_volution Multi-Device Simulator")
    print("=" * 50)
    print("This simulator provides web servers that mimic R_volution device APIs")
    print("for testing the Unfolded Circle integration without physical hardware.")
    print("")
    print("Supports two device types:")
    print("  - Amlogic: PlayerOne 8K, Pro 8K, Mini")
    print("  - Player:  R_volution Players")
    print("")
    print("Usage:")
    print("  Single device:   python r_volution_simulator.py --single --type amlogic")
    print("  Multi-device:    python r_volution_simulator.py --amlogic 2 --player 2")
    print("  Debug mode:      python r_volution_simulator.py --debug --amlogic 1 --player 1")
    print("")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSimulator stopped by user")
    except Exception as e:
        print(f"\nSimulator error: {e}")
        logging.exception("Simulator crashed")