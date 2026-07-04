# R_volution Integration for Unfolded Circle Remote 2/3

Control your R_volution media players directly from your Unfolded Circle Remote 2 or Remote 3 with comprehensive remote control, **multi-device support**, and **real-time media player functionality**.

![R_volution](https://img.shields.io/badge/R_volution-Media%20Players-blue)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-rvolution?style=flat-square)](https://github.com/mase1981/uc-intg-rvolution/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-rvolution?style=flat-square)](https://github.com/mase1981/uc-intg-rvolution/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://unfolded.community/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-rvolution/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)


## Features

This integration provides full control of your R_volution media players directly from your Unfolded Circle Remote, with automatic multi-device detection and comprehensive media player and remote functionality.

---
## ❤️ Support Development ❤️

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

### 📺 **Multi-Device Support**

- **Multi-Device Setup** - Configure multiple R_volution devices in a single integration
- **Device Type Support** - Supports both Amlogic (PlayerOne 8K, Pro 8K, Mini) and R_volution Player devices
- **Smart Naming** - Automatic entity naming using real device information from API
- **Port Configuration** - Flexible port configuration for different device setups

#### **Per-Device Entities**
Each R_volution device creates six entities:
- **Media Player Entity** - Media playback control with now-playing status (title, artwork, position)
- **Remote Entity** - Full IR remote with three on-screen UI pages and physical-button mapping
- **Power Switch** - Discrete on/off/toggle power control
- **Quick Launch Select** - Jump to Home, Explorer, R_video (Amlogic) or Menu
- **Playback Sensor** - Current playback state (Playing / Paused / Idle / Off)
- **Now Playing Sensor** - Title of the currently playing media

> **Upgrading from v2.x → v3.0.0:** This release is a full rewrite on the ucapi-framework and changes the entity ID format (e.g. `mp_<id>` → `media_player.<id>`). After upgrading, re-add the R_volution entities to any activities or pages that referenced the old ones. Existing device configuration is preserved.

### 🎮 **Remote Control Functionality**

#### **Comprehensive Button Support**
Real R_volution IR protocol implementation with device-specific command sets:

**Power Control** (3 commands):
- **Power On**, **Power Off**, **Power Toggle** - Complete power management

**Navigation** (8 commands):
- **D-Pad**: Up, Down, Left, Right, Enter - Menu navigation
- **Control**: Home, Menu, Return - Interface navigation

**Playback Control** (6 commands):
- **Transport**: Play/Pause, Stop, Next, Previous, Fast Forward, Fast Reverse
- **Seeking**: 10/60 second forward/reverse skipping

**Number Pad** (10 commands):
- **Digits 0-9** - Direct input and channel/content selection

**Volume Control** (3 commands):
- **Volume Up/Down**, **Mute Toggle** - Audio control

**Color Functions** (4 commands):
- **Red**, **Green**, **Yellow**, **Blue** - Interactive functions

**Special Functions** (15+ commands):
- **Audio Track**, **Subtitle**, **Zoom**, **Repeat**, **3D**, **Info**
- **Explorer**, **Format Scroll**, **Page Up/Down**, **Delete**
- **Device-specific**: Dimmer, Mouse (Player), R_video (Amlogic), HDMI/XMOS Audio Toggle (Player)

#### **Device-Specific Command Sets**
- **Amlogic Devices** (PlayerOne 8K, Pro 8K, Mini): 47 IR commands
- **R_volution Players**: 49 IR commands including HDMI/XMOS Audio Toggle
- **Automatic Detection**: Device type determines available command set

#### **User Interface Features**
- **3 Comprehensive UI Pages**: Main Controls, Numbers & Functions, Advanced Controls
- **On-Screen Remote**: Full remote interface displayed on Remote screen
- **Button Mapping**: Physical Remote button mapping for core functions
- **Simple Commands**: All buttons available as simple command shortcuts

### 🎵 **Media Player Functionality**

#### **Playback Control**
- **Transport Controls** - Play, Pause, Stop, Next, Previous
- **Seeking** - Fast Forward, Rewind, Skip controls
- **Volume Control** - Volume Up/Down, Mute toggle

#### **Media Information Display**
- **Current Media** - Title, position, duration display from device API
- **Playback State** - Playing, Paused, Stopped status
- **Audio Settings** - Volume level, mute status
- **Media Info** - Full support for currently playing media info, name, title, image, etc
- **Advanced Features** - Subtitle status, audio track, repeat mode (when available)

#### **Status Synchronization**
- **Real-time Updates** - Media status synchronized from device when available
- **Connection Monitoring** - Automatic reconnection and status updates
- **State Persistence** - Maintains entity state across Remote reboots

### **Device Requirements**

#### **R_volution Device Compatibility**
- **Amlogic Models**: PlayerOne 8K, Pro 8K, Mini
- **R_volution Players**: All R_volution Player models
- **Firmware**: Any current firmware version with HTTP API enabled
- **Network**: Ethernet or Wi-Fi connected R_volution device
- **API Access**: HTTP REST API and IR command interface (enabled by default)

### **Protocol Requirements**

- **Protocol**: R_volution HTTP API + IR Commands
- **Port**: 80 (default) or custom port
- **Network Access**: Device must be on same local network
- **Connection**: HTTP-based communication
- **IR Control**: HTTP-based IR command interface via `/cgi-bin/do` endpoint

### **Network Requirements**

- **Local Network Access** - Integration requires same network as R_volution devices
- **HTTP Protocol** - Firewall must allow HTTP traffic
- **Static IP Recommended** - Device should have static IP or DHCP reservation
- **Port Access**: HTTP API port 80 (default) or custom port configuration

## Installation

### Option 1: Remote Web Interface (Recommended)
1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-rvolution/releases) page
2. Download the latest `uc-intg-rvolution-<version>-aarch64.tar.gz` file
3. Open your remote's web interface (`http://your-remote-ip`)
4. Go to **Settings** → **Integrations** → **Add Integration**
5. Click **Upload** and select the downloaded `.tar.gz` file

### Option 2: Docker (Advanced Users)

The integration is available as a pre-built Docker image from GitHub Container Registry:

**Image**: `ghcr.io/mase1981/uc-intg-rvolution:latest`

**Docker Compose:**
```yaml
services:
  uc-intg-rvolution:
    image: ghcr.io/mase1981/uc-intg-rvolution:latest
    container_name: uc-intg-rvolution
    network_mode: host
    volumes:
      - </local/path>:/data
    environment:
      - UC_CONFIG_HOME=/data
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name uc-rvolution --restart unless-stopped --network host -v rvolution-config:/app/config -e UC_CONFIG_HOME=/app/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9090 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-rvolution:latest
```

## Configuration

### Step 1: Prepare Your R_volution Devices

**IMPORTANT**: R_volution devices must be powered on and connected to your network before adding the integration.

#### Verify Network Connection:
1. Ensure R_volution devices are powered on and connected to network
2. Note the IP address for each device
3. Verify HTTP API is accessible (test `http://device-ip/device/info`)
4. Recommended: Give static IP addresses to your R_volution devices

#### Network Setup:
- **Wired Connection**: Recommended for stability
- **Static IP**: Recommended via DHCP reservation
- **Firewall**: Allow HTTP traffic
- **Network Isolation**: Must be on same subnet as Remote

### Step 2: Setup Integration

1. After installation, go to **Settings** → **Integrations**
2. The R_volution integration should appear in **Available Integrations**
3. Click **"Configure"** to begin setup:

#### **Device Configuration:**
- **Device Name**: Location-based name (e.g., "Living Room R_volution", "Kitchen PlayerOne")
- **IP Address**: R_volution device IP (e.g., 192.168.1.100)
- **Device Type**: Select Amlogic (PlayerOne 8K, Pro 8K, Mini) or R_volution Player

To add more devices, run the integration setup again and choose **"Add a new device"** in configuration mode. Each device can be updated or removed from the same screen.

#### **Connection Test:**
- The integration verifies reachability with a lightweight TCP check on port 80 (no on-screen command is ever sent to the device). Setup fails only if the device is unreachable.

## Using the Integration

### Media Player Entity

The media player entity provides complete control:

- **Playback Control**: Play, Pause, Stop, Next, Previous
- **Volume Control**: Volume Up/Down, Mute
- **Seeking**: Fast Forward, Rewind controls
- **Media Info**: Current title, position, duration
- **State Display**: Current playback status

### Remote Entity

The remote entity provides comprehensive device control:

- **Power Control**: On/Off/Toggle
- **Navigation**: D-Pad and menu controls
- **Playback**: Transport controls
- **Volume**: Volume and mute controls
- **Numbers**: Numeric keypad (0-9)
- **Special Functions**: Audio, Subtitle, Zoom, and more
- **3 UI Pages**: Organized button layout for all functions

### Multi-Device Management

When using multiple devices:
- **Independent Control**: Each device operates independently
- **Room-Based Activities**: Create activities for each room/device
- **Centralized Overview**: All devices visible in integration settings
- **Device Types**: Proper command sets for Amlogic vs Player devices

## Credits

- **Developer**: Meir Miyara
- **R_volution**: Media player platform
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **Protocol**: R_volution HTTP API + IR Commands
- **Community**: Testing and feedback from UC community

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0) - see LICENSE file for details.

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-rvolution/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)
- **R_volution Support**: [Official R_volution Support](https://rvolutionmedia.com/support/)

---

**Made with ❤️ for the Unfolded Circle and R_volution Communities**

**Thank You**: Meir Miyara
