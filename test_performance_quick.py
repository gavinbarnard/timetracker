#!/usr/bin/env python3
"""
Quick test of the performance test suite with minimal data
"""

import subprocess
import time
import json
import requests
import redis
from datetime import datetime, timedelta
import os

def quick_test():
    """Run a quick test with minimal data"""
    
    # Start test Redis
    print("Starting test Redis instance...")
    try:
        subprocess.run(['docker', 'stop', 'redis-test-quick'], capture_output=True, check=False)
        subprocess.run(['docker', 'rm', 'redis-test-quick'], capture_output=True, check=False)
        
        result = subprocess.run([
            'docker', 'run', '-d',
            '--name', 'redis-test-quick',
            '-p', '6381:6379',
            'redis/redis-stack:latest'
        ], capture_output=True, text=True, check=True)
        
        print("Waiting for Redis to start...")
        time.sleep(8)
        
        # Test Redis connection
        redis_client = redis.Redis(host='localhost', port=6381, decode_responses=True)
        redis_client.ping()
        redis_client.execute_command('JSON.SET', 'test', '$', '{"test": true}')
        print("Redis test instance ready!")
        
        # Start test Flask app
        print("Starting test Flask app...")
        env = os.environ.copy()
        env['REDIS_PORT'] = '6381'
        env['FLASK_PORT'] = '5002'
        
        app_process = subprocess.Popen([
            'python3', 'app.py'
        ], env=env)
        
        # Wait for app
        print("Waiting for Flask app...")
        time.sleep(5)
        
        # Test app health
        response = requests.get('http://localhost:5002/health')
        print(f"Health check: {response.status_code} - {response.json()}")
        
        # Create a few test tasks
        print("Creating test tasks...")
        for i in range(5):
            task_data = {
                "description": f"Test task {i+1}",
                "start_time": (datetime.now() - timedelta(hours=i*2)).isoformat(),
                "end_time": (datetime.now() - timedelta(hours=i*2-1)).isoformat(),
                "reference_tickets": [f"TEST-{i+1}"]
            }
            
            response = requests.post(
                'http://localhost:5002/api/tasks',
                json=task_data
            )
            print(f"Created task {i+1}: {response.status_code}")
        
        # Test API performance
        print("Testing API performance...")
        start_time = time.time()
        response = requests.get('http://localhost:5002/api/tasks')
        end_time = time.time()
        
        tasks = response.json()
        print(f"Retrieved {len(tasks)} tasks in {end_time - start_time:.3f} seconds")
        
        # Cleanup
        print("Cleaning up...")
        app_process.terminate()
        app_process.wait()
        subprocess.run(['docker', 'stop', 'redis-test-quick'], capture_output=True)
        subprocess.run(['docker', 'rm', 'redis-test-quick'], capture_output=True)
        
        print("Quick test completed successfully!")
        
    except Exception as e:
        print(f"Quick test failed: {e}")
        # Cleanup on error
        try:
            app_process.terminate()
            subprocess.run(['docker', 'stop', 'redis-test-quick'], capture_output=True)
            subprocess.run(['docker', 'rm', 'redis-test-quick'], capture_output=True)
        except:
            pass

if __name__ == "__main__":
    quick_test()