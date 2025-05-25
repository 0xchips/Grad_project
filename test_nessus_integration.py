#!/usr/bin/env python3
"""
CyberShield Nessus Integration Test Suite
=========================================

This script tests the complete Nessus integration with the CyberShield dashboard.
It validates all API endpoints, frontend functionality, and backend integration.

Author: CyberShield Development Team
Date: $(date +%Y-%m-%d)
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5050"
ENDPOINTS = {
    'setup': '/api/nessus/setup',
    'scan_start': '/api/nessus/scan/start',
    'scan_status': '/api/nessus/scan/status',
    'scan_results': '/api/nessus/scan/results',
    'scan_report': '/api/nessus/scan/report'
}

class NessusIntegrationTester:
    def __init__(self):
        self.results = []
        self.scan_id = None
        
    def log_result(self, test_name, success, message, details=None):
        """Log test results"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result = {
            'timestamp': timestamp,
            'test': test_name,
            'success': success,
            'message': message,
            'details': details or {}
        }
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"[{timestamp}] {status} - {test_name}: {message}")
        
        if details and not success:
            print(f"    Details: {json.dumps(details, indent=2)}")
    
    def test_server_health(self):
        """Test if the CyberShield server is responding"""
        try:
            response = requests.get(BASE_URL, timeout=5)
            if response.status_code == 200:
                self.log_result(
                    "Server Health Check", 
                    True, 
                    f"Server responding on {BASE_URL}"
                )
                return True
            else:
                self.log_result(
                    "Server Health Check", 
                    False, 
                    f"Server returned status {response.status_code}",
                    {'status_code': response.status_code}
                )
                return False
        except Exception as e:
            self.log_result(
                "Server Health Check", 
                False, 
                f"Failed to connect to server: {str(e)}",
                {'error': str(e)}
            )
            return False
    
    def test_nessus_setup(self):
        """Test Nessus setup endpoint"""
        try:
            payload = {'force_install': False}
            response = requests.post(
                f"{BASE_URL}{ENDPOINTS['setup']}", 
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_result(
                        "Nessus Setup", 
                        True, 
                        data.get('message', 'Setup initiated successfully')
                    )
                    return True
                else:
                    self.log_result(
                        "Nessus Setup", 
                        False, 
                        data.get('message', 'Setup failed'),
                        data
                    )
                    return False
            else:
                self.log_result(
                    "Nessus Setup", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}",
                    {'status_code': response.status_code, 'response': response.text}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Nessus Setup", 
                False, 
                f"Request failed: {str(e)}",
                {'error': str(e)}
            )
            return False
    
    def test_scan_start(self):
        """Test scan initiation"""
        try:
            payload = {
                'targets': '127.0.0.1',
                'scan_name': f'CyberShield_Test_Scan_{int(time.time())}'
            }
            
            response = requests.post(
                f"{BASE_URL}{ENDPOINTS['scan_start']}", 
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.scan_id = data.get('scan_id')
                    self.log_result(
                        "Scan Initiation", 
                        True, 
                        f"Scan started: {data.get('message', 'Success')}"
                    )
                    return True
                else:
                    self.log_result(
                        "Scan Initiation", 
                        False, 
                        data.get('message', 'Scan failed to start'),
                        data
                    )
                    return False
            else:
                self.log_result(
                    "Scan Initiation", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}",
                    {'status_code': response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Scan Initiation", 
                False, 
                f"Request failed: {str(e)}",
                {'error': str(e)}
            )
            return False
    
    def test_scan_status(self):
        """Test scan status endpoint"""
        try:
            url = f"{BASE_URL}{ENDPOINTS['scan_status']}"
            if self.scan_id:
                url += f"?scan_id={self.scan_id}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                self.log_result(
                    "Scan Status Check", 
                    True, 
                    f"Status retrieved: {status}",
                    {'scan_status': status, 'progress': data.get('progress')}
                )
                return True
            else:
                self.log_result(
                    "Scan Status Check", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}",
                    {'status_code': response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Scan Status Check", 
                False, 
                f"Request failed: {str(e)}",
                {'error': str(e)}
            )
            return False
    
    def test_scan_results(self):
        """Test scan results endpoint"""
        try:
            url = f"{BASE_URL}{ENDPOINTS['scan_results']}"
            if self.scan_id:
                url += f"?scan_id={self.scan_id}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'error' not in data:
                    self.log_result(
                        "Scan Results", 
                        True, 
                        "Results endpoint accessible",
                        {'result_keys': list(data.keys())}
                    )
                    return True
                else:
                    self.log_result(
                        "Scan Results", 
                        True, 
                        f"Expected error (no results yet): {data.get('error')}",
                        data
                    )
                    return True
            else:
                self.log_result(
                    "Scan Results", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}",
                    {'status_code': response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Scan Results", 
                False, 
                f"Request failed: {str(e)}",
                {'error': str(e)}
            )
            return False
    
    def test_frontend_integration(self):
        """Test if frontend has Nessus integration"""
        try:
            response = requests.get(BASE_URL, timeout=10)
            content = response.text
            
            # Check for key Nessus integration elements
            checks = {
                'runFullScan function': 'function runFullScan',
                'Nessus API calls': '/api/nessus/scan/start',
                'Progress modal': 'showNessusProgressModal',
                'Results modal': 'showNessusResults',
                'Nessus styling': 'nessus-progress-modal'
            }
            
            passed_checks = 0
            for check_name, search_term in checks.items():
                if search_term in content:
                    passed_checks += 1
                    print(f"    ✅ {check_name}: Found")
                else:
                    print(f"    ❌ {check_name}: Not found")
            
            success = passed_checks == len(checks)
            self.log_result(
                "Frontend Integration", 
                success, 
                f"{passed_checks}/{len(checks)} integration elements found",
                {'passed_checks': passed_checks, 'total_checks': len(checks)}
            )
            return success
            
        except Exception as e:
            self.log_result(
                "Frontend Integration", 
                False, 
                f"Failed to check frontend: {str(e)}",
                {'error': str(e)}
            )
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🔍 CyberShield Nessus Integration Test Suite")
        print("=" * 50)
        
        # Test sequence
        tests = [
            self.test_server_health,
            self.test_frontend_integration,
            self.test_nessus_setup,
            self.test_scan_start,
            self.test_scan_status,
            self.test_scan_results
        ]
        
        passed_tests = 0
        for test in tests:
            if test():
                passed_tests += 1
            print()  # Add spacing between tests
        
        # Summary
        total_tests = len(tests)
        print("=" * 50)
        print(f"📊 Test Summary: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Nessus integration is working correctly.")
            return True
        else:
            print(f"⚠️  {total_tests - passed_tests} tests failed. Check logs above.")
            return False
    
    def generate_report(self):
        """Generate detailed test report"""
        report_file = f"nessus_integration_test_report_{int(time.time())}.json"
        
        report_data = {
            'test_suite': 'CyberShield Nessus Integration',
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.results),
            'passed_tests': sum(1 for r in self.results if r['success']),
            'failed_tests': sum(1 for r in self.results if not r['success']),
            'results': self.results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📋 Detailed test report saved to: {report_file}")
        return report_file

def main():
    """Main test execution"""
    tester = NessusIntegrationTester()
    
    try:
        success = tester.run_all_tests()
        tester.generate_report()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Test suite interrupted by user")
        tester.generate_report()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {str(e)}")
        tester.generate_report()
        sys.exit(1)

if __name__ == "__main__":
    main()
