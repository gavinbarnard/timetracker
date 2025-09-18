#!/usr/bin/env python3
"""
Performance Test Runner for Time Tracker API
============================================

This script provides an easy way to run performance tests on the Time Tracker API.
It includes data generation, isolated test environment setup, and comprehensive reporting.

Usage:
    python3 run_performance_tests.py [options]

Options:
    --generate-data     Generate test datasets (1, 2, and 4 years)
    --test-dataset NAME Test a specific dataset (1_year, 2_years, 4_years, all)
    --quick-test        Run a quick validation test
    --clean-only        Only clean up containers and temporary files

Examples:
    # Generate data and run all tests
    python3 run_performance_tests.py --generate-data --test-dataset all
    
    # Test only the 1-year dataset
    python3 run_performance_tests.py --test-dataset 1_year
    
    # Quick validation test
    python3 run_performance_tests.py --quick-test
"""

import sys
import argparse
import subprocess
import os
from generate_test_data import TaskDataGenerator
from performance_test import PerformanceTestSuite

def generate_test_data():
    """Generate all test datasets"""
    print("Generating test datasets...")
    print("=" * 50)
    
    generator = TaskDataGenerator()
    
    # Generate datasets
    datasets = [
        (1, "tasks_1_year.json"),
        (2, "tasks_2_years.json"), 
        (4, "tasks_4_years.json")
    ]
    
    for years, filename in datasets:
        print(f"\nGenerating {years} year(s) of data...")
        if years == 1:
            data = generator.generate_year_data(2024)
        else:
            data = generator.generate_multi_year_data(years, 2025 - years)
        
        filepath = f"/tmp/{filename}"
        generator.save_to_json(data, filepath)
        print(f"✓ Generated {len(data)} tasks -> {filepath}")
    
    print(f"\n{'='*50}")
    print("✅ All datasets generated successfully!")

def run_quick_test():
    """Run a quick validation test"""
    print("Running quick validation test...")
    print("=" * 50)
    
    try:
        # Import and run the quick test
        from test_performance_quick import quick_test
        quick_test()
        print("✅ Quick test completed successfully!")
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False
    return True

def run_performance_tests(dataset_name):
    """Run performance tests on specified dataset(s)"""
    suite = PerformanceTestSuite()
    
    try:
        # Setup test environment
        print("Setting up isolated test environment...")
        suite.setup_test_redis()
        suite.start_test_app()
        
        # Define available datasets
        available_datasets = {
            "1_year": ("/tmp/tasks_1_year.json", "1_year"),
            "2_years": ("/tmp/tasks_2_years.json", "2_years"),
            "4_years": ("/tmp/tasks_4_years.json", "4_years")
        }
        
        # Determine which datasets to test
        if dataset_name == "all":
            datasets_to_test = available_datasets.items()
        elif dataset_name in available_datasets:
            datasets_to_test = [(dataset_name, available_datasets[dataset_name])]
        else:
            print(f"❌ Unknown dataset: {dataset_name}")
            print(f"Available datasets: {', '.join(available_datasets.keys())}, all")
            return False
        
        all_results = []
        
        # Run tests on selected datasets
        for name, (data_file, dataset_name) in datasets_to_test:
            if not os.path.exists(data_file):
                print(f"⚠️  Dataset file not found: {data_file}")
                print(f"   Run with --generate-data to create test datasets")
                continue
                
            print(f"\n{'='*80}")
            print(f"TESTING {dataset_name.upper()} DATASET")
            print(f"{'='*80}")
            
            result = suite.run_complete_test_suite(data_file, dataset_name)
            if result:
                all_results.append(result)
            
            # Clear test data between datasets
            suite.redis_client.flushdb()
        
        # Generate comparison report if multiple datasets tested
        if len(all_results) > 1:
            print_comparison_report(all_results)
        
        return len(all_results) > 0
        
    except Exception as e:
        print(f"❌ Performance tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        suite.cleanup()

def print_comparison_report(results):
    """Print a comparison report across datasets"""
    print("\n" + "=" * 80)
    print("📊 PERFORMANCE COMPARISON ACROSS DATASETS")
    print("=" * 80)
    
    print(f"\n{'Dataset':<10} {'Tasks':<8} {'Year Query':<12} {'Month Avg':<12} {'Daily Avg':<12} {'Tasks/Sec':<10}")
    print("-" * 70)
    
    for result in results:
        summary = result['summary']
        year_perf = result['year_performance']
        dataset = result['dataset_size'].replace('_', ' ').title()
        
        print(f"{dataset:<10} {summary['total_tasks']:<8.0f} "
              f"{summary['year_avg_duration']:<12.3f} "
              f"{summary['month_avg_duration']:<12.3f} "
              f"{summary['daily_avg_duration']:<12.3f} "
              f"{year_perf['tasks_per_second']:<10.1f}")
    
    # Performance insights
    print(f"\n🔍 PERFORMANCE INSIGHTS:")
    for result in results:
        dataset = result['dataset_size'].replace('_', ' ').title()
        year_duration = result['summary']['year_avg_duration']
        total_tasks = result['summary']['total_tasks']
        
        if year_duration < 0.05:
            rating = "🚀 Excellent"
        elif year_duration < 0.1:
            rating = "✅ Very Good"
        elif year_duration < 0.2:
            rating = "✅ Good"
        elif year_duration < 0.5:
            rating = "⚠️  Acceptable"
        else:
            rating = "⚠️  Needs Optimization"
            
        print(f"  {dataset}: {rating} ({year_duration:.3f}s for {total_tasks:.0f} tasks)")

def cleanup_containers():
    """Clean up test containers"""
    print("Cleaning up test containers...")
    
    containers = [
        'redis-test-performance',
        'redis-test-quick', 
        'redis-debug'
    ]
    
    for container in containers:
        try:
            subprocess.run(['docker', 'stop', container], 
                         capture_output=True, check=False)
            subprocess.run(['docker', 'rm', container], 
                         capture_output=True, check=False)
        except:
            pass
    
    print("✅ Cleanup completed")

def main():
    parser = argparse.ArgumentParser(
        description="Performance Test Runner for Time Tracker API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--generate-data', action='store_true',
                       help='Generate test datasets')
    parser.add_argument('--test-dataset', 
                       choices=['1_year', '2_years', '4_years', 'all'],
                       help='Test specific dataset(s)')
    parser.add_argument('--quick-test', action='store_true',
                       help='Run quick validation test')
    parser.add_argument('--clean-only', action='store_true',
                       help='Only clean up containers and files')
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        return 1
    
    success = True
    
    try:
        # Clean up first if requested
        if args.clean_only:
            cleanup_containers()
            return 0
        
        # Generate data if requested
        if args.generate_data:
            generate_test_data()
        
        # Run quick test if requested
        if args.quick_test:
            if not run_quick_test():
                success = False
        
        # Run performance tests if requested
        if args.test_dataset:
            if not run_performance_tests(args.test_dataset):
                success = False
        
        # Final cleanup
        cleanup_containers()
        
        if success:
            print(f"\n🎉 All operations completed successfully!")
            print(f"\n📋 NEXT STEPS:")
            print(f"   • Review performance reports in /tmp/performance_results_*.json")
            print(f"   • Check if performance meets your requirements")
            print(f"   • Consider Redis tuning for production workloads")
            return 0
        else:
            print(f"\n❌ Some operations failed. Check output above for details.")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Operation interrupted by user")
        cleanup_containers()
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        cleanup_containers()
        return 1

if __name__ == "__main__":
    sys.exit(main())