#!/usr/bin/env python3
"""
Test data generation script for performance testing.
Generates realistic time tracking tasks over specified time periods.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict
import json

class TaskDataGenerator:
    def __init__(self):
        # Common task descriptions for realistic data
        self.task_descriptions = [
            "Code review for feature implementation",
            "Bug fixing and debugging",
            "Meeting with stakeholders",
            "Documentation updates",
            "Unit test development",
            "System architecture planning",
            "Database optimization",
            "Frontend component development",
            "API endpoint implementation",
            "Performance monitoring",
            "Security audit and fixes",
            "DevOps pipeline setup",
            "Client communication",
            "Technical research",
            "Project planning session",
            "Quality assurance testing",
            "Production deployment",
            "Incident response and resolution",
            "Team standup meeting",
            "Design system updates"
        ]
        
        # Reference ticket patterns
        self.ticket_prefixes = ["PROJ", "BUG", "FEAT", "TECH", "SEC", "DOC", "TEST"]
        
    def generate_reference_tickets(self, count: int = None) -> List[str]:
        """Generate realistic reference ticket numbers"""
        if count is None:
            count = random.randint(1, 3)
        
        tickets = []
        for _ in range(count):
            prefix = random.choice(self.ticket_prefixes)
            number = random.randint(100, 9999)
            tickets.append(f"{prefix}-{number}")
        
        return tickets
    
    def generate_task_duration(self) -> float:
        """Generate realistic task duration in hours"""
        # Most tasks are 0.5-4 hours, with some longer ones
        if random.random() < 0.7:  # 70% short to medium tasks
            return round(random.uniform(0.5, 3.0), 2)
        elif random.random() < 0.9:  # 20% medium to long tasks  
            return round(random.uniform(3.0, 6.0), 2)
        else:  # 10% very long tasks
            return round(random.uniform(6.0, 8.0), 2)
    
    def is_work_day(self, date: datetime) -> bool:
        """Determine if a date is likely to have work tasks"""
        # Monday = 0, Sunday = 6
        weekday = date.weekday()
        
        if weekday < 5:  # Monday to Friday
            return random.random() < 0.95  # 95% chance of work on weekdays
        elif weekday == 5:  # Saturday
            return random.random() < 0.15  # 15% chance of work on Saturday
        else:  # Sunday
            return random.random() < 0.05  # 5% chance of work on Sunday
    
    def generate_daily_tasks(self, date: datetime) -> List[Dict]:
        """Generate tasks for a specific day"""
        if not self.is_work_day(date):
            return []
        
        # Determine number of tasks for the day (1-12 with weighted distribution)
        if random.random() < 0.4:  # 40% chance of 1-3 tasks (light day)
            num_tasks = random.randint(1, 3)
        elif random.random() < 0.8:  # 40% chance of 4-8 tasks (normal day)
            num_tasks = random.randint(4, 8)
        else:  # 20% chance of 9-12 tasks (busy day)
            num_tasks = random.randint(9, 12)
        
        tasks = []
        total_hours = 0
        max_daily_hours = 8.0
        
        # Generate start time for the day (8 AM to 10 AM typically)
        start_hour = random.randint(8, 10)
        current_time = date.replace(hour=start_hour, minute=random.randint(0, 30), second=0, microsecond=0)
        
        for i in range(num_tasks):
            # Check if we have room for more tasks
            if total_hours >= max_daily_hours:
                break
                
            # Generate task duration, ensuring we don't exceed daily limit
            duration = self.generate_task_duration()
            if total_hours + duration > max_daily_hours:
                duration = max_daily_hours - total_hours
                if duration < 0.25:  # Skip very short tasks
                    break
            
            # Create task
            task = {
                "id": str(uuid.uuid4()),
                "description": random.choice(self.task_descriptions),
                "start_time": current_time.isoformat(),
                "end_time": (current_time + timedelta(hours=duration)).isoformat(),
                "reference_tickets": self.generate_reference_tickets(),
                "created_at": current_time.isoformat(),
                "updated_at": current_time.isoformat()
            }
            
            tasks.append(task)
            total_hours += duration
            
            # Move to next task with a break (5-60 minutes)
            break_duration = random.randint(5, 60)
            current_time = current_time + timedelta(hours=duration, minutes=break_duration)
        
        return tasks
    
    def generate_year_data(self, year: int = 2024) -> List[Dict]:
        """Generate a full year of task data"""
        tasks = []
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        
        current_date = start_date
        while current_date <= end_date:
            daily_tasks = self.generate_daily_tasks(current_date)
            tasks.extend(daily_tasks)
            current_date += timedelta(days=1)
        
        return tasks
    
    def generate_multi_year_data(self, years: int, start_year: int = 2022) -> List[Dict]:
        """Generate multiple years of task data"""
        all_tasks = []
        
        for year_offset in range(years):
            year = start_year + year_offset
            year_tasks = self.generate_year_data(year)
            all_tasks.extend(year_tasks)
            print(f"Generated {len(year_tasks)} tasks for year {year}")
        
        return all_tasks
    
    def save_to_json(self, tasks: List[Dict], filename: str):
        """Save tasks to JSON file"""
        with open(filename, 'w') as f:
            json.dump(tasks, f, indent=2)
        print(f"Saved {len(tasks)} tasks to {filename}")

def main():
    """Generate test datasets"""
    generator = TaskDataGenerator()
    
    print("Generating test datasets...")
    print("=" * 50)
    
    # Generate 1 year of data
    print("Generating 1 year of data...")
    year_1_data = generator.generate_year_data(2024)
    generator.save_to_json(year_1_data, "/tmp/tasks_1_year.json")
    
    # Generate 2 years of data
    print("\nGenerating 2 years of data...")
    year_2_data = generator.generate_multi_year_data(2, 2023)
    generator.save_to_json(year_2_data, "/tmp/tasks_2_years.json")
    
    # Generate 4 years of data
    print("\nGenerating 4 years of data...")
    year_4_data = generator.generate_multi_year_data(4, 2021)
    generator.save_to_json(year_4_data, "/tmp/tasks_4_years.json")
    
    print("\n" + "=" * 50)
    print("Data generation complete!")
    print(f"1 year dataset: {len(year_1_data)} tasks")
    print(f"2 year dataset: {len(year_2_data)} tasks")
    print(f"4 year dataset: {len(year_4_data)} tasks")

if __name__ == "__main__":
    main()