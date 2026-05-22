"""Tests for string utilities."""

import pytest

from odp_platform.common.string_utils import get_display_width, pad_to_width, format_table_row, format_table_separator


class TestGetDisplayWidth:
    """Test display width calculation."""

    def test_ascii(self):
        assert get_display_width("hello") == 5

    def test_chinese(self):
        assert get_display_width("你好") == 4

    def test_mixed(self):
        assert get_display_width("hi你好") == 6

    def test_empty(self):
        assert get_display_width("") == 0


class TestPadToWidth:
    """Test padding strings to target width."""

    def test_pad_left(self):
        assert pad_to_width("hello", 10) == "hello     "

    def test_pad_right(self):
        assert pad_to_width("hello", 10, "right") == "     hello"

    def test_chinese_pad(self):
        result = pad_to_width("你好", 10)
        assert get_display_width(result) == 10
        assert result == "你好      "

    def test_no_padding_needed(self):
        assert pad_to_width("hello", 5) == "hello"

    def test_center(self):
        result = pad_to_width("hi", 6, "center")
        assert result == "  hi  "


class TestFormatTableRow:
    """Test table row formatting."""

    def test_basic_row(self):
        row = format_table_row(["name", "count"], [10, 8])
        assert "name" in row
        assert "count" in row

    def test_row_with_align(self):
        row = format_table_row(["a", "b"], [5, 5], ["left", "right"])
        assert "a    " in row
        assert "    b" in row


class TestFormatTableSeparator:
    """Test table separator generation."""

    def test_separator_length(self):
        sep = format_table_separator([10, 8])
        assert len(sep) == 10 + 1 + 8
        assert set(sep) == {"-"}