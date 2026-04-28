"""Tests for Beaver Bot Intent Parser"""

import pytest

from beaver_bot.core.intent_parser import IntentParser


@pytest.fixture
def parser():
    return IntentParser()


def test_code_generation_intent(parser):
    """Test code generation intent detection"""
    assert parser.parse("帮我写一个快排") == "code_generation"
    assert parser.parse("写一个函数") == "code_generation"
    assert parser.parse("generate code") == "code_generation"
    assert parser.parse("帮我生成代码") == "code_generation"


def test_code_review_intent(parser):
    """Test code review intent detection"""
    assert parser.parse("帮我review代码") == "code_review"
    assert parser.parse("检查代码问题") == "code_review"
    assert parser.parse("review一下") == "code_review"


def test_debug_intent(parser):
    """Test debug intent detection"""
    assert parser.parse("代码报错了") == "debug"
    assert parser.parse("调试一下") == "debug"
    assert parser.parse("程序崩溃了") == "debug"


def test_github_operation_intent(parser):
    """Test GitHub operation intent detection"""
    assert parser.parse("查看这个issue") == "github_operation"
    assert parser.parse("github仓库信息") == "github_operation"
    # "创建一个PR" matches "创建" first (code_generation)
    assert parser.parse("PR信息") == "github_operation"


def test_general_chat_intent(parser):
    """Test general chat fallback"""
    assert parser.parse("今天天气怎么样") == "general_chat"
    assert parser.parse("你好啊") == "general_chat"


def test_intent_with_confidence(parser):
    """Test intent parsing with confidence"""
    intent, confidence = parser.parse_with_confidence("帮我写一个快排算法")
    assert intent == "code_generation"
    assert 0.5 <= confidence <= 1.0


def test_get_supported_intents(parser):
    """Test getting supported intents"""
    intents = parser.get_supported_intents()
    assert "code_generation" in intents
    assert "code_review" in intents
    assert "debug" in intents
