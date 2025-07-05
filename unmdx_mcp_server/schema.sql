-- UnMDX Project Tracking Database Schema
-- SQLite database for tracking UnMDX rewrite project progress

-- Project phases (Foundation, WHERE clauses, etc.)
CREATE TABLE phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    status TEXT NOT NULL CHECK (status IN ('not_started', 'in_progress', 'completed', 'blocked')),
    start_date DATETIME,
    end_date DATETIME,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tasks within each phase
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'blocked')),
    priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_date DATETIME,
    notes TEXT,
    FOREIGN KEY (phase_id) REFERENCES phases(id) ON DELETE CASCADE
);

-- Test cases and their execution status
CREATE TABLE test_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    status TEXT NOT NULL CHECK (status IN ('passing', 'failing', 'skipped', 'not_run')),
    last_run_date DATETIME,
    last_success_date DATETIME,
    failure_reason TEXT,
    test_type TEXT CHECK (test_type IN ('unit', 'integration', 'e2e')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Git commits linked to project progress
CREATE TABLE commits (
    hash TEXT PRIMARY KEY,
    branch TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    phase_id INTEGER,
    test_results TEXT, -- JSON string of test results
    author TEXT,
    FOREIGN KEY (phase_id) REFERENCES phases(id) ON DELETE SET NULL
);

-- Project milestones
CREATE TABLE milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    target_date DATETIME,
    completion_date DATETIME,
    status TEXT NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'missed')),
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Relationship between phases and milestones
CREATE TABLE phase_milestones (
    phase_id INTEGER NOT NULL,
    milestone_id INTEGER NOT NULL,
    PRIMARY KEY (phase_id, milestone_id),
    FOREIGN KEY (phase_id) REFERENCES phases(id) ON DELETE CASCADE,
    FOREIGN KEY (milestone_id) REFERENCES milestones(id) ON DELETE CASCADE
);

-- Test case execution history
CREATE TABLE test_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_case_id INTEGER NOT NULL,
    execution_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL CHECK (status IN ('passed', 'failed', 'skipped', 'error')),
    duration_ms INTEGER,
    error_message TEXT,
    commit_hash TEXT,
    FOREIGN KEY (test_case_id) REFERENCES test_cases(id) ON DELETE CASCADE,
    FOREIGN KEY (commit_hash) REFERENCES commits(hash) ON DELETE SET NULL
);

-- Create indexes for better performance
CREATE INDEX idx_tasks_phase_id ON tasks(phase_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_commits_branch ON commits(branch);
CREATE INDEX idx_commits_timestamp ON commits(timestamp);
CREATE INDEX idx_test_executions_test_case_id ON test_executions(test_case_id);
CREATE INDEX idx_test_executions_execution_date ON test_executions(execution_date);

-- Create triggers to update timestamps
CREATE TRIGGER update_phases_timestamp 
    AFTER UPDATE ON phases
    FOR EACH ROW
    BEGIN
        UPDATE phases SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER update_test_cases_timestamp 
    AFTER UPDATE ON test_cases
    FOR EACH ROW
    BEGIN
        UPDATE test_cases SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER update_milestones_timestamp 
    AFTER UPDATE ON milestones
    FOR EACH ROW
    BEGIN
        UPDATE milestones SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Initial data - UnMDX project phases
INSERT INTO phases (name, description, status) VALUES
('Foundation', 'Core parser and IR infrastructure', 'completed'),
('WHERE Clauses', 'Implement WHERE clause parsing and transformation', 'in_progress'),
('SELECT Components', 'Handle SELECT clause dimensions and measures', 'not_started'),
('Calculated Members', 'Support for calculated members and expressions', 'not_started'),
('Advanced Features', 'Complex MDX features and optimizations', 'not_started'),
('Performance', 'Optimization and performance improvements', 'not_started'),
('Documentation', 'Complete documentation and examples', 'not_started');

-- Initial milestones
INSERT INTO milestones (name, description, status, target_date) VALUES
('Parser Foundation', 'Basic MDX parsing working', 'completed', '2024-01-15'),
('Basic Query Support', 'Simple SELECT-FROM-WHERE queries working', 'in_progress', '2024-02-01'),
('Advanced Query Support', 'Complex queries with calculated members', 'pending', '2024-03-01'),
('Production Ready', 'Full feature set with documentation', 'pending', '2024-04-01');