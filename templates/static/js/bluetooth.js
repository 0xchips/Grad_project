// Bluetooth Threat Monitoring System
let bluetoothData = [];
let threatLevels = { high: 0, medium: 0, low: 0 };
let blockedDevices = [];
let btActivityChart, btThreatDistributionChart;
let knownAttackers = ['BLE-Sniffer', 'BT-Kracker', 'BlueBorne', 'KNOB-Attack'];

document.addEventListener('DOMContentLoaded', function() {
    console.log('=== DOM Content Loaded ===');
    
    // Check if table exists
    const table = document.getElementById('bt-table');
    const tableBody = document.querySelector('#bt-table tbody');
    console.log('Table found:', !!table);
    console.log('Table body found:', !!tableBody);
    
    // Add a test row immediately to verify table rendering
    if (tableBody) {
        console.log('Adding test row...');
        const testRow = document.createElement('tr');
        testRow.innerHTML = `
            <td>TEST-DEVICE</td>
            <td>-50 dBm</td>
            <td>2025-06-09 15:53:00</td>
            <td>2025-06-09 15:53:00</td>
            <td><span class="threat-level medium">MEDIUM</span></td>
            <td><button class="btn-icon"><i class="fas fa-ban"></i></button></td>
        `;
        testRow.style.backgroundColor = '#ff0000'; // Red background for visibility
        tableBody.appendChild(testRow);
        console.log('Test row added');
    }
    
    initBluetoothCharts();
    loadBluetoothData();
    setInterval(loadBluetoothData, 5000); // Fetch real data every 5 seconds
    setInterval(updateBluetoothStats, 2000); // Update stats every 2s
});

function initBluetoothCharts() {
    // Activity Chart
    const activityCtx = document.getElementById('btActivityChart').getContext('2d');
    btActivityChart = new Chart(activityCtx, {
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
                },
                {
                    label: 'Signal Strength',
                    data: Array(12).fill(0),
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.3,
                    fill: true,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Threat Level'
                    }
                },
                y1: {
                    position: 'right',
                    beginAtZero: false,
                    grid: {
                        drawOnChartArea: false
                    },
                    title: {
                        display: true,
                        text: 'Signal Strength (dBm)'
                    }
                }
            }
        }
    });

    // Threat Distribution Chart
    const distributionCtx = document.getElementById('btThreatDistributionChart').getContext('2d');
    btThreatDistributionChart = new Chart(distributionCtx, {
        type: 'doughnut',
        data: {
            labels: ['High', 'Medium', 'Low'],
            datasets: [{
                data: Object.values(threatLevels),
                backgroundColor: [
                    '#e74c3c',
                    '#f39c12',
                    '#2ecc71'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function loadBluetoothData() {
    console.log('=== Loading Bluetooth Data ===');
    // Fetch real data from the API
    fetch('/api/bluetooth_detections?hours=1&limit=50')
        .then(response => response.json())
        .then(data => {
            console.log('Raw API response:', data);
            if (data.success && data.detections) {
                console.log(`API returned ${data.detections.length} detections`);
                
                // Create a map of existing detections by their API ID
                const existingDetections = new Map();
                bluetoothData.forEach(device => {
                    if (device.apiId) {
                        existingDetections.set(device.apiId, device);
                    }
                });
                
                let newDetections = 0;
                let updatedDetections = 0;
                
                // Process each detection from the API
                data.detections.forEach(detection => {
                    console.log('Processing detection:', detection);
                    const device = {
                        id: detection.device_id,
                        deviceName: detection.device_name || detection.device_id,
                        signal: `${detection.signal_strength} dBm`,
                        maxSignal: detection.max_signal || detection.signal_strength,
                        firstSeen: new Date(detection.timestamp),
                        lastSeen: new Date(detection.timestamp),
                        threatLevel: detection.threat_level,
                        channel: detection.channel,
                        detectionType: detection.detection_type,
                        spectrumData: detection.spectrum_data,
                        blocked: false,
                        isKnownAttacker: detection.threat_level === 'high',
                        timestamp: detection.timestamp,
                        apiId: detection.id // Store the API ID to track unique detections
                    };
                    console.log('Created device object:', device);
                    
                    if (existingDetections.has(device.apiId)) {
                        // Update existing detection
                        const existingIndex = bluetoothData.findIndex(d => d.apiId === device.apiId);
                        if (existingIndex !== -1) {
                            bluetoothData[existingIndex] = { ...bluetoothData[existingIndex], ...device };
                            updatedDetections++;
                        }
                    } else {
                        // New detection - add it
                        addBluetoothDataRaw(device);
                        newDetections++;
                    }
                });
                
                console.log(`Current bluetoothData length: ${bluetoothData.length}`);
                console.log('Sample bluetoothData entries:', bluetoothData.slice(0, 3));
                
                // Remove old entries (older than 1 hour)
                const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
                const initialCount = bluetoothData.length;
                bluetoothData = bluetoothData.filter(device => 
                    new Date(device.timestamp || device.lastSeen) > oneHourAgo
                );
                const removedCount = initialCount - bluetoothData.length;
                
                // Recalculate threat levels
                threatLevels = { high: 0, medium: 0, low: 0 };
                bluetoothData.forEach(device => {
                    threatLevels[device.threatLevel]++;
                });
                
                // Update UI
                updateBluetoothTable();
                updateBluetoothStats();
                
                // Log detailed information for debugging
                console.log(`Bluetooth data update: ${newDetections} new, ${updatedDetections} updated, ${removedCount} removed, ${bluetoothData.length} total`);
                  if (newDetections > 0 || updatedDetections > 0) {
                    console.log('Current bluetooth data:', bluetoothData.map(d => ({
                        id: d.id,
                        apiId: d.apiId,
                        signal: d.signal,
                        threatLevel: d.threatLevel,
                        timestamp: d.timestamp
                    })));
                }
            }
        })
        .catch(error => {
            console.error('Error fetching Bluetooth data:', error);
            // Fallback to simulated data if API fails
            setTimeout(() => {
                for (let i = 0; i < 5; i++) {
                    addBluetoothData(generateBluetoothDevice());
                }
                updateBluetoothStats();
            }, 1000);
        });
}

function generateBluetoothDevice() {
    // 10% chance of known attacker
    const isKnownAttacker = Math.random() < 0.1;
    let deviceName = isKnownAttacker 
        ? knownAttackers[Math.floor(Math.random() * knownAttackers.length)]
        : `DEV-${Math.random().toString(36).substr(2, 6).toUpperCase()}`;
    
    // Determine threat level based on characteristics
    let threatLevel = 'low';
    const signalStrength = Math.floor(Math.random() * 60) - 80;
    
    if (isKnownAttacker) {
        threatLevel = 'high';
    } else if (signalStrength > -50) { // Strong signal nearby
        threatLevel = Math.random() > 0.7 ? 'medium' : 'low';
    }
    
    return {
        id: deviceName,
        signal: `${signalStrength} dBm`,
        firstSeen: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000),
        lastSeen: new Date(),
        threatLevel: threatLevel,
        blocked: false,
        isKnownAttacker: isKnownAttacker
    };
}

function addBluetoothData(device) {
    // Check if device already exists
    const existingDeviceIndex = bluetoothData.findIndex(d => d.id === device.id);
    
    if (existingDeviceIndex >= 0) {
        // Update existing device
        bluetoothData[existingDeviceIndex].lastSeen = new Date();
        bluetoothData[existingDeviceIndex].signal = device.signal;
        bluetoothData[existingDeviceIndex].threatLevel = device.threatLevel;
    } else {
        // Add new device
        bluetoothData.unshift(device);
        threatLevels[device.threatLevel]++;
    }
    
    // Update UI
    updateBluetoothTable();
    updateBluetoothCharts(device);
    updateBluetoothStats();
}

function addBluetoothDataRaw(device) {
    // Add device without triggering UI updates (used for bulk loading)
    const existingDeviceIndex = bluetoothData.findIndex(d => d.id === device.id);
    
    if (existingDeviceIndex >= 0) {
        // Update existing device
        bluetoothData[existingDeviceIndex].lastSeen = new Date(device.lastSeen || device.timestamp);
        bluetoothData[existingDeviceIndex].signal = device.signal;
        bluetoothData[existingDeviceIndex].threatLevel = device.threatLevel;
        bluetoothData[existingDeviceIndex].timestamp = device.timestamp;
    } else {
        // Add new device
        bluetoothData.unshift(device);
    }
}

function updateBluetoothTable() {
    console.log('=== Updating Bluetooth Table ===');
    console.log(`bluetoothData length: ${bluetoothData.length}`);
    console.log('bluetoothData sample:', bluetoothData.slice(0, 2));
    
    const tableBody = document.querySelector('#bt-table tbody');
    if (!tableBody) {
        console.error('Table body not found!');
        return;
    }
    
    tableBody.innerHTML = '';
    
    if (bluetoothData.length === 0) {
        console.log('No bluetooth data to display');
        return;
    }
    
    // Sort by last seen (newest first) and then by threat level (high to low)
    const sortedData = [...bluetoothData].sort((a, b) => {
        // First sort by timestamp/lastSeen (newest first)
        const aTime = new Date(a.timestamp || a.lastSeen).getTime();
        const bTime = new Date(b.timestamp || b.lastSeen).getTime();
        
        if (Math.abs(bTime - aTime) > 5000) { // If more than 5 seconds difference
            return bTime - aTime; // Show newest first
        }
        
        // If timestamps are close, sort by threat level
        const threatOrder = { 'high': 3, 'medium': 2, 'low': 1 };
        return (threatOrder[b.threatLevel] || 0) - (threatOrder[a.threatLevel] || 0);
    });
    
    // Add rows (limit to 100 for performance)
    sortedData.slice(0, 100).forEach(device => {
        const row = document.createElement('tr');
        row.className = `threat-${device.threatLevel} ${device.blocked ? 'blocked' : ''}`;
        
        // Format timestamps properly
        const firstSeen = new Date(device.firstSeen || device.timestamp);
        const lastSeen = new Date(device.lastSeen || device.timestamp);
        
        row.innerHTML = `
            <td>${device.deviceName || device.id} ${device.isKnownAttacker ? '⚠️' : ''}</td>
            <td>${device.signal} ${device.maxSignal ? `(Max: ${device.maxSignal})` : ''}</td>
            <td>${firstSeen.toLocaleDateString()} ${firstSeen.toLocaleTimeString()}</td>
            <td>${lastSeen.toLocaleDateString()} ${lastSeen.toLocaleTimeString()}</td>
            <td><span class="threat-level ${device.threatLevel}">${device.threatLevel.toUpperCase()}</span></td>
            <td>
                <button class="btn-icon" onclick="toggleBlockDevice('${device.id}')">
                    <i class="fas ${device.blocked ? 'fa-unlock' : 'fa-ban'}"></i>
                </button>
                <button class="btn-icon" onclick="analyzeDevice('${device.id}')">
                    <i class="fas fa-search"></i>
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Update row count display
    const countElement = document.getElementById('bt-devices-count');
    if (countElement) {
        countElement.textContent = bluetoothData.length;
    }
}

function updateBluetoothCharts(device) {
    // Update Activity Chart
    btActivityChart.data.datasets[0].data.shift();
    btActivityChart.data.datasets[1].data.shift();
    
    // Add new data
    const threatValue = device.threatLevel === 'high' ? 10 : 
                       device.threatLevel === 'medium' ? 6 : 2;
    btActivityChart.data.datasets[0].data.push(threatValue);
    btActivityChart.data.datasets[1].data.push(parseInt(device.signal));
    
    // Update Threat Distribution Chart
    btThreatDistributionChart.data.datasets[0].data = Object.values(threatLevels);
    
    // Update both charts
    btActivityChart.update();
    btThreatDistributionChart.update();
}

function updateBluetoothStats() {
    // Update local counts
    document.getElementById('bt-devices-count').textContent = bluetoothData.length;
    document.getElementById('bt-threats-count').textContent = threatLevels.high;
    
    // Calculate average signal from local data
    const avgSignal = bluetoothData.length > 0 
        ? bluetoothData.reduce((sum, device) => sum + parseInt(device.signal), 0) / bluetoothData.length
        : 0;
    
    document.getElementById('bt-signal-avg').textContent = `${Math.round(avgSignal)} dBm`;
    
    // Fetch real-time statistics from API
    fetch('/api/bluetooth_detections/stats?hours=1')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update with real server statistics
                document.getElementById('bt-devices-count').textContent = data.stats.total_detections || bluetoothData.length;
                document.getElementById('bt-threats-count').textContent = data.stats.high_threats || threatLevels.high;
                
                if (data.stats.avg_signal_strength) {
                    document.getElementById('bt-signal-avg').textContent = `${Math.round(data.stats.avg_signal_strength)} dBm`;
                }
                
                // Update threat distribution with real data
                if (data.stats.threat_distribution) {
                    threatLevels.low = data.stats.threat_distribution.low || 0;
                    threatLevels.medium = data.stats.threat_distribution.medium || 0;
                    threatLevels.high = data.stats.threat_distribution.high || 0;
                    
                    // Update the threat distribution chart
                    btThreatDistributionChart.data.datasets[0].data = Object.values(threatLevels);
                    btThreatDistributionChart.update();
                }
            }
        })
        .catch(error => {
            console.error('Error fetching Bluetooth statistics:', error);
            // Keep using local data if API fails
        });
}

function simulateBluetoothData() {
    // 30% chance of new device
    if (Math.random() > 0.7) {
        addBluetoothData(generateBluetoothDevice());
    }
    
    // 10% chance of existing device reappearing
    if (bluetoothData.length > 0 && Math.random() > 0.9) {
        const randomDevice = bluetoothData[Math.floor(Math.random() * bluetoothData.length)];
        addBluetoothData({
            ...randomDevice,
            signal: `${Math.floor(Math.random() * 60) - 80} dBm`,
            lastSeen: new Date()
        });
    }
}

function testBluetoothData() {
    // Add a test device with high threat level
    const testDevice = {
        id: 'TEST-ATTACKER',
        signal: `${Math.floor(Math.random() * 30) - 50} dBm`,
        firstSeen: new Date(),
        lastSeen: new Date(),
        threatLevel: 'high',
        blocked: false,
        isKnownAttacker: true
    };
    addBluetoothData(testDevice);
    showAlert('Test Bluetooth threat device added', 'success');
}

function clearBluetoothData() {
    bluetoothData = [];
    threatLevels = { high: 0, medium: 0, low: 0 };
    blockedDevices = [];
    updateBluetoothTable();
    updateBluetoothStats();
    showAlert('Bluetooth data cleared', 'info');
}

function toggleBlockDevice(deviceId) {
    const deviceIndex = bluetoothData.findIndex(d => d.id === deviceId);
    if (deviceIndex >= 0) {
        const device = bluetoothData[deviceIndex];
        device.blocked = !device.blocked;
        
        if (device.blocked) {
            blockedDevices.push(deviceId);
            showAlert(`Device ${deviceId} blocked`, 'success');
        } else {
            blockedDevices = blockedDevices.filter(id => id !== deviceId);
            showAlert(`Device ${deviceId} unblocked`, 'info');
        }
        
        updateBluetoothTable();
    }
}

function analyzeDevice(deviceId) {
    const device = bluetoothData.find(d => d.id === deviceId);
    if (device) {
        let analysis = `Analyzing ${deviceId}...\n`;
        analysis += `Device Name: ${device.deviceName || device.id}\n`;
        analysis += `Signal Strength: ${device.signal}\n`;
        analysis += `Max Signal: ${device.maxSignal || 'N/A'} dBm\n`;
        analysis += `Channel: ${device.channel || 'All'}\n`;
        analysis += `Detection Type: ${device.detectionType || 'spectrum'}\n`;
        analysis += `First seen: ${device.firstSeen.toLocaleString()}\n`;
        analysis += `Last seen: ${device.lastSeen.toLocaleString()}\n`;
        analysis += `Threat level: ${device.threatLevel.toUpperCase()}\n`;
        
        // Show spectrum data if available
        if (device.spectrumData) {
            analysis += `\nSpectrum Data:\n${device.spectrumData}\n`;
        }
        
        if (device.isKnownAttacker) {
            analysis += '\n⚠️ WARNING: Known attacker device!\n';
            analysis += 'This device matches known attack patterns.\n';
            analysis += 'Recommend immediate blocking.';
        } else if (device.threatLevel === 'high') {
            analysis += '\n⚠️ Suspicious device detected!\n';
            analysis += 'High signal strength or unusual activity detected.\n';
            analysis += 'Consider investigating further.';
        } else if (device.threatLevel === 'medium') {
            analysis += '\n⚠️ Moderate threat detected.\n';
            analysis += 'Device shows elevated activity patterns.\n';
        } else {
            analysis += '\n✅ Device appears normal.\n';
            analysis += 'Low threat level detected.';
        }
        
        showAlert(analysis, device.isKnownAttacker ? 'error' : device.threatLevel);
    }
}

function generatePdfReport(type) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    
    // Report title
    doc.setFontSize(20);
    doc.setTextColor(40);
    doc.text('CyberShield Bluetooth Threat Report', 105, 20, { align: 'center' });
    
    // Report metadata
    doc.setFontSize(12);
    doc.text(`Generated on: ${new Date().toLocaleString()}`, 14, 30);
    doc.text(`Total Devices: ${bluetoothData.length}`, 14, 38);
    doc.text(`High Threats: ${threatLevels.high}`, 14, 46);
    doc.text(`Blocked Devices: ${blockedDevices.length}`, 14, 54);
    
    // Current threat assessment
    const threatAssessment = calculateThreatAssessment();
    doc.setTextColor(threatAssessment.color);
    doc.text(`Current Threat Assessment: ${threatAssessment.level}`, 14, 62);
    doc.setTextColor(40);
    doc.text(`Recommendation: ${threatAssessment.recommendation}`, 14, 70);
    
    // Add a line separator
    doc.line(14, 76, 196, 76);
    
    // Add charts
    doc.setFontSize(16);
    doc.text('Bluetooth Threat Activity', 14, 86);
    
    const activityChartImg = document.getElementById('btActivityChart').toDataURL('image/png');
    doc.addImage(activityChartImg, 'PNG', 14, 90, 180, 80);
    
    doc.addPage();
    doc.setFontSize(16);
    doc.text('Threat Level Distribution', 14, 20);
    
    const distributionChartImg = document.getElementById('btThreatDistributionChart').toDataURL('image/png');
    doc.addImage(distributionChartImg, 'PNG', 14, 30, 180, 80);
    
    // Detailed device listing
    doc.setFontSize(16);
    doc.text('Detected Bluetooth Devices', 14, 120);
    
    // Table headers
    doc.setFontSize(12);
    doc.text('Device ID', 14, 130);
    doc.text('Signal', 60, 130);
    doc.text('First Seen', 90, 130);
    doc.text('Threat Level', 140, 130);
    doc.text('Status', 180, 130);
    
    // Table rows
    let y = 140;
    bluetoothData.slice(0, 50).forEach(device => {
        if (y > 270) {
            doc.addPage();
            y = 20;
        }
        
        doc.setTextColor(40);
        doc.text(device.id, 14, y);
        doc.text(device.signal, 60, y);
        doc.text(device.firstSeen.toLocaleDateString(), 90, y);
        
        // Color code threat level
        doc.setTextColor(
            device.threatLevel === 'high' ? '#e74c3c' : 
            device.threatLevel === 'medium' ? '#f39c12' : '#2ecc71'
        );
        doc.text(device.threatLevel.toUpperCase(), 140, y);
        
        doc.setTextColor(device.blocked ? '#2ecc71' : '#e74c3c');
        doc.text(device.blocked ? 'BLOCKED' : 'ACTIVE', 180, y);
        
        y += 10;
    });
    
    // Mitigation recommendations
    doc.addPage();
    doc.setFontSize(16);
    doc.text('Bluetooth Security Recommendations', 14, 20);
    doc.setFontSize(12);
    
    let mitigationY = 30;
    
    // General recommendations
    const generalRecommendations = [
        "1. Disable Bluetooth when not in use",
        "2. Set Bluetooth to non-discoverable mode",
        "3. Use strong pairing PINs (6+ digits)",
        "4. Keep devices updated with latest firmware",
        "5. Disable unnecessary Bluetooth profiles",
        "6. Monitor for unexpected pairing requests",
        "7. Use Bluetooth Low Energy (BLE) privacy features"
    ];
    
    generalRecommendations.forEach(rec => {
        doc.text(rec, 14, mitigationY);
        mitigationY += 8;
    });
    
    // Specific threat recommendations
    mitigationY += 8;
    doc.setFontSize(14);
    doc.text('Threat-Specific Mitigations:', 14, mitigationY);
    mitigationY += 10;
    doc.setFontSize(12);
    
    const threatMitigations = {
        'BlueBorne': [
            "- Apply all available security patches",
            "- Disable unnecessary Bluetooth services",
            "- Use network segmentation for Bluetooth devices"
        ],
        'KNOB-Attack': [
            "- Ensure devices use Secure Connections mode",
            "- Verify encryption key strength is 7 octets or more",
            "- Update to Bluetooth 5.1 or later"
        ],
        'BLE-Sniffer': [
            "- Use BLE privacy features",
            "- Rotate MAC addresses regularly",
            "- Implement strong encryption"
        ],
        'BT-Kracker': [
            "- Disable legacy pairing methods",
            "- Use Secure Simple Pairing (SSP)",
            "- Monitor for brute force attempts"
        ]
    };
    
    // Only show recommendations for threats we've detected
    knownAttackers.forEach(threat => {
        if (bluetoothData.some(d => d.id === threat)) {
            doc.setFontSize(12);
            doc.setTextColor(40);
            doc.text(`${threat}:`, 14, mitigationY);
            mitigationY += 8;
            
            doc.setFontSize(10);
            threatMitigations[threat].forEach(mit => {
                doc.text(mit, 20, mitigationY);
                mitigationY += 6;
            });
            mitigationY += 4;
        }
    });
    
    // Save the PDF
    doc.save(`CyberShield-Bluetooth-Report-${new Date().toISOString().slice(0,10)}.pdf`);
}

function calculateThreatAssessment() {
    if (threatLevels.high >= 3) {
        return {
            level: 'CRITICAL',
            color: '#e74c3c',
            recommendation: 'Immediate action required. Multiple high threat devices detected.'
        };
    } else if (threatLevels.high >= 1 || threatLevels.medium >= 5) {
        return {
            level: 'HIGH',
            color: '#f39c12',
            recommendation: 'Elevated threat level. Review detected devices and block suspicious ones.'
        };
    } else if (threatLevels.medium >= 2) {
        return {
            level: 'MODERATE',
            color: '#3498db',
            recommendation: 'Potential threats detected. Monitor activity closely.'
        };
    } else {
        return {
            level: 'LOW',
            color: '#2ecc71',
            recommendation: 'Normal Bluetooth activity. No significant threats detected.'
        };
    }
}

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
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; font-size: 20px; cursor: pointer; color: ${color.text};">&times;</button>
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

// Test Arduino connection and data flow
function testArduinoConnection() {
    // Check if we're receiving data from Arduino
    fetch('/api/bluetooth_detections?device_id=NANO-2.4GHz-Scanner-001&hours=1&limit=1')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.detections && data.detections.length > 0) {
                const lastDetection = data.detections[0];
                const timeDiff = (new Date() - new Date(lastDetection.timestamp)) / 1000 / 60; // minutes
                
                if (timeDiff < 5) {
                    showAlert(`✅ Arduino connection active!\nLast data received: ${Math.round(timeDiff)} minute(s) ago\nDevice: ${lastDetection.device_name}\nSignal: ${lastDetection.signal_strength} dBm`, 'success');
                } else {
                    showAlert(`⚠️ Arduino connection stale.\nLast data received: ${Math.round(timeDiff)} minute(s) ago\nCheck Arduino WiFi connection and power.`, 'warning');
                }
            } else {
                showAlert('❌ No data from Arduino detected.\nCheck:\n- Arduino power and WiFi connection\n- Server IP configuration in Arduino code\n- Network connectivity', 'error');
            }
        })
        .catch(error => {
            console.error('Error testing Arduino connection:', error);
            showAlert('❌ Failed to check Arduino connection.\nAPI endpoint may be unreachable.', 'error');
        });
}

// Clear all detection data
function clearAllDetections() {
    if (confirm('Are you sure you want to clear all Bluetooth detection data?')) {
        fetch('/api/bluetooth_detections/clear', { method: 'DELETE' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    bluetoothData = [];
                    threatLevels = { high: 0, medium: 0, low: 0 };
                    updateBluetoothTable();
                    updateBluetoothStats();
                    showAlert('✅ All detection data cleared successfully!', 'success');
                } else {
                    showAlert('❌ Failed to clear detection data.', 'error');
                }
            })
            .catch(error => {
                console.error('Error clearing detections:', error);
                showAlert('❌ Error clearing detection data.', 'error');
            });
    }
}

// Export functions for HTML
window.testBluetoothData = testBluetoothData;
window.clearBluetoothData = clearBluetoothData;
window.toggleBlockDevice = toggleBlockDevice;
window.analyzeDevice = analyzeDevice;
window.generatePdfReport = generatePdfReport;
window.testArduinoConnection = testArduinoConnection;
window.clearAllDetections = clearAllDetections;