# 🛡️ CyberShield Security Dashboard

## Overview

CyberShield is a comprehensive security dashboard for Kali Linux that provides real-time monitoring, vulnerability assessment, and threat detection capabilities. The dashboard integrates multiple security tools and presents a unified interface for security professionals.

## Key Features

- **Comprehensive Vulnerability Scanning**: Integrated with Nessus Professional and built-in Kali tools
- **Network Attack Detection**: Real-time detection and alerting for various network attacks
- **GPS Security Monitoring**: GPS signal analysis with jamming detection
- **Bluetooth Security**: Monitoring for Bluetooth-based attacks
- **Interactive Dashboard**: Real-time data visualization and reporting
- **Responsive Design**: Works on desktop and mobile devices

## System Architecture

The system consists of:

1. **Frontend**: HTML/CSS/JavaScript dashboard with real-time updates
2. **Backend**: Flask-based API server providing security data
3. **Database**: MySQL database for storing security events and findings
4. **Security Modules**:
   - Nessus vulnerability scanner integration
   - Fallback scanner using built-in Kali tools
   - Network attack detection system
   - GPS security monitoring system
   - Bluetooth security monitoring

## Getting Started

### Prerequisites

- Kali Linux (recommended)
- Python 3.8 or higher
- MySQL/MariaDB
- Web browser (Chrome/Firefox recommended)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/cybershield.git
   cd cybershield
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize the database:
   ```bash
   mysql -u root -p < init.sql
   ```

4. Start the application:
   ```bash
   python flaskkk.py
   ```

5. Access the dashboard:
   ```
   http://localhost:5050
   ```

## Usage

### Running a Vulnerability Scan

1. Navigate to the main dashboard
2. Click the "Run Full Scan" button
3. Monitor scan progress in the modal
4. View results when scan completes

### Monitoring Network Attacks

1. Navigate to the "Network" tab
2. View real-time network attack data
3. Filter by attack type if needed

### GPS Security Monitoring

1. Navigate to the "GPS" tab
2. View GPS security status and potential jamming attempts
3. Check GPS location history for anomalies

## Documentation

For more detailed information, see:

- [CyberShield User Guide](./CyberShield_User_Guide.md)
- [Nessus Installation Guide](./Nessus_Installation_Guide.md)
- [Implementation Summary](./IMPLEMENTATION_SUMMARY.md)
- [Deployment Guide](./DEPLOYMENT.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The Kali Linux team for their excellent security tools
- The Nessus team for their professional vulnerability scanner
- All the open-source projects that made this dashboard possible
