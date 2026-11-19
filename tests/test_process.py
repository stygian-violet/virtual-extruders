from typing import Any

import pytest

from virtual_extruders import GCodeError, process

from .util import lines


@pytest.mark.parametrize(('input_name', 'output_name', 'kwargs'), [
    ('basic', 'basic_out', {}),
    ('basic', 'basic_out_skip_first_tc', {'skip_first_tool_change': True}),
    ('basic', 'basic_out_custom_gcode', {'tool_change_gcode': ['M601']}),
    ('basic_out', 'basic_out', {}),
    (
        'basic_out_skip_first_tc',
        'basic_out_skip_first_tc',
        {'skip_first_tool_change': True}
    ),
    ('basic_out', 'basic_out_skip_first_tc', {'skip_first_tool_change': True}),
    ('single_extruder', 'single_extruder', {}),
    ('custom_tc_block', 'custom_tc_block_out', {}),
    (
        'custom_tc_block',
        'custom_tc_block_out_skip_first_tc',
        {'skip_first_tool_change': True}
    ),
])
def test_process(
    input_name: str,
    output_name: str,
    kwargs: dict[str, Any]
) -> None:
    processed_lines = process(lines(input_name), **kwargs)
    output_lines = lines(output_name)
    assert list(processed_lines) == list(output_lines)


@pytest.mark.parametrize(('input_name', 'line', 'line_n'), [
    ('err_unmatched_block_start', ';TOOL_CHANGE', 10),
    ('err_unmatched_block_start_2', ';TOOL_CHANGE', 2),
    ('err_unmatched_block_end', ';TOOL_CHANGE_END', 4),
    ('err_different_tool_temperatures', 'M104 S220 T1 ; set temperature', 337),
    ('err_unknown_tool_gcode', 'M000 T1', 1),
])
def test_process_error(input_name: str, line: str, line_n: int) -> None:
    with pytest.raises(GCodeError) as exc_info:
        for _ in process(lines(input_name)):
            pass
    assert exc_info.value.line == line
    assert exc_info.value.line_n == line_n
