#!/bin/bash
# Install requirements for GPS detector and simulator

# Function to check if a package is installed
is_installed() {
  pip3 list | grep -F "$1" >/dev/null
  return $?
}

echo "Installing required Python packages for GPS detector..."

# Install pynmea2 for GPS NMEA parsing
if ! is_installed "pynmea2"; then
  echo "Installing pynmea2..."
  pip3 install pynmea2
fi

# Install pyserial for serial port communication
if ! is_installed "pyserial"; then
  echo "Installing pyserial..."
  pip3 install pyserial
fi

echo "Installation complete."
