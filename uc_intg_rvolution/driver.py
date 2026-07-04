"""
R_volution integration driver.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from ucapi_framework import BaseIntegrationDriver

from uc_intg_rvolution.config import DeviceConfig
from uc_intg_rvolution.device import RvolutionDevice
from uc_intg_rvolution.media_player import RvolutionMediaPlayer
from uc_intg_rvolution.remote import RvolutionRemote
from uc_intg_rvolution.select import QuickLaunchSelect
from uc_intg_rvolution.sensor import NowPlayingSensor, PlaybackStateSensor
from uc_intg_rvolution.switch import RvolutionPowerSwitch


class RvolutionDriver(BaseIntegrationDriver[RvolutionDevice, DeviceConfig]):
    """Integration driver for R_volution players."""

    def __init__(self) -> None:
        super().__init__(
            device_class=RvolutionDevice,
            entity_classes=[
                RvolutionMediaPlayer,
                RvolutionRemote,
                RvolutionPowerSwitch,
                QuickLaunchSelect,
                PlaybackStateSensor,
                NowPlayingSensor,
            ],
            driver_id="uc_intg_rvolution",
        )
