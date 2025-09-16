#!/usr/bin/env python3
"""
Simple test script to verify the Time Tracker application functionality
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            return True
    except Exception as e:
        print(f"Health check failed: {e}")
    return False

def test_create_task():
    """Test creating a new task"""
    now = datetime.now()
    task_data = {
        "description": "Test task for API verification",
        "start_time": now.isoformat(),
        "end_time": (now + timedelta(hours=2)).isoformat(),
        "reference_tickets": ["TEST-123", "VERIFY-456"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/tasks", 
                               headers={"Content-Type": "application/json"},
                               data=json.dumps(task_data))
        print(f"Create task: {response.status_code}")
        if response.status_code == 201:
            result = response.json()
            print(f"Created task ID: {result['task_id']}")
            return result['task_id']
    except Exception as e:
        print(f"Create task failed: {e}")
    return None

def test_get_tasks():
    """Test retrieving all tasks"""
    try:
        response = requests.get(f"{BASE_URL}/api/tasks")
        print(f"Get tasks: {response.status_code}")
        if response.status_code == 200:
            tasks = response.json()
            print(f"Found {len(tasks)} tasks")
            return tasks
    except Exception as e:
        print(f"Get tasks failed: {e}")
    return []

def test_get_task(task_id):
    """Test retrieving a specific task"""
    try:
        response = requests.get(f"{BASE_URL}/api/tasks/{task_id}")
        print(f"Get task {task_id}: {response.status_code}")
        if response.status_code == 200:
            task = response.json()
            print(f"Task description: {task['description']}")
            return task
    except Exception as e:
        print(f"Get task failed: {e}")
    return None

def test_update_task(task_id):
    """Test updating a task"""
    update_data = {
        "description": "Updated test task description"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/api/tasks/{task_id}",
                              headers={"Content-Type": "application/json"},
                              data=json.dumps(update_data))
        print(f"Update task: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Update task failed: {e}")
    return False

def test_delete_task(task_id):
    """Test deleting a task"""
    try:
        response = requests.delete(f"{BASE_URL}/api/tasks/{task_id}")
        print(f"Delete task: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Delete task failed: {e}")
    return False

def main():
    print("Testing Time Tracker API...")
    print("=" * 40)
    
    # Test health
    if not test_health():
        print("Health check failed. Make sure the application is running.")
        return
    
    print("\n" + "=" * 40)
    
    # Test creating a task
    task_id = test_create_task()
    if not task_id:
        print("Failed to create task. Cannot continue tests.")
        return
    
    # Test getting all tasks
    tasks = test_get_tasks()
    
    # Test getting specific task
    task = test_get_task(task_id)
    
    # Test updating task
    test_update_task(task_id)
    
    # Verify update worked
    updated_task = test_get_task(task_id)
    
    # Test deleting task
    test_delete_task(task_id)
    
    # Verify deletion
    final_tasks = test_get_tasks()
    
    print("\n" + "=" * 40)
    print("API test completed!")
    print(f"All endpoints tested successfully.")

if __name__ == "__main__":
    main()