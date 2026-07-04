"""
R_volution device client.

Communicates with R_volution players over two channels:
- IR-over-IP control on port 80 (``/cgi-bin/do?cmd=ir_code``) - fire-and-forget commands.
- R_video metadata API on port 8990 (``/PlaybackInformation`` + ``/LastMedia``) -
  optional now-playing information, only available while the R_video app is active.

Reachability is probed with a plain TCP connect to port 80. The integration never
sends an IR command to test connectivity, so no on-screen overlay is ever triggered
by the integration itself.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import json
import logging
import xml.etree.ElementTree as ET
from typing import Any

import aiohttp

from uc_intg_rvolution.const import IR_PORT, RVIDEO_PORT, commands_for

_LOG = logging.getLogger(__name__)


class RvolutionClient:
    """HTTP client for a single R_volution device."""

    def __init__(self, host: str, device_type: str, port: int = IR_PORT) -> None:
        self._host = host
        self._device_type = device_type
        self._port = port
        self._commands = commands_for(device_type)
        self._session: aiohttp.ClientSession | None = None
        self._session_lock = asyncio.Lock()

    @property
    def host(self) -> str:
        return self._host

    @property
    def available_commands(self) -> list[str]:
        return list(self._commands.keys())

    def has_command(self, command: str) -> bool:
        return command in self._commands

    async def _ensure_session(self) -> aiohttp.ClientSession:
        async with self._session_lock:
            if self._session is None or self._session.closed:
                connector = aiohttp.TCPConnector(limit_per_host=1, force_close=True)
                timeout = aiohttp.ClientTimeout(total=8, connect=4, sock_read=6)
                self._session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={"Accept": "*/*", "Connection": "close"},
                )
            return self._session

    async def close(self) -> None:
        async with self._session_lock:
            if self._session and not self._session.closed:
                await self._session.close()
            self._session = None

    async def is_reachable(self, timeout: float = 3.0) -> bool:
        """Non-disruptive reachability check: open a TCP socket to the IR port."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), timeout=timeout
            )
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:  # pylint: disable=broad-except
                pass
            return True
        except (OSError, asyncio.TimeoutError) as err:
            _LOG.debug("[%s] Reachability check failed: %s", self._host, err)
            return False

    async def send_command(self, command: str) -> bool:
        """Send an IR command by name. Returns True if the device accepted it."""
        code = self._commands.get(command)
        if code is None:
            _LOG.warning("[%s] Unknown command '%s'", self._host, command)
            return False

        url = f"http://{self._host}:{self._port}/cgi-bin/do?cmd=ir_code&ir_code={code}"
        try:
            session = await self._ensure_session()
            async with session.get(url, ssl=False) as response:
                await response.read()
                if response.status == 200:
                    _LOG.debug("[%s] Sent command '%s'", self._host, command)
                    return True
                _LOG.warning(
                    "[%s] Command '%s' returned HTTP %s",
                    self._host,
                    command,
                    response.status,
                )
                return False
        except Exception as err:  # pylint: disable=broad-except
            _LOG.warning("[%s] Command '%s' failed: %s", self._host, command, err)
            return False

    async def _rvideo_post(self, endpoint: str) -> str | None:
        """POST to the R_video API. Returns response text or None on any failure.

        Failures here are expected and benign (the R_video app is not running / the
        device is in the file explorer), so they are only logged at debug level and
        never retried.
        """
        url = f"http://{self._host}:{RVIDEO_PORT}{endpoint}"
        try:
            session = await self._ensure_session()
            async with session.post(
                url, ssl=False, timeout=aiohttp.ClientTimeout(total=3)
            ) as response:
                if response.status != 200:
                    return None
                return await response.text()
        except Exception as err:  # pylint: disable=broad-except
            _LOG.debug("[%s] R_video %s unavailable: %s", self._host, endpoint, err)
            return None

    async def get_playback_information(self) -> dict[str, str] | None:
        """Return the R_video playback info map, or None when unavailable."""
        response = await self._rvideo_post("/PlaybackInformation")
        if not response:
            return None
        try:
            xml_content = json.loads(response).get("XmlContent", "")
            if not xml_content:
                return None
            root = ET.fromstring(xml_content)
            info: dict[str, str] = {}
            for param in root.findall(".//param"):
                name = param.get("name")
                value = param.get("value")
                if name is not None and value is not None:
                    info[name] = value
            return info or None
        except (json.JSONDecodeError, ET.ParseError) as err:
            _LOG.debug("[%s] Failed to parse PlaybackInformation: %s", self._host, err)
            return None

    async def get_last_media(self) -> dict[str, Any] | None:
        """Return the R_video current media metadata, or None when unavailable."""
        response = await self._rvideo_post("/LastMedia")
        if not response:
            return None
        try:
            data = json.loads(response)
            if data.get("ErrorCode") not in (None, "None"):
                return None
            return data.get("Media") or None
        except json.JSONDecodeError as err:
            _LOG.debug("[%s] Failed to parse LastMedia: %s", self._host, err)
            return None
