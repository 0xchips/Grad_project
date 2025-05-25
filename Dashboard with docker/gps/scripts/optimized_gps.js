// GPS Monitoring System with Optimized Data Fetching
let gpsData = [];
let map;
let accuracyChart;
let anomalies = 0;
let baseLat = 31.833360;
let baseLng = 35.890387;
let lastId = null;

document.addEventListener('DOMContentLoaded', function() {
    initMap();
    initAccuracyChart();
    loadGpsData();
    
    // Use faster polling interval (3 seconds) with optimized endpoint
    setInterval(fetchNewGpsDataFast, 3000);
    
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
            animation: {
                duration: 500 // Faster animations
            },
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
    // Fetch real GPS data from the optimized API endpoint
    fetch('/api/gps/fast')
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
            
            // Update last ID for efficient polling
            if (data.length > 0) {
                lastId = data[0].id;
            }
            
            updateGpsStats();
            
            // If any anomalies are present, focus the map on the most recent one
            const recentAnomaly = gpsData.find(reading => reading.anomaly);
            if (recentAnomaly) {
                map.setView([recentAnomaly.latitude, recentAnomaly.longitude], 14);
            } else if (gpsData.length > 0) {
                map.setView([gpsData[0].latitude, gpsData[0].longitude], 13);
            }
        })
        .catch(error => {
            console.error('Error fetching GPS data:', error);
            document.getElementById('gps-total-count').textContent = 'Error loading data';
        });
    
    // Also fetch statistics separately for efficiency
    fetchGpsStats();
}

function fetchNewGpsDataFast() {
    const url = lastId ? `/api/gps/fast?last_id=${lastId}` : '/api/gps/fast';
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            // Process and add each new GPS reading
            if (data.length > 0) {
                data.forEach(reading => {
                    const processed = {
                        id: reading.id,
                        timestamp: new Date(reading.timestamp),
                        latitude: reading.latitude,
                        longitude: reading.longitude,
                        accuracy: reading.hdop ? reading.hdop * 10 : 5,
                        satellites: reading.satellites || 0,
                        anomaly: reading.jamming_detected === 1,
                        flagged: false
                    };
                    
                    addGpsData(processed);
                });
                
                // Update last ID for next poll
                lastId = data[0].id;
                
                // Get updated stats
                fetchGpsStats();
            }
        })
        .catch(error => {
            console.error('Error fetching new GPS data:', error);
        });
}

function fetchGpsStats() {
    // Get lightweight statistics separately
    fetch('/api/gps/stats')
        .then(response => response.json())
        .then(stats => {
            document.getElementById('gps-total-count').textContent = stats.total;
            document.getElementById('gps-anomalies-count').textContent = stats.anomalies;
        })
        .catch(error => {
            console.error('Error fetching GPS stats:', error);
        });
}

function addGpsData(reading) {
    gpsData.unshift(reading);
    if (reading.anomaly) anomalies++;
    
    // Update map - only if it's a recent reading (within the last hour)
    const oneHourAgo = new Date();
    oneHourAgo.setHours(oneHourAgo.getHours() - 1);
    
    if (reading.timestamp > oneHourAgo) {
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
            Satellites: ${reading.satellites}<br>
            Status: ${reading.anomaly ? '<span style="color:#e74c3c">Jamming Detected</span>' : 'Normal'}
        `);
        
        // Auto-focus map on anomalies
        if (reading.anomaly) {
            map.setView([reading.latitude, reading.longitude], 14);
        }
    }
    
    // Update table but limit to 100 entries for performance
    if (gpsData.length <= 100) {
        updateGpsTable();
    } else {
        // If more than 100 entries, only update visible rows
        const tableBody = document.querySelector('#gps-table tbody');
        if (tableBody.children.length < 100) {
            updateGpsTable();
        } else {
            // Just update anomaly count and chart
            updateGpsStats();
        }
    }
    
    // Update chart
    updateAccuracyChart(reading.accuracy);
}

function updateGpsTable() {
    const tableBody = document.querySelector('#gps-table tbody');
    tableBody.innerHTML = '';
    
    // Sort by timestamp (newest first)
    const sortedData = [...gpsData].sort((a, b) => b.timestamp - a.timestamp);
    
    // Add rows (limit to 100 for performance)
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
    accuracyChart.update('none'); // Use 'none' mode for performance
}

function updateGpsStats() {
    document.getElementById('gps-locations-count').textContent = gpsData.length;
    document.getElementById('gps-anomalies-count').textContent = anomalies;
    
    // Calculate average accuracy
    const avgAccuracy = gpsData.reduce((sum, reading) => {
        return sum + reading.accuracy;
    }, 0) / Math.max(1, gpsData.length); // Avoid division by zero
    
    document.getElementById('gps-accuracy-avg').textContent = `${Math.round(avgAccuracy)}m`;
}

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

function generateGpsReading() {
    // This is just for testing
    return {
        id: Math.random().toString(36).substring(2, 15),
        timestamp: new Date(),
        latitude: baseLat + (Math.random() - 0.5) * 0.01,
        longitude: baseLng + (Math.random() - 0.5) * 0.01,
        accuracy: Math.random() * 20 + 1,
        satellites: Math.floor(Math.random() * 12),
        anomaly: false,
        flagged: false
    };
}

function showAlert(message, type = 'info') {
    // Create alert container if it doesn't exist
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
