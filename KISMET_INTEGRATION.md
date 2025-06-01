# Kismet Integration Documentation

## Overview
The CyberShield dashboard now includes comprehensive Kismet wireless monitoring integration. This allows real-time detection and monitoring of wireless devices, networks, and potential security threats.

## Features

### 1. Wireless Device Detection
- Real-time discovery of wireless devices
- Device information including MAC addresses, manufacturers, signal strength
- Packet statistics and activity monitoring

### 2. Network Monitoring
- Access point detection
- Client device tracking
- Signal strength monitoring
- Network activity analysis

### 3. Web Interface Integration
- Start/stop Kismet monitoring from the dashboard
- Real-time status updates
- Device table with comprehensive information
- Activity logs and monitoring history

## API Endpoints

### Start Kismet Monitoring
```
POST /api/kismet/start
{
  "interface": "wlan0"  // optional, auto-detects best interface
}
```

### Stop Kismet Monitoring
```
POST /api/kismet/stop
```

### Get Kismet Status
```
GET /api/kismet/status
```

### Get Detected Devices
```
GET /api/kismet/devices
```

## Configuration

### API Key
The Kismet integration uses a predefined API key: `4EB980F446769D0164739F9301A5C793`

### Interface Selection
The system automatically detects and prefers monitor mode interfaces:
1. Requested interface (if specified)
2. wlan0mon (monitor mode)
3. wlan1mon (backup monitor mode)
4. wlan0 (regular mode)
5. First available wireless interface

### Network Configuration
- Default Kismet port: 2501
- Host: localhost
- Authentication: Uses API key for both username and password

## Usage Instructions

### From the Dashboard
1. Navigate to the main dashboard
2. Scroll down to the "Kismet Wireless Monitoring" section
3. Click "Start Monitoring" to begin wireless detection
4. View detected devices in the real-time table
5. Monitor activity through the logs section
6. Use "Refresh" to manually update data
7. Click "Stop Monitoring" to end the session

### Quick Actions
A "Start Kismet" button is also available in the Quick Actions section for immediate access.

## Interface Setup

### Automatic Setup
The system attempts to use the best available wireless interface automatically.

### Manual Setup (if needed)
Use the provided setup script:
```bash
./setup_kismet_interface.sh
```

This script:
- Checks for wireless interfaces
- Sets up monitor mode if needed
- Configures interface for Kismet use

### Monitor Mode Commands
```bash
# Put interface down
sudo ip link set wlan0 down

# Set monitor mode
sudo iw dev wlan0 set type monitor

# Bring interface up
sudo ip link set wlan0 up
```

## Security Considerations

### Permissions
- Kismet requires root privileges for wireless monitoring
- The dashboard runs with appropriate permissions for system access
- Monitor mode requires administrative access

### Data Privacy
- Wireless monitoring may capture sensitive information
- Ensure compliance with local privacy laws
- Use only for authorized network testing and monitoring

### Network Impact
- Monitor mode may temporarily disable normal wireless connectivity
- Ensure you have alternative network access if needed
- Some wireless cards may not support monitor mode

## Troubleshooting

### Common Issues

#### "Interface not found"
- Check available interfaces: `ip link show`
- Ensure wireless adapter is connected
- Verify driver support for monitor mode

#### "Permission denied"
- Ensure the application has appropriate privileges
- Check if wireless interface is in use by other applications
- Verify monitor mode capability: `iw list`

#### "Kismet failed to start"
- Check if Kismet is installed: `which kismet`
- Verify interface is not in use: `airmon-ng check`
- Check system logs: `journalctl -u kismet`

#### "No devices detected"
- Verify monitor mode is active
- Check if there are wireless devices in range
- Ensure interface is properly configured

### Verification Commands
```bash
# Check Kismet installation
which kismet
kismet --version

# Check wireless interfaces
ip link show | grep wlan
iw dev

# Check monitor mode capability
iw list | grep monitor

# Test interface
iwconfig
```

## Advanced Configuration

### Custom Kismet Configuration
You can modify the Kismet startup parameters in the Flask code:
- Port configuration
- Additional interfaces
- Logging options
- Filter settings

### Database Integration
Device data can be stored in the dashboard database for:
- Historical analysis
- Trend monitoring
- Security alerting
- Reporting

## Integration with Other Tools

### Network Discovery
Kismet data complements the existing network discovery tools:
- Passive wireless monitoring vs active scanning
- Different device detection methods
- Comprehensive network mapping

### Security Monitoring
Integration with other security tools:
- Deauthentication attack detection
- Rogue access point identification
- Wireless intrusion detection

## Performance Considerations

### Resource Usage
- Kismet can be resource-intensive
- Monitor CPU and memory usage
- Consider limiting scan duration for resource-constrained systems

### Update Frequency
- Device table updates every 5 seconds
- Configurable refresh intervals
- Balance between real-time updates and system load

## Future Enhancements

### Planned Features
- Device tracking and mapping
- Security threat detection
- Alert integration
- Export capabilities
- Historical data analysis
- Custom filtering options

### Integration Opportunities
- GPS location correlation
- Network topology mapping
- Automated threat response
- Machine learning for anomaly detection
