-- Initialize Security Dashboard Database
-- This script sets up the required tables and indexes

USE security_dashboard;

-- Alerts table with improved schema
CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(36) PRIMARY KEY,
    tool_name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    description TEXT,
    raw_data TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_ip VARCHAR(45),
    INDEX idx_timestamp (timestamp),
    INDEX idx_severity (severity),
    INDEX idx_tool_name (tool_name)
);

-- GPS data table with enhanced schema
CREATE TABLE IF NOT EXISTS gps_data (
    id VARCHAR(36) PRIMARY KEY,
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    device_id VARCHAR(100),
    satellites INT DEFAULT 0,
    hdop DECIMAL(4,2) DEFAULT 99.99,
    jamming_detected BOOLEAN DEFAULT FALSE,
    INDEX idx_timestamp (timestamp),
    INDEX idx_device_id (device_id),
    INDEX idx_jamming (jamming_detected)
);

-- Network attacks table with proper indexing
CREATE TABLE IF NOT EXISTS network_attacks (
    id VARCHAR(36) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    alert_type VARCHAR(100) NOT NULL,
    attacker_bssid VARCHAR(17),
    attacker_ssid VARCHAR(255),
    destination_bssid VARCHAR(17),
    destination_ssid VARCHAR(255),
    attack_count INT DEFAULT 1,
    source_ip VARCHAR(45),
    INDEX idx_timestamp (timestamp),
    INDEX idx_alert_type (alert_type),
    INDEX idx_attacker_bssid (attacker_bssid)
);

-- Insert some sample data for testing (optional)
-- INSERT INTO alerts (id, tool_name, alert_type, severity, description) VALUES
-- (UUID(), 'Test Tool', 'Test Alert', 'low', 'Sample alert for testing');

COMMIT;
