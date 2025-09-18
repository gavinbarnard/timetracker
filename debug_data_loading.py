#!/usr/bin/env python3
"""
Debug script to check data loading and date range queries
"""

import subprocess
import time
import json
import redis
from datetime import datetime
import os

def debug_data_loading():
    """Debug data loading and date range queries"""
    
    # Start test Redis
    print("Starting debug Redis instance...")
    try:
        subprocess.run(['docker', 'stop', 'redis-debug'], capture_output=True, check=False)
        subprocess.run(['docker', 'rm', 'redis-debug'], capture_output=True, check=False)
        
        result = subprocess.run([
            'docker', 'run', '-d',
            '--name', 'redis-debug',
            '-p', '6382:6379',
            'redis/redis-stack:latest'
        ], capture_output=True, text=True, check=True)
        
        print("Waiting for Redis...")
        time.sleep(8)
        
        # Test Redis connection
        redis_client = redis.Redis(host='localhost', port=6382, decode_responses=True)
        redis_client.ping()
        print("Redis ready!")
        
        # Load sample data
        print("\nLoading sample data...")
        with open('/tmp/tasks_1_year.json', 'r') as f:
            tasks = json.load(f)
        
        print(f"Found {len(tasks)} tasks in JSON file")
        
        # Check first few tasks
        print("\nFirst 3 tasks from JSON:")
        for i in range(min(3, len(tasks))):
            task = tasks[i]
            print(f"  Task {i+1}:")
            print(f"    ID: {task['id']}")
            print(f"    Description: {task['description']}")
            print(f"    Start: {task['start_time']}")
            print(f"    End: {task['end_time']}")
        
        # Load data manually
        loaded_count = 0
        for task in tasks[:50]:  # Load first 50 tasks for testing
            # Convert timestamps
            start_time = datetime.fromisoformat(task['start_time'].replace('Z', '')).timestamp() * 1000
            end_time = datetime.fromisoformat(task['end_time'].replace('Z', '')).timestamp() * 1000
            created_at = datetime.fromisoformat(task['created_at'].replace('Z', '')).timestamp() * 1000
            
            task_data = {
                "id": task['id'],
                "description": task['description'],
                "start_time": int(start_time),
                "end_time": int(end_time),
                "reference_tickets": task['reference_tickets'],
                "created_at": int(created_at),
                "updated_at": int(created_at)
            }
            
            # Store in Redis
            task_key = f"timetracker:tasks:{task['id']}"
            redis_client.execute_command('JSON.SET', task_key, '$', json.dumps(task_data))
            redis_client.sadd("timetracker:task_ids", task['id'])
            loaded_count += 1
        
        print(f"\nLoaded {loaded_count} tasks into Redis")
        
        # Check what's in Redis
        task_ids = redis_client.smembers("timetracker:task_ids")
        print(f"Task IDs in Redis: {len(task_ids)}")
        
        # Get a sample task from Redis
        if task_ids:
            sample_id = list(task_ids)[0]
            sample_task_key = f"timetracker:tasks:{sample_id}"
            sample_data = redis_client.execute_command('JSON.GET', sample_task_key)
            print(f"\nSample task from Redis:")
            print(f"  Key: {sample_task_key}")
            print(f"  Data: {sample_data}")
            
            # Parse the data
            task_obj = json.loads(sample_data)
            start_ms = task_obj['start_time']
            start_dt = datetime.fromtimestamp(start_ms / 1000)
            print(f"  Start timestamp: {start_ms}")
            print(f"  Start datetime: {start_dt}")
        
        # Test date range conversion
        print(f"\nTesting date range conversion:")
        test_start = "2024-01-01T00:00:00"
        test_end = "2024-12-31T23:59:59"
        
        start_dt = datetime.fromisoformat(test_start)
        end_dt = datetime.fromisoformat(test_end)
        
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)
        
        print(f"  Query start: {test_start} -> {start_ms}")
        print(f"  Query end: {test_end} -> {end_ms}")
        
        # Check if Redis search index exists
        try:
            indexes = redis_client.execute_command('FT._LIST')
            print(f"\nRedis indexes: {indexes}")
        except Exception as e:
            print(f"\nNo Redis search indexes: {e}")
        
        # Try to create search index manually
        try:
            redis_client.execute_command(
                'FT.CREATE', 'timetracker:startTimeIdx',
                'ON', 'JSON',
                'SCHEMA', '$.start_time', 'AS', 'start_time', 'NUMERIC'
            )
            print("Created search index successfully")
        except Exception as e:
            print(f"Failed to create search index: {e}")
        
        # Test search query
        try:
            search_result = redis_client.execute_command(
                'FT.SEARCH', 'timetracker:startTimeIdx',
                f'@start_time:[{start_ms} {end_ms}]'
            )
            print(f"\nSearch result: {search_result}")
        except Exception as e:
            print(f"Search failed: {e}")
        
        # Cleanup
        print("\nCleaning up...")
        subprocess.run(['docker', 'stop', 'redis-debug'], capture_output=True)
        subprocess.run(['docker', 'rm', 'redis-debug'], capture_output=True)
        
    except Exception as e:
        print(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_data_loading()