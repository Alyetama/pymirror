#!/usr/bin/env python3
# coding: utf-8

import sys
import time
import traceback
from typing import NoReturn

import psutil
from dracula import DraculaPalette as Dp

from .helpers import console, logger, Shared


def firefoxInterrupt(pids) -> list:
    terminated = []
    if pids:
        for pid in pids:
            try:
                p = psutil.Process(pid)
                p.terminate()
                terminated.append(pid)
            except psutil.NoSuchProcess:
                continue
    return terminated


def keyboardInterruptHandler(*args) -> NoReturn:  # noqa
    sys.tracebacklimit = 0
    print('', end='\r')
    time.sleep(0.5)
    console.print(f'[{Dp.y}]Quitting...')
    terminated = firefoxInterrupt(Shared.pids)
    logger.info('Interrupted by the user.')
    if terminated:
        logger.info('Terminated interrupted Firefox instances:', terminated)
    sys.exit(0)


def SeleniumExceptionInfo(exception: Exception) -> str:
    tb = traceback.format_exception(None, exception,
                                    exception.__traceback__)
    tb = ''.join(tb).rstrip()
    logger.error(f'Selenium encountered an error:\n{tb}')
    return tb


def custom_error_traceback(exception: Exception,
                           error_msg: str,
                           log: bool = False) -> list:
    if log:
        logger.error(error_msg)
    tb = traceback.format_exception(None, exception,
                                    exception.__traceback__)
    if log:
        logger.error(f'{"-" * 10} Start of error traceback {"-" * 10}')
        for ln in tb:
            logger.error(ln.replace('\n', ''))
        logger.error(f'{"-" * 10} End of error traceback {"-" * 10}')
    return tb
