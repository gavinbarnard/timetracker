import os
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import redis
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

class TimeTracker:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD', 'mypassword'),
            decode_responses=True
        )
        self.key_prefix = "timetracker:tasks:"
        
    def create_task(self, description: str, start_time: str, end_time: str, 
                   reference_tickets: List[str] = None) -> str:
        """Create a new time tracking task"""
        task_id = str(uuid.uuid4())
        task_key = f"{self.key_prefix}{task_id}"
        
        task_data = {
            "id": task_id,
            "description": description,
            "start_time": start_time,
            "end_time": end_time,
            "reference_tickets": reference_tickets or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Store as JSON in Redis
        self.redis_client.json().set(task_key, '$', task_data)
        
        # Add to index for querying
        self.redis_client.sadd("timetracker:task_ids", task_id)
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a specific task by ID"""
        task_key = f"{self.key_prefix}{task_id}"
        try:
            task_data = self.redis_client.json().get(task_key)
            return task_data
        except:
            return None
    
    def update_task(self, task_id: str, **kwargs) -> bool:
        """Update a task with new values"""
        task_key = f"{self.key_prefix}{task_id}"
        try:
            # Update the updated_at timestamp
            kwargs['updated_at'] = datetime.now().isoformat()
            
            # Update each field
            for field, value in kwargs.items():
                self.redis_client.json().set(task_key, f'$.{field}', value)
            
            return True
        except:
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        task_key = f"{self.key_prefix}{task_id}"
        try:
            self.redis_client.delete(task_key)
            self.redis_client.srem("timetracker:task_ids", task_id)
            return True
        except:
            return False
    
    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks"""
        task_ids = self.redis_client.smembers("timetracker:task_ids")
        tasks = []
        
        for task_id in task_ids:
            task = self.get_task(task_id)
            if task:
                tasks.append(task)
        
        # Sort by start_time
        tasks.sort(key=lambda x: x.get('start_time', ''))
        return tasks
    
    def get_tasks_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get tasks within a date range"""
        all_tasks = self.get_all_tasks()
        filtered_tasks = []
        
        for task in all_tasks:
            task_date = task.get('start_time', '')[:10]  # Extract date part
            if start_date <= task_date <= end_date:
                filtered_tasks.append(task)
        
        return filtered_tasks

# Initialize the time tracker
tracker = TimeTracker()

# Routes
@app.route('/')
def index():
    """Main page with calendar view"""
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks or tasks filtered by date range"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date and end_date:
        tasks = tracker.get_tasks_by_date_range(start_date, end_date)
    else:
        tasks = tracker.get_all_tasks()
    
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    data = request.get_json()
    
    if not data or 'description' not in data or 'start_time' not in data or 'end_time' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    task_id = tracker.create_task(
        description=data['description'],
        start_time=data['start_time'],
        end_time=data['end_time'],
        reference_tickets=data.get('reference_tickets', [])
    )
    
    return jsonify({'task_id': task_id}), 201

@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """Get a specific task"""
    task = tracker.get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify(task)

@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    success = tracker.update_task(task_id, **data)
    
    if not success:
        return jsonify({'error': 'Task not found or update failed'}), 404
    
    return jsonify({'message': 'Task updated successfully'})

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    success = tracker.delete_task(task_id)
    
    if not success:
        return jsonify({'error': 'Task not found or delete failed'}), 404
    
    return jsonify({'message': 'Task deleted successfully'})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        tracker.redis_client.ping()
        return jsonify({'status': 'healthy', 'redis': 'connected'})
    except:
        return jsonify({'status': 'unhealthy', 'redis': 'disconnected'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)