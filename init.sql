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
    type ENUM('deauth', 'evil-twin') NOT NULL DEFAULT 'deauth',
    attacker_bssid VARCHAR(17),
    attacker_ssid VARCHAR(255),
    destination_bssid VARCHAR(17),
    destination_ssid VARCHAR(255),
    attack_count INT DEFAULT 1,
    source_ip VARCHAR(45),
    INDEX idx_timestamp (timestamp),
    INDEX idx_alert_type (alert_type),
    INDEX idx_type (type),
    INDEX idx_attacker_bssid (attacker_bssid)
);

-- Bluetooth/Spectrum detections table
CREATE TABLE IF NOT EXISTS bluetooth_detections (
    id VARCHAR(36) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    device_id VARCHAR(100) NOT NULL,
    device_name VARCHAR(255),
    signal_strength INT,
    channel INT,
    rssi_value INT,
    threat_level ENUM('low', 'medium', 'high', 'critical') DEFAULT 'low',
    detection_type ENUM('bluetooth', 'spectrum', 'deauth', 'jamming') DEFAULT 'bluetooth',
    raw_data TEXT,
    max_signal INT DEFAULT 0,
    spectrum_data TEXT,
    INDEX idx_timestamp (timestamp),
    INDEX idx_device_id (device_id),
    INDEX idx_threat_level (threat_level),
    INDEX idx_detection_type (detection_type)
);

-- NIDS alerts table
CREATE TABLE IF NOT EXISTS nids_alerts (
    id VARCHAR(36) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    alert_severity ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    category VARCHAR(100),
    protocol VARCHAR(100),
    source_ip VARCHAR(45),
    destination_ip VARCHAR(45),
    alert_data TEXT,
    INDEX idx_timestamp (timestamp),
    INDEX idx_severity (alert_severity),
    INDEX idx_category (category),
    INDEX idx_protocol (protocol)
);

-- DNS logs table
CREATE TABLE IF NOT EXISTS dns_logs (
    id VARCHAR(36) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    query_name VARCHAR(255),
    query_type VARCHAR(10),
    response_code VARCHAR(10),
    is_suspicious BOOLEAN DEFAULT FALSE,
    threat_type VARCHAR(100),
    source_ip VARCHAR(45),
    destination_ip VARCHAR(45),
    INDEX idx_timestamp (timestamp),
    INDEX idx_query_name (query_name),
    INDEX idx_response_code (response_code),
    INDEX idx_threat_type (threat_type)
);

-- GeoIP information table
CREATE TABLE IF NOT EXISTS geoip_info (
    id VARCHAR(36) PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    country VARCHAR(100),
    region VARCHAR(100),
    city VARCHAR(100),
    zip_code VARCHAR(20),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    timezone VARCHAR(50),
    isp VARCHAR(100),
    organization VARCHAR(100),
    asn VARCHAR(50),
    INDEX idx_ip_address (ip_address)
);

-- Insert some sample data for testing (optional)
-- INSERT INTO alerts (id, tool_name, alert_type, severity, description) VALUES
-- (UUID(), 'Test Tool', 'Test Alert', 'low', 'Sample alert for testing');

COMMIT;
