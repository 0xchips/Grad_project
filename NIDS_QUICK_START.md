# NIDS Dashboard Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- Linux system (Kali Linux recommended)
- Python 3.8+
- MySQL/MariaDB
- Suricata IDS

### Quick Launch
```bash
# Navigate to dashboard directory
cd /home/kali/latest/dashboard

# Start the services
python3 suricata_parser.py &  # Background parser
python3 flaskkk.py            # Main application

# Access the dashboard
firefox http://localhost:5053/nids
```

## 📊 Dashboard Features

### Main Interface
- **Real-time Alerts**: Live security event monitoring
- **Statistical Charts**: Attack trends and distributions
- **Filter Controls**: Time, severity, protocol, and IP filtering
- **Alert Details**: Comprehensive event information

### Key Sections
1. **System Status** - Health indicators and metrics
2. **Alert Statistics** - Severity and protocol breakdowns  
3. **Timeline Chart** - Historical attack patterns
4. **Top IPs** - Source and destination analysis
5. **Recent Alerts** - Detailed alert table
6. **DNS Analysis** - Suspicious domain detection

## 🧪 Testing & Validation

### Run Attack Simulations
```bash
# Basic testing
python3 simple_ids_test.py

# Comprehensive testing  
python3 test_ids_attacks.py

# Validation suite
python3 validate_nids_dashboard.py

# Generate report
python3 nids_test_report.py
```

### Expected Results
- DNS queries to malicious domains
- HTTP attack pattern detection
- Port scanning alerts
- Suspicious user-agent detection
- Real-time dashboard updates

## 🔧 Configuration

### Time Ranges
- 1 Hour: Recent activity
- 6 Hours: Short-term analysis
- 24 Hours: Daily overview
- 7 Days: Weekly trends (default)

### Alert Severities
- 🔴 **Critical**: Immediate threats
- 🟠 **High**: Significant risks
- 🟡 **Medium**: Moderate concerns
- 🟢 **Low**: Informational

### API Endpoints
- `/api/nids-status` - System health
- `/api/nids-stats` - Statistics
- `/api/nids-alerts` - Alert data
- `/api/nids-dns` - DNS analysis
- `/api/nids-geoip/<ip>` - IP location

## 🛠️ Troubleshooting

### Common Issues

**Dashboard not loading:**
```bash
# Check if Flask is running
ps aux | grep flaskkk.py

# Restart if needed
python3 flaskkk.py
```

**No alerts appearing:**
```bash
# Check Suricata parser
ps aux | grep suricata_parser.py
tail -f suricata_parser.log

# Restart if needed
python3 suricata_parser.py &
```

**Database connection errors:**
```bash
# Check MySQL service
systemctl status mysql

# Test connection
mysql -u dashboard -p security_dashboard
```

### Log Files
- `suricata_parser.log` - Parser activity
- `app.log` - Application logs
- `flask_output.log` - Server output

## 📈 Performance Tips

### For High Alert Volumes
1. Increase database connection pool
2. Implement alert aggregation
3. Add database indexing
4. Configure log rotation

### Dashboard Optimization
1. Adjust refresh intervals
2. Limit chart data points
3. Implement data pagination
4. Cache frequently accessed data

## 🔒 Security Considerations

### Production Deployment
1. **HTTPS**: Enable SSL/TLS encryption
2. **Authentication**: Implement user management
3. **Firewall**: Restrict access to trusted networks
4. **Monitoring**: Set up system health monitoring
5. **Backups**: Regular database backups

### Access Control
```bash
# Restrict to localhost (default)
# For remote access, modify flaskkk.py:
app.run(host='0.0.0.0', port=5053)  # CAUTION: Use with firewall
```

## 🎯 Next Steps

### Immediate Actions
1. Review system status and alerts
2. Configure alert thresholds
3. Set up monitoring schedules
4. Test incident response procedures

### Advanced Features
1. Custom detection rules
2. Threat intelligence feeds
3. Automated response actions
4. SIEM integration
5. Machine learning models

## 📞 Support

### Documentation
- `NIDS_IMPLEMENTATION_COMPLETE.md` - Full project details
- `WiGuard_User_Guide.md` - General system guide
- API test page: http://localhost:5053/api_test.html

### Testing Tools
- Attack simulators in `/testing/` directory
- Validation scripts for system verification
- Performance testing utilities

---

**Dashboard URL**: http://localhost:5053/nids  
**API Documentation**: http://localhost:5053/api_test.html  
**Status**: 🟢 Operational and Ready for Use
