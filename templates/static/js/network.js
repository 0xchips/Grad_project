// Network Threat Monitoring System
let networkData = [];
let attackTypes = {
    'Port Scan': 0,
    'DDoS': 0,
    'MITM': 0,
    'SQL Injection': 0,
    'DNS Spoofing': 0,
    'Zero-Day': 0,
    'Phishing': 0
};
let severityCounts = {
    high: 0,
    medium: 0,
    low: 0
};
let blockedIPs = [];
let attackChart, severityChart;
let portScanIPs = {};
let requestRates = {};

document.addEventListener('DOMContentLoaded', function() {
    initNetworkCharts();
    loadNetworkData();
    setInterval(simulateNetworkData, 10000); // Simulate new data every 10s
    setInterval(updateNetworkStats, 2000); // Update stats every 2s
});

function initNetworkCharts() {
    // Attack Types Chart
    const attackCtx = document.getElementById('networkAttackChart').getContext('2d');
    attackChart = new Chart(attackCtx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(attackTypes),
            datasets: [{
                data: Object.values(attackTypes),
                backgroundColor: [
                    '#3498db',
                    '#e74c3c',
                    '#f39c12',
                    '#9b59b6',
                    '#2ecc71',
                    '#e84393',
                    '#00cec9'
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

    // Severity Chart
    const severityCtx = document.getElementById('networkSeverityChart').getContext('2d');
    severityChart = new Chart(severityCtx, {
        type: 'bar',
        data: {
            labels: ['High', 'Medium', 'Low'],
            datasets: [{
                label: 'Severity Count',
                data: Object.values(severityCounts),
                backgroundColor: [
                    'rgba(231, 76, 60, 0.7)',
                    'rgba(243, 156, 18, 0.7)',
                    'rgba(46, 204, 113, 0.7)'
                ],
                borderColor: [
                    'rgba(231, 76, 60, 1)',
                    'rgba(243, 156, 18, 1)',
                    'rgba(46, 204, 113, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function loadNetworkData() {
    // Simulate loading data
    setTimeout(() => {
        for (let i = 0; i < 20; i++) {
            addNetworkEvent(generateNetworkEvent());
        }
        updateNetworkStats();
    }, 1000);
}

function generateNetworkEvent() {
    const types = Object.keys(attackTypes);
    let type = types[Math.floor(Math.random() * types.length)];
    let severity = Math.random() > 0.8 ? 'high' : Math.random() > 0.5 ? 'medium' : 'low';
    const sourceIP = `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`;
    
    // Create base event
    const event = {
        timestamp: new Date(),
        sourceIP: sourceIP,
        type: type,
        severity: severity,
        blocked: blockedIPs.includes(sourceIP)
    };
    
    // Analyze the event for attack patterns
    return analyzeNetworkEvent(event);
}

function analyzeNetworkEvent(event) {
    // Check for port scanning behavior
    if (isPortScan(event)) {
        event.type = 'Port Scan';
        event.severity = 'high';
    }
    
    // Check for DDoS patterns
    if (isDDoSAttempt(event)) {
        event.type = 'DDoS';
        event.severity = 'high';
    }
    
    return event;
}

function isPortScan(event) {
    const scanThreshold = 5; // Number of ports to trigger detection
    
    if (!portScanIPs[event.sourceIP]) {
        portScanIPs[event.sourceIP] = {
            ports: new Set(),
            lastScanTime: Date.now()
        };
    }
    
    // Simulate port access (in real system, you'd get this from event data)
    const randomPort = Math.floor(Math.random() * 65535);
    portScanIPs[event.sourceIP].ports.add(randomPort);
    
    // Reset if more than 1 minute has passed
    if (Date.now() - portScanIPs[event.sourceIP].lastScanTime > 60000) {
        portScanIPs[event.sourceIP].ports.clear();
        portScanIPs[event.sourceIP].lastScanTime = Date.now();
        return false;
    }
    
    return portScanIPs[event.sourceIP].ports.size > scanThreshold;
}

function isDDoSAttempt(event) {
    const ddosThreshold = 50; // Requests per second
    
    if (!requestRates[event.sourceIP]) {
        requestRates[event.sourceIP] = {
            count: 0,
            lastTime: Date.now()
        };
    }
    
    requestRates[event.sourceIP].count++;
    
    // Reset count if more than 1 second has passed
    if (Date.now() - requestRates[event.sourceIP].lastTime > 1000) {
        requestRates[event.sourceIP].count = 1;
        requestRates[event.sourceIP].lastTime = Date.now();
        return false;
    }
    
    return requestRates[event.sourceIP].count > ddosThreshold;
}

function addNetworkEvent(event) {
    networkData.unshift(event);
    
    // Only count if not blocked
    if (!event.blocked) {
        attackTypes[event.type]++;
        severityCounts[event.severity]++;
    }
    
    // Update table (limit to 100 entries)
    if (networkData.length > 100) {
        const removedEvent = networkData.pop();
        // Decrement counts if the removed event wasn't blocked
        if (!removedEvent.blocked) {
            attackTypes[removedEvent.type]--;
            severityCounts[removedEvent.severity]--;
        }
    }
    
    updateNetworkTable(event);
    updateNetworkStats();
}

function updateNetworkTable(event) {
    const tableBody = document.querySelector('#network-table tbody');
    
    // Create new row
    const row = document.createElement('tr');
    row.className = `severity-${event.severity} ${event.blocked ? 'blocked' : ''}`;
    
    row.innerHTML = `
        <td>${event.timestamp.toLocaleTimeString()}</td>
        <td>${event.sourceIP}</td>
        <td>${event.type}</td>
        <td><span class="severity-badge ${event.severity}">${event.severity.toUpperCase()}</span></td>
        <td>${event.blocked ? 'BLOCKED' : 'ACTIVE'}</td>
        <td>
            <button class="btn-block" data-ip="${event.sourceIP}">
                ${event.blocked ? 'Unblock' : 'Block'}
            </button>
        </td>
    `;
    
    // Add to top of table
    if (tableBody.firstChild) {
        tableBody.insertBefore(row, tableBody.firstChild);
    } else {
        tableBody.appendChild(row);
    }
    
    // Remove excess rows
    while (tableBody.children.length > 100) {
        tableBody.removeChild(tableBody.lastChild);
    }
    
    // Add event listener to block button
    row.querySelector('.btn-block').addEventListener('click', function() {
        toggleBlockIP(this.dataset.ip);
    });
}

function toggleBlockIP(ip) {
    const index = blockedIPs.indexOf(ip);
    if (index === -1) {
        // Block IP
        blockedIPs.push(ip);
        // Update all events with this IP
        networkData.forEach(event => {
            if (event.sourceIP === ip) {
                event.blocked = true;
                // Remove from counts if previously unblocked
                if (!event.blocked) {
                    attackTypes[event.type]--;
                    severityCounts[event.severity]--;
                }
            }
        });
    } else {
        // Unblock IP
        blockedIPs.splice(index, 1);
        // Update all events with this IP
        networkData.forEach(event => {
            if (event.sourceIP === ip) {
                event.blocked = false;
                // Add back to counts
                attackTypes[event.type]++;
                severityCounts[event.severity]++;
            }
        });
    }
    
    // Update the table to reflect changes
    document.querySelectorAll('#network-table tbody tr').forEach(row => {
        const rowIP = row.querySelector('.btn-block').dataset.ip;
        if (rowIP === ip) {
            const btn = row.querySelector('.btn-block');
            btn.textContent = blockedIPs.includes(ip) ? 'Unblock' : 'Block';
            row.className = `severity-${networkData.find(e => e.sourceIP === ip).severity} ${blockedIPs.includes(ip) ? 'blocked' : ''}`;
            row.cells[4].textContent = blockedIPs.includes(ip) ? 'BLOCKED' : 'ACTIVE';
        }
    });
    
    updateNetworkStats();
}

function simulateNetworkData() {
    // Generate 1-3 new events
    const numEvents = Math.floor(Math.random() * 3) + 1;
    for (let i = 0; i < numEvents; i++) {
        addNetworkEvent(generateNetworkEvent());
    }
}

function updateNetworkStats() {

 


    // Update charts
    attackChart.data.datasets[0].data = Object.values(attackTypes);
    attackChart.update();
    
    severityChart.data.datasets[0].data = Object.values(severityCounts);
    severityChart.update();
    
    // Update summary stats
    document.getElementById('network-events-count').textContent = networkData.length;
    document.getElementById('network-critical-count').textContent = severityCounts.high;
    document.getElementById('network-blocked-count').textContent = blockedIPs.length;
}

function calculateThreatLevel() {
    const totalHigh = severityCounts.high;
    const totalMedium = severityCounts.medium;
    
    if (totalHigh > 5 || (totalHigh > 3 && totalMedium > 10)) {
        return {
            level: 'CRITICAL',
            class: 'critical',
            description: 'Immediate action required - multiple high severity threats detected'
        };
    } else if (totalHigh > 2 || totalMedium > 5) {
        return {
            level: 'HIGH',
            class: 'high',
            description: 'Elevated threat level - increased security measures recommended'
        };
    } else if (totalMedium > 2 || networkData.length > 15) {
        return {
            level: 'MODERATE',
            class: 'moderate',
            description: 'Potential threats detected - monitoring recommended'
        };
    } else {
        return {
            level: 'LOW',
            class: 'low',
            description: 'Normal network activity - no significant threats detected'
        };
    }
}

function generatePdfReport(type) {
    // Initialize the PDF
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    
    // Report title
    doc.setFontSize(20);
    doc.setTextColor(40);
    doc.text('WiGuard Network Threat Report', 105, 20, { align: 'center' });
    
    // Report metadata
    doc.setFontSize(12);
    doc.text(`Generated on: ${new Date().toLocaleString()}`, 14, 30);
    doc.text(`Total Events: ${networkData.length}`, 14, 38);
    doc.text(`Critical Attacks: ${severityCounts.high}`, 14, 46);
    doc.text(`Blocked IPs: ${blockedIPs.length}`, 14, 54);
    
    // Current threat level
    const threatLevel = calculateThreatLevel();
    doc.setTextColor(threatLevel.class === 'critical' ? '#e74c3c' : 
                     threatLevel.class === 'high' ? '#f39c12' : 
                     threatLevel.class === 'moderate' ? '#3498db' : '#2ecc71');
    doc.text(`Current Threat Level: ${threatLevel.level}`, 14, 62);
    doc.setTextColor(40);
    doc.text(`Description: ${threatLevel.description}`, 14, 70);
    
    // Add a line separator
    doc.line(14, 76, 196, 76);
    
    // Attack type distribution
    doc.setFontSize(16);
    doc.text('Attack Type Distribution', 14, 86);
    
    // Convert chart to image and add to PDF
    const attackChartCanvas = document.getElementById('networkAttackChart');
    const attackChartImg = attackChartCanvas.toDataURL('image/png');
    doc.addImage(attackChartImg, 'PNG', 14, 90, 80, 60);
    
    // Severity distribution
    doc.setFontSize(16);
    doc.text('Attack Severity Distribution', 105, 86);
    
    const severityChartCanvas = document.getElementById('networkSeverityChart');
    const severityChartImg = severityChartCanvas.toDataURL('image/png');
    doc.addImage(severityChartImg, 'PNG', 105, 90, 80, 60);
    
    // Detailed event listing
    doc.addPage();
    doc.setFontSize(16);
    doc.text('Detailed Network Events', 14, 20);
    
    // Table headers
    doc.setFontSize(12);
    doc.text('Timestamp', 14, 30);
    doc.text('Source IP', 50, 30);
    doc.text('Event Type', 90, 30);
    doc.text('Severity', 140, 30);
    doc.text('Status', 170, 30);
    
    // Table rows
    let y = 38;
    networkData.slice(0, 50).forEach(event => { // Limit to 50 most recent events
        if (y > 270) {
            doc.addPage();
            y = 20;
        }
        
        doc.setTextColor(40);
        doc.text(event.timestamp.toLocaleString(), 14, y);
        doc.text(event.sourceIP, 50, y);
        doc.text(event.type, 90, y);
        
        // Color code severity
        doc.setTextColor(
            event.severity === 'high' ? '#e74c3c' : 
            event.severity === 'medium' ? '#f39c12' : '#2ecc71'
        );
        doc.text(event.severity.toUpperCase(), 140, y);
        
        doc.setTextColor(event.blocked ? '#2ecc71' : '#e74c3c');
        doc.text(event.blocked ? 'BLOCKED' : 'ACTIVE', 170, y);
        
        y += 8;
    });
    
    // Mitigation recommendations
    doc.addPage();
    doc.setFontSize(16);
    doc.text('Recommended Mitigation Strategies', 14, 20);
    doc.setFontSize(12);
    
    let mitigationY = 30;
    
    // General recommendations
    const generalRecommendations = [
        "1. Ensure all network devices have the latest firmware/software updates",
        "2. Implement a Web Application Firewall (WAF) for HTTP/HTTPS traffic",
        "3. Regularly review and update firewall rules",
        "4. Monitor network traffic for unusual patterns",
        "5. Implement intrusion detection/prevention systems (IDS/IPS)"
    ];
    
    generalRecommendations.forEach(rec => {
        doc.text(rec, 14, mitigationY);
        mitigationY += 8;
    });
    
    // Specific recommendations based on attack types
    mitigationY += 8;
    doc.setFontSize(14);
    doc.text('Attack-Specific Recommendations:', 14, mitigationY);
    mitigationY += 10;
    doc.setFontSize(12);
    
    const attackRecommendations = {
        'Port Scan': [
            "- Implement port knocking or silent drop rules",
            "- Rate limit connection attempts per IP",
            "- Use a firewall to close unnecessary ports"
        ],
        'DDoS': [
            "- Implement DDoS protection services (e.g., Cloudflare)",
            "- Configure rate limiting on your network devices",
            "- Consider using Anycast for critical services"
        ],
        'MITM': [
            "- Enforce HTTPS with HSTS headers",
            "- Implement certificate pinning",
            "- Use VPNs for internal communications"
        ],
        'SQL Injection': [
            "- Use prepared statements and parameterized queries",
            "- Implement input validation on all form fields",
            "- Regularly update database software"
        ],
        'DNS Spoofing': [
            "- Implement DNSSEC",
            "- Use DNS over HTTPS/TLS",
            "- Monitor DNS queries for anomalies"
        ],
        'Zero-Day': [
            "- Implement behavior-based detection systems",
            "- Segment your network to limit blast radius",
            "- Maintain offline backups"
        ],
        'Phishing': [
            "- Conduct regular employee security training",
            "- Implement email filtering solutions",
            "- Use DMARC, DKIM, and SPF records"
        ]
    };
    
    // Only show recommendations for attack types we've actually seen
    Object.keys(attackTypes).forEach(type => {
        if (attackTypes[type] > 0 && attackRecommendations[type]) {
            doc.setFontSize(12);
            doc.setTextColor(40);
            doc.text(`${type}:`, 14, mitigationY);
            mitigationY += 8;
            
            doc.setFontSize(10);
            attackRecommendations[type].forEach(rec => {
                doc.text(rec, 20, mitigationY);
                mitigationY += 6;
            });
            mitigationY += 4;
        }
    });
    
    // Save the PDF
    doc.save(`WiGuard-Network-Report-${new Date().toISOString().slice(0,10)}.pdf`);
}

function testNetworkData() {
    // Simulate a critical attack
    const criticalEvent = {
        timestamp: new Date(),
        sourceIP: `192.168.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
        type: 'DDoS',
        severity: 'high',
        blocked: false
    };
    addNetworkEvent(criticalEvent);
}

function clearNetworkData() {
    networkData = [];
    blockedIPs = [];
    
    // Reset counters
    Object.keys(attackTypes).forEach(key => attackTypes[key] = 0);
    Object.keys(severityCounts).forEach(key => severityCounts[key] = 0);
    
    // Clear table
    document.querySelector('#network-table tbody').innerHTML = '';
    
    // Reset detection systems
    portScanIPs = {};
    requestRates = {};
    
    updateNetworkStats();
}