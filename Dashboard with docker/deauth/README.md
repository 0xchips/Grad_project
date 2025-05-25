# Deauthentication Attack Toolkit

A comprehensive toolkit for detecting, monitoring, and performing deauthentication attacks for security research and testing purposes.

## Overview

This toolkit provides a unified interface for:

1. **Detecting deauthentication attacks** - Monitor wireless networks for malicious deauth frames
2. **Performing deauthentication attacks** - Launch controlled deauth attacks for testing network security
3. **Visualizing attack data** - Display attack information on a real-time dashboard
4. **Managing wireless interfaces** - Setup monitor mode and scan for networks

## Legal Disclaimer

This toolkit is designed for legitimate security research, network testing, and educational purposes only. Only use these tools on networks you own or have explicit permission to test. Unauthorized use against networks without permission is illegal and unethical.

## Components

The toolkit consists of the following components:

- **deauth_toolkit.sh**: Main interface script that provides all functionality
- **detector.py**: Python script that detects and logs deauthentication attacks
- **Database integration**: Automatically saves detected attacks to MySQL database
- **Dashboard integration**: Visualizes attack data on the security dashboard

## Installation

1. Make sure you're in the deauth directory:
   ```
   cd /path/to/Dashboard\ with\ docker/deauth/
   ```

2. Make the toolkit script executable:
   ```
   chmod +x deauth_toolkit.sh
   ```

3. Install dependencies:
   ```
   ./deauth_toolkit.sh install
   ```

## Usage

### Interactive Menu

Run the toolkit with no arguments to access the interactive menu:
```
./deauth_toolkit.sh
```

### Command Line Interface

Run specific commands directly:
```
./deauth_toolkit.sh [command]
```

Available commands:
- `setup`: Setup a wireless interface in monitor mode
- `scan`: Scan for wireless networks
- `start`: Start the deauth detector
- `stop`: Stop the deauth detector
- `logs`: View detector logs
- `status`: Check detector status
- `attack`: Launch a deauth attack
- `dblogs`: View database logs
- `dbclear`: Clear database logs
- `install`: Install dependencies
- `verify`: Verify database connection
- `dashboard`: Open the deauth dashboard
- `restore`: Restore wireless interfaces to managed mode
- `simulate`: Simulate a deauth attack
- `help`: Show help menu

## Workflow

### Detecting Deauthentication Attacks

1. Set up a wireless interface in monitor mode:
   ```
   ./deauth_toolkit.sh setup
   ```

2. Start the detector:
   ```
   ./deauth_toolkit.sh start
   ```

3. View logs in real-time:
   ```
   ./deauth_toolkit.sh logs
   ```

4. Open the dashboard to visualize attacks:
   ```
   ./deauth_toolkit.sh dashboard
   ```

### Performing Deauthentication Attacks

1. Set up a wireless interface in monitor mode:
   ```
   ./deauth_toolkit.sh setup
   ```

2. Scan for networks:
   ```
   ./deauth_toolkit.sh scan
   ```

3. Launch a deauth attack:
   ```
   ./deauth_toolkit.sh attack
   ```

## Dashboard Integration

The toolkit automatically saves detected attacks to the MySQL database, which is displayed on the deauthentication dashboard. The dashboard provides:

- Real-time visualization of attacks
- Historical attack data
- Statistics on attackers and targets
- Attack frequency analysis

Access the dashboard at:
```
http://localhost/deauth.html
```

## Requirements

- Kali Linux or similar Linux distribution
- Wireless network interface that supports monitor mode
- MySQL database (already set up in the Docker environment)
- Python 3 with Scapy and MySQLdb packages
- Aircrack-ng suite

## Troubleshooting

- **Interface not going into monitor mode**: Some network interfaces don't support monitor mode. Try with a different interface or external USB WiFi adapter.
- **Database connection issues**: Verify the database is running with `./deauth_toolkit.sh verify`
- **Dashboard not showing data**: Make sure the detector is running and attacks are being logged to the database.
- **Detector not capturing deauth frames**: Make sure you're using an interface that supports monitor mode and the correct channel.

## Author

CyberShield Team
