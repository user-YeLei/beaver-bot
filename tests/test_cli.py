"""Tests for Beaver Bot CLI"""

import pytest
from typer.testing import CliRunner

from beaver_bot.main import app


@pytest.fixture
def runner():
    return CliRunner()


def test_help_command(runner):
    """Test --help shows all commands"""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "run" in result.output
    assert "chat" in result.output
    assert "model" in result.output


def test_version_command(runner):
    """Test version command"""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "Beaver Bot" in result.output


def test_model_command_show(runner):
    """Test model show command"""
    result = runner.invoke(app, ["model", "--show"])
    assert result.exit_code == 0


def test_chat_single_query(runner):
    """Test single query chat mode"""
    result = runner.invoke(app, ["chat", "-q", "你好"])
    assert result.exit_code == 0
    assert "Beaver" in result.output or "🦫" in result.output
