"""
Configuration management for the R_volution integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from dataclasses import dataclass

from ucapi_framework import BaseConfigManager

from uc_intg_rvolution.const import DEVICE_TYPE_AMLOGIC, IR_PORT


@dataclass
class DeviceConfig:
    """Configuration for a single R_volution device."""

    identifier: str = ""
    name: str = ""
    host: str = ""
    device_type: str = DEVICE_TYPE_AMLOGIC
    port: int = IR_PORT


class DeviceConfigManager(BaseConfigManager[DeviceConfig]):
    """Configuration manager for R_volution devices."""
