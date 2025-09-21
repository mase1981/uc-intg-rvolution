"""
Setup flow handler for R_volution integration.

:copyright: (c) 2025 by Meir Miyara
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any, Dict, List

import ucapi
from ucapi import IntegrationSetupError, RequestUserInput, SetupAction, SetupComplete, SetupError

from uc_intg_rvolution.client import RvolutionClient
from uc_intg_rvolution.config import DeviceConfig, DeviceType, RvolutionConfig

_LOG = logging.getLogger(__name__)


class SetupManager:
    """Handles the multi-device setup flow for R_volution integration."""
    
    def __init__(self, config: RvolutionConfig):
        """Initialize setup manager."""
        self._config = config
        self._setup_data: Dict[str, Any] = {}
        self._device_count = 0
        self._current_device = 0
        
    async def handle_setup(self, msg: ucapi.SetupDriver) -> SetupAction:
        """Handle setup messages from Remote Two."""
        _LOG.debug(f"Setup handler received: {type(msg).__name__}")
        
        if isinstance(msg, ucapi.DriverSetupRequest):
            return await self._handle_driver_setup_request(msg)
        elif isinstance(msg, ucapi.UserDataResponse):
            return await self._handle_user_data_response(msg)
        elif isinstance(msg, ucapi.AbortDriverSetup):
            return await self._handle_abort_setup(msg)
        else:
            _LOG.warning(f"Unknown setup message type: {type(msg)}")
            return SetupError(IntegrationSetupError.OTHER)
    
    async def _handle_driver_setup_request(self, msg: ucapi.DriverSetupRequest) -> SetupAction:
        """Handle initial driver setup request."""
        _LOG.info("Starting R_volution integration setup")
        
        self._setup_data = msg.setup_data
        
        # Get device count from initial setup data
        device_count = int(self._setup_data.get("device_count", 1))
        self._device_count = device_count
        
        if device_count < 1 or device_count > 10:
            _LOG.error(f"Device count out of range: {device_count}")
            return SetupError(IntegrationSetupError.OTHER)
        
        _LOG.info(f"Setting up {device_count} R_volution devices")
        
        # Clear existing configuration if not reconfiguring
        if not msg.reconfigure:
            self._config.clear_all_devices()
        
        if device_count == 1:
            # Single device - use existing simple flow from driver.json
            return await self._handle_single_device_setup(self._setup_data)
        else:
            # Multi-device setup - start with first device
            self._current_device = 1
            return await self._request_device_info()
    
    async def _handle_single_device_setup(self, setup_data: Dict[str, Any]) -> SetupAction:
        """Handle single device setup (existing flow)."""
        host = setup_data.get("host", "").strip()
        device_type_str = setup_data.get("device_type", "amlogic")
        
        if not host:
            _LOG.error("No host provided in setup data")
            return SetupError(IntegrationSetupError.OTHER)
        
        if device_type_str not in ["amlogic", "player"]:
            _LOG.error(f"Invalid device type: {device_type_str}")
            return SetupError(IntegrationSetupError.OTHER)
        
        _LOG.info(f"Testing connection to R_volution device at {host}")
        
        try:
            device_type = DeviceType.AMLOGIC if device_type_str == "amlogic" else DeviceType.PLAYER
            device_config = DeviceConfig(
                device_id="rvolution_single",
                name=f"R_volution Device ({device_type_str.title()})",
                ip_address=host,
                device_type=device_type
            )
            
            client = RvolutionClient(device_config)
            connection_success = await client.test_connection()
            await client.close()
            
            if not connection_success:
                _LOG.error(f"Connection test failed for device at {host}")
                return SetupError(IntegrationSetupError.CONNECTION_REFUSED)
            
            # Add device to configuration
            self._config.add_device(device_config)
            _LOG.info(f"Successfully configured single device: {host} ({device_type_str})")
            
            return SetupComplete()
            
        except Exception as e:
            _LOG.error(f"Setup error: {e}")
            return SetupError(IntegrationSetupError.OTHER)
    
    async def _handle_user_data_response(self, msg: ucapi.UserDataResponse) -> SetupAction:
        """Handle user input response for multi-device setup."""
        input_values = msg.input_values
        _LOG.debug(f"Received user input for device {self._current_device}: {list(input_values.keys())}")
        
        # Validate device configuration
        device_name = input_values.get("device_name", f"R_volution Device {self._current_device}")
        ip_address = input_values.get("ip_address", "").strip()
        device_type_str = input_values.get("device_type", "amlogic")
        
        # Validation
        errors = []
        
        if not ip_address:
            errors.append("IP address is required")
        else:
            # Basic IP validation
            ip_parts = ip_address.split('.')
            if len(ip_parts) != 4:
                errors.append("Invalid IP address format")
            else:
                for part in ip_parts:
                    try:
                        num = int(part)
                        if num < 0 or num > 255:
                            errors.append("Invalid IP address range")
                            break
                    except ValueError:
                        errors.append("Invalid IP address format")
                        break
        
        if device_type_str not in ["amlogic", "player"]:
            errors.append("Invalid device type")
        
        if errors:
            _LOG.error(f"Validation errors for device {self._current_device}: {errors}")
            return await self._request_device_info(errors)
        
        # Test connection to device
        try:
            device_type = DeviceType.AMLOGIC if device_type_str == "amlogic" else DeviceType.PLAYER
            device_config = DeviceConfig(
                device_id=f"rvolution_{self._current_device}",
                name=device_name,
                ip_address=ip_address,
                device_type=device_type
            )
            
            client = RvolutionClient(device_config)
            connection_success = await client.test_connection()
            await client.close()
            
            if not connection_success:
                _LOG.warning(f"Connection test failed for device {self._current_device} at {ip_address}")
                return await self._request_device_info([f"Could not connect to device at {ip_address}. Please check IP address and ensure device is powered on."])
            
            # Add device to configuration
            self._config.add_device(device_config)
            _LOG.info(f"Successfully added device {self._current_device}: {device_name} ({device_type_str}) at {ip_address}")
            
        except Exception as e:
            _LOG.error(f"Error testing device connection for device {self._current_device}: {e}")
            return await self._request_device_info([f"Connection test failed: {str(e)}"])
        
        # Move to next device or complete setup
        self._current_device += 1
        
        if self._current_device <= self._device_count:
            return await self._request_device_info()
        else:
            return await self._complete_setup()
    
    async def _handle_abort_setup(self, msg: ucapi.AbortDriverSetup) -> SetupAction:
        """Handle setup abort."""
        _LOG.warning(f"Setup aborted: {msg.error}")
        return SetupError(msg.error)
    
    async def _request_device_info(self, errors: List[str] = None) -> RequestUserInput:
        """Request device information from user for multi-device setup."""
        title = f"R_volution Device {self._current_device} of {self._device_count}"
        
        settings = []
        
        # Add error messages if any
        if errors:
            error_text = "\n".join([f"• {error}" for error in errors])
            settings.append({
                "id": "errors",
                "label": {
                    "en": "Please fix the following errors:"
                },
                "field": {
                    "label": {
                        "value": error_text
                    }
                }
            })
        
        settings.extend([
            {
                "id": "device_name",
                "label": {
                    "en": "Device Name"
                },
                "field": {
                    "text": {
                        "value": f"R_volution Device {self._current_device}"
                    }
                }
            },
            {
                "id": "ip_address", 
                "label": {
                    "en": "IP Address"
                },
                "field": {
                    "text": {
                        "regex": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
                    }
                }
            },
            {
                "id": "device_type",
                "label": {
                    "en": "Device Type"
                },
                "field": {
                    "dropdown": {
                        "items": [
                            {
                                "id": "amlogic",
                                "label": {
                                    "en": "Amlogic (PlayerOne 8K, Pro 8K, Mini)"
                                }
                            },
                            {
                                "id": "player", 
                                "label": {
                                    "en": "R_volution Player"
                                }
                            }
                        ]
                    }
                }
            }
        ])
        
        return RequestUserInput(title, settings)
    
    async def _complete_setup(self) -> SetupComplete:
        """Complete the setup process."""
        device_count = self._config.get_device_count()
        _LOG.info(f"Setup completed successfully with {device_count} devices configured")
        
        # Log device summary
        for device in self._config.get_all_devices():
            _LOG.info(f"  - {device.name} ({device.device_type.value}) at {device.ip_address}")
        
        return SetupComplete()