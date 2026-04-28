"""Tests for Beaver Bot Session Memory"""

import pytest
import time

from beaver_bot.core.memory.session import SessionMemory


@pytest.fixture
def memory():
    return SessionMemory()


def test_add_message(memory):
    """Test adding messages to memory"""
    memory.add_message("user", "Hello")
    memory.add_message("assistant", "Hi there")

    history = memory.get_history()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"


def test_clear_memory(memory):
    """Test clearing memory"""
    memory.add_message("user", "Hello")
    memory.clear()

    history = memory.get_history()
    assert len(history) == 0


def test_get_history_with_limit(memory):
    """Test getting history with limit"""
    for i in range(10):
        memory.add_message("user", f"Message {i}")

    history = memory.get_history(limit=3)
    assert len(history) == 3


def test_search_memory(memory):
    """Test searching memory"""
    memory.add_message("user", "Write a quicksort")
    memory.add_message("assistant", "Here's a quicksort")
    memory.add_message("user", "Add tests")

    results = memory.search("quicksort")
    assert len(results) == 2


def test_get_context(memory):
    """Test getting formatted context"""
    memory.add_message("user", "Hello")
    memory.add_message("assistant", "Hi")

    context = memory.get_context()
    assert "user" in context
    assert "Hello" in context


def test_max_history_limit(memory):
    """Test that memory respects max history limit"""
    mem = SessionMemory(max_history=5)

    for i in range(10):
        mem.add_message("user", f"Message {i}")

    history = mem.get_history()
    assert len(history) == 5
    assert history[0]["content"] == "Message 5"  # Oldest messages dropped


def test_metadata_tracking(memory):
    """Test that metadata is tracked"""
    memory.add_message("user", "Test")

    assert "created_at" in memory.metadata
    assert "last_updated" in memory.metadata
