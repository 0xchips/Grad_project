# Deauth Detector Dashboard Integration Guide

This guide explains how to connect the deauthentication attack detector to the MySQL database and view the attacks on the dashboard.

## Overview

The system works as follows:

1. The `detector.py` script monitors wireless traffic for deauthentication frames
2. When deauth attacks are detected, they are logged to the MySQL database
3. The dashboard queries the database and displays the attacks in real-time

## Quick Start

### 1. Set Up the Environment

```bash
# Navigate to the deauth directory
cd /path/to/Dashboard\ with\ docker/deauth/

# Make scripts executable
chmod +x deauth_toolkit.sh db_test.py detector.py visualizer.py

# Install dependencies
./deauth_toolkit.sh install
```

### 2. Test Database Connection

Before starting the detector, verify that the database connection is working:

```bash
# Test the database connection
./db_test.py --check

# Insert a test record to verify write access
./db_test.py --test-data

# Query recent records to verify read access
./db_test.py --query
```

### 3. Configure Monitor Mode

To detect deauthentication attacks, you need a wireless interface in monitor mode:

```bash
# Set up monitor mode using the toolkit
./deauth_toolkit.sh setup

# Or manually with airmon-ng:
sudo airmon-ng check kill
sudo airmon-ng start wlan0  # Replace wlan0 with your interface
```

### 4. Start the Detector

```bash
# Start the detector using the toolkit
./deauth_toolkit.sh start

# Or manually:
python3 detector.py
```

### 5. View the Dashboard

The dashboard is accessible at:

```
http://localhost/deauth.html
```

This page displays:
- Real-time deauth attack data
- Historical attack trends
- Top attackers and targets
- Attack frequency statistics

## Troubleshooting

### Database Connection Issues

If you're having trouble connecting to the database:

1. Verify the database is running:
   ```bash
   systemctl status mysql
   ```

2. Check database credentials in `detector.py`:
   ```python
   db_config = {
       'host': 'localhost',
       'user': 'dashboard',
       'passwd': 'securepass',
       'db': 'security_dashboard',
   }
   ```

3. Test database connectivity:
   ```bash
   ./db_test.py --check
   ```

### No Attacks Showing on Dashboard

If attacks aren't appearing on the dashboard:

1. Verify the detector is running:
   ```bash
   ./deauth_toolkit.sh status
   ```

2. Check the detector logs:
   ```bash
   ./deauth_toolkit.sh logs
   ```

3. Verify data is in the database:
   ```bash
   ./db_test.py --query
   ```

4. Try inserting a test record:
   ```bash
   ./db_test.py --test-data
   ```

5. Refresh the dashboard page

### Monitor Mode Issues

If you're having trouble with monitor mode:

1. Check available interfaces:
   ```bash
   iwconfig
   ```

2. Verify interface supports monitor mode:
   ```bash
   iw list | grep -A 10 "Supported interface modes"
   ```

3. Try a different wireless adapter if necessary

## Advanced Usage

### Visualize Attack Data

For offline analysis and visualization:

```bash
# Generate real-time visualization
./visualizer.py

# Create static analysis of the last 24 hours
./visualizer.py --static --hours 24

# Save plots to a directory
./visualizer.py --static --output ./attack_reports
```

### Perform Controlled Testing

To test your detection system with controlled deauth attacks:

```bash
# Launch deauth attack using the toolkit
./deauth_toolkit.sh attack

# View the resulting data on the dashboard
./deauth_toolkit.sh dashboard
```

## Dashboard Features

The deauth dashboard provides several key features:

1. **Attack Overview** - Summary statistics and current threat level
2. **Attack Timeline** - Chronological view of detected attacks
3. **Top Attackers** - Identifies the most active attack sources
4. **Top Targets** - Shows which networks are being targeted most frequently
5. **Data Table** - Detailed log of all detected attacks
6. **Export Functions** - Generate reports and export attack data

## System Architecture

```
┌──────────────┐     ┌───────────────┐     ┌─────────────┐
│  Wireless    │     │  detector.py  │     │   MySQL     │
│  Traffic     │────▶│  (Deauth      │────▶│  Database   │
│              │     │   Detector)   │     │             │
└──────────────┘     └───────────────┘     └──────┬──────┘
                                                  │
                                                  ▼
                            ┌─────────────────────────────────┐
                            │          Flask Web App          │
                            │    (Dashboard with Docker)      │
                            └─────────────────────────────────┘
                                                  │
                                                  ▼
                            ┌─────────────────────────────────┐
                            │      Web Browser Interface      │
                            │       (deauth.html page)        │
                            └─────────────────────────────────┘
```

## Integration Workflow

1. **Data Collection**: `detector.py` captures and analyzes wireless packets
2. **Data Storage**: Detected attacks are saved to the `network_attacks` table
3. **Data Retrieval**: The dashboard queries the database via API endpoints
4. **Data Visualization**: JavaScript renders the data in charts and tables
5. **User Interaction**: Users can filter, sort, and export the attack data

This integration provides a complete system for detecting, logging, analyzing, and visualizing deauthentication attacks in real-time.
