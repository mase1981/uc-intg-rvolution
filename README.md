# R_volution Integration for Unfolded Circle Remote 2/3

Control your R_volution media players directly from your Unfolded Circle Remote 2 or Remote 3 with comprehensive remote control and media player functionality.

![R_volution](https://img.shields.io/badge/R_volution-Media%20Players-blue)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-rvolution)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-rvolution/total)
![License](https://img.shields.io/badge/license-MPL--2.0-blue)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA)](https://github.com/sponsors/mase1981/button)

## Features

This integration provides full control of your R_volution media players directly from your Unfolded Circle Remote, with automatic multi-device detection and comprehensive media player and remote functionality.

### 📺 **Multi-Device Support**

- **Multi-Device Setup**: Configure up to 10 R_volution devices in a single integration
- **Device Type Support**: Supports both Amlogic (PlayerOne 8K, Pro 8K, Mini) and R_volution Player devices
- **Smart Naming**: Automatic entity naming using real device information from API
- **Port Configuration**: Flexible port configuration for different device setups

#### **Per-Device Entities**
Each R_volution device creates two entities:
- **Media Player Entity**: `[Device Name] (Device Type)` - Media playback control with status display
- **Remote Entity**: `[Device Name] Remote (Device Type)` - Full remote control with on-screen interface

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
- **Transport Controls**: Play, Pause, Stop, Next, Previous
- **Seeking**: Fast Forward, Rewind, Skip controls
- **Volume Control**: Volume Up/Down, Mute toggle

#### **Media Information Display**
- **Current Media**: Title, position, duration display from device API
- **Playback State**: Playing, Paused, Stopped status
- **Audio Settings**: Volume level, mute status
- **Advanced Features**: Subtitle status, audio track, repeat mode (when available)

#### **Status Synchronization**
- **Real-time Updates**: Media status synchronized from device when available
- **Connection Monitoring**: Automatic reconnection and status updates
- **State Persistence**: Maintains entity state across Remote reboots

## Device Requirements

### **R_volution Device Compatibility**
- **Amlogic Models**: PlayerOne 8K, Pro 8K, Mini
- **R_volution Players**: All R_volution Player models
- **Firmware**: Any current firmware version with HTTP API enabled
- **Network**: Ethernet or Wi-Fi connected R_volution device
- **API Access**: HTTP REST API and IR command interface (enabled by default)

### **Network Requirements**
- **Local Network Access** - Integration requires same network as R_volution devices
- **Port Access**: 
  - **HTTP API**: Port 80 (default) or custom port configuration
  - **IR Commands**: HTTP-based IR control via `/cgi-bin/do` endpoint
- **Firewall**: No special configuration required for standard home networks

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
      - ./data:/config
    environment:
      - UC_INTEGRATION_HTTP_PORT=9090
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name=uc-intg-rvolution --network host -v </local/path>:/config --restart unless-stopped ghcr.io/mase1981/uc-intg-rvolution:latest
```

## Configuration

### Step 1: Prepare Your R_volution Devices

1. **Device Setup:**
   - Ensure R_volution devices are powered on and connected to your network
   - Recommended: Give static IP addresses to your R_volution devices
   - Verify devices are accessible via their web interface: `http://device-ip/`
   - Note device types (Amlogic or Player) for proper configuration

2. **Network Discovery:**
   - Find R_volution device IP addresses via router admin interface
   - Or use network scanning tools to locate devices on port 80
   - Test HTTP access: `http://device-ip/device/info` should return device information

3. **Multiple Devices:**
   - Each R_volution device should have a static or reserved IP address
   - Note the location/name for each device (Living Room, Bedroom, etc.)
   - Identify device types for proper command set configuration

### Step 2: Setup Integration

1. After installation, go to **Settings** → **Integrations**
2. The R_volution integration should appear in **Available Integrations**
3. Click **"Configure"** and follow the setup wizard:

   **Device Count Selection:**
   - Choose number of R_volution devices to configure (1-10)

   **Device Configuration:**
   For each device:
   - **Device IP Address**: R_volution device IP (e.g., 192.168.1.100 or 192.168.1.100:8080)
   - **Device Name**: Location-based name (e.g., "Living Room R_volution", "Kitchen PlayerOne")
   - **Device Type**: Select Amlogic (PlayerOne 8K, Pro 8K, Mini) or R_volution Player

4. Click **"Complete Setup"** when all devices are configured
5. Entities will be created for each successful device:
   - **[Device Name] (Device Type)** (Media Player Entity)
   - **[Device Name] Remote (Device Type)** (Remote Entity)

### Step 3: Add Entities to Activities

1. Go to **Activities** in your remote interface
2. Edit or create an activity for each room/device
3. Add R_volution entities from the **Available Entities** list:
   - **R_volution Media Player** - Media playback control with status display
   - **R_volution Remote** - Full remote control with comprehensive on-screen interface
4. Configure button mappings and UI layout as desired
5. Save your activity

## Usage Examples

### Single Device Setup
```
Setup Input:
- Device Count: 1
- IP Address: 192.168.1.100
- Name: "Living Room R_volution"
- Type: Amlogic (PlayerOne 8K, Pro 8K, Mini)

Result:
- Media Player: "Living Room R_volution (Amlogic Player)"
- Remote: "Living Room R_volution Remote (Amlogic Remote)"
```

### Multi-Device Setup
```
Setup Input:
- Device Count: 3
- Device 1: 192.168.1.100, "Living Room PlayerOne", Amlogic
- Device 2: 192.168.1.101, "Kitchen R_volution", Player  
- Device 3: 192.168.1.102:8080, "Bedroom PlayerOne", Amlogic

Result:
- Living Room PlayerOne (Amlogic Player) + Remote
- Kitchen R_volution (R_volution Player) + Remote
- Bedroom PlayerOne (Amlogic Player) + Remote
```

## Troubleshooting

### Common Issues

**Device Not Found:**
- Verify R_volution device IP address is correct
- Check device is powered on and connected to network
- Try accessing device web interface: `http://device-ip/`
- Test device info endpoint: `http://device-ip/device/info`
- Ensure Remote and R_volution device are on same network subnet

**Connection Timeout:**
- Check firewall settings on router/network
- Verify R_volution device is responding (try ping test)
- Some devices may use different ports - try common ports (80, 8080)
- Ensure HTTP API is enabled on R_volution device

**Remote Not Working:**
- Check device power state (must be on, not standby)
- Verify network connectivity to device
- Review integration logs for error messages
- Confirm correct device type selection (Amlogic vs Player)

**Media Player Not Updating:**
- Some R_volution devices may not provide status API
- Check device `/device/status` endpoint availability
- Media player will work for control even without status updates
- Verify device supports status information via HTTP API

### Debug Information

Enable detailed logging for troubleshooting:

**Docker Environment:**
```bash
# Add to docker-compose.yml environment section
- LOG_LEVEL=DEBUG

# View logs
docker logs uc-intg-rvolution
```

**Integration Logs:**
- **Remote Interface**: Settings → Integrations → R_volution → View Logs
- **Common Errors**: Connection timeouts, IR command failures, device detection issues

**Device Verification:**
- **HTTP Test**: Try accessing `http://device-ip/` in web browser
- **Device Info**: Access `http://device-ip/device/info` for device information
- **Status Test**: Check `http://device-ip/device/status` for media status
- **IR Test**: Manual test `http://device-ip/cgi-bin/do?cmd=ir_code&ir_code=POWER_CODE`

**Network Scan:**
Use network tools to verify device accessibility:
```bash
# Ping test
ping device-ip

# Port scan
nmap -p 80,8080 device-ip

# HTTP test
curl http://device-ip/device/info
```

## For Developers

### Local Development

1. **Clone and setup:**
   ```bash
   git clone https://github.com/mase1981/uc-intg-rvolution.git
   cd uc-intg-rvolution
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configuration:**
   Integration uses local config files:
   ```bash
   # Configuration automatically created during setup
   # Located in UC_CONFIG_HOME or project root: config.json
   ```

3. **Development with Simulator:**
   ```bash
   # Start R_volution simulator for testing
   python r_volution_simulator.py --amlogic 2 --player 2
   
   # Run integration
   python -m uc_intg_rvolution.driver
   # Integration runs on localhost:9090
   ```

4. **VS Code debugging:**
   - Open project in VS Code
   - Use F5 to start debugging session
   - Configure integration with simulator or real devices

### Project Structure

```
uc-intg-rvolution/
├── uc_intg_rvolution/          # Main package
│   ├── __init__.py             # Package info  
│   ├── client.py               # R_volution HTTP client
│   ├── config.py               # Configuration management
│   ├── driver.py               # Main integration driver
│   ├── media_player.py         # Media player entity
│   └── remote.py               # Remote control entity
├── .github/workflows/          # GitHub Actions CI/CD
│   └── build.yml               # Automated build pipeline
├── docker-compose.yml          # Docker deployment
├── Dockerfile                  # Container build instructions
├── docker-entry.sh             # Container entry point
├── driver.json                 # Integration metadata
├── requirements.txt            # Dependencies
├── pyproject.toml              # Python project config
├── r_volution_simulator.py     # Multi-device simulator for testing
└── README.md                   # This file
```

### Development Features

#### **R_volution Protocol Implementation**
Complete R_volution API implementation:
- **HTTP Client**: Comprehensive HTTP API client with connection management
- **IR Commands**: Full IR command support for both device types
- **Device Detection**: Automatic device info and capability detection
- **Status Monitoring**: Media status synchronization when available

#### **Multi-Device Architecture**
Production-ready multi-device support:
- **Configuration Management**: Persistent multi-device configuration with reboot survival
- **Entity Lifecycle**: Independent entity management per device
- **Connection Monitoring**: Per-device health monitoring and reconnection
- **State Management**: Maintains entity state across Remote reboots

#### **Device Type Support**
Comprehensive device type handling:
- **Amlogic Devices**: Full command set for PlayerOne 8K, Pro 8K, Mini
- **R_volution Players**: Complete Player command set with unique functions
- **Command Mapping**: Device-specific IR code mapping
- **Auto-Detection**: Automatic device type recognition and configuration

#### **Development Simulator**
Included multi-device simulator for development:
- **Multi-Device Support**: Simulate multiple R_volution devices simultaneously
- **Device Types**: Both Amlogic and Player device simulation
- **HTTP API**: Complete API simulation including status endpoints
- **IR Command Processing**: Full IR command handling and state management

### Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Start simulator for testing
python r_volution_simulator.py --amlogic 2 --player 2

# Run integration
python -m uc_intg_rvolution.driver

# Configure integration with simulator devices
# Test all media player and remote functions

# Single device testing
python r_volution_simulator.py --single --type amlogic --port 8080
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test with simulator
4. Test with real R_volution devices if available
5. Verify all device types work correctly
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push to branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

## Architecture Notes

### **Current Implementation**
- **Dual Entity Design**: Media Player + Remote entities per device for complete control
- **Production Tested**: Verified working with R_volution simulator and real devices
- **HTTP-Based Communication**: Reliable HTTP API communication with proper error handling
- **Device-Specific Support**: Tailored command sets for different R_volution device types

### **Entity Design Philosophy**
- **Media Player**: Focused on media playback control and status display
- **Remote**: Comprehensive remote control with full button interface
- **Complementary**: Both entities work together for complete device control
- **User Choice**: Users can choose to use one or both entities per activity

### **Protocol Implementation**
- **HTTP REST API**: Primary communication via HTTP GET requests
- **IR Command Interface**: Direct IR command sending via `/cgi-bin/do` endpoint
- **Status Synchronization**: Real-time media status updates when supported
- **Error Recovery**: Robust connection management and automatic reconnection

## Credits

- **Developer**: Meir Miyara
- **R_volution Protocol**: Built using HTTP API analysis and IR command mapping
- **Unfolded Circle**: Remote 2/3 integration framework (ucapi)
- **Community**: Testing and feedback from UC community with R_volution devices

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-rvolution/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **Developer**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara)

---

**Made with ❤️ for the Unfolded Circle Community** 

<<<<<<< HEAD
**Thank You**: Meir Miyara
=======
**Thank You**: Meir Miyara
>>>>>>> 441245fa880724bb3723b038c2114307f227a354
