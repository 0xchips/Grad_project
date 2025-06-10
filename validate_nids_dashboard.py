#!/usr/bin/env python3
"""
NIDS Dashboard Validation Script
Comprehensive testing and validation of the NIDS dashboard functionality
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
DASHBOARD_URL = "http://localhost:5053"
ENDPOINTS = {
    'status': '/api/nids-status',
    'stats': '/api/nids-stats',
    'alerts': '/api/nids-alerts',
    'dns': '/api/nids-dns',
    'geoip': '/api/nids-geoip'
}

class NIDSValidator:
    def __init__(self, base_url=DASHBOARD_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            'tests_passed': 0,
            'tests_failed': 0,
            'errors': []
        }
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_endpoint(self, endpoint, expected_keys=None, params=None):
        """Test an API endpoint and validate response"""
        try:
            url = f"{self.base_url}{endpoint}"
            if params:
                url += "?" + "&".join([f"{k}={v}" for k, v in params.items()])
            
            self.log(f"Testing endpoint: {endpoint}")
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            data = response.json()
            
            if expected_keys:
                for key in expected_keys:
                    if key not in data:
                        raise Exception(f"Missing expected key: {key}")
            
            self.log(f"✅ Endpoint {endpoint} - OK")
            self.results['tests_passed'] += 1
            return data
            
        except Exception as e:
            self.log(f"❌ Endpoint {endpoint} - FAILED: {str(e)}", "ERROR")
            self.results['tests_failed'] += 1
            self.results['errors'].append(f"{endpoint}: {str(e)}")
            return None
    
    def validate_nids_status(self):
        """Validate NIDS status endpoint"""
        data = self.test_endpoint(
            ENDPOINTS['status'],
            expected_keys=['database_connected', 'total_alerts', 'status']
        )
        if data:
            self.log(f"  - Database connected: {data.get('database_connected', False)}")
            self.log(f"  - Total alerts: {data.get('total_alerts', 0)}")
            self.log(f"  - System status: {data.get('status', 'unknown')}")
    
    def validate_nids_stats(self):
        """Validate NIDS statistics endpoint"""
        data = self.test_endpoint(
            ENDPOINTS['stats'],
            expected_keys=['total_alerts', 'by_severity', 'by_protocol'],
            params={'hours': 168}
        )
        if data:
            self.log(f"  - Total alerts (168h): {data.get('total_alerts', 0)}")
            self.log(f"  - Severity breakdown: {data.get('by_severity', {})}")
            self.log(f"  - Protocol breakdown: {data.get('by_protocol', {})}")
            
            # Check for chart data
            if 'hourly_trend' in data:
                self.log(f"  - Hourly trend points: {len(data['hourly_trend'])}")
            if 'top_source_ips' in data:
                self.log(f"  - Top source IPs: {len(data['top_source_ips'])}")
    
    def validate_nids_alerts(self):
        """Validate NIDS alerts endpoint"""
        data = self.test_endpoint(
            ENDPOINTS['alerts'],
            expected_keys=['alerts', 'count', 'filters'],
            params={'hours': 168, 'limit': 10}
        )
        if data:
            self.log(f"  - Alert count: {data.get('count', 0)}")
            self.log(f"  - Filters applied: {data.get('filters', {})}")
            
            alerts = data.get('alerts', [])
            if alerts:
                self.log(f"  - Sample alert: {alerts[0].get('alert_signature', 'N/A')}")
    
    def validate_dns_logs(self):
        """Validate DNS logs endpoint"""
        data = self.test_endpoint(
            ENDPOINTS['dns'],
            expected_keys=['dns_logs', 'count', 'filters'],
            params={'hours': 168, 'limit': 10, 'suspicious_only': 'true'}
        )
        if data:
            self.log(f"  - DNS log count: {data.get('count', 0)}")
            
            dns_logs = data.get('dns_logs', [])
            if dns_logs:
                self.log(f"  - Sample DNS query: {dns_logs[0].get('query_name', 'N/A')}")
    
    def validate_geoip(self):
        """Validate GeoIP endpoint"""
        # Test with a known IP
        test_ip = "8.8.8.8"
        data = self.test_endpoint(f"{ENDPOINTS['geoip']}/{test_ip}")
        if data:
            self.log(f"  - GeoIP lookup for {test_ip}: {data.get('found', False)}")
    
    def run_comprehensive_test(self):
        """Run all validation tests"""
        self.log("Starting NIDS Dashboard Validation", "INFO")
        self.log("=" * 50)
        
        # Test all endpoints
        self.validate_nids_status()
        self.validate_nids_stats()
        self.validate_nids_alerts()
        self.validate_dns_logs()
        self.validate_geoip()
        
        # Summary
        self.log("=" * 50)
        self.log("VALIDATION SUMMARY")
        self.log(f"Tests Passed: {self.results['tests_passed']}")
        self.log(f"Tests Failed: {self.results['tests_failed']}")
        
        if self.results['errors']:
            self.log("ERRORS:")
            for error in self.results['errors']:
                self.log(f"  - {error}", "ERROR")
        
        success_rate = (self.results['tests_passed'] / 
                       (self.results['tests_passed'] + self.results['tests_failed'])) * 100
        self.log(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            self.log("✅ NIDS Dashboard is functioning properly!", "SUCCESS")
            return True
        else:
            self.log("❌ NIDS Dashboard has significant issues!", "ERROR")
            return False

def main():
    try:
        validator = NIDSValidator()
        success = validator.run_comprehensive_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
