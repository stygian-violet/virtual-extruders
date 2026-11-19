import os
from collections.abc import Generator


def path(fname: str) -> str:
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'data',
        f'{fname}.gcode'
    )


def lines(fname: str) -> Generator[str, None, None]:
    with open(path(fname), 'r') as fp:
        for line in fp:
            yield line.rstrip('\n')
