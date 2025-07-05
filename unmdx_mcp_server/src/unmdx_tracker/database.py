"""
Database operations for UnMDX project tracking.
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

from .models import (
    Phase, Task, TestCase, Commit, Milestone, TestExecution,
    ProjectStatus, PhaseProgress, TestCaseResult, CommitWithPhase,
    CreatePhaseRequest, UpdatePhaseRequest, CreateTaskRequest, UpdateTaskRequest,
    CreateTestCaseRequest, UpdateTestCaseRequest, CreateCommitRequest,
    RecordTestExecutionRequest
)

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database operations."""
    pass


class UnMDXDatabase:
    """Database operations for UnMDX project tracking."""
    
    def __init__(self, db_path: str = "unmdx_tracking.db"):
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up logging for database operations."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def connect(self) -> sqlite3.Connection:
        """Create and return a database connection."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
            return conn
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to database: {e}")
    
    def initialize_database(self, schema_path: str = "schema.sql"):
        """Initialize the database with the schema."""
        schema_file = Path(schema_path)
        if not schema_file.exists():
            raise DatabaseError(f"Schema file not found: {schema_path}")
        
        try:
            with self.connect() as conn:
                with open(schema_file, 'r') as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)
                conn.commit()
                logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to initialize database: {e}")
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a sqlite3.Row to a dictionary."""
        return {key: row[key] for key in row.keys()}
    
    # Phase operations
    def create_phase(self, request: CreatePhaseRequest) -> Phase:
        """Create a new phase."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO phases (name, description, status, start_date, end_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    request.name, request.description, request.status,
                    request.start_date, request.end_date, request.notes
                ))
                phase_id = cursor.lastrowid
                conn.commit()
                return self.get_phase(phase_id)
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create phase: {e}")
    
    def get_phase(self, phase_id: int) -> Phase:
        """Get a phase by ID."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM phases WHERE id = ?", (phase_id,))
                row = cursor.fetchone()
                if not row:
                    raise DatabaseError(f"Phase with ID {phase_id} not found")
                return Phase(**self._row_to_dict(row))
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get phase: {e}")
    
    def get_all_phases(self) -> List[Phase]:
        """Get all phases."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM phases ORDER BY id")
                rows = cursor.fetchall()
                return [Phase(**self._row_to_dict(row)) for row in rows]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get phases: {e}")
    
    def update_phase(self, phase_id: int, request: UpdatePhaseRequest) -> Phase:
        """Update an existing phase."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                updates = []
                params = []
                
                if request.name is not None:
                    updates.append("name = ?")
                    params.append(request.name)
                if request.description is not None:
                    updates.append("description = ?")
                    params.append(request.description)
                if request.status is not None:
                    updates.append("status = ?")
                    params.append(request.status)
                if request.start_date is not None:
                    updates.append("start_date = ?")
                    params.append(request.start_date)
                if request.end_date is not None:
                    updates.append("end_date = ?")
                    params.append(request.end_date)
                if request.notes is not None:
                    updates.append("notes = ?")
                    params.append(request.notes)
                
                if not updates:
                    return self.get_phase(phase_id)
                
                params.append(phase_id)
                query = f"UPDATE phases SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
                
                return self.get_phase(phase_id)
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update phase: {e}")
    
    def delete_phase(self, phase_id: int) -> bool:
        """Delete a phase."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM phases WHERE id = ?", (phase_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to delete phase: {e}")
    
    # Task operations
    def create_task(self, request: CreateTaskRequest) -> Task:
        """Create a new task."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tasks (phase_id, description, status, priority, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    request.phase_id, request.description, request.status,
                    request.priority, request.notes
                ))
                task_id = cursor.lastrowid
                conn.commit()
                return self.get_task(task_id)
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create task: {e}")
    
    def get_task(self, task_id: int) -> Task:
        """Get a task by ID."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
                row = cursor.fetchone()
                if not row:
                    raise DatabaseError(f"Task with ID {task_id} not found")
                return Task(**self._row_to_dict(row))
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get task: {e}")
    
    def get_tasks_by_phase(self, phase_id: int) -> List[Task]:
        """Get all tasks for a specific phase."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM tasks WHERE phase_id = ? ORDER BY created_date
                """, (phase_id,))
                rows = cursor.fetchall()
                return [Task(**self._row_to_dict(row)) for row in rows]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get tasks for phase: {e}")
    
    def update_task(self, task_id: int, request: UpdateTaskRequest) -> Task:
        """Update an existing task."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                updates = []
                params = []
                
                if request.description is not None:
                    updates.append("description = ?")
                    params.append(request.description)
                if request.status is not None:
                    updates.append("status = ?")
                    params.append(request.status)
                    # Set completed_date if status is completed
                    if request.status == 'completed':
                        updates.append("completed_date = ?")
                        params.append(datetime.now())
                if request.priority is not None:
                    updates.append("priority = ?")
                    params.append(request.priority)
                if request.notes is not None:
                    updates.append("notes = ?")
                    params.append(request.notes)
                
                if not updates:
                    return self.get_task(task_id)
                
                params.append(task_id)
                query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
                
                return self.get_task(task_id)
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update task: {e}")
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to delete task: {e}")
    
    # Test case operations
    def create_test_case(self, request: CreateTestCaseRequest) -> TestCase:
        """Create a new test case."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO test_cases (name, description, status, test_type)
                    VALUES (?, ?, ?, ?)
                """, (
                    request.name, request.description, request.status, request.test_type
                ))
                test_case_id = cursor.lastrowid
                conn.commit()
                return self.get_test_case(test_case_id)
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create test case: {e}")
    
    def get_test_case(self, test_case_id: int) -> TestCase:
        """Get a test case by ID."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM test_cases WHERE id = ?", (test_case_id,))
                row = cursor.fetchone()
                if not row:
                    raise DatabaseError(f"Test case with ID {test_case_id} not found")
                return TestCase(**self._row_to_dict(row))
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get test case: {e}")
    
    def get_all_test_cases(self) -> List[TestCase]:
        """Get all test cases."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM test_cases ORDER BY name")
                rows = cursor.fetchall()
                return [TestCase(**self._row_to_dict(row)) for row in rows]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get test cases: {e}")
    
    def update_test_case(self, test_case_id: int, request: UpdateTestCaseRequest) -> TestCase:
        """Update an existing test case."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query
                updates = []
                params = []
                
                if request.name is not None:
                    updates.append("name = ?")
                    params.append(request.name)
                if request.description is not None:
                    updates.append("description = ?")
                    params.append(request.description)
                if request.status is not None:
                    updates.append("status = ?")
                    params.append(request.status)
                    # Update last_success_date if status is passing
                    if request.status == 'passing':
                        updates.append("last_success_date = ?")
                        params.append(datetime.now())
                if request.failure_reason is not None:
                    updates.append("failure_reason = ?")
                    params.append(request.failure_reason)
                if request.test_type is not None:
                    updates.append("test_type = ?")
                    params.append(request.test_type)
                
                if not updates:
                    return self.get_test_case(test_case_id)
                
                params.append(test_case_id)
                query = f"UPDATE test_cases SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
                
                return self.get_test_case(test_case_id)
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update test case: {e}")
    
    # Commit operations
    def create_commit(self, request: CreateCommitRequest) -> Commit:
        """Create a new commit record."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                test_results_json = json.dumps(request.test_results) if request.test_results else None
                cursor.execute("""
                    INSERT INTO commits (hash, branch, message, timestamp, phase_id, test_results, author)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    request.hash, request.branch, request.message, request.timestamp,
                    request.phase_id, test_results_json, request.author
                ))
                conn.commit()
                return self.get_commit(request.hash)
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create commit: {e}")
    
    def get_commit(self, commit_hash: str) -> Commit:
        """Get a commit by hash."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM commits WHERE hash = ?", (commit_hash,))
                row = cursor.fetchone()
                if not row:
                    raise DatabaseError(f"Commit with hash {commit_hash} not found")
                return Commit(**self._row_to_dict(row))
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get commit: {e}")
    
    def get_recent_commits(self, limit: int = 10) -> List[Commit]:
        """Get recent commits."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM commits ORDER BY timestamp DESC LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                return [Commit(**self._row_to_dict(row)) for row in rows]
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get recent commits: {e}")
    
    # Test execution operations
    def record_test_execution(self, request: RecordTestExecutionRequest) -> TestExecution:
        """Record a test execution."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO test_executions (test_case_id, status, duration_ms, error_message, commit_hash)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    request.test_case_id, request.status, request.duration_ms,
                    request.error_message, request.commit_hash
                ))
                execution_id = cursor.lastrowid
                
                # Update test case status and last_run_date
                cursor.execute("""
                    UPDATE test_cases 
                    SET status = ?, last_run_date = ?, 
                        last_success_date = CASE WHEN ? = 'passed' THEN ? ELSE last_success_date END,
                        failure_reason = CASE WHEN ? != 'passed' THEN ? ELSE NULL END
                    WHERE id = ?
                """, (
                    'passing' if request.status == 'passed' else 'failing',
                    datetime.now(),
                    request.status, datetime.now(),
                    request.status, request.error_message,
                    request.test_case_id
                ))
                
                conn.commit()
                
                # Return the created execution
                cursor.execute("SELECT * FROM test_executions WHERE id = ?", (execution_id,))
                row = cursor.fetchone()
                return TestExecution(**self._row_to_dict(row))
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to record test execution: {e}")
    
    # Analytics and reporting
    def get_project_status(self) -> ProjectStatus:
        """Get overall project status."""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                
                # Phase statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress
                    FROM phases
                """)
                phase_stats = cursor.fetchone()
                
                # Task statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COALESCE(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), 0) as completed
                    FROM tasks
                """)
                task_stats = cursor.fetchone()
                
                # Test case statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COALESCE(SUM(CASE WHEN status = 'passing' THEN 1 ELSE 0 END), 0) as passing,
                        COALESCE(SUM(CASE WHEN status = 'failing' THEN 1 ELSE 0 END), 0) as failing
                    FROM test_cases
                """)
                test_stats = cursor.fetchone()
                
                # Recent commits
                recent_commits = self.get_recent_commits(5)
                
                # Next milestone
                cursor.execute("""
                    SELECT * FROM milestones 
                    WHERE status IN ('pending', 'in_progress')
                    ORDER BY target_date ASC
                    LIMIT 1
                """)
                next_milestone_row = cursor.fetchone()
                next_milestone = None
                if next_milestone_row:
                    next_milestone = Milestone(**self._row_to_dict(next_milestone_row))
                
                return ProjectStatus(
                    total_phases=phase_stats['total'],
                    completed_phases=phase_stats['completed'],
                    in_progress_phases=phase_stats['in_progress'],
                    total_tasks=task_stats['total'],
                    completed_tasks=task_stats['completed'],
                    total_test_cases=test_stats['total'],
                    passing_tests=test_stats['passing'],
                    failing_tests=test_stats['failing'],
                    recent_commits=recent_commits,
                    next_milestone=next_milestone
                )
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get project status: {e}")
    
    def get_phase_progress(self, phase_id: int) -> PhaseProgress:
        """Get detailed progress for a specific phase."""
        try:
            phase = self.get_phase(phase_id)
            tasks = self.get_tasks_by_phase(phase_id)
            
            # Calculate task completion rate
            if tasks:
                completed_tasks = sum(1 for task in tasks if task.status == 'completed')
                task_completion_rate = completed_tasks / len(tasks)
            else:
                task_completion_rate = 0.0
            
            # Get related commits
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM commits WHERE phase_id = ? ORDER BY timestamp DESC
                """, (phase_id,))
                rows = cursor.fetchall()
                related_commits = [Commit(**self._row_to_dict(row)) for row in rows]
            
            # Get test cases (for now, get all - in future could be phase-specific)
            test_cases = self.get_all_test_cases()
            
            # Calculate test pass rate
            if test_cases:
                passing_tests = sum(1 for tc in test_cases if tc.status == 'passing')
                test_pass_rate = passing_tests / len(test_cases)
            else:
                test_pass_rate = 0.0
            
            return PhaseProgress(
                phase=phase,
                tasks=tasks,
                task_completion_rate=task_completion_rate,
                related_commits=related_commits,
                test_cases=test_cases,
                test_pass_rate=test_pass_rate
            )
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get phase progress: {e}")
    
    def get_test_case_results(self, test_case_id: int, limit: int = 10) -> TestCaseResult:
        """Get test case with recent execution results."""
        try:
            test_case = self.get_test_case(test_case_id)
            
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM test_executions 
                    WHERE test_case_id = ? 
                    ORDER BY execution_date DESC 
                    LIMIT ?
                """, (test_case_id, limit))
                rows = cursor.fetchall()
                recent_executions = [TestExecution(**self._row_to_dict(row)) for row in rows]
                
                # Calculate success rate
                if recent_executions:
                    passed_executions = sum(1 for exe in recent_executions if exe.status == 'passed')
                    success_rate = passed_executions / len(recent_executions)
                    
                    # Calculate average duration
                    durations = [exe.duration_ms for exe in recent_executions if exe.duration_ms]
                    avg_duration_ms = sum(durations) / len(durations) if durations else None
                else:
                    success_rate = 0.0
                    avg_duration_ms = None
                
                return TestCaseResult(
                    test_case=test_case,
                    recent_executions=recent_executions,
                    success_rate=success_rate,
                    avg_duration_ms=avg_duration_ms
                )
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get test case results: {e}")
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None