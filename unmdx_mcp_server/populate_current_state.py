#!/usr/bin/env python3
"""
Populate MCP server with current UnMDX project state.

This script populates the database with the actual current state of the UnMDX rewrite project,
including completed phases, current tasks, test results, and git history.
"""

import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from unmdx_tracker.database import UnMDXDatabase
from unmdx_tracker.models import CreateTaskRequest, CreateTestCaseRequest, CreateCommitRequest


async def populate_project_state():
    """Populate the database with current UnMDX project state."""
    
    # Initialize database
    db_path = Path(__file__).parent / "unmdx_project.db"
    schema_path = Path(__file__).parent / "schema.sql"
    
    db = UnMDXDatabase(str(db_path))
    
    # Initialize with schema if needed
    if not db_path.exists():
        db.initialize_database(str(schema_path))
        print("✓ Database initialized with schema")
    
    print("🔄 Populating UnMDX project current state...")
    
    # Update Phase 1 to completed (Foundation)
    print("\n📋 Updating Phase Status...")
    try:
        db.update_phase_status(1, "completed", "Phase 1 foundation completed - all basic test cases working")
        print("✓ Phase 1 (Foundation) marked as completed")
    except Exception as e:
        print(f"  Note: {e}")
    
    # Add completed tasks for Phase 1
    print("\n📝 Adding Phase 1 Completed Tasks...")
    
    phase_1_tasks = [
        "Create new git branch 'rewrite-foundation'",
        "Set up basic project structure with minimal dependencies", 
        "Implement simplest possible MDX parser",
        "Create basic transformer for Test Case 1",
        "Add simple DAX generator for measure-only queries",
        "Ensure Test Case 1 passes with functional test",
        "Extend to handle Test Cases 2-3 (basic dimensions)",
        "Add comprehensive error handling",
        "Write real integration tests"
    ]
    
    for i, task_desc in enumerate(phase_1_tasks, 1):
        try:
            task_req = CreateTaskRequest(
                phase_id=1,
                description=task_desc,
                status="completed",
                priority="high"
            )
            task_id = db.create_task(task_req)
            # Mark as completed
            db.update_task_status(task_id, "completed", f"Completed as part of Phase 1 foundation work")
            print(f"✓ Task {i}: {task_desc[:50]}...")
        except Exception as e:
            print(f"  Note: {e}")
    
    # Add test cases for current working functionality  
    print("\n🧪 Adding Test Cases...")
    
    test_cases = [
        ("test_case_1_simple_measure", "Simple measure query conversion", "passing", "Basic measure-only queries work correctly"),
        ("test_case_2_measure_with_dimension", "Measure with dimension query", "passing", "Measure + dimension queries work correctly"),
        ("test_case_3_multiple_measures", "Multiple measures query", "passing", "Multiple measures with dimensions work correctly"),
        ("test_case_4_where_clause", "WHERE clause support", "failing", "WHERE clause conversion not yet implemented"),
        ("test_case_5_crossjoin", "CrossJoin optimization", "passing", "Basic CrossJoin conversion works"),
        ("test_case_6_specific_members", "Specific member selection", "failing", "Specific member selection not implemented"),
        ("test_case_7_calculated_members", "Calculated members", "failing", "Calculated member support not implemented"),
        ("test_case_8_non_empty", "NON EMPTY support", "failing", "NON EMPTY clause not implemented"),
        ("test_case_9_multiple_filters", "Multiple filters in WHERE", "failing", "Complex WHERE clauses not implemented"),
        ("test_case_10_empty_sets", "Empty set handling", "failing", "Empty set optimization not implemented")
    ]
    
    for name, description, status, notes in test_cases:
        try:
            test_req = CreateTestCaseRequest(
                name=name,
                description=description,
                status=status
            )
            test_id = db.create_test_case(test_req)
            
            # Record recent test execution
            if status == "passing":
                db.record_test_execution(test_id, True, 150, notes)
            else:
                db.record_test_execution(test_id, False, 0, notes)
                
            print(f"✓ Test Case: {name} - {status}")
        except Exception as e:
            print(f"  Note: {e}")
    
    # Add recent commits from rewrite-foundation branch
    print("\n📝 Adding Recent Commits...")
    
    commits = [
        ("5817b44", "rewrite-foundation", "Add comprehensive audit report and recovery plan", "2025-07-05 04:30:00"),
        ("9459d53", "rewrite-foundation", "Complete Phase 1: Working UnMDX v2 Foundation", "2025-07-05 04:45:00"),
    ]
    
    for commit_hash, branch, message, timestamp in commits:
        try:
            commit_req = CreateCommitRequest(
                hash=commit_hash,
                branch=branch,
                message=message,
                timestamp=datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S"),
                phase_id=1,
                test_results="3/3 basic tests passing"
            )
            commit_id = db.create_commit(commit_req)
            print(f"✓ Commit: {commit_hash[:8]} - {message[:50]}...")
        except Exception as e:
            print(f"  Note: {e}")
    
    # Start Phase 2 tasks
    print("\n🚀 Setting up Phase 2 (WHERE Clause Support)...")
    try:
        db.update_phase_status(2, "in_progress", "Starting WHERE clause support implementation")
        print("✓ Phase 2 marked as in_progress")
        
        # Add initial Phase 2 tasks
        phase_2_tasks = [
            "Implement WHERE clause detection in parser",
            "Add DAX filter generation for simple WHERE clauses", 
            "Handle key references (.&[value]) in filters",
            "Support multiple filters in tuple expressions",
            "Test real-world WHERE patterns from Necto",
            "Get Test Cases 4 & 9 passing"
        ]
        
        for task_desc in phase_2_tasks:
            task_req = CreateTaskRequest(
                phase_id=2,
                description=task_desc,
                status="pending",
                priority="high"
            )
            task_id = db.create_task(task_req)
            print(f"✓ Added Phase 2 task: {task_desc[:50]}...")
    except Exception as e:
        print(f"  Note: {e}")
    
    # Get current project status
    print("\n📊 Current Project Status:")
    status = db.get_project_status()
    print(f"  • Total Phases: {status.total_phases}")
    print(f"  • Completed Phases: {status.completed_phases}")
    print(f"  • Total Tasks: {status.total_tasks}")
    print(f"  • Completed Tasks: {status.completed_tasks}")
    print(f"  • Total Test Cases: {status.total_test_cases}")
    print(f"  • Passing Tests: {status.passing_test_cases}")
    print(f"  • Recent Commits: {status.recent_commits}")
    print(f"  • Next Milestone: {status.next_milestone}")
    
    print(f"\n🎉 UnMDX project state populated successfully!")
    print(f"   Database: {db_path}")
    print(f"   Ready for MCP server integration with Claude")


if __name__ == "__main__":
    asyncio.run(populate_project_state())