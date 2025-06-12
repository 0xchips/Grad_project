# WiGuard Dashboard - Linux Installation Guide

The WiGuard Dashboard is a comprehensive wireless security monitoring platform specifically designed for Linux distributions including Kali Linux, Ubuntu, and Debian. This guide focuses exclusively on Linux deployment and configuration.

## Quick Start

### Automated Setup (Recommended)

```bash
# Clone or download the project
cd /path/to/wiguard-dashboard

# Run the setup script (works on all supported Linux distributions)
./setup.sh
```

### Manual Setup

If the automated setup doesn't work for your system, follow these manual steps:

## System Requirements

### Minimum Requirements
- Linux (Kali, Ubuntu, Debian)
- Python 3.8+ 
- 2GB RAM
- 1GB disk space
- Network interface (wireless preferred)

### Recommended Requirements
- Kali Linux (optimal wireless monitoring)
- Python 3.9+
- 4GB RAM
- 5GB disk space
- Multiple wireless interfaces with monitor mode support
- MySQL/MariaDB database

## Installation by Linux Distribution

### Kali Linux (Recommended for Full Features)
```bash
# Update package list
sudo apt update

# Install system dependencies (most tools already included)
sudo apt install python3 python3-pip python3-venv python3-dev \
                 libmysqlclient-dev build-essential libssl-dev \
                 git mysql-server

# Wireless tools are usually pre-installed, but verify:
sudo apt install wireless-tools aircrack-ng net-tools iw nmap

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install system dependencies
sudo apt install python3 python3-pip python3-venv python3-dev \
                 libmysqlclient-dev build-essential libssl-dev \
                 wireless-tools aircrack-ng net-tools iw nmap git \
                 mysql-server

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Advanced Installation Options

#### Option 1: Full Installation with Optimization
```bash
./setup.sh  # Choose option 1
```

#### Option 2: Development Environment
```bash
./setup.sh  # Choose option 3
```

#### Option 3: Production Service Setup
```bash
sudo ./setup.sh  # Choose option 6
sudo ./service_manager.sh install
```

## Configuration

### 1. Environment Configuration
```bash
# Copy example configuration
cp .env.example .env

# Edit configuration file
nano .env
```

### 2. Key Configuration Options
```bash
# Database settings
DB_HOST=localhost
DB_USER=dashboard
DB_PASSWORD=securepass
DB_NAME=security_dashboard

# Flask settings
FLASK_HOST=127.0.0.1
FLASK_PORT=5053
DASHBOARD_URL=http://127.0.0.1:5053

# Network interfaces (auto-detected if empty)
PRIMARY_INTERFACE=wlan0
MONITOR_INTERFACE=wlan0mon
```

### 3. Database Setup (Optional)
```bash
# Install MySQL/MariaDB (works on all supported Linux distributions)
sudo apt install mysql-server mariadb-server

# Start MySQL service
sudo systemctl start mysql

# Create database and user
mysql -u root -p < init.sql
```

## Running the Dashboard

### Development Mode
```bash
# Activate virtual environment
source venv/bin/activate

# Run directly
python3 flaskkk.py

# Or use the start script
./start_wiguard.sh
```

### Production Mode
```bash
# Using Gunicorn
source venv/bin/activate
gunicorn --config gunicorn.conf.py flaskkk:app
```

## Wireless Monitoring Setup

### Linux Systems (All Supported Distributions)
```bash
# Check available interfaces
iwconfig

# Enable monitor mode (if supported)
sudo airmon-ng start wlan0

# Verify monitor interface
iwconfig

# Alternative: Use interface manager
python3 interface_manager.py --discover
python3 interface_manager.py --create-monitor wlan0
```

### Kali Linux Specific Features
```bash
# Kali has additional pre-installed tools
airodump-ng wlan0mon     # Scan for networks
aireplay-ng --help       # Packet injection tools
kismet -c wlan0mon       # Advanced monitoring

# Use WiGuard's enhanced monitoring
./start_wiguard.sh
```

### Troubleshooting Wireless Issues
```bash
# Check interface capabilities
iw list

# Check for monitor mode support
iw dev wlan0 info

# Manual monitor mode (alternative method)
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up
```

## Feature Availability by Linux Distribution

| Feature | Kali Linux | Ubuntu/Debian | Notes |
|---------|------------|---------------|--------|
| Web Dashboard | ✅ | ✅ | Full support on all distributions |
| Network Discovery | ✅ | ✅ | Built-in tools and custom scanning |
| Wireless Monitoring | ✅ | ✅ | Requires wireless-tools package |
| Packet Capture | ✅ | ✅ | Root privileges required |
| Monitor Mode | ✅ | ✅ | Hardware dependent |
| Advanced RF Tools | ✅ | ⚠️ | Pre-installed in Kali, installable on others |
| GPS Integration | ✅ | ✅ | Hardware dependent |
| Bluetooth Monitoring | ✅ | ✅ | Requires bluetooth packages |
| Deauth Detection | ✅ | ✅ | Monitor mode required |
| Evil Twin Detection | ✅ | ✅ | Multiple interface setup recommended |

**Legend:** ✅ Full Support | ⚠️ Requires Additional Setup

## System Validation and Tools

### Check System Compatibility
```bash
# Quick system validation
python3 system_validator.py --quick

# Full system check with auto-fix
python3 system_validator.py --auto-fix

# Generate comprehensive report
python3 system_validator.py --output report.json --format json
```

### Interface Management
```bash
# Discover all network interfaces
python3 interface_manager.py --discover

# Check wireless capabilities
python3 interface_manager.py --discover --json

# Create monitor interface
python3 interface_manager.py --create-monitor wlan0
```

### Performance Monitoring
```bash
# Check system performance
python3 performance_monitor.py --status

# Continuous monitoring
python3 performance_monitor.py --monitor 30
```

## Common Issues and Solutions

### 1. Permission Denied Errors
```bash
# Run with sudo for packet capture
sudo python3 flaskkk.py

# Or add user to netdev group
sudo usermod -a -G netdev $USER
```

### 2. MySQL Connection Issues
```bash
# Install alternative MySQL connector
pip install pymysql

# Check MySQL service status
sudo systemctl status mysql
```

### 3. Scapy Import Errors
```bash
# Install system dependencies
sudo apt install python3-dev libpcap-dev

# Reinstall scapy
pip uninstall scapy
pip install scapy

# Alternative: Use system package
sudo apt install python3-scapy
```

### 4. Interface Not Found
```bash
# List all interfaces
ip link show

# Check wireless capabilities
iwconfig

# Use interface manager for discovery
python3 interface_manager.py --discover

# Update interface names in .env file
```

### 5. Monitor Mode Issues
```bash
# Stop NetworkManager (temporary)
sudo systemctl stop NetworkManager

# Use airmon-ng (Kali/Ubuntu)
sudo airmon-ng start wlan0

# Alternative: Manual setup
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up

# Use WiGuard's interface manager
python3 interface_manager.py --create-monitor wlan0
```

### 6. Permission Issues
```bash
# Add user to netdev group
sudo usermod -a -G netdev $USER

# For packet capture (alternative to running as root)
sudo setcap cap_net_raw,cap_net_admin+eip $(which python3)

# Or run with sudo when needed
sudo ./start_wiguard.sh
```

## Accessing the Dashboard

1. Start the application using one of the methods above
2. Open your web browser
3. Navigate to: `http://localhost:5053`
4. Use the dashboard to:
   - Monitor wireless networks
   - Detect security threats
   - View GPS locations
   - Analyze network traffic

## Security Considerations for Linux Deployments

### System-Level Security
```bash
# Create dedicated user for WiGuard (recommended)
sudo useradd -m -s /bin/bash wiguard
sudo usermod -a -G netdev,wireshark wiguard

# Set proper file permissions
chmod 750 /path/to/wiguard-dashboard
chown -R wiguard:wiguard /path/to/wiguard-dashboard

# Configure sudo access for wireless operations only
echo "wiguard ALL=(ALL) NOPASSWD: /usr/sbin/airmon-ng, /sbin/ip, /usr/sbin/iw" | sudo tee -a /etc/sudoers.d/wiguard
```

### Firewall Configuration
```bash
# Ubuntu/Debian UFW setup
sudo ufw enable
sudo ufw allow from 127.0.0.1 to any port 5053
sudo ufw allow from 192.168.1.0/24 to any port 5053  # Local network only

# Alternative: iptables rules
sudo iptables -A INPUT -p tcp --dport 5053 -s 127.0.0.1 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5053 -s 192.168.1.0/24 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5053 -j DROP
```

### Database Security
```bash
# Secure MySQL installation
sudo mysql_secure_installation

# Create restricted database user
mysql -u root -p << EOF
CREATE USER 'wiguard'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT SELECT, INSERT, UPDATE, DELETE ON security_dashboard.* TO 'wiguard'@'localhost';
FLUSH PRIVILEGES;
EOF
```

### Process Isolation and Capabilities
```bash
# Use systemd for process isolation (recommended for production)
sudo systemctl edit wiguard-dashboard.service --full

# Add security directives:
[Service]
User=wiguard
Group=wiguard
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/var/log/wiguard /var/lib/wiguard
CapabilityBoundingSet=CAP_NET_RAW CAP_NET_ADMIN
AmbientCapabilities=CAP_NET_RAW CAP_NET_ADMIN
```

### Network Monitoring Ethics and Legal Compliance
- **Authorization**: Only monitor networks you own or have explicit permission to monitor
- **Data Protection**: Implement proper data handling for captured packets
- **Logging**: Maintain audit logs of monitoring activities
- **Compliance**: Follow local laws regarding wireless monitoring and penetration testing

### Distribution-Specific Security Notes

#### Kali Linux
- **Root Access**: Kali runs as root by default - create dedicated user for WiGuard
- **Tool Isolation**: Separate WiGuard from other penetration testing tools
- **Network Isolation**: Use VMs or containers for testing environments
```bash
# Switch to non-root user for WiGuard
sudo useradd -m -s /bin/bash kali-wiguard
sudo usermod -a -G netdev,wireshark kali-wiguard
```

#### Ubuntu/Debian
- **AppArmor/SELinux**: Consider additional mandatory access controls
- **Snap Confinement**: If using snap packages, leverage confinement features
- **Service Hardening**: Use systemd security features extensively
```bash
# Enable additional security features
sudo systemctl edit wiguard-dashboard.service --full
# Add: ProtectKernelTunables=yes, ProtectControlGroups=yes
```

## Support and Troubleshooting

### Diagnostic Commands
```bash
# System validation
python3 system_validator.py --quick

# Interface discovery
python3 interface_manager.py --discover

# Performance check
python3 performance_monitor.py --status

# Check logs
tail -f logs/app.log
journalctl -u wiguard-dashboard.service -f  # If using systemd services
```

### Log Locations
- Application logs: `logs/` directory
- System service logs: `journalctl -u wiguard-dashboard.service`
- Performance logs: `logs/performance.log`
- Monitoring logs: `logs/monitoring.log`

### Getting Help
1. Run comprehensive system validation: `python3 system_validator.py --output report.json`
2. Check network interface status: `python3 interface_manager.py --discover`
3. Review application logs in `logs/` directory
4. Verify configuration in `.env` file
5. Test wireless interface capabilities: `iwconfig` and `iw list`

## Development on Linux

### Development Environment Setup
```bash
# Use enhanced setup script
./setup.sh  # Choose option 3 for development environment

# Or manual setup
source venv/bin/activate
pip install -r requirements.txt
pip install pytest black flake8  # Development tools
```

### Running Tests
```bash
source venv/bin/activate
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Code Style and Quality
```bash
# Format code
black *.py

# Check style
flake8 *.py

# Type checking (if mypy is installed)
mypy *.py
```

### Testing on Different Linux Distributions
```bash
# Docker testing
docker run -it --rm -v $(pwd):/app ubuntu:20.04 bash
docker run -it --rm -v $(pwd):/app debian:bullseye bash

# Test installation process
cd /app && ./setup.sh
```

### Contributing to WiGuard Dashboard
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Test on Kali, Ubuntu, and Debian
4. Run validation: `python3 system_validator.py --quick`
5. Submit a pull request

---

## Advanced Usage

### Production Deployment with Services
```bash
# Install as systemd service
sudo ./setup.sh  # Choose option 6
sudo ./service_manager.sh install
sudo ./service_manager.sh start

# Monitor service health
./service_manager.sh health-check
./service_manager.sh status
```

### Docker Deployment (Alternative)
```bash
# Build and run with Docker
cd docker/
docker-compose -f docker-compose.multiplatform.yml up -d

# Check container status
docker-compose ps
```

### Performance Optimization
```bash
# System optimization for wireless monitoring
sudo ./setup.sh  # Choose option 4

# Monitor performance
PERFORMANCE_MONITOR=true ./start_wiguard.sh
```

For detailed advanced features documentation, see `ADVANCED_FEATURES.md` and other guides in the project directories.

### Linux Distribution-Specific Optimizations

#### Kali Linux Optimizations
```bash
# Kali Linux comes pre-configured for security testing
# Additional optimizations for WiGuard:

# Ensure aircrack-ng suite is updated
sudo apt update && sudo apt install --only-upgrade aircrack-ng

# Optimize for wireless monitoring
sudo modprobe mac80211_hwsim radios=2  # For testing without hardware

# Set up dedicated monitoring user (recommended)
sudo useradd -m -s /bin/bash wiguard
sudo usermod -a -G netdev,wireshark wiguard
```

#### Ubuntu/Debian Optimizations
```bash
# Install additional wireless tools not included by default
sudo apt install kismet kismet-plugins wireshark-qt

# Configure NetworkManager to ignore monitor interfaces
sudo tee -a /etc/NetworkManager/NetworkManager.conf << EOF
[keyfile]
unmanaged-devices=interface-name:*mon
EOF

# Restart NetworkManager
sudo systemctl restart NetworkManager
```

## Linux Kernel and Driver Requirements

### Minimum Kernel Requirements
- **Kernel Version**: 4.15+ (Ubuntu 18.04+, Debian 10+, Kali 2020.1+)
- **mac80211 stack**: Required for monitor mode support
- **cfg80211**: Required for wireless configuration

### Wireless Driver Compatibility
```bash
# Check your wireless driver
lsmod | grep -E "(ath|iwl|rt|mt|brcm)"

# Verify monitor mode support
iw list | grep -A 5 "Supported interface modes:"
```

#### Recommended Wireless Chipsets for Linux
| Chipset Family | Driver | Monitor Mode | Packet Injection | Kali Support |
|----------------|--------|--------------|------------------|--------------|
| Atheros AR9271 | ath9k_htc | ✅ | ✅ | ✅ Excellent |
| Realtek RTL8812AU | rtl8812au | ✅ | ✅ | ✅ Good |
| Intel AC Series | iwlwifi | ⚠️ Limited | ❌ | ⚠️ Basic |
| Broadcom | brcmfmac | ❌ | ❌ | ❌ Poor |
| Ralink RT2800USB | rt2800usb | ✅ | ✅ | ✅ Good |

### Driver Installation (if needed)
```bash
# For Realtek RTL8812AU (common USB adapter)
git clone https://github.com/aircrack-ng/rtl8812au.git
cd rtl8812au
make
sudo make install

# For older Realtek drivers
sudo apt install realtek-rtl88xxau-dkms

# Check if driver loaded correctly
dmesg | grep -i wireless
```

## Linux System Performance Tuning

#### Kernel Parameters for Wireless Monitoring
```bash
# Optimize network buffers for packet capture
sudo tee -a /etc/sysctl.conf << EOF
# WiGuard Dashboard optimizations
net.core.rmem_max = 134217728
net.core.rmem_default = 65536
net.core.netdev_max_backlog = 5000
net.core.netdev_budget = 600
EOF

# Apply changes
sudo sysctl -p
```

#### CPU and Process Scheduling
```bash
# Set CPU scaling governor for performance
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# For battery-powered systems, use balanced approach
echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Set process priorities for WiGuard components
sudo systemctl edit wiguard-dashboard.service --full
# Add: Nice=-10, IOSchedulingClass=1, IOSchedulingPriority=4
```

#### Memory Management
```bash
# Configure swap for wireless monitoring systems
sudo sysctl vm.swappiness=10
sudo sysctl vm.vfs_cache_pressure=50

# For systems with limited RAM
sudo sysctl vm.overcommit_memory=1
```

#### Disk I/O Optimization
```bash
# Use appropriate I/O scheduler for storage type
# For SSDs:
echo noop | sudo tee /sys/block/sda/queue/scheduler

# For HDDs:
echo deadline | sudo tee /sys/block/sda/queue/scheduler

# Create dedicated logging partition (optional)
sudo mkdir /var/log/wiguard
sudo mount -o noatime,nodiratime /dev/sdXY /var/log/wiguard
```

#### Wireless Interface Optimization
```bash
# Disable power management for wireless interfaces
sudo iwconfig wlan0 power off

# Optimize channel scanning
sudo iw dev wlan0 scan flush

# Set optimal MTU for monitoring
sudo ip link set wlan0 mtu 1500
```

#### Distribution-Specific Performance Tips

##### Kali Linux
```bash
# Disable unnecessary services for monitoring focus
sudo systemctl disable bluetooth apache2 postgresql
sudo systemctl stop bluetooth apache2 postgresql

# Optimize for wireless tools
sudo modprobe -r iwlwifi && sudo modprobe iwlwifi 11n_disable=1
```

##### Ubuntu/Debian
```bash
# Disable NetworkManager for dedicated monitoring interfaces
sudo systemctl mask NetworkManager-wait-online.service
echo -e "[main]\nplugins=keyfile\n[keyfile]\nunmanaged-devices=interface-name:wlan*mon" | sudo tee -a /etc/NetworkManager/NetworkManager.conf
```

#### Monitoring System Performance
```bash
# Use WiGuard's built-in performance monitor
python3 performance_monitor.py --monitor 60 --alert

# System monitoring commands
htop -p $(pgrep -f wiguard)
iotop -a -o -d 1
nethogs wlan0

# Check wireless interface statistics
watch -n 1 'cat /proc/net/wireless'
```

---

## Linux Installation Summary

The WiGuard Dashboard has been optimized specifically for Linux distributions with the following key features:

### ✅ **Fully Supported Linux Distributions**
- **Kali Linux** (Recommended for full wireless security features)
- **Ubuntu 18.04+** (LTS versions recommended)
- **Debian 10+** (Stable branch)

### ✅ **Linux-Optimized Features**
- **Native systemd integration** with hardened service configurations
- **Advanced wireless monitoring** with monitor mode and packet injection
- **Kernel-level optimizations** for packet capture and network monitoring
- **Distribution-specific package management** and dependency handling
- **Security hardening** with Linux capabilities and process isolation
- **Performance tuning** for wireless monitoring workloads

### ✅ **Quick Installation Methods**
1. **Automated**: `./setup.sh` (handles all distributions automatically)
2. **Manual**: Follow distribution-specific instructions above
3. **Docker**: Multi-platform container deployment
4. **Production**: Systemd service with security hardening

### ✅ **Verified Compatibility**
- All major wireless chipsets and drivers
- Modern Linux kernels (4.15+)
- Multiple database backends (MySQL/MariaDB)
- Various Python environments (3.8+)

### 🛠️ **Next Steps After Installation**
1. Run system validation: `python3 system_validator.py --quick`
2. Discover interfaces: `python3 interface_manager.py --discover`  
3. Start monitoring: `./start_wiguard.sh`
4. Access dashboard: `http://localhost:5053`

For advanced features and configuration options, see `ADVANCED_FEATURES.md` and other documentation files in the project directory.

---

**Note**: This installation guide focuses exclusively on Linux distributions. WiGuard Dashboard leverages Linux-specific features for optimal wireless security monitoring and may not be compatible with other operating systems without significant modifications.
