"""
Constants for the R_volution integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

DEVICE_TYPE_AMLOGIC = "amlogic"
DEVICE_TYPE_PLAYER = "player"

IR_PORT = 80
RVIDEO_PORT = 8990

AMLOGIC_COMMANDS: dict[str, str] = {
    "Power On": "4CB34040",
    "Power Off": "4AB54040",
    "Power Toggle": "B24D4040",
    "Play/Pause": "AC534040",
    "Stop": "BD424040",
    "Next": "E11E4040",
    "Previous": "E01F4040",
    "Fast Forward": "E41BBF00",
    "Fast Reverse": "E31CBF00",
    "Volume Up": "E7184040",
    "Volume Down": "E8174040",
    "Mute": "BC434040",
    "Cursor Up": "F40B4040",
    "Cursor Down": "F10E4040",
    "Cursor Left": "EF104040",
    "Cursor Right": "EE114040",
    "Cursor Enter": "F20D4040",
    "Home": "E51A4040",
    "Menu": "BA454040",
    "Return": "BD424040",
    "Info": "BB444040",
    "10 sec forward": "BF404040",
    "10 sec rewind": "DF204040",
    "60 sec forward": "EE114040",
    "60 sec rewind": "EF104040",
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
    "Function Red": "A68E4040",
    "Function Green": "F50A4040",
    "Function Yellow": "BE414040",
    "Function Blue": "AB544040",
    "3D": "ED124040",
    "Audio": "E6194040",
    "Subtitle": "E41B4040",
    "Zoom": "E21D4040",
    "Repeat": "B9464040",
    "Page Up": "BF404040",
    "Page Down": "DB204040",
    "Delete": "F30C4040",
    "Dimmer": "A45B4040",
    "Explorer": "EA164040",
    "Format Scroll": "EB144040",
    "R_video": "EC134040",
}

PLAYER_COMMANDS: dict[str, str] = {
    "Power On": "ECB34040",
    "Power Off": "ECB54040",
    "Power Toggle": "EC4D4040",
    "Play/Pause": "EC534040",
    "Stop": "EC424040",
    "Next": "EC1E4040",
    "Previous": "EC1F4040",
    "Fast Forward": "E41BBF00",
    "Fast Reverse": "E31CBF00",
    "Volume Up": "EC184040",
    "Volume Down": "EC174040",
    "Mute": "EC434040",
    "Cursor Up": "EC0B4040",
    "Cursor Down": "EC0E4040",
    "Cursor Left": "EC104040",
    "Cursor Right": "EC114040",
    "Cursor Enter": "EC0D4040",
    "Home": "EC1A4040",
    "Menu": "EC454040",
    "Return": "EC424040",
    "Info": "EC444040",
    "10 sec forward": "EC404040",
    "10 sec rewind": "EC204040",
    "60 sec forward": "EC114040",
    "60 sec rewind": "EC104040",
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
    "Function Red": "EC574040",
    "Function Green": "EC0A4040",
    "Function Yellow": "EC414040",
    "Function Blue": "EC544040",
    "3D": "EC124040",
    "Audio": "EC194040",
    "Subtitle": "EC1B4040",
    "Zoom": "EC1D4040",
    "Repeat": "EC464040",
    "Page Up": "EC404040",
    "Page Down": "EC204040",
    "Delete": "EC0C4040",
    "Dimmer": "EC5B4040",
    "Explorer": "EC164040",
    "Format Scroll": "EC144040",
    "Mouse": "EC474040",
    "HDMI/XMOS Audio Toggle": "BA45BF00",
}


def commands_for(device_type: str) -> dict[str, str]:
    """Return the IR command map for the given device type."""
    if device_type == DEVICE_TYPE_PLAYER:
        return PLAYER_COMMANDS
    return AMLOGIC_COMMANDS
