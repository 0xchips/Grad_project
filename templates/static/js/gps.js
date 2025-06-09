// GPS Monitoring System
let gpsData = [];
let map;
let accuracyChart;
let anomalies = 0;
let baseLat = 31.833360;
let baseLng = 35.890387;

document.addEventListener('DOMContentLoaded', function() {
    initMap();
    initAccuracyChart();
    loadGpsData();
    setInterval(fetchNewGpsData, 10000); // Fetch new data every 10s
    
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
    // Fetch real GPS data from the API
    fetch('/api/gps?hours=24')
        .then(response => response.json())
        .then(data => {
            // Clear existing data
            gpsData = [];
            anomalies = 0;
            
            // Process each GPS reading
            data.forEach(reading => {
                const processed = {
                    id: reading.id,
                    timestamp: new Date(reading.timestamp),
                    latitude: reading.latitude,
                    longitude: reading.longitude,
                    accuracy: reading.hdop ? reading.hdop * 10 : 5, // Convert HDOP to approximate accuracy in meters
                    satellites: reading.satellites || 0,
                    anomaly: reading.jamming_detected === 1,
                    flagged: false
                };
                
                addGpsData(processed);
            });
            
            updateGpsStats();
        })
        .catch(error => {
            console.error('Error fetching GPS data:', error);
            // If API call fails, show error message
            document.getElementById('gps-total-count').textContent = 'Error loading data';
        });
}

function fetchNewGpsData() {
    // Get the timestamp of our most recent data point
    let lastTimestamp = gpsData.length > 0 ? gpsData[0].timestamp.toISOString() : '';
    
    fetch(`/api/gps?hours=1`)
        .then(response => response.json())
        .then(data => {
            // Filter for only new data points
            const newData = data.filter(reading => {
                return !gpsData.some(existing => existing.id === reading.id);
            });
            
            // Process and add each new GPS reading
            newData.forEach(reading => {
                const processed = {
                    id: reading.id,
                    timestamp: new Date(reading.timestamp),
                    latitude: reading.latitude,
                    longitude: reading.longitude,
                    accuracy: reading.hdop ? reading.hdop * 10 : 5, // Convert HDOP to meters
                    satellites: reading.satellites || 0,
                    anomaly: reading.jamming_detected === 1,
                    flagged: false
                };
                
                addGpsData(processed);
            });
            
            if (newData.length > 0) {
                updateGpsStats();
            }
        })
        .catch(error => {
            console.error('Error fetching new GPS data:', error);
        });
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
        
        // Format timestamp to show both date and time
        const timestamp = reading.timestamp.toLocaleString();
        
        row.innerHTML = `
            <td>${timestamp}</td>
            <td>${reading.latitude.toFixed(6)}, ${reading.longitude.toFixed(6)}</td>
            <td>${reading.satellites || 'N/A'}</td>
            <td><span class="status ${reading.anomaly ? 'anomaly' : 'normal'}">${reading.anomaly ? 'Jamming Detected' : 'Normal'}</span></td>
            <td>
                <button class="btn-icon" onclick="zoomToLocation(${reading.latitude}, ${reading.longitude})"><i class="fas fa-search-location"></i></button>
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

// No longer need to simulate GPS data as we use real data from the API

function testGpsData() {
    const testReading = generateGpsReading();
    testReading.anomaly = true; // Force anomaly for testing
    addGpsData(testReading);
    showAlert('Test GPS anomaly added', 'success');
}

function clearGpsData() {
    if (!confirm('Are you sure you want to clear all GPS data from the database? This cannot be undone.')) {
        return;
    }
    
    fetch('/api/gps/clear', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear local data
            gpsData = [];
            anomalies = 0;
            
            // Clear map markers
            map.eachLayer(layer => {
                if (layer instanceof L.CircleMarker) {
                    map.removeLayer(layer);
                }
            });
            
            // Update UI
            document.querySelector('#gps-table tbody').innerHTML = '';
            updateGpsStats();
            showAlert(`GPS data cleared: ${data.deleted_count} records removed`, 'success');
        } else {
            showAlert('Error clearing GPS data: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error clearing GPS data:', error);
        showAlert('Error clearing GPS data', 'error');
    });
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
    doc.text('WiGuard GPS Threat Report', 105, 20, { align: 'center' });
    
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
    doc.save(`WiGuard-GPS-Report-${new Date().toISOString().slice(0,10)}.pdf`);
}

function showAlert(message, type = 'info') {
    // Create alert element if it doesn't exist
    let alertContainer = document.querySelector('.alert-container');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.className = 'alert-container';
        alertContainer.style.position = 'fixed';
        alertContainer.style.top = '20px';
        alertContainer.style.right = '20px';
        alertContainer.style.zIndex = '9999';
        document.body.appendChild(alertContainer);
    }
    
    // Create the alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.style.padding = '12px 20px';
    alert.style.margin = '10px 0';
    alert.style.borderRadius = '5px';
    alert.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
    alert.style.minWidth = '200px';
    
    // Set background color based on type
    switch (type) {
        case 'success':
            alert.style.backgroundColor = '#2ecc71';
            alert.style.color = 'white';
            break;
        case 'error':
            alert.style.backgroundColor = '#e74c3c';
            alert.style.color = 'white';
            break;
        case 'warning':
            alert.style.backgroundColor = '#f39c12';
            alert.style.color = 'white';
            break;
        default: // info
            alert.style.backgroundColor = '#3498db';
            alert.style.color = 'white';
    }
    
    alert.innerHTML = `
        <span>${message}</span>
        <button style="background: none; border: none; color: white; float: right; cursor: pointer;">×</button>
    `;
    
    // Add close button functionality
    alert.querySelector('button').addEventListener('click', () => {
        alert.remove();
    });
    
    // Add to container
    alertContainer.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

// Export functions for HTML
window.testGpsData = testGpsData;
window.clearGpsData = clearGpsData;
window.zoomToLocation = zoomToLocation;
window.flagLocation = flagLocation;
window.generatePdfReport = generatePdfReport;