#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
#define OLED_RESET     -1 // Reset pin # (or -1 if sharing Arduino reset pin)
#define SCREEN_ADDRESS 0x3C // See datasheet for Address; 0x3D for 128x64, 0x3C for 128x32

#define CE  9

#define CHANNELS  64
int channel[CHANNELS];

int  line;
char grey[] = " .:-=+*aRW";

#define _NRF24_CONFIG      0x00
#define _NRF24_EN_AA       0x01
#define _NRF24_RF_CH       0x05
#define _NRF24_RF_SETUP    0x06
#define _NRF24_RPD         0x09

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

byte count;
byte sensorArray[128];
byte drawHeight;

char filled = 'F'; 
char drawDirection = 'R'; 
char slope = 'W'; 

// Bridge communication variables
const String deviceId = "NANO-2.4GHz-Scanner-001";
unsigned long lastDataSend = 0;
const unsigned long sendInterval = 5000; // Send structured data every 5 seconds
int maxSignalSinceLastSend = 0;

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

void sendStructuredData(int maxSignal, String spectrumData) {
  // Send JSON-like structured data that the Python bridge can parse
  Serial.println("===SPECTRUM_DATA_START===");
  Serial.print("{\"device_id\":\"");
  Serial.print(deviceId);
  Serial.print("\",\"device_name\":\"Arduino Nano 2.4GHz Scanner\",\"signal_strength\":");
  Serial.print(maxSignal);
  Serial.print(",\"max_signal\":");
  Serial.print(maxSignal);
  Serial.print(",\"channel\":0,\"rssi_value\":");
  Serial.print(maxSignal);
  Serial.print(",\"detection_type\":\"spectrum\",\"spectrum_data\":\"");
  Serial.print(spectrumData);
  Serial.print("\",\"raw_data\":{\"scan_channels\":");
  Serial.print(CHANNELS);
  Serial.print(",\"scan_method\":\"nRF24L01\",\"device_type\":\"Arduino_Nano\",\"firmware_version\":\"1.0\"}}");
  Serial.println();
  Serial.println("===SPECTRUM_DATA_END===");
}

void testOLEDDisplay() {
  // Simple OLED test function
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(F("OLED Test"));
  display.setCursor(0, 8);
  display.println(F("Display Working"));
  display.setCursor(0, 16);
  display.print(F("Time: "));
  display.print(millis() / 1000);
  display.setCursor(0, 24);
  display.println(F("Bridge Ready"));
  display.display();
}

void outputChannels(void)
{
 int norm = 0;
 
 for( int i=0 ; i<CHANNELS ; i++)
   if( channel[i]>norm ) norm = channel[i];
   
 // Track maximum signal for bridge transmission
 if (norm > maxSignalSinceLastSend) {
   maxSignalSinceLastSend = norm;
 }
 
 // Build spectrum data string
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
 
 Serial.print("| ");
 Serial.println(norm);

 // Update OLED display
 display.clearDisplay();
 
 // Display bridge status
 display.setTextSize(1);
 display.setTextColor(SSD1306_WHITE);
 display.setCursor(0, 0);
 display.println(F("Bridge: PC"));
 
 // Display maximum signal value
 display.setCursor(85, 0);
 display.print(F("Max: "));
 display.print(norm);
 
 // Display current time indicator (simple counter)
 display.setCursor(0, 8);
 display.print(F("Scan: "));
 display.print(millis() / 1000);
 display.print(F("s"));

 // Draw spectrum visualization frame
 display.drawRect(0, 16, 128, 16, SSD1306_WHITE);
 
 // Draw spectrum bars
 for (int i = 0; i < min(CHANNELS, 60); i++) {
   int barHeight = map(channel[i], 0, norm > 0 ? norm : 1, 0, 14);
   if (barHeight > 0) {
     display.drawLine(i * 2 + 1, 31 - barHeight, i * 2 + 1, 31, SSD1306_WHITE);
   }
 }
 
 // Show transmission status if data was just sent
 if (millis() - lastDataSend < 1000) {
   display.setCursor(90, 24);
   display.setTextSize(1);
   display.setTextColor(SSD1306_WHITE);
   display.print(F("TX:OK"));
 }

 display.display();
 
 // Check if it's time to send structured data to bridge
 if (millis() - lastDataSend > sendInterval) {
   sendStructuredData(maxSignalSinceLastSend, currentSpectrum);
   lastDataSend = millis();
   maxSignalSinceLastSend = 0; // Reset for next interval
   
   Serial.println("Data sent to bridge");
 }
}

void printChannels(void)
{
 Serial.println(">      1 2  3 4  5  6 7 8  9 10 11 12 13  14                     <");
}

void setup()
{
 Serial.begin(115200);

 // Initialize display
 if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
   Serial.println(F("SSD1306 allocation failed"));
   // Don't proceed, loop forever
   for(;;);
 }
 
 display.clearDisplay();
 display.setTextSize(1);
 display.setTextColor(SSD1306_WHITE);
 display.setCursor(0, 0);
 display.println(F("Starting Scanner..."));
 display.display();
 delay(2000);

 for (count = 0; count <= 128; count++) 
 {
   sensorArray[count] = 0;
 }
 
 Serial.println("Starting 2.4GHz Scanner with PC Bridge...");
 Serial.println();

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
 
 Serial.println("Scanner initialized. Sending data to PC bridge...");
 
 // Display initialization complete message
 display.clearDisplay();
 display.setCursor(0, 0);
 display.println(F("Scanner Ready"));
 display.println(F("Bridge: PC"));
 display.display();
 delay(1000);
}

void loop()
{
 scanChannels();
 outputChannels();
 
 if( line++>12 )
 {
   printChannels();
   line = 0;
 }
}
