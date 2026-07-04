"""
R_volution media player entity.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes, media_player
from ucapi_framework import MediaPlayerEntity

from uc_intg_rvolution.config import DeviceConfig
from uc_intg_rvolution.device import RvolutionDevice

_LOG = logging.getLogger(__name__)

FEATURES = [
    media_player.Features.ON_OFF,
    media_player.Features.TOGGLE,
    media_player.Features.PLAY_PAUSE,
    media_player.Features.STOP,
    media_player.Features.NEXT,
    media_player.Features.PREVIOUS,
    media_player.Features.FAST_FORWARD,
    media_player.Features.REWIND,
    media_player.Features.VOLUME_UP_DOWN,
    media_player.Features.MUTE_TOGGLE,
    media_player.Features.MEDIA_TITLE,
    media_player.Features.MEDIA_ARTIST,
    media_player.Features.MEDIA_ALBUM,
    media_player.Features.MEDIA_IMAGE_URL,
    media_player.Features.MEDIA_TYPE,
    media_player.Features.MEDIA_DURATION,
    media_player.Features.MEDIA_POSITION,
]

_COMMAND_MAP = {
    media_player.Commands.PLAY_PAUSE: "Play/Pause",
    media_player.Commands.STOP: "Stop",
    media_player.Commands.NEXT: "Next",
    media_player.Commands.PREVIOUS: "Previous",
    media_player.Commands.FAST_FORWARD: "Fast Forward",
    media_player.Commands.REWIND: "Fast Reverse",
    media_player.Commands.VOLUME_UP: "Volume Up",
    media_player.Commands.VOLUME_DOWN: "Volume Down",
    media_player.Commands.MUTE_TOGGLE: "Mute",
}


class RvolutionMediaPlayer(MediaPlayerEntity):
    """Media player entity for an R_volution device."""

    def __init__(self, device_config: DeviceConfig, device: RvolutionDevice) -> None:
        self._device = device
        entity_id = f"media_player.{device_config.identifier}"
        super().__init__(
            entity_id,
            device_config.name,
            FEATURES,
            {
                media_player.Attributes.STATE: media_player.States.UNKNOWN,
                media_player.Attributes.VOLUME: 0,
                media_player.Attributes.MUTED: False,
                media_player.Attributes.MEDIA_TITLE: "",
                media_player.Attributes.MEDIA_ARTIST: "",
                media_player.Attributes.MEDIA_ALBUM: "",
                media_player.Attributes.MEDIA_IMAGE_URL: "",
                media_player.Attributes.MEDIA_TYPE: "",
                media_player.Attributes.MEDIA_DURATION: 0,
                media_player.Attributes.MEDIA_POSITION: 0,
            },
            device_class=media_player.DeviceClasses.STREAMING_BOX,
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        attributes: dict[str, Any] = {
            media_player.Attributes.STATE: self.map_entity_states(self._device.state),
            media_player.Attributes.MEDIA_TITLE: self._device.media_title,
            media_player.Attributes.MEDIA_ARTIST: self._device.media_artist,
            media_player.Attributes.MEDIA_ALBUM: self._device.media_album,
            media_player.Attributes.MEDIA_IMAGE_URL: self._device.media_image_url,
            media_player.Attributes.MEDIA_TYPE: self._device.media_type,
            media_player.Attributes.MEDIA_DURATION: self._device.media_duration,
            media_player.Attributes.MEDIA_POSITION: self._device.media_position,
        }
        if self._device.volume is not None:
            attributes[media_player.Attributes.VOLUME] = self._device.volume
        if self._device.muted is not None:
            attributes[media_player.Attributes.MUTED] = self._device.muted
        self.update(attributes)

    async def _handle_command(
        self, entity: Any, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        try:
            if cmd_id == media_player.Commands.ON:
                ok = await self._device.power_on()
            elif cmd_id == media_player.Commands.OFF:
                ok = await self._device.power_off()
            elif cmd_id == media_player.Commands.TOGGLE:
                ok = await self._device.power_toggle()
            elif cmd_id in _COMMAND_MAP:
                ok = await self._device.send_command(_COMMAND_MAP[cmd_id])
            else:
                return StatusCodes.NOT_IMPLEMENTED
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
        except Exception as err:  # pylint: disable=broad-except
            _LOG.error("[%s] Command '%s' error: %s", self.id, cmd_id, err)
            return StatusCodes.SERVER_ERROR
