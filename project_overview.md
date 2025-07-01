# MDX to DAX Converter - Project Plan

## Project Overview

### Goal

Build a comprehensive Python CLI tool that converts MDX queries (particularly messy output from Necto SSAS cubes) into clean, optimized DAX queries with human-readable explanations.

### Key Components

1. **MDX Parser** - Lark-based parser for handling poorly formatted MDX
1. **Intermediate Representation (IR)** - Normalized semantic representation
1. **Linter** - Cleans and optimizes the parsed MDX structure
1. **DAX Generator** - Produces clean DAX queries from IR
1. **SQL Explainer** - Generates human-readable explanations

### Technical Stack

- Python 3.10+
- Lark for parsing
- Textual for CLI interface
- Pydantic for data models
- Pytest for testing
- Black/Ruff for code quality

-----

## Milestones

### Milestone 1: Project Setup & Infrastructure

**Timeline**: Week 1  
**Test Coverage Target**: 100% of utilities

#### Deliverables

- [ ] Project structure with proper packaging
- [ ] Development environment setup (pyproject.toml, requirements.txt)
- [ ] CI/CD pipeline configuration (GitHub Actions)
- [ ] Code quality tools integration (black, ruff, mypy)
- [ ] Logging infrastructure
- [ ] Basic CLI skeleton with Typer

#### Testing Requirements

- [ ] Unit tests for all utility functions
- [ ] Test fixtures setup for MDX queries
- [ ] Test data management structure
- [ ] Coverage reporting configuration
- [ ] Pre-commit hooks for test execution

-----

### Milestone 2: MDX Grammar & Parser

**Timeline**: Weeks 2-3  
**Test Coverage Target**: 95% of grammar rules

#### Deliverables

- [ ] Complete Lark grammar for MDX (parts 1 & 2)
- [ ] Parser wrapper with error handling
- [ ] Parse tree visitor for debugging
- [ ] Grammar validation utilities

#### Testing Requirements

- [ ] **Unit Tests - Valid Queries** (Tests 1-10)
  - [ ] Simple measure queries
  - [ ] Measure with dimensions
  - [ ] Multiple measures
  - [ ] WHERE clauses
  - [ ] CrossJoins
  - [ ] Calculated members
  - [ ] NON EMPTY handling
- [ ] **Unit Tests - Complex Queries** (Tests 11-20)
  - [ ] Deep hierarchies (7+ levels)
  - [ ] Optimizer comment parsing
  - [ ] Nested DESCENDANTS
  - [ ] Time intelligence
  - [ ] Matrix organizations
- [ ] **Unit Tests - Invalid Queries** (Tests 21-30)
  - [ ] Missing clauses
  - [ ] Syntax errors
  - [ ] Circular references
  - [ ] Invalid functions
- [ ] **Property-based Tests**
  - [ ] Random nesting depth handling
  - [ ] Unicode character support
  - [ ] Large query performance

-----

### Milestone 3: Intermediate Representation (IR)

**Timeline**: Weeks 4-5  
**Test Coverage Target**: 100% of IR classes

#### Deliverables

- [ ] IR data models with Pydantic
- [ ] Query, Measure, Dimension, Filter classes
- [ ] Expression tree implementation
- [ ] Metadata and error tracking
- [ ] IR serialization/deserialization

#### Testing Requirements

- [ ] **Unit Tests - IR Construction**
  - [ ] Each IR class construction
  - [ ] Validation rules
  - [ ] Default value handling
- [ ] **Unit Tests - IR Operations**
  - [ ] Expression evaluation
  - [ ] Hierarchy depth detection
  - [ ] Filter combination logic
- [ ] **Integration Tests**
  - [ ] Complex query IR representation
  - [ ] Round-trip serialization
  - [ ] Memory efficiency tests

-----

### Milestone 4: MDX to IR Transformer

**Timeline**: Weeks 6-7  
**Test Coverage Target**: 95% of transformation logic

#### Deliverables

- [ ] Complete transformer implementation
- [ ] Hierarchy normalization logic
- [ ] Set flattening algorithms
- [ ] Comment/hint extraction
- [ ] Error collection and reporting

#### Testing Requirements

- [ ] **Unit Tests - Basic Transformations**
  - [ ] Each grammar rule transformation
  - [ ] WITH clause handling
  - [ ] Axis mapping
  - [ ] Set expression normalization
- [ ] **Unit Tests - Hierarchy Handling**
  - [ ] Redundant level detection
  - [ ] Deepest level extraction
  - [ ] Ragged hierarchy support
- [ ] **Unit Tests - Error Handling**
  - [ ] Invalid syntax recovery
  - [ ] Circular reference detection
  - [ ] Missing member references
- [ ] **Integration Tests**
  - [ ] All 30 test cases end-to-end
  - [ ] Performance with large queries
  - [ ] Memory leak detection

-----

### Milestone 5: Query Linter

**Timeline**: Week 8  
**Test Coverage Target**: 90% of linting rules

#### Deliverables

- [ ] Linting rule engine
- [ ] Necto-specific pattern detection
- [ ] Query optimization rules
- [ ] Lint report generation

#### Testing Requirements

- [ ] **Unit Tests - Linting Rules**
  - [ ] Redundant nesting removal
  - [ ] Empty set elimination
  - [ ] Hierarchy optimization
  - [ ] Comment cleanup
- [ ] **Unit Tests - Pattern Detection**
  - [ ] Necto-specific patterns
  - [ ] Common MDX anti-patterns
  - [ ] Performance bottlenecks
- [ ] **Property-based Tests**
  - [ ] Linting preserves semantics
  - [ ] Optimization effectiveness

-----

### Milestone 6: DAX Generator

**Timeline**: Weeks 9-10  
**Test Coverage Target**: 95% of generation logic

#### Deliverables

- [ ] DAX query builder from IR
- [ ] Function mapping (MDX to DAX)
- [ ] Context transition handling
- [ ] DAX formatter integration

#### Testing Requirements

- [ ] **Unit Tests - Basic Generation**
  - [ ] EVALUATE statements
  - [ ] SUMMARIZECOLUMNS generation
  - [ ] Filter generation
  - [ ] Measure definitions
- [ ] **Unit Tests - Complex Patterns**
  - [ ] Time intelligence conversion
  - [ ] Hierarchy to table mapping
  - [ ] Calculated member conversion
- [ ] **Integration Tests**
  - [ ] All 30 test cases DAX output
  - [ ] DAX syntax validation
  - [ ] Performance comparison tests
- [ ] **Snapshot Tests**
  - [ ] DAX output consistency
  - [ ] Formatting stability

-----

### Milestone 7: SQL Explainer & Human-Readable Output

**Timeline**: Week 11  
**Test Coverage Target**: 90% of explanation logic

#### Deliverables

- [ ] SQL-like query generator
- [ ] Natural language explanation engine
- [ ] Query complexity analyzer
- [ ] Documentation generator

#### Testing Requirements

- [ ] **Unit Tests - SQL Generation**
  - [ ] SELECT clause generation
  - [ ] JOIN logic explanation
  - [ ] GROUP BY mapping
  - [ ] WHERE condition translation
- [ ] **Unit Tests - Explanations**
  - [ ] Measure descriptions
  - [ ] Dimension explanations
  - [ ] Filter clarifications
- [ ] **User Acceptance Tests**
  - [ ] Explanation clarity scoring
  - [ ] SQL-familiarity testing
  - [ ] Documentation completeness

-----

### Milestone 8: CLI Interface & User Experience

**Timeline**: Week 12  
**Test Coverage Target**: 85% of UI code

#### Deliverables

- [ ] Textual-based TUI with MDX editor
- [ ] File input/output handling
- [ ] Batch processing support
- [ ] Progress indicators
- [ ] Export formats (DAX, SQL, Markdown)

#### Testing Requirements

- [ ] **Unit Tests - CLI Commands**
  - [ ] Command parsing
  - [ ] File operations
  - [ ] Output formatting
- [ ] **Integration Tests**
  - [ ] End-to-end workflows
  - [ ] Error display handling
  - [ ] Large file processing
- [ ] **UI Tests**
  - [ ] Textual component testing
  - [ ] Keyboard navigation
  - [ ] Copy/paste functionality

-----

### Milestone 9: Performance & Optimization

**Timeline**: Week 13  
**Test Coverage Target**: Maintain existing coverage

#### Deliverables

- [ ] Performance profiling results
- [ ] Query optimization implementation
- [ ] Caching layer for repeated patterns
- [ ] Parallel processing for batch jobs
- [ ] Memory usage optimization

#### Testing Requirements

- [ ] **Performance Tests**
  - [ ] Large query benchmarks (>1000 lines)
  - [ ] Batch processing speed
  - [ ] Memory usage profiling
  - [ ] Cache effectiveness
- [ ] **Stress Tests**
  - [ ] Concurrent query processing
  - [ ] Memory leak detection
  - [ ] Error recovery under load
- [ ] **Regression Tests**
  - [ ] Performance baseline maintenance
  - [ ] Optimization verification

-----

### Milestone 10: Documentation & Release

**Timeline**: Week 14  
**Test Coverage Target**: 90% overall

#### Deliverables

- [ ] User documentation
- [ ] API documentation
- [ ] Tutorial with examples
- [ ] Architecture documentation
- [ ] Release packaging

#### Testing Requirements

- [ ] **Documentation Tests**
  - [ ] Code example validation
  - [ ] API documentation accuracy
  - [ ] Tutorial completeness
- [ ] **Release Tests**
  - [ ] Package installation testing
  - [ ] Dependency resolution
  - [ ] Cross-platform compatibility
- [ ] **End-to-End Validation**
  - [ ] Full test suite execution
  - [ ] Real-world query testing
  - [ ] User acceptance scenarios

-----

## Testing Strategy

### Test Pyramid

```
         /\
        /  \    E2E Tests (10%)
       /    \   - Full workflow tests
      /------\  - Real MDX files
     /        \ 
    /  Integr. \ Integration Tests (30%)
   /   Tests    \ - Component integration
  /--------------\ - Parser + Transformer
 /                \ - Transformer + Generator
/   Unit Tests     \ Unit Tests (60%)
└──────────────────┘ - Individual functions
                     - Class methods
                     - Edge cases
```

### Testing Best Practices

1. **Test-Driven Development** - Write tests before implementation
1. **Fixture Management** - Centralized test data in `tests/fixtures/`
1. **Mocking Strategy** - Mock external dependencies only
1. **Coverage Requirements** - Minimum 90% overall, 100% for critical paths
1. **Performance Testing** - Benchmark against baseline metrics
1. **Error Testing** - Every error path must have a test

### Continuous Testing

- Pre-commit hooks run unit tests
- PR checks run full test suite
- Nightly builds run performance tests
- Weekly runs of property-based tests
- Monthly security vulnerability scans

-----

## Risk Mitigation

### Technical Risks

1. **Lark Performance** - Mitigate with grammar optimization and caching
1. **Complex Hierarchies** - Extensive test cases, fallback strategies
1. **DAX Compatibility** - Validate against Power BI, iterate based on feedback

### Testing Risks

1. **Test Maintenance** - Use fixtures and factories to minimize duplication
1. **Flaky Tests** - Identify and fix non-deterministic tests immediately
1. **Coverage Gaps** - Weekly coverage reviews, mutation testing

-----

## Success Metrics

1. **Code Quality**
- Test coverage > 90%
- Zero critical bugs in production
- All linting rules pass
1. **Performance**
- Parse 1000-line MDX query < 1 second
- Generate DAX < 100ms after parsing
- Memory usage < 500MB for large queries
1. **User Satisfaction**
- Clear error messages for 100% of invalid queries
- Human-readable output rated “understandable” by SQL users
- Successfully convert 95% of Necto-generated queries

-----

## Timeline Summary

- **Weeks 1-3**: Foundation (Setup, Parser)
- **Weeks 4-7**: Core Logic (IR, Transformer)
- **Weeks 8-10**: Conversion (Linter, DAX Generator)
- **Weeks 11-12**: User Experience (Explainer, CLI)
- **Weeks 13-14**: Polish (Performance, Documentation)

**Total Duration**: 14 weeks with comprehensive testing throughout
