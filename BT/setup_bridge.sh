#!/bin/bash

# Arduino Bridge Setup Script

echo "=== Arduino Nano Bridge Setup ==="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found"

# Install required Python packages
echo "Installing required Python packages..."
pip3 install pyserial requests

# Make scripts executable
chmod +x arduino_bridge.py

echo "✓ Python dependencies installed"

# Check for Arduino ports
echo "Checking for Arduino devices..."
python3 -c "
import serial.tools.list_ports
ports = serial.tools.list_ports.comports()
arduino_ports = []
for port in ports:
    if 'Arduino' in port.description or 'USB' in port.description or 'ACM' in port.device or 'ttyUSB' in port.device:
        arduino_ports.append(f'{port.device} - {port.description}')

if arduino_ports:
    print('✓ Found potential Arduino ports:')
    for port in arduino_ports:
        print(f'  {port}')
else:
    print('⚠️  No Arduino devices detected')
    print('   Make sure Arduino is connected and drivers are installed')
"

echo ""
echo "=== Setup Instructions ==="
echo "1. Upload 'Arduino_Nano_Bridge.ino' to your Arduino Nano"
echo "2. Connect Arduino Nano via USB to your PC"
echo "3. Make sure Flask API is running: python3 flaskkk.py"
echo "4. Run the bridge: python3 arduino_bridge.py"
echo ""
echo "=== Quick Test ==="
echo "To test if everything is working:"
echo "1. python3 arduino_bridge.py --help"
echo "2. python3 arduino_bridge.py --port /dev/ttyUSB0  (adjust port as needed)"
echo ""
echo "The bridge will automatically detect Arduino ports and forward data to your Flask API."
