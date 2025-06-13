// Configurations page JavaScript functionality
class ConfigurationsManager {
    constructor() {
        this.adapters = [];
        this.currentConfig = {};
        this.configurationLoaded = false;
        this.adaptersLoaded = false;
        this.init();
    }

    init() {
        console.log('🚀 Initializing ConfigurationsManager...');
        this.setupEventListeners();
        
        // Load configuration and adapters in parallel, then apply when both are ready
        Promise.all([
            this.loadConfigurationFromServer(),
            this.scanAdapters()
        ]).then(() => {
            console.log('✅ Both configuration and adapters loaded, applying config...');
            this.applyConfigurationToForm(this.currentConfig);
        }).catch(error => {
            console.error('❌ Error during initialization:', error);
        });
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

    async loadConfigurationFromServer() {
        console.log('📖 Loading configuration from server...');
        try {
            const response = await fetch('/api/configurations');
            const data = await response.json();
            
            if (response.ok && data.configuration) {
                this.currentConfig = data.configuration;
                this.configurationLoaded = true;
                console.log('✅ Configuration loaded:', this.currentConfig);
                return this.currentConfig;
            } else {
                console.warn('⚠️ No configuration found');
                this.currentConfig = {};
                this.configurationLoaded = true;
                return {};
            }
        } catch (error) {
            console.error('❌ Error loading configuration:', error);
            this.currentConfig = {};
            this.configurationLoaded = true;
            throw error;
        }
    }

    async scanAdapters() {
        console.log('🔍 Scanning for wireless adapters...');
        this.showScanStatus('scanning', 'Scanning for wireless adapters...');
        
        try {
            const response = await fetch('/api/wireless-adapters');
            const data = await response.json();
            
            if (response.ok) {
                this.adapters = data.adapters || [];
                this.adaptersLoaded = true;
                console.log('✅ Found adapters:', this.adapters.map(a => a.name));
                
                this.populateAdapterSelects();
                this.showScanStatus('success', `Found ${this.adapters.length} wireless adapter(s)`);
                this.updateAdapterInfo();
                
                return this.adapters;
            } else {
                throw new Error(data.error || 'Failed to scan adapters');
            }
        } catch (error) {
            console.error('❌ Error scanning adapters:', error);
            this.showScanStatus('error', `Error: ${error.message}`);
            this.showError(`Failed to scan adapters: ${error.message}`);
            throw error;
        }
    }

    populateAdapterSelects() {
        console.log('📝 Populating adapter select elements...');
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
            
            console.log(`📝 Populated ${selectId} with ${this.adapters.length} options`);
        });
    }

    applyConfigurationToForm(config) {
        console.log('🎯 Applying configuration to form:', config);
        
        const fieldMappings = {
            'realtime_monitoring': 'realtime-monitoring',
            'network_devices': 'network-devices',
            'kismet_monitoring': 'kismet-monitoring'
        };
        
        // Apply each configuration value
        Object.keys(fieldMappings).forEach(configKey => {
            const elementId = fieldMappings[configKey];
            const value = config[configKey];
            
            if (value) {
                const element = document.getElementById(elementId);
                if (element) {
                    console.log(`🔧 Setting ${elementId} to "${value}"`);
                    
                    // Check if the value exists in the options
                    const optionExists = Array.from(element.options).some(option => option.value === value);
                    
                    if (optionExists) {
                        element.value = value;
                        console.log(`✅ Successfully set ${elementId} = "${value}"`);
                        
                        // Trigger change event to ensure any listeners are notified
                        element.dispatchEvent(new Event('change'));
                    } else {
                        console.warn(`⚠️ Option "${value}" not found in ${elementId}`);
                        console.log(`Available options:`, Array.from(element.options).map(opt => `"${opt.value}"`));
                    }
                } else {
                    console.error(`❌ Element ${elementId} not found in DOM`);
                }
            } else {
                console.log(`⏭️ Skipping ${configKey} - no value provided`);
            }
        });
        
        // Validate the selection after applying configuration
        this.validateSelection();
        console.log('🏁 Configuration application completed');
        
        // Log final state for debugging
        Object.keys(fieldMappings).forEach(configKey => {
            const elementId = fieldMappings[configKey];
            const element = document.getElementById(elementId);
            if (element) {
                console.log(`📊 Final state: ${elementId} = "${element.value}"`);
            }
        });
    }

    async saveConfiguration() {
        const form = document.getElementById('config-form');
        const formData = new FormData(form);
        
        const config = {
            realtime_monitoring: formData.get('realtime_monitoring') || '',
            network_devices: formData.get('network_devices') || '',
            kismet_monitoring: formData.get('kismet_monitoring') || ''
        };

        console.log('💾 Saving configuration:', config);

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
                console.log('✅ Configuration saved successfully:', config);
                
                // Refresh adapter list to update availability
                setTimeout(() => {
                    this.scanAdapters();
                }, 1000);
            } else {
                throw new Error(data.error || 'Failed to save configuration');
            }
        } catch (error) {
            console.error('❌ Error saving configuration:', error);
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

    // Legacy methods for backward compatibility
    async loadCurrentConfig() {
        if (!this.configurationLoaded) {
            await this.loadConfigurationFromServer();
        }
        if (this.adaptersLoaded) {
            this.applyConfigurationToForm(this.currentConfig);
        }
    }

    // Debug methods
    async debugReloadConfig() {
        console.log('🔄 Debug: Manually reloading configuration...');
        await this.loadConfigurationFromServer();
        this.applyConfigurationToForm(this.currentConfig);
    }
    
    debugFormState() {
        console.log('📊 Current form state:');
        const selects = ['realtime-monitoring', 'network-devices', 'kismet-monitoring'];
        selects.forEach(selectId => {
            const element = document.getElementById(selectId);
            if (element) {
                console.log(`  ${selectId}: "${element.value}" (${element.options.length} options)`);
                Array.from(element.options).forEach((opt, idx) => {
                    console.log(`    [${idx}] "${opt.value}" - ${opt.textContent}`);
                });
            }
        });
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
