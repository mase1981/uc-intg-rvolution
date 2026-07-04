"""
R_volution device interface.

Uses the polling pattern: reachability is probed with a non-disruptive TCP connect
to the IR port, and optional now-playing metadata is fetched from the R_video API
when available. A missing R_video API is treated as "no rich metadata right now",
never as a disconnection, so no reconnection/probe storm is ever triggered.

Because R_volution players are controlled one-way over IR, the device follows the
"TV-off" pattern: an unreachable device reports OFF (not UNAVAILABLE) and stays
available so the user can always power it back on.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any

from ucapi_framework import PollingDevice

from uc_intg_rvolution.client import RvolutionClient
from uc_intg_rvolution.config import DeviceConfig

_LOG = logging.getLogger(__name__)

POLL_INTERVAL = 10


class RvolutionDevice(PollingDevice):
    """Polling device interface for an R_volution player."""

    def __init__(self, device_config: DeviceConfig, **kwargs: Any) -> None:
        super().__init__(device_config, poll_interval=POLL_INTERVAL, **kwargs)
        self._device_config = device_config
        self._client: RvolutionClient | None = None
        self._connect_lock = asyncio.Lock()
        self._state = "OFF"

        self.volume: int | None = None
        self.muted: bool | None = None
        self.media_title = ""
        self.media_artist = ""
        self.media_album = ""
        self.media_type = ""
        self.media_image_url = ""
        self.media_duration = 0
        self.media_position = 0

    # ------------------------------------------------------------------ props
    @property
    def identifier(self) -> str:
        return self._device_config.identifier

    @property
    def name(self) -> str:
        return self._device_config.name

    @property
    def address(self) -> str:
        return self._device_config.host

    @property
    def log_id(self) -> str:
        return f"{self.name} ({self.address})"

    @property
    def device_type(self) -> str:
        return self._device_config.device_type

    @property
    def client(self) -> RvolutionClient | None:
        return self._client

    def _get_client(self) -> RvolutionClient:
        if self._client is None:
            self._client = RvolutionClient(
                self._device_config.host,
                self._device_config.device_type,
                self._device_config.port,
            )
        return self._client

    # ------------------------------------------------------------- lifecycle
    async def establish_connection(self) -> None:
        """Verify reachability without disrupting the device.

        Never raises: an unreachable player reports OFF so the user can power it
        on (TV-off pattern). The poll loop keeps probing afterwards.
        """
        async with self._connect_lock:
            client = self._get_client()
            if await client.is_reachable():
                await self._refresh_state()
            else:
                self._reset_media()
                self._state = "OFF"
                _LOG.info("[%s] Not reachable at setup, reporting OFF", self.log_id)

    async def poll_device(self) -> None:
        client = self._get_client()
        if not await client.is_reachable():
            if self._state != "OFF":
                self._reset_media()
                self._state = "OFF"
                self.push_update()
            return
        await self._refresh_state()
        self.push_update()

    async def disconnect(self) -> None:
        async with self._connect_lock:
            if self._client:
                await self._client.close()
                self._client = None
        self._state = "OFF"
        await super().disconnect()

    # --------------------------------------------------------------- helpers
    def _reset_media(self) -> None:
        self.media_title = ""
        self.media_artist = ""
        self.media_album = ""
        self.media_type = ""
        self.media_image_url = ""
        self.media_duration = 0
        self.media_position = 0

    async def _refresh_state(self) -> None:
        """Refresh state from the R_video API (best effort).

        When the R_video API is unavailable (file explorer, no playback), the device
        is simply reachable-and-idle: state ON with cleared media metadata.
        """
        client = self._get_client()
        playback = await client.get_playback_information()

        if not playback:
            self._reset_media()
            self._state = "ON"
            return

        self._apply_volume(playback)

        playback_state = playback.get("playback_state", "")
        player_state = playback.get("player_state", "")
        is_playing = player_state == "file_playback"

        if playback_state == "playing" or (is_playing and playback_state != "paused"):
            self._state = "PLAYING"
        elif playback_state == "paused":
            self._state = "PAUSED"
        elif playback_state == "buffering":
            self._state = "BUFFERING"
        else:
            self._state = "ON"

        if self._state in ("PLAYING", "PAUSED", "BUFFERING"):
            self.media_duration = _to_int(playback.get("playback_duration"), self.media_duration)
            self.media_position = _to_int(playback.get("playback_position"), self.media_position)
            await self._refresh_media(client)
        else:
            self._reset_media()

    def _apply_volume(self, playback: dict[str, str]) -> None:
        if "playback_volume" in playback:
            self.volume = _to_int(playback.get("playback_volume"), self.volume)
        if "playback_mute" in playback:
            self.muted = _to_int(playback.get("playback_mute"), 0) == 1

    async def _refresh_media(self, client: RvolutionClient) -> None:
        media = await client.get_last_media()
        if not media:
            return

        media_type = media.get("Type", "")
        title = media.get("Title", "")
        poster = media.get("PosterUrl", "") or ""

        if media_type == "Movie":
            self.media_title = title
            self.media_artist = ""
            self.media_album = ""
            self.media_type = "MOVIE"
        elif media_type == "TVShowEpisode":
            season = media.get("Season", 0)
            episode = media.get("Episode", 0)
            self.media_title = title
            self.media_artist = media.get("TvShowName", "")
            self.media_album = (
                f"Season {season} Episode {episode}" if season and episode else ""
            )
            self.media_type = "TVSHOW"
        else:
            self.media_title = title
            self.media_artist = ""
            self.media_album = ""
            self.media_type = "VIDEO"

        self.media_image_url = poster

    # ---------------------------------------------------------------- commands
    async def send_command(self, command: str) -> bool:
        return await self._get_client().send_command(command)

    async def power_on(self) -> bool:
        result = await self.send_command("Power On")
        if result:
            self._state = "ON"
            self.push_update()
        return result

    async def power_off(self) -> bool:
        result = await self.send_command("Power Off")
        if result:
            self._reset_media()
            self._state = "OFF"
            self.push_update()
        return result

    async def power_toggle(self) -> bool:
        return await self.send_command("Power Toggle")


def _to_int(value: Any, default: int | None) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default if default is not None else 0
