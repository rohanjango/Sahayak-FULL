#!/usr/bin/env python3
"""
Sahayak Backend API Testing Suite
Tests all API endpoints and core functionality
"""

import requests
import sys
import json
from datetime import datetime
import time

class SahayakAPITester:
    def __init__(self, base_url="https://sahayak-app.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_id = f"test_user_{datetime.now().strftime('%H%M%S')}"

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        if details:
            print(f"   Details: {details}")
        print()

    def test_health_endpoint(self):
        """Test API health check"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Status: {data.get('status')}, Service: {data.get('service')}"
            else:
                details = f"Status code: {response.status_code}"
                
            self.log_test("Health Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Health Endpoint", False, str(e))
            return False

    def test_root_endpoint(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                capabilities = data.get('capabilities', [])
                details = f"Version: {data.get('version')}, Capabilities: {len(capabilities)}"
            else:
                details = f"Status code: {response.status_code}"
                
            self.log_test("Root Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("Root Endpoint", False, str(e))
            return False

    def test_memory_save(self):
        """Test memory save functionality"""
        try:
            payload = {
                "user_id": self.test_user_id,
                "key": "test_email",
                "value": "test@sahayak.com"
            }
            
            response = requests.post(
                f"{self.api_url}/memory/save",
                json=payload,
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Success: {data.get('success')}, Message: {data.get('message')}"
            else:
                details = f"Status code: {response.status_code}, Response: {response.text}"
                
            self.log_test("Memory Save", success, details)
            return success
        except Exception as e:
            self.log_test("Memory Save", False, str(e))
            return False

    def test_memory_get(self):
        """Test memory retrieval functionality"""
        try:
            payload = {
                "user_id": self.test_user_id,
                "key": "test_email"
            }
            
            response = requests.post(
                f"{self.api_url}/memory/get",
                json=payload,
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                memory_value = data.get('memory')
                details = f"Retrieved value: {memory_value}"
                # Verify we got back what we saved
                if memory_value != "test@sahayak.com":
                    success = False
                    details += " (Value mismatch!)"
            else:
                details = f"Status code: {response.status_code}, Response: {response.text}"
                
            self.log_test("Memory Get", success, details)
            return success
        except Exception as e:
            self.log_test("Memory Get", False, str(e))
            return False

    def test_history_endpoint(self):
        """Test execution history endpoint"""
        try:
            response = requests.get(
                f"{self.api_url}/history/{self.test_user_id}?limit=5",
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                history = data.get('history', [])
                details = f"History entries: {len(history)}"
            else:
                details = f"Status code: {response.status_code}, Response: {response.text}"
                
            self.log_test("History Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("History Endpoint", False, str(e))
            return False

    def test_execute_simple_command(self):
        """Test simple command execution (mock/dry run)"""
        try:
            payload = {
                "user_id": self.test_user_id,
                "command": "Test command - do not execute browser automation",
                "mode": "guided"
            }
            
            print("⏳ Testing command execution (this may take 10-15 seconds)...")
            response = requests.post(
                f"{self.api_url}/execute",
                json=payload,
                timeout=30  # Longer timeout for execution
            )
            
            success = response.status_code == 200
            
            if success:
                data = response.json()
                execution_success = data.get('success', False)
                message = data.get('message', '')
                execution_log = data.get('execution_log', [])
                details = f"Execution success: {execution_success}, Log entries: {len(execution_log)}, Message: {message}"
            else:
                details = f"Status code: {response.status_code}, Response: {response.text[:200]}"
                
            self.log_test("Execute Command", success, details)
            return success
        except Exception as e:
            self.log_test("Execute Command", False, str(e))
            return False

    def test_environment_check(self):
        """Test if required environment variables are configured"""
        try:
            # Try to make a request that would use the API key
            payload = {
                "user_id": self.test_user_id,
                "command": "Simple test",
                "mode": "guided"
            }
            
            response = requests.post(
                f"{self.api_url}/execute",
                json=payload,
                timeout=15
            )
            
            # Check if we get an API key error
            if response.status_code == 500:
                error_detail = response.json().get('detail', '')
                if 'API key not configured' in error_detail:
                    self.log_test("Environment Check", False, "EMERGENT_LLM_KEY not configured")
                    return False
            
            # If we get here, API key is likely configured
            self.log_test("Environment Check", True, "EMERGENT_LLM_KEY appears to be configured")
            return True
            
        except Exception as e:
            self.log_test("Environment Check", False, str(e))
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Sahayak Backend API Tests")
        print(f"Testing against: {self.base_url}")
        print(f"Test User ID: {self.test_user_id}")
        print("=" * 60)
        
        # Basic connectivity tests
        health_ok = self.test_health_endpoint()
        root_ok = self.test_root_endpoint()
        
        if not health_ok or not root_ok:
            print("❌ Basic connectivity failed. Stopping tests.")
            return False
        
        # Environment check
        env_ok = self.test_environment_check()
        
        # Memory system tests
        memory_save_ok = self.test_memory_save()
        memory_get_ok = self.test_memory_get()
        
        # History test
        history_ok = self.test_history_endpoint()
        
        # Command execution test (if environment is OK)
        execute_ok = False
        if env_ok:
            execute_ok = self.test_execute_simple_command()
        else:
            print("⚠️  Skipping command execution test due to environment issues")
        
        # Summary
        print("=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        critical_tests = [health_ok, root_ok, memory_save_ok, memory_get_ok, history_ok]
        critical_passed = sum(critical_tests)
        
        if critical_passed == len(critical_tests):
            print("✅ All critical backend functionality working")
            if env_ok and execute_ok:
                print("✅ Command execution also working")
            elif env_ok:
                print("⚠️  Command execution had issues")
            else:
                print("⚠️  Environment configuration needs attention")
            return True
        else:
            print("❌ Critical backend issues found")
            return False

def main():
    tester = SahayakAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())