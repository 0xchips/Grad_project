#!/bin/bash
# Setup script for Kismet passwordless sudo
# This script helps configure passwordless sudo for Kismet

echo "=== Kismet Passwordless Sudo Setup ==="
echo "This script will configure sudo to allow running Kismet without password prompt."
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Error: Do not run this script as root. Run as your regular user."
    exit 1
fi

# Check if user is in sudo group
if ! groups | grep -q sudo; then
    echo "Error: Current user is not in the sudo group."
    echo "Please add your user to sudo group: sudo usermod -aG sudo \$USER"
    exit 1
fi

# Check if Kismet is installed
if ! command -v kismet &> /dev/null; then
    echo "Error: Kismet is not installed."
    echo "Please install Kismet first: sudo apt-get install kismet"
    exit 1
fi

echo "Current user: $(whoami)"
echo "Kismet location: $(which kismet)"
echo ""

read -p "Do you want to add passwordless sudo for Kismet? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 0
fi

# Create sudoers entry
KISMET_PATH=$(which kismet)
SUDOERS_ENTRY="$(whoami) ALL=(ALL) NOPASSWD: $KISMET_PATH"
SUDOERS_FILE="/etc/sudoers.d/kismet-$(whoami)"

echo "Creating sudoers entry..."
echo "Entry: $SUDOERS_ENTRY"
echo "File: $SUDOERS_FILE"

# Create the sudoers file
echo "$SUDOERS_ENTRY" | sudo tee "$SUDOERS_FILE" > /dev/null

if [ $? -eq 0 ]; then
    echo "✓ Sudoers entry created successfully!"
    
    # Set proper permissions
    sudo chmod 0440 "$SUDOERS_FILE"
    
    # Test the configuration
    echo ""
    echo "Testing passwordless sudo for Kismet..."
    if sudo -n kismet --version > /dev/null 2>&1; then
        echo "✓ Passwordless sudo for Kismet is working!"
        echo ""
        echo "You can now start Kismet from the web interface without password prompts."
    else
        echo "✗ Test failed. There might be an issue with the sudoers configuration."
        echo "You may need to check /etc/sudoers.d/kismet-$(whoami)"
    fi
else
    echo "✗ Failed to create sudoers entry."
    exit 1
fi

echo ""
echo "=== Setup Complete ==="
echo "Note: If you still have issues, try restarting your terminal session."
