#!/bin/bash

# Setup Kismet interface script
# This script prepares the wireless interface for Kismet monitoring

INTERFACE="wlan0"
MONITOR_INTERFACE="wlan0mon"

echo "Setting up wireless interface for Kismet monitoring..."

# Check if interface exists
if ! ip link show "$INTERFACE" >/dev/null 2>&1; then
    echo "Error: Interface $INTERFACE not found"
    exit 1
fi

# Check if monitor interface already exists
if ip link show "$MONITOR_INTERFACE" >/dev/null 2>&1; then
    echo "Monitor interface $MONITOR_INTERFACE already exists"
else
    echo "Creating monitor interface..."
    # Put interface down
    sudo ip link set "$INTERFACE" down
    
    # Set to monitor mode
    sudo iw dev "$INTERFACE" set type monitor
    
    # Bring interface up
    sudo ip link set "$INTERFACE" up
    
    echo "Monitor mode enabled on $INTERFACE"
fi

# Check if interface is up
if ip link show "$INTERFACE" | grep -q "state UP"; then
    echo "Interface $INTERFACE is ready for monitoring"
else
    echo "Bringing up interface $INTERFACE..."
    sudo ip link set "$INTERFACE" up
fi

echo "Kismet interface setup completed!"
echo "You can now start Kismet with: kismet -c $INTERFACE"
