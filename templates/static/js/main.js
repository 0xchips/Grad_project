// Initialize jsPDF
const { jsPDF } = window.jspdf;

// Initialize EmailJS with your public key
emailjs.init('rsajzqeerdfifaxt');

// Email configuration
const emailConfig = {
    serviceId: 'service_ej68ebi',
    templateId: 'template_46n88j3',
    recipientEmail: 'qaisalsayeh@gmail.com'
};

// Global threat data storage
const threatData = {
    bluetooth: [],
    gps: [],
    network: []
};

// WebSocket connection management
let socket;
const connectionStatus = document.querySelector('.connection-status');
let alertBox;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    alertBox = document.getElementById('alert-box');
    if (!alertBox) {
        alertBox = document.createElement('div');
        alertBox.id = 'alert-box';
        document.body.prepend(alertBox);
    }
    
    updateTime();
    setInterval(updateTime, 1000);
    connectWebSocket();
    
    // Load initial data
    loadInitialData();
});

function loadInitialData() {
    // Simulate loading data from API
    setTimeout(() => {
        generateFakeLogs();
        showAlert('System initialized and data loaded', 'success');
    }, 1500);
}

function showAlert(message, type = 'success') {
    const alertTypes = {
        success: { icon: 'check-circle', color: 'success' },
        error: { icon: 'exclamation-circle', color: 'danger' },
        warning: { icon: 'exclamation-triangle', color: 'warning' },
        info: { icon: 'info-circle', color: 'primary' }
    };
    
    const alertConfig = alertTypes[type] || alertTypes.success;
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${alertConfig.color}`;
    alertElement.innerHTML = `
        <i class="fas fa-${alertConfig.icon}"></i>
        ${message}
        <button class="alert-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    alertBox.appendChild(alertElement);
    setTimeout(() => {
        alertElement.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        alertElement.classList.remove('show');
        setTimeout(() => {
            alertElement.remove();
        }, 300);
    }, 5000);
}

function connectWebSocket() {
    console.log('Simulating WebSocket connection');
    connectionStatus.querySelector('span').textContent = 'Connected';
    
    // Simulate random attacks
    setInterval(() => {
        if (Math.random() > 0.7) { // 30% chance of attack
            const attackType = Math.random();
            if (attackType < 0.33) {
                testBluetoothData();
            } else if (attackType < 0.66) {
                testGpsData();
            } else {
                testNetworkData();
            }
        }
    }, 15000); // Every 15 seconds
}

function updateTime() {
    const timeElements = document.querySelectorAll('.timestamp');
    if (timeElements.length > 0) {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        const dateString = now.toLocaleDateString(undefined, { 
            weekday: 'short', 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
        
        timeElements.forEach(el => {
            el.textContent = `${dateString} ${timeString}`;
        });
    }
}

function getThreatClass(level) {
    if (!level) return 'safe';
    if (typeof level === 'boolean') return level ? 'danger' : 'safe';
    level = level.toLowerCase();
    return level === 'high' ? 'danger' : level === 'medium' ? 'warning' : 'safe';
}

function updateStatus(elementId, level) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const indicator = element.querySelector('.status-indicator') || document.createElement('span');
    indicator.className = 'status-indicator ' + getThreatClass(level);
    
    let statusText = '';
    if (typeof level === 'boolean') {
        statusText = level ? 'Spoofing detected!' : 'No anomalies detected';
    } else {
        statusText = level === 'high' ? 'Active threat detected' :
                   level === 'medium' ? 'Suspicious activity' :
                   'No threats detected';
    }
    
    if (!element.querySelector('.status-indicator')) {
        element.prepend(indicator);
    }
    element.innerHTML = `<span class="status-indicator ${getThreatClass(level)}"></span> ${statusText}`;
}

function clearTable(tableId) {
    const table = document.getElementById(tableId);
    if (table) {
        table.getElementsByTagName('tbody')[0].innerHTML = '';
    }
    const type = tableId.split('-')[0];
    threatData[type] = [];
    updateStatus(`${type}-status`, 'low');
    showAlert(`Cleared ${type} data`, 'success');
    
    // Update dashboard stats if on main page
    if (window.location.pathname.endsWith('index.html') || window.location.pathname === '/') {
        updateDashboardStats();
    }
}

function blockDevice(button, deviceId) {
    const row = button.closest('tr');
    row.style.opacity = '0.5';
    row.style.textDecoration = 'line-through';
    button.disabled = true;
    showAlert(`Device ${deviceId} blocked`, 'success');
}

function blockIP(button, ip) {
    const row = button.closest('tr');
    row.style.opacity = '0.5';
    row.style.textDecoration = 'line-through';
    button.disabled = true;
    showAlert(`IP ${ip} blocked`, 'success');
}

// Format threat details for email
function formatThreatDetails(threatType, data) {
    const now = new Date();
    let details = `Threat detected at ${now.toLocaleString()}\n\n`;
    
    if (threatType === 'bluetooth') {
        details += `BLUETOOTH THREAT DETECTED:\n`;
        details += `Device ID: ${data.device_id}\n`;
        details += `Signal Strength: ${data.signal_strength} dBm\n`;
        details += `Threat Level: ${data.threat_level}\n`;
    } 
    else if (threatType === 'gps') {
        details += `GPS SPOOFING DETECTED:\n`;
        details += `Coordinates: ${data.latitude.toFixed(4)}, ${data.longitude.toFixed(4)}\n`;
        details += `Accuracy: ±${data.accuracy.toFixed(1)}m\n`;
        details += `Status: ${data.anomaly ? 'SPOOFING DETECTED' : 'Normal'}\n`;
    } 
    else if (threatType === 'network') {
        details += `NETWORK ATTACK DETECTED:\n`;
        details += `Event Type: ${data.event_type}\n`;
        details += `Source IP: ${data.source_ip}\n`;
        details += `Severity: ${data.severity}\n`;
    }
    
    details += `\nACTION REQUIRED: Please check your Cyber Threat Dashboard immediately.`;
    return details;
}

// Send email notification using EmailJS
async function sendEmailNotification(threatType, threatData) {
    try {
        const threatDetails = formatThreatDetails(threatType, threatData);
        
        const response = await emailjs.send(
            emailConfig.serviceId, 
            emailConfig.templateId, 
            {
                to_email: emailConfig.recipientEmail,
                from_name: 'Cyber Threat Dashboard',
                threat_type: threatType.toUpperCase(),
                threat_details: threatDetails,
                timestamp: new Date().toLocaleString()
            }
        );

        console.log('Email sent:', response);
        showAlert('Security team notified via email', 'success');
    } catch (error) {
        console.error('Failed to send email:', error);
        showAlert('Failed to send email notification', 'error');
    }
}

function generatePdfReport(type) {
    try {
        // Check if jsPDF is properly loaded
        if (typeof jsPDF === 'undefined' || !jsPDF.API.autoTable) {
            showAlert('PDF library not loaded properly. Please refresh the page.', 'error');
            return;
        }

        if (!threatData[type] || threatData[type].length === 0) {
            showAlert(`No ${type} data available to generate report`, 'error');
            return;
        }

        const doc = new jsPDF();
        const now = new Date();
        
        // Set document properties
        doc.setProperties({
            title: `${type.toUpperCase()} Threat Report`,
            subject: 'Cybersecurity Threat Analysis',
            author: 'Cyber Threat Dashboard'
        });

        // Add title
        doc.setFontSize(20);
        doc.setTextColor(41, 128, 185);
        doc.text(`${type.toUpperCase()} THREAT REPORT`, 105, 20, { align: 'center' });
        
        // Add subtitle
        doc.setFontSize(12);
        doc.setTextColor(100, 100, 100);
        doc.text(`Generated: ${now.toLocaleString()}`, 105, 30, { align: 'center' });

        // Prepare table data
        const headers = {
            bluetooth: ['Device ID', 'Signal', 'Timestamp', 'Threat Level'],
            gps: ['Timestamp', 'Coordinates', 'Accuracy', 'Status'],
            network: ['Timestamp', 'Event Type', 'Source IP', 'Severity']
        }[type];

        const body = threatData[type].map(item => {
            const date = new Date(item.timestamp || new Date());
            if (type === 'bluetooth') {
                return [
                    item.device_id,
                    `${item.signal_strength} dBm`,
                    date.toLocaleTimeString(),
                    item.threat_level
                ];
            } else if (type === 'gps') {
                return [
                    date.toLocaleTimeString(),
                    `${item.latitude.toFixed(4)}, ${item.longitude.toFixed(4)}`,
                    `±${item.accuracy.toFixed(1)}m`,
                    item.anomaly ? 'Spoofing' : 'Normal'
                ];
            } else {
                return [
                    date.toLocaleTimeString(),
                    item.event_type,
                    item.source_ip,
                    item.severity
                ];
            }
        });

        // Add table
        doc.autoTable({
            startY: 40,
            head: [headers],
            body: body,
            theme: 'grid',
            headStyles: {
                fillColor: [41, 128, 185],
                textColor: 255,
                fontStyle: 'bold'
            },
            alternateRowStyles: {
                fillColor: [240, 240, 240]
            },
            margin: { top: 10 },
            styles: {
                cellPadding: 5,
                fontSize: 10,
                valign: 'middle'
            }
        });

        // Add footer
        const pageCount = doc.internal.getNumberOfPages();
        for(let i = 1; i <= pageCount; i++) {
            doc.setPage(i);
            doc.setFontSize(10);
            doc.setTextColor(150);
            doc.text(`Page ${i} of ${pageCount}`, doc.internal.pageSize.width - 20, doc.internal.pageSize.height - 10, { align: 'right' });
        }

        // Save the PDF
        doc.save(`${type}_threat_report_${now.getTime()}.pdf`);
        showAlert(`${type} report generated successfully!`, 'success');
        
    } catch (error) {
        console.error('PDF generation error:', error);
        showAlert(`Failed to generate report: ${error.message}`, 'error');
    }
}

function updateDashboardStats() {
    // Update Bluetooth stats
    const btDevices = document.getElementById('bt-devices-total');
    const btThreats = document.getElementById('bt-threats-total');
    if (btDevices) btDevices.textContent = threatData.bluetooth.length;
    if (btThreats) btThreats.textContent = threatData.bluetooth.filter(d => d.threat_level === 'high').length;
    
    // Update GPS stats
    const gpsReadings = document.getElementById('gps-readings-total');
    const gpsAnomalies = document.getElementById('gps-anomalies-total');
    if (gpsReadings) gpsReadings.textContent = threatData.gps.length;
    if (gpsAnomalies) gpsAnomalies.textContent = threatData.gps.filter(d => d.anomaly).length;
    
    // Update Network stats
    const networkEvents = document.getElementById('network-events-total');
    const networkHigh = document.getElementById('network-high-total');
    if (networkEvents) networkEvents.textContent = threatData.network.length;
    if (networkHigh) networkHigh.textContent = threatData.network.filter(d => d.severity === 'high').length;
}

// Fake logs generator
function generateFakeLogs() {
    // Clear existing data
    threatData.bluetooth = [];
    threatData.gps = [];
    threatData.network = [];
    
    // Generate Bluetooth logs
    for (let i = 0; i < 15; i++) {
        addBluetoothData({
            device_id: "DEV-" + Math.random().toString(36).substr(2, 4).toUpperCase(),
            signal_strength: -Math.floor(Math.random() * 60) - 30,
            threat_level: Math.random() > 0.8 ? "high" : Math.random() > 0.5 ? "medium" : "low",
            timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString()
        });
    }
    //31.9210905,35.9355047,846
    // Generate GPS logs
    const baseLat = 31.9210905;
    const baseLng = 35.9355047;
    for (let i = 0; i < 20; i++) {
        addGpsData({
            latitude: baseLat + (Math.random() * 0.02 - 0.01),
            longitude: baseLng + (Math.random() * 0.02 - 0.01),
            accuracy: Math.random() > 0.7 ? Math.random() * 150 + 50 : Math.random() * 10 + 5,
            anomaly: Math.random() > 0.85,
            timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString()
        });
    }
    
    // Generate Network logs
    const attackTypes = ["Port Scan", "DDoS", "MITM", "SQL Injection", "DNS Spoofing"];
    for (let i = 0; i < 25; i++) {
        addNetworkData({
            event_type: attackTypes[Math.floor(Math.random() * attackTypes.length)],
            source_ip: `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
            severity: Math.random() > 0.9 ? "high" : Math.random() > 0.6 ? "medium" : "low",
            timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString()
        });
    }
    
    showAlert('Generated fake logs with historical data', 'success');
    updateDashboardStats();
}

function testBluetoothData() {
    const testData = {
        device_id: "TEST:" + Math.random().toString(36).substring(2, 6).toUpperCase(),
        signal_strength: -Math.floor(Math.random() * 60) - 30,
        threat_level: ["low", "medium", "high"][Math.floor(Math.random() * 3)],
        timestamp: new Date().toISOString()
    };
    addBluetoothData(testData);
    showAlert('Bluetooth test data added!', 'success');
}

function testGpsData() {
    const baseLat = 37.7749;
    const baseLng = -122.4194;
    const testData = {
        latitude: baseLat + (Math.random() * 0.02 - 0.01),
        longitude: baseLng + (Math.random() * 0.02 - 0.01),
        accuracy: Math.random() > 0.5 ? Math.random() * 10 + 5 : Math.random() * 200 + 50,
        anomaly: Math.random() > 0.7,
        timestamp: new Date().toISOString()
    };
    addGpsData(testData);
    showAlert('GPS test data added!', 'success');
}

function testNetworkData() {
    const attackTypes = [
        "Port Scan", "DDoS", "MITM", "SQL Injection", 
        "DNS Spoofing", "Brute Force", "XSS Attempt"
    ];
    const testData = {
        event_type: attackTypes[Math.floor(Math.random() * attackTypes.length)],
        source_ip: `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
        severity: ["low", "medium", "high"][Math.floor(Math.random() * 3)],
        timestamp: new Date().toISOString()
    };
    addNetworkData(testData);
    showAlert('Network test data added!', 'success');

    fetch('/logs')
            .then(response => response.json())
            .then(logs => {
                const tableBody = document.querySelector("#logTable tbody");

                // Clear the table before adding new rows
                tableBody.innerHTML = "";

                // Populate the table with the logs
                logs.forEach(log => {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td>${log.timestamp}</td>
                        <td>${log.alert_type}</td>
                        <td>${log.count}</td>
                        <td>${log.attacker_bssid}</td>
                        <td>${log.attacker_ssid}</td>
                        <td>${log.destination_bssid}</td>
                        <td>${log.destination_ssid}</td>
                    `;
                    tableBody.appendChild(row);
                });
            })
            .catch(error => console.error("Error fetching logs:", error));

}

// Universal Chart Expansion Functionality
function expandChart(chartId, chartTitle = 'Chart') {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'chart-expand-overlay';
    overlay.innerHTML = `
        <div class="chart-expand-modal">
            <div class="chart-expand-header">
                <h2>${chartTitle}</h2>
                <button class="chart-expand-close" onclick="closeExpandedChart()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="chart-expand-content">
                <canvas id="${chartId}_expanded"></canvas>
            </div>
            <div class="chart-expand-footer">
                <button class="btn btn-secondary" onclick="downloadExpandedChart('${chartId}_expanded', '${chartTitle}')">
                    <i class="fas fa-download"></i> Download Chart
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    
    // Get the original chart
    const originalCanvas = document.getElementById(chartId);
    if (!originalCanvas) {
        console.error(`Chart with ID ${chartId} not found`);
        closeExpandedChart();
        return;
    }
    
    // Get the Chart.js instance
    let originalChart = null;
    if (typeof Chart !== 'undefined' && Chart.instances) {
        Chart.helpers.each(Chart.instances, function(instance) {
            if (instance.canvas && instance.canvas.id === chartId) {
                originalChart = instance;
            }
        });
    }
    
    if (!originalChart) {
        console.error(`Chart instance for ${chartId} not found`);
        closeExpandedChart();
        return;
    }
    
    // Create expanded chart with same configuration
    const expandedCanvas = document.getElementById(`${chartId}_expanded`);
    const expandedCtx = expandedCanvas.getContext('2d');
    
    // Clone the chart configuration with deep copy
    const config = {
        type: originalChart.config.type,
        data: JSON.parse(JSON.stringify(originalChart.data)),
        options: JSON.parse(JSON.stringify(originalChart.options || {}))
    };
    
    // Enhance the configuration for expanded view
    config.options.responsive = true;
    config.options.maintainAspectRatio = false;
    
    // Ensure plugins object exists
    if (!config.options.plugins) {
        config.options.plugins = {};
    }
    
    // Enhance legend for expanded view
    config.options.plugins.legend = {
        display: true,
        position: 'bottom',
        labels: {
            padding: 20,
            usePointStyle: true,
            font: {
                size: 12
            }
        }
    };
    
    // Add title if not present
    if (!config.options.plugins.title) {
        config.options.plugins.title = {
            display: true,
            text: chartTitle,
            font: {
                size: 16,
                weight: 'bold'
            },
            padding: 20
        };
    }
    
    // Create the expanded chart
    new Chart(expandedCtx, config);
    
    // Show overlay with animation
    setTimeout(() => {
        overlay.classList.add('active');
    }, 10);
}

// Special handler for GPS map expansion
function expandGpsMap() {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'chart-expand-overlay';
    overlay.innerHTML = `
        <div class="chart-expand-modal">
            <div class="chart-expand-header">
                <h2>GPS Location Map</h2>
                <button class="chart-expand-close" onclick="closeExpandedChart()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="chart-expand-content">
                <div id="gpsMap_expanded" style="width: 100%; height: 100%;"></div>
            </div>
            <div class="chart-expand-footer">
                <button class="btn btn-secondary" onclick="downloadGpsMap()">
                    <i class="fas fa-download"></i> Download Map
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    
    // Initialize expanded map if Leaflet is available
    if (typeof L !== 'undefined') {
        setTimeout(() => {
            const expandedMap = L.map('gpsMap_expanded').setView([51.505, -0.09], 13);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(expandedMap);
            
            // Copy markers from original map if available
            if (window.gpsMap && window.gpsMap._layers) {
                Object.values(window.gpsMap._layers).forEach(layer => {
                    if (layer instanceof L.Marker) {
                        const newMarker = L.marker(layer.getLatLng()).addTo(expandedMap);
                        if (layer.getPopup()) {
                            newMarker.bindPopup(layer.getPopup().getContent());
                        }
                    }
                });
            }
        }, 100);
    }
    
    // Show overlay with animation
    setTimeout(() => {
        overlay.classList.add('active');
    }, 10);
}

function downloadGpsMap() {
    // Simple implementation - could be enhanced with map screenshot
    console.log('GPS Map download requested');
    showAlert('GPS Map download functionality would be implemented here', 'info');
}

// Export functions for HTML event handlers
window.generateFakeLogs = generateFakeLogs;
window.testBluetoothData = testBluetoothData;
window.testGpsData = testGpsData;
window.testNetworkData = testNetworkData;
window.generatePdfReport = generatePdfReport;
window.clearTable = clearTable;
window.blockDevice = blockDevice;
window.blockIP = blockIP;
window.expandChart = expandChart;
window.closeExpandedChart = closeExpandedChart;
window.downloadExpandedChart = downloadExpandedChart;
window.expandGpsMap = expandGpsMap;
window.downloadGpsMap = downloadGpsMap;