"""
Configuration management for R_volution integration.

:copyright: (c) 2025 by Meir Miyara
:license: MPL-2.0, see LICENSE for more details.
"""

import json
import logging
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from enum import Enum

_LOG = logging.getLogger(__name__)


class DeviceType(Enum):
    AMLOGIC = "amlogic"
    PLAYER = "player"


@dataclass
class DeviceConfig:
    device_id: str
    name: str
    ip_address: str
    device_type: DeviceType
    port: int = 80
    timeout: int = 10
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "ip_address": self.ip_address,
            "device_type": self.device_type.value,
            "port": self.port,
            "timeout": self.timeout,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceConfig":
        return cls(
            device_id=data["device_id"],
            name=data["name"],
            ip_address=data["ip_address"],
            device_type=DeviceType(data["device_type"]),
            port=data.get("port", 80),
            timeout=data.get("timeout", 10),
            enabled=data.get("enabled", True)
        )


class RvolutionConfig:
    
    def __init__(self, config_file_path: str = "config.json"):
        self._config_file_path = config_file_path
        self._devices: List[DeviceConfig] = []
        self._loaded = False
        
        config_dir = os.path.dirname(self._config_file_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        self._load_config()
    
    def _load_config(self) -> None:
        try:
            if os.path.exists(self._config_file_path):
                with open(self._config_file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    
                devices_data = data.get("devices", [])
                self._devices = [DeviceConfig.from_dict(device_data) for device_data in devices_data]
                
                _LOG.info(f"Loaded configuration with {len(self._devices)} devices")
                self._loaded = True
            else:
                _LOG.info("No existing configuration file found")
                self._devices = []
                self._loaded = True
        except Exception as e:
            _LOG.error(f"Failed to load configuration: {e}")
            self._devices = []
            self._loaded = True
    
    def _save_config(self) -> None:
        try:
            config_data = {
                "devices": [device.to_dict() for device in self._devices],
                "version": "1.0.0"
            }
            
            with open(self._config_file_path, 'w', encoding='utf-8') as file:
                json.dump(config_data, file, indent=2, ensure_ascii=False)
            
            _LOG.info(f"Saved configuration with {len(self._devices)} devices")
        except Exception as e:
            _LOG.error(f"Failed to save configuration: {e}")
            raise
    
    def reload_from_disk(self) -> None:
        _LOG.debug("Reloading configuration from disk")
        self._load_config()
    
    def is_configured(self) -> bool:
        return self._loaded and len(self._devices) > 0
    
    def add_device(self, device: DeviceConfig) -> None:
        existing_ids = [d.device_id for d in self._devices]
        if device.device_id in existing_ids:
            raise ValueError(f"Device ID {device.device_id} already exists")
        
        self._devices.append(device)
        self._save_config()
        _LOG.info(f"Added device: {device.name} ({device.device_type.value}) at {device.ip_address}")
    
    def remove_device(self, device_id: str) -> bool:
        original_count = len(self._devices)
        self._devices = [d for d in self._devices if d.device_id != device_id]
        
        if len(self._devices) < original_count:
            self._save_config()
            _LOG.info(f"Removed device: {device_id}")
            return True
        return False
    
    def get_device(self, device_id: str) -> Optional[DeviceConfig]:
        for device in self._devices:
            if device.device_id == device_id:
                return device
        return None
    
    def get_all_devices(self) -> List[DeviceConfig]:
        return self._devices.copy()
    
    def get_enabled_devices(self) -> List[DeviceConfig]:
        return [device for device in self._devices if device.enabled]
    
    def get_devices_by_type(self, device_type: DeviceType) -> List[DeviceConfig]:
        return [device for device in self._devices if device.device_type == device_type]
    
    def update_device(self, device_id: str, **kwargs) -> bool:
        device = self.get_device(device_id)
        if not device:
            return False
        
        allowed_fields = ['name', 'ip_address', 'device_type', 'port', 'timeout', 'enabled']
        updated = False
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(device, field):
                if field == 'device_type' and isinstance(value, str):
                    value = DeviceType(value)
                setattr(device, field, value)
                updated = True
        
        if updated:
            self._save_config()
            _LOG.info(f"Updated device: {device_id}")
        
        return updated
    
    def clear_all_devices(self) -> None:
        self._devices = []
        self._save_config()
        _LOG.info("Cleared all device configurations")
    
    def validate_device_config(self, device: DeviceConfig) -> List[str]:
        errors = []
        
        if not device.device_id or not device.device_id.strip():
            errors.append("Device ID cannot be empty")
        
        if not device.name or not device.name.strip():
            errors.append("Device name cannot be empty")
        
        if not device.ip_address or not device.ip_address.strip():
            errors.append("IP address cannot be empty")
        
        ip_parts = device.ip_address.split('.')
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
        
        if device.port < 1 or device.port > 65535:
            errors.append("Port must be between 1 and 65535")
        
        if device.timeout < 1 or device.timeout > 60:
            errors.append("Timeout must be between 1 and 60 seconds")
        
        return errors
    
    def get_device_count(self) -> int:
        return len(self._devices)
    
    def get_enabled_device_count(self) -> int:
        return len(self.get_enabled_devices())
    
    def get_summary(self) -> Dict[str, Any]:
        amlogic_devices = self.get_devices_by_type(DeviceType.AMLOGIC)
        player_devices = self.get_devices_by_type(DeviceType.PLAYER)
        
        return {
            "total_devices": len(self._devices),
            "enabled_devices": len(self.get_enabled_devices()),
            "amlogic_devices": len(amlogic_devices),
            "player_devices": len(player_devices),
            "configured": self.is_configured(),
            "config_file": self._config_file_path
        }
    
    def export_config(self) -> Dict[str, Any]:
        return {
            "devices": [device.to_dict() for device in self._devices],
            "version": "1.0.0",
            "exported_at": "2025-01-01T00:00:00Z"
        }
    
    def import_config(self, config_data: Dict[str, Any]) -> None:
        try:
            devices_data = config_data.get("devices", [])
            imported_devices = [DeviceConfig.from_dict(device_data) for device_data in devices_data]
            
            for device in imported_devices:
                errors = self.validate_device_config(device)
                if errors:
                    raise ValueError(f"Invalid device {device.device_id}: {', '.join(errors)}")
            
            self._devices = imported_devices
            self._save_config()
            _LOG.info(f"Imported configuration with {len(imported_devices)} devices")
        except Exception as e:
            _LOG.error(f"Failed to import configuration: {e}")
            raise
    
    @property
    def config_file_path(self) -> str:
        return self._config_file_path