// Debugging functions for Bluetooth page issues

// Function to manually test the table update with mock data
function testTableWithMultipleEntries() {
    console.log('Testing table with multiple entries...');
    
    // Clear existing data
    bluetoothData = [];
    threatLevels = { high: 0, medium: 0, low: 0 };
    
    // Add multiple test entries
    const testEntries = [
        {
            id: 'TEST-DEVICE-001',
            deviceName: 'Test Device 1',
            signal: '-45 dBm',
            maxSignal: 65,
            firstSeen: new Date(),
            lastSeen: new Date(),
            threatLevel: 'high',
            channel: 6,
            detectionType: 'bluetooth',
            spectrumData: '|.:-=+*aRW| 65',
            blocked: false,
            isKnownAttacker: true,
            timestamp: new Date().toISOString(),
            apiId: 'test-1'
        },
        {
            id: 'TEST-DEVICE-002',
            deviceName: 'Test Device 2',
            signal: '-60 dBm',
            maxSignal: 85,
            firstSeen: new Date(Date.now() - 30000),
            lastSeen: new Date(),
            threatLevel: 'medium',
            channel: 11,
            detectionType: 'spectrum',
            spectrumData: '|.:-=+*aRW| 85',
            blocked: false,
            isKnownAttacker: false,
            timestamp: new Date(Date.now() - 30000).toISOString(),
            apiId: 'test-2'
        },
        {
            id: 'TEST-DEVICE-003',
            deviceName: 'Test Device 3',
            signal: '-75 dBm',
            maxSignal: 25,
            firstSeen: new Date(Date.now() - 60000),
            lastSeen: new Date(),
            threatLevel: 'low',
            channel: 1,
            detectionType: 'bluetooth',
            spectrumData: '|.:-=+*aRW| 25',
            blocked: false,
            isKnownAttacker: false,
            timestamp: new Date(Date.now() - 60000).toISOString(),
            apiId: 'test-3'
        }
    ];
    
    // Add each test entry
    testEntries.forEach(entry => {
        addBluetoothDataRaw(entry);
        threatLevels[entry.threatLevel]++;
    });
    
    console.log('Added test entries:', bluetoothData.length);
    console.log('Threat levels:', threatLevels);
    
    // Update the table
    updateBluetoothTable();
    updateBluetoothStats();
    
    console.log('Table should now show', bluetoothData.length, 'entries');
}

// Function to check current table state
function debugTableState() {
    console.log('=== Bluetooth Table Debug ===');
    console.log('bluetoothData array length:', bluetoothData.length);
    console.log('bluetoothData contents:', bluetoothData);
    console.log('threatLevels:', threatLevels);
    
    const tableRows = document.querySelectorAll('#bt-table tbody tr');
    console.log('Table rows in DOM:', tableRows.length);
    
    const countElement = document.getElementById('bt-devices-count');
    console.log('Count element value:', countElement ? countElement.textContent : 'not found');
    
    return {
        dataLength: bluetoothData.length,
        tableRows: tableRows.length,
        threatLevels: threatLevels
    };
}

// Function to test API data loading
function testAPIDataLoading() {
    console.log('Testing API data loading...');
    
    fetch('/api/bluetooth_detections?hours=1&limit=10')
        .then(response => response.json())
        .then(data => {
            console.log('API Response:', data);
            if (data.success && data.detections) {
                console.log('Number of detections from API:', data.detections.length);
                data.detections.forEach((detection, index) => {
                    console.log(`Detection ${index + 1}:`, {
                        id: detection.id,
                        device_id: detection.device_id,
                        signal_strength: detection.signal_strength,
                        threat_level: detection.threat_level,
                        timestamp: detection.timestamp
                    });
                });
            }
        })
        .catch(error => {
            console.error('API Error:', error);
        });
}

// Function to clear all data and reload
function resetAndReload() {
    console.log('Resetting and reloading...');
    bluetoothData = [];
    threatLevels = { high: 0, medium: 0, low: 0 };
    updateBluetoothTable();
    updateBluetoothStats();
    loadBluetoothData();
}

// Add these functions to window object for console access
window.debugBluetooth = {
    testTable: testTableWithMultipleEntries,
    debugState: debugTableState,
    testAPI: testAPIDataLoading,
    reset: resetAndReload
};

console.log('Bluetooth debugging functions loaded. Use:');
console.log('- debugBluetooth.testTable() - Add test entries');
console.log('- debugBluetooth.debugState() - Check current state');
console.log('- debugBluetooth.testAPI() - Test API loading');
console.log('- debugBluetooth.reset() - Reset and reload');
