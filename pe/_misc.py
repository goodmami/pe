
import sys


ANSICOLORS = {
    'red': '\x1b[31m',
    'green': '\x1b[32m',
    'yellow': '\x1b[33m',
}


def ansicolor(color, text, stream=None):
    if stream is None:
        stream = sys.stdout
    if stream.isatty():
        text = f'{ANSICOLORS[color.lower()]}{text}\x1b[0m'
    return text
