# WiGuard Dashboard User Guide
## Enhanced Security Scanning with Nessus Integration

### 🛡️ Overview

The WiGuard dashboard now features comprehensive vulnerability scanning capabilities powered by Nessus Professional. This integration transforms the simple "Run Full Scan" button into a sophisticated security assessment tool that provides enterprise-grade vulnerability detection and reporting.

### 🚀 Features

#### Core Functionality
- **Automated Nessus Installation**: Automatically detects and installs Nessus if not present
- **Real-time Scan Progress**: Live monitoring with visual progress indicators
- **Comprehensive Vulnerability Assessment**: Full network vulnerability scanning
- **Interactive Results Dashboard**: Detailed vulnerability breakdown with severity categorization
- **Professional Reporting**: PDF export functionality for scan results
- **Background Processing**: Non-blocking scan execution with status monitoring

#### Enhanced User Interface
- **Progress Modal**: Interactive scan progress with real-time updates
- **Results Visualization**: Professional vulnerability summary with severity breakdown
- **Responsive Design**: Mobile-friendly interface
- **Status Monitoring**: Live scan status updates and progress tracking

### 📋 Getting Started

#### Prerequisites
- Kali Linux system (recommended)
- Python 3.8+ with Flask
- Network access for Nessus installation
- Admin privileges for installation (if Nessus not present)

#### Starting the Dashboard
1. Navigate to the dashboard directory:
   ```bash
   cd /home/kali/latest/dashboard
   ```

2. Start the Flask application:
   ```bash
   python3 flaskkk.py
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:5050
   ```

### 🔍 Using the Enhanced Full Scan Feature

#### Initiating a Vulnerability Scan

1. **Access the Dashboard**: Open the WiGuard dashboard in your web browser

2. **Start Full Scan**: Click the "Run Full Scan" button in the Actions section

3. **Automatic Setup**: If Nessus is not installed, the system will:
   - Automatically download and install Nessus
   - Configure the scanner for your environment
   - Set up API access credentials
   - This process may take 10-15 minutes on first run

4. **Scan Configuration**: The system automatically configures:
   - **Target Range**: Default 192.168.1.0/24 (local network)
   - **Scan Type**: Full vulnerability assessment
   - **Scan Name**: Auto-generated with timestamp

#### Monitoring Scan Progress

The enhanced progress modal provides real-time information:

- **Progress Bar**: Visual indication of scan completion percentage
- **Status Updates**: Current scan phase and activity
- **Scan Details**: Target information and scan type
- **Progress Log**: Timestamped log of scan activities

#### Scan Phases

1. **Initialization** (0-10%): Setting up scan parameters
2. **Discovery** (10-30%): Network host discovery
3. **Port Scanning** (30-50%): Service identification
4. **Vulnerability Detection** (50-90%): Security assessment
5. **Report Generation** (90-100%): Compiling results

### 📊 Understanding Scan Results

#### Vulnerability Severity Levels

The results are categorized by severity:

- **🔴 Critical**: Immediately exploitable vulnerabilities requiring urgent attention
- **🟠 High**: Serious vulnerabilities that should be addressed promptly
- **🟡 Medium**: Moderate risk vulnerabilities for planned remediation
- **🔵 Low**: Low-risk issues for future consideration
- **⚪ Info**: Informational findings and configuration notes

#### Results Dashboard Features

- **Summary Cards**: Quick overview of vulnerability counts by severity
- **Detailed Findings**: Expandable vulnerability details with:
  - CVE identifiers
  - Risk scores
  - Affected systems
  - Remediation recommendations
- **Export Options**: PDF report generation for documentation

### ⚙️ API Endpoints

The dashboard provides RESTful API endpoints for integration:

#### Scan Management
- `POST /api/nessus/scan/start` - Initiate vulnerability scan
- `GET /api/nessus/scan/status` - Check scan progress
- `GET /api/nessus/scan/results` - Retrieve scan results
- `GET /api/nessus/scan/report` - Export scan report

#### System Configuration
- `POST /api/nessus/setup` - Configure Nessus installation

#### Example API Usage

```bash
# Start a scan
curl -X POST http://localhost:5050/api/nessus/scan/start \
  -H "Content-Type: application/json" \
  -d '{"targets": "192.168.1.0/24", "scan_name": "Production_Scan"}'

# Check scan status
curl http://localhost:5050/api/nessus/scan/status

# Get results
curl http://localhost:5050/api/nessus/scan/results
```

### 🔧 Configuration Options

#### Scan Targets
Modify scan targets by editing the frontend JavaScript:
```javascript
// In templates/index.html, modify the runFullScan function
body: JSON.stringify({
    targets: 'your.target.range/24',  // Customize target range
    scan_name: 'Custom_Scan_Name'
})
```

#### Advanced Configuration
For advanced Nessus configuration, modify `nessus_scanner.py`:
- Custom scan policies
- Credential-based scanning
- Compliance auditing
- Custom vulnerability checks

### 🛠️ Troubleshooting

#### Common Issues

**Issue: Nessus Installation Fails**
- Solution: Ensure internet connectivity and admin privileges
- Check: `/home/kali/latest/dashboard/app.log` for detailed error messages

**Issue: Scan Won't Start**
- Solution: Verify Nessus service is running: `systemctl status nessusd`
- Check: Network connectivity to target systems

**Issue: No Results Displayed**
- Solution: Wait for scan completion (can take 30+ minutes for large networks)
- Check: Scan status via API endpoint

**Issue: Progress Modal Not Updating**
- Solution: Refresh browser page and restart scan
- Check: Browser console for JavaScript errors

#### Debug Mode
Enable debug logging by setting environment variable:
```bash
export FLASK_DEBUG=1
python3 flaskkk.py
```

### 📈 Performance Optimization

#### Scan Performance
- **Network Size**: Limit scan targets for faster completion
- **Scan Policies**: Use targeted policies for specific assessments
- **Resource Allocation**: Ensure adequate system resources (4GB+ RAM recommended)

#### Dashboard Performance
- **Browser**: Use modern browsers (Chrome, Firefox, Edge)
- **Network**: Ensure stable connection for real-time updates
- **Resources**: Close unnecessary browser tabs during scans

### 🔒 Security Considerations

#### Network Security
- Run scans from dedicated security assessment network
- Ensure proper authorization before scanning production systems
- Consider scan timing to minimize business impact

#### Data Protection
- Scan results contain sensitive security information
- Implement proper access controls for the dashboard
- Regular backup of scan results and configurations

#### Compliance
- Document scan procedures for compliance requirements
- Maintain scan schedules for regular security assessments
- Archive scan results per organizational retention policies

### 🔄 Fallback Scanning System

The WiGuard dashboard includes a built-in fallback scanning system that activates when Nessus is not available. This ensures you always have security scanning capabilities, even without a professional Nessus license.

#### Fallback Scanner Features
- **Automatic Activation**: No user intervention required if Nessus is unavailable
- **Multiple Security Tools**: Leverages built-in Kali Linux security tools
- **Comparable Results**: Provides vulnerability assessment similar to Nessus
- **Seamless Integration**: Uses the same interface as the Nessus scanner
- **Real-time Progress**: Identical monitoring and status updates

#### Available Security Tools
The fallback scanner leverages these built-in Kali Linux tools:

| Tool | Purpose | Description |
|------|---------|-------------|
| nmap | Network scanning | Comprehensive port scanning with vulnerability detection |
| nikto | Web vulnerability scanning | Identifies web server vulnerabilities and misconfigurations |
| sslscan | SSL/TLS analysis | Checks for weak cryptographic implementations |
| whatweb | Web technology identification | Identifies web technologies and potential security issues |
| dirb | Directory discovery | Finds hidden directories on web servers |
| enum4linux | SMB enumeration | Enumerates information from Windows and Samba systems |
| netdiscover | Network discovery | Identifies active hosts on the network |

#### Using the Fallback Scanner
The fallback scanner is used exactly the same way as the Nessus scanner:

1. Click the "Run Full Scan" button
2. The dashboard automatically detects which scanner to use
3. The interface will indicate which scanning system is being used
4. Monitor progress through the same progress modal
5. View results in the same results interface

#### Stopping a Scan in Progress
You can stop an in-progress scan by clicking the "Stop Scan" button in the progress modal.

### 📚 Additional Resources

- **Nessus Documentation**: [Tenable Nessus User Guide](https://docs.tenable.com/nessus/)
- **CVE Database**: [MITRE CVE](https://cve.mitre.org/)
- **Security Best Practices**: [OWASP Guidelines](https://owasp.org/)

### 🆘 Support

For technical support:
1. Check the application logs: `/home/kali/latest/dashboard/app.log`
2. Review the Nessus Installation Guide: `Nessus_Installation_Guide.md`
3. Run the integration test suite: `python3 test_nessus_integration.py`

### 📝 Version History

- **v2.0** - Nessus integration with real-time progress monitoring
- **v1.5** - Enhanced UI with professional modals and reporting
- **v1.0** - Basic security dashboard with network scanning

---

**Last Updated**: May 25, 2025  
**Author**: WiGuard Development Team  
**Version**: 2.0
