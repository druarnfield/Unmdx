"""
Pydantic models for UnMDX project tracking database.
"""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
import json


class Phase(BaseModel):
    """Project phase model."""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    status: Literal['not_started', 'in_progress', 'completed', 'blocked']
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Task(BaseModel):
    """Task model within a phase."""
    id: Optional[int] = None
    phase_id: int
    description: str
    status: Literal['pending', 'in_progress', 'completed', 'blocked']
    priority: Literal['low', 'medium', 'high', 'critical']
    created_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class TestCase(BaseModel):
    """Test case model."""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    status: Literal['passing', 'failing', 'skipped', 'not_run']
    last_run_date: Optional[datetime] = None
    last_success_date: Optional[datetime] = None
    failure_reason: Optional[str] = None
    test_type: Optional[Literal['unit', 'integration', 'e2e']] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Commit(BaseModel):
    """Git commit model."""
    hash: str
    branch: str
    message: str
    timestamp: datetime
    phase_id: Optional[int] = None
    test_results: Optional[str] = None  # JSON string
    author: Optional[str] = None

    @property
    def test_results_dict(self) -> Optional[dict]:
        """Parse test results JSON string to dict."""
        if self.test_results:
            try:
                return json.loads(self.test_results)
            except json.JSONDecodeError:
                return None
        return None

    @test_results_dict.setter
    def test_results_dict(self, value: Optional[dict]):
        """Set test results from dict."""
        if value:
            self.test_results = json.dumps(value)
        else:
            self.test_results = None

    class Config:
        from_attributes = True


class Milestone(BaseModel):
    """Project milestone model."""
    id: Optional[int] = None
    name: str
    target_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    status: Literal['pending', 'in_progress', 'completed', 'missed']
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestExecution(BaseModel):
    """Test execution history model."""
    id: Optional[int] = None
    test_case_id: int
    execution_date: Optional[datetime] = None
    status: Literal['passed', 'failed', 'skipped', 'error']
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    commit_hash: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectStatus(BaseModel):
    """Overall project status summary."""
    total_phases: int
    completed_phases: int
    in_progress_phases: int
    total_tasks: int
    completed_tasks: int
    total_test_cases: int
    passing_tests: int
    failing_tests: int
    recent_commits: List[Commit]
    next_milestone: Optional[Milestone] = None


class PhaseProgress(BaseModel):
    """Detailed phase progress."""
    phase: Phase
    tasks: List[Task]
    task_completion_rate: float
    related_commits: List[Commit]
    test_cases: List[TestCase]
    test_pass_rate: float


class TestCaseResult(BaseModel):
    """Test case with recent execution results."""
    test_case: TestCase
    recent_executions: List[TestExecution]
    success_rate: float
    avg_duration_ms: Optional[float] = None


class CommitWithPhase(BaseModel):
    """Commit with associated phase information."""
    commit: Commit
    phase: Optional[Phase] = None


# Request/Response models for API operations
class CreatePhaseRequest(BaseModel):
    """Request to create a new phase."""
    name: str
    description: Optional[str] = None
    status: Literal['not_started', 'in_progress', 'completed', 'blocked'] = 'not_started'
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None


class UpdatePhaseRequest(BaseModel):
    """Request to update an existing phase."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal['not_started', 'in_progress', 'completed', 'blocked']] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    notes: Optional[str] = None


class CreateTaskRequest(BaseModel):
    """Request to create a new task."""
    phase_id: int
    description: str
    status: Literal['pending', 'in_progress', 'completed', 'blocked'] = 'pending'
    priority: Literal['low', 'medium', 'high', 'critical'] = 'medium'
    notes: Optional[str] = None


class UpdateTaskRequest(BaseModel):
    """Request to update an existing task."""
    description: Optional[str] = None
    status: Optional[Literal['pending', 'in_progress', 'completed', 'blocked']] = None
    priority: Optional[Literal['low', 'medium', 'high', 'critical']] = None
    notes: Optional[str] = None


class CreateTestCaseRequest(BaseModel):
    """Request to create a new test case."""
    name: str
    description: Optional[str] = None
    status: Literal['passing', 'failing', 'skipped', 'not_run'] = 'not_run'
    test_type: Optional[Literal['unit', 'integration', 'e2e']] = None


class UpdateTestCaseRequest(BaseModel):
    """Request to update an existing test case."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal['passing', 'failing', 'skipped', 'not_run']] = None
    failure_reason: Optional[str] = None
    test_type: Optional[Literal['unit', 'integration', 'e2e']] = None


class CreateCommitRequest(BaseModel):
    """Request to create a new commit record."""
    hash: str
    branch: str
    message: str
    timestamp: datetime
    phase_id: Optional[int] = None
    test_results: Optional[dict] = None
    author: Optional[str] = None


class RecordTestExecutionRequest(BaseModel):
    """Request to record a test execution."""
    test_case_id: int
    status: Literal['passed', 'failed', 'skipped', 'error']
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    commit_hash: Optional[str] = None