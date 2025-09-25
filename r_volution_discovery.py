#!/usr/bin/env python3
"""
R_volution Discovery Script

Author: Meir Miyara
Email: meir.miyara@gmail.com

This script performs comprehensive discovery and analysis of R_volution media players
to diagnose connection issues and optimize integration compatibility.
"""

import json
import socket
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import sys
import traceback
import threading
import subprocess
import platform


class RvolutionDiscovery:
    """Comprehensive R_volution device discovery and analysis."""
    
    def __init__(self, device_ip: str, http_port: int = 80):
        """Initialize discovery with configurable HTTP port."""
        self.device_ip = device_ip
        self.http_port = http_port
        self.discovery_report = {
            "device_ip": device_ip,
            "http_port": http_port,
            "discovery_timestamp": datetime.now().isoformat(),
            "script_version": "1.0.0",
            "platform_info": self._get_platform_info(),
            "device_analysis": {},
            "connectivity_tests": {},
            "command_verification": {},
            "port_discovery": {},
            "network_analysis": {},
            "integration_recommendations": {},
            "errors": []
        }
        
        # Current integration command set (from client.py)
        self.amlogic_commands = {
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
            "Info": "BB444040"
        }
        
        # R_volution Player command set (from PDF)
        self.player_commands = {
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
            "HDMI/XMOS Audio Toggle": "BA45BF00"  # Player-specific
        }
        
        # Common ports to test
        self.test_ports = [80, 8080, 9006, 9090, 443, 8443, 49152, 1900]
        
    def _get_platform_info(self) -> Dict[str, Any]:
        """Get platform and environment information."""
        try:
            return {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "hostname": socket.gethostname(),
                "local_ip": self._get_local_ip()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_local_ip(self) -> str:
        """Get local machine IP address."""
        try:
            # Connect to a dummy address to get local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "Unknown"
    
    def run_discovery(self) -> Dict[str, Any]:
        """Run comprehensive R_volution discovery."""
        print("R_volution Device Discovery & Analysis")
        print("=" * 50)
        print(f"Target Device: {self.device_ip}:{self.http_port}")
        print(f"Script Version: {self.discovery_report['script_version']}")
        print(f"Platform: {self.discovery_report['platform_info'].get('system', 'Unknown')}")
        print(f"Local IP: {self.discovery_report['platform_info'].get('local_ip', 'Unknown')}")
        print()
        
        try:
            # Phase 1: Network connectivity analysis
            print("Phase 1: Network Connectivity Analysis")
            self._analyze_network_connectivity()
            
            # Phase 2: Port discovery
            print("\nPhase 2: Port Discovery & Service Detection")
            self._discover_ports_and_services()
            
            # Phase 3: HTTP endpoint analysis
            print("\nPhase 3: HTTP Endpoint Analysis")
            self._analyze_http_endpoints()
            
            # Phase 4: Device information gathering
            print("\nPhase 4: Device Information Gathering")
            self._gather_device_information()
            
            # Phase 5: IR command verification
            print("\nPhase 5: IR Command Verification")
            self._verify_ir_commands()
            
            # Phase 6: Integration compatibility analysis
            print("\nPhase 6: Integration Compatibility Analysis")
            self._analyze_integration_compatibility()
            
            # Phase 7: Generate recommendations
            print("\nPhase 7: Generate Integration Recommendations")
            self._generate_recommendations()
            
        except Exception as e:
            error_msg = f"Discovery failed: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.discovery_report["errors"].append(error_msg)
            self.discovery_report["errors"].append(traceback.format_exc())
        
        return self.discovery_report
    
    def _analyze_network_connectivity(self):
        """Analyze basic network connectivity."""
        connectivity = {
            "ping_test": {},
            "dns_resolution": {},
            "traceroute": {},
            "local_network_analysis": {}
        }
        
        print(f"   Testing ping connectivity to {self.device_ip}...")
        connectivity["ping_test"] = self._test_ping()
        
        print(f"   Analyzing local network configuration...")
        connectivity["local_network_analysis"] = self._analyze_local_network()
        
        print(f"   Testing DNS resolution...")
        connectivity["dns_resolution"] = self._test_dns_resolution()
        
        self.discovery_report["network_analysis"] = connectivity
    
    def _test_ping(self) -> Dict[str, Any]:
        """Test ping connectivity."""
        try:
            system = platform.system().lower()
            if system == "windows":
                cmd = ["ping", "-n", "4", self.device_ip]
            else:
                cmd = ["ping", "-c", "4", self.device_ip]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            response_time = time.time() - start_time
            
            success = result.returncode == 0
            
            return {
                "success": success,
                "return_code": result.returncode,
                "response_time": response_time,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _analyze_local_network(self) -> Dict[str, Any]:
        """Analyze local network configuration."""
        try:
            local_ip = self.discovery_report["platform_info"].get("local_ip", "Unknown")
            device_network = ".".join(self.device_ip.split(".")[:-1]) + ".0/24"
            local_network = ".".join(local_ip.split(".")[:-1]) + ".0/24" if local_ip != "Unknown" else "Unknown"
            
            same_subnet = device_network == local_network
            
            return {
                "local_ip": local_ip,
                "device_ip": self.device_ip,
                "local_network": local_network,
                "device_network": device_network,
                "same_subnet": same_subnet,
                "network_analysis": "Same subnet" if same_subnet else "Different subnets - potential routing issue"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _test_dns_resolution(self) -> Dict[str, Any]:
        """Test DNS resolution if hostname is used."""
        try:
            # Check if device_ip is actually a hostname
            if not self.device_ip.replace(".", "").isdigit():
                resolved_ip = socket.gethostbyname(self.device_ip)
                return {
                    "hostname": self.device_ip,
                    "resolved_ip": resolved_ip,
                    "resolution_successful": True
                }
            else:
                return {
                    "is_ip_address": True,
                    "no_resolution_needed": True
                }
        except Exception as e:
            return {
                "hostname": self.device_ip,
                "resolution_successful": False,
                "error": str(e)
            }
    
    def _discover_ports_and_services(self):
        """Discover open ports and running services."""
        port_discovery = {
            "scanned_ports": self.test_ports,
            "open_ports": [],
            "closed_ports": [],
            "filtered_ports": [],
            "service_detection": {},
            "scan_duration": 0
        }
        
        print(f"   Scanning {len(self.test_ports)} common ports...")
        
        start_time = time.time()
        
        for port in self.test_ports:
            print(f"      Testing port {port}...")
            result = self._test_port(port)
            
            if result["open"]:
                port_discovery["open_ports"].append(port)
                print(f"        ✓ Port {port} OPEN ({result.get('response_time_ms', 0)}ms)")
                
                # Try to detect service
                service_info = self._detect_service(port)
                if service_info:
                    port_discovery["service_detection"][port] = service_info
                    
            elif result.get("filtered"):
                port_discovery["filtered_ports"].append(port)
                print(f"        ? Port {port} FILTERED")
            else:
                port_discovery["closed_ports"].append(port)
                print(f"        ✗ Port {port} CLOSED")
        
        port_discovery["scan_duration"] = time.time() - start_time
        
        print(f"   PORT SCAN SUMMARY:")
        print(f"     Open: {len(port_discovery['open_ports'])} {port_discovery['open_ports']}")
        print(f"     Closed: {len(port_discovery['closed_ports'])}")
        print(f"     Filtered: {len(port_discovery['filtered_ports'])}")
        
        self.discovery_report["port_discovery"] = port_discovery
    
    def _test_port(self, port: int, timeout: float = 3.0) -> Dict[str, Any]:
        """Test if a port is open."""
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            result = sock.connect_ex((self.device_ip, port))
            response_time = time.time() - start_time
            
            sock.close()
            
            return {
                "open": result == 0,
                "response_time_ms": int(response_time * 1000),
                "connection_result": result
            }
            
        except Exception as e:
            return {
                "open": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _detect_service(self, port: int) -> Optional[Dict[str, Any]]:
        """Try to detect what service is running on an open port."""
        try:
            if port == 80:
                return self._detect_http_service(port)
            elif port in [8080, 8443]:
                return self._detect_http_service(port)
            elif port == 443:
                return {"service": "HTTPS", "description": "Secure HTTP"}
            elif port == 9006:
                return {"service": "Possible SkyQ REST API", "description": "Common media device API port"}
            elif port == 1900:
                return {"service": "UPnP/SSDP", "description": "Universal Plug and Play discovery"}
            else:
                return {"service": "Unknown", "port": port}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _detect_http_service(self, port: int) -> Dict[str, Any]:
        """Detect HTTP service details."""
        try:
            protocol = "https" if port == 443 else "http"
            url = f"{protocol}://{self.device_ip}:{port}/"
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'R_volution-Discovery/1.0')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                headers = dict(response.headers)
                content_preview = response.read(512)  # First 512 bytes
                
                return {
                    "service": "HTTP Server",
                    "status_code": response.getcode(),
                    "headers": headers,
                    "server": headers.get("Server", "Unknown"),
                    "content_type": headers.get("Content-Type", "Unknown"),
                    "content_preview": content_preview.decode('utf-8', errors='ignore')[:200]
                }
                
        except Exception as e:
            return {
                "service": "HTTP (connection failed)",
                "error": str(e)
            }
    
    def _analyze_http_endpoints(self):
        """Analyze HTTP endpoints and API availability."""
        http_analysis = {
            "base_url_test": {},
            "device_endpoints": {},
            "api_discovery": {},
            "cgi_bin_test": {}
        }
        
        print(f"   Testing base HTTP access...")
        base_url = f"http://{self.device_ip}:{self.http_port}/"
        http_analysis["base_url_test"] = self._test_http_endpoint(base_url)
        
        # Test common R_volution endpoints
        endpoints_to_test = [
            "/",
            "/device/info",
            "/device/status", 
            "/as/system/information",
            "/cgi-bin/do",
            "/api/v1/device",
            "/api/device/info"
        ]
        
        print(f"   Testing {len(endpoints_to_test)} device endpoints...")
        for endpoint in endpoints_to_test:
            url = f"http://{self.device_ip}:{self.http_port}{endpoint}"
            print(f"      Testing: {endpoint}")
            result = self._test_http_endpoint(url, method="GET")
            http_analysis["device_endpoints"][endpoint] = result
            
            if result.get("success"):
                print(f"        ✓ SUCCESS ({result.get('status_code')})")
            else:
                error = result.get("error", "Unknown")
                print(f"        ✗ FAILED: {error}")
        
        # Test CGI-bin IR command interface
        print(f"   Testing CGI-bin IR command interface...")
        test_ir_url = f"http://{self.device_ip}:{self.http_port}/cgi-bin/do?cmd=ir_code&ir_code=4CB34040"
        http_analysis["cgi_bin_test"] = self._test_http_endpoint(test_ir_url, method="GET")
        
        self.discovery_report["connectivity_tests"] = http_analysis
    
    def _test_http_endpoint(self, url: str, method: str = "GET", timeout: int = 10) -> Dict[str, Any]:
        """Test HTTP endpoint accessibility."""
        try:
            req = urllib.request.Request(url, method=method)
            req.add_header('User-Agent', 'R_volution-Discovery/1.0')
            req.add_header('Accept', '*/*')
            
            start_time = time.time()
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_time = time.time() - start_time
                content = response.read()
                
                return {
                    "success": True,
                    "url": url,
                    "status_code": response.getcode(),
                    "response_time_ms": int(response_time * 1000),
                    "content_length": len(content),
                    "headers": dict(response.headers),
                    "content_preview": content.decode('utf-8', errors='ignore')[:500]
                }
                
        except urllib.error.HTTPError as e:
            return {
                "success": False,
                "url": url,
                "error": f"HTTP {e.code}: {e.reason}",
                "status_code": e.code,
                "error_type": "HTTPError"
            }
        except urllib.error.URLError as e:
            return {
                "success": False,
                "url": url,
                "error": str(e.reason),
                "error_type": "URLError"
            }
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _gather_device_information(self):
        """Gather device-specific information."""
        device_info = {
            "device_detection": {},
            "firmware_info": {},
            "capability_detection": {},
            "web_interface_analysis": {}
        }
        
        # Try to get device information from various endpoints
        info_endpoints = [
            "/device/info",
            "/as/system/information",
            "/api/v1/device",
            "/api/device/info"
        ]
        
        print(f"   Attempting device information retrieval...")
        for endpoint in info_endpoints:
            url = f"http://{self.device_ip}:{self.http_port}{endpoint}"
            result = self._test_http_endpoint(url)
            
            if result.get("success"):
                print(f"      ✓ Got response from {endpoint}")
                try:
                    content = result.get("content_preview", "")
                    if content and "{" in content:  # Likely JSON
                        device_info["device_detection"][endpoint] = {
                            "success": True,
                            "data": content,
                            "parsed": self._try_parse_json(content)
                        }
                    else:
                        device_info["device_detection"][endpoint] = {
                            "success": True,
                            "data": content,
                            "type": "non-json"
                        }
                except Exception as e:
                    device_info["device_detection"][endpoint] = {
                        "success": False,
                        "error": str(e)
                    }
            else:
                print(f"      ✗ No response from {endpoint}")
        
        # Analyze web interface if base URL is accessible
        connectivity = self.discovery_report.get("connectivity_tests", {})
        base_test = connectivity.get("base_url_test", {})
        if base_test.get("success"):
            print(f"   Analyzing web interface...")
            device_info["web_interface_analysis"] = self._analyze_web_interface()
        
        self.discovery_report["device_analysis"] = device_info
    
    def _try_parse_json(self, content: str) -> Optional[Dict]:
        """Try to parse JSON content."""
        try:
            # Find JSON in content
            start = content.find("{")
            if start != -1:
                # Try to find complete JSON
                brace_count = 0
                end = start
                for i, char in enumerate(content[start:], start):
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            end = i + 1
                            break
                
                json_str = content[start:end]
                return json.loads(json_str)
        except:
            pass
        return None
    
    def _analyze_web_interface(self) -> Dict[str, Any]:
        """Analyze web interface characteristics."""
        try:
            base_url = f"http://{self.device_ip}:{self.http_port}/"
            result = self._test_http_endpoint(base_url)
            
            if not result.get("success"):
                return {"error": "Base URL not accessible"}
            
            content = result.get("content_preview", "")
            headers = result.get("headers", {})
            
            analysis = {
                "has_web_interface": True,
                "server_header": headers.get("Server", "Unknown"),
                "content_type": headers.get("Content-Type", "Unknown"),
                "content_analysis": {}
            }
            
            # Analyze content for R_volution characteristics
            content_lower = content.lower()
            if "r_volution" in content_lower:
                analysis["content_analysis"]["r_volution_branding"] = True
            if "r_video" in content_lower:
                analysis["content_analysis"]["r_video_interface"] = True
            if "cgi-bin" in content_lower:
                analysis["content_analysis"]["cgi_support"] = True
            
            return analysis
            
        except Exception as e:
            return {"error": str(e)}
    
    def _verify_ir_commands(self):
        """Verify IR command functionality."""
        command_verification = {
            "amlogic_commands": {},
            "player_commands": {},
            "command_success_rate": {},
            "timing_analysis": {},
            "best_working_commands": []
        }
        
        print(f"   Testing Amlogic command set ({len(self.amlogic_commands)} commands)...")
        command_verification["amlogic_commands"] = self._test_command_set("Amlogic", self.amlogic_commands)
        
        print(f"   Testing Player command set ({len(self.player_commands)} commands)...")
        command_verification["player_commands"] = self._test_command_set("Player", self.player_commands)
        
        # Calculate success rates
        amlogic_working = len([r for r in command_verification["amlogic_commands"].values() if r.get("success")])
        player_working = len([r for r in command_verification["player_commands"].values() if r.get("success")])
        
        command_verification["command_success_rate"] = {
            "amlogic": {
                "working": amlogic_working,
                "total": len(self.amlogic_commands),
                "percentage": (amlogic_working / len(self.amlogic_commands)) * 100
            },
            "player": {
                "working": player_working,
                "total": len(self.player_commands), 
                "percentage": (player_working / len(self.player_commands)) * 100
            }
        }
        
        print(f"   COMMAND VERIFICATION SUMMARY:")
        print(f"     Amlogic: {amlogic_working}/{len(self.amlogic_commands)} ({command_verification['command_success_rate']['amlogic']['percentage']:.1f}%)")
        print(f"     Player: {player_working}/{len(self.player_commands)} ({command_verification['command_success_rate']['player']['percentage']:.1f}%)")
        
        # Identify best command set
        if amlogic_working > player_working:
            command_verification["recommended_device_type"] = "Amlogic"
            command_verification["best_working_commands"] = [cmd for cmd, result in command_verification["amlogic_commands"].items() if result.get("success")]
        else:
            command_verification["recommended_device_type"] = "Player"
            command_verification["best_working_commands"] = [cmd for cmd, result in command_verification["player_commands"].items() if result.get("success")]
        
        self.discovery_report["command_verification"] = command_verification
    
    def _test_command_set(self, device_type: str, commands: Dict[str, str]) -> Dict[str, Dict]:
        """Test a set of IR commands."""
        results = {}
        
        for i, (command_name, ir_code) in enumerate(commands.items()):
            print(f"      [{i+1:2d}/{len(commands)}] Testing: {command_name}")
            
            url = f"http://{self.device_ip}:{self.http_port}/cgi-bin/do?cmd=ir_code&ir_code={ir_code}"
            result = self._test_http_endpoint(url, timeout=5)
            
            success = result.get("success", False) and result.get("status_code") == 200
            
            results[command_name] = {
                "success": success,
                "ir_code": ir_code,
                "url": url,
                "response_time_ms": result.get("response_time_ms", 0),
                "status_code": result.get("status_code"),
                "error": result.get("error") if not success else None
            }
            
            if success:
                timing = result.get("response_time_ms", 0)
                print(f"          ✓ SUCCESS ({timing}ms)")
            else:
                error = result.get("error", "Unknown error")
                print(f"          ✗ FAILED: {error}")
            
            # Small delay between commands
            time.sleep(0.1)
        
        return results
    
    def _analyze_integration_compatibility(self):
        """Analyze compatibility with UC integration."""
        compatibility = {
            "overall_compatibility": "Unknown",
            "connection_issues": [],
            "working_features": [],
            "missing_features": [],
            "configuration_recommendations": [],
            "troubleshooting_steps": []
        }
        
        print("   Analyzing integration compatibility...")
        
        # Check basic HTTP connectivity
        connectivity_tests = self.discovery_report.get("connectivity_tests", {})
        base_test = connectivity_tests.get("base_url_test", {})
        cgi_test = connectivity_tests.get("cgi_bin_test", {})
        
        if not base_test.get("success"):
            compatibility["connection_issues"].append("Base HTTP connectivity failed")
            compatibility["troubleshooting_steps"].append("Check device IP address and network connectivity")
        
        if not cgi_test.get("success"):
            compatibility["connection_issues"].append("CGI-bin interface not accessible")
            compatibility["troubleshooting_steps"].append("Verify device supports HTTP IR commands")
        else:
            compatibility["working_features"].append("IR command interface accessible")
        
        # Check port accessibility
        port_discovery = self.discovery_report.get("port_discovery", {})
        open_ports = port_discovery.get("open_ports", [])
        
        if 80 in open_ports:
            compatibility["working_features"].append("Standard HTTP port (80) accessible")
        else:
            compatibility["connection_issues"].append("Port 80 not accessible")
            if open_ports:
                compatibility["configuration_recommendations"].append(f"Try alternative ports: {open_ports}")
        
        # Check command success rates
        command_verification = self.discovery_report.get("command_verification", {})
        amlogic_rate = command_verification.get("command_success_rate", {}).get("amlogic", {}).get("percentage", 0)
        player_rate = command_verification.get("command_success_rate", {}).get("player", {}).get("percentage", 0)
        
        best_rate = max(amlogic_rate, player_rate)
        
        if best_rate >= 80:
            compatibility["overall_compatibility"] = "Excellent"
            compatibility["working_features"].append(f"High command success rate: {best_rate:.1f}%")
        elif best_rate >= 60:
            compatibility["overall_compatibility"] = "Good"
            compatibility["working_features"].append(f"Good command success rate: {best_rate:.1f}%")
        elif best_rate >= 30:
            compatibility["overall_compatibility"] = "Limited"
            compatibility["connection_issues"].append(f"Low command success rate: {best_rate:.1f}%")
        else:
            compatibility["overall_compatibility"] = "Poor"
            compatibility["connection_issues"].append(f"Very low command success rate: {best_rate:.1f}%")
        
        # Device type recommendation
        recommended_type = command_verification.get("recommended_device_type")
        if recommended_type:
            compatibility["configuration_recommendations"].append(f"Use {recommended_type} device type in integration")
        
        print(f"   COMPATIBILITY: {compatibility['overall_compatibility']}")
        
        self.discovery_report["integration_recommendations"] = compatibility
    
    def _generate_recommendations(self):
        """Generate final recommendations for users and developers."""
        recommendations = {
            "user_actions": [],
            "integration_fixes": [],
            "network_troubleshooting": [],
            "device_configuration": [],
            "summary": {}
        }
        
        print("   Generating recommendations...")
        
        # Analyze connectivity issues
        connectivity_tests = self.discovery_report.get("connectivity_tests", {})
        network_analysis = self.discovery_report.get("network_analysis", {})
        port_discovery = self.discovery_report.get("port_discovery", {})
        command_verification = self.discovery_report.get("command_verification", {})
        
        # Network recommendations
        local_network = network_analysis.get("local_network_analysis", {})
        if not local_network.get("same_subnet", True):
            recommendations["network_troubleshooting"].append("Device and computer are on different subnets - check router configuration")
        
        ping_test = network_analysis.get("ping_test", {})
        if not ping_test.get("success", False):
            recommendations["network_troubleshooting"].append("Ping test failed - check firewall settings and device connectivity")
            recommendations["user_actions"].append("Verify device IP address is correct and device is powered on")
        
        # Port accessibility recommendations
        open_ports = port_discovery.get("open_ports", [])
        if 80 not in open_ports:
            if open_ports:
                recommendations["integration_fixes"].append(f"Port 80 not accessible - try alternative ports: {open_ports}")
                recommendations["device_configuration"].append("Check if device uses non-standard HTTP port")
            else:
                recommendations["network_troubleshooting"].append("No ports accessible - likely network connectivity issue")
                recommendations["user_actions"].append("Check device network settings and firewall configuration")
        
        # HTTP endpoint recommendations
        base_test = connectivity_tests.get("base_url_test", {})
        if not base_test.get("success"):
            error = base_test.get("error", "Unknown")
            if "Connection refused" in error:
                recommendations["integration_fixes"].append("Connection refused error - device may not have HTTP API enabled")
                recommendations["user_actions"].append("Check device settings for HTTP/IP control options")
            elif "timeout" in error.lower():
                recommendations["network_troubleshooting"].append("Connection timeout - check network latency and device responsiveness")
        
        # Command verification recommendations
        amlogic_rate = command_verification.get("command_success_rate", {}).get("amlogic", {}).get("percentage", 0)
        player_rate = command_verification.get("command_success_rate", {}).get("player", {}).get("percentage", 0)
        
        if amlogic_rate > player_rate:
            recommendations["device_configuration"].append("Device responds better to Amlogic command set")
            recommendations["integration_fixes"].append("Configure integration to use DeviceType.AMLOGIC")
        elif player_rate > amlogic_rate:
            recommendations["device_configuration"].append("Device responds better to Player command set")
            recommendations["integration_fixes"].append("Configure integration to use DeviceType.PLAYER")
        
        if max(amlogic_rate, player_rate) < 50:
            recommendations["integration_fixes"].append("Low command success rate - device may need firmware update")
            recommendations["user_actions"].append("Check for device firmware updates")
        
        # Device information recommendations
        device_analysis = self.discovery_report.get("device_analysis", {})
        device_detection = device_analysis.get("device_detection", {})
        
        if not device_detection:
            recommendations["integration_fixes"].append("No device information endpoints found - limited status monitoring available")
        
        # Generate summary
        compatibility = self.discovery_report.get("integration_recommendations", {})
        overall_compatibility = compatibility.get("overall_compatibility", "Unknown")
        
        recommendations["summary"] = {
            "overall_status": overall_compatibility,
            "primary_issues": len(compatibility.get("connection_issues", [])),
            "working_features": len(compatibility.get("working_features", [])),
            "recommended_actions": len(recommendations["user_actions"]) + len(recommendations["integration_fixes"])
        }
        
        # Print summary
        print(f"   RECOMMENDATIONS GENERATED:")
        print(f"     Overall Status: {overall_compatibility}")
        print(f"     User Actions: {len(recommendations['user_actions'])}")
        print(f"     Integration Fixes: {len(recommendations['integration_fixes'])}")
        print(f"     Network Issues: {len(recommendations['network_troubleshooting'])}")
        
        self.discovery_report["final_recommendations"] = recommendations
    
    def save_report(self, filename: Optional[str] = None) -> str:
        """Save discovery report to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            device_ip_safe = self.device_ip.replace(".", "_")
            filename = f"rvolution_discovery_{device_ip_safe}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.discovery_report, f, indent=2, default=str)
            print(f"SUCCESS: Discovery report saved to {filename}")
            return filename
        except Exception as e:
            print(f"ERROR: Failed to save report: {e}")
            # Try backup filename
            try:
                backup_name = f"rvolution_discovery_backup_{int(time.time())}.json"
                with open(backup_name, 'w', encoding='utf-8') as f:
                    json.dump(self.discovery_report, f, indent=2, default=str)
                print(f"SUCCESS: Report saved to backup file {backup_name}")
                return backup_name
            except Exception as e2:
                print(f"CRITICAL: Could not save report at all: {e2}")
                return ""
    
    def print_summary(self):
        """Print comprehensive discovery summary."""
        print("\n" + "=" * 60)
        print("R_VOLUTION DISCOVERY SUMMARY")
        print("=" * 60)
        
        try:
            # Device information
            print("DEVICE INFORMATION:")
            device_analysis = self.discovery_report.get("device_analysis", {})
            device_detection = device_analysis.get("device_detection", {})
            
            found_info = False
            for endpoint, info in device_detection.items():
                if info.get("success") and info.get("parsed"):
                    parsed = info["parsed"]
                    print(f"  Model: {parsed.get('model', parsed.get('hardwareModel', 'Unknown'))}")
                    print(f"  Serial: {parsed.get('serial', parsed.get('serialNumber', 'Unknown'))}")
                    print(f"  Firmware: {parsed.get('firmware', parsed.get('ASVersion', 'Unknown'))}")
                    found_info = True
                    break
            
            if not found_info:
                print("  Device information: Not available")
            
            # Network status
            print(f"\nNETWORK STATUS:")
            network_analysis = self.discovery_report.get("network_analysis", {})
            ping_test = network_analysis.get("ping_test", {})
            local_network = network_analysis.get("local_network_analysis", {})
            
            print(f"  Ping Test: {'✓ SUCCESS' if ping_test.get('success') else '✗ FAILED'}")
            print(f"  Same Subnet: {'Yes' if local_network.get('same_subnet') else 'No - Potential routing issue'}")
            
            # Port accessibility
            print(f"\nPORT ACCESSIBILITY:")
            port_discovery = self.discovery_report.get("port_discovery", {})
            open_ports = port_discovery.get("open_ports", [])
            
            if 80 in open_ports:
                print(f"  HTTP Port 80: ✓ ACCESSIBLE")
            else:
                print(f"  HTTP Port 80: ✗ NOT ACCESSIBLE")
            
            if open_ports:
                print(f"  Open Ports: {open_ports}")
            else:
                print(f"  Open Ports: None found")
            
            # HTTP endpoints
            print(f"\nHTTP ENDPOINTS:")
            connectivity_tests = self.discovery_report.get("connectivity_tests", {})
            base_test = connectivity_tests.get("base_url_test", {})
            cgi_test = connectivity_tests.get("cgi_bin_test", {})
            
            print(f"  Base URL: {'✓ SUCCESS' if base_test.get('success') else '✗ FAILED'}")
            print(f"  CGI-bin Interface: {'✓ SUCCESS' if cgi_test.get('success') else '✗ FAILED'}")
            
            # Command verification
            print(f"\nCOMMAND VERIFICATION:")
            command_verification = self.discovery_report.get("command_verification", {})
            amlogic_rate = command_verification.get("command_success_rate", {}).get("amlogic", {})
            player_rate = command_verification.get("command_success_rate", {}).get("player", {})
            
            if amlogic_rate:
                print(f"  Amlogic Commands: {amlogic_rate.get('working', 0)}/{amlogic_rate.get('total', 0)} ({amlogic_rate.get('percentage', 0):.1f}%)")
            
            if player_rate:
                print(f"  Player Commands: {player_rate.get('working', 0)}/{player_rate.get('total', 0)} ({player_rate.get('percentage', 0):.1f}%)")
            
            recommended_type = command_verification.get("recommended_device_type")
            if recommended_type:
                print(f"  Recommended Type: {recommended_type}")
            
            # Integration compatibility
            print(f"\nINTEGRATION COMPATIBILITY:")
            compatibility = self.discovery_report.get("integration_recommendations", {})
            overall = compatibility.get("overall_compatibility", "Unknown")
            connection_issues = compatibility.get("connection_issues", [])
            working_features = compatibility.get("working_features", [])
            
            print(f"  Overall Status: {overall}")
            print(f"  Working Features: {len(working_features)}")
            print(f"  Connection Issues: {len(connection_issues)}")
            
            # Recommendations
            print(f"\nRECOMMENDATIONS:")
            final_recommendations = self.discovery_report.get("final_recommendations", {})
            user_actions = final_recommendations.get("user_actions", [])
            integration_fixes = final_recommendations.get("integration_fixes", [])
            network_troubleshooting = final_recommendations.get("network_troubleshooting", [])
            
            if user_actions:
                print(f"  USER ACTIONS:")
                for i, action in enumerate(user_actions[:3], 1):  # Show top 3
                    print(f"    {i}. {action}")
                if len(user_actions) > 3:
                    print(f"    ... and {len(user_actions) - 3} more (see full report)")
            
            if integration_fixes:
                print(f"  INTEGRATION FIXES:")
                for i, fix in enumerate(integration_fixes[:3], 1):  # Show top 3
                    print(f"    {i}. {fix}")
                if len(integration_fixes) > 3:
                    print(f"    ... and {len(integration_fixes) - 3} more (see full report)")
            
            if network_troubleshooting:
                print(f"  NETWORK TROUBLESHOOTING:")
                for i, item in enumerate(network_troubleshooting[:3], 1):  # Show top 3
                    print(f"    {i}. {item}")
                if len(network_troubleshooting) > 3:
                    print(f"    ... and {len(network_troubleshooting) - 3} more (see full report)")
            
        except Exception as e:
            print(f"Error printing summary: {e}")


def main():
    """Main function for R_volution discovery."""
    print("R_volution Device Discovery Script")
    print("Author: Meir Miyara (meir.miyara@gmail.com)")
    print("Version: 1.0.0")
    print("=" * 50)
    
    # Get device IP from command line or user input
    if len(sys.argv) > 1:
        device_ip = sys.argv[1]
    else:
        device_ip = input("Enter R_volution device IP address: ").strip()
        if not device_ip:
            print("ERROR: No IP address provided")
            sys.exit(1)
    
    # Optional HTTP port override
    http_port = 80
    if len(sys.argv) > 2:
        try:
            http_port = int(sys.argv[2])
        except ValueError:
            print(f"WARNING: Invalid port '{sys.argv[2]}', using default port 80")
    
    discovery = None
    report_file = ""
    
    try:
        # Run discovery
        print(f"Starting discovery for {device_ip}:{http_port}")
        discovery = RvolutionDiscovery(device_ip, http_port)
        results = discovery.run_discovery()
        
        print("\nDiscovery completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nDiscovery cancelled by user")
        if discovery:
            print("Saving partial results...")
    except Exception as e:
        print(f"\n\nERROR during discovery: {e}")
        print("Attempting to save partial results...")
        traceback.print_exc()
    
    # Always try to save results
    if discovery and discovery.discovery_report:
        try:
            report_file = discovery.save_report()
        except Exception as e:
            print(f"Failed to save report: {e}")
    
    # Print summary
    if discovery:
        try:
            discovery.print_summary()
        except Exception as e:
            print(f"Failed to print summary: {e}")
    
    # Final instructions
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    
    if report_file:
        print(f"📋 DETAILED REPORT SAVED: {report_file}")
        print("📧 SEND THIS FILE TO: meir.miyara@gmail.com")
        print("📝 Include in email:")
        print("   - Your R_volution device model")
        print("   - Firmware version (if known)")
        print("   - Description of connection issues")
        print("   - Network setup details")
    else:
        print("⚠️  Could not save detailed report")
        print("📧 EMAIL SUPPORT: meir.miyara@gmail.com")
        print("Include console output and device details")
    
    print(f"\n💡 QUICK FIXES TO TRY:")
    print("   1. Verify device IP address is correct")
    print("   2. Check device is powered on and connected")
    print("   3. Ensure firewall allows connections to device")
    print("   4. Try different HTTP port if device uses non-standard port")
    
    print(f"\n📖 USAGE: python {sys.argv[0]} [IP_ADDRESS] [HTTP_PORT]")
    print(f"   Example: python {sys.argv[0]} 192.168.1.100 80")
    
    # Keep window open for user
    try:
        input("\nPress ENTER to exit...")
    except:
        pass


if __name__ == "__main__":
    main()