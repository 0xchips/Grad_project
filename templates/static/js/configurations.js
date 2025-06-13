// Configurations page JavaScript functionality
class ConfigurationsManager {
    constructor() {
        this.adapters = [];
        this.currentConfig = {};
        this.init();
    }

    init() {
        this.setupEventListeners();
        // Just scan adapters - configuration will be loaded automatically afterward
        this.scanAdapters();
    }

    setupEventListeners() {
        // Form submission
        document.getElementById('config-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveConfiguration();
        });

        // Adapter selection changes
        const selects = ['realtime-monitoring', 'network-devices', 'kismet-monitoring'];
        selects.forEach(selectId => {
            document.getElementById(selectId).addEventListener('change', () => {
                this.validateSelection();
            });
        });
    }

    async scanAdapters() {
        this.showScanStatus('scanning', 'Scanning for wireless adapters...');
        
        try {
            const response = await fetch('/api/wireless-adapters');
            const data = await response.json();
            
            if (response.ok) {
                this.adapters = data.adapters || [];
                this.populateAdapterSelects();
                this.showScanStatus('success', `Found ${this.adapters.length} wireless adapter(s)`);
                this.updateAdapterInfo();
                
                // After adapters are loaded, load and apply saved configuration
                await this.loadAndApplyConfig();
            } else {
                throw new Error(data.error || 'Failed to scan adapters');
            }
        } catch (error) {
            console.error('Error scanning adapters:', error);
            this.showScanStatus('error', `Error: ${error.message}`);
            this.showError(`Failed to scan adapters: ${error.message}`);
        }
    }

    async loadAndApplyConfig() {
        console.log('🔄 Loading configuration from server...');
        try {
            const response = await fetch('/api/configurations');
            const data = await response.json();
            
            console.log('📡 Server response:', data);
            
            if (response.ok && data.configuration) {
                this.currentConfig = data.configuration;
                console.log('✅ Loaded configuration:', this.currentConfig);
                
                // Apply configuration to form with delay to ensure DOM is ready
                setTimeout(() => {
                    this.applyConfigurationToForm(this.currentConfig);
                }, 100);
            } else {
                console.warn('⚠️ No configuration found in response');
            }
        } catch (error) {
            console.error('❌ Error loading configuration:', error);
        }
    }

    applyConfigurationToForm(config) {
        console.log('🎯 Applying configuration to form:', config);
        
        // Set values for each select element
        Object.keys(config).forEach(key => {
            const value = config[key];
            if (value) {
                let elementId;
                switch(key) {
                    case 'realtime_monitoring':
                        elementId = 'realtime-monitoring';
                        break;
                    case 'network_devices':
                        elementId = 'network-devices';
                        break;
                    case 'kismet_monitoring':
                        elementId = 'kismet-monitoring';
                        break;
                }
                
                if (elementId) {
                    const element = document.getElementById(elementId);
                    if (element) {
                        console.log(`🔧 Setting ${elementId} to "${value}"`);
                        element.value = value;
                        
                        // Verify the value was set
                        if (element.value === value) {
                            console.log(`✅ Successfully set ${elementId} = "${value}"`);
                        } else {
                            console.warn(`⚠️ Failed to set ${elementId}, value is "${element.value}" instead of "${value}"`);
                            console.log(`Available options:`, Array.from(element.options).map(opt => opt.value));
                        }
                    } else {
                        console.error(`❌ Element ${elementId} not found in DOM`);
                    }
                }
            }
        });
        
        this.validateSelection();
        console.log('🏁 Configuration application completed');
    }

    populateAdapterSelects() {
        const selects = ['realtime-monitoring', 'network-devices', 'kismet-monitoring'];
        
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            
            // Clear existing options except the first one
            while (select.children.length > 1) {
                select.removeChild(select.lastChild);
            }
            
            // Add adapter options
            this.adapters.forEach(adapter => {
                const option = document.createElement('option');
                option.value = adapter.name;
                option.textContent = `${adapter.name} - ${adapter.description}`;
                
                if (!adapter.available) {
                    option.disabled = true;
                    option.textContent += ' (In use)';
                }
                
                select.appendChild(option);
            });
        });
    }

    async loadCurrentConfig() {
        // This method is now handled by loadAndApplyConfig
        await this.loadAndApplyConfig();
    }

    async saveConfiguration() {
        const form = document.getElementById('config-form');
        const formData = new FormData(form);
        
        const config = {
            realtime_monitoring: formData.get('realtime_monitoring') || '',
            network_devices: formData.get('network_devices') || '',
            kismet_monitoring: formData.get('kismet_monitoring') || ''
        };

        console.log('Saving configuration:', config);

        try {
            const response = await fetch('/api/configurations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            });

            const data = await response.json();

            if (response.ok) {
                this.currentConfig = config;
                this.showSuccess('Configuration saved successfully!');
                console.log('Configuration saved successfully:', config);
                
                // Refresh adapter list to update availability
                setTimeout(() => {
                    this.scanAdapters();
                }, 1000);
            } else {
                throw new Error(data.error || 'Failed to save configuration');
            }
        } catch (error) {
            console.error('Error saving configuration:', error);
            this.showError(`Failed to save configuration: ${error.message}`);
        }
    }

    validateSelection() {
        const selections = {
            realtime: document.getElementById('realtime-monitoring').value,
            network: document.getElementById('network-devices').value,
            kismet: document.getElementById('kismet-monitoring').value
        };

        // Check for duplicate selections
        const values = Object.values(selections).filter(v => v);
        const duplicates = values.length !== new Set(values).size;

        if (duplicates) {
            this.showWarning('Warning: The same adapter is selected for multiple functions. This may cause conflicts.');
        } else {
            this.hideAlert();
        }
    }

    showScanStatus(type, message) {
        const statusElement = document.getElementById('scan-status');
        statusElement.className = `scan-status ${type}`;
        
        if (type === 'scanning') {
            statusElement.innerHTML = `<div class="spinner"></div><span>${message}</span>`;
        } else if (type === 'success') {
            statusElement.innerHTML = `<i class="fas fa-check-circle"></i><span>${message}</span>`;
            setTimeout(() => {
                statusElement.style.display = 'none';
            }, 3000);
        } else if (type === 'error') {
            statusElement.innerHTML = `<i class="fas fa-exclamation-circle"></i><span>${message}</span>`;
        }
    }

    updateAdapterInfo() {
        const adapterInfo = document.getElementById('adapter-info');
        const adapterCount = document.getElementById('adapter-count');
        
        adapterCount.textContent = this.adapters.length;
        adapterInfo.style.display = 'block';
    }

    showSuccess(message) {
        this.hideAlert();
        const alert = document.getElementById('success-alert');
        alert.style.display = 'flex';
        alert.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
        
        setTimeout(() => {
            alert.style.display = 'none';
        }, 5000);
    }

    showError(message) {
        this.hideAlert();
        const alert = document.getElementById('error-alert');
        const messageSpan = document.getElementById('error-message');
        messageSpan.textContent = message;
        alert.style.display = 'flex';
        
        setTimeout(() => {
            alert.style.display = 'none';
        }, 8000);
    }

    showWarning(message) {
        // For now, use error styling for warnings
        this.showError(message);
    }

    hideAlert() {
        document.getElementById('success-alert').style.display = 'none';
        document.getElementById('error-alert').style.display = 'none';
    }
}

// Global functions for button handlers
function scanAdapters() {
    if (window.configurationsManager) {
        window.configurationsManager.scanAdapters();
    }
}

function loadCurrentConfig() {
    if (window.configurationsManager) {
        window.configurationsManager.loadCurrentConfig();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.configurationsManager = new ConfigurationsManager();
});
