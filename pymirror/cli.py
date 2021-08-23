#!/usr/bin/env python3
# coding: utf-8

import argparse

from .__init__ import __version__


class CustomHelpFormatter(argparse.HelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=40, width=80)

    def _format_action_invocation(self, action):
        if not action.option_strings or action.nargs == 0:
            return super()._format_action_invocation(action)  # noqa
        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)
        return ', '.join(action.option_strings) + ' ' + args_string


def fmt(prog):
    return CustomHelpFormatter(prog)


def cli() -> argparse.Namespace:
    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(prog='pymirror', formatter_class=fmt,
                                     add_help=False)
    parser.add_argument('-h',
                        '--help',
                        action='help',
                        default=argparse.SUPPRESS,
                        help='Show this help message and exit')
    parser.add_argument('-i',
                        '--input',
                        help='Path to the input file/folder',
                        required=True)
    parser.add_argument('-s',
                        '--style',
                        help='Output style (default: lines)',
                        choices=['lines', 'list', 'markdown', 'reddit'],
                        default='lines')
    parser.add_argument(
        '-m',
        '--more-links',
        help='Use mirrored.to to generate more likes (default: False)',
        action='store_true',
        default=False)
    parser.add_argument(
        '-n',
        '--number',
        help='Select a specific number of servers to use (default: max)',
        default=None)
    parser.add_argument(
        '-d',
        '--delete',
        help='Delete the file after the process is complete (default: False)',
        action='store_true',
        default=False)
    parser.add_argument(
        '-c',
        '--check-status',
        help='Check the status of the remote servers (default: False)',
        action='store_false',
        default=False)
    parser.add_argument(
        '-D',
        '--debug',
        help='Debug',
        action='store_true',
        default=False)
    parser.add_argument(
        '-l',
        '--log',
        help='Show logs and save it to a file (default: False)',
        action='store_true',
        default=False)
    parser.add_argument(
        '-e',
        '--experimental',
        help='Generate even more links (experimental) (default: False)',
        action='store_true',
        default=False)
    parser.add_argument('-v',
                        '--version',
                        action='version',
                        version=f'%(prog)s {__version__}')

    args = parser.parse_args()
    return args
