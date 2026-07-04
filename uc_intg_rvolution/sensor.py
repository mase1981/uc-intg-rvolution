"""
R_volution sensor entities: playback state and now-playing title.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi import sensor
from ucapi_framework import SensorEntity

from uc_intg_rvolution.config import DeviceConfig
from uc_intg_rvolution.device import RvolutionDevice

_LOG = logging.getLogger(__name__)


class PlaybackStateSensor(SensorEntity):
    """Reports the current playback state (Playing / Paused / Idle / Off)."""

    _LABELS = {
        "PLAYING": "Playing",
        "PAUSED": "Paused",
        "BUFFERING": "Buffering",
        "ON": "Idle",
        "OFF": "Off",
    }

    def __init__(self, device_config: DeviceConfig, device: RvolutionDevice) -> None:
        self._device = device
        entity_id = f"sensor.{device_config.identifier}.playback"
        super().__init__(
            entity_id,
            f"{device_config.name} Playback",
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: ""},
            device_class=sensor.DeviceClasses.CUSTOM,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        self.update(
            {
                sensor.Attributes.STATE: sensor.States.ON,
                sensor.Attributes.VALUE: self._LABELS.get(self._device.state, "Unknown"),
            }
        )


class NowPlayingSensor(SensorEntity):
    """Reports the current media title (from the R_video API when available)."""

    def __init__(self, device_config: DeviceConfig, device: RvolutionDevice) -> None:
        self._device = device
        entity_id = f"sensor.{device_config.identifier}.now_playing"
        super().__init__(
            entity_id,
            f"{device_config.name} Now Playing",
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: ""},
            device_class=sensor.DeviceClasses.CUSTOM,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        self.update(
            {
                sensor.Attributes.STATE: sensor.States.ON,
                sensor.Attributes.VALUE: self._device.media_title or "Nothing playing",
            }
        )
