#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
#define OLED_RESET     -1 // Reset pin # (or -1 if sharing Arduino reset pin)
#define SCREEN_ADDRESS 0x3C // See datasheet for Address; 0x3D for 128x64, 0x3C for 128x32

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

void setup() {
  Serial.begin(115200);
  
  Serial.println(F("OLED Diagnostic Test Starting..."));
  
  // Initialize display
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("SSD1306 allocation failed"));
    // Don't proceed, loop forever
    for(;;) {
      Serial.println(F("OLED FAILED - Check wiring!"));
      delay(1000);
    }
  }
  
  Serial.println(F("OLED initialized successfully"));
  
  // Test display
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(F("OLED Test"));
  display.println(F("Working!"));
  display.display();
  
  delay(2000);
}

void loop() {
  // Continuous OLED test
  static unsigned long lastUpdate = 0;
  static int counter = 0;
  
  if (millis() - lastUpdate > 1000) {
    lastUpdate = millis();
    counter++;
    
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 0);
    display.println(F("OLED Diagnostic"));
    display.setCursor(0, 8);
    display.print(F("Counter: "));
    display.println(counter);
    display.setCursor(0, 16);
    display.print(F("Time: "));
    display.print(millis() / 1000);
    display.println(F("s"));
    display.setCursor(0, 24);
    display.println(F("Status: OK"));
    
    // Draw a simple animation
    display.drawRect(100, 8, 20, 16, SSD1306_WHITE);
    int fillHeight = (counter % 8) * 2;
    display.fillRect(102, 22 - fillHeight, 16, fillHeight, SSD1306_WHITE);
    
    display.display();
    
    Serial.print(F("OLED Update #"));
    Serial.print(counter);
    Serial.println(F(" - Display should be working"));
  }
}
