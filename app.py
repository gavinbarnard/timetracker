import os
import json
import uuid
import csv
import io
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from flask import Flask, request, jsonify, render_template, make_response
from flask_cors import CORS
import redis
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

class TimeTracker:
    def __init__(self):
        # Connect to Redis server (assumes Redis is running locally or configured separately)
        redis_password = os.getenv('REDIS_PASSWORD', None)
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=redis_password,  # None means no password authentication
            decode_responses=True
        )
        self.key_prefix = "timetracker:tasks:"
        self._ensure_search_index()
    
    def _ensure_search_index(self):
        """Create Redis search index for start_time if it doesn't exist"""
        try:
            # Check if index already exists
            existing_indexes = self.redis_client.execute_command('FT._LIST')
            if 'timetracker:startTimeIdx' not in existing_indexes:
                # Create index on start_time field as integer
                self.redis_client.execute_command(
                    'FT.CREATE', 'timetracker:startTimeIdx',
                    'ON', 'JSON',
                    'SCHEMA', '$.start_time', 'AS', 'start_time', 'NUMERIC'
                )
        except Exception as e:
            # Index creation might fail if it already exists, which is okay
            pass
    
    def _iso_to_epoch_ms(self, iso_string: str) -> int:
        """Convert ISO format string to epoch milliseconds"""
        try:
            dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
            return int(dt.timestamp() * 1000)
        except (ValueError, AttributeError):
            # If conversion fails, assume it's already an integer
            return int(iso_string) if isinstance(iso_string, (str, int, float)) else 0
    
    def _epoch_ms_to_iso(self, epoch_ms: int) -> str:
        """Convert epoch milliseconds to ISO format string"""
        try:
            dt = datetime.fromtimestamp(epoch_ms / 1000)
            return dt.isoformat()
        except (ValueError, TypeError):
            # If conversion fails, return current time
            return datetime.now().isoformat()
    
    def _normalize_timestamp(self, timestamp) -> int:
        """Normalize timestamp to epoch milliseconds, handling both formats"""
        if isinstance(timestamp, str):
            return self._iso_to_epoch_ms(timestamp)
        elif isinstance(timestamp, (int, float)):
            return int(timestamp)
        else:
            return int(datetime.now().timestamp() * 1000)
        
    def create_task(self, description: str, start_time: str, end_time: str, 
                   reference_tickets: List[str] = None) -> str:
        """Create a new time tracking task"""
        task_id = str(uuid.uuid4())
        task_key = f"{self.key_prefix}{task_id}"
        
        # Convert timestamps to epoch milliseconds
        start_time_ms = self._normalize_timestamp(start_time)
        end_time_ms = self._normalize_timestamp(end_time)
        created_at_ms = int(datetime.now().timestamp() * 1000)
        
        task_data = {
            "id": task_id,
            "description": description,
            "start_time": start_time_ms,
            "end_time": end_time_ms,
            "reference_tickets": reference_tickets or [],
            "created_at": created_at_ms,
            "updated_at": created_at_ms
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
            kwargs['updated_at'] = int(datetime.now().timestamp() * 1000)
            
            # Convert timestamp fields to epoch milliseconds if they're being updated
            if 'start_time' in kwargs:
                kwargs['start_time'] = self._normalize_timestamp(kwargs['start_time'])
            if 'end_time' in kwargs:
                kwargs['end_time'] = self._normalize_timestamp(kwargs['end_time'])
            
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
        
        # Sort by start_time (handling both integer and string formats)
        tasks.sort(key=lambda x: self._normalize_timestamp(x.get('start_time', 0)))
        return tasks
    
    def get_tasks_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get tasks within a date range"""
        all_tasks = self.get_all_tasks()
        filtered_tasks = []
        
        # Convert date strings to epoch milliseconds for comparison
        start_date_ms = self._iso_to_epoch_ms(start_date + "T00:00:00")
        end_date_ms = self._iso_to_epoch_ms(end_date + "T23:59:59")
        
        for task in all_tasks:
            task_start_time = self._normalize_timestamp(task.get('start_time', 0))
            if start_date_ms <= task_start_time <= end_date_ms:
                filtered_tasks.append(task)
        
        return filtered_tasks
    
    def calculate_task_hours(self, task: Dict) -> float:
        """Calculate the duration of a task in hours"""
        try:
            start_time_ms = self._normalize_timestamp(task['start_time'])
            end_time_ms = self._normalize_timestamp(task['end_time'])
            duration_ms = end_time_ms - start_time_ms
            return round(duration_ms / (1000 * 3600), 2)  # Convert to hours and round to 2 decimal places
        except (ValueError, KeyError):
            return 0.0
    
    def export_tasks_to_csv(self, start_date: str, end_date: str) -> str:
        """Export tasks within date range to CSV format"""
        tasks = self.get_tasks_by_date_range(start_date, end_date)
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Date', 
            'Description', 
            'Reference Tickets',
            'Start Time', 
            'End Time', 
            'Duration (Hours)'
        ])
        
        total_hours = 0.0
        
        # Write task data
        for task in tasks:
            hours = self.calculate_task_hours(task)
            total_hours += hours
            
            # Convert timestamps to display format
            start_time_ms = self._normalize_timestamp(task.get('start_time', 0))
            end_time_ms = self._normalize_timestamp(task.get('end_time', 0))
            
            start_dt = datetime.fromtimestamp(start_time_ms / 1000)
            end_dt = datetime.fromtimestamp(end_time_ms / 1000)
            
            date = start_dt.strftime('%Y-%m-%d')
            start_display = start_dt.strftime('%H:%M')
            end_display = end_dt.strftime('%H:%M')
            
            # Format reference tickets
            tickets = task.get('reference_tickets', [])
            tickets_str = ', '.join(tickets) if tickets else ''
            
            writer.writerow([
                date,
                task.get('description', ''),
                tickets_str,
                start_display,
                end_display,
                hours
            ])
        
        # Add total row
        writer.writerow([])  # Empty row
        writer.writerow(['', '', '', '', 'TOTAL HOURS:', total_hours])
        
        return output.getvalue()

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
    
    # Validate reference tickets are provided
    reference_tickets = data.get('reference_tickets', [])
    if not reference_tickets or len(reference_tickets) == 0:
        return jsonify({'error': 'At least one reference ticket is required'}), 400
    
    task_id = tracker.create_task(
        description=data['description'],
        start_time=data['start_time'],
        end_time=data['end_time'],
        reference_tickets=reference_tickets
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
    
    # If reference_tickets are being updated, validate they are provided
    if 'reference_tickets' in data:
        reference_tickets = data['reference_tickets']
        if not reference_tickets or len(reference_tickets) == 0:
            return jsonify({'error': 'At least one reference ticket is required'}), 400
    
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

@app.route('/api/export/csv', methods=['GET'])
def export_tasks_csv():
    """Export tasks to CSV format"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'error': 'start_date and end_date parameters are required'}), 400
    
    try:
        csv_data = tracker.export_tasks_to_csv(start_date, end_date)
        
        # Create response with CSV data
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=timetracker_export_{start_date}_to_{end_date}.csv'
        
        return response
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)