#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_wifi.h"

// ===== SETTINGS ===== //
#define SERIAL_BAUD 115200  // Baudrate for serial communication
#define CH_TIME 140         // Scan time (in ms) per channel
#define PKT_RATE 5          // Minimum packets required to recognize an attack
#define PKT_TIME 1          // Minimum update intervals before confirming an attack

// Channels to scan (adjust based on your region)
const short channels[] = { 1, 6, 11 };

// ===== Flask API SETTINGS ===== //
const char* ssid = "ssid";
const char* password = "pass";
const char* flask_server = "192.168.1.24";  // Replace with your Flask server IP
const int flask_port = 5000;                // Flask server port (default 5000)
const char* flask_endpoint = "/api/event";  // API endpoint on your Flask dashboard

// ===== Runtime variables ===== //
int ch_index = 0;               // Current channel index
volatile int packet_rate = 0;   // Deauth packet counter (resets each update)
int attack_counter = 0;         // Counter for consecutive attack intervals
unsigned long update_time = 0;  // Timestamp for last update interval
unsigned long ch_time = 0;      // Timestamp for last channel hop

// Global variable to store the last detected attacker's MAC address (Address2)
char attacker_mac[18] = "00:00:00:00:00:00";

// ===== Send Detection Event to Flask Dashboard ===== //
void sendDetection(const String &eventType) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String("http://") + flask_server + ":" + flask_port + flask_endpoint;
    WiFiClient client;
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    
    // Build a JSON payload containing the event type and attacker MAC.
    String jsonData = "{\"event\":\"" + eventType + "\", \"attacker_mac\":\"" + String(attacker_mac) + "\"}";
    int httpCode = http.POST(jsonData);
    if (httpCode > 0) {
      String payload = http.getString();
      Serial.println("Sent " + eventType + " to dashboard. Response: " + payload);
    } else {
      Serial.print("Failed to send ");
      Serial.print(eventType);
      Serial.print(". Error code: ");
      Serial.print(httpCode);
      Serial.print(" - ");
      Serial.println(http.errorToString(httpCode));
    }
    http.end();
  } else {
    Serial.println("WiFi not connected, cannot send detection.");
  }
}

// ===== Sniffer Callback for ESP32 ===== //
// This function is called for every captured packet.
void sniffer(void *buf, wifi_promiscuous_pkt_type_t type) {
  wifi_promiscuous_pkt_t *pkt = (wifi_promiscuous_pkt_t *)buf;
  // Ensure the packet is long enough (at least 24 bytes for the MAC header)
  if (pkt->rx_ctrl.sig_len < 24) return;
  uint8_t *packet = pkt->payload;
  
  // Check for deauthentication (0xC0) or disassociation (0xA0) frames.
  // In an 802.11 management frame:
  //   Bytes 0-1: Frame Control
  //   Bytes 2-3: Duration
  //   Bytes 4-9: Address 1 (Receiver)
  //   Bytes 10-15: Address 2 (Transmitter) <-- likely the attacker
  //   Bytes 16-21: Address 3 (BSSID)
  if (packet[0] == 0xC0 || packet[0] == 0xA0) {
    packet_rate++;
    // Extract the transmitter's MAC address (Address2)
    sprintf(attacker_mac, "%02X:%02X:%02X:%02X:%02X:%02X",
            packet[10], packet[11], packet[12],
            packet[13], packet[14], packet[15]);
    
    // For debugging, you can print the MAC addresses:
    /*
    char addr1[18], addr3[18];
    sprintf(addr1, "%02X:%02X:%02X:%02X:%02X:%02X",
            packet[4], packet[5], packet[6],
            packet[7], packet[8], packet[9]);
    sprintf(addr3, "%02X:%02X:%02X:%02X:%02X:%02X",
            packet[16], packet[17], packet[18],
            packet[19], packet[20], packet[21]);
    Serial.print("Deauth frame: Addr1: ");
    Serial.print(addr1);
    Serial.print(" | Attacker (Addr2): ");
    Serial.print(attacker_mac);
    Serial.print(" | BSSID (Addr3): ");
    Serial.println(addr3);
    */
  }
}

// ===== Attack Detection Functions ===== //
void attack_started() {
  Serial.println("ATTACK DETECTED");
  sendDetection("attack_started");
}

void attack_stopped() {
  Serial.println("ATTACK STOPPED");
  sendDetection("attack_stopped");
}

// ===== Setup ===== //
void setup() {
  Serial.begin(SERIAL_BAUD);
  Serial.println("\nStarting ESP32 Deauth Detector");

  // Connect to WiFi so the ESP32 can send HTTP requests.
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected, IP address: ");
  Serial.println(WiFi.localIP());

  // Set up promiscuous mode on the first channel in the list.
  esp_wifi_set_promiscuous_rx_cb(&sniffer);
  esp_wifi_set_channel(channels[0], WIFI_SECOND_CHAN_NONE);
  esp_wifi_set_promiscuous(true);
  Serial.println("Promiscuous mode enabled.");
}

// ===== Main Loop ===== //
void loop() {
  unsigned long current_time = millis();

  // Update once every (number_of_channels * CH_TIME) milliseconds.
  if (current_time - update_time >= (sizeof(channels) * CH_TIME)) {
    update_time = current_time;
    
    // If packet_rate exceeds threshold, consider it an attack.
    if (packet_rate >= PKT_RATE) {
      attack_counter++;
    } else {
      if (attack_counter >= PKT_TIME) {
        attack_stopped();
      }
      attack_counter = 0;
    }
    
    // If the attack counter confirms an attack, report it.
    if (attack_counter == PKT_TIME) {
      attack_started();
    }
    
    Serial.print("Packets/s: ");
    Serial.println(packet_rate);
    packet_rate = 0;  // Reset the packet counter.
  }

  // Channel hopping: Change channels every CH_TIME milliseconds.
  if (sizeof(channels) > 1 && current_time - ch_time >= CH_TIME) {
    ch_time = current_time;
    ch_index = (ch_index + 1) % (sizeof(channels) / sizeof(channels[0]));
    short ch = channels[ch_index];
    esp_wifi_set_channel(ch, WIFI_SECOND_CHAN_NONE);
    // Uncomment the following lines for channel hopping debug logs:
    // Serial.print("Hopping to channel: ");
    // Serial.println(ch);
  }
}
