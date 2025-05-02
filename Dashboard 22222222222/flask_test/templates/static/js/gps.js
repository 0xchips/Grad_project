// GPS Monitoring System
let gpsData = [];
let map;
let accuracyChart;
let anomalies = 0;
let baseLat = 31.9210905;
let baseLng = 35.9355047;

document.addEventListener('DOMContentLoaded', function() {
    initMap();
    initAccuracyChart();
    loadGpsData();
    setInterval(simulateGpsData, 15000); // Simulate new data every 15s
    
    // Setup search functionality
    document.getElementById('gps-search').addEventListener('input', function() {
        filterGpsTable(this.value);
    });
});

function initMap() {
    map = L.map('gpsMap').setView([baseLat, baseLng], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
}

function initAccuracyChart() {
    const ctx = document.getElementById('gpsAccuracyChart').getContext('2d');
    accuracyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array(12).fill('').map((_, i) => `${i}:00`),
            datasets: [{
                label: 'Accuracy (m)',
                data: Array(12).fill(0),
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Meters'
                    }
                }
            }
        }
    });
}

function loadGpsData() {
    // Simulate loading initial data
    setTimeout(() => {
        for (let i = 0; i < 10; i++) {
            addGpsData(generateGpsReading());
        }
        updateGpsStats();
    }, 1000);
}

function generateGpsReading() {
    const isAnomaly = Math.random() > 0.85;
    const accuracy = Math.random() > 0.7 ? Math.random() * 100 + 50 : Math.random() * 10 + 5;
    
    // Generate realistic movement
    const movementFactor = isAnomaly ? 10 : 1;
    const latVariation = (Math.random() * 0.02 - 0.01) * movementFactor;
    const lngVariation = (Math.random() * 0.02 - 0.01) * movementFactor;
    
    return {
        timestamp: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000),
        latitude: baseLat + latVariation,
        longitude: baseLng + lngVariation,
        accuracy: accuracy,
        anomaly: isAnomaly,
        flagged: false
    };
}

function addGpsData(reading) {
    gpsData.unshift(reading);
    if (reading.anomaly) anomalies++;
    
    // Update map
    const marker = L.circleMarker([reading.latitude, reading.longitude], {
        radius: 5 + (reading.anomaly ? 3 : 0),
        color: reading.anomaly ? '#e74c3c' : '#2ecc71',
        fillOpacity: 0.8,
        weight: reading.flagged ? 3 : 1
    }).addTo(map);
    
    marker.bindPopup(`
        <b>${reading.timestamp.toLocaleTimeString()}</b><br>
        Coordinates: ${reading.latitude.toFixed(6)}, ${reading.longitude.toFixed(6)}<br>
        Accuracy: ${reading.accuracy.toFixed(1)}m<br>
        Status: ${reading.anomaly ? '<span style="color:#e74c3c">Anomaly</span>' : 'Normal'}
    `);
    
    // Update table
    updateGpsTable();
    
    // Update chart
    updateAccuracyChart(reading.accuracy);
    updateGpsStats();
}

function updateGpsTable() {
    const tableBody = document.querySelector('#gps-table tbody');
    tableBody.innerHTML = '';
    
    // Sort by timestamp (newest first)
    const sortedData = [...gpsData].sort((a, b) => b.timestamp - a.timestamp);
    
    // Add rows
    sortedData.slice(0, 100).forEach(reading => {
        const row = document.createElement('tr');
        row.className = reading.anomaly ? 'anomaly' : '';
        
        row.innerHTML = `
            <td>${reading.timestamp.toLocaleTimeString()}</td>
            <td>${reading.latitude.toFixed(6)}, ${reading.longitude.toFixed(6)}</td>
            <td>${reading.accuracy.toFixed(1)}m</td>
            <td><span class="status ${reading.anomaly ? 'anomaly' : 'normal'}">${reading.anomaly ? 'Anomaly' : 'Normal'}</span></td>
            <td>
                <button class="btn-icon" onclick="zoomToLocation(${reading.latitude}, ${reading.longitude})"><i class="fas fa-search-location"></i></button>
                <button class="btn-icon" onclick="flagLocation(${gpsData.indexOf(reading)})"><i class="fas fa-flag"></i></button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    document.getElementById('gps-total-count').textContent = gpsData.length;
}

function filterGpsTable(searchTerm) {
    const rows = document.querySelectorAll('#gps-table tbody tr');
    searchTerm = searchTerm.toLowerCase();
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

function updateAccuracyChart(accuracy) {
    accuracyChart.data.datasets[0].data.shift();
    accuracyChart.data.datasets[0].data.push(accuracy);
    accuracyChart.update();
}

function updateGpsStats() {
    document.getElementById('gps-locations-count').textContent = gpsData.length;
    document.getElementById('gps-anomalies-count').textContent = anomalies;
    
    // Calculate average accuracy
    const avgAccuracy = gpsData.reduce((sum, reading) => {
        return sum + reading.accuracy;
    }, 0) / gpsData.length;
    
    document.getElementById('gps-accuracy-avg').textContent = `${Math.round(avgAccuracy)}m`;
}

function simulateGpsData() {
    if (Math.random() > 0.7) { // 30% chance of new reading
        addGpsData(generateGpsReading());
    }
}

function testGpsData() {
    const testReading = generateGpsReading();
    testReading.anomaly = true; // Force anomaly for testing
    addGpsData(testReading);
    showAlert('Test GPS anomaly added', 'success');
}

function clearGpsData() {
    gpsData = [];
    anomalies = 0;
    map.eachLayer(layer => {
        if (layer instanceof L.CircleMarker) {
            map.removeLayer(layer);
        }
    });
    document.querySelector('#gps-table tbody').innerHTML = '';
    updateGpsStats();
    showAlert('GPS data cleared', 'info');
}

function zoomToLocation(lat, lng) {
    map.setView([lat, lng], 15);
}

function flagLocation(index) {
    if (index >= 0 && index < gpsData.length) {
        gpsData[index].flagged = !gpsData[index].flagged;
        updateGpsTable();
        showAlert(`Location ${gpsData[index].flagged ? 'flagged' : 'unflagged'} for review`, 'success');
    }
}

function generatePdfReport(type) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    
    // Report title
    doc.setFontSize(20);
    doc.setTextColor(40);
    doc.text('CyberShield GPS Threat Report', 105, 20, { align: 'center' });
    
    // Report metadata
    doc.setFontSize(12);
    doc.text(`Generated on: ${new Date().toLocaleString()}`, 14, 30);
    doc.text(`Total Locations: ${gpsData.length}`, 14, 38);
    doc.text(`Anomalies Detected: ${anomalies}`, 14, 46);
    doc.text(`Average Accuracy: ${document.getElementById('gps-accuracy-avg').textContent}`, 14, 54);
    
    // Current threat assessment
    const threatLevel = anomalies > 3 ? 'HIGH' : anomalies > 0 ? 'MODERATE' : 'LOW';
    const threatColor = anomalies > 3 ? '#e74c3c' : anomalies > 0 ? '#f39c12' : '#2ecc71';
    
    doc.setTextColor(threatColor);
    doc.text(`Current Threat Level: ${threatLevel}`, 14, 62);
    doc.setTextColor(40);
    doc.text(`Recommendation: ${anomalies > 3 ? 'Immediate action required' : anomalies > 0 ? 'Further investigation recommended' : 'No action required'}`, 14, 70);
    
    // Add a line separator
    doc.line(14, 76, 196, 76);
    
    // Add charts
    doc.setFontSize(16);
    doc.text('GPS Location Map', 14, 86);
    
    // Convert map to image (simplified - in real app you'd use html2canvas)
    doc.setFontSize(10);
    doc.text('Map visualization would appear here', 14, 94);
    
    doc.setFontSize(16);
    doc.text('Accuracy Over Time', 14, 120);
    
    const accuracyChartImg = document.getElementById('gpsAccuracyChart').toDataURL('image/png');
    doc.addImage(accuracyChartImg, 'PNG', 14, 126, 180, 80);
    
    // Detailed location listing
    doc.addPage();
    doc.setFontSize(16);
    doc.text('Detailed Location History', 14, 20);
    
    // Table headers
    doc.setFontSize(12);
    doc.text('Timestamp', 14, 30);
    doc.text('Coordinates', 50, 30);
    doc.text('Accuracy', 110, 30);
    doc.text('Status', 150, 30);
    
    // Table rows
    let y = 38;
    gpsData.slice(0, 50).forEach(location => { // Limit to 50 most recent locations
        if (y > 270) {
            doc.addPage();
            y = 20;
        }
        
        doc.setTextColor(40);
        doc.text(location.timestamp.toLocaleTimeString(), 14, y);
        doc.text(`${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}`, 50, y);
        doc.text(`${location.accuracy.toFixed(1)}m`, 110, y);
        
        // Color code status
        doc.setTextColor(location.anomaly ? '#e74c3c' : '#2ecc71');
        doc.text(location.anomaly ? 'ANOMALY' : 'NORMAL', 150, y);
        
        y += 8;
    });
    
    // Mitigation recommendations
    doc.addPage();
    doc.setFontSize(16);
    doc.text('GPS Spoofing Mitigation Strategies', 14, 20);
    doc.setFontSize(12);
    
    let mitigationY = 30;
    
    const recommendations = [
        "1. Use multiple location sources (GPS, WiFi, cell towers) for verification",
        "2. Implement location data consistency checks",
        "3. Monitor for sudden jumps in location",
        "4. Verify location against known safe zones",
        "5. Use encrypted GPS signals when available",
        "6. Implement rate limiting on location changes",
        "7. Cross-validate with other sensors (accelerometer, gyroscope)"
    ];
    
    recommendations.forEach(rec => {
        doc.text(rec, 14, mitigationY);
        mitigationY += 8;
    });
    
    // Save the PDF
    doc.save(`CyberShield-GPS-Report-${new Date().toISOString().slice(0,10)}.pdf`);
}

// Export functions for HTML
window.testGpsData = testGpsData;
window.clearGpsData = clearGpsData;
window.zoomToLocation = zoomToLocation;
window.flagLocation = flagLocation;
window.generatePdfReport = generatePdfReport;