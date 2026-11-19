import sys
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from virtual_extruders import (
    DEFAULT_TOOL_CHANGE_BLOCK_END,
    DEFAULT_TOOL_CHANGE_BLOCK_START,
    DEFAULT_TOOL_CHANGE_GCODE,
    GCodeError,
    ToolTemperature,
    comment_out,
    format_lines,
    get_tool_change_gcode,
    join,
    open_input,
    open_output,
    parse_tool_selection,
    parse_tool_temperature,
    split,
)


@pytest.mark.parametrize(('message', 'line', 'line_n'), [
    ('msg', 'M600', 11),
    ('msg', 'M600', None),
    ('msg', None, 11),
    ('msg', None, None)
])
def test_gcode_error_to_string(
    message: str,
    line: str | None,
    line_n: int | None
) -> None:
    res = str(GCodeError(message, line, line_n))
    assert message in res
    if line is not None:
        assert line in res
    if line_n is not None:
        assert str(line_n) in res


@pytest.mark.parametrize(('line', 'message', 'result'), [
    ('', '', ''),
    ('', 'comment', '; comment'),
    (';comment', '', ';comment'),
    (';comment', 'comment2', ';comment, comment2'),
    ('line', '', ';line'),
    ('line', 'comment', ';line ; comment'),
    ('line ;comment', 'comment2', ';line ;comment, comment2'),
])
def test_comment_out(line: str, message: str, result: str) -> None:
    assert comment_out(line, message) == result


@pytest.mark.parametrize(('lines', 'kwargs', 'result'), [
    ('x=[x]', {'x': 0}, ['x=0']),
    (['x=[x]', 'y=[y]'], {'x': 0, 'y': 1}, ['x=0', 'y=1']),
])
def test_format_lines(
    lines: str | list[str],
    kwargs: dict[str, Any],
    result: str
) -> None:
    assert list(format_lines(lines, **kwargs)) == result


@pytest.mark.parametrize(('gcode', 'result'), [
    (None, DEFAULT_TOOL_CHANGE_GCODE),
    (
        ['M600'],
        [DEFAULT_TOOL_CHANGE_BLOCK_START, 'M600', DEFAULT_TOOL_CHANGE_BLOCK_END]
    ),
    (
        [DEFAULT_TOOL_CHANGE_BLOCK_START, 'M600'],
        [DEFAULT_TOOL_CHANGE_BLOCK_START, 'M600', DEFAULT_TOOL_CHANGE_BLOCK_END]
    ),
    (
        ['M600', DEFAULT_TOOL_CHANGE_BLOCK_END],
        [DEFAULT_TOOL_CHANGE_BLOCK_START, 'M600', DEFAULT_TOOL_CHANGE_BLOCK_END]
    ),
    (
        [DEFAULT_TOOL_CHANGE_BLOCK_START, 'M600', DEFAULT_TOOL_CHANGE_BLOCK_END],
        [DEFAULT_TOOL_CHANGE_BLOCK_START, 'M600', DEFAULT_TOOL_CHANGE_BLOCK_END]
    ),
])
def test_get_tool_change_gcode(gcode: list[str] | None, result: list[str]) -> None:
    assert get_tool_change_gcode(gcode) == result


@pytest.mark.parametrize(('cmd', 'comment', 'result'), [
    ([], '', ''),
    ([], ';comment', ';comment'),
    (['M104', 'S240'], '', 'M104 S240'),
    (['M104', 'S240'], '; set temperature', 'M104 S240 ; set temperature'),
])
def test_join(cmd: list[str], comment: str, result: str) -> None:
    assert join(cmd, comment) == result


@pytest.mark.parametrize(('line', 'cmd', 'comment'), [
    ('', [], ''),
    (';comment', [], ';comment'),
    ('\tM104 S240\n', ['M104', 'S240'], ''),
    ('\tM104 S240   ; set temperature\n', ['M104', 'S240'], '; set temperature')
])
def test_split(line: str, cmd: list[str], comment: str) -> None:
    assert split(line) == (cmd, comment)


def test_open_input_stdin() -> None:
    with open_input(None) as fp:
        assert fp is sys.stdin


@patch('virtual_extruders.open')
def test_open_input_file(mock_open: MagicMock) -> None:
    name = 'test.gcode'
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    with open_input(name) as fp:
        assert fp is mock_file
    mock_open.assert_called_once_with(name, 'r')


def test_open_output_stdout() -> None:
    with open_output(None) as fp:
        assert fp is sys.stdout


@patch('virtual_extruders.open')
def test_open_output_file(mock_open: MagicMock) -> None:
    name = 'test.gcode'
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    with open_output(name) as fp:
        assert fp is mock_file
    mock_open.assert_called_once_with(name, 'w')


@pytest.mark.parametrize(('cmd', 'result'), [
    (['M600'], None),
    (['T0', 'T1'], None),
    (['T2'], 2),
])
def test_parse_tool_selection(cmd: list[str], result: int | None) -> None:
    assert parse_tool_selection(cmd) == result


@pytest.mark.parametrize(('cmd', 'result'), [
    (['M600'], None),
    (['M104', 'S220'], None),
    (['M104', 'S220', 'S220'], None),
    (['M109', 'S220', 'T1', 'T2'], None),
    (['M104', 'T0', 'S220'], ToolTemperature('M104', 'S220', 0)),
    (['M109', 'S240', 'T1'], ToolTemperature('M109', 'S240', 1)),
])
def test_parse_tool_temperature(cmd: list[str], result: int | None) -> None:
    assert parse_tool_temperature(cmd) == result
