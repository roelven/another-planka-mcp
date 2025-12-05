# Testing Guide for Planka MCP Server

This document explains how to run and write tests for the Planka MCP Server.

## Quick Start

```bash
# Install dependencies including test packages
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=planka_mcp --cov-report=html

# View coverage report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Test Structure

```
tests/
├── __init__.py              # Test package init
├── conftest.py              # Shared fixtures and configuration
├── test_infrastructure.py   # Tests for API client, cache, formatters
├── test_models.py           # Tests for Pydantic input validation
└── test_tools.py            # Tests for all 9 MCP tools
```

## Test Coverage

### Infrastructure Tests (test_infrastructure.py)
- ✅ **PlankaAPIClient**: HTTP client, request methods, cleanup
- ✅ **PlankaCache**: Cache hits/misses, expiration, invalidation
- ✅ **CacheEntry**: Validity checks, TTL behavior
- ✅ **ResponseFormatter**: Card formatting, task progress, truncation
- ✅ **PaginationHelper**: Page calculations, edge cases
- ✅ **Error Handling**: All HTTP status codes, timeouts, connection errors

### Model Tests (test_models.py)
- ✅ **Input Validation**: All 8 Pydantic models
- ✅ **Required Fields**: Missing field detection
- ✅ **Field Constraints**: Min/max lengths, ranges
- ✅ **String Processing**: Whitespace stripping
- ✅ **Extra Fields**: Forbidden field detection
- ✅ **Enum Values**: All enum types

### Tool Tests (test_tools.py)
- ✅ **planka_get_workspace**: 6 tests (cache, errors, formats)
- ✅ **planka_list_cards**: 9 tests (filtering, pagination, detail levels)
- ✅ **planka_find_and_get_card**: 7 tests (search, multiple matches)
- ✅ **planka_get_card**: 6 tests (cache, formats, errors)
- ✅ **planka_create_card**: 4 tests (validation, cache invalidation)
- ✅ **planka_update_card**: 6 tests (fields, moves, invalidation)
- ✅ **planka_add_task**: 5 tests (list creation, errors)
- ✅ **planka_update_task**: 4 tests (completion states, errors)
- ✅ **Cache Behavior**: 3 tests (TTL, cleanup, invalidation)
- ✅ **Edge Cases**: 6 tests (truncation, empty results, timeouts)

**Total: 56+ comprehensive tests**

## Running Specific Tests

```bash
# Run a specific test file
pytest tests/test_tools.py

# Run a specific test class
pytest tests/test_tools.py::TestPlankaGetWorkspace

# Run a specific test
pytest tests/test_tools.py::TestPlankaGetWorkspace::test_get_workspace_success_markdown

# Run tests matching a pattern
pytest -k "cache"  # All tests with "cache" in the name

# Run only unit tests (if marked)
pytest -m unit

# Run excluding slow tests
pytest -m "not slow"
```

## Coverage Reports

```bash
# Generate coverage report in terminal
pytest --cov=planka_mcp --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=planka_mcp --cov-report=html

# Fail if coverage is below threshold
pytest --cov=planka_mcp --cov-fail-under=80
```

**Coverage Goal**: >90% for production code (excluding tests)

## Writing New Tests

### Test Structure

```python
import pytest
from unittest.mock import AsyncMock, patch

class TestNewFeature:
    """Test new feature functionality."""

    @pytest.mark.asyncio
    async def test_happy_path(self):
        """Test the happy path scenario."""
        # Arrange
        mock_api = AsyncMock()
        mock_api.get.return_value = {"data": "value"}

        # Act
        result = await my_function()

        # Assert
        assert result == expected_value
```

### Using Fixtures

```python
def test_with_fixtures(sample_workspace_data, mock_planka_api_client):
    """Test using shared fixtures from conftest.py."""
    # Fixtures are automatically available
    assert "projects" in sample_workspace_data
```

### Mocking API Calls

```python
@pytest.mark.asyncio
async def test_api_call(mocker):
    """Test with mocked API call."""
    # Mock the global api_client
    mock_client = AsyncMock()
    mock_client.get.return_value = {"item": {"id": "123"}}

    with patch('planka_mcp.api_client', mock_client):
        result = await my_tool()
        mock_client.get.assert_called_once()
```

### Testing Error Handling

```python
@pytest.mark.asyncio
async def test_error_handling(mock_planka_api_client):
    """Test error handling."""
    import httpx
    from unittest.mock import Mock

    # Create HTTP error
    response = Mock()
    response.status_code = 404
    error = httpx.HTTPStatusError("Not Found", request=Mock(), response=response)

    mock_planka_api_client.get.side_effect = error

    with patch('planka_mcp.api_client', mock_planka_api_client):
        result = await my_tool()
        assert "not found" in result.lower()
```

## Test Best Practices

### 1. Test Naming
- Use descriptive names: `test_get_workspace_returns_cached_data`
- Follow pattern: `test_<function>_<scenario>_<expected>`
- Use underscores for readability

### 2. Test Organization
- One test class per tool/component
- Group related tests together
- Use clear docstrings

### 3. Assertions
- Be specific with assertions
- Test multiple aspects when needed
- Use appropriate assert methods

```python
# Good
assert result["id"] == "card123"
assert "Test Card" in output
assert len(items) == 5

# Avoid
assert result  # Too vague
```

### 4. Test Independence
- Each test should run independently
- Don't rely on test execution order
- Clean up after tests if needed

### 5. Mock External Dependencies
- Always mock API calls
- Mock time-dependent operations
- Use fixtures for common mocks

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run tests
      run: |
        pytest --cov=planka_mcp --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Debugging Tests

```bash
# Run with debugging output
pytest -vv --tb=long

# Drop into debugger on failure
pytest --pdb

# Show print statements
pytest -s

# Run only failed tests from last run
pytest --lf

# Run failed tests first, then others
pytest --ff
```

## Performance Testing

```bash
# Show slowest tests
pytest --durations=10

# Profile test execution
pytest --profile

# Mark slow tests and skip them
pytest -m "not slow"
```

## Common Issues

### 1. Import Errors
```bash
# Make sure to run pytest from project root
cd /path/to/planka-mcp
pytest
```

### 2. Async Test Failures
```python
# Always use @pytest.mark.asyncio for async tests
@pytest.mark.asyncio
async def test_my_async_function():
    result = await my_async_function()
```

### 3. Mock Not Working
```python
# Patch at the location where it's used, not where it's defined
# If planka_mcp imports api_client, patch 'planka_mcp.api_client'
with patch('planka_mcp.api_client', mock_client):
    ...
```

## Test Maintenance

### Regular Tasks
- ✅ Run full test suite before commits
- ✅ Update tests when adding new features
- ✅ Keep test coverage above 80%
- ✅ Review and update fixtures periodically
- ✅ Remove obsolete tests

### Adding New Features
1. Write tests first (TDD approach)
2. Implement feature
3. Verify all tests pass
4. Check coverage hasn't dropped
5. Document new test requirements

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest AsyncIO](https://pytest-asyncio.readthedocs.io/)
- [Unittest Mock](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py](https://coverage.readthedocs.io/)

## Success Criteria

Tests are considered successful when:
- ✅ All tests pass
- ✅ Coverage is >90%
- ✅ No flaky tests
- ✅ Fast execution (<30 seconds)
- ✅ Clear failure messages
- ✅ Well-organized and maintainable

## Getting Help

If tests are failing:
1. Read the error message carefully
2. Run with `-vv` for more details
3. Check if mocks are configured correctly
4. Verify fixtures are being used properly
5. Ensure async tests use `@pytest.mark.asyncio`
6. Check that imports are correct
