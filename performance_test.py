#!/usr/bin/env python3
"""
Performance test suite for Time Tracker API backend.
Uses a dedicated Redis instance on port 6380 to avoid conflicts.
"""

import subprocess
import time
import json
import statistics
import requests
import redis
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import os
import sys

class PerformanceTestSuite:
    def __init__(self, test_port: int = 6380):
        self.test_port = test_port
        self.redis_container = None
        self.redis_client = None
        self.app_process = None
        self.base_url = "http://localhost:5001"  # Use different port for test app
        
    def setup_test_redis(self):
        """Start a dedicated Redis Stack instance for testing"""
        try:
            # Stop any existing test container
            subprocess.run(['docker', 'stop', 'redis-test-performance'], 
                         capture_output=True, check=False)
            subprocess.run(['docker', 'rm', 'redis-test-performance'], 
                         capture_output=True, check=False)
            
            # Start new Redis Stack container on test port
            print(f"Starting Redis Stack on port {self.test_port} for performance testing...")
            result = subprocess.run([
                'docker', 'run', '-d',
                '--name', 'redis-test-performance',
                '-p', f'{self.test_port}:6379',
                'redis/redis-stack:latest'
            ], capture_output=True, text=True, check=True)
            
            self.redis_container = result.stdout.strip()
            print(f"Redis test container started: {self.redis_container[:12]}")
            
            # Wait for Redis to be ready
            print("Waiting for Redis to be ready...")
            time.sleep(5)
            
            # Test connection
            self.redis_client = redis.Redis(
                host='localhost', 
                port=self.test_port, 
                decode_responses=True
            )
            
            # Verify Redis JSON functionality
            for i in range(10):  # Try for 10 seconds
                try:
                    self.redis_client.ping()
                    self.redis_client.execute_command('JSON.SET', 'test', '$', '{"test": true}')
                    self.redis_client.execute_command('JSON.GET', 'test')
                    print("Redis test instance ready!")
                    break
                except Exception as e:
                    if i == 9:
                        raise Exception(f"Redis test instance failed to start: {e}")
                    time.sleep(1)
                    
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to start Redis test container: {e.stderr}")
    
    def start_test_app(self):
        """Start Flask app configured to use test Redis instance"""
        print("Starting test Flask application...")
        
        # Set environment variables for test Redis and Flask port
        env = os.environ.copy()
        env['REDIS_PORT'] = str(self.test_port)
        env['FLASK_PORT'] = '5001'
        env['FLASK_ENV'] = 'testing'
        
        # Get the directory containing this script (where app.py should be located)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Start Flask app on different port
        self.app_process = subprocess.Popen([
            'python3', 'app.py'
        ], env=env, cwd=script_dir)
        
        # Wait for app to start
        print("Waiting for Flask app to start...")
        for i in range(20):  # Try for 20 seconds
            try:
                response = requests.get(f"{self.base_url}/health", timeout=1)
                if response.status_code == 200:
                    print("Test Flask app ready!")
                    return
            except:
                pass
            time.sleep(1)
        
        raise Exception("Failed to start test Flask application")
    
    def load_test_data(self, data_file: str) -> int:
        """Load test data into the test Redis instance"""
        print(f"Loading test data from {data_file}...")
        
        with open(data_file, 'r') as f:
            tasks = json.load(f)
        
        # First ensure the search index is created
        print("Creating Redis search index...")
        try:
            # Drop index if it exists
            try:
                self.redis_client.execute_command('FT.DROPINDEX', 'timetracker:startTimeIdx')
            except:
                pass
            
            # Create fresh index
            self.redis_client.execute_command(
                'FT.CREATE', 'timetracker:startTimeIdx',
                'ON', 'JSON',
                'SCHEMA', '$.start_time', 'AS', 'start_time', 'NUMERIC'
            )
            print("Search index created successfully")
        except Exception as e:
            print(f"Warning: Could not create search index: {e}")
        
        loaded_count = 0
        batch_size = 100
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            
            for task in batch:
                # Convert ISO timestamps to epoch milliseconds for consistency
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
                self.redis_client.execute_command('JSON.SET', task_key, '$', json.dumps(task_data))
                self.redis_client.sadd("timetracker:task_ids", task['id'])
                loaded_count += 1
            
            if i % (batch_size * 10) == 0:
                print(f"Loaded {loaded_count}/{len(tasks)} tasks...")
        
        print(f"Loaded {loaded_count} tasks into test database")
        
        # Verify data loading with a quick search
        try:
            # Test with a broad date range
            start_ms = int(datetime(2024, 1, 1).timestamp() * 1000)
            end_ms = int(datetime(2024, 12, 31, 23, 59, 59).timestamp() * 1000)
            
            search_result = self.redis_client.execute_command(
                'FT.SEARCH', 'timetracker:startTimeIdx',
                f'@start_time:[{start_ms} {end_ms}]'
            )
            
            if search_result and len(search_result) > 1:
                found_count = search_result[0]
                print(f"Verification: Search index found {found_count} tasks for 2024")
            else:
                print("Warning: Search index verification found no tasks")
                
        except Exception as e:
            print(f"Warning: Could not verify search index: {e}")
        
        return loaded_count
    
    def measure_api_performance(self, endpoint: str, params: Dict = None, iterations: int = 10) -> Dict:
        """Measure API endpoint performance"""
        times = []
        errors = 0
        
        for i in range(iterations):
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_data = response.json()
                    task_count = len(response_data) if isinstance(response_data, list) else 1
                    times.append({
                        'duration': end_time - start_time,
                        'task_count': task_count
                    })
                    
                    # Debug output for first iteration
                    if i == 0:
                        print(f"  API response: {task_count} tasks returned")
                        if params:
                            print(f"  Query params: {params}")
                else:
                    errors += 1
                    print(f"Error response {response.status_code} for {endpoint}")
                    
            except Exception as e:
                errors += 1
                print(f"Request error for {endpoint}: {e}")
        
        if not times:
            return {'error': 'All requests failed'}
        
        durations = [t['duration'] for t in times]
        task_counts = [t['task_count'] for t in times]
        
        return {
            'endpoint': endpoint,
            'params': params,
            'iterations': len(times),
            'errors': errors,
            'avg_duration': statistics.mean(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'median_duration': statistics.median(durations),
            'std_deviation': statistics.stdev(durations) if len(durations) > 1 else 0,
            'avg_task_count': statistics.mean(task_counts),
            'tasks_per_second': statistics.mean(task_counts) / statistics.mean(durations)
        }
    
    def run_year_performance_test(self, year: int = 2024) -> Dict:
        """Test performance for retrieving a full year of data"""
        print(f"\nTesting full year performance ({year})...")
        
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        return self.measure_api_performance('/api/tasks', params, iterations=5)
    
    def run_month_performance_tests(self, year: int = 2024) -> List[Dict]:
        """Test performance for each month of the year"""
        print(f"\nTesting monthly performance ({year})...")
        
        results = []
        for month in range(1, 13):
            month_start = f"{year}-{month:02d}-01"
            
            # Calculate last day of month
            if month == 12:
                next_month = datetime(year + 1, 1, 1)
            else:
                next_month = datetime(year, month + 1, 1)
            last_day = next_month - timedelta(days=1)
            month_end = last_day.strftime("%Y-%m-%d")
            
            params = {
                'start_date': month_start,
                'end_date': month_end
            }
            
            result = self.measure_api_performance('/api/tasks', params, iterations=3)
            result['month'] = month
            result['month_name'] = datetime(year, month, 1).strftime("%B")
            results.append(result)
            
            print(f"  {result['month_name']}: {result['avg_duration']:.3f}s avg, {result['avg_task_count']:.0f} tasks")
        
        return results
    
    def run_daily_performance_sample(self, year: int = 2024, sample_days: int = 30) -> List[Dict]:
        """Test performance for a sample of individual days"""
        print(f"\nTesting daily performance (sample of {sample_days} days from {year})...")
        
        results = []
        start_date = datetime(year, 1, 1)
        
        for i in range(sample_days):
            # Sample days throughout the year
            day_offset = i * (365 // sample_days)
            test_date = start_date + timedelta(days=day_offset)
            date_str = test_date.strftime("%Y-%m-%d")
            
            params = {
                'start_date': date_str,
                'end_date': date_str
            }
            
            result = self.measure_api_performance('/api/tasks', params, iterations=5)
            result['date'] = date_str
            results.append(result)
        
        return results
    
    def generate_performance_report(self, year_result: Dict, month_results: List[Dict], 
                                  daily_results: List[Dict], dataset_size: str):
        """Generate comprehensive performance report"""
        print("\n" + "=" * 80)
        print(f"PERFORMANCE TEST REPORT - {dataset_size.upper()} DATASET")
        print("=" * 80)
        
        # Year performance
        print(f"\nFULL YEAR PERFORMANCE:")
        print(f"  Average Duration: {year_result['avg_duration']:.3f} seconds")
        print(f"  Median Duration:  {year_result['median_duration']:.3f} seconds")
        print(f"  Min Duration:     {year_result['min_duration']:.3f} seconds")
        print(f"  Max Duration:     {year_result['max_duration']:.3f} seconds")
        print(f"  Standard Dev:     {year_result['std_deviation']:.3f} seconds")
        print(f"  Tasks Retrieved:  {year_result['avg_task_count']:.0f}")
        print(f"  Tasks/Second:     {year_result['tasks_per_second']:.1f}")
        
        # Monthly summary
        month_durations = [r['avg_duration'] for r in month_results if 'avg_duration' in r]
        month_task_counts = [r['avg_task_count'] for r in month_results if 'avg_task_count' in r]
        
        print(f"\nMONTHLY PERFORMANCE SUMMARY:")
        print(f"  Average Duration: {statistics.mean(month_durations):.3f} seconds")
        print(f"  Min Duration:     {min(month_durations):.3f} seconds")
        print(f"  Max Duration:     {max(month_durations):.3f} seconds")
        print(f"  Avg Tasks/Month:  {statistics.mean(month_task_counts):.1f}")
        
        # Daily summary
        daily_durations = [r['avg_duration'] for r in daily_results if 'avg_duration' in r]
        daily_task_counts = [r['avg_task_count'] for r in daily_results if 'avg_task_count' in r]
        
        print(f"\nDAILY PERFORMANCE SUMMARY:")
        print(f"  Average Duration: {statistics.mean(daily_durations):.3f} seconds")
        print(f"  Min Duration:     {min(daily_durations):.3f} seconds")
        print(f"  Max Duration:     {max(daily_durations):.3f} seconds")
        print(f"  Avg Tasks/Day:    {statistics.mean(daily_task_counts):.1f}")
        
        # Performance characteristics
        print(f"\nPERFORMANCE CHARACTERISTICS:")
        if year_result['avg_duration'] < 0.1:
            print("  ✓ Excellent performance - sub-100ms response times")
        elif year_result['avg_duration'] < 0.5:
            print("  ✓ Good performance - sub-500ms response times")
        elif year_result['avg_duration'] < 1.0:
            print("  ⚠ Acceptable performance - sub-1s response times")
        else:
            print("  ⚠ Performance may need optimization - >1s response times")
        
        return {
            'dataset_size': dataset_size,
            'year_performance': year_result,
            'monthly_performance': month_results,
            'daily_performance': daily_results,
            'summary': {
                'year_avg_duration': year_result['avg_duration'],
                'month_avg_duration': statistics.mean(month_durations),
                'daily_avg_duration': statistics.mean(daily_durations),
                'total_tasks': year_result['avg_task_count']
            }
        }
    
    def run_complete_test_suite(self, data_file: str, dataset_name: str):
        """Run complete performance test suite for a dataset"""
        try:
            # Load test data
            task_count = self.load_test_data(data_file)
            
            # Test with 2024 data (most recent year in dataset)
            year_result = self.run_year_performance_test(2024)
            month_results = self.run_month_performance_tests(2024)
            daily_results = self.run_daily_performance_sample(2024, 20)
            
            # Generate report
            report = self.generate_performance_report(
                year_result, month_results, daily_results, dataset_name
            )
            
            # Save detailed results
            results_file = f"/tmp/performance_results_{dataset_name}.json"
            with open(results_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\nDetailed results saved to: {results_file}")
            
            return report
            
        except Exception as e:
            print(f"Error running test suite: {e}")
            return None
    
    def cleanup(self):
        """Clean up test resources"""
        print("\nCleaning up test resources...")
        
        if self.app_process:
            self.app_process.terminate()
            self.app_process.wait()
        
        if self.redis_container:
            subprocess.run(['docker', 'stop', 'redis-test-performance'], 
                         capture_output=True, check=False)
            subprocess.run(['docker', 'rm', 'redis-test-performance'], 
                         capture_output=True, check=False)

def main():
    """Run performance tests on all datasets"""
    suite = PerformanceTestSuite()
    
    try:
        # Setup test environment
        suite.setup_test_redis()
        suite.start_test_app()
        
        # Test datasets
        datasets = [
            ("/tmp/tasks_1_year.json", "1_year"),
            ("/tmp/tasks_2_years.json", "2_years"),
            ("/tmp/tasks_4_years.json", "4_years")
        ]
        
        all_results = []
        
        for data_file, dataset_name in datasets:
            if os.path.exists(data_file):
                print(f"\n{'='*80}")
                print(f"TESTING {dataset_name.upper()} DATASET")
                print(f"{'='*80}")
                
                result = suite.run_complete_test_suite(data_file, dataset_name)
                if result:
                    all_results.append(result)
                
                # Clear test data between datasets
                suite.redis_client.flushdb()
            else:
                print(f"Dataset file not found: {data_file}")
        
        # Generate comparison report
        if all_results:
            print("\n" + "=" * 80)
            print("PERFORMANCE COMPARISON ACROSS DATASETS")
            print("=" * 80)
            
            for result in all_results:
                summary = result['summary']
                print(f"\n{result['dataset_size'].upper()}:")
                print(f"  Total Tasks:      {summary['total_tasks']:.0f}")
                print(f"  Year Query:       {summary['year_avg_duration']:.3f}s")
                print(f"  Month Query Avg:  {summary['month_avg_duration']:.3f}s")
                print(f"  Daily Query Avg:  {summary['daily_avg_duration']:.3f}s")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        suite.cleanup()

if __name__ == "__main__":
    main()