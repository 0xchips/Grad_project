#include <Wire.h>

void setup() {
  Wire.begin();
  Serial.begin(115200);
  while (!Serial);
  Serial.println("\nI2C Scanner - OLED Diagnostic");
  Serial.println("Scanning for I2C devices...");
}

void loop() {
  byte error, address;
  int nDevices;

  Serial.println("Scanning...");

  nDevices = 0;
  for(address = 1; address < 127; address++ ) {
    // The I2C scanner uses the return value of the Write.endTransmission 
    // to see if a device did acknowledge to the address.
    Wire.beginTransmission(address);
    error = Wire.endTransmission();

    if (error == 0) {
      Serial.print("I2C device found at address 0x");
      if (address < 16) 
        Serial.print("0");
      Serial.print(address, HEX);
      Serial.println(" !");
      
      // Check if this is likely an OLED
      if (address == 0x3C || address == 0x3D) {
        Serial.println("  -> This is likely your OLED display!");
      }
      
      nDevices++;
    }
    else if (error == 4) {
      Serial.print("Unknown error at address 0x");
      if (address < 16) 
        Serial.print("0");
      Serial.println(address, HEX);
    }    
  }
  
  if (nDevices == 0) {
    Serial.println("No I2C devices found");
    Serial.println("Check your wiring:");
    Serial.println("  Arduino A4 -> OLED SDA");
    Serial.println("  Arduino A5 -> OLED SCL");
    Serial.println("  Arduino 5V -> OLED VCC");
    Serial.println("  Arduino GND -> OLED GND");
  }
  else {
    Serial.print("Found ");
    Serial.print(nDevices);
    Serial.println(" device(s)");
  }

  delay(5000);  // wait 5 seconds for next scan
}
