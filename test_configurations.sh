#!/bin/bash

# Test script for WiGuard Configurations functionality
echo "Testing WiGuard Configurations Page..."

BASE_URL="http://127.0.0.1:5053"

# Test 1: Check if configurations page loads
echo "1. Testing configurations page access..."
response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/configurations.html")
if [ "$response" = "200" ]; then
    echo "   ✓ Configurations page loads successfully"
else
    echo "   ✗ Configurations page failed to load (HTTP $response)"
    exit 1
fi

# Test 2: Test wireless adapter scanning API
echo "2. Testing wireless adapter scanning API..."
response=$(curl -s "$BASE_URL/api/wireless-adapters")
if echo "$response" | grep -q '"success": true'; then
    adapter_count=$(echo "$response" | grep -o '"count": [0-9]*' | grep -o '[0-9]*')
    echo "   ✓ Wireless adapter scanning successful (found $adapter_count adapter(s))"
else
    echo "   ✗ Wireless adapter scanning failed"
    echo "   Response: $response"
    exit 1
fi

# Test 3: Test configuration retrieval API
echo "3. Testing configuration retrieval API..."
response=$(curl -s "$BASE_URL/api/configurations")
if echo "$response" | grep -q '"success": true'; then
    echo "   ✓ Configuration retrieval successful"
else
    echo "   ✗ Configuration retrieval failed"
    echo "   Response: $response"
fi

# Test 4: Test configuration saving API
echo "4. Testing configuration saving API..."
test_config='{"realtime_monitoring": "wlan0mon", "network_devices": "wlan0mon", "kismet_monitoring": "wlan0mon"}'
response=$(curl -s -X POST "$BASE_URL/api/configurations" \
    -H "Content-Type: application/json" \
    -d "$test_config")

if echo "$response" | grep -q '"success": true'; then
    echo "   ✓ Configuration saving successful"
else
    echo "   ✗ Configuration saving failed"
    echo "   Response: $response"
    exit 1
fi

# Test 5: Verify configuration was saved
echo "5. Verifying saved configuration..."
response=$(curl -s "$BASE_URL/api/configurations")
if echo "$response" | grep -q '"realtime_monitoring": "wlan0mon"'; then
    echo "   ✓ Configuration saved and retrieved correctly"
else
    echo "   ✗ Configuration verification failed"
    echo "   Response: $response"
    exit 1
fi

echo ""
echo "🎉 All tests passed! WiGuard Configurations functionality is working correctly."
echo ""
echo "You can now:"
echo "  • Access the configurations page at: $BASE_URL/configurations.html"
echo "  • Scan for wireless adapters"
echo "  • Assign adapters to different monitoring functions"
echo "  • Save and load configuration settings"
echo ""
echo "The Configurations page has been successfully integrated into the WiGuard Dashboard!"
