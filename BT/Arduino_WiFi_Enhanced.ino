#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Note: This code is designed for ESP32 with WiFi capability
// If using Arduino Nano, you'll need an ESP8266 WiFi module or use ESP32

#define OLED_RESET 4
#define CE  9

#define CHANNELS  64
int channel[CHANNELS];

int  line;
char grey[] = " .:-=+*aRW";

// WiFi Configuration
const char* ssid = "ZainFiber-2.4G-kP9f";
const char* password = "MkN30062000";

// Server Configuration
const char* serverURL = "http://192.168.1.100:5053/api/bluetooth_detections";  // Update with your server IP
const String deviceId = "NANO-2.4GHz-Scanner-001";

// nRF24L01 Registers
#define _NRF24_CONFIG      0x00
#define _NRF24_EN_AA       0x01
#define _NRF24_RF_CH       0x05
#define _NRF24_RF_SETUP    0x06
#define _NRF24_RPD         0x09

Adafruit_SSD1306 display = Adafruit_SSD1306(128, 32, &Wire);

byte count;
byte sensorArray[128];
byte drawHeight;

char filled = 'F'; 
char drawDirection = 'R'; 
char slope = 'W'; 

// Data transmission variables
unsigned long lastTransmission = 0;
const unsigned long transmissionInterval = 5000; // Send data every 5 seconds
int maxSignalSinceLastTransmission = 0;
String spectrumDataBuffer = "";

// WiFi status tracking
bool wifiConnected = false;
unsigned long lastWiFiCheck = 0;
const unsigned long wifiCheckInterval = 30000; // Check WiFi every 30 seconds

byte getRegister(byte r)
{
 byte c;
 
 PORTB &=~_BV(2);
 c = SPI.transfer(r&0x1F);
 c = SPI.transfer(0);  
 PORTB |= _BV(2);

 return(c);
}

void setRegister(byte r, byte v)
{
 PORTB &=~_BV(2);
 SPI.transfer((r&0x1F)|0x20);
 SPI.transfer(v);
 PORTB |= _BV(2);
}
 
void powerUp(void)
{
 setRegister(_NRF24_CONFIG,getRegister(_NRF24_CONFIG)|0x02);
 delayMicroseconds(130);
}

void powerDown(void)
{
 setRegister(_NRF24_CONFIG,getRegister(_NRF24_CONFIG)&~0x02);
}

void enable(void)
{
   PORTB |= _BV(1);
}

void disable(void)
{
   PORTB &=~_BV(1);
}

void setRX(void)
{
 setRegister(_NRF24_CONFIG,getRegister(_NRF24_CONFIG)|0x01);
 enable();
 delayMicroseconds(100);
}

void scanChannels(void)
{
 disable();
 for( int j=0 ; j<200  ; j++)
 {
   for( int i=0 ; i<CHANNELS ; i++)
   {
     setRegister(_NRF24_RF_CH,(128*i)/CHANNELS);
     
     setRX();
     
     delayMicroseconds(40);
     
     disable();
     
     if( getRegister(_NRF24_RPD)>0 )   channel[i]++;
   }
 }
}

void setupWiFi() {
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println();
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    
    // Display WiFi status on OLED
    display.clearDisplay();
    display.setCursor(0, 0);
    display.setTextSize(1);
    display.setTextColor(WHITE);
    display.println("WiFi Connected");
    display.print("IP: ");
    display.println(WiFi.localIP());
    display.display();
    delay(2000);
  } else {
    wifiConnected = false;
    Serial.println("WiFi connection failed!");
    
    display.clearDisplay();
    display.setCursor(0, 0);
    display.setTextSize(1);
    display.setTextColor(WHITE);
    display.println("WiFi Failed");
    display.println("Operating offline");
    display.display();
    delay(2000);
  }
}

void checkWiFiConnection() {
  if (millis() - lastWiFiCheck > wifiCheckInterval) {
    lastWiFiCheck = millis();
    
    if (WiFi.status() != WL_CONNECTED) {
      wifiConnected = false;
      Serial.println("WiFi disconnected, attempting reconnection...");
      setupWiFi();
    } else {
      wifiConnected = true;
    }
  }
}

void sendDataToServer(int maxSignal, String spectrumData) {
  if (!wifiConnected) {
    Serial.println("WiFi not connected, skipping data transmission");
    return;
  }
  
  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  DynamicJsonDocument doc(1024);
  doc["device_id"] = deviceId;
  doc["device_name"] = "Arduino Nano 2.4GHz Scanner";
  doc["signal_strength"] = maxSignal;
  doc["max_signal"] = maxSignal;
  doc["channel"] = 0; // We scan all channels, use 0 as identifier
  doc["rssi_value"] = maxSignal;
  doc["detection_type"] = "spectrum";
  doc["spectrum_data"] = spectrumData;
  
  // Add raw data for detailed analysis
  JsonObject rawData = doc.createNestedObject("raw_data");
  rawData["scan_channels"] = CHANNELS;
  rawData["scan_method"] = "nRF24L01";
  rawData["device_type"] = "Arduino_Nano";
  rawData["firmware_version"] = "1.0";
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  Serial.println("Sending data to server:");
  Serial.println(jsonString);
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
    Serial.print("Response: ");
    Serial.println(response);
    
    // Show transmission status on OLED
    display.setCursor(90, 24);
    display.setTextSize(1);
    display.setTextColor(WHITE);
    if (httpResponseCode == 201) {
      display.print("TX:OK");
    } else {
      display.print("TX:ERR");
    }
  } else {
    Serial.print("HTTP Error: ");
    Serial.println(httpResponseCode);
    
    display.setCursor(90, 24);
    display.setTextSize(1);
    display.setTextColor(WHITE);
    display.print("TX:FAIL");
  }
  
  http.end();
}

void outputChannels(void)
{
 int norm = 0;
 
 // Find maximum signal across all channels
 for( int i=0 ; i<CHANNELS ; i++)
   if( channel[i]>norm ) norm = channel[i];
   
 // Track maximum signal for transmission
 if (norm > maxSignalSinceLastTransmission) {
   maxSignalSinceLastTransmission = norm;
 }
 
 // Build spectrum data string for transmission
 String currentSpectrum = "|";
 
 Serial.print('|');
 for( int i=0 ; i<CHANNELS ; i++)
 {
   int pos;
   
   if( norm!=0 ) pos = (channel[i]*10)/norm;
   else          pos = 0;
   
   if( pos==0 && channel[i]>0 ) pos++;
   
   if( pos>9 ) pos = 9;
 
   Serial.print(grey[pos]);
   currentSpectrum += grey[pos];
   channel[i] = 0;
 }
 
 currentSpectrum += "| " + String(norm);
 spectrumDataBuffer = currentSpectrum;
 
 Serial.print("| ");
 Serial.println(norm);

 // Update OLED display
 display.clearDisplay();
 
 // Display maximum signal value
 display.setCursor(90, 10);
 display.setTextSize(2);
 display.setTextColor(WHITE);
 display.print(norm);
 display.setCursor(90, 8);
 display.setTextSize(1);
 display.setTextColor(WHITE);
 display.print("");

 // Display WiFi status
 display.setCursor(0, 0);
 display.setTextSize(1);
 display.setTextColor(WHITE);
 if (wifiConnected) {
   display.println("WiFi: OK");
 } else {
   display.println("WiFi: OFF");
 }

 // Draw spectrum visualization
 display.drawLine(0, 8, 0, 32, WHITE);
 display.drawLine(80, 8, 80, 32, WHITE);

 for (count = 8; count < 32; count += 6)
 {
   display.drawLine(80, count, 75, count, WHITE);
   display.drawLine(0, count, 5, count, WHITE);
 }

 for (count = 10; count < 80; count += 10)
 {
   display.drawPixel(count, 8 , WHITE);
   display.drawPixel(count, 31 , WHITE);
 }

 drawHeight = map(norm, 0, 200, 0, 24);
 sensorArray[0] = drawHeight;

 for (count = 1; count <= 80; count++ )
 {
   if (filled == 'D' || filled == 'd')
   {
     if (drawDirection == 'L' || drawDirection == 'l')
     {
       display.drawPixel(count, 32 - sensorArray[count - 1], WHITE);
     }
     else
     {
       display.drawPixel(80 - count, 32 - sensorArray[count - 1], WHITE);
     }
   }
   else
   {
     if (drawDirection == 'L' || drawDirection == 'l')
     {
       if (slope == 'W' || slope == 'w')
       {
         display.drawLine(count, 32, count, 32 - sensorArray[count - 1], WHITE);
       }
       else
       {
         display.drawLine(count, 9, count, 32 - sensorArray[count - 1], WHITE);
       }
     }
     else
     {
       if (slope == 'W' || slope == 'w')
       {
         display.drawLine(80 - count, 32, 80 - count, 32 - sensorArray[count - 1], WHITE);
       }
       else
       {
         display.drawLine(80 - count, 9, 80 - count, 32 - sensorArray[count - 1], WHITE);
       }
     }
   }
 }

 display.display(); 

 // Shift array for scrolling effect
 for (count = 80; count >= 2; count--) 
 {
   sensorArray[count - 1] = sensorArray[count - 2];
 }
 
 // Check if it's time to send data
 if (millis() - lastTransmission > transmissionInterval) {
   if (wifiConnected) {
     sendDataToServer(maxSignalSinceLastTransmission, spectrumDataBuffer);
   }
   lastTransmission = millis();
   maxSignalSinceLastTransmission = 0; // Reset for next interval
 }
}

void printChannels(void)
{
 Serial.println(">      1 2  3 4  5  6 7 8  9 10 11 12 13  14                     <");
}

void setup()
{
 Serial.begin(115200);

 display.begin(SSD1306_SWITCHCAPVCC, 0x3C);  
 display.clearDisplay();

 for (count = 0; count <= 128; count++) 
 {
   sensorArray[count] = 0;
 }
 
 Serial.println("Starting Enhanced 2.4GHz Scanner with WiFi...");
 Serial.println();
 
 // Initialize WiFi
 setupWiFi();
 
 Serial.println("Channel Layout");
 printChannels();
 
 SPI.begin();
 SPI.setDataMode(SPI_MODE0);
 SPI.setClockDivider(SPI_CLOCK_DIV2);
 SPI.setBitOrder(MSBFIRST);
 
 pinMode(CE,OUTPUT);
 disable();
 
 powerUp();
 
 setRegister(_NRF24_EN_AA,0x0);
 setRegister(_NRF24_RF_SETUP,0x0F);
 
 Serial.println("Scanner initialized. Starting spectrum monitoring...");
}

void loop()
{
  // Check WiFi connection periodically
  checkWiFiConnection();
  
  // Scan 2.4GHz spectrum
  scanChannels();
  
  // Output results and potentially send to server
  outputChannels();
  
  // Print channel layout periodically
  if( line++>12 )
  {
    printChannels();
    line = 0;
  }
}
