# ESP32 GPS Jamming Detector - Setup Instructions

This document provides detailed step-by-step instructions for setting up an ESP32-based GPS jamming detector that integrates with the security dashboard.

## Hardware Requirements

1. **ESP32 Development Board** - Any ESP32-based board (ESP32-WROOM, ESP32-WROVER, etc.)
2. **GPS Module** - NEO-6M or similar UART-based GPS module
3. **Jumper Wires** - For connecting components
4. **USB Cable** - For programming the ESP32
5. **Power Source** - USB power or separate 5V supply

## Hardware Assembly

1. **Connect the GPS Module to ESP32:**
   - GPS VCC → ESP32 3.3V
   - GPS GND → ESP32 GND
   - GPS TX → ESP32 RX (GPIO 16)
   - GPS RX → ESP32 TX (GPIO 17)

   > **Note:** If your GPS module requires 5V power, connect VCC to the 5V pin on the ESP32 instead of 3.3V.

2. **Antenna Positioning:**
   - If your GPS module has an external antenna, position it with clear view of the sky
   - For best results, keep the antenna away from metal objects and electromagnetic interference sources

## Software Prerequisites

1. **Arduino IDE Installation:**
   ```bash
   # For Ubuntu/Debian based systems
   sudo apt-get update
   sudo apt-get install arduino
   ```

2. **ESP32 Board Support:**
   - Open Arduino IDE
   - Go to File → Preferences
   - Add this URL to "Additional Boards Manager URLs":
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to Tools → Board → Boards Manager
   - Search for "esp32" and install "ESP32 by Espressif Systems"

3. **Required Libraries:**
   - Open Arduino IDE
   - Go to Sketch → Include Library → Manage Libraries
   - Install the following libraries:
     - TinyGPS++ by Mikal Hart
     - ArduinoJson by Benoit Blanchon

## ESP32 Configuration

1. **Download the ESP32 Sketch:**
   - The `ESP32_GPS_MySQL.ino` file is located in your project folder
   - Open it with Arduino IDE

2. **Configure WiFi Settings:**
   - Locate these lines in the code:
     ```cpp
     // WiFi credentials - replace with your network details
     const char* ssid = "YourWiFiName";
     const char* password = "YourWiFiPassword";
     ```
   - Replace with your actual WiFi credentials

3. **Configure Server Settings:**
   - Locate these lines:
     ```cpp
     // API configuration
     const char* serverURL = "http://your-server-ip:5050/api/esp32/gps";
     const String deviceId = "ESP32-GPS-1"; // Unique identifier for this device
     ```
   - Replace `your-server-ip` with the actual IP address of your server
   - Change `deviceId` to a unique name for this specific ESP32 device

4. **Optional Configuration:**
   - You can adjust the data sending interval (default is 10 seconds):
     ```cpp
     const int sendInterval = 10000; // Send data every 10 seconds
     ```
   - You can modify the jamming detection thresholds:
     ```cpp
     if (numSatellites < 3 || hdop > 2.0) {
       // Jamming detected
     }
     ```

## Uploading the Sketch

1. **Connect ESP32 to Computer:**
   - Connect your ESP32 to your computer using a USB cable

2. **Configure Arduino IDE Settings:**
   - Open Arduino IDE with the `ESP32_GPS_MySQL.ino` sketch
   - Go to Tools → Board → ESP32 → select your board type (e.g., "ESP32 Dev Module")
   - Go to Tools → Port → select the COM port connected to your ESP32
   - Go to Tools → Upload Speed → select "115200"

3. **Upload the Sketch:**
   - Click the Upload button (→) or press Ctrl+U
   - Wait for the "Done uploading" message

## Testing and Verification

1. **Serial Monitor:**
   - Open Arduino IDE Serial Monitor (Tools → Serial Monitor)
   - Set baud rate to 115200
   - You should see:
     - WiFi connection status
     - GPS data (latitude, longitude)
     - Number of satellites and HDOP (Horizontal Dilution of Precision)
     - Jamming detection status

2. **Server Connectivity Test:**
   - The Serial Monitor will show "HTTP Response code: 201" if data is successfully sent to server
   - If you see connection errors, check:
     - WiFi credentials
     - Server IP address and port
     - Whether the server is running

3. **Dashboard Verification:**
   - Open your web browser and navigate to: `http://your-server-ip/gps.html`
   - You should see your ESP32's GPS data on the map
   - Check the jamming detection status indicator

## Troubleshooting

1. **No GPS Signal:**
   - If you see "No GPS detected: check wiring", verify:
     - GPS module connections
     - Antenna placement (needs clear view of sky)
     - Try moving to a window or outdoors

2. **WiFi Connection Issues:**
   - Verify WiFi credentials
   - Check if ESP32 is within range of WiFi network
   - The Serial Monitor will display the assigned IP address when connected

3. **Data Not Appearing on Dashboard:**
   - Check API adapter response:
     ```bash
     curl http://your-server-ip:5050/api/gps?hours=24
     ```
   - Verify server is running:
     ```bash
     ./start_servers.sh
     ```
   - Check MySQL database connection

4. **GPS Jamming Simulation:**
   - To test jamming detection without actual jammers (illegal to use):
     - Cover the GPS antenna completely
     - Move to an area with poor GPS reception
     - Use the provided simulator script for software-only testing

## Advanced Configuration

1. **Multiple ESP32 Devices:**
   - Each ESP32 should have a unique `deviceId` value
   - Deploy multiple units in different locations for wider coverage

2. **Power Saving Mode:**
   - To extend battery life, add these lines to setup():
     ```cpp
     // Enable light sleep mode
     esp_sleep_enable_timer_wakeup(sendInterval * 1000);
     ```
   - Add WiFi disconnect after sending data to save power

3. **External Antenna:**
   - For increased range and sensitivity, connect an external active GPS antenna
   - Ensure proper power requirements for active antennas

## Safety and Legal Considerations

1. **GPS Jammers:**
   - Owning or using actual GPS jammers is illegal in most countries
   - This system detects potential jamming but does not jam signals

2. **Privacy:**
   - The system collects and stores location data
   - Ensure compliance with relevant privacy regulations

3. **Power Considerations:**
   - For permanent installations, use a regulated power supply
   - For portable use, connect a suitable LiPo battery

## Maintenance

1. **Regular Updates:**
   - Check for updated libraries or firmware
   - Periodically verify system functionality

2. **Database Management:**
   - Set up a data retention policy to avoid excessive database growth
   - Consider adding scripts to purge old data

## Next Steps

1. **Integration with Alert Systems:**
   - Configure email or SMS alerts when jamming is detected
   - Add webhook support for integration with other security systems

2. **Case Design:**
   - Create a weatherproof enclosure for outdoor deployment
   - Consider ventilation for heat dissipation

3. **Analytics:**
   - Implement machine learning for better detection of jamming patterns
   - Create historical analysis reports
