// Bluetooth Threat Monitoring System
let bluetoothData = [];
let threatLevels = { high: 0, medium: 0, low: 0 };
let blockedDevices = [];
let btActivityChart, btThreatDistributionChart;
let knownAttackers = ['BLE-Sniffer', 'BT-Kracker', 'BlueBorne', 'KNOB-Attack'];

document.addEventListener('DOMContentLoaded', function() {
    initBluetoothCharts();
    loadBluetoothData();
    setInterval(simulateBluetoothData, 10000); // Simulate new data every 10s
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
    // Simulate loading data
    setTimeout(() => {
        for (let i = 0; i < 15; i++) {
            addBluetoothData(generateBluetoothDevice());
        }
        updateBluetoothStats();
    }, 1000);
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

function updateBluetoothTable() {
    const tableBody = document.querySelector('#bt-table tbody');
    tableBody.innerHTML = '';
    
    // Sort by threat level (high to low) and then by last seen (newest first)
    const sortedData = [...bluetoothData].sort((a, b) => {
        if (a.threatLevel === b.threatLevel) {
            return b.lastSeen - a.lastSeen;
        }
        return (b.threatLevel === 'high' ? 2 : b.threatLevel === 'medium' ? 1 : 0) - 
               (a.threatLevel === 'high' ? 2 : a.threatLevel === 'medium' ? 1 : 0);
    });
    
    // Add rows
    sortedData.slice(0, 100).forEach(device => {
        const row = document.createElement('tr');
        row.className = `threat-${device.threatLevel} ${device.blocked ? 'blocked' : ''}`;
        
        row.innerHTML = `
            <td>${device.id} ${device.isKnownAttacker ? '⚠️' : ''}</td>
            <td>${device.signal}</td>
            <td>${device.firstSeen.toLocaleDateString()}</td>
            <td>${device.lastSeen.toLocaleTimeString()}</td>
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
    document.getElementById('bt-devices-count').textContent = bluetoothData.length;
    document.getElementById('bt-threats-count').textContent = threatLevels.high;
    
    // Calculate average signal
    const avgSignal = bluetoothData.length > 0 
        ? bluetoothData.reduce((sum, device) => sum + parseInt(device.signal), 0) / bluetoothData.length
        : 0;
    
    document.getElementById('bt-signal-avg').textContent = `${Math.round(avgSignal)} dBm`;
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
        analysis += `Signal: ${device.signal}\n`;
        analysis += `First seen: ${device.firstSeen.toLocaleString()}\n`;
        analysis += `Threat level: ${device.threatLevel.toUpperCase()}\n`;
        
        if (device.isKnownAttacker) {
            analysis += '\n⚠️ WARNING: Known attacker device!\n';
            analysis += 'This device matches known attack patterns.\n';
            analysis += 'Recommend immediate blocking.';
        } else if (device.threatLevel === 'high') {
            analysis += '\n⚠️ Suspicious device detected!\n';
            analysis += 'This device exhibits suspicious behavior.\n';
            analysis += 'Consider blocking if not recognized.';
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
    doc.text('WiGuard Bluetooth Threat Report', 105, 20, { align: 'center' });
    
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
    doc.save(`WiGuard-Bluetooth-Report-${new Date().toISOString().slice(0,10)}.pdf`);
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
    // In a real app, you'd show this in the UI
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Export functions for HTML
window.testBluetoothData = testBluetoothData;
window.clearBluetoothData = clearBluetoothData;
window.toggleBlockDevice = toggleBlockDevice;
window.analyzeDevice = analyzeDevice;
window.generatePdfReport = generatePdfReport;