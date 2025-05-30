// Deauthentication Attack Monitoring System
let deauthData = [];
let filteredDeauthData = [];
let currentPage = 1;
const itemsPerPage = 8;
let frequencyChart, targetsChart, modalChart;
let attackFrequency = Array(24).fill(0);
let targetNetworks = {};
let currentModalType = '';

document.addEventListener('DOMContentLoaded', function() {
    initDeauthCharts();
    loadDeauthData();
    
    // Check for new data more frequently (every 2 seconds)
    setInterval(loadDeauthData, 2000);
    
    // Add event listener for search input
    document.getElementById('deauth-search').addEventListener('input', function() {
        filterDeauthTable();
    });
    
    // Hide chart container initially if no data
    updateChartVisibility();
});

function initDeauthCharts() {
    // Safety check if elements don't exist
    const freqChartEl = document.getElementById('deauthFrequencyChart');
    const targetsChartEl = document.getElementById('deauthTargetsChart');
    const modalChartEl = document.getElementById('modalChart');
    
    if (!freqChartEl || !targetsChartEl) {
        console.error("Chart elements not found in the DOM");
        return;
    }
    
    // Destroy existing charts if they exist to prevent duplicates
    if (frequencyChart) {
        frequencyChart.destroy();
    }
    
    if (targetsChart) {
        targetsChart.destroy();
    }
    
    if (modalChart) {
        modalChart.destroy();
    }
    
    // Frequency Chart (smaller size)
    const freqCtx = freqChartEl.getContext('2d');
    frequencyChart = new Chart(freqCtx, {
        type: 'bar',
        data: {
            labels: Array(24).fill('').map((_, i) => `${i}:00`),
            datasets: [{
                label: 'Attacks per hour',
                data: attackFrequency,
                backgroundColor: 'rgba(231, 76, 60, 0.7)',
                borderColor: 'rgba(231, 76, 60, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: true
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        font: {
                            size: 10
                        }
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 0,
                        font: {
                            size: 8
                        },
                        callback: function(value, index) {
                            // Show only even hours to save space
                            return index % 4 === 0 ? value : '';
                        }
                    }
                }
            }
        }
    });

    // Targets Chart (smaller size)
    const targetsCtx = targetsChartEl.getContext('2d');
    targetsChart = new Chart(targetsCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#e74c3c', '#f39c12', '#3498db', '#9b59b6', '#2ecc71',
                    '#e84393', '#00cec9', '#fd79a8', '#0984e3', '#6c5ce7'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    left: 10,
                    right: 10,
                    top: 0,
                    bottom: 10
                }
            },
            plugins: {
                legend: {
                    position: 'right',
                    align: 'start',
                    labels: {
                        boxWidth: 10,
                        font: {
                            size: 9
                        },
                        padding: 5,
                        color: '#ecf0f1'
                    }
                },
                tooltip: {
                    bodyFont: {
                        size: 10
                    },
                    titleFont: {
                        size: 10
                    }
                }
            },
            cutout: '60%'
        }
    });
    
    // Initialize the modal chart (will be configured when opened)
    if (modalChartEl) {
        const modalCtx = modalChartEl.getContext('2d');
        modalChart = new Chart(modalCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
    
    console.log("Charts initialized successfully");
}

function loadDeauthData() {
    // Fetch data from API endpoint
    fetch('/api/deauth_logs')
        .then(response => response.json())
        .then(data => {
            // Check if we already have empty data and new data is also empty
            const wasEmpty = deauthData.length === 0;
            const isEmpty = data.length === 0;
            
            // Only process and update if there's actual data or if this is the first time with no data
            if (!isEmpty || !wasEmpty) {
                // Clear existing data
                deauthData = [];
                attackFrequency = Array(24).fill(0);
                targetNetworks = {};
                
                // Process the data
                data.forEach(attack => {
                    // Convert to our expected format
                    const attackObj = {
                        timestamp: new Date(attack.timestamp),
                        severity: attack.alert_type.includes('Deauth') ? 'critical' : 'warning',
                        count: attack.attack_count || 0,
                        attackerBssid: attack.attacker_bssid || 'Unknown',
                        attackerSsid: attack.attacker_ssid || 'Unknown',
                        targetBssid: attack.destination_bssid || 'Unknown',
                        targetSsid: attack.destination_ssid || 'Unknown',
                        active: true // Assume active for newly detected attacks
                    };
                    
                    // Add to our dataset
                    deauthData.push(attackObj);
                    
                    // Update frequency data
                    const hour = attackObj.timestamp.getHours();
                    attackFrequency[hour]++;
                    
                    // Update target networks data
                    if (!targetNetworks[attackObj.targetSsid]) {
                        targetNetworks[attackObj.targetSsid] = 0;
                    }
                    targetNetworks[attackObj.targetSsid]++;
                });
                
                // Sort by timestamp
                deauthData.sort((a, b) => b.timestamp - a.timestamp);
                
                // Update UI
                updateTargetsChart();
                updateDeauthTable();
                updateDeauthStats();
                updateChartVisibility();
                
                // Update frequency chart
                frequencyChart.data.datasets[0].data = attackFrequency;
                frequencyChart.update();
                
                console.log(`Loaded ${deauthData.length} deauth attacks from database`);
            }
        })
        .catch(error => {
            console.error('Error fetching deauth data:', error);
            showAlert('Failed to load deauthentication data from the server', 'error');
        });
}

function updateChartVisibility() {
    const chartContainer = document.getElementById('chart-container');
    
    // Always show charts, even when no data is available
    chartContainer.style.display = 'flex';
    
    // Update chart sizes based on window width - increased height values that match CSS
    const isMobile = window.innerWidth < 768;
    if (isMobile) {
        chartContainer.style.height = '220px'; // Mobile height
    } else {
        chartContainer.style.height = '300px'; // Desktop height - matches CSS
    }
    
    // If no data, ensure charts display placeholder data
    if (deauthData.length === 0) {
        updateChartsWithPlaceholderData();
    }
}

function updateTargetsChart() {
    // Sort networks by attack count and take top 10
    const sortedNetworks = Object.entries(targetNetworks)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
    
    targetsChart.data.labels = sortedNetworks.map(n => n[0]);
    targetsChart.data.datasets[0].data = sortedNetworks.map(n => n[1]);
    targetsChart.update();
}

function updateDeauthTable() {
    const tableBody = document.querySelector('#deauth-table tbody');
    tableBody.innerHTML = '';
    
    // Apply filtering if search term exists
    const searchTerm = document.getElementById('deauth-search').value.toLowerCase();
    filteredDeauthData = deauthData.filter(attack => 
        searchTerm === '' || 
        attack.attackerBssid.toLowerCase().includes(searchTerm) ||
        attack.targetBssid.toLowerCase().includes(searchTerm) ||
        attack.targetSsid.toLowerCase().includes(searchTerm)
    );
    
    // Pagination
    const startIndex = (currentPage - 1) * itemsPerPage;
    const paginatedData = filteredDeauthData.slice(startIndex, startIndex + itemsPerPage);
    
    // Populate table with well-organized data
    paginatedData.forEach((attack, index) => {
        const row = document.createElement('tr');
        // Add zebra striping for better organization
        row.className = `${attack.active ? 'active-attack' : ''} ${index % 2 === 0 ? 'even-row' : 'odd-row'}`;
        
        // Format timestamp nicely
        const formattedTime = attack.timestamp.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        row.innerHTML = `
            <td>${formattedTime}</td>
            <td class="bssid-cell">${attack.attackerBssid}</td>
            <td class="bssid-cell">${attack.targetBssid}</td>
            <td>${attack.targetSsid || 'Unknown'}</td>
            <td>
                <button class="btn-icon" onclick="blockDevice('${attack.attackerBssid}')" title="Block Attacker">
                    <i class="fas fa-ban"></i>
                </button>
                <button class="btn-icon" onclick="protectNetwork('${attack.targetBssid}')" title="Protect Network">
                    <i class="fas fa-shield-alt"></i>
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Update pagination info with more descriptive text
    const endIndex = Math.min(startIndex + itemsPerPage, filteredDeauthData.length);
    document.getElementById('deauth-showing').textContent = 
        filteredDeauthData.length > 0 ? `${startIndex + 1}-${endIndex}` : '0';
    document.getElementById('deauth-total').textContent = filteredDeauthData.length;
    document.getElementById('deauth-page').textContent = currentPage;
}

function updateDeauthStats() {
    const activeAttacks = deauthData.filter(a => a.active).length;
    
    document.getElementById('deauth-total-count').textContent = deauthData.length;
    document.getElementById('deauth-active-count').textContent = activeAttacks;
    
    // Calculate protected networks (simplified - in real app this would come from your protection system)
    const protectedCount = Object.keys(targetNetworks).length > 0 ? 
        Math.floor(Object.keys(targetNetworks).length / 3) : 0;
    document.getElementById('deauth-protected-count').textContent = protectedCount;
}

function testDeauthData() {
    // Make a test attack entry using the MySQL database via API
    const testData = {
        timestamp: new Date().toISOString(),
        alert_type: "Deauth Attack",
        attacker_bssid: "00:11:22:33:44:55",
        attacker_ssid: "TestAttacker",
        destination_bssid: "AA:BB:CC:DD:EE:FF",
        destination_ssid: "TestVictim",
        attack_count: 100
    };
    
    // Send test data to server
    fetch('/api/deauth_logs', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(testData)
    })
    .then(response => {
        if (response.ok) {
            showAlert('Test deauthentication attack added', 'success');
            // Reload data to show the new attack
            loadDeauthData();
        } else {
            showAlert('Failed to add test attack', 'error');
        }
    })
    .catch(error => {
        console.error('Error adding test attack:', error);
        showAlert('Error adding test attack', 'error');
    });
}

function clearDeauthData() {
    // Confirm before deleting all logs
    if (confirm("Are you sure you want to clear all deauthentication logs from the database? This action cannot be undone.")) {
        // Call the server endpoint to clear logs from the database
        fetch('/api/deauth_logs/clear', {
            method: 'DELETE'
        })
        .then(response => {
            if (response.ok) {
                // Clear local data
                deauthData = [];
                filteredDeauthData = [];
                attackFrequency = Array(24).fill(0);
                targetNetworks = {};
                currentPage = 1;
                
                // Update UI
                frequencyChart.data.datasets[0].data = attackFrequency;
                frequencyChart.update();
                
                targetsChart.data.labels = [];
                targetsChart.data.datasets[0].data = [];
                targetsChart.update();
                
                updateDeauthTable();
                updateDeauthStats();
                updateChartVisibility();
                
                console.log('All deauthentication logs cleared from database');
            } else {
                console.error('Failed to clear logs from database');
            }
        })
        .catch(error => {
            console.error('Error clearing logs:', error);
        });
    }
}

function filterDeauthTable() {
    currentPage = 1;
    updateDeauthTable();
}

function nextDeauthPage() {
    const totalPages = Math.ceil(filteredDeauthData.length / itemsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        updateDeauthTable();
    }
}

function prevDeauthPage() {
    if (currentPage > 1) {
        currentPage--;
        updateDeauthTable();
    }
}

function blockDevice(bssid) {
    // In a real app, this would send a request to your backend to block the device
    deauthData.forEach(attack => {
        if (attack.attackerBssid === bssid) {
            attack.active = false;
        }
    });
    showAlert(`Blocked device ${bssid}`, 'success');
    updateDeauthTable();
    updateDeauthStats();
}

function protectNetwork(bssid) {
    // In a real app, this would enable protection measures for the network
    showAlert(`Enabled protection for network ${bssid}`, 'success');
    updateDeauthStats();
}

// New function to expand chart into modal
function expandChart(type) {
    const modal = document.getElementById('chartModal');
    const modalTitle = document.getElementById('modal-title');
    
    // Configure modal based on chart type
    if (type === 'frequency') {
        modalTitle.textContent = 'Attack Frequency by Hour';
        modalChart.config.type = 'bar';
        modalChart.data = {
            labels: Array(24).fill('').map((_, i) => `${i}:00`),
            datasets: [{
                label: 'Attacks per hour',
                data: attackFrequency,
                backgroundColor: 'rgba(231, 76, 60, 0.7)',
                borderColor: 'rgba(231, 76, 60, 1)',
                borderWidth: 1
            }]
        };
        
        modalChart.options = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        };
    } else if (type === 'targets') {
        modalTitle.textContent = 'Target Networks';
        modalChart.config.type = 'doughnut';
        
        // Sort networks by attack count
        const sortedNetworks = Object.entries(targetNetworks)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);
        
        modalChart.data = {
            labels: sortedNetworks.map(n => n[0]),
            datasets: [{
                data: sortedNetworks.map(n => n[1]),
                backgroundColor: [
                    '#e74c3c', '#f39c12', '#3498db', '#9b59b6', '#2ecc71',
                    '#e84393', '#00cec9', '#fd79a8', '#0984e3', '#6c5ce7'
                ],
                borderWidth: 1
            }]
        };
        
        modalChart.options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        };
    }
    
    currentModalType = type;
    modalChart.update();
    
    // Show modal
    modal.classList.add('active');
}

// Close the chart modal
function closeModal() {
    const modal = document.getElementById('chartModal');
    modal.classList.remove('active');
}

// Function to show alert messages - now logging only, no UI alerts
function showAlert(message, type) {
    // Log to console instead of showing UI notifications
    if (type === 'error') {
        console.error(message);
    } else {
        console.log(`${type}: ${message}`);
    }
    
    // No UI notifications will appear
}

// Function to display placeholder data in charts when no real data is available
function updateChartsWithPlaceholderData() {
    // Reset charts to default state with clean placeholder data
    
    // Frequency chart - reset to zero but with slight variations for visual interest
    const placeholderFrequency = Array(24).fill(0).map(() => Math.floor(Math.random() * 3));
    
    // Restore original colors for frequency chart
    frequencyChart.data.datasets[0].data = placeholderFrequency;
    frequencyChart.data.datasets[0].backgroundColor = 'rgba(231, 76, 60, 0.7)';
    frequencyChart.data.datasets[0].borderColor = 'rgba(231, 76, 60, 1)';
    frequencyChart.update();
    
    // Targets chart - reset to default placeholder
    const placeholderNetworks = [
        { name: 'No Data Available', value: 1 }
    ];
    
    // Restore original colors for targets chart
    targetsChart.data.labels = placeholderNetworks.map(n => n.name);
    targetsChart.data.datasets[0].data = placeholderNetworks.map(n => n.value);
    targetsChart.data.datasets[0].backgroundColor = [
        '#e74c3c', '#f39c12', '#3498db', '#9b59b6', '#2ecc71'
    ];
    targetsChart.update();
}

function generatePdfReport(type) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    
    // Report title
    doc.setFontSize(20);
    doc.setTextColor(40);
    doc.text('CyberShield Deauthentication Attack Report', 105, 20, { align: 'center' });
    
    // Report metadata
    doc.setFontSize(12);
    doc.text(`Generated on: ${new Date().toLocaleString()}`, 14, 30);
    doc.text(`Total Attacks: ${deauthData.length}`, 14, 38);
    doc.text(`Active Attacks: ${deauthData.filter(a => a.active).length}`, 14, 46);
    doc.text(`Protected Networks: ${document.getElementById('deauth-protected-count').textContent}`, 14, 54);
    
    // Current threat assessment
    const threatLevel = deauthData.filter(a => a.active).length > 3 ? 'HIGH' :
                       deauthData.filter(a => a.active).length > 0 ? 'MODERATE' : 'LOW';
    const threatColor = threatLevel === 'HIGH' ? '#e74c3c' : 
                       threatLevel === 'MODERATE' ? '#f39c12' : '#2ecc71';
    
    doc.setTextColor(threatColor);
    doc.text(`Current Threat Level: ${threatLevel}`, 14, 62);
    doc.setTextColor(40);
    
    const recommendation = threatLevel === 'HIGH' ? 
        'Immediate action required. Multiple active deauthentication attacks detected.' :
        threatLevel === 'MODERATE' ? 
        'Potential threats detected. Monitor network activity closely.' :
        'Normal network activity. No significant threats detected.';
    
    doc.text(`Recommendation: ${recommendation}`, 14, 70);
    
    // Add charts
    doc.addPage();
    doc.setFontSize(16);
    doc.text('Attack Frequency by Hour', 14, 20);
    
    const freqChartImg = document.getElementById('deauthFrequencyChart').toDataURL('image/png');
    doc.addImage(freqChartImg, 'PNG', 14, 30, 180, 80);
    
    doc.setFontSize(16);
    doc.text('Most Targeted Networks', 14, 120);
    
    const targetsChartImg = document.getElementById('deauthTargetsChart').toDataURL('image/png');
    doc.addImage(targetsChartImg, 'PNG', 14, 130, 180, 80);
    
    // Detailed attack listing
    doc.addPage();
    doc.setFontSize(16);
    doc.text('Recent Deauthentication Attacks', 14, 20);
    
    // Table headers
    doc.setFontSize(12);
    doc.text('Timestamp', 14, 30);
    doc.text('Severity', 40, 30);
    doc.text('Count', 70, 30);
    doc.text('Attacker BSSID', 90, 30);
    doc.text('Target SSID', 140, 30);
    doc.text('Status', 180, 30);
    
    // Table rows (show last 50 attacks)
    let y = 40;
    deauthData.slice(0, 50).forEach(attack => {
        if (y > 270) {
            doc.addPage();
            y = 20;
        }
        
        // Color code severity
        doc.setTextColor(
            attack.severity === 'critical' ? '#e74c3c' : 
            attack.severity === 'warning' ? '#f39c12' : '#3498db'
        );
        doc.text(attack.timestamp.toLocaleTimeString(), 14, y);
        doc.text(attack.severity.toUpperCase(), 40, y);
        
        doc.setTextColor(40);
        doc.text(attack.count.toString(), 70, y);
        doc.text(attack.attackerBssid, 90, y);
        doc.text(attack.targetSsid, 140, y);
        
        // Color code status
        doc.setTextColor(attack.active ? '#e74c3c' : '#2ecc71');
        doc.text(attack.active ? 'ACTIVE' : 'INACTIVE', 180, y);
        
        y += 10;
    });
    
    // Protection recommendations
    doc.addPage();
    doc.setFontSize(16);
    doc.text('Deauthentication Attack Mitigation', 14, 20);
    doc.setFontSize(12);
    
    let yPos = 30;
    const recommendations = [
        "1. Enable Protected Management Frames (PMF) on your Wi-Fi networks",
        "2. Use WPA3 encryption instead of WPA2 where possible",
        "3. Monitor for unusual deauthentication frames",
        "4. Implement wireless intrusion detection/prevention systems",
        "5. Segment your wireless networks from critical infrastructure",
        "6. Regularly update firmware on all wireless access points",
        "7. Consider using 802.1X authentication for enterprise networks",
        "8. Monitor MAC addresses of devices sending excessive deauth frames",
        "9. Implement rate limiting for management frames",
        "10. Educate users about the risks of public Wi-Fi networks"
    ];
    
    recommendations.forEach(rec => {
        doc.text(rec, 14, yPos);
        yPos += 8;
    });
    
    // Save the PDF
    doc.save(`CyberShield-Deauth-Report-${new Date().toISOString().slice(0,10)}.pdf`);
}

// Export logs to JSON file
function exportDeauthLogs() {
    // Fetch the most current data first
    fetch('/api/deauth_logs')
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                showAlert('No logs to export', 'warning');
                return;
            }
            
            // Convert data to JSON string
            const jsonString = JSON.stringify(data, null, 2);
            
            // Create a Blob with the JSON data
            const blob = new Blob([jsonString], { type: 'application/json' });
            
            // Create a download link
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `deauth_logs_${new Date().toISOString().slice(0, 10)}.json`;
            
            // Trigger download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Clean up
            URL.revokeObjectURL(url);
            
            showAlert(`${data.length} logs exported successfully`, 'success');
        })
        .catch(error => {
            console.error('Error exporting logs:', error);
            showAlert('Failed to export logs', 'error');
        });
}

// Show the import modal
function showImportModal() {
    document.getElementById('importModal').classList.add('active');
}

// Close the import modal
function closeImportModal() {
    document.getElementById('importModal').classList.remove('active');
}

// Import logs from JSON file
function importDeauthLogs() {
    const fileInput = document.getElementById('importFile');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        showAlert('Please select a file to import', 'warning');
        return;
    }
    
    // Show the import status elements and disable the import button
    const importStatus = document.getElementById('importStatus');
    const importButton = document.getElementById('importButton');
    const importStatusText = document.getElementById('importStatusText');
    const importProgressBar = document.getElementById('importProgressBar');
    
    importStatus.style.display = 'block';
    importButton.disabled = true;
    
    const file = fileInput.files[0];
    const reader = new FileReader();
    
    reader.onload = function(event) {
        try {
            // Parse the JSON file
            const logsData = JSON.parse(event.target.result);
            
            if (!Array.isArray(logsData)) {
                throw new Error('Invalid format: Expected an array of logs');
            }
            
            // Count of successfully imported logs
            let successCount = 0;
            let totalLogs = logsData.length;
            let processedCount = 0;
            
            if (totalLogs === 0) {
                importStatusText.textContent = 'No logs found in the file';
                importProgressBar.style.width = '100%';
                
                setTimeout(() => {
                    importStatus.style.display = 'none';
                    importButton.disabled = false;
                    importProgressBar.style.width = '0%';
                    showAlert('No logs found in the file to import', 'warning');
                }, 1500);
                
                return;
            }
            
            importStatusText.textContent = `Importing logs... 0/${totalLogs}`;
            
            // Import each log entry
            logsData.forEach((log, index) => {
                // Format the log data
                const logEntry = {
                    timestamp: log.timestamp || new Date().toISOString(),
                    alert_type: log.alert_type || 'Deauth Attack',
                    attacker_bssid: log.attacker_bssid || log.source_bssid || 'Unknown',
                    attacker_ssid: log.attacker_ssid || log.source_ssid || 'Unknown',
                    destination_bssid: log.destination_bssid || log.target_bssid || 'Unknown',
                    destination_ssid: log.destination_ssid || log.target_ssid || 'Unknown',
                    attack_count: log.attack_count || log.count || 0
                };
                
                // Send the data to the server
                fetch('/api/deauth_logs', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(logEntry)
                })
                .then(response => {
                    processedCount++;
                    if (response.ok) {
                        successCount++;
                    }
                    
                    // Update progress bar and status text
                    const progress = Math.round((processedCount / totalLogs) * 100);
                    importProgressBar.style.width = `${progress}%`;
                    importStatusText.textContent = `Importing logs... ${processedCount}/${totalLogs}`;
                    
                    // When all logs have been processed
                    if (processedCount === totalLogs) {
                        importStatusText.textContent = 'Import complete!';
                        
                        setTimeout(() => {
                            // Reset the import modal
                            importStatus.style.display = 'none';
                            importButton.disabled = false;
                            importProgressBar.style.width = '0%';
                            
                            // Clear the file input
                            fileInput.value = '';
                            
                            // Show success message
                            showAlert(`Successfully imported ${successCount} of ${totalLogs} logs`, 'success');
                            
                            // Load the imported data with a small delay to ensure server processes all entries
                            setTimeout(() => {
                                // Add a special class to the table to highlight it temporarily
                                const tableElement = document.getElementById('deauth-table');
                                if (tableElement) {
                                    tableElement.id = 'importedDataHighlight';
                                    setTimeout(() => {
                                        tableElement.id = 'deauth-table';
                                    }, 2000);
                                }
                                
                                // Reload data to show the imported logs
                                loadDeauthData();
                                
                                // Close the import modal
                                closeImportModal();
                            }, 500);
                        }, 1000);
                    }
                })
                .catch(error => {
                    console.error('Error importing log:', error);
                    processedCount++;
                    
                    // Update progress bar
                    const progress = Math.round((processedCount / totalLogs) * 100);
                    importProgressBar.style.width = `${progress}%`;
                    importStatusText.textContent = `Importing logs... ${processedCount}/${totalLogs}`;
                    
                    // Check if all logs have been processed
                    if (processedCount === totalLogs) {
                        importStatusText.textContent = 'Import complete with some errors';
                        
                        setTimeout(() => {
                            // Reset the import modal
                            importStatus.style.display = 'none';
                            importButton.disabled = false;
                            importProgressBar.style.width = '0%';
                            
                            // Clear the file input
                            fileInput.value = '';
                            
                            // Show status message
                            showAlert(`Successfully imported ${successCount} of ${totalLogs} logs`, 'info');
                            
                            // Reload data for any successful imports
                            if (successCount > 0) {
                                // Add a special class to the table to highlight it temporarily
                                const tableElement = document.getElementById('deauth-table');
                                if (tableElement) {
                                    tableElement.id = 'importedDataHighlight';
                                    setTimeout(() => {
                                        tableElement.id = 'deauth-table';
                                    }, 2000);
                                }
                                
                                // Reload data to show the imported logs
                                loadDeauthData();
                            }
                            
                            // Close the import modal
                            closeImportModal();
                        }, 1000);
                    }
                });
            });
        } catch (error) {
            console.error('Error parsing import file:', error);
            showAlert(`Error importing file: ${error.message}`, 'error');
            
            // Reset the import modal
            importStatus.style.display = 'none';
            importButton.disabled = false;
            importProgressBar.style.width = '0%';
        }
    };
    
    reader.onerror = function(event) {
        console.error('Error reading file:', event);
        showAlert('Error reading the import file', 'error');
        
        // Reset the import modal
        importStatus.style.display = 'none';
        importButton.disabled = false;
        importProgressBar.style.width = '0%';
    };
    
    reader.readAsText(file);
}