#!/usr/bin/env python3
# coding: utf-8

import sys
from pathlib import Path

from .cli import cli
from .main import PyMirror


def main():
    args = cli()
    PyMirror(args).uploader()


if __name__ == '__main__':
    testing = True
    if testing:
        foo = Path('foo.txt')
        if not foo.exists():
            with open(str(foo), 'w') as f:
                f.write('foo\n')
        sys.argv[1:] = ['-i', str(foo), '-m', '--debug']
        main()
        foo.unlink()
    else:
        main()
