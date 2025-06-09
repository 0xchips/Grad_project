# Nessus Installation and Configuration Guide

## Overview
This guide provides comprehensive instructions for installing and configuring Tenable Nessus vulnerability scanner for integration with the WiGuard security dashboard.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Automatic Installation](#automatic-installation)
3. [Manual Installation](#manual-installation)
4. [Configuration](#configuration)
5. [Integration with WiGuard](#integration-with-wiguard)
6. [Troubleshooting](#troubleshooting)
7. [Security Considerations](#security-considerations)

## Prerequisites

### System Requirements
- **Operating System**: Kali Linux / Debian-based distribution
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Disk Space**: Minimum 2GB free space
- **Network**: Internet connection for initial download and updates
- **User Privileges**: sudo/root access required

### Dependencies
```bash
# Update package repository
sudo apt update

# Install required packages
sudo apt install -y curl wget python3 python3-pip
```

## Automatic Installation

The WiGuard dashboard includes an automated Nessus installation script that handles the entire setup process.

### Using the Integrated Scanner
1. **Access Dashboard**: Navigate to the WiGuard dashboard
2. **Click "Run Full Scan"**: The system will automatically detect if Nessus is installed
3. **Automatic Setup**: If not found, the system will:
   - Download Nessus installer
   - Install and configure Nessus
   - Create admin user
   - Start the scanning service

### Python Script Usage
```bash
# Navigate to dashboard directory
cd /home/kali/latest/dashboard

# Run the Nessus scanner setup
python3 nessus_scanner.py
```

## Manual Installation

### Step 1: Download Nessus
```bash
# Create temporary directory
mkdir -p /tmp/nessus_install
cd /tmp/nessus_install

# Download Nessus for Debian/Ubuntu
wget "https://www.tenable.com/downloads/api/v1/public/pages/nessus/downloads/17204/download?i_agree_to_tenable_license_agreement=true" -O Nessus-latest-debian9_amd64.deb
```

### Step 2: Install Nessus Package
```bash
# Install the downloaded package
sudo dpkg -i Nessus-latest-debian9_amd64.deb

# Fix any dependency issues
sudo apt --fix-broken install
```

### Step 3: Start Nessus Service
```bash
# Enable Nessus service
sudo systemctl enable nessusd

# Start Nessus service
sudo systemctl start nessusd

# Check service status
sudo systemctl status nessusd
```

### Step 4: Verify Installation
```bash
# Check if Nessus daemon is running
ps aux | grep nessus

# Check listening ports
sudo netstat -tlnp | grep 8834
```

## Configuration

### Initial Setup via Web Interface

1. **Access Nessus Web Interface**:
   - Open browser and navigate to: `https://localhost:8834`
   - Accept the self-signed certificate warning

2. **Choose Nessus Essentials** (Free version):
   - Select "Nessus Essentials"
   - Register with Tenable to get activation code
   - Enter activation code when prompted

3. **Create Administrator Account**:
   - Username: `admin`
   - Password: `admin123` (or choose secure password)
   - Email: `admin@localhost.local`

4. **Download Plugins**:
   - Wait for initial plugin download (can take 30-60 minutes)
   - Plugins are required for vulnerability detection

### Configuration via API (Automated)

The CyberShield integration handles configuration automatically:

```python
# Example configuration
nessus_config = {
    'host': 'localhost',
    'port': 8834,
    'username': 'admin',
    'password': 'admin123',
    'verify_ssl': False
}
```

## Integration with WiGuard

### Backend Integration

The Flask backend (`flaskkk.py`) includes new endpoints for Nessus integration:

```python
# Nessus scan endpoints
/api/nessus/scan/start    # Start vulnerability scan
/api/nessus/scan/status   # Get scan status
/api/nessus/scan/results  # Get scan results
/api/nessus/scan/report   # Export scan report
```

### Frontend Integration

The dashboard's "Run Full Scan" button now triggers comprehensive vulnerability scanning:

1. **Automatic Detection**: Checks if Nessus is installed
2. **Setup Process**: Installs and configures if needed
3. **Scan Execution**: Launches vulnerability scan
4. **Progress Monitoring**: Real-time scan progress updates
5. **Results Display**: Shows vulnerability summary and details

### Default Scan Configuration

```json
{
  "scan_name": "WiGuard_Full_Scan",
  "targets": "192.168.1.0/24",
  "template": "basic_network_scan",
  "enabled": true,
  "launch": "ONETIME"
}
```

## File Locations

### Nessus Installation Paths
- **Binary**: `/opt/nessus/sbin/nessusd`
- **Configuration**: `/opt/nessus/etc/nessus/`
- **Plugins**: `/opt/nessus/lib/nessus/plugins/`
- **Logs**: `/opt/nessus/var/nessus/logs/`

### CyberShield Integration Files
- **Scanner Module**: `/home/kali/latest/dashboard/nessus_scanner.py`
- **Backend Routes**: `/home/kali/latest/dashboard/flaskkk.py`
- **Frontend Logic**: `/home/kali/latest/dashboard/templates/static/js/main.js`

## Troubleshooting

### Common Issues

#### 1. Nessus Service Won't Start
```bash
# Check logs
sudo journalctl -u nessusd -f

# Restart service
sudo systemctl restart nessusd

# Check port conflicts
sudo netstat -tlnp | grep 8834
```

#### 2. Web Interface Inaccessible
```bash
# Verify service is running
sudo systemctl status nessusd

# Check firewall settings
sudo ufw status

# Allow Nessus port
sudo ufw allow 8834
```

#### 3. Plugin Download Issues
```bash
# Check internet connectivity
ping updates.nessus.org

# Restart service after network issues
sudo systemctl restart nessusd
```

#### 4. Authentication Failures
```bash
# Reset admin password (if needed)
sudo /opt/nessus/sbin/nessuscli user delete admin
sudo /opt/nessus/sbin/nessuscli user add admin
```

### Log Files
- **Nessus Daemon**: `/opt/nessus/var/nessus/logs/nessusd.messages`
- **Web Server**: `/opt/nessus/var/nessus/logs/www_server.log`
- **CyberShield**: `/home/kali/latest/dashboard/app.log`

## Security Considerations

### Access Control
- **Web Interface**: Only accessible via localhost (127.0.0.1:8834)
- **API Access**: Secured with authentication tokens
- **User Management**: Single admin user for dashboard integration

### Network Security
```bash
# Configure firewall (if needed)
sudo ufw allow from 127.0.0.1 to any port 8834
sudo ufw deny 8834
```

### SSL/TLS Configuration
- Nessus uses self-signed certificates by default
- For production, consider using proper SSL certificates
- API calls disable SSL verification for localhost

### Data Protection
- Scan results contain sensitive vulnerability information
- Ensure proper file permissions on scan reports
- Consider encrypting scan data at rest

## Advanced Configuration

### Custom Scan Templates
```python
# Create custom scan template
scan_template = {
    'name': 'CyberShield Custom Scan',
    'description': 'Comprehensive security assessment',
    'settings': {
        'port_range': '1-65535',
        'syn_scanner': 'yes',
        'ping_host': 'yes',
        'safe_checks': 'yes'
    }
}
```

### Automated Scheduling
```python
# Schedule recurring scans
import schedule
import time

def run_weekly_scan():
    scanner = NessusScanner()
    scanner.run_full_scan("192.168.1.0/24")

schedule.every().week.do(run_weekly_scan)
```

## API Reference

### Authentication
```python
# Authenticate with Nessus
auth_data = {
    'username': 'admin',
    'password': 'admin123'
}
response = requests.post('https://localhost:8834/session', json=auth_data, verify=False)
token = response.json()['token']
```

### Scan Management
```python
# Create scan
scan_data = {
    'uuid': template_uuid,
    'settings': {
        'name': 'My Scan',
        'targets': '192.168.1.0/24'
    }
}
response = requests.post('https://localhost:8834/scans', json=scan_data, headers={'X-Cookie': f'token={token}'})

# Launch scan
scan_id = response.json()['scan']['id']
requests.post(f'https://localhost:8834/scans/{scan_id}/launch', headers={'X-Cookie': f'token={token}'})
```

## Support and Resources

### Official Documentation
- [Nessus User Guide](https://docs.tenable.com/nessus/)
- [Nessus API Reference](https://developer.tenable.com/reference)
- [Tenable Community](https://community.tenable.com/)

### CyberShield Support
- **Repository**: `/home/kali/latest/dashboard/`
- **Logs**: Check `app.log` for integration issues
- **Configuration**: Review `nessus_scanner.py` for customization

## License and Compliance

### Nessus Essentials
- **Free Version**: Limited to 16 IP addresses
- **Registration Required**: Tenable account needed
- **Commercial Use**: Check license terms

### Integration License
- **CyberShield**: Open source integration
- **Compliance**: Ensure proper Nessus licensing for your use case

---

**Note**: This guide assumes Kali Linux environment. Adapt commands and paths as needed for other distributions.

**Last Updated**: May 25, 2025
