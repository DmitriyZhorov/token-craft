# AGENTS.md: Instructions for AI Agents

This document provides guidelines for AI agents working in the `token-craft` repository.

## 1. Project Overview

`token-craft` is a gamified LLM token optimization tool. It analyzes usage patterns from platforms like Claude Code or Cursor and provides prescriptive insights through a space-themed ranking and achievement system.

The core philosophy is to encourage *prudent* and *sustainable* optimization, not aggressive token maximization. The tool is written in Python 3.8+ and has no external dependencies.

## 2. Build, Lint, and Test Commands

### Linting

The project follows the PEP 8 style guide. Use a linter to ensure compliance before committing code.

```bash
# Lint with flake8 (assumed, not specified)
pip install flake8
flake8 token_craft/ tests/

# Format with black (assumed, not specified)
pip install black
black token_craft/ tests/
```

### Testing

The project uses `pytest` for testing. The test suite is located in the `tests/` directory.

```bash
# Run the full test suite
python -m pytest tests/ -v

# Run a specific test class
python -m pytest tests/test_scoring.py::TestDifficultyModifier -v

# Run a specific test method by name
python -m pytest -k "test_streak_bonus" -v

# Run tests with code coverage
pip install pytest-cov
python -m pytest tests/ --cov=token_craft --cov-report=html
```

### Build Process

This is a pure Python project with no compilation or build step.

## 3. Code Style and Conventions

### Formatting

- **PEP 8:** All code must adhere to the [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/).
- **Line Length:** Maximum line length is 88 characters, compatible with `black`.
- **Indentation:** Use 4 spaces for indentation.

### Naming Conventions

- **Variables & Functions:** `snake_case` (e.g., `scoring_engine`, `calculate_bonus`).
- **Classes:** `PascalCase` (e.g., `ScoringEngine`, `RankSystem`).
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `MAX_SCORE`, `DEFAULT_CONFIG`).
- **Modules:** `snake_case.py` (e.g., `scoring_engine.py`).
- **Private Members:** Use a single leading underscore for internal attributes/methods (e.g., `_calculate_rank`).

### Type Hinting

- All function signatures (arguments and return types) must include type hints.
- Use the `typing` module for complex types (`List`, `Dict`, `Tuple`, `Optional`).
- Annotate variables where the type cannot be easily inferred.

```python
from typing import Dict, Optional

def get_user_profile(user_id: str) -> Optional[Dict[str, any]]:
    # ... implementation ...
```

### Imports

Order imports in the following sequence, separated by a blank line:
1.  Standard library imports (`os`, `sys`, `json`).
2.  Third-party library imports (none in this project).
3.  Local application imports (`from token_craft import ...`).

### Docstrings

- Every module, class, and function should have a descriptive docstring.
- Use Google-style docstrings for clarity.

```python
def calculate_score(session_data: dict) -> int:
    """Calculates the final score based on session data.

    Args:
        session_data: A dictionary containing token usage and other metrics.

    Returns:
        The calculated score as an integer.
    """
    # ...
```

### Error Handling

- Avoid bare `except:` clauses. Catch specific exceptions.
- Use custom exception classes for application-specific errors if needed.
- Log errors with sufficient context.

### Comments

- Use comments to explain the *why*, not the *what*.
- Avoid obvious comments that restate the code.
- Keep comments up-to-date with code changes.

## 4. Agent-Specific Instructions

### Cursor / Copilot Rules

- No `.cursor/rules` or `.github/copilot-instructions.md` file was found in this repository.
- Agents should adhere to the general guidelines in this document.

### General Workflow

1.  **Understand the Goal:** Before writing code, understand the user's request and the existing codebase.
2.  **Run Tests First:** Ensure the current test suite passes before making changes.
3.  **Write/Modify Code:** Follow the style and conventions outlined above. Add new tests for new functionality.
4.  **Run Tests Again:** Verify that all tests, including your new ones, pass.
5.  **Lint Your Code:** Run a linter to check for any style issues.
6.  **Commit:** Write a clear and concise commit message.
