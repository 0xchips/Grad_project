# BSSID to SSID Mapping Enhancement

## Summary
Enhanced the Kismet device API endpoint to provide BSSID to SSID mapping, allowing clients to see which wireless network (SSID) each device is connected to.

## Changes Made

### Enhanced `/api/kismet/devices` endpoint:

1. **Two-pass processing**:
   - **First pass**: Collect all Access Point devices and create a mapping dictionary `bssid_to_ssid`
   - **Second pass**: Process all devices and use the mapping to provide SSID names

2. **New fields in device data**:
   - `connected_ap`: The BSSID of the connected Access Point (existing)
   - `connected_ssid`: The SSID name of the connected Access Point (NEW)

3. **Enhanced response includes**:
   - `bssid_mappings`: Dictionary mapping all discovered BSSIDs to their SSID names

## Example Output

### Before Enhancement:
```json
{
  "mac": "3E:81:1D:2E:13:A7",
  "type": "Wi-Fi Client", 
  "connected_ap": "DC:8D:8A:B9:13:36"
}
```

### After Enhancement:
```json
{
  "mac": "3E:81:1D:2E:13:A7",
  "type": "Wi-Fi Client",
  "connected_ap": "DC:8D:8A:B9:13:36",
  "connected_ssid": "PotatoChips-2323@2.4GH"
}
```

### Additional Response Data:
```json
{
  "success": true,
  "devices": [...],
  "count": 25,
  "bssid_mappings": {
    "DC:8D:8A:B9:13:36": "PotatoChips-2323@2.4GH",
    "AA:BB:CC:DD:EE:FF": "SomeOtherNetwork",
    ...
  }
}
```

## SSID Extraction Strategy

The code attempts to extract SSID names from multiple locations in the Kismet data structure:

1. **Primary**: `dot11.device.advertised_ssid_map` - SSIDs being broadcast by APs
2. **Fallback**: `dot11.device.responded_ssid_map` - SSIDs that responded to probes

This ensures maximum compatibility with different types of wireless networks and configurations.

## Usage

When Kismet is running and detecting devices, the enhanced endpoint will now provide:
- Clear mapping between client devices and the networks they're connected to
- SSID names instead of just MAC addresses for better readability
- A complete mapping dictionary for frontend applications to use

## Testing

Use the provided test script:
```bash
python3 test_bssid_mapping.py
```

This will show:
- All BSSID to SSID mappings discovered
- Sample devices with their connection information
- Specific client-to-AP associations with SSID names
