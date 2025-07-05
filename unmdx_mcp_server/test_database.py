#!/usr/bin/env python3
"""
Test script for UnMDX project tracking database.
Demonstrates all database operations and verifies functionality.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from unmdx_tracker import (
    UnMDXDatabase, DatabaseError,
    CreatePhaseRequest, UpdatePhaseRequest,
    CreateTaskRequest, UpdateTaskRequest,
    CreateTestCaseRequest, UpdateTestCaseRequest,
    CreateCommitRequest, RecordTestExecutionRequest
)


def test_database_operations():
    """Test all database operations."""
    print("Starting UnMDX Database Test Suite")
    print("=" * 50)
    
    # Initialize database
    db_path = "test_unmdx_tracking.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = UnMDXDatabase(db_path)
    
    try:
        # Initialize with schema
        print("\n1. Initializing database with schema...")
        db.initialize_database("schema.sql")
        print("✓ Database initialized successfully")
        
        # Test phase operations
        print("\n2. Testing Phase Operations...")
        
        # Create a new phase
        new_phase_request = CreatePhaseRequest(
            name="Test Phase",
            description="A test phase for demonstration",
            status="in_progress",
            start_date=datetime.now(),
            notes="This is a test phase"
        )
        
        new_phase = db.create_phase(new_phase_request)
        print(f"✓ Created phase: {new_phase.name} (ID: {new_phase.id})")
        
        # Get all phases
        all_phases = db.get_all_phases()
        print(f"✓ Retrieved {len(all_phases)} phases")
        
        # Update the phase
        update_phase_request = UpdatePhaseRequest(
            status="completed",
            end_date=datetime.now(),
            notes="Updated test phase"
        )
        
        updated_phase = db.update_phase(new_phase.id, update_phase_request)
        print(f"✓ Updated phase status to: {updated_phase.status}")
        
        # Test task operations
        print("\n3. Testing Task Operations...")
        
        # Create tasks for the phase
        task1_request = CreateTaskRequest(
            phase_id=new_phase.id,
            description="Implement basic functionality",
            status="completed",
            priority="high",
            notes="First task completed"
        )
        
        task2_request = CreateTaskRequest(
            phase_id=new_phase.id,
            description="Write tests",
            status="in_progress",
            priority="medium"
        )
        
        task1 = db.create_task(task1_request)
        task2 = db.create_task(task2_request)
        print(f"✓ Created tasks: {task1.description}, {task2.description}")
        
        # Get tasks for the phase
        phase_tasks = db.get_tasks_by_phase(new_phase.id)
        print(f"✓ Retrieved {len(phase_tasks)} tasks for phase")
        
        # Update task
        update_task_request = UpdateTaskRequest(
            status="completed",
            notes="Tests completed successfully"
        )
        
        updated_task = db.update_task(task2.id, update_task_request)
        print(f"✓ Updated task status to: {updated_task.status}")
        
        # Test test case operations
        print("\n4. Testing Test Case Operations...")
        
        # Create test cases
        test_case1_request = CreateTestCaseRequest(
            name="test_basic_parsing",
            description="Test basic MDX parsing functionality",
            status="passing",
            test_type="unit"
        )
        
        test_case2_request = CreateTestCaseRequest(
            name="test_dax_generation",
            description="Test DAX generation from IR",
            status="failing",
            test_type="integration"
        )
        
        test_case1 = db.create_test_case(test_case1_request)
        test_case2 = db.create_test_case(test_case2_request)
        print(f"✓ Created test cases: {test_case1.name}, {test_case2.name}")
        
        # Get all test cases
        all_test_cases = db.get_all_test_cases()
        print(f"✓ Retrieved {len(all_test_cases)} test cases")
        
        # Update test case
        update_test_case_request = UpdateTestCaseRequest(
            status="passing",
            failure_reason=None
        )
        
        updated_test_case = db.update_test_case(test_case2.id, update_test_case_request)
        print(f"✓ Updated test case status to: {updated_test_case.status}")
        
        # Test commit operations
        print("\n5. Testing Commit Operations...")
        
        # Create commit records
        commit1_request = CreateCommitRequest(
            hash="abc123def456",
            branch="main",
            message="Fix basic test cases",
            timestamp=datetime.now() - timedelta(hours=2),
            phase_id=new_phase.id,
            test_results={"passed": 8, "failed": 2, "skipped": 1},
            author="developer@example.com"
        )
        
        commit2_request = CreateCommitRequest(
            hash="def456ghi789",
            branch="feature/new-parser",
            message="Add advanced parsing features",
            timestamp=datetime.now() - timedelta(hours=1),
            phase_id=new_phase.id,
            test_results={"passed": 10, "failed": 1, "skipped": 0},
            author="developer@example.com"
        )
        
        commit1 = db.create_commit(commit1_request)
        commit2 = db.create_commit(commit2_request)
        print(f"✓ Created commits: {commit1.hash[:8]}, {commit2.hash[:8]}")
        
        # Get recent commits
        recent_commits = db.get_recent_commits(5)
        print(f"✓ Retrieved {len(recent_commits)} recent commits")
        
        # Test test execution recording
        print("\n6. Testing Test Execution Recording...")
        
        # Record test executions
        execution1_request = RecordTestExecutionRequest(
            test_case_id=test_case1.id,
            status="passed",
            duration_ms=150,
            commit_hash=commit1.hash
        )
        
        execution2_request = RecordTestExecutionRequest(
            test_case_id=test_case2.id,
            status="failed",
            duration_ms=200,
            error_message="Assertion error in DAX generation",
            commit_hash=commit1.hash
        )
        
        execution3_request = RecordTestExecutionRequest(
            test_case_id=test_case2.id,
            status="passed",
            duration_ms=180,
            commit_hash=commit2.hash
        )
        
        execution1 = db.record_test_execution(execution1_request)
        execution2 = db.record_test_execution(execution2_request)
        execution3 = db.record_test_execution(execution3_request)
        print(f"✓ Recorded 3 test executions")
        
        # Test analytics and reporting
        print("\n7. Testing Analytics and Reporting...")
        
        # Get project status
        project_status = db.get_project_status()
        print(f"✓ Project Status:")
        print(f"  - Total phases: {project_status.total_phases}")
        print(f"  - Completed phases: {project_status.completed_phases}")
        print(f"  - Total tasks: {project_status.total_tasks}")
        print(f"  - Completed tasks: {project_status.completed_tasks}")
        print(f"  - Total test cases: {project_status.total_test_cases}")
        print(f"  - Passing tests: {project_status.passing_tests}")
        print(f"  - Recent commits: {len(project_status.recent_commits)}")
        if project_status.next_milestone:
            print(f"  - Next milestone: {project_status.next_milestone.name}")
        
        # Get phase progress
        phase_progress = db.get_phase_progress(new_phase.id)
        print(f"✓ Phase Progress for '{phase_progress.phase.name}':")
        print(f"  - Task completion rate: {phase_progress.task_completion_rate:.2%}")
        print(f"  - Test pass rate: {phase_progress.test_pass_rate:.2%}")
        print(f"  - Related commits: {len(phase_progress.related_commits)}")
        
        # Get test case results
        test_case_results = db.get_test_case_results(test_case2.id)
        print(f"✓ Test Case Results for '{test_case_results.test_case.name}':")
        print(f"  - Success rate: {test_case_results.success_rate:.2%}")
        print(f"  - Average duration: {test_case_results.avg_duration_ms}ms")
        print(f"  - Recent executions: {len(test_case_results.recent_executions)}")
        
        # Test error handling
        print("\n8. Testing Error Handling...")
        
        try:
            db.get_phase(99999)
            print("✗ Should have raised DatabaseError for non-existent phase")
        except DatabaseError as e:
            print(f"✓ Correctly raised DatabaseError: {e}")
        
        try:
            duplicate_phase_request = CreatePhaseRequest(
                name="Test Phase",  # Same name as existing phase
                description="This should fail",
                status="not_started"
            )
            db.create_phase(duplicate_phase_request)
            print("✗ Should have raised DatabaseError for duplicate phase name")
        except DatabaseError as e:
            print(f"✓ Correctly raised DatabaseError for duplicate: {e}")
        
        # Test deletion operations
        print("\n9. Testing Deletion Operations...")
        
        # Delete task
        deleted_task = db.delete_task(task1.id)
        print(f"✓ Deleted task: {deleted_task}")
        
        # Verify task is deleted
        try:
            db.get_task(task1.id)
            print("✗ Should have raised DatabaseError for deleted task")
        except DatabaseError:
            print("✓ Correctly raised error for deleted task")
        
        print("\n" + "=" * 50)
        print("✓ All database tests completed successfully!")
        print("Database functionality verified and ready for MCP server integration.")
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test database
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"✓ Cleaned up test database: {db_path}")
    
    return True


if __name__ == "__main__":
    success = test_database_operations()
    sys.exit(0 if success else 1)