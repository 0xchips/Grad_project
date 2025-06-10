// Simplified Bluetooth monitoring with enhanced debugging
let bluetoothData = [];
let threatLevels = { high: 0, medium: 0, low: 0 };
let btActivityChart, btThreatDistributionChart;

document.addEventListener('DOMContentLoaded', function() {
    console.log('=== Bluetooth.js Loaded ===');
    
    // Initialize immediately
    initBluetoothCharts();
    
    // Force initial data load
    console.log('Starting initial data load...');
    loadBluetoothData();
    
    // Set up intervals
    setInterval(loadBluetoothData, 5000); // Fetch every 5 seconds
    setInterval(updateBluetoothStats, 2000); // Update stats every 2s
    
    console.log('Bluetooth monitoring initialized');
});

function initBluetoothCharts() {
    console.log('Initializing charts...');
    try {
        // Activity Chart
        const activityCtx = document.getElementById('btActivityChart');
        if (activityCtx) {
            btActivityChart = new Chart(activityCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: Array(12).fill('').map((_, i) => `${i}:00`),
                    datasets: [
                        {
                            label: 'Threat Level',
                            data: Array(12).fill(0),
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)',
                            tension: 0.3,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        // Threat Distribution Chart
        const distributionCtx = document.getElementById('btThreatDistributionChart');
        if (distributionCtx) {
            btThreatDistributionChart = new Chart(distributionCtx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['High', 'Medium', 'Low'],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: ['#e74c3c', '#f39c12', '#2ecc71'],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
        console.log('Charts initialized successfully');
    } catch (error) {
        console.error('Error initializing charts:', error);
    }
}

function loadBluetoothData() {
    console.log('=== Loading Data ===');
    
    fetch('/api/bluetooth_detections?hours=1&limit=50')
        .then(response => {
            console.log('API response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('API data received:', data);
            
            if (data.success && data.detections && data.detections.length > 0) {
                console.log(`Processing ${data.detections.length} detections`);
                
                // Clear existing data
                bluetoothData = [];
                threatLevels = { high: 0, medium: 0, low: 0 };
                
                // Process each detection - include all threat levels
                data.detections.forEach((detection, index) => {
                    console.log(`Processing detection ${index + 1}:`, detection);
                    
                    const device = {
                        id: detection.device_id,
                        deviceName: detection.device_name || detection.device_id,
                        signal: `${detection.signal_strength} dBm`,
                        firstSeen: new Date(detection.timestamp),
                        lastSeen: new Date(detection.timestamp),
                        threatLevel: detection.threat_level,
                        channel: detection.channel || 'N/A',
                        blocked: false,
                        isKnownAttacker: detection.threat_level === 'high',
                        timestamp: detection.timestamp,
                        apiId: detection.id
                    };
                    
                    bluetoothData.push(device);
                    threatLevels[device.threatLevel]++;
                });
                
                console.log('Final bluetoothData (all threat levels):', bluetoothData);
                console.log('Threat levels:', threatLevels);
                
                // Force table update
                updateBluetoothTable();
                updateBluetoothStats();
                
            } else {
                console.log('No detections found or API error');
                if (!data.success) {
                    console.error('API error:', data);
                }
            }
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            
            // Add test data for debugging
            console.log('Adding test data due to API error...');
            addTestData();
        });
}

function addTestData() {
    console.log('Adding test threat data to database...');
    
    const testDevices = [
        {
            device_id: 'TEST-DEVICE-' + Date.now() + '-001',
            device_name: 'Simulated Medium Threat Device',
            signal_strength: 105,  // Will be classified as medium threat
            channel: 1,
            rssi_value: 105,
            detection_type: 'spectrum',  // Valid ENUM value
            raw_data: {
                test_device: true,
                threat_type: 'medium',
                simulation_time: new Date().toISOString()
            },
            max_signal: 105,
            spectrum_data: 'simulated_medium_threat'
        },
        {
            device_id: 'TEST-DEVICE-' + Date.now() + '-002',
            device_name: 'Simulated High Threat Device', 
            signal_strength: 160,  // Will be classified as high threat
            channel: 6,
            rssi_value: 160,
            detection_type: 'bluetooth',  // Valid ENUM value
            raw_data: {
                test_device: true,
                threat_type: 'high',
                simulation_time: new Date().toISOString()
            },
            max_signal: 160,
            spectrum_data: 'simulated_high_threat'
        },
        {
            device_id: 'TEST-ATTACKER-' + Date.now() + '-001',
            device_name: 'Simulated BLE Scanner Attack',
            signal_strength: 180,  // Will be classified as high threat
            channel: 11,
            rssi_value: 180,
            detection_type: 'jamming',  // Valid ENUM value for attack simulation
            raw_data: {
                test_device: true,
                threat_type: 'high',
                attack_pattern: 'ble_scanner',
                simulation_time: new Date().toISOString()
            },
            max_signal: 180,
            spectrum_data: 'simulated_attacker'
        }
    ];
    
    let successCount = 0;
    let totalDevices = testDevices.length;
    
    // Send each test device to the API
    testDevices.forEach((device, index) => {
        fetch('/api/bluetooth_detections', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(device)
        })
        .then(response => response.json())
        .then(data => {
            if (data.id) {
                successCount++;
                console.log(`Test device ${index + 1} saved to database:`, data);
                
                // If this is the last device, show success message and reload data
                if (successCount === totalDevices) {
                    showAlert(`✅ Successfully added ${totalDevices} simulated threat devices to database!\n- Devices will persist across page refreshes\n- Data will appear in threat monitoring`, 'success');
                    
                    // Reload data from database to show new threats
                    setTimeout(() => {
                        loadBluetoothData();
                    }, 1000);
                }
            } else {
                console.error('Failed to save test device:', data);
                showAlert('❌ Failed to save some test devices to database', 'error');
            }
        })
        .catch(error => {
            console.error('Error saving test device:', error);
            showAlert('❌ Error saving test devices: ' + error.message, 'error');
        });
    });
}

function updateBluetoothTable() {
    console.log('=== Updating Table ===');
    console.log(`Data to display: ${bluetoothData.length} devices`);
    
    const tableBody = document.querySelector('#bt-table tbody');
    if (!tableBody) {
        console.error('❌ Table body not found! Selector: #bt-table tbody');
        return;
    }
    
    console.log('✅ Table body found');
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    if (bluetoothData.length === 0) {
        console.log('No Bluetooth data to display');
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="6" style="text-align: center; color: #888; padding: 20px;">No Bluetooth devices detected<br><small>All threat levels are displayed</small></td>';
        tableBody.appendChild(row);
        return;
    }
    
    // Add each device as a row
    bluetoothData.forEach((device, index) => {
        console.log(`Adding row ${index + 1} for device:`, device.id);
        
        const row = document.createElement('tr');
        row.style.borderBottom = '1px solid #333';
        
        // Format timestamps
        const firstSeen = new Date(device.firstSeen || device.timestamp);
        const lastSeen = new Date(device.lastSeen || device.timestamp);
        
        row.innerHTML = `
            <td style="padding: 10px; color: white;">${device.deviceName || device.id} ${device.isKnownAttacker ? '⚠️' : ''}</td>
            <td style="padding: 10px; color: white;">${device.signal}</td>
            <td style="padding: 10px; color: white;">${firstSeen.toLocaleDateString()} ${firstSeen.toLocaleTimeString()}</td>
            <td style="padding: 10px; color: white;">${lastSeen.toLocaleDateString()} ${lastSeen.toLocaleTimeString()}</td>
            <td style="padding: 10px;"><span class="threat-level ${device.threatLevel}" style="color: ${getThreatColor(device.threatLevel)}; font-weight: bold;">${device.threatLevel.toUpperCase()}</span></td>
            <td style="padding: 10px;">
                <button class="btn-icon" onclick="analyzeDevice('${device.id}')" style="background: #0066cc; color: white; border: none; padding: 20px 30px; border-radius: 3px; cursor: pointer;">
                    Analyze
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
        console.log(`✅ Row ${index + 1} added successfully`);
    });
    
    console.log(`✅ Table updated with ${bluetoothData.length} rows`);
    
    // Update device count
    const countElement = document.getElementById('bt-devices-count');
    if (countElement) {
        countElement.textContent = bluetoothData.length;
        console.log(`✅ Device count updated: ${bluetoothData.length}`);
    }
}

function getThreatColor(threatLevel) {
    switch(threatLevel) {
        case 'high': return '#ffffff';
        case 'medium': return '#ffffff'; 
        case 'low': return '#ffffff';
        default: return '#888';
    }
}

function updateBluetoothStats() {
    console.log('Updating stats...');
    
    // Update device count
    const countElement = document.getElementById('bt-devices-count');
    if (countElement) {
        countElement.textContent = bluetoothData.length;
    }
    
    // Update threat count
    const threatsElement = document.getElementById('bt-threats-count');
    if (threatsElement) {
        threatsElement.textContent = threatLevels.high || 0;
    }
    
    // Update average signal
    const avgElement = document.getElementById('bt-signal-avg');
    if (avgElement && bluetoothData.length > 0) {
        const avgSignal = bluetoothData
            .map(d => parseInt(d.signal.replace(' dBm', '')))
            .reduce((a, b) => a + b, 0) / bluetoothData.length;
        avgElement.textContent = `${Math.round(avgSignal)} dBm`;
    }
    
    // Update charts
    if (btThreatDistributionChart) {
        btThreatDistributionChart.data.datasets[0].data = [
            threatLevels.high || 0,
            threatLevels.medium || 0, 
            threatLevels.low || 0
        ];
        btThreatDistributionChart.update();
    }
}

function analyzeDevice(deviceId) {
    const device = bluetoothData.find(d => d.id === deviceId);
    if (device) {
        let analysis = `Device Analysis: ${device.deviceName}\n`;
        analysis += `Signal: ${device.signal}\n`;
        analysis += `Threat Level: ${device.threatLevel.toUpperCase()}\n`;
        analysis += `Channel: ${device.channel}\n`;
        analysis += `First Seen: ${device.firstSeen.toLocaleString()}\n`;
        analysis += `Last Seen: ${device.lastSeen.toLocaleString()}\n`;
        
        if (device.isKnownAttacker) {
            analysis += '\n⚠️ WARNING: High threat device detected!';
        }
        
        alert(analysis);
    }
}

// Clear all Bluetooth detection data from database
function clearAllDetections() {
    if (confirm('Are you sure you want to clear all Bluetooth detection data from the database?')) {
        fetch('/api/bluetooth_detections/clear', { 
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Clear local data
                bluetoothData = [];
                threatLevels = { high: 0, medium: 0, low: 0 };
                
                // Update display
                updateBluetoothTable();
                updateBluetoothStats();
                
                showAlert('✅ All Bluetooth detection data cleared successfully!', 'success');
                console.log('Database cleared successfully');
            } else {
                showAlert('❌ Failed to clear detection data: ' + (data.error || 'Unknown error'), 'error');
                console.error('Failed to clear data:', data);
            }
        })
        .catch(error => {
            console.error('Error clearing detections:', error);
            showAlert('❌ Error clearing detection data: ' + error.message, 'error');
        });
    }
}

// Generate PDF report (placeholder - can be enhanced)
function generatePdfReport() {
    showAlert('📄 PDF Report generation functionality\nwould be implemented here.\n\nCurrent data:\n' + 
              `- Devices: ${bluetoothData.length}\n` +
              `- High threats: ${threatLevels.high}\n` +
              `- Medium threats: ${threatLevels.medium}`, 'info');
}

// Show alert messages to user
function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        padding: 15px 20px;
        border-radius: 5px;
        max-width: 400px;
        white-space: pre-line;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        font-family: Arial, sans-serif;
    `;
    
    // Set colors based on type
    const colors = {
        success: { bg: '#d4edda', border: '#c3e6cb', text: '#155724' },
        warning: { bg: '#fff3cd', border: '#ffeaa7', text: '#856404' },
        error: { bg: '#f8d7da', border: '#f5c6cb', text: '#721c24' },
        info: { bg: '#d1ecf1', border: '#bee5eb', text: '#0c5460' }
    };
    
    const color = colors[type] || colors.info;
    alertDiv.style.backgroundColor = color.bg;
    alertDiv.style.borderLeft = `4px solid ${color.border}`;
    alertDiv.style.color = color.text;
    
    alertDiv.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; font-size: 20px; cursor: pointer; color: ${color.text}; margin-left: 10px;">&times;</button>
        </div>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
    
    // Also log to console
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Export functions for global access
window.analyzeDevice = analyzeDevice;
window.loadBluetoothData = loadBluetoothData;
window.addTestData = addTestData;
window.clearAllDetections = clearAllDetections;
window.generatePdfReport = generatePdfReport;

console.log('Bluetooth.js loaded and ready');
