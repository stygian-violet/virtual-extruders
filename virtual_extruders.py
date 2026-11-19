#!/usr/bin/env python3

import os
import re
import sys
from argparse import ArgumentParser, Namespace
from collections.abc import Generator, Iterable
from contextlib import contextmanager
from typing import Any, NamedTuple, TextIO

__appname__ = 'virtual-extruders'
__version__ = '0.1.1'

NAME_VERSION = f'{__appname__} {__version__}'


RE_TOOL = re.compile(r'^T([0-9]+)$')
NON_TOOL_T = {'M106', 'M117', 'M118'}
SET_TEMPERATURE = {'M104', 'M109'}

RE_TOOL_CHANGE_BLOCK_START = re.compile(r'^\s*;\s*TOOL_CHANGE(?:_START)?\s*$')
RE_TOOL_CHANGE_BLOCK_END = re.compile(r'^\s*;\s*TOOL_CHANGE_END\s*$')

DEFAULT_TOOL_CHANGE_BLOCK_START = ';TOOL_CHANGE'
DEFAULT_TOOL_CHANGE_BLOCK_END = ';TOOL_CHANGE_END'
DEFAULT_TOOL_CHANGE_GCODE = [
    DEFAULT_TOOL_CHANGE_BLOCK_START,
    'M117 Insert filament [next_extruder] and resume printing',
    'M600',
    DEFAULT_TOOL_CHANGE_BLOCK_END
]

VIRTUAL_UNUSED = 'not used for virtual extruders'
FIRST_TOOL_CHANGE_UNUSED = 'first tool change is not needed for virtual extruders'

INPLACE_STDIN = '--in-place can not be used with standard input'


class GCodeError(Exception):
    def __init__(self, message: str, line: str | None, line_n: int | None):
        self.message = message
        self.line = line
        self.line_n = line_n

    def __str__(self) -> str:
        res = ['error']
        if self.line is not None or self.line_n is not None:
            res.append('at line')
            if self.line_n is not None:
                res.append(str(self.line_n))
            if self.line is not None:
                res.append(repr(self.line))
        return f'{" ".join(res)}: {self.message}'


class ToolTemperature(NamedTuple):
    command: str
    temperature: str
    tool: int


def comment_out(line: str, message: str = '') -> str:
    if not line:
        return f'; {message}' if message else ''
    start = ';' if line[0] != ';' else ''
    if not message:
        return f'{start}{line}'
    separator = ',' if ';' in line else ' ;'
    return f'{start}{line}{separator} {message}'


def split(line: str) -> tuple[list[str], str]:
    line = line.strip()
    comment = ''
    try:
        i = line.index(';')
    except ValueError:
        pass
    else:
        comment = line[i:]
        line = line[:i].strip()
    return line.split(), comment


def join(cmd: list[str], comment: str) -> str:
    if not cmd:
        return comment
    line = ' '.join(cmd)
    if comment:
        return f'{line} {comment}'
    return line


def format_lines(
    lines: str | Iterable[str],
    **kwargs: Any
) -> Generator[str, None, None]:
    replace = [(f'[{name}]', str(value)) for name, value in kwargs.items()]
    if isinstance(lines, str):
        lines = (lines,)
    for line in lines:
        for old, new in replace:
            line = line.replace(old, new)
        yield line


def get_tool_change_gcode(gcode: list[str] | None) -> list[str]:
    if gcode is None:
        return DEFAULT_TOOL_CHANGE_GCODE
    if not gcode or not RE_TOOL_CHANGE_BLOCK_START.match(gcode[0]):
        gcode.insert(0, DEFAULT_TOOL_CHANGE_BLOCK_START)
    if not RE_TOOL_CHANGE_BLOCK_END.match(gcode[-1]):
        gcode.append(DEFAULT_TOOL_CHANGE_BLOCK_END)
    return gcode


@contextmanager
def open_input(name: str | None) -> Generator[TextIO, None, None]:
    if name is None:
        yield sys.stdin
    else:
        with open(name, 'r') as fp:
            yield fp


@contextmanager
def open_output(name: str | None) -> Generator[TextIO, None, None]:
    if name is None:
        yield sys.stdout
    else:
        with open(name, 'w') as fp:
            yield fp


def parse_tool_selection(cmd: list[str]) -> int | None:
    if len(cmd) == 1 and (m := RE_TOOL.match(cmd[0])):
        return int(m.group(1))
    return None


def parse_tool_temperature(cmd: list[str]) -> ToolTemperature | None:
    if len(cmd) != 3 or cmd[0] not in SET_TEMPERATURE:
        return None
    for i in range(2):
        if m := RE_TOOL.match(cmd[i + 1]):
            return ToolTemperature(cmd[0], cmd[2 - i], int(m.group(1)))
    return None


def process(
    lines: Iterable[str],
    *,
    skip_first_tool_change: bool = False,
    tool_change_gcode: list[str] | None = None
) -> Generator[str, None, None]:
    first_tool_change = True
    insert_tool_change_gcode = False

    set_temperature_tool = None
    temperature = None

    in_tool_change_block = False
    tool_change_block_start = None
    tool_change_block_start_n = None

    tool_change_gcode = get_tool_change_gcode(tool_change_gcode)

    for line_n, line in enumerate(lines, 1):
        cmd, comment = split(line)
        if FIRST_TOOL_CHANGE_UNUSED in comment:
            first_tool_change = False
        elif RE_TOOL_CHANGE_BLOCK_START.match(line):
            if in_tool_change_block:
                raise GCodeError(
                    'unterminated tool change block',
                    tool_change_block_start,
                    tool_change_block_start_n
                )
            tool_change_block_start = line
            tool_change_block_start_n = line_n
            in_tool_change_block = True
            if first_tool_change and skip_first_tool_change:
                yield comment_out('', FIRST_TOOL_CHANGE_UNUSED)
                line = comment_out(line)
        elif RE_TOOL_CHANGE_BLOCK_END.match(line):
            if not in_tool_change_block:
                raise GCodeError(
                    'unmatched tool change block end',
                    line, line_n
                )
            in_tool_change_block = False
            if first_tool_change:
                first_tool_change = False
                if skip_first_tool_change:
                    line = comment_out(line)
        elif (
            skip_first_tool_change
            and first_tool_change
            and in_tool_change_block
        ):
            line = comment_out(line)
        elif not cmd:
            pass
        elif (tool := parse_tool_selection(cmd)) is not None:
            skip = False
            if first_tool_change and not in_tool_change_block:
                insert_tool_change_gcode = True
                first_tool_change = False
                skip = skip_first_tool_change
            if insert_tool_change_gcode:
                tool_change_block: Iterable[str]= format_lines(
                    tool_change_gcode,
                    next_extruder=tool
                )
                if skip:
                    yield comment_out('', FIRST_TOOL_CHANGE_UNUSED)
                    tool_change_block = map(comment_out, tool_change_block)
                yield from tool_change_block
            line = comment_out(line, VIRTUAL_UNUSED)
        elif (temp := parse_tool_temperature(cmd)) is not None:
            if set_temperature_tool is None:
                set_temperature_tool = temp.tool
            if temp.tool == set_temperature_tool:
                temperature = temp.temperature
                yield join([temp.command, temp.temperature], comment)
            elif temp.temperature != temperature:
                raise GCodeError(
                    f'extruders {set_temperature_tool} and {temp.tool}'
                    ' have different temperatures: '
                    f' {temperature} != {temp.temperature}',
                    line, line_n
                )
            line = comment_out(line, VIRTUAL_UNUSED)
        elif (
            cmd[0] not in NON_TOOL_T
            and any(RE_TOOL.match(word) for word in cmd)
        ):
            raise GCodeError(
                'T* g-code processing is not implemented for this line',
                line, line_n
            )
        yield line

    if in_tool_change_block:
        raise GCodeError(
            'unterminated tool change block',
            tool_change_block_start,
            tool_change_block_start_n
        )


def parse_args(args: list[str] | None) -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        '-V', '--version', action='version', version=NAME_VERSION
    )
    parser.add_argument(
        '-i', '--in-place', action='store_true',
        help='edit the file in place'
    )
    parser.add_argument(
        '-f', '--skip-first', action='store_true',
        help='skip first tool change'
    )
    parser.add_argument(
        '-g', '--tool-change-gcode', nargs='+', metavar='GCODE',
        help=f'set tool change g-code (default: {DEFAULT_TOOL_CHANGE_GCODE})'
    )
    parser.add_argument('input', metavar='file', help='g-code file')

    res = parser.parse_args(args)

    if res.input == '-':
        res.input = None

    if res.in_place:
        if res.input is None:
            parser.error(INPLACE_STDIN)
        res.output = res.input + '.tmp'
    else:
        res.output = None

    return res


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    try:
        with (
            open_input(args.input) as input_file,
            open_output(args.output) as output_file
        ):
            for line in process(
                (l.rstrip('\n') for l in input_file),
                skip_first_tool_change=args.skip_first,
                tool_change_gcode=args.tool_change_gcode
            ):
                output_file.write(f'{line}\n')
    except:
        if args.output is not None and os.path.exists(args.output):
            os.remove(args.output)
        raise
    else:
        if args.in_place:
            os.rename(args.output, args.input)


if __name__ == '__main__':
    main()
