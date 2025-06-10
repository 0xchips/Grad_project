// NIDS Dashboard JavaScript
// Handles real-time updates, charts, and interactions for the Network Intrusion Detection System

class NIDSDashboard {
    constructor() {
        this.charts = {};
        this.refreshInterval = 30000; // 30 seconds
        this.refreshTimer = null;
        this.geoipCache = new Map();
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.loadInitialData();
        this.startAutoRefresh();
    }
    
    setupEventListeners() {
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadAllData();
        });
        
        // Apply filters button
        document.getElementById('applyFiltersBtn').addEventListener('click', () => {
            this.loadAlerts();
        });
        
        // Clear alerts button
        document.getElementById('clearAlertsBtn').addEventListener('click', () => {
            this.clearOldAlerts();
        });
        
        // Auto-refresh on filter changes
        ['severityFilter', 'protocolFilter', 'timeRangeFilter'].forEach(id => {
            document.getElementById(id).addEventListener('change', () => {
                this.loadAlerts();
            });
        });
        
        // Source IP filter with debounce
        let sourceIpTimeout;
        document.getElementById('sourceIpFilter').addEventListener('input', (e) => {
            clearTimeout(sourceIpTimeout);
            sourceIpTimeout = setTimeout(() => {
                this.loadAlerts();
            }, 1000);
        });
    }
    
    initializeCharts() {
        // Alert Trend Chart
        const trendCtx = document.getElementById('alertTrendChart').getContext('2d');
        this.charts.alertTrend = new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Alerts per Hour',
                    data: [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4,
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
                        ticks: {
                            stepSize: 1
                        }
                    },
                    x: {
                        ticks: {
                            maxTicksLimit: 12
                        }
                    }
                }
            }
        });
        
        // Protocol Distribution Chart
        const protocolCtx = document.getElementById('protocolChart').getContext('2d');
        this.charts.protocol = new Chart(protocolCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#007bff',
                        '#28a745',
                        '#ffc107',
                        '#dc3545',
                        '#6c757d',
                        '#17a2b8'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        
        // Category Distribution Chart
        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
        this.charts.category = new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#fd7e14',
                        '#e83e8c',
                        '#6f42c1',
                        '#20c997',
                        '#fd7e14',
                        '#6c757d'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    async loadInitialData() {
        await Promise.all([
            this.loadNIDSStatus(),
            this.loadNIDSStats(),
            this.loadAlerts(),
            this.loadDNSLogs()
        ]);
    }
    
    async loadAllData() {
        const refreshBtn = document.getElementById('refreshBtn');
        const icon = refreshBtn.querySelector('i');
        
        // Show loading state
        icon.classList.add('fa-spin');
        refreshBtn.disabled = true;
        
        try {
            await this.loadInitialData();
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showError('Failed to refresh data. Please try again.');
        } finally {
            // Remove loading state
            icon.classList.remove('fa-spin');
            refreshBtn.disabled = false;
        }
    }
    
    async loadNIDSStatus() {
        try {
            const response = await fetch('/api/nids-status');
            if (!response.ok) throw new Error('Failed to fetch NIDS status');
            
            const status = await response.json();
            this.updateStatusIndicator(status);
        } catch (error) {
            console.error('Error loading NIDS status:', error);
            this.updateStatusIndicator({ overall_health: false });
        }
    }
    
    updateStatusIndicator(status) {
        const indicator = document.getElementById('nidsStatusIndicator');
        const text = document.getElementById('nidsStatusText');
        
        if (status.overall_health) {
            indicator.className = 'status-indicator status-running';
            text.textContent = 'NIDS Running';
        } else if (status.suricata_running && !status.log_file_recent) {
            indicator.className = 'status-indicator status-warning';
            text.textContent = 'NIDS Warning';
        } else {
            indicator.className = 'status-indicator status-stopped';
            text.textContent = 'NIDS Stopped';
        }
    }
    
    async loadNIDSStats() {
        try {
            const timeRange = document.getElementById('timeRangeFilter')?.value || 168;
            const response = await fetch(`/api/nids-stats?hours=${timeRange}`);
            if (!response.ok) throw new Error('Failed to fetch NIDS stats');
            
            const stats = await response.json();
            this.updateStatsCards(stats);
            this.updateCharts(stats);
            this.updateTopIPs(stats);
        } catch (error) {
            console.error('Error loading NIDS stats:', error);
            this.showError('Failed to load statistics');
        }
    }
    
    updateStatsCards(stats) {
        document.getElementById('totalAlerts').textContent = stats.total_alerts || 0;
        document.getElementById('criticalAlerts').textContent = stats.by_severity?.critical || 0;
        document.getElementById('highAlerts').textContent = stats.by_severity?.high || 0;
        document.getElementById('mediumAlerts').textContent = stats.by_severity?.medium || 0;
        document.getElementById('lowAlerts').textContent = stats.by_severity?.low || 0;
    }
    
    updateCharts(stats) {
        // Update alert trend chart
        if (stats.hourly_trend && stats.hourly_trend.length > 0) {
            const trendData = stats.hourly_trend;
            const labels = trendData.map(item => {
                const date = new Date(item.hour);
                return date.toLocaleTimeString('en-US', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                });
            });
            const data = trendData.map(item => item.count);
            
            this.charts.alertTrend.data.labels = labels;
            this.charts.alertTrend.data.datasets[0].data = data;
            this.charts.alertTrend.update();
        }
        
        // Update protocol chart
        if (stats.by_protocol && Object.keys(stats.by_protocol).length > 0) {
            const protocols = Object.keys(stats.by_protocol);
            const protocolCounts = Object.values(stats.by_protocol);
            
            this.charts.protocol.data.labels = protocols.map(p => p.toUpperCase());
            this.charts.protocol.data.datasets[0].data = protocolCounts;
            this.charts.protocol.update();
        }
        
        // Update category chart
        if (stats.by_category && Object.keys(stats.by_category).length > 0) {
            const categories = Object.keys(stats.by_category);
            const categoryCounts = Object.values(stats.by_category);
            
            this.charts.category.data.labels = categories;
            this.charts.category.data.datasets[0].data = categoryCounts;
            this.charts.category.update();
        }
    }
    
    updateTopIPs(stats) {
        // Update top source IPs
        const sourceIPsList = document.getElementById('topSourceIPs');
        if (stats.top_source_ips && stats.top_source_ips.length > 0) {
            sourceIPsList.innerHTML = stats.top_source_ips.slice(0, 10).map(item => `
                <li class="ip-item">
                    <div>
                        <div class="ip-cell">${item.ip}</div>
                        <div class="geo-info" id="geo-src-${item.ip.replace(/\./g, '-')}">Loading location...</div>
                    </div>
                    <span class="ip-count">${item.count}</span>
                </li>
            `).join('');
            
            // Load GeoIP data for source IPs
            stats.top_source_ips.slice(0, 5).forEach(item => {
                this.loadGeoIP(item.ip, `geo-src-${item.ip.replace(/\./g, '-')}`);
            });
        } else {
            sourceIPsList.innerHTML = '<li class="loading">No data available</li>';
        }
        
        // Update top destination IPs
        const destIPsList = document.getElementById('topDestIPs');
        if (stats.top_destination_ips && stats.top_destination_ips.length > 0) {
            destIPsList.innerHTML = stats.top_destination_ips.slice(0, 10).map(item => `
                <li class="ip-item">
                    <div>
                        <div class="ip-cell">${item.ip}</div>
                        <div class="geo-info" id="geo-dst-${item.ip.replace(/\./g, '-')}">Loading location...</div>
                    </div>
                    <span class="ip-count">${item.count}</span>
                </li>
            `).join('');
            
            // Load GeoIP data for destination IPs
            stats.top_destination_ips.slice(0, 5).forEach(item => {
                this.loadGeoIP(item.ip, `geo-dst-${item.ip.replace(/\./g, '-')}`);
            });
        } else {
            destIPsList.innerHTML = '<li class="loading">No data available</li>';
        }
    }
    
    async loadGeoIP(ip, elementId) {
        // Check cache first
        if (this.geoipCache.has(ip)) {
            const geoInfo = this.geoipCache.get(ip);
            this.updateGeoInfo(elementId, geoInfo);
            return;
        }
        
        try {
            const response = await fetch(`/api/nids-geoip/${ip}`);
            if (response.ok) {
                const geoInfo = await response.json();
                this.geoipCache.set(ip, geoInfo);
                this.updateGeoInfo(elementId, geoInfo);
            } else {
                this.updateGeoInfo(elementId, null);
            }
        } catch (error) {
            console.error(`Error loading GeoIP for ${ip}:`, error);
            this.updateGeoInfo(elementId, null);
        }
    }
    
    updateGeoInfo(elementId, geoInfo) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        if (geoInfo && geoInfo.country) {
            const location = [geoInfo.city, geoInfo.region, geoInfo.country]
                .filter(Boolean)
                .join(', ');
            element.innerHTML = `<i class="fas fa-map-marker-alt"></i> ${location}`;
        } else {
            element.textContent = 'Location unknown';
        }
    }
    
    async loadAlerts() {
        try {
            const params = new URLSearchParams();
            
            // Get filter values
            const severity = document.getElementById('severityFilter').value;
            const protocol = document.getElementById('protocolFilter').value;
            const sourceIp = document.getElementById('sourceIpFilter').value;
            const hours = document.getElementById('timeRangeFilter').value;
            
            if (severity) params.append('severity', severity);
            if (protocol) params.append('protocol', protocol);
            if (sourceIp) params.append('source_ip', sourceIp);
            if (hours) params.append('hours', hours);
            params.append('limit', '100');
            
            const response = await fetch(`/api/nids-alerts?${params}`);
            if (!response.ok) throw new Error('Failed to fetch alerts');
            
            const data = await response.json();
            this.updateAlertsTable(data.alerts);
        } catch (error) {
            console.error('Error loading alerts:', error);
            this.showError('Failed to load alerts');
        }
    }
    
    updateAlertsTable(alerts) {
        const tbody = document.getElementById('alertsTableBody');
        
        if (!alerts || alerts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="loading">No alerts found</td></tr>';
            return;
        }
        
        tbody.innerHTML = alerts.map(alert => {
            const timestamp = new Date(alert.timestamp);
            const timeStr = timestamp.toLocaleString();
            
            return `
                <tr>
                    <td>${timeStr}</td>
                    <td><span class="severity-badge severity-${alert.alert_severity}">${alert.alert_severity}</span></td>
                    <td title="${alert.alert_signature}">${this.truncateText(alert.alert_signature, 50)}</td>
                    <td><span class="ip-cell">${alert.source_ip}</span></td>
                    <td><span class="ip-cell">${alert.destination_ip}</span></td>
                    <td><span class="protocol-badge">${alert.protocol.toUpperCase()}</span></td>
                    <td>${alert.category || '-'}</td>
                    <td>${alert.action || '-'}</td>
                </tr>
            `;
        }).join('');
    }
    
    async loadDNSLogs() {
        try {
            const hours = document.getElementById('timeRangeFilter')?.value || 168;
            const response = await fetch(`/api/nids-dns?hours=${hours}&suspicious_only=true&limit=50`);
            if (!response.ok) throw new Error('Failed to fetch DNS logs');
            
            const data = await response.json();
            this.updateDNSTable(data.dns_logs);
        } catch (error) {
            console.error('Error loading DNS logs:', error);
            // Don't show error for DNS logs as they might not be available
        }
    }
    
    updateDNSTable(dnsLogs) {
        const tbody = document.getElementById('dnsLogsTableBody');
        
        if (!dnsLogs || dnsLogs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">No suspicious DNS queries found</td></tr>';
            return;
        }
        
        tbody.innerHTML = dnsLogs.map(log => {
            const timestamp = new Date(log.timestamp);
            const timeStr = timestamp.toLocaleString();
            const confidence = Math.round(log.confidence_score * 100);
            
            return `
                <tr>
                    <td>${timeStr}</td>
                    <td title="${log.query_name}">${this.truncateText(log.query_name, 40)}</td>
                    <td>${log.query_type}</td>
                    <td><span class="ip-cell">${log.source_ip}</span></td>
                    <td><span class="severity-badge severity-${this.getThreatSeverity(log.threat_type)}">${log.threat_type}</span></td>
                    <td>${confidence}%</td>
                </tr>
            `;
        }).join('');
    }
    
    getThreatSeverity(threatType) {
        const severityMap = {
            'tor_hidden_service': 'high',
            'domain_generation_algorithm': 'critical',
            'phishing': 'high',
            'malware': 'critical',
            'botnet': 'high',
            'cryptomining': 'medium',
            'suspicious_pattern': 'medium'
        };
        return severityMap[threatType] || 'low';
    }
    
    async clearOldAlerts() {
        if (!confirm('Are you sure you want to clear alerts older than 7 days?')) {
            return;
        }
        
        try {
            const response = await fetch('/api/nids-alerts/clear?days_old=7', {
                method: 'DELETE'
            });
            
            if (!response.ok) throw new Error('Failed to clear alerts');
            
            const result = await response.json();
            this.showSuccess(`Successfully cleared ${result.deleted_count} old alerts`);
            
            // Refresh data
            await this.loadAllData();
        } catch (error) {
            console.error('Error clearing alerts:', error);
            this.showError('Failed to clear old alerts');
        }
    }
    
    truncateText(text, maxLength) {
        if (!text) return '-';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showNotification(message, type) {
        // Remove existing notifications
        const existing = document.querySelector('.notification');
        if (existing) existing.remove();
        
        // Create notification
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
            background: ${type === 'error' ? '#dc3545' : '#28a745'};
        `;
        notification.textContent = message;
        
        // Add animation styles
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideIn 0.3s ease-out reverse';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }
    
    startAutoRefresh() {
        this.refreshTimer = setInterval(() => {
            this.loadNIDSStatus();
            this.loadNIDSStats();
        }, this.refreshInterval);
    }
    
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.nidsDashboard = new NIDSDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.nidsDashboard) {
        window.nidsDashboard.stopAutoRefresh();
    }
});
