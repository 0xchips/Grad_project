function getSeverityLevel(severityText) {
    switch (severityText.toLowerCase()) {
        case 'critical': return 4;
        case 'high': return 3;
        case 'medium': return 2;
        case 'low': return 1;
        case 'info': return 0;
        default: return 0;
    }
}

function showNessusResultsModal(results, scannerType = 'unknown') {
    // Close progress modal
    closeNessusProgressModal();
    
    // Set default values for missing results
    const defaultResults = {
        critical: 0,
        high: 0, 
        medium: 0,
        low: 0,
        info: 0,
        total_hosts: 0,
        total_vulnerabilities: 0,
        scan_status: 'Unknown',
        vulnerabilities: [],
        hosts_scanned: 0,
        hosts_up: 0,
        services: [],
        additional_findings: {},
        tools_used: []
    };
    
    // Merge default values with actual results
    const displayResults = {...defaultResults, ...results};
    
    // Handle special case for partial fallback scanner results
    if (scannerType === 'fallback' && results.status && results.status.includes('partial')) {
        displayResults.scan_status = 'Partial Results Available';
    }
    
    // Create results modal
    const modal = document.createElement('div');
    modal.id = 'nessusResultsModal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content nessus-results-modal">
            <div class="modal-header">
                <h3><i class="fas fa-chart-bar"></i> Vulnerability Scan Results <span class="scanner-badge ${scannerType}">${scannerType}</span></h3>
                <span class="close" onclick="closeNessusResultsModal()">&times;</span>
            </div>
            <div class="modal-body">
                <div class="results-summary">
                    <div class="summary-cards">
                        <div class="summary-card critical">
                            <div class="card-content">
                                <div class="card-number">${displayResults.critical || 0}</div>
                                <div class="card-label">Critical</div>
                            </div>
                        </div>
                        <div class="summary-card high">
                            <div class="card-content">
                                <div class="card-number">${displayResults.high || 0}</div>
                                <div class="card-label">High</div>
                            </div>
                        </div>
                        <div class="summary-card medium">
                            <div class="card-content">
                                <div class="card-number">${displayResults.medium || 0}</div>
                                <div class="card-label">Medium</div>
                            </div>
                        </div>
                        <div class="summary-card low">
                            <div class="card-content">
                                <div class="card-number">${displayResults.low || 0}</div>
                                <div class="card-label">Low</div>
                            </div>
                        </div>
                        <div class="summary-card info">
                            <div class="card-content">
                                <div class="card-number">${displayResults.info || 0}</div>
                                <div class="card-label">Info</div>
                            </div>
                        </div>
                    </div>
                    <div class="scan-summary">
                        <p><strong>Scanner Type:</strong> ${scannerType.charAt(0).toUpperCase() + scannerType.slice(1)}</p>
                        <p><strong>Total Hosts Scanned:</strong> ${displayResults.hosts_scanned || displayResults.total_hosts || 0}</p>
                        <p><strong>Hosts Found:</strong> ${displayResults.hosts_up || 0}</p>
                        <p><strong>Total Vulnerabilities:</strong> ${displayResults.total_vulnerabilities || 0}</p>
                        <p><strong>Scan Status:</strong> ${displayResults.scan_status || 'Unknown'}</p>
                        ${scannerType === 'fallback' && displayResults.tools_used && displayResults.tools_used.length > 0 ? 
                          `<p><strong>Tools Used:</strong> ${displayResults.tools_used.join(', ')}</p>` : ''}
                        ${scannerType === 'fallback' && displayResults.status ? 
                          `<p><strong>Details:</strong> ${displayResults.status}</p>` : ''}
                    </div>
                </div>
                
                ${displayResults.vulnerabilities && displayResults.vulnerabilities.length > 0 ? `
                    <div class="vulnerabilities-table">
                        <h4>Top Vulnerabilities</h4>
                        <table class="results-table">
                            <thead>
                                <tr>
                                    <th>Severity</th>
                                    <th>${scannerType === 'fallback' ? 'Finding' : 'Plugin Name'}</th>
                                    <th>${scannerType === 'fallback' ? 'Host' : 'Count'}</th>
                                    ${scannerType === 'fallback' ? '<th>Source</th>' : ''}
                                </tr>
                            </thead>
                            <tbody>
                                ${displayResults.vulnerabilities.slice(0, 10).map(vuln => `
                                    <tr>
                                        <td><span class="severity severity-${typeof vuln.severity === 'string' ? 
                                            getSeverityLevel(vuln.severity) : (vuln.severity || 0)}">${
                                            typeof vuln.severity === 'string' ? 
                                            vuln.severity.charAt(0).toUpperCase() + vuln.severity.slice(1) : 
                                            getSeverityText(vuln.severity)
                                        }</span></td>
                                        <td>${vuln.plugin_name || vuln.description || 'Unknown'}</td>
                                        <td>${vuln.count || vuln.host || 'N/A'}</td>
                                        ${scannerType === 'fallback' ? `<td>${vuln.source || 'N/A'}</td>` : ''}
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                        ${displayResults.vulnerabilities.length > 10 ? 
                          `<p class="table-note">Showing 10 of ${displayResults.vulnerabilities.length} vulnerabilities</p>` : ''}
                    </div>
                ` : '<p>No vulnerabilities found in this scan.</p>'}
                
                ${scannerType === 'fallback' && displayResults.services && displayResults.services.length > 0 ? `
                    <div class="services-table">
                        <h4>Open Services</h4>
                        <table class="results-table">
                            <thead>
                                <tr>
                                    <th>Host</th>
                                    <th>Port</th>
                                    <th>Service</th>
                                    <th>Version</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${displayResults.services.slice(0, 10).map(service => `
                                    <tr>
                                        <td>${service.host || 'Unknown'}</td>
                                        <td>${service.port || 'Unknown'}</td>
                                        <td>${service.name || 'Unknown'}</td>
                                        <td>${service.version || 'Unknown'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                        ${displayResults.services.length > 10 ? 
                          `<p class="table-note">Showing 10 of ${displayResults.services.length} services</p>` : ''}
                    </div>
                ` : ''}
            </div>
            <div class="modal-footer">
                <button class="btn btn-primary" onclick="exportNessusReport()">
                    <i class="fas fa-download"></i> Export Report
                </button>
                <button class="btn btn-secondary" onclick="closeNessusResultsModal()">
                    <i class="fas fa-times"></i> Close
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.style.display = 'block';
    
    // Close modal when clicking outside
    modal.onclick = function(event) {
        if (event.target === modal) {
            closeNessusResultsModal();
        }
    };
}
