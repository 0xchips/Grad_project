# OLED Display Troubleshooting Guide

## Problem: OLED Screen Stopped Working in Bridge Code

### Possible Causes:
1. **Incorrect OLED initialization**
2. **I2C address conflicts**
3. **Power supply issues**
4. **Wiring problems**
5. **Library compatibility issues**
6. **Memory conflicts**

## Quick Diagnostics

### Step 1: Test OLED Hardware
Upload the `OLED_Diagnostic.ino` file to test if OLED hardware is working:

```bash
# Upload this file to Arduino:
/home/kali/Grad_project-chipss/Grad_project-chipss/BT/OLED_Diagnostic.ino
```

**Expected Output:**
- Serial Monitor: "OLED initialized successfully"
- OLED Display: Shows counter, time, and simple animation

**If OLED Diagnostic Fails:**
- Check wiring connections
- Verify power supply (3.3V or 5V depending on OLED module)
- Try different I2C address (0x3C or 0x3D)

### Step 2: Check Wiring

**Standard SSD1306 OLED Wiring for Arduino Nano:**
```
Arduino Nano   SSD1306 OLED
A4 (SDA)   →   SDA
A5 (SCL)   →   SCL
5V         →   VCC (or 3.3V depending on module)
GND        →   GND
```

**Important Notes:**
- Some OLED modules require 3.3V, others work with 5V
- Ensure solid connections (no loose wires)
- Check for short circuits

### Step 3: I2C Scanner
Use this code to scan for I2C devices:

```cpp
#include <Wire.h>

void setup() {
  Wire.begin();
  Serial.begin(115200);
  Serial.println("I2C Scanner");
}

void loop() {
  byte error, address;
  int nDevices;
  
  Serial.println("Scanning...");
  nDevices = 0;
  for(address = 1; address < 127; address++ ) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    if (error == 0) {
      Serial.print("I2C device found at address 0x");
      if (address<16) Serial.print("0");
      Serial.print(address,HEX);
      Serial.println(" !");
      nDevices++;
    }
  }
  if (nDevices == 0) Serial.println("No I2C devices found\n");
  else Serial.println("done\n");
  delay(5000);
}
```

## Fixed Issues in Updated Code

### 1. Proper OLED Initialization
**Old Code:**
```cpp
display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
```

**New Code:**
```cpp
if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
  Serial.println(F("SSD1306 allocation failed"));
  for(;;); // Don't proceed if OLED fails
}
```

### 2. Correct Display Constants
**Old Code:**
```cpp
display.setTextColor(WHITE);
```

**New Code:**
```cpp
display.setTextColor(SSD1306_WHITE);
```

### 3. Simplified Display Logic
- Removed complex scrolling animation that could cause memory issues
- Added proper display buffer management
- Reduced memory usage in display functions

### 4. Better Error Handling
- Added OLED initialization checks
- Added serial output for debugging
- Simplified display updates to prevent conflicts

## Testing Steps

### 1. Upload Fixed Arduino Code
Upload the updated `Arduino_Nano_Bridge.ino` with the fixes.

### 2. Monitor Serial Output
Open Serial Monitor (115200 baud) and look for:
```
Starting 2.4GHz Scanner with PC Bridge...
Scanner initialized. Sending data to PC bridge...
```

**If you see "SSD1306 allocation failed":**
- Check wiring
- Try different I2C address
- Check power supply

### 3. Test Bridge Functionality
Run the bridge script and verify:
```bash
cd /home/kali/Grad_project-chipss/Grad_project-chipss/BT
python3 arduino_bridge.py
```

## Common OLED Issues and Solutions

### Issue 1: Display Shows Nothing
**Solutions:**
- Check power connections (VCC and GND)
- Verify I2C address (try 0x3C or 0x3D)
- Test with OLED diagnostic code

### Issue 2: Display Works Initially Then Stops
**Solutions:**
- Reduce display update frequency
- Simplify display content
- Check for memory leaks in code

### Issue 3: Partial Display or Garbled Text
**Solutions:**
- Check I2C connections (SDA/SCL)
- Verify power supply stability
- Add delays between display operations

### Issue 4: "SSD1306 allocation failed" Error
**Solutions:**
- Check wiring connections
- Try different I2C address
- Verify OLED module compatibility

## Alternative OLED Configurations

### For 0.96" 128x64 OLED:
```cpp
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define SCREEN_ADDRESS 0x3D  // Often 0x3D for 128x64
```

### For Different I2C Address:
```cpp
#define SCREEN_ADDRESS 0x3D  // Try 0x3D if 0x3C doesn't work
```

## Hardware Verification Checklist

- [ ] OLED module is getting power (LED indicator if present)
- [ ] SDA connected to A4 on Arduino Nano
- [ ] SCL connected to A5 on Arduino Nano
- [ ] VCC connected to 5V or 3.3V (check module requirements)
- [ ] GND connected to Arduino GND
- [ ] No loose connections
- [ ] No short circuits

## Code Verification Checklist

- [ ] Correct Adafruit_SSD1306 library installed
- [ ] Proper display initialization with error checking
- [ ] Using SSD1306_WHITE instead of WHITE
- [ ] display.display() called after each update
- [ ] No memory conflicts with other operations

## Next Steps

1. **Upload OLED_Diagnostic.ino** to test hardware
2. **Upload fixed Arduino_Nano_Bridge.ino** with OLED improvements
3. **Test bridge functionality** with python script
4. **Monitor serial output** for any error messages

If OLED still doesn't work after these steps, the issue is likely hardware-related (wiring, power, or faulty OLED module).
