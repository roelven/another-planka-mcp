# Contributing to Planka MCP Server

Thank you for considering contributing to the Planka MCP Server! This document outlines the requirements and guidelines for contributing.

## Requirements for All Contributions

### ✅ All Tests Must Pass

**This is a strict requirement.** No code will be merged that fails any tests.

```bash
# Before committing, run all tests
pytest

# Tests must pass with >80% coverage
pytest --cov=planka_mcp --cov-fail-under=80
```

### Code Quality Standards

1. **Tests Required**: All new features must include tests
2. **Coverage**: Maintain >90% test coverage for new code
3. **Documentation**: Update relevant documentation (README, TESTING.md)
4. **Type Hints**: Use type hints for all function signatures
5. **Docstrings**: All public functions must have docstrings

## Development Workflow

### 1. Set Up Development Environment

```bash
# Clone the repository
git clone git@github.com:roelven/another-planka-mcp.git
cd another-planka-mcp

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install
```

### 2. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Make Your Changes

Follow these guidelines:
- Write tests FIRST (TDD approach recommended)
- Implement your feature
- Ensure all tests pass
- Update documentation

### 4. Run Tests

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=planka_mcp --cov-report=html

# Run specific test file
pytest tests/test_tools.py -v

# Run specific test
pytest tests/test_tools.py::TestPlankaGetWorkspace::test_get_workspace_success_markdown -v
```

**Required**: ALL tests must pass before committing.

### 5. Check Code Quality

```bash
# Format code with black
black planka_mcp.py tests/

# Sort imports with isort
isort planka_mcp.py tests/

# Lint with flake8
flake8 planka_mcp.py tests/ --max-line-length=120
```

### 6. Commit Your Changes

```bash
git add .
git commit -m "Your descriptive commit message

- Detail 1
- Detail 2

🤖 Generated with Claude Code

Co-Authored-By: Your Name <your.email@example.com>"
```

**Note**: If you have pre-commit hooks installed, tests will run automatically before commit.

### 7. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Writing Tests

### Test Requirements

Every new feature must include:

1. **Unit tests** for the feature in isolation
2. **Integration tests** with mocked dependencies
3. **Error handling tests** for all error paths
4. **Edge case tests** for boundary conditions

### Test Structure

```python
import pytest
from unittest.mock import AsyncMock, patch

class TestYourFeature:
    """Test your feature functionality."""

    @pytest.mark.asyncio
    async def test_happy_path(self):
        """Test the main success scenario."""
        # Arrange
        mock_api = AsyncMock()
        mock_api.get.return_value = {"data": "value"}

        # Act
        with patch('planka_mcp.api_client', mock_api):
            result = await your_function()

        # Assert
        assert result == expected_value
        mock_api.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling."""
        # Test error scenarios
        pass

    def test_edge_cases(self):
        """Test boundary conditions."""
        # Test edge cases
        pass
```

### Running Tests Efficiently

```bash
# Run only fast tests during development
pytest -m "not slow"

# Run failed tests first
pytest --ff

# Run tests in parallel (faster)
pytest -n auto

# Watch for changes and re-run tests
ptw
```

## Code Style

### Python Style Guide

- Follow PEP 8
- Use Black for formatting (line length: 120)
- Use isort for import sorting
- Maximum complexity: 10 (flake8)

### Type Hints

```python
from typing import Optional, List, Dict

async def my_function(
    param1: str,
    param2: Optional[int] = None
) -> Dict[str, Any]:
    """Function with proper type hints."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def my_function(param1: str, param2: int) -> bool:
    """Short description of function.

    Longer description if needed. Explain what the function does,
    not how it does it (code should be self-explanatory).

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: If param1 is empty
        TypeError: If param2 is not an integer

    Examples:
        >>> my_function("test", 5)
        True
    """
    pass
```

## CI/CD Pipeline

### Automated Checks

Every push triggers:

1. **Test Suite**: All tests must pass (Python 3.10, 3.11, 3.12)
2. **Coverage Check**: Must maintain >80% coverage
3. **Linting**: Black, isort, flake8 checks
4. **Type Checking**: MyPy validation (if configured)

### Pull Request Requirements

Before a PR can be merged:

- ✅ All tests pass
- ✅ Coverage >80%
- ✅ No linting errors
- ✅ Code review approved
- ✅ Documentation updated
- ✅ CHANGELOG updated (if applicable)

## Adding New Tools

When adding a new MCP tool:

1. **Plan**: Update IMPLEMENTATION_PLAN.md
2. **Model**: Create Pydantic input model in planka_mcp.py
3. **Test Model**: Add tests in tests/test_models.py
4. **Implement**: Add tool function with proper annotations
5. **Test Tool**: Add comprehensive tests in tests/test_tools.py
6. **Document**: Update README.md with tool documentation
7. **Verify**: Run all tests and ensure they pass

### New Tool Checklist

- [ ] Pydantic input model with Field() descriptions
- [ ] Tool function with @mcp.tool decorator
- [ ] Proper tool annotations (readOnlyHint, etc.)
- [ ] Comprehensive docstring with examples
- [ ] Unit tests (happy path, errors, edge cases)
- [ ] Integration tests with mocked API
- [ ] README documentation
- [ ] TESTING.md updated (if needed)
- [ ] All tests passing

## Bug Reports

When reporting bugs:

1. Check if the bug already exists in Issues
2. Provide minimal reproduction steps
3. Include relevant error messages
4. Specify your environment (Python version, OS)
5. Include relevant test output

## Feature Requests

When requesting features:

1. Check if the feature already exists in Issues
2. Explain the use case and benefit
3. Provide examples of desired behavior
4. Discuss implementation approach (optional)

## Questions?

- Read [TESTING.md](TESTING.md) for testing details
- Read [README.md](README.md) for usage documentation
- Check existing Issues and Discussions
- Ask in GitHub Discussions

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the project's technical standards

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Remember**: All tests must pass. No exceptions. This ensures we maintain a reliable, production-quality codebase.
