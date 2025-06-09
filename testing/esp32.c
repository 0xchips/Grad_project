#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_wifi.h"

// ===== SETTINGS ===== //
#define SERIAL_BAUD 115200  // Baudrate for serial communication
#define CH_TIME 140         // Scan time (in ms) per channel
#define PKT_RATE 5          // Minimum packets required to recognize an attack
#define PKT_TIME 1          // Minimum update intervals before confirming an attack
#define MAX_QUEUED_EVENTS 50  // Maximum number of events to queue when offline

// Channels to scan (adjust based on your region)
const short channels[] = { 1, 6, 11 };

// ===== Flask API SETTINGS ===== //
const char* ssid = "PotatoChips-2323@2.4GH";
const char* password = "F@ri$2OO3";
const char* flask_server = "192.168.1.43";  // Replace with your Flask server IP
const int flask_port = 5053;                // Flask server port (default 5000)
const char* flask_endpoint = "/api/deauth_logs";  // API endpoint on your Flask dashboard

// ===== Runtime variables ===== //
int ch_index = 0;               // Current channel index
volatile int packet_rate = 0;   // Deauth packet counter (resets each update)
int attack_counter = 0;         // Counter for consecutive attack intervals
unsigned long update_time = 0;  // Timestamp for last update interval
unsigned long ch_time = 0;      // Timestamp for last channel hop

// Global variables to store detection information
char attacker_mac[18] = "00:00:00:00:00:00";
char target_bssid[18] = "00:00:00:00:00:00";
String attacker_ssid = "";
String target_ssid = "";

// Global variables to store last deauth info for queuing
int last_channel = 0;
int last_rssi = 0;
bool last_spoofed = false;

// Structure to store AP information
struct APInfo {
  char bssid[18];
  String ssid;
  int channel;
  long rssi;
  unsigned long last_seen;
};

// Array to store discovered APs
APInfo discovered_aps[50];
int ap_count = 0;

// ===== Deauth Event Queue Structure ===== //
struct DeauthEvent {
  String event_type;
  char attacker_mac[18];
  String attacker_ssid;
  char target_bssid[18];
  String target_ssid;
  unsigned long timestamp;
  int channel;
  int rssi;
  bool is_spoofed;
};

// Queue for storing events when WiFi is down
DeauthEvent event_queue[MAX_QUEUED_EVENTS];
int queue_head = 0;
int queue_tail = 0;
int queue_count = 0;

// WiFi reconnection variables
unsigned long last_wifi_check = 0;
unsigned long wifi_check_interval = 5000; // Check WiFi every 5 seconds
bool wifi_was_connected = false;

// ===== Helper Functions ===== //
// Convert MAC address bytes to string format
void macToString(uint8_t* mac, char* str) {
  sprintf(str, "%02X:%02X:%02X:%02X:%02X:%02X",
          mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

// Find SSID by BSSID in discovered APs
String findSSIDByBSSID(const char* bssid) {
  for (int i = 0; i < ap_count; i++) {
    if (strcmp(discovered_aps[i].bssid, bssid) == 0) {
      return discovered_aps[i].ssid;
    }
  }
  return "Unknown";
}

// Add or update AP in the discovered list
void updateAPList(const char* bssid, const String& ssid, int channel, long rssi) {
  // Check if AP already exists
  for (int i = 0; i < ap_count; i++) {
    if (strcmp(discovered_aps[i].bssid, bssid) == 0) {
      discovered_aps[i].ssid = ssid;
      discovered_aps[i].channel = channel;
      discovered_aps[i].rssi = rssi;
      discovered_aps[i].last_seen = millis();
      return;
    }
  }
  
  // Add new AP if space available
  if (ap_count < 50) {
    strcpy(discovered_aps[ap_count].bssid, bssid);
    discovered_aps[ap_count].ssid = ssid;
    discovered_aps[ap_count].channel = channel;
    discovered_aps[ap_count].rssi = rssi;
    discovered_aps[ap_count].last_seen = millis();
    ap_count++;
  }
}

// Scan for nearby APs to build SSID database
void scanForAPs() {
  Serial.println("Scanning for nearby APs...");
  WiFi.scanDelete();
  int n = WiFi.scanNetworks();
  
  for (int i = 0; i < n && i < 50; i++) {
    char bssid_str[18];
    uint8_t* bssid = WiFi.BSSID(i);
    macToString(bssid, bssid_str);
    updateAPList(bssid_str, WiFi.SSID(i), WiFi.channel(i), WiFi.RSSI(i));
  }
  
  Serial.print("Found ");
  Serial.print(ap_count);
  Serial.println(" access points");
}

// ===== Send Detection Event to Flask Dashboard ===== //
void sendDetection(const String &eventType, bool spoofed = false, int channel = 0, int rssi = 0) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String url = String("http://") + flask_server + ":" + flask_port + flask_endpoint;
    WiFiClient client;
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");
    
    // Build a comprehensive JSON payload
    String jsonData = "{";
    jsonData += "\"event\":\"" + eventType + "\",";
    jsonData += "\"alert_type\":\"Deauth Attack\",";
    jsonData += "\"attacker_bssid\":\"" + String(attacker_mac) + "\",";
    jsonData += "\"attacker_ssid\":\"" + attacker_ssid + "\",";
    jsonData += "\"destination_bssid\":\"" + String(target_bssid) + "\",";
    jsonData += "\"destination_ssid\":\"" + target_ssid + "\",";
    jsonData += "\"timestamp\":" + String(millis()) + ",";
    jsonData += "\"channel\":" + String(channel) + ",";
    jsonData += "\"rssi\":" + String(rssi) + ",";
    jsonData += "\"is_spoofed\":" + String(spoofed ? "true" : "false") + ",";
    jsonData += "\"attack_count\":1";
    jsonData += "}";
    
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
      
      // Queue the event for later if send failed
      queueDeauthEvent(eventType, spoofed, channel, rssi);
    }
    http.end();
  } else {
    Serial.println("WiFi not connected, queueing event for later...");
    queueDeauthEvent(eventType, spoofed, channel, rssi);
  }
}

// ===== Queue Management Functions ===== //
void queueDeauthEvent(const String &eventType, bool spoofed, int channel, int rssi) {
  if (queue_count >= MAX_QUEUED_EVENTS) {
    Serial.println("Event queue full, dropping oldest event");
    queue_tail = (queue_tail + 1) % MAX_QUEUED_EVENTS;
    queue_count--;
  }
  
  DeauthEvent &event = event_queue[queue_head];
  event.event_type = eventType;
  strcpy(event.attacker_mac, attacker_mac);
  event.attacker_ssid = attacker_ssid;
  strcpy(event.target_bssid, target_bssid);
  event.target_ssid = target_ssid;
  event.timestamp = millis();
  event.channel = channel;
  event.rssi = rssi;
  event.is_spoofed = spoofed;
  
  queue_head = (queue_head + 1) % MAX_QUEUED_EVENTS;
  queue_count++;
  
  Serial.print("Queued event: ");
  Serial.print(eventType);
  Serial.print(" (Queue size: ");
  Serial.print(queue_count);
  Serial.println(")");
}

void sendQueuedEvents() {
  if (queue_count == 0) return;
  
  Serial.print("Sending ");
  Serial.print(queue_count);
  Serial.println(" queued events...");
  
  while (queue_count > 0) {
    DeauthEvent &event = event_queue[queue_tail];
    
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      String url = String("http://") + flask_server + ":" + flask_port + flask_endpoint;
      WiFiClient client;
      http.begin(client, url);
      http.addHeader("Content-Type", "application/json");
      
      // Build JSON payload for queued event
      String jsonData = "{";
      jsonData += "\"event\":\"" + event.event_type + "\",";
      jsonData += "\"alert_type\":\"Deauth Attack\",";
      jsonData += "\"attacker_bssid\":\"" + String(event.attacker_mac) + "\",";
      jsonData += "\"attacker_ssid\":\"" + event.attacker_ssid + "\",";
      jsonData += "\"destination_bssid\":\"" + String(event.target_bssid) + "\",";
      jsonData += "\"destination_ssid\":\"" + event.target_ssid + "\",";
      jsonData += "\"timestamp\":" + String(event.timestamp) + ",";
      jsonData += "\"channel\":" + String(event.channel) + ",";
      jsonData += "\"rssi\":" + String(event.rssi) + ",";
      jsonData += "\"is_spoofed\":" + String(event.is_spoofed ? "true" : "false") + ",";
      jsonData += "\"attack_count\":1";
      jsonData += "}";
      
      int httpCode = http.POST(jsonData);
      if (httpCode > 0) {
        Serial.print("Sent queued ");
        Serial.print(event.event_type);
        Serial.print(" - Response code: ");
        Serial.println(httpCode);
      } else {
        Serial.print("Failed to send queued event. Error: ");
        Serial.println(http.errorToString(httpCode));
        http.end();
        break; // Stop sending if there's an error
      }
      http.end();
      
      // Remove event from queue
      queue_tail = (queue_tail + 1) % MAX_QUEUED_EVENTS;
      queue_count--;
      
      delay(100); // Small delay between requests
    } else {
      Serial.println("WiFi disconnected while sending queued events");
      break;
    }
  }
  
  if (queue_count == 0) {
    Serial.println("All queued events sent successfully");
  }
}

// ===== WiFi Management Functions ===== //
void checkAndReconnectWiFi() {
  if (WiFi.status() != WL_CONNECTED) {
    if (wifi_was_connected) {
      Serial.println("WiFi connection lost, attempting to reconnect...");
      wifi_was_connected = false;
    }
    
    WiFi.begin(ssid, password);
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 10) {
      delay(500);
      Serial.print(".");
      attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println();
      Serial.print("WiFi reconnected, IP: ");
      Serial.println(WiFi.localIP());
      wifi_was_connected = true;
      
      // Send any queued events
      sendQueuedEvents();
    }
  } else {
    if (!wifi_was_connected) {
      wifi_was_connected = true;
      // Send any queued events when WiFi comes back
      sendQueuedEvents();
    }
  }
}

// ===== Sniffer Callback for ESP32 ===== //
void sniffer(void *buf, wifi_promiscuous_pkt_type_t type) {
  wifi_promiscuous_pkt_t *pkt = (wifi_promiscuous_pkt_t *)buf;
  
  // Ensure the packet is long enough (at least 24 bytes for the MAC header)
  if (pkt->rx_ctrl.sig_len < 24) return;
  uint8_t *packet = pkt->payload;
  
  // Parse beacon frames to discover SSIDs
  if (packet[0] == 0x80) { // Beacon frame
    // Extract BSSID (Address 3 in beacon frames)
    char bssid_str[18];
    macToString(&packet[16], bssid_str);
    
    // Extract SSID from beacon frame
    int ssid_len = packet[37]; // SSID length is at offset 37
    if (ssid_len > 0 && ssid_len <= 32 && (37 + ssid_len) < pkt->rx_ctrl.sig_len) {
      String ssid_str = "";
      for (int i = 0; i < ssid_len; i++) {
        ssid_str += (char)packet[38 + i];
      }
      updateAPList(bssid_str, ssid_str, pkt->rx_ctrl.channel, pkt->rx_ctrl.rssi);
    }
    return;
  }
  
  // Check for deauthentication (0xC0) or disassociation (0xA0) frames
  if (packet[0] == 0xC0 || packet[0] == 0xA0) {
    packet_rate++;
    
    // Extract MAC addresses from deauth frame
    // Address 1 (Receiver/Target): bytes 4-9
    // Address 2 (Transmitter): bytes 10-15  
    // Address 3 (BSSID): bytes 16-21
    
    char receiver_mac[18], transmitter_mac[18], bssid_mac[18];
    macToString(&packet[4], receiver_mac);
    macToString(&packet[10], transmitter_mac);
    macToString(&packet[16], bssid_mac);
    
    // Check if receiver is broadcast (FF:FF:FF:FF:FF:FF) indicating mass deauth
    bool is_broadcast = (strcmp(receiver_mac, "FF:FF:FF:FF:FF:FF") == 0);
    
    // Determine if this is a legitimate deauth from AP or a spoofed attack
    bool is_spoofed = (strcmp(transmitter_mac, bssid_mac) != 0);
    
    // Enhanced attack detection logic
    bool likely_attack = false;
    
    if (is_spoofed) {
      // Transmitter is different from BSSID - definitely spoofed
      likely_attack = true;
      strcpy(attacker_mac, transmitter_mac);
      strcpy(target_bssid, bssid_mac);
      attacker_ssid = findSSIDByBSSID(attacker_mac);
      target_ssid = findSSIDByBSSID(target_bssid);
    } else if (is_broadcast) {
      // Broadcast deauth from AP - could be an attack using AP's MAC
      // Check if this AP is in our database and has unusual behavior
      likely_attack = true;
      strcpy(attacker_mac, transmitter_mac);
      strcpy(target_bssid, bssid_mac);
      attacker_ssid = "SPOOFED_" + findSSIDByBSSID(attacker_mac);
      target_ssid = findSSIDByBSSID(target_bssid);
    } else {
      // Single client deauth from AP - less likely to be attack but monitor
      // Only flag as attack if rate is very high
      if (packet_rate > PKT_RATE * 2) {
        likely_attack = true;
        strcpy(attacker_mac, transmitter_mac);
        strcpy(target_bssid, bssid_mac);
        attacker_ssid = findSSIDByBSSID(attacker_mac);
        target_ssid = findSSIDByBSSID(target_bssid);
      }
    }
    
    // Print detailed deauth information
    Serial.println("=== DEAUTH FRAME DETECTED ===");
    Serial.print("Frame Type: ");
    Serial.println(packet[0] == 0xC0 ? "Deauthentication" : "Disassociation");
    Serial.print("Receiver (Target): ");
    Serial.print(receiver_mac);
    Serial.print(is_broadcast ? " (BROADCAST)" : " (UNICAST)");
    Serial.println();
    Serial.print("Transmitter: ");
    Serial.print(transmitter_mac);
    Serial.print(" (");
    Serial.print(findSSIDByBSSID(transmitter_mac));
    Serial.println(")");
    Serial.print("BSSID: ");
    Serial.print(bssid_mac);
    Serial.print(" (");
    Serial.print(findSSIDByBSSID(bssid_mac));
    Serial.println(")");
    Serial.print("Spoofed: ");
    Serial.println(is_spoofed ? "YES" : "NO");
    Serial.print("Likely Attack: ");
    Serial.println(likely_attack ? "YES" : "NO");
    Serial.print("Channel: ");
    Serial.println(pkt->rx_ctrl.channel);
    Serial.print("RSSI: ");
    Serial.println(pkt->rx_ctrl.rssi);
    Serial.println("=============================");
    
    // Only count packets that are likely attacks
    if (likely_attack) {
      last_channel = pkt->rx_ctrl.channel;
      last_rssi = pkt->rx_ctrl.rssi;
      last_spoofed = is_spoofed;
    } else {
      // Reduce packet_rate for legitimate deauths
      if (packet_rate > 0) packet_rate--;
    }
  }
}

// ===== Attack Detection Functions ===== //
void attack_started() {
  Serial.println("\n!!! DEAUTH ATTACK DETECTED !!!");
  Serial.print("Attack Type: ");
  Serial.println(last_spoofed ? "SPOOFED MAC" : "BROADCAST DEAUTH");
  Serial.print("Attacker: ");
  Serial.print(attacker_mac);
  if (attacker_ssid != "Unknown" && attacker_ssid != "") {
    Serial.print(" (");
    Serial.print(attacker_ssid);
    Serial.print(")");
  }
  Serial.println();
  Serial.print("Target Network: ");
  Serial.print(target_bssid);
  if (target_ssid != "Unknown" && target_ssid != "") {
    Serial.print(" (");
    Serial.print(target_ssid);
    Serial.print(")");
  }
  Serial.println();
  Serial.print("Channel: ");
  Serial.print(last_channel);
  Serial.print(" | RSSI: ");
  Serial.println(last_rssi);
  Serial.println("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
  
  sendDetection("attack_started", last_spoofed, last_channel, last_rssi);
}

void attack_stopped() {
  Serial.println("ATTACK STOPPED");
  sendDetection("attack_stopped", last_spoofed, last_channel, last_rssi);
}

// ===== Setup ===== //
void setup() {
  Serial.begin(SERIAL_BAUD);
  Serial.println("\nStarting Enhanced ESP32 Deauth Detector with Offline Queuing");

  // Connect to WiFi
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
  wifi_was_connected = true;

  // Initial AP scan to build SSID database
  scanForAPs();
  
  // Set up promiscuous mode
  esp_wifi_set_promiscuous_rx_cb(&sniffer);
  esp_wifi_set_channel(channels[0], WIFI_SECOND_CHAN_NONE);
  esp_wifi_set_promiscuous(true);
  Serial.println("Promiscuous mode enabled.");
  Serial.println("Monitoring for deauth attacks...\n");
}

// ===== Main Loop ===== //
void loop() {
  unsigned long current_time = millis();
  
  // Check WiFi connection and reconnect if needed
  if (current_time - last_wifi_check >= wifi_check_interval) {
    last_wifi_check = current_time;
    checkAndReconnectWiFi();
  }

  // Periodic AP scan every 30 seconds to update SSID database
  static unsigned long last_scan = 0;
  if (current_time - last_scan >= 30000) {
    Serial.println("Refreshing AP database...");
    esp_wifi_set_promiscuous(false);
    scanForAPs();
    esp_wifi_set_promiscuous(true);
    last_scan = current_time;
  }

  // Update once every (number_of_channels * CH_TIME) milliseconds
  if (current_time - update_time >= (sizeof(channels) * CH_TIME)) {
    update_time = current_time;
    
    // If packet_rate exceeds threshold, consider it an attack
    if (packet_rate >= PKT_RATE) {
      attack_counter++;
    } else {
      if (attack_counter >= PKT_TIME) {
        attack_stopped();
      }
      attack_counter = 0;
    }
    
    // If the attack counter confirms an attack, report it
    if (attack_counter == PKT_TIME) {
      attack_started();
    }
    
    Serial.print("Deauth packets/s: ");
    Serial.print(packet_rate);
    Serial.print(" | APs discovered: ");
    Serial.print(ap_count);
    Serial.print(" | Queue size: ");
    Serial.println(queue_count);
    packet_rate = 0;  // Reset the packet counter
  }

  // Channel hopping
  if (sizeof(channels) > 1 && current_time - ch_time >= CH_TIME) {
    ch_time = current_time;
    ch_index = (ch_index + 1) % (sizeof(channels) / sizeof(channels[0]));
    short ch = channels[ch_index];
    esp_wifi_set_channel(ch, WIFI_SECOND_CHAN_NONE);
  }
}