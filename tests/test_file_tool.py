"""Tests for Beaver Bot File Tool"""

import pytest
import tempfile
import os
from pathlib import Path

from beaver_bot.tools.file_tool import FileTool
from beaver_bot.core.config import BeaverConfig, AppConfig, FileToolConfig


@pytest.fixture
def config():
    return BeaverConfig(
        app=AppConfig(debug=True),
        file_tool=FileToolConfig(root_path=Path("/"))  # Allow temp files in tests
    )


@pytest.fixture
def file_tool(config):
    return FileTool(config)


@pytest.fixture
def temp_file():
    """Create a temporary test file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("# Test file\nprint('hello')\n")
        f.write("x = 1 + 2\n")
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


def test_read_file(file_tool, temp_file):
    """Test reading a file"""
    result = file_tool.read_file(temp_file)
    assert "Test file" in result
    assert "print('hello')" in result
    assert "📄" in result


def test_read_file_with_limit(file_tool, temp_file):
    """Test reading file with line limit"""
    result = file_tool.read_file(temp_file, limit=1)
    assert "前1行" in result


def test_read_nonexistent_file(file_tool):
    """Test reading a file that doesn't exist"""
    result = file_tool.read_file("/nonexistent/path/file.py")
    assert "not found" in result.lower()


def test_write_and_read_file(file_tool):
    """Test writing then reading a file"""
    test_content = "# New file\ny = 42\n"

    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = os.path.join(tmpdir, "test_write.py")
        result = file_tool.write_file(test_path, test_content)

        assert "✅" in result or "written" in result.lower()

        # Verify by reading
        read_result = file_tool.read_file(test_path)
        assert "New file" in read_result
        assert "y = 42" in read_result


def test_list_directory(file_tool):
    """Test listing directory contents"""
    result = file_tool.list_directory(".")
    assert "📂" in result
    assert "beaver_bot" in result.lower() or "src" in result.lower()


def test_list_nonexistent_directory(file_tool):
    """Test listing a directory that doesn't exist"""
    result = file_tool.list_directory("/nonexistent/directory")
    assert "not found" in result.lower()


def test_search_files(file_tool):
    """Test searching for files by pattern"""
    result = file_tool.search_files("*.py", path="src")
    assert "py" in result.lower() or "Found" in result


def test_search_content(file_tool):
    """Test searching for content in files"""
    result = file_tool.search_content("def ", path="src/beaver_bot")
    # Should find Python function definitions
    assert result  # Just verify it runs without error


def test_check_project_structure(file_tool):
    """Test checking project structure"""
    result = file_tool.check_project_structure(".")
    assert "📂" in result
    # Should find some common project files
    assert "pyproject" in result or "src" in result
