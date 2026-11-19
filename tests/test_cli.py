from io import StringIO
from typing import Any
from unittest.mock import ANY, MagicMock, patch

import pytest

from virtual_extruders import INPLACE_STDIN, GCodeError, main, parse_args

from .util import path


@pytest.mark.parametrize(('args', 'message'), [
    (['-i', '-'], INPLACE_STDIN)
])
@patch('virtual_extruders.sys.stderr', new_callable=StringIO)
def test_parse_args_error(
    stderr: StringIO,
    args: list[str],
    message: str | None
) -> None:
    with pytest.raises(SystemExit):
        parse_args(args)
    stderr.seek(0)
    if message is not None:
        assert message in stderr.read()


@pytest.mark.parametrize(('args', 'fname_in', 'fname_out', 'process_kwargs'), [
    (
        ['file.gcode'],
        'file.gcode',
        None,
        { 'skip_first_tool_change': False, 'tool_change_gcode': None }
    ),
    (
        ['-'],
        None,
        None,
        { 'skip_first_tool_change': False, 'tool_change_gcode': None }
    ),
    (
        ['-i', 'file.gcode'],
        'file.gcode',
        'file.gcode.tmp',
        { 'skip_first_tool_change': False, 'tool_change_gcode': None }
    ),
    (
        ['-f', 'file.gcode'],
        'file.gcode',
        None,
        { 'skip_first_tool_change': True, 'tool_change_gcode': None }
    ),
    (
        ['-g', 'M600', 'M601', '--', 'file.gcode'],
        'file.gcode',
        None,
        {
            'skip_first_tool_change': False,
            'tool_change_gcode': ['M600', 'M601']
        }
    ),
])
@patch('virtual_extruders.process')
@patch('virtual_extruders.open_output')
@patch('virtual_extruders.open_input')
@patch('virtual_extruders.os.rename')
@patch('virtual_extruders.os.remove')
def test_main_args(
    remove_mock: MagicMock,
    rename_mock: MagicMock,
    open_input_mock: MagicMock,
    open_output_mock: MagicMock,
    process_mock: MagicMock,
    args: list[str],
    fname_in: str | None,
    fname_out: str | None,
    process_kwargs: dict[str, Any]
) -> None:
    main(args)
    open_input_mock.assert_called_once_with(fname_in)
    open_output_mock.assert_called_once_with(fname_out)
    process_mock.assert_called_once_with(ANY, **process_kwargs)
    if fname_out is not None:
        rename_mock.assert_called_once_with(fname_out, fname_in)
    else:
        rename_mock.assert_not_called()
    remove_mock.assert_not_called()


@pytest.mark.parametrize(('args', 'fname_in', 'fname_out'), [
    (['file.gcode'], 'file.gcode', None),
    (['-i', 'file.gcode'], 'file.gcode', 'file.gcode.tmp'),
])
@patch('virtual_extruders.process', side_effect=GCodeError('test', None, None))
@patch('virtual_extruders.open_output')
@patch('virtual_extruders.open_input')
@patch('virtual_extruders.os.rename')
@patch('virtual_extruders.os.remove')
@patch('virtual_extruders.os.path.exists', return_value=True)
def test_main_error(
    exists_mock: MagicMock,
    remove_mock: MagicMock,
    rename_mock: MagicMock,
    open_input_mock: MagicMock,
    open_output_mock: MagicMock,
    process_mock: MagicMock,
    args: list[str],
    fname_in: str | None,
    fname_out: str | None
) -> None:
    with pytest.raises(GCodeError):
        main(args)
    open_input_mock.assert_called_once_with(fname_in)
    open_output_mock.assert_called_once_with(fname_out)
    process_mock.assert_called_once()
    if fname_out is not None:
        remove_mock.assert_called_with(fname_out)
    else:
        remove_mock.assert_not_called()
    rename_mock.assert_not_called()


@patch('virtual_extruders.process', new_callable=lambda: lambda x, **kw: x)
@patch('virtual_extruders.sys.stdout', new_callable=StringIO)
def test_main_passthrough(stdout: StringIO, process_mock: Any) -> None:
    fpath = path('basic')
    with open(fpath, 'r') as fp:
        result = fp.read()
    main([fpath])
    stdout.seek(0)
    assert stdout.read() == result
