"""
R_volution integration driver for Unfolded Circle Remote.

:copyright: (c) 2025 by Meir Miyara
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
import os
from typing import Dict, Optional, List, Any
from aiohttp import web

import ucapi
from ucapi import DeviceStates, Events, StatusCodes, IntegrationSetupError, SetupComplete, SetupError, RequestUserInput, UserDataResponse

from uc_intg_rvolution.client import RvolutionClient
from uc_intg_rvolution.config import RvolutionConfig, DeviceConfig, DeviceType
from uc_intg_rvolution.media_player import RvolutionMediaPlayer
from uc_intg_rvolution.remote import RvolutionRemote

api: ucapi.IntegrationAPI | None = None
config: RvolutionConfig | None = None
clients: Dict[str, RvolutionClient] = {}
media_players: Dict[str, RvolutionMediaPlayer] = {}
remotes: Dict[str, RvolutionRemote] = {}
entities_ready: bool = False
initialization_lock: asyncio.Lock = asyncio.Lock()

_LOG = logging.getLogger(__name__)


async def _initialize_integration():
    global clients, api, config, media_players, remotes, entities_ready
    
    async with initialization_lock:
        if entities_ready:
            _LOG.debug("Entities already initialized, skipping")
            return True
            
        if not config or not config.is_configured():
            _LOG.error("Configuration not found or invalid.")
            if api: 
                await api.set_device_state(DeviceStates.ERROR)
            return False

        _LOG.info("Initializing R_volution integration for %d devices...", len(config.get_all_devices()))
        if api: 
            await api.set_device_state(DeviceStates.CONNECTING)

        connected_devices = 0

        # Clear all entity collections for fresh initialization
        api.available_entities.clear()
        clients.clear()
        media_players.clear()
        remotes.clear()

        for device_config in config.get_enabled_devices():
            try:
                _LOG.info("Connecting to R_volution device: %s at %s", device_config.name, device_config.ip_address)
                
                client = RvolutionClient(device_config)
                
                # Use improved connection test with stability fixes
                connection_success = await client.test_connection()
                if not connection_success:
                    _LOG.warning("Failed to connect to device: %s", device_config.name)
                    await client.close()
                    continue

                device_name = device_config.name
                device_entity_id = device_config.device_id

                _LOG.info("Connected to R_volution device: %s (ID: %s, Type: %s)", 
                         device_name, device_entity_id, device_config.device_type.value)

                media_player_id = f"mp_{device_config.device_id}"
                remote_id = f"remote_{device_config.device_id}"

                # Create entity objects
                media_player_entity = RvolutionMediaPlayer(client, device_config, api)
                remote_entity = RvolutionRemote(client, device_config, api)

                # Add to available_entities for UC Remote discovery
                api.available_entities.add(media_player_entity)
                api.available_entities.add(remote_entity)

                # Store in global dictionaries for access
                clients[device_config.device_id] = client
                media_players[device_config.device_id] = media_player_entity
                remotes[device_config.device_id] = remote_entity

                connected_devices += 1
                _LOG.info("Successfully setup device: %s (Media Player: %s, Remote: %s)", 
                         device_config.name, media_player_id, remote_id)

            except Exception as e:
                _LOG.error("Failed to setup device %s: %s", device_config.name, e, exc_info=True)
                continue

        if connected_devices > 0:
            # CRITICAL: Mark entities as ready BEFORE setting connected state
            # This prevents race condition where UC Remote tries to subscribe before entities exist
            entities_ready = True
            
            # Set device state to CONNECTED
            await api.set_device_state(DeviceStates.CONNECTED)
            
            _LOG.info("R_volution integration initialization completed successfully - %d/%d devices connected.", 
                     connected_devices, len(config.get_all_devices()))
            
            # Log entity registration status for debugging
            _LOG.debug("Available entities: %d", len(api.available_entities._entities) if hasattr(api.available_entities, '_entities') else 0)
            
            return True
        else:
            entities_ready = False
            if api: 
                await api.set_device_state(DeviceStates.ERROR)
            _LOG.error("No devices could be connected during initialization")
            return False


async def setup_handler(msg: ucapi.SetupDriver) -> ucapi.SetupAction:
    global config, entities_ready

    if isinstance(msg, ucapi.DriverSetupRequest):
        device_count = int(msg.setup_data.get("device_count", 1))
        host = msg.setup_data.get("host", "").strip()
        
        if device_count == 1 and host:
            # Single device quick setup
            return await _handle_single_device_setup(msg.setup_data)
        else:
            # Multi-device setup flow
            return await _request_device_configurations(device_count)
    
    elif isinstance(msg, UserDataResponse):
        return await _handle_device_configurations(msg.input_values)

    return SetupError(IntegrationSetupError.OTHER)


async def _handle_single_device_setup(setup_data: Dict[str, Any]) -> ucapi.SetupAction:
    """Handle single device setup from driver.json initial configuration."""
    host_input = setup_data.get("host")
    if not host_input:
        _LOG.error("No host provided in setup data")
        return SetupError(IntegrationSetupError.OTHER)

    host = host_input.strip()
    _LOG.info("Testing connection to R_volution device at %s", host)

    try:
        device_type = DeviceType.AMLOGIC
        device_name = f"R_volution Device ({host})"
        
        device_config = DeviceConfig(
            device_id=f"rvolution_{host.replace('.', '_')}",
            name=device_name,
            ip_address=host,
            device_type=device_type
        )
        
        # Use improved connection test with stability fixes
        test_client = RvolutionClient(device_config)
        
        try:
            _LOG.info("Testing connection with improved stability handling...")
            connection_successful = await test_client.test_connection()
        finally:
            await test_client.close()

        if not connection_successful:
            _LOG.error("Connection test failed for host: %s", host)
            return SetupError(IntegrationSetupError.CONNECTION_REFUSED)

        config.add_device(device_config)
        _LOG.info("Device configuration saved, initializing integration...")
        
        # Initialize integration with new device
        await _initialize_integration()
        
        return SetupComplete()

    except Exception as e:
        _LOG.error("Setup error: %s", e, exc_info=True)
        return SetupError(IntegrationSetupError.OTHER)


async def _request_device_configurations(device_count: int) -> RequestUserInput:
    """Request configuration for multiple devices."""
    settings = []

    for i in range(device_count):
        settings.extend([
            {
                "id": f"device_{i}_ip",
                "label": {"en": f"Device {i+1} IP Address"},
                "description": {"en": f"IP address for R_volution device {i+1} (e.g., 192.168.1.{100+i})"},
                "field": {"text": {"value": f"192.168.1.{100+i}"}}
            },
            {
                "id": f"device_{i}_name",
                "label": {"en": f"Device {i+1} Name"},
                "description": {"en": f"Friendly name for device {i+1}"},
                "field": {"text": {"value": f"R_volution Device {i+1}"}}
            },
            {
                "id": f"device_{i}_type",
                "label": {"en": f"Device {i+1} Type"},
                "description": {"en": f"Select device type for device {i+1}"},
                "field": {
                    "dropdown": {
                        "items": [
                            {"id": "amlogic", "label": {"en": "Amlogic (PlayerOne 8K, Pro 8K, Mini)"}},
                            {"id": "player", "label": {"en": "R_volution Player"}}
                        ]
                    }
                }
            }
        ])

    return RequestUserInput(
        title={"en": f"Configure {device_count} R_volution Devices"},
        settings=settings
    )


async def _handle_device_configurations(input_values: Dict[str, Any]) -> ucapi.SetupAction:
    """Process device configurations from multi-device setup."""
    devices_to_test = []

    device_index = 0
    while f"device_{device_index}_ip" in input_values:
        ip_input = input_values[f"device_{device_index}_ip"]
        name = input_values[f"device_{device_index}_name"]
        device_type_str = input_values.get(f"device_{device_index}_type", "amlogic")

        try:
            if ':' in ip_input:
                host, port_str = ip_input.split(':', 1)
                port = int(port_str)
            else:
                host = ip_input
                port = 80
        except ValueError:
            _LOG.error(f"Invalid IP:port format for device {device_index + 1}: {ip_input}")
            return SetupError(IntegrationSetupError.OTHER)

        host = host.strip()
        if not host:
            _LOG.error(f"Invalid IP format for device {device_index + 1}: {ip_input}")
            return SetupError(IntegrationSetupError.OTHER)

        devices_to_test.append({
            "host": host,
            "port": port,
            "name": name,
            "device_type": device_type_str,
            "index": device_index
        })
        device_index += 1

    _LOG.info(f"Testing connections to {len(devices_to_test)} devices with improved stability handling...")
    test_results = await _test_multiple_devices_safely(devices_to_test)

    successful_devices = 0
    for device_data, success in zip(devices_to_test, test_results):
        if success:
            device_type = DeviceType.AMLOGIC if device_data['device_type'] == "amlogic" else DeviceType.PLAYER
            device_id = f"rvolution_{device_data['host'].replace('.', '_')}_{device_data['port']}"
            device_config = DeviceConfig(
                device_id=device_id,
                name=device_data['name'],
                ip_address=device_data['host'],
                port=device_data['port'],
                device_type=device_type
            )
            config.add_device(device_config)
            successful_devices += 1
            _LOG.info(f"Device {device_data['index'] + 1} ({device_data['name']}) connection successful")
        else:
            _LOG.error(f"Device {device_data['index'] + 1} ({device_data['name']}) connection failed")

    if successful_devices == 0:
        _LOG.error("No devices could be connected")
        return SetupError(IntegrationSetupError.CONNECTION_REFUSED)

    _LOG.info(f"Device configurations saved, initializing integration...")
    await _initialize_integration()
    
    _LOG.info(f"Multi-device setup completed: {successful_devices}/{len(devices_to_test)} devices configured")
    return SetupComplete()


async def _test_multiple_devices_safely(devices: List[Dict]) -> List[bool]:

    async def test_single_device_safely(device_data):
        """Test single device with proper error handling and connection management."""
        try:
            device_type = DeviceType.AMLOGIC if device_data['device_type'] == "amlogic" else DeviceType.PLAYER
            device_config = DeviceConfig(
                device_id=f"test_{device_data['index']}",
                name=device_data['name'],
                ip_address=device_data['host'],
                port=device_data['port'],
                device_type=device_type
            )
            
            _LOG.info(f"Testing device {device_data['index'] + 1}: {device_data['name']} at {device_data['host']}:{device_data['port']}")
            
            client = RvolutionClient(device_config)
            
            try:
                # Use improved connection test with stability fixes
                success = await client.test_connection()
                _LOG.info(f"Device {device_data['index'] + 1} test result: {'SUCCESS' if success else 'FAILED'}")
                return success
            finally:
                await client.close()
                
        except Exception as e:
            _LOG.error(f"Device {device_data['index'] + 1} test exception: {e}")
            return False

    results = []
    
    # Test devices sequentially to avoid overwhelming HTTP servers
    for i, device in enumerate(devices):
        _LOG.info(f"Testing device {i + 1}/{len(devices)}: {device['name']}")
        
        result = await test_single_device_safely(device)
        results.append(result)

        if i < len(devices) - 1:  # Don't delay after last device
            delay = 3.0  # 3 second delay between device tests
            _LOG.debug(f"Waiting {delay}s before testing next device (HTTP server stability)")
            await asyncio.sleep(delay)
    
    return results


async def on_subscribe_entities(entity_ids: List[str]):
    """
    Handle entity subscription with race condition protection.
    CRITICAL: Must verify entities are ready before processing subscriptions.
    """
    _LOG.info("Entities subscribed: %s", entity_ids)
    
    # Race condition protection: ensure entities are initialized
    if not entities_ready:
        _LOG.error("RACE CONDITION DETECTED: Subscription before entities ready!")
        _LOG.info("Attempting emergency initialization...")
        success = await _initialize_integration()
        if not success:
            _LOG.error("Failed to initialize during subscription attempt")
            return

    for entity_id in entity_ids:
        try:
            # Check media players
            for media_player in media_players.values():
                if media_player.id == entity_id:
                    _LOG.debug(f"Pushing update for media player: {entity_id}")
                    await media_player.push_update()
                    break
            
            # Check remotes
            for remote in remotes.values():
                if remote.id == entity_id:
                    _LOG.debug(f"Pushing update for remote: {entity_id}")
                    await remote.push_update()
                    break
                    
        except Exception as e:
            _LOG.error(f"Error pushing update for entity {entity_id}: {e}", exc_info=True)


async def on_connect():

    global entities_ready
    
    _LOG.info("Remote Two connected")
    
    # CRITICAL: Reload configuration from disk for reboot survival
    if config:
        config.reload_from_disk()
        _LOG.debug("Configuration reloaded from disk")
    
    if config and config.is_configured():
        if not entities_ready:
            _LOG.warning("Entities not ready on connect - initializing now")
            await _initialize_integration()
        else:
            _LOG.info("Entities already ready, confirming connection")
            if api:
                await api.set_device_state(DeviceStates.CONNECTED)
    else:
        _LOG.info("Not configured, waiting for setup")
        if api:
            await api.set_device_state(DeviceStates.DISCONNECTED)


async def on_disconnect():
    """Handle UC Remote disconnection."""
    _LOG.info("Remote Two disconnected")


async def on_unsubscribe_entities(entity_ids: List[str]):
    """Handle entity unsubscription."""
    _LOG.info("Entities unsubscribed: %s", entity_ids)


async def health_check(request):
    """Health check endpoint for monitoring."""
    return web.Response(text="OK", status=200)


async def start_health_server():
    """Start health check HTTP server on port 9090."""
    try:
        app = web.Application()
        app.router.add_get('/health', health_check)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 9090)
        await site.start()
        _LOG.info("Health check server started on port 9090")
    except Exception as e:
        _LOG.error("Failed to start health server: %s", e)


async def main():

    global api, config
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    _LOG.info("Starting R_volution Integration Driver")
    
    try:
        loop = asyncio.get_running_loop()
        
        # Initialize configuration
        config_dir = os.getenv("UC_CONFIG_HOME", "./")
        config_file_path = os.path.join(config_dir, "config.json")
        config = RvolutionConfig(config_file_path)

        # Load driver metadata
        driver_path = os.path.join(os.path.dirname(__file__), "..", "driver.json")
        api = ucapi.IntegrationAPI(loop)

        if config.is_configured():
            _LOG.info("Pre-configuring entities before UC Remote connection")
            _LOG.info(f"Configuration summary: {config.get_summary()}")

            await _initialize_integration()
        else:
            _LOG.info("No existing configuration found, waiting for setup")

        # Initialize integration API
        await api.init(os.path.abspath(driver_path), setup_handler)

        # Start health check server
        asyncio.create_task(start_health_server())

        # Register event handlers
        api.add_listener(Events.SUBSCRIBE_ENTITIES, on_subscribe_entities)
        api.add_listener(Events.UNSUBSCRIBE_ENTITIES, on_unsubscribe_entities)
        api.add_listener(Events.CONNECT, on_connect)
        api.add_listener(Events.DISCONNECT, on_disconnect)

        # Set initial device state
        if not config.is_configured():
            _LOG.info("Device not configured, waiting for setup...")
            await api.set_device_state(DeviceStates.DISCONNECTED)

        _LOG.info("R_volution integration driver started successfully")
        _LOG.info(f"Entities ready: {entities_ready}, Configured devices: {config.get_device_count()}")
        
        # Run forever
        await asyncio.Future()
        
    except Exception as e:
        _LOG.critical("Fatal error in main: %s", e, exc_info=True)
    finally:
        _LOG.info("Shutting down R_volution integration")
        
        # Clean up all client connections
        for client in clients.values():
            try:
                await client.close()
            except Exception as e:
                _LOG.error(f"Error closing client: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _LOG.info("Integration stopped by user")
    except Exception as e:
        _LOG.error(f"Integration failed: {e}")
        raise