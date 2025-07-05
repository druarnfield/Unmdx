"""
UnMDX Project Tracking Database Package.

This package provides SQLite database operations for tracking the UnMDX project
rewrite progress, including phases, tasks, test cases, commits, and milestones.
"""

from .database import UnMDXDatabase, DatabaseError
from .models import (
    Phase, Task, TestCase, Commit, Milestone, TestExecution,
    ProjectStatus, PhaseProgress, TestCaseResult, CommitWithPhase,
    CreatePhaseRequest, UpdatePhaseRequest, CreateTaskRequest, UpdateTaskRequest,
    CreateTestCaseRequest, UpdateTestCaseRequest, CreateCommitRequest,
    RecordTestExecutionRequest
)

__version__ = "0.1.0"
__all__ = [
    # Database class
    "UnMDXDatabase",
    "DatabaseError",
    
    # Core models
    "Phase",
    "Task", 
    "TestCase",
    "Commit",
    "Milestone",
    "TestExecution",
    
    # Analysis models
    "ProjectStatus",
    "PhaseProgress", 
    "TestCaseResult",
    "CommitWithPhase",
    
    # Request models
    "CreatePhaseRequest",
    "UpdatePhaseRequest",
    "CreateTaskRequest",
    "UpdateTaskRequest",
    "CreateTestCaseRequest",
    "UpdateTestCaseRequest",
    "CreateCommitRequest",
    "RecordTestExecutionRequest",
]