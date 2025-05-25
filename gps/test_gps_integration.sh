#!/bin/bash
# Run GPS testing tools

echo "===== Testing GPS Integration with MySQL ====="
echo ""
echo "1. Running update_gps_table.py..."
python3 update_gps_table.py
echo ""

echo "2. Adding test data with GPS simulator..."
python3 gps_simulator.py --count 10 --interval 0.5 --jamming 0.3
echo ""

echo "3. Checking data in MySQL..."
mysql -u dashboard -psecurepass security_dashboard -e "SELECT id, latitude, longitude, device_id, satellites, hdop, jamming_detected FROM gps_data ORDER BY timestamp DESC LIMIT 10;"
echo ""

echo "4. Testing API endpoint..."
curl -s "http://localhost:80/api/gps?hours=1" | python3 -m json.tool | head -30
echo ""

echo "===== Test Complete ====="
echo ""
echo "Open the GPS dashboard page to view the data"
echo ""
