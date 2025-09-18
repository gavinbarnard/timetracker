#!/usr/bin/env python3
"""
Test the performance suite with just the 1-year dataset
"""

from performance_test import PerformanceTestSuite
import os

def test_single_dataset():
    """Test performance suite with 1-year dataset"""
    suite = PerformanceTestSuite()
    
    try:
        # Setup test environment
        suite.setup_test_redis()
        suite.start_test_app()
        
        # Test with 1-year dataset only
        data_file = "/tmp/tasks_1_year.json"
        if os.path.exists(data_file):
            print(f"\nTesting 1-year dataset performance...")
            result = suite.run_complete_test_suite(data_file, "1_year")
            
            if result:
                print("\nTest completed successfully!")
                summary = result['summary']
                print(f"Total Tasks: {summary['total_tasks']:.0f}")
                print(f"Year Query: {summary['year_avg_duration']:.3f}s")
                print(f"Month Query Avg: {summary['month_avg_duration']:.3f}s")
                print(f"Daily Query Avg: {summary['daily_avg_duration']:.3f}s")
            else:
                print("Test failed!")
        else:
            print(f"Dataset file not found: {data_file}")
            print("Run: python3 generate_test_data.py first")
    
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        suite.cleanup()

if __name__ == "__main__":
    test_single_dataset()