"""
Command-line interface for UnMDX project tracking.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from .database import UnMDXDatabase, DatabaseError
from .models import CreatePhaseRequest, CreateTaskRequest, CreateTestCaseRequest


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="UnMDX Project Tracking CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--db-path",
        default="unmdx_tracking.db",
        help="Path to the SQLite database file"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Initialize command
    init_parser = subparsers.add_parser("init", help="Initialize the database")
    init_parser.add_argument(
        "--schema",
        default="schema.sql",
        help="Path to schema file"
    )
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show project status")
    
    # Phase commands
    phase_parser = subparsers.add_parser("phase", help="Phase management")
    phase_subparsers = phase_parser.add_subparsers(dest="phase_action")
    
    # List phases
    phase_subparsers.add_parser("list", help="List all phases")
    
    # Create phase
    create_phase_parser = phase_subparsers.add_parser("create", help="Create new phase")
    create_phase_parser.add_argument("name", help="Phase name")
    create_phase_parser.add_argument("--description", help="Phase description")
    create_phase_parser.add_argument(
        "--status",
        choices=["not_started", "in_progress", "completed", "blocked"],
        default="not_started",
        help="Phase status"
    )
    
    # Task commands
    task_parser = subparsers.add_parser("task", help="Task management")
    task_subparsers = task_parser.add_subparsers(dest="task_action")
    
    # Create task
    create_task_parser = task_subparsers.add_parser("create", help="Create new task")
    create_task_parser.add_argument("phase_id", type=int, help="Phase ID")
    create_task_parser.add_argument("description", help="Task description")
    create_task_parser.add_argument(
        "--priority",
        choices=["low", "medium", "high", "critical"],
        default="medium",
        help="Task priority"
    )
    
    # Test case commands
    test_parser = subparsers.add_parser("test", help="Test case management")
    test_subparsers = test_parser.add_subparsers(dest="test_action")
    
    # Create test case
    create_test_parser = test_subparsers.add_parser("create", help="Create new test case")
    create_test_parser.add_argument("name", help="Test case name")
    create_test_parser.add_argument("--description", help="Test case description")
    create_test_parser.add_argument(
        "--type",
        choices=["unit", "integration", "e2e"],
        help="Test case type"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        db = UnMDXDatabase(args.db_path)
        
        if args.command == "init":
            db.initialize_database(args.schema)
            print(f"Database initialized: {args.db_path}")
            
        elif args.command == "status":
            status = db.get_project_status()
            print("UnMDX Project Status")
            print("=" * 30)
            print(f"Phases: {status.completed_phases}/{status.total_phases} completed")
            print(f"Tasks: {status.completed_tasks}/{status.total_tasks} completed")
            print(f"Tests: {status.passing_tests}/{status.total_test_cases} passing")
            
            if status.next_milestone:
                print(f"Next milestone: {status.next_milestone.name}")
            
            print(f"\nRecent commits: {len(status.recent_commits)}")
            for commit in status.recent_commits[:3]:
                print(f"  - {commit.hash[:8]}: {commit.message}")
                
        elif args.command == "phase":
            if args.phase_action == "list":
                phases = db.get_all_phases()
                print("Phases:")
                for phase in phases:
                    print(f"  {phase.id}: {phase.name} ({phase.status})")
                    
            elif args.phase_action == "create":
                request = CreatePhaseRequest(
                    name=args.name,
                    description=args.description,
                    status=args.status
                )
                phase = db.create_phase(request)
                print(f"Created phase: {phase.name} (ID: {phase.id})")
                
        elif args.command == "task":
            if args.task_action == "create":
                request = CreateTaskRequest(
                    phase_id=args.phase_id,
                    description=args.description,
                    priority=args.priority
                )
                task = db.create_task(request)
                print(f"Created task: {task.description} (ID: {task.id})")
                
        elif args.command == "test":
            if args.test_action == "create":
                request = CreateTestCaseRequest(
                    name=args.name,
                    description=args.description,
                    test_type=args.type
                )
                test_case = db.create_test_case(request)
                print(f"Created test case: {test_case.name} (ID: {test_case.id})")
                
        return 0
        
    except DatabaseError as e:
        print(f"Database error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())