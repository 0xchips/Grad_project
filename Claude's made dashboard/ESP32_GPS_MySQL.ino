#include <TinyGPS++.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

TinyGPSPlus gps;

// Use UART1 on ESP32
HardwareSerial gpsSerial(1);

// Set your GPS RX/TX pins
#define RXD2 16  // GPS TX -> ESP32 RX (GPIO 16)
#define TXD2 17  // GPS RX -> ESP32 TX (GPIO 17)

// WiFi credentials - replace with your network details
const char* ssid = "YourWiFiName";
const char* password = "YourWiFiPassword";

// API configuration
const char* serverURL = "http://your-server-ip:5050/api/esp32/gps"; // Use API adapter port
const String deviceId = "ESP32-GPS-1"; // Unique identifier for this device
unsigned long lastSendTime = 0;
const int sendInterval = 10000; // Send data every 10 seconds

void setup() {
  Serial.begin(115200);         // USB Serial Monitor
  gpsSerial.begin(9600, SERIAL_8N1, RXD2, TXD2);  // GPS UART

  Serial.println("GPS Jamming Detector - Using GPS module (NEO-6M)");
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  while (gpsSerial.available()) {
    int data = gpsSerial.read();
    if (gps.encode(data)) {
      float latitude = gps.location.lat();
      float longitude = gps.location.lng();
      int numSatellites = gps.satellites.value();
      float hdop = gps.hdop.hdop();

      Serial.print("Latitude: ");
      Serial.println(latitude, 6);
      Serial.print("Longitude: ");
      Serial.println(longitude, 6);
      Serial.print("Number of Satellites: ");
      Serial.println(numSatellites);
      Serial.print("HDOP: ");
      Serial.println(hdop);

      bool jamming = false;
      if (numSatellites < 3 || hdop > 2.0) {
        Serial.println("🚨 GPS Jamming Detected!");
        jamming = true;
      } else {
        Serial.println("GPS Signal OK.");
      }
      
      // Send data to server periodically
      unsigned long currentMillis = millis();
      if (currentMillis - lastSendTime >= sendInterval) {
        lastSendTime = currentMillis;
        sendGPSData(latitude, longitude, numSatellites, hdop, jamming);
      }
    }
  }

  if (millis() > 5000 && gps.charsProcessed() < 10) {
    Serial.println("No GPS detected: check wiring.");
    delay(5000);
  }
}

// Send GPS data to API adapter
void sendGPSData(float lat, float lng, int satellites, float hdop, bool jamming) {
  // Only send if WiFi is connected
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    
    // Start HTTP connection
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");
    
    // Create JSON document
    DynamicJsonDocument doc(1024);
    doc["latitude"] = lat;
    doc["longitude"] = lng;
    doc["satellites"] = satellites;
    doc["hdop"] = hdop;
    doc["jamming_detected"] = jamming;
    doc["device_id"] = deviceId;
    
    // Serialize JSON to string
    String jsonStr;
    serializeJson(doc, jsonStr);
    
    // Send POST request
    int httpResponseCode = http.POST(jsonStr);
    
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("HTTP Response code: " + String(httpResponseCode));
      Serial.println("Response: " + response);
    } else {
      Serial.println("Error on sending data. HTTP Error code: " + String(httpResponseCode));
    }
    
    // Free resources
    http.end();
  } else {
    Serial.println("WiFi Disconnected. Cannot send data.");
    // Try to reconnect
    WiFi.begin(ssid, password);
  }
}
